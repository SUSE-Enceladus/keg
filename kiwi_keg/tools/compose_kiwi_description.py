# Copyright (c) 2022 SUSE Software Solutions Germany GmbH. All rights reserved.
#
# This file is part of keg.
#
# keg is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# keg is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with keg. If not, see <http://www.gnu.org/licenses/>
#
"""
Usage:
    compose_kiwi_description --git-recipes=<git_clone_source> ... --image-source=<path> --outdir=<obs_out>
        [--git-branch=<name>] ...
        [--image-version=<VERSION>]
        [--arch=<arch>] ...
        [--version-bump=<true|false>]
        [--update-changelogs=<true|false>]
        [--update-revisions=<true|false>]
        [--force=<true|false>]
        [--generate-multibuild=<true|false>]
        [--new-image-change=<changelog_entry>]
        [--changelog-format=<format>]
    compose_kiwi_description -h | --help
    compose_kiwi_description --version

Options:
    --git-recipes=<git_clone_source>
        Remote git repository containing keg-recipes (multiples allowed).

    --git-branch=<name>
        Recipes repository branch to check out (multiples allowed, optional).

    --image-source=<path>
        Keg path in git source pointing to the image description.
        The path must be relative to the images/ directory.

    --arch=<arch>
        Set build architecture to arch (multiples allowed, optional).

    --outdir=<obs_out>
        Output directory to store data produced by the service.
        At the time the service is called through the OBS API
        this option is set.

   --image-version=<VERSION>
        Set image version to VERSION. If no version is given, the old version
        will be used with the patch number increased by one.

    --version-bump=<true|false>
        Whether the patch version number should be incremented. Ignored if
        '--image-version' is set. If set to 'false' and '--image-version' is
        not set, the image version defined in the recipes will be used. If no
        image version is defined, image description generation will fail.
        [default: true]

    --update-changelogs=<true|false>
        Whether 'changes.yaml' files should be updated. [default: true]

    --update-revisions=<true|false>
        Whether '_keg_revisions' should be updated. [default: true]

    --force=<true|false>
        If true, refresh image description even if there are no new commits.
        [default: false]

    --generate-multibuild=<true|false>
        If true, generate a _multibuild file if the image definition has
        profiles defined. [default: true]

    --new-image-change=<changelog_entry>
        If set, when generating a net new image description, use
        changelog_entry as the sole entry in the generated change log instead
        of using the full commit history. [default: None]

    --changelog-format=<format>
        Use format as output format for the generated change log. Supported
        values are 'yaml', 'json', and 'osc'. Existing change logs will be
        converted if necessary. Conversion from 'osc' is not supported.
        [default: json]


"""
import docopt
import glob
import itertools
import json
import logging
import os
import pathlib
import subprocess
import sys
import tempfile
import yaml
import xml.etree.ElementTree as ET

from datetime import datetime, timezone

from kiwi_keg.version import __version__
from kiwi_keg.image_definition import KegImageDefinition
from kiwi_keg.generator import KegGenerator
from kiwi_keg.source_info_generator import SourceInfoGenerator


log = logging.getLogger('compose_keg_description')
log.setLevel(logging.INFO)


class RepoInfo:
    def __init__(self, path):
        self._path = path
        self._head_commit = get_head_commit_hash(path.name)
        self._start_commit = None

    def set_start_commit(self, commit):
        self._start_commit = commit

    @property
    def pathname(self):
        return self._path.name

    @property
    def head_commit(self):
        return self._head_commit

    @property
    def start_commit(self):
        return self._start_commit

    def has_commits(self):
        return self._start_commit != self._head_commit


def repr_mstr(dumper, data):
    if '\n' in data:
        tag = u'tag:yaml.org,2002:str'
        return dumper.represent_scalar(tag, data, style='|')
    return dumper.represent_str(data)


def get_head_commit_hash(repo_path):
    result = subprocess.run(
        ['git', '-C', repo_path, 'show', '--no-patch', '--format=%H', 'HEAD'],
        capture_output=True,
        encoding='UTF-8'
    )
    return result.stdout.strip('\n')


def get_image_version(kiwi_config):
    # It is expected that the <version> setting exists only once
    # in a keg generated image description. KIWI allows for profiled
    # <preferences> which in theory also allows to distribute the
    # <version> information between several <preferences> sections
    # but this would be in general questionable and should not be
    # be done any case by keg managed recipes. Thus the following
    # code takes the first version setting it can find and takes
    # it as the only version information available
    tree = ET.parse(kiwi_config)
    root = tree.getroot()
    for preferences in root.findall('preferences'):
        image_version = preferences.find('version')
        if image_version is not None:
            return image_version.text
    if not image_version:
        sys.exit('Cannot determine image version.')


def parse_revisions(repos):
    if os.path.exists('_keg_revisions'):
        with open('_keg_revisions') as inf:
            for line in inf.readlines():
                rev_spec = line.strip('\n').split(' ')
                if len(rev_spec) != 2:
                    sys.exit('Malformed revision spec "{}".'.format(line.strip('\n')))
                repo = repos.get(rev_spec[0])
                if not repo:
                    log.warning('Cannot map URL "{}" to repository.'.format(rev_spec[0]))
                else:
                    repo.set_start_commit(rev_spec[1])
    else:
        log.info(
            'No _keg_revision file.'
        )


def get_revision_args(repos):
    rev_args = []
    for repo in repos.values():
        if repo.start_commit:
            rev_args += ['-r', '{}:{}..'.format(repo.pathname, repo.start_commit)]
    return rev_args


def generate_changelog(source_log, changes_file, log_format, image_version, rev_args):
    result = subprocess.run(
        [
            'generate_recipes_changelog',
            '-o', changes_file,
            '-f', log_format,
            '-t', image_version,
            *rev_args,
            source_log
        ]
    )
    if result.returncode == 1:
        sys.exit('Error generating change log.')
    # generate_recipes_changelog returns 2 in case there were no changes
    # return True or False accordingly
    return result.returncode == 0


def read_changelog(log_file):
    changes = None
    if log_file.endswith('.txt'):
        with open(log_file, 'r') as inf:  # pragma: no cover
            changes = inf.read()          # pragma: no cover
    elif log_file.endswith('.yaml'):
        with open(log_file, 'r') as inf:
            changes = yaml.safe_load(inf)
    elif log_file.endswith('.json'):
        with open(log_file, 'r') as inf:
            changes = json.load(inf)
    else:
        log.warning('Unsupported log format {}'.format(log_file))
    return changes


def update_changelog(log_file, log_format):
    old_logs = glob.glob(pathlib.Path(log_file).stem + '.*')
    if old_logs:
        old_log = old_logs[0]
        if len(old_logs) > 1:
            log.warning('More than one format for old log, using {}'.format(old_log))
    else:
        log.info('No old log')
        return

    old_log_format = pathlib.Path(old_log).suffix[1:]
    if old_log_format == 'txt':
        old_log_format = 'osc'

    if log_format != 'json' and log_format == old_log_format:
        # simply concatenate old log to new one
        with open(log_file, 'a') as outf, open(old_log) as inf:
            log.info('Appending old changes to {}'.format(log_file))
            outf.write(inf.read())
    else:
        if old_log_format == 'osc':
            log.warning('Converting text log files is not supported, losing history')
            return
        else:
            # different formats, or both json which needs merge
            log.info('Reading old changes from {}'.format(old_log))
            old_changes = read_changelog(old_log)
            if old_changes:
                if log_format == 'osc':
                    log.info('Appending old changes to {}'.format(pathlib.Path(log_file).name))
                    write_changelog(log_file, log_format, old_changes, append=True)
                else:
                    new_changes = read_changelog(log_file)
                    new_changes.update(old_changes)
                    log.info('Writing merged changes to {}'.format(pathlib.Path(log_file).name))
                    write_changelog(log_file, log_format, new_changes)


def get_osc_log(ver, entries):
    change = '-------------------------------------------------------------------\n'
    if hasattr(datetime, 'fromisoformat'):
        change += datetime.fromisoformat(entries[0]['date']).strftime('%c UTC')  # pragma: nocover_py36
    else:
        import iso8601  # pragma: nocover
        change += iso8601.parse_date(entries[0]['date']).strftime('%c UTC')  # pragma: nocover
    change += '\n'
    indent = '- '
    if ver:
        change += '\n- Update to {}\n'.format(ver)
        indent = '  + '
    for entry in entries:
        change += indent
        change += '{}\n'.format(entry['change'])
    return change


def update_revisions(repos, outdir):
    with open(os.path.join(outdir, '_keg_revisions'), 'w') as outf:
        for rname, rinfo in repos.items():
            print('{} {}'.format(rname, rinfo.head_commit), file=outf)


def get_log_sources(logdir):
    for source_log in glob.glob(os.path.join(logdir, 'log_sources*')):
        flavor = source_log[len(os.path.join(logdir, 'log_sources')) + 1:]
        yield source_log, flavor


def write_changelog(log_file, log_format, changes, append=False):
    open_mode = 'w'
    if append:
        open_mode = 'a'
    with open(log_file, open_mode) as outf:
        if log_format == 'osc':
            for image_version in changes:
                if changes[image_version]:
                    print(get_osc_log(image_version, changes[image_version]), file=outf)
        elif log_format == 'yaml':
            yaml.add_representer(str, repr_mstr, Dumper=yaml.SafeDumper)
            yaml.safe_dump(changes, outf, sort_keys=False)
        elif log_format == 'json':
            json.dump(changes, outf, indent=2, default=str)


def main() -> None:
    args = docopt.docopt(__doc__, version=__version__)

    if len(args['--git-branch']) > len(args['--git-recipes']):
        sys.exit('Number of --git-branch arguments must not exceed number of git repos.')

    handle_changelog = args['--update-changelogs'] == 'true'

    if args['--changelog-format'] == 'osc':
        log_ext = 'txt'
    elif args['--changelog-format'] in ['yaml', 'json']:
        log_ext = args['--changelog-format']
    else:
        sys.exit('Unknown changelog format {}'.format(args['--changelog-format']))

    if not os.path.exists(args['--outdir']):
        os.mkdir(args['--outdir'])

    repos = {}
    for repo, branch in itertools.zip_longest(args['--git-recipes'], args['--git-branch']):
        temp_git_dir = tempfile.TemporaryDirectory(prefix='keg_recipes.', dir='.')
        if branch:
            subprocess.run(['git', 'clone', '-b', branch, repo, temp_git_dir.name])
        else:
            subprocess.run(['git', 'clone', repo, temp_git_dir.name])
        repos[repo] = RepoInfo(temp_git_dir)

    parse_revisions(repos)
    repos_with_commits = list(filter(lambda x: x.has_commits() is True, repos.values()))
    if not repos_with_commits:
        log.warning('No repository has new commits.')
        if args['--force'] != 'true':
            log.info('Aborting.')
            sys.exit()

    image_version = args['--image-version']
    old_kiwi_config = None
    if os.path.exists('config.kiwi'):
        old_kiwi_config = 'config.kiwi'

    if not image_version:
        if args['--version-bump'] == 'true' and old_kiwi_config:
            # if old config.kiwi exists, increment patch version number
            version = get_image_version(old_kiwi_config)
            if version:
                ver_elements = version.split('.')
                ver_elements[2] = f'{int(ver_elements[2]) + 1}'
                image_version = '.'.join(ver_elements)

    logging.getLogger('keg').setLevel(logging.INFO)
    image_definition = KegImageDefinition(
        image_name=args['--image-source'],
        recipes_roots=[x.pathname for x in repos.values()],
        track_sources=handle_changelog,
        image_version=image_version
    )
    image_generator = KegGenerator(
        image_definition=image_definition,
        dest_dir=args['--outdir'],
        archs=args['--arch']
    )
    image_generator.create_kiwi_description(
        overwrite=True
    )
    image_generator.create_custom_scripts(
        overwrite=True
    )
    image_generator.create_overlays(
        disable_root_tar=False, overwrite=True
    )
    image_generator.create_custom_files(
        overwrite=True
    )
    if args['--generate-multibuild']:
        image_generator.create_multibuild_file(overwrite=True)

    if handle_changelog:
        sig = SourceInfoGenerator(image_definition, dest_dir=args['--outdir'])
        sig.write_source_info()
        rev_args = get_revision_args(repos)
        have_changes = False

        if not image_version:
            image_version = get_image_version(os.path.join(args['--outdir'], 'config.kiwi'))

        if not old_kiwi_config and args['--new-image-change']:
            # net new image, use supplied change log entry instead of generating
            # full log from commit history
            new_changes = {
                image_version: [
                    {
                        'change': args['--new-image-change'],
                        'date': datetime.now(timezone.utc).isoformat(timespec='minutes')
                    }
                ]
            }
            for source_log, flavor in get_log_sources(args['--outdir']):
                changes_filename = f'{flavor}{"." if flavor else ""}changes.{log_ext}'
                changes_path = os.path.join(args['--outdir'], changes_filename)
                log.info('Writing {}'.format(changes_path))
                write_changelog(changes_path, args['--changelog-format'], new_changes)
                # clean up source log
                os.remove(source_log)
        else:
            for source_log, flavor in get_log_sources(args['--outdir']):
                changes_filename = f'{flavor}{"." if flavor else ""}changes.{log_ext}'
                changes_path = os.path.join(args['--outdir'], changes_filename)
                have_changes |= generate_changelog(source_log, changes_path, args['--changelog-format'], image_version, rev_args)

            if not have_changes:
                log.warning('Image has no changes.')
                if args['--force'] != 'true':
                    log.info('Deleting generated files.')
                    for f in next(os.walk(args['--outdir']))[2]:
                        os.remove(os.path.join(args['--outdir'], f))
                    sys.exit()

            for source_log, flavor in get_log_sources(os.path.join(args['--outdir'])):
                changes_filename = f'{flavor}{"." if flavor else ""}changes.{log_ext}'
                changes_path = os.path.join(args['--outdir'], changes_filename)
                update_changelog(changes_path, args['--changelog-format'])
                # clean up source log
                os.remove(source_log)

    if args['--update-revisions'] == 'true':
        # capture current commits
        update_revisions(repos, args['--outdir'])
