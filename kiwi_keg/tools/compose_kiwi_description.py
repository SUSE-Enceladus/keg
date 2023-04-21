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
"""
import glob
import docopt
import itertools
import logging
import os
import sys

from kiwi.xml_description import XMLDescription
from kiwi.utils.temporary import Temporary
from kiwi.command import Command
from kiwi.path import Path
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
    def path(self):
        return self._path.name

    @property
    def head_commit(self):
        return self._head_commit

    @property
    def start_commit(self):
        return self._start_commit

    def has_commits(self):
        return self._start_commit != self._head_commit


def get_kiwi_data(kiwi_config):
    description = XMLDescription(kiwi_config)
    return description.load()


def get_head_commit_hash(repo_path):
    result = Command.run(['git', '-C', repo_path, 'show', '--no-patch', '--format=%H', 'HEAD'])
    return result.output.strip('\n')


def get_image_version(kiwi_config):
    # It is expected that the <version> setting exists only once
    # in a keg generated image description. KIWI allows for profiled
    # <preferences> which in theory also allows to distribute the
    # <version> information between several <preferences> sections
    # but this would be in general questionable and should not be
    # be done any case by keg managed recipes. Thus the following
    # code takes the first version setting it can find and takes
    # it as the only version information available
    for preferences in get_kiwi_data(kiwi_config).get_preferences():
        image_version = preferences.get_version()
        if image_version:
            return image_version[0]
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
        log.warning(
            'No _keg_revision file. '
            'Changes file(s) will contain all applicable commit messages.'
        )


def get_revision_args(repos):
    rev_args = []
    for repo in repos.values():
        if repo.start_commit:
            rev_args += ['-r', '{}:{}..'.format(repo.path, repo.start_commit)]
    return rev_args


def generate_changelog(source_log, changes_file, image_version, rev_args):
    result = Command.run(
        [
            'generate_recipes_changelog',
            '-o', changes_file,
            '-f', 'yaml',
            '-t', image_version,
            *rev_args,
            source_log
        ], raise_on_error=False
    )
    if result.returncode == 1:
        sys.exit('Error generating change log: {}'.format(result.error))
    # generate_recipes_changelog returns 2 in case there were no changes
    # return True or False accordingly
    return result.returncode == 0


def update_changelog(changes_old, changes_new):
    if os.path.exists(changes_old):
        with open(changes_new, 'a') as outf, open(changes_old) as inf:
            outf.write(inf.read())


def update_revisions(repos, outdir):
    with open(os.path.join(outdir, '_keg_revisions'), 'w') as outf:
        for rname, rinfo in repos.items():
            print('{} {}'.format(rname, rinfo.head_commit), file=outf)


def get_log_sources(logdir):
    for source_log in glob.glob(os.path.join(logdir, 'log_sources*')):
        flavor = source_log[len(os.path.join(logdir, 'log_sources')) + 1:]
        yield source_log, flavor


def main() -> None:
    args = docopt.docopt(__doc__, version=__version__)

    if not os.path.exists(args['--outdir']):
        Path.create(args['--outdir'])

    if len(args['--git-branch']) > len(args['--git-recipes']):
        sys.exit('Number of --git-branch arguments must not exceed number of git repos.')

    handle_changelog = args['--update-changelogs'] == 'true'

    repos = {}
    for repo, branch in itertools.zip_longest(args['--git-recipes'], args['--git-branch']):
        temp_git_dir = Temporary(prefix='keg_recipes.').new_dir()
        if branch:
            Command.run(['git', 'clone', '-b', branch, repo, temp_git_dir.name])
        else:
            Command.run(['git', 'clone', repo, temp_git_dir.name])
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

    image_definition = KegImageDefinition(
        image_name=args['--image-source'],
        recipes_roots=[x.path for x in repos.values()],
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
    if args['--generate-multibuild']:
        image_generator.create_multibuild_file(overwrite=True)

    if handle_changelog:
        sig = SourceInfoGenerator(image_definition, dest_dir=args['--outdir'])
        sig.write_source_info()
        rev_args = get_revision_args(repos)
        have_changes = False

        if not image_version:
            image_version = get_image_version(os.path.join(args['--outdir'], 'config.kiwi'))

        for source_log, flavor in get_log_sources(os.path.join(args['--outdir'])):
            changes_filename = f'{flavor}{"." if flavor else ""}changes.yaml'
            changes_path = os.path.join(args['--outdir'], changes_filename)
            have_changes |= generate_changelog(source_log, changes_path, image_version, rev_args)

        if not have_changes:
            log.warning('Image has no changes.')
            if args['--force'] != 'true':
                log.info('Deleting generated files.')
                for f in next(os.walk(args['--outdir']))[2]:
                    os.remove(os.path.join(args['--outdir'], f))
                sys.exit()

        for source_log, flavor in get_log_sources(os.path.join(args['--outdir'])):
            changes_filename = f'{flavor}{"." if flavor else ""}changes.yaml'
            changes_new = os.path.join(args['--outdir'], changes_filename)
            update_changelog(changes_filename, changes_new)
            # clean up source log
            os.remove(source_log)

    if args['--update-revisions'] == 'true':
        # capture current commits
        update_revisions(repos, args['--outdir'])
