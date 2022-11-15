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
from typing import (
    List, Optional
)
from datetime import (
    datetime, timezone
)
from schema import SchemaError

# project
from kiwi_keg import dict_utils
from kiwi_keg import file_utils
from kiwi_keg import script_utils
from kiwi_keg import version
from kiwi_keg.exceptions import KegDataError
from kiwi_keg.annotated_mapping import AnnotatedMapping, keg_dict, keg_dict_type
from kiwi_keg.image_schema import ImageSchema


class KegImageDefinition:
    """
    Class for constructing a keg image definition from recipes
    """
    def __init__(
        self,
        image_name: str,
        recipes_roots: List[str],
        image_version: Optional[str] = None,
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
            'image_source_path': '{}'.format(self.image_name),
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

        try:
            self._expand_includes(self._data)
            if self._image_version:
                self._data['image']['preferences'][0]['version'] = self._image_version
            ImageSchema().validate(self._data)
            self._generate_config_scripts()
            self._generate_overlay_info()
        except SchemaError as err:
            raise KegDataError('Image definition malformed: {}'.format(err))
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

    def _expand_includes(self, data, key=None):
        if not hasattr(data, '__iter__') or isinstance(data, str):
            return
        if isinstance(data, list):
            for item in data:
                self._expand_includes(item, key)
            return
        if '_include' in data.keys():
            self._expand_include(data, key)
        for subkey, value in data.items():
            self._expand_includes(value, subkey)

    def _expand_include(self, node, key):
        include_paths = self._data.get('include-paths')
        includes = node.get('_include')
        if isinstance(includes, str):
            includes = [includes]
        if includes:
            incl_dict = file_utils.get_recipes(
                self.data_roots,
                includes,
                include_paths,
                self._track_sources
            )
            if incl_dict.get(key):
                dict_utils.rmerge(
                    incl_dict[key],
                    node
                )
            del node['_include']
            if isinstance(node, AnnotatedMapping):
                # preserve source info
                node['__deleted__include'] = {}

    def _generate_config_scripts(self):
        script_dirs = [
            os.path.join(x, 'scripts') for x in self._data_roots
            if os.path.exists(os.path.join(x, 'scripts'))
        ]
        if self._data.get('config'):
            self._config_script = script_utils.get_config_script(
                self._data['config'], script_dirs
            )
        if self._data.get('setup'):
            self._images_script = script_utils.get_config_script(
                self._data['setup'], script_dirs
            )

    def _generate_overlay_info(self):
        for archive in self._data.get('archive', []):
            for ns, data in archive.items():
                if ns == 'name':
                    continue
                for overlay in data['_include_overlays']:
                    self._add_dir_to_archive(archive['name'], overlay)

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
