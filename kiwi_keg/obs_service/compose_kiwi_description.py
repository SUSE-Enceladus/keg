# Copyright (c) 2021 SUSE Software Solutions Germany GmbH. All rights reserved.
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
    compose_kiwi_description --main-git-recipes=<git_clone_source> --image-source=<path> --outdir=<obs_out>
        [--main-branch=<name>]
        [--add-on-git-recipes=<add_on_git_clone_source>]
        [--add-on-branch=<name>]
    compose_kiwi_description -h | --help
    compose_kiwi_description --version

Options:
    --main-git-recipes=<git_clone_source>
        Main git clone location to fetch keg recipes.

    --image-source=<path>
        Keg path in git source pointing to the image description.
        The path must be relative to the images/ directory

    --main-branch=<name>
        Branch in main git source [default: released].

    --add-on-git-recipes=<add_on_git_clone_source>
        Additional git clone location to fetch other keg recipes.

    --add-on-branch=<name>
        Branch in additional git source [default: released].

    --outdir=<obs_out>
        Output directory to store data produced by the service.
        At the time the service is called through the OBS API
        this option is set.
"""
import docopt
import logging

from kiwi_keg.version import __version__

log = logging.getLogger('keg')
log.setLevel(logging.INFO)


def main() -> None:
    args = docopt.docopt(__doc__, version=__version__)

    # steps
    # 1. clone from args['--git-recipes']
    # 2. Run KegGenerator on args['--image-source']
    # 3. Care for the version bump
    # 4. Commit results

    log.info(args)
