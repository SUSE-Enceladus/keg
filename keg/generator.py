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
from jinja2 import Environment, FileSystemLoader
import os

from keg import (
    image_definition,
    kiwi_description,
    template_functions,
    utils
)
from keg.exceptions import KegError, KegKiwiValidationError


def create_image_description(image_source,
                             recipes_root,
                             data_roots,
                             dest_dir,
                             log,
                             force=False):
    """
    Create a KIWI image description in dest_dir from image_source.

    Expects a keg-recipes structure at recipes_root and image_source
    referring to a directory under images in recipes_root.
    """
    # Sanity check image source location
    if not os.path.exists(os.path.join(recipes_root, 'images', image_source)):
        errmsg = 'Source directory for {} does not exist.'.format(image_source)
        if force:
            log.warning(errmsg)
        else:
            raise KegError(errmsg)

    img = image_definition.ImageDefinition(image_source, recipes_root, data_roots)
    img.populate()

    schemas_dir = os.path.join(recipes_root, 'schemas')
    env = Environment(loader=FileSystemLoader(schemas_dir))
    env.globals['keg_funcs'] = template_functions

    kiwi_templ = env.get_template('{}.kiwi.templ'.format(img['schema']))
    kiwi_doc = kiwi_templ.render(data=img.get_data())

    outfile = os.path.join(dest_dir, 'config.kiwi')
    if os.path.exists(outfile) and not force:
        raise KegError('{} exists, use force to overwrite.'.format(outfile))
    with open(outfile, 'w') as fd:
        fd.write(kiwi_doc)

    kiwi_desc = kiwi_description.KiwiDescription(outfile)
    try:
        kiwi_desc.validate_description()
    except KegKiwiValidationError:
        if force:
            log.warning('KIWI description validation error')
            # FIXME: find out how to get details
            pass
        else:
            raise

    script_roots = [ os.path.join(recipes_root, 'data') ] + data_roots
    script_lib = utils.load_scripts('scripts', script_roots, img['include-paths'])
    config_templ = env.get_template('{}.config.sh.templ'.format(img['schema']))
    config_sh = config_templ.render(data=img.get_data(), scripts=script_lib)

    outfile = os.path.join(dest_dir, 'config.sh')
    if os.path.exists(outfile) and not force:
        raise KegError('{} exists, use force to overwrite.'.format(outfile))
    with open(outfile, 'w') as fd:
        fd.write(config_sh)
