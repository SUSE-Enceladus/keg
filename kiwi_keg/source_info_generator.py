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
import logging
import os

from kiwi_keg.image_definition import KegImageDefinition
from kiwi_keg import dict_utils
from kiwi_keg import file_utils
from kiwi_keg import script_utils
from kiwi_keg.exceptions import KegError
from kiwi_keg.annotated_mapping import AnnotatedMapping

log = logging.getLogger('keg')


class SourceInfoGenerator:
    """
    Class for creating a source info files from image definition

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
        self.image_definition: KegImageDefinition = image_definition
        self.dest_dir: str = dest_dir
        self.internal_toplevel_keys = ['archive', 'archives', 'generator', 'timestamp', 'image_source_path']

    def write_source_info(self, overwrite: bool = False):
        """
        Write source info files for use with 'git log'

        :param bool overwrite: Overwrite any existing files
        """
        profiles = self.image_definition.data['image'].get('profiles', {}).get('profile')
        if not profiles:
            src_info = self._get_mapping_sources(self.image_definition.data, profile=None, skip_keys=self.internal_toplevel_keys)
            src_info += self._get_script_sources()
            src_info += self._get_archive_sources()
            with self._open_source_info_file('log_sources', overwrite) as outf:
                for r in self.image_definition.recipes_roots:
                    outf.write('root:{}\n'.format(r))
                outf.write('\n'.join(src_info))
                outf.write('\n')
        else:
            profile_names = [x['_attributes']['name'] for x in profiles]
            for profile_name in profile_names:
                src_info = self._get_mapping_sources(self.image_definition.data, profile_name, skip_keys=self.internal_toplevel_keys)
                src_info += self._get_script_sources(profile_name)
                src_info += self._get_archive_sources(profile_name)
                with self._open_source_info_file(
                    'log_sources_{}'.format(profile_name), overwrite
                ) as outf:
                    for r in self.image_definition.recipes_roots:
                        outf.write('root:{}\n'.format(r))
                    outf.write('\n'.join(src_info))
                    outf.write('\n')

    def _open_source_info_file(self, fname, overwrite):
        fpath = os.path.join(self.dest_dir, fname)
        file_utils.raise_on_file_exists(fpath, overwrite)
        fobj = open(fpath, 'w')
        return fobj

    def _get_mapping_sources(self, data, profile=None, skip_keys=[]):
        src_info: list = []
        if not hasattr(data, '__iter__') or isinstance(data, str):
            return []
        if not isinstance(data, AnnotatedMapping):
            for item in data:
                src_info += self._get_mapping_sources(item, profile)
        else:
            profiles = self._get_profiles_attrib(data)
            if profiles and profile not in profiles:
                return []
            for key, value in data.items():
                if key in skip_keys:
                    continue
                if key == 'profile' and isinstance(value, list):
                    # special case for image:profiles; select only matching ones
                    for item in value:
                        item_name = dict_utils.get_attribute(item, 'name')
                        if item_name == profile:
                            src_info += self._get_mapping_sources(item)
                elif isinstance(value, list):
                    # We can't simply add the source of the list as one block,
                    # because it may contain keys included from other sources,
                    # and also profile specific attributes.
                    if all(isinstance(i, AnnotatedMapping) for i in value):
                        src_info.append(self._get_key_def_source(key, data))
                        src_info += self._get_mapping_sources(value, profile)
                    else:
                        src_info.append(self._get_key_sources(key, data))
                elif isinstance(value, AnnotatedMapping):
                    src_info.append(self._get_key_def_source(key, data))
                    src_info += self._get_mapping_sources(value, profile)
                else:
                    src_info.append(self._get_key_sources(key, data))
            # keys may be deleted when merging, but info is preserved with __deleted_ prefix
            for key in [x for x in data.all_keys() if x.startswith('__deleted_')]:
                orig_key = key[10:]
                if orig_key not in data.keys():
                    src_info.append(self._get_key_sources(orig_key, data))
        return src_info

    def _get_key_sources(self, key, data):
        src = data.get('__{}_source__'.format(key))
        start = data.get('__{}_line_start__'.format(key))
        end = data.get('__{}_line_end__'.format(key))
        if src and start and end:
            return 'range:{}:{}:{}'.format(start, end, src)
        else:
            log.warning('Source information for key {} missing or incomplete'.format(key))
            return ''

    def _get_key_def_source(self, key, data):
        src = data.get('__{}_source__'.format(key))
        start = data.get('__{}_line_start__'.format(key))
        if src and start:
            return 'range:{}:{}:{}'.format(start, start, src)
        else:
            log.warning('Source information for key {} missing or incomplete'.format(key))
            return ''

    def _get_profiles_attrib(self, data):
        if not isinstance(data, AnnotatedMapping):  # pragma: no cover
            return [None]
        profiles_attr = data.get('profiles')
        if isinstance(profiles_attr, AnnotatedMapping):
            # special case for image:profiles node; return None to avoid skipping image def
            return None
        if not profiles_attr:
            profiles_attr = dict_utils.get_attribute(data, 'profiles')
        return profiles_attr

    def _get_archive_profiles(self, archive_name):
        profiles = []
        for pkg_sect in self.image_definition.data['image']['packages']:
            archives = pkg_sect.get('archive', [])
            for archive_sect in archives:
                if dict_utils.get_attribute(archive_sect, 'name') == archive_name:
                    profiles += dict_utils.get_attribute(pkg_sect, 'profiles', [])
        return profiles

    def _get_archive_sources(self, profile=None):
        src_info: list = []
        for archive in self.image_definition.data.get('archive', []):
            if profile:
                profiles = self._get_archive_profiles(archive['name'])
                if profiles and profile not in profiles:
                    continue
            src_info += self._get_mapping_sources(archive)
            src_info += self.image_definition.data['archives'].get(archive['name'], [])
        return src_info

    def _get_script_sources(self, profile=''):
        src_info: list = []
        script_dirs = [
            os.path.join(x, 'scripts') for x in self.image_definition.data_roots
            if os.path.exists(os.path.join(x, 'scripts'))
        ]
        for config_sect in self.image_definition.data.get('config', []):
            profiles = self._get_profiles_attrib(config_sect)
            if profiles and profile not in profiles:
                continue
            for ns, scriptlets in config_sect.get('scripts', {}).items():
                for scriptlet in scriptlets:
                    src_info += [script_utils.get_script_path(script_dirs, scriptlet)]
        return src_info
