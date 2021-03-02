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
    List, Dict
)
from datetime import (
    datetime, timezone
)

# project
from kiwi_keg.utils import KegUtils
from kiwi_keg import version
from kiwi_keg.exceptions import KegError


class KegImageDefinition:
    """
    Class for constructing a keg image definition from recipes
    """
    def __init__(
        self, image_name: str, recipes_root: str, data_roots: List[str] = []
    ):
        """
        Init ImageDefintion with image_name and recipes root path
        """
        self._data: Dict = {}
        self._recipes_root = recipes_root
        self._image_name = image_name
        self._image_root = os.path.join(recipes_root, 'images')
        self._data_roots = [os.path.join(recipes_root, 'data')]
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

    def populate(self) -> None:
        """
        Parse recipes data and construct wanted image definition
        """
        utc_now = datetime.now(timezone.utc)
        utc_now_str = utc_now.strftime("%Y-%m-%d %H:%M:%S")
        self._data = {
            'generator': 'keg {}'.format(version.__version__),
            'timestamp': '{}'.format(utc_now_str),
            'image source path': '{}'.format(self._image_name)
        }
        try:
            self._data.update(
                KegUtils.get_recipes(
                    [self._image_root], self._image_name
                )
            )
        except Exception as issue:
            raise KegError(
                'Error parsing image data: {error}'.format(error=issue)
            )

        # load profile sections
        if 'profiles' in self._data:
            self.update_profiles(self._data.get('include-paths'))

        # expand unprofiled contents section (for single build)
        if 'contents' in self._data:
            self.update_contents(self._data.get('include-paths'))

    def update_profiles(self, include_paths):
        for profile_name, profile_data in self._data['profiles'].items():
            profile: Dict = {}
            for item, value in profile_data.items():
                if item == 'include':
                    for inc in value:
                        KegUtils.rmerge(
                            KegUtils.get_recipes(
                                self._data_roots,
                                inc,
                                include_paths
                            ),
                            profile
                        )
                else:
                    KegUtils.rmerge({item: value}, profile_data)
            self._data['profiles'][profile_name].update(profile)

    def update_contents(self, include_paths):
        contents: Dict = {}
        for inc in self._data['contents'].get('include'):
            KegUtils.rmerge(
                KegUtils().get_recipes(
                    self._data_roots,
                    inc,
                    include_paths
                ),
                contents
            )
        self._data['contents'].update(contents)
