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
import logging
import xml.etree.ElementTree as ET

from kiwi_keg.image_definition import KegImageDefinition
from kiwi_keg.generator import KegGenerator
from kiwi_keg.source_info_generator import SourceInfoGenerator


def get_image_version(kiwi_config):
    # It is expected that the <version> setting exists only once
    # in a keg generated image description. KIWI allows for profiled
    # <preferences> which in theory also allows to istribute the
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
        raise RuntimeError('Cannot determine image version.')


def get_bumped_image_version(kiwi_file):
    image_version = None
    version = get_image_version(kiwi_file)
    if version:
        ver_elements = version.split('.')
        ver_elements[2] = f'{int(ver_elements[2]) + 1}'
        image_version = '.'.join(ver_elements)
    return image_version


def generate_image_description(image_source, repos, gen_src_log, image_version, gen_mbuild, outdir, archs):
    logging.getLogger('keg').setLevel(logging.INFO)
    image_definition = KegImageDefinition(
        image_name=image_source,
        recipes_roots=[x.pathname for x in repos.values()],
        track_sources=gen_src_log,
        image_version=image_version
    )
    image_generator = KegGenerator(
        image_definition=image_definition,
        dest_dir=outdir,
        archs=archs
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
    if gen_mbuild:
        image_generator.create_multibuild_file(overwrite=True)
    if gen_src_log:
        sig = SourceInfoGenerator(image_definition, dest_dir=outdir)
        sig.write_source_info()
