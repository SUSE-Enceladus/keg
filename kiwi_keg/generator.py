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
from jinja2 import Environment, FileSystemLoader, ChoiceLoader
from typing import Optional
import os
import shutil
import tarfile
from collections import OrderedDict
from xml.sax.saxutils import XMLGenerator
from xml.sax.xmlreader import AttributesImpl

from kiwi_keg import dict_utils
from kiwi_keg import file_utils
from kiwi_keg.image_definition import KegImageDefinition
from kiwi_keg.kiwi_description import KiwiDescription
from kiwi_keg.exceptions import (
    KegError,
    KegDataError
)

from jinja2.exceptions import TemplateNotFound

log = logging.getLogger('keg')


class KegGenerator:
    """
    Class for creating a KIWI image description from Keg Templates

    :param object image_definition: Instance of KegImageDefinition
    :param str dest_dir: Destination directory
    """
    def __init__(
            self, image_definition: KegImageDefinition, dest_dir: str, archs: list = []
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
        self.dest_dir: str = dest_dir
        self.archs = archs
        loaders = []
        for root in reversed(image_definition.recipes_roots):
            loaders.append(FileSystemLoader(os.path.join(root, 'schemas')))
        self.env = Environment(
            loader=ChoiceLoader(loaders)
        )

        self.image_definition.populate()

        self.image_schema: Optional[str] = self.image_definition.data.get('schema')

    def create_kiwi_description(self, overwrite: bool = False) -> None:
        file_utils.raise_on_file_exists(self.kiwi_description, overwrite)
        if not self.image_schema:
            self.create_xml_description()
        else:
            log.info(
                'Using KIWI schema: {keg_schema}'.format(
                    keg_schema=self.image_schema
                )
            )
            self.create_template_description()

    def create_template_description(self) -> None:
        """
        Creates KIWI config.xml from a KegImageDefinition.

        :param bool overwrite:
            Override destination contents, default is: False
        """
        if not self.image_schema:
            raise KegError('No template schema defined')

        kiwi_template = self._read_template(
            '{}.kiwi.templ'.format(self.image_schema)
        )
        kiwi_document = kiwi_template.render(
            data=self.image_definition.data
        )
        with open(self.kiwi_description, 'w') as kiwi_config:
            kiwi_config.write(kiwi_document)
            kiwi_config.write('\n')

    def create_xml_description(self) -> None:
        with open(self.kiwi_description, 'w') as kiwi_config:
            content_handler = ContentGenerator(out=kiwi_config, encoding='utf-8', short_empty_elements=True)
            content_handler.startDocument()
            content_handler.ignorableWhitespace('\n')
            content_handler.comment('Image description generated by keg on {}'.format(self.image_definition.data['timestamp']))
            content_handler.ignorableWhitespace('\n')
            obs_comments = self.image_definition.data.get('image-config-comments')
            if obs_comments:
                content_handler.ignorableWhitespace('\n')
                for comment in obs_comments.values():
                    content_handler.comment(comment)
                    content_handler.ignorableWhitespace('\n')
            if self.archs:
                arch_comment = 'OBS-ExclusiveArch: {}'.format(
                    ' '.join(self.archs)
                )
                content_handler.comment(arch_comment)
                content_handler.ignorableWhitespace('\n')
            content_handler.ignorableWhitespace('\n')
            filter_arg = {}
            if self.archs:
                filter_arg = {'arch': self.archs}
            self._create_xml_node('image', self.image_definition.data['image'], content_handler, filter_attributes=filter_arg)
            content_handler.endDocument()

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
            file_utils.raise_on_file_exists(self.kiwi_config_script, overwrite)
            self._write_custom_script(
                self.kiwi_config_script,
                self.image_definition.config_script,
                'config_sh_header.templ'
            )

        if self.image_definition.images_script:
            log.debug('Generating images.sh')
            file_utils.raise_on_file_exists(self.kiwi_images_script, overwrite)
            self._write_custom_script(
                self.kiwi_images_script,
                self.image_definition.images_script,
                'images_sh_header.templ'
            )

    def create_overlays(self,
                        disable_root_tar: bool = False,
                        overwrite: bool = False
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
            if archive_name.startswith('root.') and disable_root_tar:
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
                    archive_name
                )
                compression = archive_name.split('.')[-1]
                with tarfile.open(overlay_tarball_path, 'w:{}'.format(compression)) as tar:
                    for base_dir in dir_list:
                        self._add_dir_to_tar(tar, base_dir)

    def create_multibuild_file(self, overwrite: bool = False):
        profiles = self.image_definition.data['image'].get('profiles', {}).get('profile')
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
                    profile_name = dict_utils.get_attribute(profile, 'name')
                    if profile_name:
                        mbuild_obj.write('    <flavor>{}</flavor>\n'.format(profile_name))
                mbuild_obj.write('</multibuild>\n')

    @staticmethod
    def _tarinfo_set_root(tarinfo):
        tarinfo.uid = tarinfo.gid = 0
        tarinfo.uname = tarinfo.gname = 'root'
        return tarinfo

    def _add_dir_to_tar(self, tar, src_dir, subdir=''):
        entries = os.scandir(os.path.join(src_dir, subdir))
        for entry in entries:
            if os.path.join(subdir, entry.name) in [x.rstrip('/') for x in tar.getnames()]:
                if entry.is_dir():
                    self._add_dir_to_tar(tar, src_dir, os.path.join(subdir, entry.name))
                else:
                    log.warning('{fname} included twice in {archive}'.format(
                        fname=os.path.join(subdir, entry.name),
                        archive=os.path.basename(tar.name))
                    )
            else:
                tar.add(name=entry.path, arcname=os.path.join(subdir, entry.name), filter=self._tarinfo_set_root)

    def _copytree(self, src_dir, dest_dir):
        for entry in os.walk(src_dir):
            dest_sub = os.path.join(dest_dir, os.path.relpath(entry[0], src_dir))
            os.makedirs(dest_sub, exist_ok=True)
            for file in entry[2]:
                src = os.path.join(entry[0], file)
                shutil.copy(src, dest_sub, follow_symlinks=False)

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
            raise KegDataError(
                'Template {name} not found'.format(
                    name=repr(template_name)
                )
            )

    def _create_xml_node(
            self,
            key,
            value,
            content_handler,
            depth=0,
            indent='    ',
            map_attribute=None,
            filter_attributes={}
    ):
        if not isinstance(value, list):
            value = [value]

        for val in value:
            if val is None:  # pragma: no cover
                continue
            elif isinstance(val, bool):
                val = 'true' if val else 'false'
            if isinstance(val, str) or not hasattr(val, '__iter__'):
                if map_attribute:
                    val = OrderedDict({'_attributes': {map_attribute: val}})
                else:
                    val = OrderedDict((('_text', str(val)),))
            cdata = None
            attr = OrderedDict()
            children = []
            skip_elem = False
            for ik, iv in val.items():
                if ik == '_text':
                    cdata = str(iv)
                    continue
                if ik == '_attributes':
                    for fa, fv in filter_attributes.items():
                        if fa in iv.keys():
                            attrib_val = iv[fa]
                            if isinstance(attrib_val, str):
                                attrib_val = attrib_val.split(',')
                            if not set(fv) & set(attrib_val):
                                skip_elem = True
                    if skip_elem:
                        break
                    attr = NodeAttributes(iv)
                    continue
                if ik.startswith('_comment'):
                    content_handler.ignorableWhitespace(depth * indent)
                    content_handler.comment(str(iv))
                    content_handler.ignorableWhitespace('\n')
                    continue
                if ik == '_map_attribute':
                    map_attribute = str(iv)
                    continue
                if ik.startswith('_') and not ik.startswith('_namespace'):
                    continue
                children.append((ik, iv))

            if not skip_elem and (children or attr or cdata):
                self._create_xml_element(
                    content_handler,
                    key,
                    attr,
                    cdata,
                    children,
                    depth,
                    indent,
                    map_attribute,
                    filter_attributes
                )

    def _create_xml_element(
            self,
            content_handler,
            key,
            attr,
            cdata,
            children,
            depth,
            indent,
            map_attribute,
            filter_attributes
    ):
        child_indent = 0
        content_handler.ignorableWhitespace(depth * indent)
        if key.startswith('_namespace'):
            content_handler.comment(f'begin namespace {key[11:]}')
        else:
            content_handler.startElement(key, attr)
            child_indent = 1
        if children:
            content_handler.ignorableWhitespace('\n')
        for ck, cv in children:
            self._create_xml_node(ck, cv, content_handler, depth + child_indent,
                                  indent, map_attribute, filter_attributes)
        if cdata:
            content_handler.characters(cdata)
        if children:
            content_handler.ignorableWhitespace(depth * indent)
        if key.startswith('_namespace'):
            content_handler.comment(f'end namespace {key[11:]}')
        else:
            content_handler.endElement(key)
        content_handler.ignorableWhitespace('\n')


class ContentGenerator(XMLGenerator):
    def comment(self, text):
        self._finish_pending_start_element()
        self._write('<!-- {} -->'.format(text))


class NodeAttributes(AttributesImpl):
    def __init__(self, attrs):
        self._attrs = {}
        for attr, value in attrs.items():
            if not hasattr(value, '__iter__') or isinstance(value, str):
                self._attrs[attr] = str(value)
            elif isinstance(value, list):
                self._attrs[attr] = ','.join(value)
            else:
                self._attrs[attr] = self._dict_to_string(value)

    def _dict_to_string(self, data):
        valstr = ''
        for key, val in data.items():
            if val:
                valstr += '{space}{key}={value}'.format(
                    space=' ' * (len(valstr) > 0),
                    key=key,
                    value=str(val)
                )
            else:
                valstr += ' ' * (len(valstr) > 0) + key
        return valstr

    def __repr__(self):
        return str(self._attrs)
