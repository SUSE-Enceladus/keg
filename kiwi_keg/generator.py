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
from kiwi_keg import (
    template_functions, utils
)
from kiwi_keg.exceptions import KegError

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

    def create_kiwi_description(
        self, markup: str = 'xml', override: bool = False
    ):
        """
        Creates KIWI config.xml from a KegImageDefinition.

        :param bool override:
            Override destination contents, default is: False
        """
        outfile = os.path.join(self.dest_dir, 'config.kiwi')
        self._validate_outfile(outfile, override)

        kiwi_template = self.env.get_template(
            '{}.kiwi.templ'.format(self.image_definition.data['schema'])
        )
        kiwi_document = kiwi_template.render(
            data=self.image_definition.data
        )
        with open(outfile, 'w') as kiwi_config:
            kiwi_config.write(kiwi_document)
        kiwi = KiwiDescription(outfile)
        if markup == 'xml':
            kiwi.create_XML_description(outfile)
        elif markup == 'yaml':
            kiwi.create_YAML_description(outfile)
        else:
            raise KegError(
                'Unsupported markup type: {name}'.format(name=markup)
            )

    def create_custom_scripts(self, override: bool = False):
        """
        Creates custom KIWI config.sh script from a KegImageDefinition.

        :param bool override:
            Override destination contents, default is: False
        """
        outfile = os.path.join(self.dest_dir, 'config.sh')
        self._validate_outfile(outfile, override)

        script_lib = utils.load_scripts(
            'scripts', self.image_definition.data_roots,
            self.image_definition.data['include-paths']
        )
        config_template = self.env.get_template(
            '{}.config.sh.templ'.format(self.image_definition.data['schema'])
        )
        config_sh = config_template.render(
            data=self.image_definition.data, scripts=script_lib
        )
        with open(outfile, 'w') as custom_script:
            custom_script.write(config_sh)

    @staticmethod
    def _validate_outfile(outfile, override):
        if not override and os.path.exists(outfile):
            raise KegError(
                '{target} exists, use force to overwrite.'.format(
                    target=outfile
                )
            )
