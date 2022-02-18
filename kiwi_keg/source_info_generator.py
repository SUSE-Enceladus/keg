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
import os

from kiwi_keg.image_definition import KegImageDefinition
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

    """
    Write source info files for use with 'git log'

    :param bool overwrite: Overwrite any existing files
    """
    def write_source_info(self, overwrite: bool = False):
        profiles = self.image_definition.data['profiles']
        if list(profiles.keys()) == ['common']:
            with self._open_source_info_file('log_sources', overwrite) as outf:
                for r in self.image_definition.recipes_roots:
                    outf.write('root:{}\n'.format(r))
                outf.write(self._get_source_info_root())
                outf.write('\n')
                outf.write(self._get_source_info_profile('common'))
                outf.write('\n')
        else:
            for profile_name in profiles:
                if profile_name == 'common':
                    continue
                if profiles[profile_name].get('base_profile'):
                    continue
                top_src_info = self._get_source_info_root()
                base_src_info = self._get_source_info_profile(profile_name)
                nested_profiles = profiles[profile_name].get('nested_profiles')
                if nested_profiles:
                    for nested_profile in nested_profiles:
                        with self._open_source_info_file(
                            'log_sources_{}'.format(nested_profile), overwrite
                        ) as outf:
                            for r in self.image_definition.recipes_roots:
                                outf.write('root:{}\n'.format(r))
                            outf.write(top_src_info)
                            outf.write('\n')
                            outf.write(base_src_info)
                            outf.write('\n')
                            outf.write(self._get_source_info_profile(nested_profile))
                            outf.write('\n')
                else:
                    with self._open_source_info_file(
                        'log_sources_{}'.format(profile_name), overwrite
                    ) as outf:
                        for r in self.image_definition.recipes_roots:
                            outf.write('root:{}\n'.format(r))
                        outf.write(top_src_info)
                        outf.write('\n')
                        outf.write(base_src_info)
                        outf.write('\n')

    def _open_source_info_file(self, fname, overwrite):
        fpath = os.path.join(self.dest_dir, fname)
        file_utils.raise_on_file_exists(fpath, overwrite)
        fobj = open(fpath, 'w')
        return fobj

    def _get_source_info_root(self):
        src_info: list = []
        src_info = self._get_mapping_sources(self.image_definition.data, ['profiles'])
        return '\n'.join(src_info)

    def _get_source_info_profile(self, profile_name):
        src_info: list = []
        if profile_name not in self.image_definition.data['profiles'].keys():
            raise KegError('Source info for nonexistent profile {} requested'.format(profile_name))
        common_profile = self.image_definition.data['profiles'].get('common')
        if common_profile:
            src_info = self._get_mapping_sources(common_profile)
            src_info += self._get_script_sources(common_profile)
        if profile_name != 'common':
            src_info += self._get_mapping_sources(
                self.image_definition.data['profiles'][profile_name]
            )
            src_info += self._get_script_sources(
                self.image_definition.data['profiles'][profile_name]
            )
        return '\n'.join(src_info)

    def _get_mapping_sources(self, mapping, skip_keys=[]):
        src_info: list = []
        # skip internal keys to avoid warning
        skip_keys += ['generator', 'timestamp', 'image source path',
                      'archives', 'nested_profiles', 'base_profile']
        if not isinstance(mapping, AnnotatedMapping):
            raise KegError('_get_source_info: Object is not AnnotatedMapping: {}'.format(mapping))
        for key, value in mapping.items():
            if key in skip_keys:
                continue
            if isinstance(value, AnnotatedMapping):
                src_info += self._get_mapping_sources(value)
            else:
                if key == 'archive':
                    src_info += self._get_archive_sources(value)
                else:
                    src = mapping.get('__{}_source__'.format(key))
                    start = mapping.get('__{}_line_start__'.format(key))
                    end = mapping.get('__{}_line_end__'.format(key))
                    if src and start and end:
                        src_info.append('range:{}:{}:{}'.format(start, end, src))
                    else:
                        log.warning('Source information for key {} missing or incomplete'.format(key))
        return src_info

    def _get_archive_sources(self, archives: list):
        src_info: list = []
        try:
            for archive in archives:
                archive_name = archive['name'].split('.')[0]
                src_info += self.image_definition.data['archives'][archive_name]
        except Exception as err:
            log.warning('Error while looking up archive sources ({})'.format(err))
        return src_info

    def _get_script_sources(self, profile):
        try:
            src_info: list = []
            script_dirs = [
                os.path.join(x, 'scripts') for x in self.image_definition.data_roots
                if os.path.exists(os.path.join(x, 'scripts'))
            ]
            scripts = profile['config']['scripts']
            for ns, scriptlets in scripts.items():
                for scriptlet in scriptlets:
                    src_info += [script_utils.get_script_path(script_dirs, scriptlet)]
        except KeyError:
            pass
        return src_info
