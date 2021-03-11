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
import os

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
        self.kiwi_description = os.path.join(
            dest_dir, 'config.kiwi'
        )
        self.kiwi_config_script = os.path.join(
            dest_dir, 'config.sh'
        )
        self.kiwi_images_script = os.path.join(
            dest_dir, 'images.sh'
        )
        self.image_definition = image_definition
        self.description_schemas = os.path.join(
            image_definition.recipes_root, 'schemas'
        )
        self.dest_dir = dest_dir
        self.env = Environment(
            loader=FileSystemLoader(self.description_schemas)
        )
        self.env.globals['keg_funcs'] = template_functions

        self.image_definition.populate()

        self.image_schema = self.image_definition.data.get('schema')
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
