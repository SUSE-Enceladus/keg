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

Usage: keg (-l|--list-recipes) (-r RECIPES_ROOT|--recipes-root=RECIPES_ROOT)... [-v]
       keg (-r RECIPES_ROOT|-recipes-root=RECIPES_ROOT)...
           [--format-xml|--format-yaml] [--disable-root-tar]
           [--disable-multibuild] [--dump-dict]
           [-i IMAGE_VERSION|--image-version=IMAGE_VERSION]
           [-d DEST_DIR] [-a ARCH]... [-fv]
           [-s|--write-source-info] SOURCE
       keg -h | --help
       keg --version

Arguments:
    SOURCE    Path to image source, expected under RECIPES_ROOT/images

Options:
    -r RECIPES_ROOT, --recipes-root=RECIPES_ROOT
        Root directory of keg recipes. Can be used more than once. Elements
        from later roots may overwrite earlier one.

    -d DEST_DIR, --dest-dir=DEST_DIR
        Destination directory for generated description [default: .]

    --disable-multibuild
        Option to disable creation of OBS _multibuild file (for image
        definitions with multiple profiles). [default: false]

    --disable-root-tar
        Option to disable the creation of root.tar.gz in destination directory.
        If present, an overlay tree will be created instead.
        [default: false]

    --dump-dict
        Dump generated data dictionary to stdout instead of generating an image
        description. Useful for debugging.

    -l, --list-recipes
        List available images that can be created with the current recipes

    -f, --force
        Force mode (ignore errors, overwrite files)

    --format-yaml
        Format/Update Keg written image description to installed
        KIWI schema and write the result description in YAML markup

    --format-xml
        Format/Update Keg written image description to installed
        KIWI schema and write the result description in XML markup

    -i IMAGE_VERSION, --image-version=IMAGE_VERSION
        Set image version

    -a ARCH
        Generate image description for architecture ARCH (can be used
        multiple times)

    -s, --write-source-info
        Write a file per profile containing a list of all used source
        locations. The files can used to generate a change log from the
        recipes repository commit log.

    -v, --verbose
        Enable verbose output

    --version
        Print version
"""
import docopt
import logging
import os
import sys

# project
from kiwi_keg.annotated_mapping import AnnotatedPrettyPrinter
from kiwi_keg.exceptions import KegError
from kiwi_keg.file_utils import get_all_leaf_dirs
from kiwi_keg.generator import KegGenerator
from kiwi_keg.image_definition import KegImageDefinition
from kiwi_keg.source_info_generator import SourceInfoGenerator
from kiwi_keg.version import __version__

log = logging.getLogger('keg')
log.setLevel(logging.INFO)


def main():
    args = docopt.docopt(__doc__, version=__version__)

    # docopt seems to duplicate repeatable options, remove them
    roots = list(dict.fromkeys(args['--recipes-root']))

    if args['--verbose']:
        log.setLevel(logging.DEBUG)

    if args['--list-recipes']:
        image_roots = [os.path.join(x, 'images') for x in roots]
        image_dirs = []
        for image_root in image_roots:
            image_dirs += get_all_leaf_dirs(image_root)
        images = {}
        for image_src in sorted(image_dirs):
            try:
                image_definition = KegImageDefinition(
                    image_name=image_src,
                    recipes_roots=roots
                )
                image_definition.populate()
                image_spec = image_definition.data['image']
                images[image_src] = {
                    'name': image_spec['_attributes']['name'],
                    'desc': image_spec['description']['specification'],
                    'ver': image_spec['preferences'][0].get('version', 'n/a')
                }
            except KegError as e:
                log.error('{} is not a valid image: {}'.format(image_src, e))
        print('{:30s} {:30s} {:8s} {}'.format('Source', 'Name', 'Version', 'Description'))
        for image, spec in images.items():
            print('{:30s} {:30s} {:8s} {}'.format(image, spec['name'], spec['ver'], spec['desc']))
        return

    try:
        image_definition = KegImageDefinition(
            image_name=args['SOURCE'],
            recipes_roots=roots,
            image_version=args['--image-version'],
            track_sources=args['--write-source-info']
        )
        if args['--dump-dict']:
            try:
                image_definition.populate()
            except KegError:  # pragma: no cover
                pass
            ap = AnnotatedPrettyPrinter(indent=2)
            ap.pprint(image_definition.data)
            return
        image_generator = KegGenerator(
            image_definition=image_definition,
            dest_dir=args['--dest-dir'],
            archs=args['-a'],
            gen_profiles_comment=not args['--disable-multibuild']
        )
        image_generator.create_kiwi_description(
            overwrite=args['--force']
        )
        if args['--format-yaml']:
            image_generator.format_kiwi_description('yaml')
        elif args['--format-xml']:
            image_generator.format_kiwi_description('xml')
        else:
            image_generator.validate_kiwi_description()
        image_generator.create_custom_scripts(
            overwrite=args['--force']
        )
        image_generator.create_overlays(
            disable_root_tar=args['--disable-root-tar'],
            overwrite=args['--force']
        )
        if not args['--disable-multibuild']:
            image_generator.create_multibuild_file(
                overwrite=args['--force']
            )
        if args['--write-source-info']:
            source_info_generator = SourceInfoGenerator(
                image_definition=image_definition,
                dest_dir=args['--dest-dir']
            )
            source_info_generator.write_source_info(overwrite=args['--force'])
    except KegError as issue:
        # known exception, log information and exit
        if args['--verbose']:
            import traceback
            traceback.print_exc()
        log.error('%s: %s', type(issue).__name__, format(issue))
        sys.exit(1)
    except KeyboardInterrupt:
        log.error('keg aborted by keyboard interrupt')
        sys.exit(1)
    except Exception:
        # exception we did no expect, show python backtrace
        log.error('Unexpected error:')
        raise
