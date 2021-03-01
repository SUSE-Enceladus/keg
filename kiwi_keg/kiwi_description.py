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
import os
import shutil
import logging

# from KIWI
from kiwi.xml_description import XMLDescription

# from KEG
from kiwi_keg.exceptions import (
    KegDescriptionNotFound,
    KegKiwiValidationError,
    KegKiwiDescriptionError
)


class KiwiDescription:
    """
    **KIWI Image description validation/translation**
    """
    def __init__(self, description_file: str):
        """
        :param str description_file: keg created kiwi file
        """
        if not os.path.isfile(description_file):
            raise KegDescriptionNotFound(
                'No such file {0}'.format(description_file)
            )
        kiwi_logger = logging.getLogger('kiwi')
        kiwi_logger.disabled = True
        self.description_file = description_file

    def validate_description(self) -> XMLDescription:
        try:
            description = XMLDescription(self.description_file)
            description.load()
        except Exception as issue:
            raise KegKiwiValidationError(
                'Failed to validate image description: {0}'.format(issue)
            )
        return description

    def create_YAML_description(self, output_file: str):
        self._create_description(output_file, 'yaml')

    def create_XML_description(self, output_file: str):
        self._create_description(output_file, 'xml')

    def _create_description(self, output_file, markup):
        description = self.validate_description()
        try:
            if markup == 'xml':
                document = description.markup.get_xml_description()
            else:
                document = description.markup.get_yaml_description()
            shutil.copy(document, output_file)
        except Exception as issue:
            raise KegKiwiDescriptionError(
                'Failed to create image description: {0}'.format(issue)
            )
