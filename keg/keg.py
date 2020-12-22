# Copyright (c) 2020 SUSE Software Solutions Germany GmbH. All rights reserved.
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

import argparse
import logging
import sys

# project
from keg.exceptions import KegError
from keg.generator import create_image_description
from keg.version import __version__

log = logging.getLogger('keg')


def main():
    argparser = argparse.ArgumentParser(
        description='Create KIWI image description from keg recipe'
    )
    argparser.add_argument(
        '-r', '--recipes-root',
        dest='recipes_root',
        help='Root directory of recipes (required)'
    )
    argparser.add_argument(
        '-d', '--dest-dir',
        default='.',
        dest='dest_dir',
        help='Destination directory for generated description, default cwd'
    )
    argparser.add_argument(
        '-f', '--force',
        action='store_true',
        default=False,
        dest='force',
        help='Force mode (ignore errors, overwrite files)'
    )
    argparser.add_argument(
        '-v', '--verbose',
        action='store_true',
        default=False,
        dest='verbose',
        help='Enable verbose output'
    )
    argparser.add_argument(
        '--version',
        action='version',
        version=__version__,
        help='Print version'
    )
    argparser.add_argument(
        'source',
        help='Path to image source, expected under recipes-root/images'
    )
    args = argparser.parse_args()

    if args.verbose:
        log.setLevel(logging.DEBUG)

    try:
        create_image_description(
            args.source,
            args.recipes_root,
            args.dest_dir,
            log,
            args.force
        )
    except KegError as err:
        sys.exit('Error creating image description: {}'.format(err))
