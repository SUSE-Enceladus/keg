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
from typing import Optional
from kiwi_keg.exceptions import KegDataError
from kiwi_keg.annotated_mapping import AnnotatedMapping, keg_dict

log = logging.getLogger('keg')


def rmerge(src: keg_dict, dest: keg_dict) -> keg_dict:
    """
    Merge two dictionaries recursively,
    preserving all properties found in src.
    Updating 'dest' to the latest value, if property is not a dict
    or adding them in the right key, if it is while keeping the existing
    key-values.

    Example:
    src = {'a': 'foo', 'b': {'c': 'bar'}}
    dest = {'a': 'baz', 'b': {'d': 'more_bar'}}

    Result: {'a': 'foo', 'b': {'d': 'more_bar', 'c': 'bar'}}
    """
    if not isinstance(dest, dict) and not isinstance(dest, AnnotatedMapping):
        raise KegDataError(
            'Cannot rmerge, destination is not a mapping: {} {}'.format(dest, type(dest))
        )
    if isinstance(src, dict):
        items = src.items()
    elif isinstance(src, AnnotatedMapping):
        items = src.all_items()
    else:
        raise KegDataError(
            'Cannot rmerge, source mapping type not supported: {}'.format(type(src))
        )

    for key, value in items:
        if isinstance(value, dict) or isinstance(value, AnnotatedMapping):
            node = dest.setdefault(key, type(value)({}))
            rmerge(value, node)
        elif value is None:
            if dest.get(key) is not None:
                del dest[key]
                if isinstance(src, AnnotatedMapping):
                    dest[f'__deleted_{key}'] = {}
        else:
            dest[key] = value
    return dest


def get_attribute(data: keg_dict, attr: str, default=None) -> Optional[str]:
    """
    Look up wanted attribute from given dict
    """
    attr = data.get('_attributes', {}).get(attr)
    return attr if attr else default
