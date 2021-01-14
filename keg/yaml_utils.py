# Copyright (c) 2020 SUSE Software Solutions Germany GmbH. All rights reserved.
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
import os
import yaml


def _get_versioned_source_files(src_path, include_paths):
    src_files = glob(os.path.join(src_path, '*.yaml'))
    scanned_dirs = []
    if include_paths:
        for include_path in include_paths:
            current_dir = src_path
            if current_dir not in scanned_dirs:
                scanned_dirs.append(current_dir)
                for level_down in Path(include_path).parts:
                    current_dir = os.path.join(current_dir, level_down)
                    src_files += glob(os.path.join(current_dir, '*.yaml'))
    return src_files


def _get_source_files(root, src_path, include_paths=None):
    src_files = _get_versioned_source_files(os.path.join(root, src_path), include_paths)
    for parent in Path(src_path).parents:
        src_files = _get_versioned_source_files(
            os.path.join(root, parent),
            include_paths
        ) + src_files
    return src_files


def rmerge(src, dest):
    for key, value in src.items():
        if isinstance(value, dict):
            node = dest.setdefault(key, {})
            rmerge(value, node)
        else:
            dest[key] = value
    return dest


def parse_tree(sub_dir, roots, include_paths=None):
    desc_files = []
    for root_dir in roots:
        desc_files += _get_source_files(root_dir, sub_dir, include_paths)
    merged_tree = {}
    for df in desc_files:
        with open(df, 'r') as f:
            desc_yaml = yaml.safe_load(f.read())
        rmerge(desc_yaml, merged_tree)
    return merged_tree
