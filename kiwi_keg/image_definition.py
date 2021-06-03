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
from typing import (
    List, Dict, Optional
)
from datetime import (
    datetime, timezone
)

# project
from kiwi_keg import script_utils
from kiwi_keg import file_utils
from kiwi_keg import version
from kiwi_keg.exceptions import KegError


class KegImageDefinition:
    """
    Class for constructing a keg image definition from recipes
    """
    def __init__(
        self,
        image_name: str,
        recipes_root: str,
        data_roots: List[str] = [],
        archive_ext: str = 'tar.gz'
    ):
        """
        Init ImageDefintion with image_name and recipes root path
        """
        self._data: Dict = {}
        self._recipes_root = recipes_root
        self._image_name = image_name
        self._image_root = os.path.join(recipes_root, 'images')
        self._data_roots = [os.path.join(recipes_root, 'data')]
        self._overlay_root = os.path.join(recipes_root, 'data', 'overlayfiles')
        self._archive_ext = archive_ext
        self._config_script = None
        self._images_script = None
        if data_roots:
            self._data_roots += data_roots
        if not os.path.isdir(recipes_root):
            raise KegError(
                'Recipes Root: {root} does not exist'.format(
                    root=recipes_root
                )
            )

    @property
    def data(self) -> Dict:
        return self._data

    @property
    def recipes_root(self) -> str:
        return self._recipes_root

    @property
    def data_roots(self) -> List[str]:
        return self._data_roots

    @property
    def image_name(self) -> str:
        return self._image_name

    @property
    def image_root(self) -> str:
        return self._image_root

    @property
    def archives(self) -> Optional[Dict]:
        return self._data.get('archives')

    @property
    def config_script(self) -> Optional[str]:
        return self._config_script

    @property
    def images_script(self) -> Optional[str]:
        return self._images_script

    def populate(self) -> None:
        """
        Parse recipes data and construct wanted image definition
        """
        utc_now = datetime.now(timezone.utc)
        utc_now_str = utc_now.strftime("%Y-%m-%d %H:%M:%S")
        self._data = {
            'generator': 'keg {}'.format(version.__version__),
            'timestamp': '{}'.format(utc_now_str),
            'image source path': '{}'.format(self.image_name),
            'archives': {}
        }
        try:
            self._data.update(
                file_utils.get_recipes(
                    [self.image_root], [self.image_name]
                )
            )
        except Exception as issue:
            raise KegError(
                'Error parsing image data: {error}'.format(error=issue)
            )

        self._update_profiles(self._data.get('include-paths'))
        self._generate_config_scripts()
        self._generate_overlay_info()

    def _update_profiles(self, include_paths):
        if 'profiles' in self._data:
            for profile_name, profile_data in self._data['profiles'].items():
                profile: Dict = {}
                for item, value in profile_data.items():
                    if item == 'include':
                        file_utils.rmerge(
                            file_utils.get_recipes(
                                self.data_roots,
                                value,
                                include_paths
                            ),
                            profile
                        )
                    else:
                        file_utils.rmerge({item: value}, profile_data)
                self._data['profiles'][profile_name].update(profile)

    def _generate_config_scripts(self):
        script_dirs = [
            os.path.join(x, 'scripts') for x in self._data_roots
            if os.path.exists(os.path.join(x, 'scripts'))
        ]
        self._config_script = script_utils.get_config_script(
            self._data['profiles'], 'config', script_dirs
        )
        self._images_script = script_utils.get_config_script(
            self._data['profiles'], 'setup', script_dirs
        )

    def _generate_overlay_info(self):
        for profile_name, profile_data in self._data['profiles'].items():
            if not profile_data.get('overlayfiles'):
                continue
            archive_list = []

            if profile_name == 'common':
                default_archive_name = 'root'
            else:
                default_archive_name = profile_name
                archive_list.append({'name': '{}.{}'.format(default_archive_name, self._archive_ext)})

            for namespace, content in profile_data['overlayfiles'].items():
                archive_name = content.get('archivename')
                if archive_name:
                    archive_list.append({'name': '{}.{}'.format(archive_name, self._archive_ext)})
                else:
                    archive_name = default_archive_name
                for inc in content['include']:
                    self._add_dir_to_archive(archive_name, inc)

            self._add_archive_tag(self._data['profiles'][profile_name], archive_list)

    def _add_archive_tag(self, dict_node, archive_list):
        if archive_list:
            file_utils.rmerge(
                {
                    'packages': {
                        'image': {
                            'archive': archive_list
                        }
                    }
                },
                dict_node
            )

    def _add_dir_to_archive(self, archive_name, overlay_module_name):
        src_dir = None
        for data_root in self._data_roots:
            comp_dir = os.path.join(data_root, 'overlayfiles', overlay_module_name)
            if os.path.exists(comp_dir):
                src_dir = comp_dir
        if not src_dir:
            raise KegError('No such overlay files module "{}"'.format(overlay_module_name))
        if not self._data['archives'].get(archive_name):
            self._data['archives'][archive_name] = []
        self._data['archives'][archive_name].append(src_dir)
