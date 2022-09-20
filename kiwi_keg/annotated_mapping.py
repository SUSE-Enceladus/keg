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
from collections.abc import MutableMapping
from typing import Dict, Type, Union
import pprint


class AnnotatedMapping(MutableMapping):
    def __init__(self, mapping=None):
        if mapping:
            self._mapping = mapping
        else:
            self._mapping = {}

    def __getitem__(self, key):
        return self._mapping[key]

    def __setitem__(self, key, value):
        if isinstance(value, dict):
            self._mapping[key] = type(self)(value)
        else:
            self._mapping[key] = value

    def __delitem__(self, key):
        if key in self:
            del self._mapping[key]

    def __iter__(self):
        for key in self._mapping.keys():
            if not isinstance(key, str) or not key.startswith('__'):
                yield key

    def __len__(self):
        return len(self._mapping)

    def __repr__(self):
        return f"{type(self).__name__}{self._mapping}"

    def __str__(self):
        return f"{self._mapping}"

    def all_items(self):
        for key in self._mapping:
            yield key, self._mapping[key]

    def all_keys(self):
        for key in self._mapping:
            yield key

    def update(self, data):
        if isinstance(data, type(self)):
            self._mapping.update(data._mapping)
        else:
            self._mapping.update(data)

    def to_dict(self):
        d = {}
        for key, value in self.items():
            d[key] = self._to_plain(value)
        return d

    @staticmethod
    def _to_plain(data):
        if isinstance(data, AnnotatedMapping):
            return data.to_dict()
        elif hasattr(data, '__iter__') and not isinstance(data, str):
            d = type(data)()
            for item in data:
                d.append(AnnotatedMapping._to_plain(item))
            return d
        else:
            return data


class AnnotatedPrettyPrinter(pprint.PrettyPrinter):
    def _format(self, obj, *args, **kwargs):
        if isinstance(obj, AnnotatedMapping):
            obj = obj._mapping
        return super()._format(obj, *args, **kwargs)


keg_dict = Union[Dict, AnnotatedMapping]
keg_dict_type = Union[Type[Dict], Type[AnnotatedMapping]]
