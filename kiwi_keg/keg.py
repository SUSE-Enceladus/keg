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
Usage: keg (-r RECIPES_ROOT|--recipes-root=RECIPES_ROOT)
           [-a ADD_DATA_ROOT] ... [-d DEST_DIR] [-fv]
           SOURCE
       keg -h | --help
       keg --version

Arguments:
    SOURCE    Path to image source, expected under RECIPES_ROOT/images

Options:
    -r RECIPES_ROOT, --recipes-root=RECIPES_ROOT
        Root directory of keg recipes

    -a ADD_DATA_ROOT, --add-data-root=ADD_DATA_ROOT
        Additional data root directory of recipes (multiples allowed)

    -d DEST_DIR, --dest-dir=DEST_DIR
        Destination directory for generated description, default cwd

    -f, --force
       Force mode (ignore errors, overwrite files)

    -v, --verbose
        Enable verbose output

    --version
       Print version
"""
import docopt
import logging
import sys

# project
from kiwi_keg.exceptions import KegError
from kiwi_keg.image_definition import KegImageDefinition
from kiwi_keg.generator import KegGenerator
from kiwi_keg.version import __version__

log = logging.getLogger('keg')


def main():
    args = docopt.docopt(__doc__, version=__version__)

    if args['--verbose']:
        log.setLevel(logging.DEBUG)

    try:
        image_definition = KegImageDefinition(
            image_name=args['SOURCE'],
            recipes_root=args['--recipes-root'],
            data_roots=args['--add-data-root']
        )
        image_generator = KegGenerator(
            image_definition=image_definition,
            dest_dir=args['--dest-dir']
        )
        image_generator.create_kiwi_description(
            args['--force']
        )
        image_generator.create_custom_scripts(
            args['--force']
        )
    except KegError as issue:
        # known exception, log information and exit
        log.error('%s: %s', type(issue).__name__, format(issue))
        sys.exit(1)
    except KeyboardInterrupt:
        log.error('keg aborted by keyboard interrupt')
        sys.exit(1)
    except Exception:
        # exception we did no expect, show python backtrace
        log.error('Unexpected error:')
        raise
