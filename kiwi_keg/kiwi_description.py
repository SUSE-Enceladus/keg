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
import os
import shutil
import logging
from typing import Any

# from KIWI
from kiwi.xml_description import XMLDescription

# from KEG
from kiwi_keg.exceptions import (
    KegDescriptionNotFound,
    KegKiwiValidationError,
    KegKiwiDescriptionError
)

log = logging.getLogger('keg')


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
        kiwi_logger: Any = logging.getLogger('kiwi')
        kiwi_logger.setLogLevel(logging.INFO)
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

    def create_YAML_description(self, output_file: str) -> None:
        self._read_YAML_comments()
        self._create_description(output_file, 'yaml')

    def create_XML_description(self, output_file: str) -> None:
        comments = self._read_XML_comments()
        self._create_description(output_file, 'xml')
        if comments:
            # KIWI does not preserve comment blocks after validation.
            # However, for OBS the comments are no comments but effective
            # project config data. Questionable design but we can't
            # influence this and will add back at least the toplevel
            # header comments.
            with open(output_file, 'r') as xml:
                xml_data = xml.read()

            with open(output_file, 'w') as xml:
                xml.write(''.join(comments))
                xml.write(xml_data)

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

    def _read_YAML_comments(self):
        # Currently this method does not translate XML comments to
        # YAML because I think OBS is expecting the comments in XML
        # comment syntax and does not support anything else. If this
        # turns out to be an issue in the future and people start
        # to use YAML markup for KIWI images in OBS this method needs
        # to be adapted
        log.warn(
            'Comments from Keg KIWI description will not be preserved'
        )

    def _read_XML_comments(self):
        comments = []
        multiline_comment = False
        with open(self.description_file, 'r') as keg_description:
            description_lines = keg_description.readlines()

        for comment in description_lines:
            if multiline_comment:
                # within a multiline comment
                comments.append(comment)
                if comment.endswith('-->\n'):
                    multiline_comment = False
            elif comment.startswith('<?'):
                # toplevel XML processing instruction
                comments.append(comment)
            elif comment.startswith('<!--') and comment.endswith('-->\n'):
                # toplevel comment
                comments.append(comment)
            elif comment.startswith('<!--'):
                # toplevel start of multiline comment
                multiline_comment = True
                comments.append(comment)

        log.warn(
            'Inline comments from Keg KIWI description will not be preserved !'
        )
        return comments
