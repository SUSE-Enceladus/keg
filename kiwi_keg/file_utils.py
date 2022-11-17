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
from glob import glob
from pathlib import Path
from typing import (
    List, Dict, Union, Type
)
import os
import collections.abc
import yaml
from kiwi_keg import dict_utils
from kiwi_keg.exceptions import KegError
from kiwi_keg.annotated_mapping import AnnotatedMapping, keg_dict

log = logging.getLogger('keg')


class SafeTrackerLoader(yaml.loader.SafeLoader):
    """
    Extends SafeLoader with source info tracking.
    Adds source file and line number info for all hashable keys.
    Uses AnnotatedMappings to hide annotated tags from normal access.
    """
    def __init__(self, stream):
        self._source = stream.name
        self._current_end = None
        super().__init__(stream)
        yaml.add_constructor(
            yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
            SafeTrackerLoader.construct_yaml_map,
            SafeTrackerLoader
        )

    def construct_mapping(self, node, deep=False):
        if isinstance(node, yaml.nodes.MappingNode):
            self.flatten_mapping(node)
        else:
            raise yaml.constructor.ConstructorError(
                None, None,
                "expected a mapping node, but found %s" % node.id,
                node.start_mark
            )
        mapping = AnnotatedMapping()
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if not isinstance(key, collections.abc.Hashable):
                raise yaml.constructor.ConstructorError(
                    "while constructing a mapping", node.start_mark,
                    "found unhashable key", key_node.start_mark
                )
            value = self.construct_object(value_node, deep=deep)
            mapping[key] = value
            mapping['__{}_source__'.format(key)] = self._source
            mapping['__{}_line_start__'.format(key)] = key_node.start_mark.line + 1
            # for multi-line values, end_mark points to the next line, so no +1 needed
            # in case it's single line, +1 is needed, so adjust if necessary
            end_line = value_node.end_mark.line
            if end_line <= value_node.start_mark.line:
                end_line += 1
            mapping['__{}_line_end__'.format(key)] = end_line
        return mapping

    def construct_yaml_map(self, node):
        data = AnnotatedMapping()
        yield data
        value = self.construct_mapping(node)
        data.update(value)


def get_recipes(
    roots: List[str], sub_dirs: List[str], include_paths: List[str] = [], track_sources: bool = False
) -> keg_dict:
    """
    Return a new yaml tree including the data of all the source files for
    a given list of root directories and a sub directory

    :param: list roots: list of root directory paths to get the files from
    :param: str sub_dir: subdirectory path to get the files from
    :param: list include_paths: list of paths to be included
    """
    desc_files = []
    for sub_dir in sub_dirs:
        desc_files += _get_source_files(
            roots, sub_dir, 'yaml', include_paths
        )
    merged_tree: Union[Dict[str, str], AnnotatedMapping]
    yaml_loader: Union[Type[yaml.SafeLoader], Type[SafeTrackerLoader]]
    if track_sources:
        merged_tree = AnnotatedMapping()
        yaml_loader = SafeTrackerLoader
    else:
        merged_tree = {}
        yaml_loader = yaml.SafeLoader
    files_read = []
    for desc_file in desc_files:
        if desc_file not in files_read:
            log.debug(f'Reading: {desc_file}')
            with open(desc_file, 'r') as f:
                desc_yaml = yaml.load(f, Loader=yaml_loader)
            dict_utils.rmerge(desc_yaml, merged_tree)
            files_read.append(desc_file)
    return merged_tree


def load_scripts(
    roots: List[str], sub_dir: str, include_paths: List[str] = []
) -> Dict[str, str]:
    """
    Return a dict containing the name of the scripts and its content for
    a given list of root directories and a sub directory

    :param: str sub_dir:
        subdirectory path to load the scripts from
    :param: list roots:
        list of root directory paths to load the scripts from
    :param: list include_paths:
        list of paths to be included

    :return:
        dict with the name of the scripts (without the ext)
        and their content

    :rtype: dict
    """
    script_files = _get_source_files(
        roots, sub_dir, 'sh', include_paths
    )
    script_lib: Dict[str, str] = {}
    for script_file in script_files:
        with open(script_file, 'r') as f:
            script_source = f.read()
            script_lib[os.path.basename(script_file[:-3])] = script_source
    return script_lib


def get_all_leaf_dirs(base_dir: str) -> List[str]:
    """
    Return a list of leaf directories of a given path.
    :param: str base_dir: directory path to scan
    :return: list of all leaf directories
    """
    strip_offset = len(base_dir) + 1
    walker = os.walk(base_dir)
    return [x[0][strip_offset:] for x in walker if not x[1]]


def raise_on_file_exists(fpath: str, overwrite: bool):
    """
    Raise error if given path exists and overwrite is False.
    :param: str fpath: file with path.
    """
    if not overwrite and os.path.exists(fpath):
        raise KegError(
            '{target} exists, use force to overwrite.'.format(
                target=fpath
            )
        )


def _get_source_files(roots, sub_dir, ext, include_paths):
    src_files = []
    for root_dir in roots:
        src_files += _get_versioned_source_files(
            os.path.join(root_dir, sub_dir),
            ext,
            include_paths
        )
        for parent in Path(sub_dir).parents:
            src_files = _get_versioned_source_files(
                os.path.join(root_dir, parent),
                ext,
                include_paths
            ) + src_files
    return src_files


def _get_versioned_source_files(src_path, ext, include_paths):
    ver_src_files = glob(os.path.join(src_path, '*.{}'.format(ext)))
    scanned_dirs = []
    if include_paths:
        for include_path in include_paths:
            current_dir = src_path
            if current_dir not in scanned_dirs:
                for level_down in Path(include_path).parts:
                    current_dir = os.path.join(current_dir, level_down)
                    ver_src_files += glob(
                        os.path.join(current_dir, '*.{}'.format(ext))
                    )
                    scanned_dirs.append(current_dir)
    return ver_src_files
