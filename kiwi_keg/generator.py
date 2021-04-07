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
import logging
from jinja2 import Environment, FileSystemLoader
from lxml import etree
from typing import Optional
import os
import shutil
import tarfile

from kiwi_keg.image_definition import KegImageDefinition
from kiwi_keg.kiwi_description import KiwiDescription
from kiwi_keg.utils import KegUtils
from kiwi_keg import template_functions
from kiwi_keg.exceptions import KegError

from jinja2.exceptions import TemplateNotFound

log = logging.getLogger('keg')


class KegGenerator:
    """
    Class for creating a KIWI image description from Keg Templates

    :param object image_definition: Instance of KegImageDefinition
    :param str dest_dir: Destination directory
    """
    def __init__(
        self, image_definition: KegImageDefinition, dest_dir: str
    ):
        if not os.path.isdir(dest_dir):
            raise KegError(
                'Given destination directory: {target} does not exist'.format(
                    target=repr(dest_dir)
                )
            )
        self.kiwi_description: str = os.path.join(
            dest_dir, 'config.kiwi'
        )
        self.kiwi_config_script: str = os.path.join(
            dest_dir, 'config.sh'
        )
        self.kiwi_images_script: str = os.path.join(
            dest_dir, 'images.sh'
        )
        self.image_definition: KegImageDefinition = image_definition
        self.description_schemas = os.path.join(
            image_definition.recipes_root, 'schemas'
        )
        self.dest_dir: str = dest_dir
        self.env = Environment(
            loader=FileSystemLoader(self.description_schemas)
        )
        self.env.globals['keg_funcs'] = template_functions

        self.image_definition.populate()

        self.image_schema: Optional[str] = self.image_definition.data.get('schema')
        if not self.image_schema:
            raise KegError(
                'No KIWI schema configured in image definition'
            )
        log.info(
            'Using KIWI schema: {keg_schema}'.format(
                keg_schema=self.image_schema
            )
        )

    def create_kiwi_description(self, override: bool = False) -> None:
        """
        Creates KIWI config.xml from a KegImageDefinition.

        :param bool override:
            Override destination contents, default is: False
        """
        self._check_file(self.kiwi_description, override)

        kiwi_template = self._read_template(
            '{}.kiwi.templ'.format(self.image_schema)
        )
        kiwi_document = kiwi_template.render(
            data=self.image_definition.data
        )
        with open(self.kiwi_description, 'w') as kiwi_config:
            kiwi_config.write(kiwi_document)

    def validate_kiwi_description(self) -> None:
        kiwi = KiwiDescription(self.kiwi_description)
        kiwi.validate_description()

    def format_kiwi_description(self, markup: str = 'xml') -> None:
        supported_markup_languages = ['xml', 'yaml']
        kiwi = KiwiDescription(self.kiwi_description)
        if markup not in supported_markup_languages:
            raise KegError(
                'Unsupported markup type: {name}'.format(name=markup)
            )
        log.info(
            'Formatting Keg KIWI description to installed KIWI schema'
        )
        log.info(
            f'--> Writing description in {markup!r} markup'
        )
        if markup == 'xml':
            kiwi.create_XML_description(self.kiwi_description)
        if markup == 'yaml':
            kiwi.create_YAML_description(self.kiwi_description)

    def create_custom_scripts(self, override: bool = False):
        """
        Creates custom KIWI config.sh/images.sh script(s) from a
        KegImageDefinition.
        :param bool override:
            Override destination contents, default is: False
        """
        script_lib = KegUtils.load_scripts(
            self.image_definition.data_roots, 'scripts',
            self.image_definition.data.get('include-paths')
        )

        if self._has_script_data('config_script'):
            self._check_file(self.kiwi_config_script, override)
            config_template = self._read_template(
                'config.sh.templ'
            )
            config_sh = config_template.render(
                data=self.image_definition.data, scripts=script_lib
            )
            with open(self.kiwi_config_script, 'w') as custom_script:
                custom_script.write(config_sh)

        if self._has_script_data('image_script'):
            self._check_file(self.kiwi_images_script, override)
            images_template = self._read_template(
                'images.sh.templ'
            )
            images_sh = images_template.render(
                data=self.image_definition.data, scripts=script_lib
            )
            with open(self.kiwi_images_script, 'w') as custom_script:
                custom_script.write(images_sh)

    def create_overlays(self, disable_root_tar: bool = False) -> None:
        """
        Copy all the files and the overlay tree structure from overlays section under root inside destination directory.

        :param: bool tarball:
            Flag to create tarball
        """
        has_overlays = False
        if 'profiles' in self.image_definition.data:
            for profile_name, profile_data in self.image_definition.data['profiles'].items():
                if 'overlayfiles' in profile_data:
                    has_overlays = True
                    overlay_files_paths = profile_data['overlayfiles']
                    tarball_data: dict = {}
                    for _, overlay_content in overlay_files_paths.items():
                        overlay_dest_dir = ''
                        if 'name' in overlay_content.keys():
                            overlay_dest_dir = os.path.join(self.dest_dir, overlay_content.get('name'))
                        elif profile_name == 'common':
                            overlay_dest_dir = os.path.join(self.dest_dir, 'root')
                        else:
                            overlay_dest_dir = os.path.join(self.dest_dir, profile_name)

                        overlay_name = os.path.basename(overlay_dest_dir)
                        for overlay_path in overlay_content.get('include'):
                            overlay_full_path = os.path.join(
                                self.image_definition.overlay_root,
                                overlay_path
                            )
                            # loop all the file paths of overlay sub directory 'overlay_path'
                            for name in KegUtils.get_all_files(overlay_full_path):
                                rel_path = os.path.relpath(name, overlay_full_path)
                                new_dir = os.path.dirname(rel_path)
                                if new_dir:
                                    new_dir = os.path.join(overlay_dest_dir, new_dir)
                                    os.makedirs(new_dir, exist_ok=True)
                                dest_file = os.path.join(overlay_dest_dir, rel_path)
                                shutil.copy(name, dest_file)

                        tarball_data[overlay_name] = {}
                        tarball_data[overlay_name] = overlay_dest_dir

                    for overlay_name, overlay_dest_dir in tarball_data.items():
                        self._create_tarball(
                            disable_root_tar,
                            overlay_name,
                            overlay_dest_dir
                        )
                        if (overlay_name == 'root' and not disable_root_tar) or overlay_name != 'root':
                            shutil.rmtree(overlay_dest_dir)
                        self._update_config_kiwi(
                            '{}.tar.gz'.format(overlay_name),
                            overlay_dest_dir
                        )

        if not has_overlays:
            log.warn(
                'Attempt to create a tarball or an overlay tree but '
                'not overlay paths were provided.'
            )

    def _create_tarball(self, disable_root_tar, overlay_name, dest_dir):
        overlay_tarball_name = '{}.tar.gz'.format(overlay_name)
        tarball_dir = os.path.join(self.dest_dir, overlay_tarball_name)
        if (overlay_name == 'root' and not disable_root_tar) or overlay_name != 'root':
            with tarfile.open(tarball_dir, 'w:gz') as tar:
                for overlay_dir in os.scandir(dest_dir):
                    tar.add(
                        overlay_dir.path,
                        arcname=overlay_dir.name
                    )

    def _update_config_kiwi(self, archive_name, dest_dir):
        if 'root' != archive_name.partition('.')[0]:
            if os.path.exists(dest_dir) and os.path.exists(self.kiwi_description):
                etree_parser = etree.XMLParser(remove_blank_text=True)
                kiwi_xml = etree.parse(self.kiwi_description, parser=etree_parser)
                kiwi_root = kiwi_xml.getroot()

                image_element = kiwi_root.find('.//packages[@type="image"]')

                archive_element = etree.SubElement(image_element, 'archive')
                archive_element.attrib['name'] = archive_name
                tree = etree.ElementTree(kiwi_root)
                tree.write(
                    self.kiwi_description,
                    encoding="utf-8",
                    xml_declaration=True,
                    pretty_print=True
                )

    def _has_script_data(self, script_key):
        profiles = self.image_definition.data.get('profiles')
        for profile in profiles.values():
            config = profile.get('config')
            if config and config.get(script_key):
                return True

    @staticmethod
    def _check_file(filename, override):
        if not override and os.path.exists(filename):
            raise KegError(
                '{target} exists, use force to overwrite.'.format(
                    target=filename
                )
            )

    def _read_template(self, template_name):
        try:
            return self.env.get_template(
                template_name
            )
        except TemplateNotFound:
            raise KegError(
                'Template {name} not found in: {location}'.format(
                    name=repr(template_name),
                    location=self.description_schemas
                )
            )
