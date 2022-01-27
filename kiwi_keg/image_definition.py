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
    List, Optional
)
from datetime import (
    datetime, timezone
)

# project
from kiwi_keg import script_utils
from kiwi_keg import file_utils
from kiwi_keg import version
from kiwi_keg.exceptions import KegDataError
from kiwi_keg.annotated_mapping import AnnotatedMapping, keg_dict, keg_dict_type


class KegImageDefinition:
    """
    Class for constructing a keg image definition from recipes
    """
    def __init__(
        self,
        image_name: str,
        recipes_roots: List[str],
        image_version: str = None,
        archive_ext: str = 'tar.gz',
        track_sources: bool = False
    ):
        """
        Init ImageDefintion with image_name and recipes root path
        """
        self._recipes_roots = recipes_roots
        self._image_name = image_name
        self._image_roots = [os.path.join(x, 'images') for x in recipes_roots]
        self._image_version = image_version
        self._data_roots = [os.path.join(x, 'data') for x in recipes_roots]
        self._overlay_roots = [os.path.join(x, 'data', 'overlayfiles') for x in recipes_roots]
        self._archive_ext = archive_ext
        self._track_sources = track_sources
        self._dict_type: keg_dict_type
        self._data: keg_dict
        if self._track_sources:
            self._dict_type = AnnotatedMapping
        else:
            self._dict_type = dict
        self._data = self._dict_type({})
        self._config_script = None
        self._images_script = None
        self._check_recipes_paths_exist()
        self._check_image_path_exists()

    @property
    def data(self) -> keg_dict:
        return self._data

    @property
    def recipes_roots(self) -> List[str]:
        return self._recipes_roots

    @property
    def data_roots(self) -> List[str]:
        return self._data_roots

    @property
    def image_name(self) -> str:
        return self._image_name

    @property
    def image_roots(self) -> List[str]:
        return self._image_roots

    @property
    def archives(self) -> Optional[keg_dict]:
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
        self._data = self._dict_type({
            'generator': 'keg {}'.format(version.__version__),
            'timestamp': '{}'.format(utc_now_str),
            'image source path': '{}'.format(self.image_name),
            'archives': {}
        })
        try:
            img_dict = file_utils.get_recipes(
                self.image_roots, [self.image_name], track_sources=self._track_sources
            )
            self._data.update(img_dict)
        except Exception as issue:
            raise KegDataError(
                'Error parsing image data: {error}'.format(error=issue)
            )

        self._verify_basic_image_structure()
        if self._image_version:
            self._data['image']['version'] = self._image_version

        try:
            self._update_profiles()
            self._generate_config_scripts()
            self._generate_overlay_info()
        except Exception as issue:
            raise KegDataError(
                'Error generating profile data: {error}'.format(error=issue)
            )

    def _check_recipes_paths_exist(self):
        for recipes_root in self._recipes_roots:
            if not os.path.isdir(recipes_root):
                raise KegDataError(
                    'Recipes root "{root}" does not exist'.format(
                        root=recipes_root
                    )
                )

    def _check_image_path_exists(self):
        image_dir_exists = False
        for image_dir in self._image_roots:
            if os.path.isdir(os.path.join(image_dir, self._image_name)):
                image_dir_exists = True
                break
        if not image_dir_exists:
            raise KegDataError(
                'Image source path "{image}" does not exist'.format(
                    image=self._image_name
                )
            )

    def _update_profiles(self):
        include_paths = self._data.get('include-paths')
        if 'profiles' in self._data:
            for profile_name in list(self._data['profiles'].keys()):
                profile = self._dict_type({})
                profile_data = self._data['profiles'][profile_name]
                self._expand_profile_includes(
                    profile_data,
                    profile,
                    include_paths,
                    self._data['profiles'][profile_name]
                )

                # sort nested profiles, otherwise order may not be deterministic
#                nested_profile_names = sorted(list(profile_data.keys()) - ['include', 'description'])
                nested_profile_names = sorted([x for x in profile_data.keys() if x != 'include' and x != 'description'])

                if nested_profile_names:
                    profile['nested_profiles'] = nested_profile_names
                    profile_params = profile.get('profile')
                    if profile_params:
                        # remove parameter section from base profile so it
                        # won't prevent nested profile parameters from being
                        # merged and also so the template does not have to
                        # deal with it
                        del profile['profile']

                    nested_profiles = self._dict_type({})
                    for nested_profile_name in nested_profile_names:
                        nested_profiles[nested_profile_name] = self._dict_type({})
                        nested_profile_data = self._data['profiles'][profile_name][nested_profile_name]
                        nested_profile_data['base_profile'] = profile_name
                        # copy base profile parameters (if any) into nested profile
                        if profile_params:
                            file_utils.rmerge(
                                {'profile': profile_params},
                                nested_profiles[nested_profile_name]
                            )
                        self._expand_profile_includes(
                            nested_profile_data,
                            nested_profiles[nested_profile_name],
                            include_paths,
                            profile
                        )
                    self._data['profiles'].update(nested_profiles)

                self._data['profiles'][profile_name].update(profile)

    def _expand_profile_includes(self, src, dest, include_paths, ref_profile=None):
        if isinstance(src, AnnotatedMapping):
            items = src.all_items()
        else:
            items = src.items()
        for item, value in items:
            if item == 'include':
                profile_dict = file_utils.get_recipes(
                    self.data_roots,
                    value,
                    include_paths,
                    self._track_sources
                )
                file_utils.rmerge(
                    profile_dict,
                    dest,
                    ref_profile
                )
            else:
                file_utils.rmerge({item: value}, dest)

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
                if not content.get('include'):
                    raise KegDataError('overlayfiles namespace {} lacks include secion'.format(namespace))
                for inc in content['include']:
                    self._add_dir_to_archive(archive_name, inc)

            self._add_archive_tag(self._data['profiles'][profile_name], archive_list)

    def _verify_basic_image_structure(self):
        try:
            self._data['image']['name']
            self._data['image']['specification']
            self._data['profiles']
        except KeyError as err:
            raise KegDataError(
                'Image Definition: mandatory key {key} does not exist'.format(
                    key=err
                )
            )

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
            raise KegDataError('No such overlay files module "{}"'.format(overlay_module_name))
        if not self._data['archives'].get(archive_name):
            self._data['archives'][archive_name] = []
        self._data['archives'][archive_name].append(src_dir)
