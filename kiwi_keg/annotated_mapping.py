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


class AnnotatedPrettyPrinter(pprint.PrettyPrinter):
    def _format(self, obj, *args, **kwargs):
        if isinstance(obj, AnnotatedMapping):
            obj = obj._mapping
        return super()._format(obj, *args, **kwargs)


keg_dict = Union[Dict, AnnotatedMapping]
keg_dict_type = Union[Type[Dict], Type[AnnotatedMapping]]
