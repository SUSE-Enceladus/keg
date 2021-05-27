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
from typing import Optional
import os
import shutil
import tarfile

from kiwi_keg.image_definition import KegImageDefinition
from kiwi_keg.kiwi_description import KiwiDescription
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

    def create_kiwi_description(self, overwrite: bool = False) -> None:
        """
        Creates KIWI config.xml from a KegImageDefinition.

        :param bool overwrite:
            Override destination contents, default is: False
        """
        self._check_file(self.kiwi_description, overwrite)

        kiwi_template = self._read_template(
            '{}.kiwi.templ'.format(self.image_schema)
        )
        kiwi_document = kiwi_template.render(
            data=self.image_definition.data
        )
        with open(self.kiwi_description, 'w') as kiwi_config:
            kiwi_config.write(kiwi_document)
            kiwi_config.write('\n')

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

    def create_custom_scripts(self, overwrite: bool = False):
        """
        Creates custom KIWI config.sh/images.sh script(s) from a
        KegImageDefinition.
        :param bool overwrite:
            Overwrite destination contents, default is: False
        """
        if self.image_definition.config_script:
            log.debug('Generating config.sh')
            self._check_file(self.kiwi_config_script, overwrite)
            self._write_custom_script(
                self.kiwi_config_script,
                self.image_definition.config_script,
                'config_sh_header.templ'
            )

        if self.image_definition.images_script:
            log.debug('Generating images.sh')
            self._check_file(self.kiwi_images_script, overwrite)
            self._write_custom_script(
                self.kiwi_images_script,
                self.image_definition.images_script,
                'images_sh_header.templ'
            )

    def create_overlays(self,
                        disable_root_tar: bool = False,
                        overwrite: bool = False,
                        compression: str = 'gz',
                        ) -> None:
        """
        Create overlay archives as defined in the 'archives' section of the
        data dictionary.

        :param: bool disable_root_tar:
            Flag to disable packing for root overlay
        :param: bool overwrite:
            Flag to enable overwriting of existing archives or root dir
        :param: str compression:
            Compression to use for packing
        """
        if not self.image_definition.archives:
            return
        for archive_name, dir_list in self.image_definition.archives.items():
            if archive_name == 'root' and disable_root_tar:
                overlay_dest_dir = os.path.join(self.dest_dir, 'root')
                if os.path.exists(overlay_dest_dir):
                    if not overwrite:
                        raise KegError(
                            '{target} exists, use force to overwrite.'.format(
                                target=overlay_dest_dir
                            )
                        )
                    shutil.rmtree(overlay_dest_dir)
                os.makedirs(overlay_dest_dir)
                for base_dir in dir_list:
                    self._copytree(base_dir, overlay_dest_dir)
            else:
                overlay_tarball_path = os.path.join(
                    self.dest_dir,
                    '{}.tar.{}'.format(archive_name, compression)
                )
                with tarfile.open(overlay_tarball_path, 'w:{}'.format(compression)) as tar:
                    for base_dir in dir_list:
                        self._add_dir_to_tar(tar, base_dir)

    def create_multibuild_file(self, overwrite: bool = False):
        profiles = [x for x in self.image_definition.data['profiles'] if x != 'common']
        if profiles:
            mbuild_file = os.path.join(self.dest_dir, '_multibuild')
            if os.path.exists(mbuild_file) and not overwrite:
                raise KegError(
                    '{target} exists, use force to overwrite.'.format(
                        target=mbuild_file
                    )
                )
            with open(mbuild_file, 'w') as mbuild_obj:
                mbuild_obj.write('<multibuild>\n')
                for profile in profiles:
                    mbuild_obj.write('    <flavor>{}</flavor>\n'.format(profile))
                mbuild_obj.write('</multibuild>\n')

    @staticmethod
    def _tarinfo_set_root(tarinfo):
        tarinfo.uid = tarinfo.gid = 0
        tarinfo.uname = tarinfo.gname = 'root'
        return tarinfo

    def _add_dir_to_tar(self, tar, src_dir):
        entries = os.scandir(src_dir)
        for entry in entries:
            tar.add(name=entry.path, arcname=entry.name, filter=self._tarinfo_set_root)

    def _copytree(self, src_dir, dest_dir):
        for entry in os.walk(src_dir):
            dest_sub = os.path.join(dest_dir, os.path.relpath(entry[0], src_dir))
            os.makedirs(dest_sub, exist_ok=True)
            for file in entry[2]:
                src = os.path.join(entry[0], file)
                shutil.copy(src, dest_sub, follow_symlinks=False)

    @staticmethod
    def _check_file(filename, overwrite):
        if not overwrite and os.path.exists(filename):
            raise KegError(
                '{target} exists, use force to overwrite.'.format(
                    target=filename
                )
            )

    def _write_custom_script(self, filename, content, template_name):
        try:
            header_template = self._read_template(template_name)
            header = header_template.render(
                data=self.image_definition.data,
                template_target=header_template
            )
        except KegError:
            log.warning('header template {} missing, using fallback header'.format(template_name))
            header = '#!/bin/bash\n'

        with open(filename, 'w') as custom_script:
            custom_script.write(header)
            custom_script.write('\n')
            custom_script.write(content)

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
