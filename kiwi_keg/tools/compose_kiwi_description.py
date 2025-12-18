# Copyright (c) 2025 SUSE Software Solutions Germany GmbH. All rights reserved.
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
        [--purge-stale-files=<true|false>]
        [--purge-ignore=<regex>]
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

    --purge-stale-files=<true|false>
        Purge files from existing image description if the generated image
        description does not contain them. [default: true]

    --purge-ignore=<regex>
        When checking for old files to purge, ignore files matching <regex>
        (optional). [default: '']

"""
import docopt
import itertools
import logging
import os
import tempfile
import sys

from datetime import datetime, timezone

from kiwi_keg.version import __version__
import kiwi_keg.tools.lib_changelog as lib_changelog
import kiwi_keg.tools.lib_fileutil as lib_fileutil
import kiwi_keg.tools.lib_image as lib_image
import kiwi_keg.tools.lib_repo as lib_repo
import kiwi_keg.tools.lib_source as lib_source

logging.basicConfig(
    format='%(asctime)s [%(levelname)-8s] %(message)s',
    datefmt='%H:%M:%S',
    stream=sys.stderr,
    level=logging.INFO
)


def get_changelog_format(changelog_format):
    if changelog_format == 'osc':
        log_ext = 'txt'
    elif changelog_format in ['yaml', 'json']:
        log_ext = changelog_format
    else:
        sys.exit('Unknown changelog format {}'.format(changelog_format))
    return log_ext


def get_repos(args):
    if len(args['--git-branch']) > 0 and len(args['--git-branch']) != len(args['--git-recipes']):
        sys.exit('Number of --git-branch arguments (when used) must be equial to number of --git-recipes.')

    repos = {}
    for repo, branch in itertools.zip_longest(args['--git-recipes'], args['--git-branch']):
        logging.info(f'Checking out {repo}')
        repos[repo] = lib_repo.GitRepo(repo, branch)

    lib_repo.parse_revisions(repos)
    repos_with_commits = list(filter(lambda x: x.has_commits() is True, repos.values()))
    if not repos_with_commits:
        logging.info('No repository has new commits.')
        if args['--force'] != 'true':
            logging.info('Nothing to do. Aborting.')
            sys.exit()

    return repos


def get_new_image_version(args):
    image_version = args['--image-version']
    have_old_kiwi_config = os.path.exists('config.kiwi')

    if not image_version and args['--version-bump'] == 'true' and have_old_kiwi_config:
        image_version = lib_image.get_bumped_image_version('config.kiwi')

    return image_version, have_old_kiwi_config


def generate_deleted_source_info(args, repos, image_version):
    # generate previous source logs to find deleted items
    with tempfile.TemporaryDirectory(dir=args['--outdir']) as tmpdir:
        lib_repo.checkout_start_commits(repos)

        logging.info('Generating previous image description')
        lib_image.generate_image_description(
            image_source=args['--image-source'],
            repos=repos,
            gen_src_log=True,
            image_version=image_version,
            gen_mbuild=False,
            outdir=tmpdir,
            archs=args['--arch']
        )

        logging.info('Trying to detect deletions')
        lib_source.find_deleted_src_lines(tmpdir, args['--outdir'])

        lib_repo.checkout_head_commits(repos)


def generate_changelogs(args, image_version, rev_args, have_old_kiwi_config, log_ext):
    if not image_version:
        image_version = lib_image.get_image_version(os.path.join(args['--outdir'], 'config.kiwi'))

    change_entries = None
    if not have_old_kiwi_config and args['--new-image-change']:
        # net new image, use supplied change log entry instead of generating
        # full log from commit history
        change_entries = {
            image_version: [
                {
                    'change': args['--new-image-change'],
                    'date': datetime.now(timezone.utc).isoformat(timespec='minutes')
                }
            ]
        }

    have_changes = False
    for source_log, flavor in lib_source.get_log_sources(args['--outdir']):
        have_changes |= lib_changelog.generate_and_update(
            outdir=args['--outdir'],
            prefix=flavor,
            log_ext=log_ext,
            changes=change_entries,
            source_log=source_log,
            image_version=image_version,
            rev_args=rev_args
        )
        # clean up source log file
        os.remove(source_log)

    return have_changes


def main() -> None:
    args = docopt.docopt(__doc__, version=__version__)

    handle_changelog = args['--update-changelogs'] == 'true'
    log_ext = get_changelog_format(args['--changelog-format'])
    repos = get_repos(args)
    image_version, have_old_kiwi_config = get_new_image_version(args)

    if not os.path.exists(args['--outdir']):
        os.mkdir(args['--outdir'])

    lib_image.generate_image_description(
        image_source=args['--image-source'],
        repos=repos,
        gen_src_log=handle_changelog,
        image_version=image_version,
        gen_mbuild=args['--generate-multibuild'] == 'true',
        outdir=args['--outdir'],
        archs=args['--arch']
    )

    stale_files = lib_fileutil.purge_files(
        '.',
        args['--outdir'],
        args['--purge-stale-files'] == 'true',
        args['--purge-ignore'],
        args['--version-bump'] == 'true',
        not args['--force'] == 'true'
    )

    if handle_changelog:
        rev_args = lib_repo.get_revision_args(repos)
        if rev_args:
            generate_deleted_source_info(args, repos, image_version)

        have_changes = generate_changelogs(args, image_version, rev_args, have_old_kiwi_config, log_ext)

        if not have_changes:
            logging.warning('Image description has changed but no new change log entries were generated.')

    if args['--update-revisions'] == 'true':
        # capture current commits
        lib_repo.update_revisions(repos, args['--outdir'])

    for f in stale_files:
        logging.info('Deleting stale file {}'.format(f))
        os.remove(f)
