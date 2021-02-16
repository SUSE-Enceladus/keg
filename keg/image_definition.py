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
from datetime import datetime, timezone
import os

from keg import version, utils
from keg.exceptions import KegError


class ImageDefinition:
    """Class for constructing a keg image definition from recipes"""

    def __init__(self, image_name, recipes_root, data_roots):
        """Init ImageDefintion with image_name and recipes root path"""
        self._image_name = image_name
        self._image_root = os.path.join(recipes_root, 'images')
        self._data_roots = [os.path.join(recipes_root, 'data')]
        self._data_roots += data_roots

    def populate(self):
        """Parse recipes data and construct wanted image definition"""
        utc_now = datetime.now(timezone.utc)
        utc_now_str = utc_now.strftime("%Y-%m-%d %H:%M:%S")
        self._data = {
            'generator': 'keg {}'.format(version.__version__),
            'timestamp': '{}'.format(utc_now_str),
            'image source path': '{}'.format(self._image_name)
        }
        try:
            self._data.update(
                utils.parse_yaml_tree(self._image_name, [self._image_root])
            )
        except Exception as e:
            raise KegError('Error parsing image data: {}'.format(e))

        include_paths = self._data.get('include-paths')
        # load profile sections
        try:
            for profile_name, profile_data in self._data['profiles'].items():
                profile = {}
                for item, value in profile_data.items():
                    if item == 'include':
                        for inc in value:
                            utils.rmerge(
                                utils.parse_yaml_tree(
                                    inc,
                                    self._data_roots,
                                    include_paths
                                ),
                                profile
                            )
                    else:
                        utils.rmerge({item: value}, profile_data)
                self._data['profiles'][profile_name].update(profile)
        except Exception as e:
            raise KegError('Error parsing profile data: {}'.format(e))

        # expand unprofiled contents section (for single build)
        try:
            if self._data.get('contents'):
                contents = {}
                for inc in self._data['contents']['include']:
                    utils.rmerge(
                        utils.parse_yaml_tree(
                            inc,
                            self._data_roots,
                            include_paths
                        ),
                        contents
                    )
                self._data['contents'].update(contents)
        except Exception as e:
            raise KegError('Error parsing single build data: {}'.format(e))

    def get_data(self):
        return self._data

    def __getitem__(self, key):
        return self._data[key]
