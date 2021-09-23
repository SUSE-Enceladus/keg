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
Usage: fetch_from_keg --git-recipes=<git_clone_source> --image-source=<path> --branch=<name>
       fetch_from_keg -h | --help
       fetch_from_keg --version
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
