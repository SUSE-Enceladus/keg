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

from glob import glob
from pathlib import Path
from typing import (
    List, Dict
)
import os
import yaml


class KegUtils:
    """
    Class for managing source files
    """
    @staticmethod
    def rmerge(src: Dict[str, str], dest: Dict[str, str]) -> Dict[str, str]:
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
        for key, value in src.items():
            if isinstance(value, dict):
                node = dest.setdefault(key, {})
                KegUtils.rmerge(value, node)
            else:
                dest[key] = value
        return dest

    @staticmethod
    def get_recipes(
        roots: List[str], sub_dir: str, include_paths: List[str] = None
    ) -> Dict[str, str]:
        """
        Return a new yaml tree including the data of all the source files for
        a given list of root directories and a sub directory

        :param: list roots: list of root directory paths to get the files from
        :param: str sub_dir: subdirectory path to get the files from
        :param: list include_paths: list of paths to be included
        """
        desc_files = KegUtils._get_source_files(
            roots, sub_dir, 'yaml', include_paths
        )
        merged_tree: Dict[str, str] = {}
        for desc_file in desc_files:
            with open(desc_file, 'r') as f:
                desc_yaml = yaml.safe_load(f.read())
            KegUtils.rmerge(desc_yaml, merged_tree)
        return merged_tree

    @staticmethod
    def load_scripts(
        roots: List[str], sub_dir: str, include_paths: List[str] = None
    ) -> Dict[str, str]:
        """
        Return a dict containing the name of the scripts and its content for
        a given list of root directories and a sub directory

        :param: str sub_dir: subdirectory path to load the scripts from
        :param: list roots: list of root directory paths to load the scripts from
        :param: list include_paths: list of paths to be included

        :return: dict with the name of the scripts (without the ext) and their
        content

        :rtype: dict
        """
        script_files = KegUtils._get_source_files(
            roots, sub_dir, 'sh', include_paths
        )
        script_lib: Dict[str, str] = {}
        for script_file in script_files:
            with open(script_file, 'r') as f:
                script_source = f.read()
                script_lib[os.path.basename(script_file[:-3])] = script_source
        return script_lib

    @staticmethod
    def get_all_files(base_dir):
        """
        Return a generator containing all the files paths in the sub directories
        of a given path.
        :param: str base_dir: directory path to get all the files from.
        :return: generator with all the file paths inside that directory.
        :rtype: generator
        """
        for sub_dir in os.scandir(base_dir):
            if sub_dir.is_dir():
                yield from KegUtils.get_all_files(sub_dir.path)
            elif sub_dir.is_file():
                yield sub_dir.path

    @staticmethod
    def _get_source_files(roots, sub_dir, ext, include_paths):
        src_files = []
        for root_dir in roots:
            src_files = KegUtils._get_versioned_source_files(
                os.path.join(root_dir, sub_dir),
                ext,
                include_paths
            )
            for parent in Path(sub_dir).parents:
                src_files = KegUtils._get_versioned_source_files(
                    os.path.join(root_dir, parent),
                    ext,
                    include_paths
                ) + src_files
        return src_files

    @staticmethod
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
