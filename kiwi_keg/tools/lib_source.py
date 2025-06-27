# Copyright (c) 2025 SUSE Software Solutions Germany GmbH. All rights reserved.
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
import glob
import os
import logging


class Range:
    def __init__(self, range_spec, roots):
        range_mark, range_start_str, range_end_str, src_path = range_spec.split(':', 3)
        self.src_root, self.src_file = get_root_and_fname(src_path, roots)
        self.range_start = int(range_start_str)
        self.range_end = int(range_end_str)

    def line_covered(self, line_number, line_file, line_root):
        if line_root != self.src_root:
            return False
        if line_file != self.src_file:
            return False
        if line_number >= self.range_start and line_number <= self.range_end:
            return True
        return False


class SourcesFile:
    def __init__(self, srcs_file):
        self.roots = []
        self.ranges = []
        self.whole_files = []
        with open(srcs_file, 'r') as sf:
            for line in sf:
                line = line.rstrip('\n')
                if line.startswith('root:'):
                    self.roots.append(line[line.find(':') + 1:])
                elif line.startswith('range:'):
                    self.ranges.append(Range(line, self.roots))

    def line_covered(self, line_number, line_file, line_root):
        for r in self.ranges:
            if r.line_covered(line_number, line_file, line_root):
                return True
        return False


def get_log_sources(logdir):
    for source_log in glob.glob(os.path.join(logdir, 'log_sources*')):
        flavor = source_log[len(os.path.join(logdir, 'log_sources')) + 1:]
        yield source_log, flavor


def get_root_and_fname(file_path, roots):
    src_root = None
    i = 0
    while i < len(roots):
        if file_path.startswith(roots[i]):
            src_root = i
            src_file = file_path[len(roots[i]) + 1:]
            break
        i += 1
    if not src_root:
        raise RuntimeError(f'Source path {file_path} outside root spec')
    return src_root, src_file


def find_deleted_src_lines(old_log_dir, new_log_dir):
    for old_source_log, flavor in get_log_sources(old_log_dir):
        new_source_log = os.path.join(new_log_dir, os.path.basename(old_source_log))
        if not os.path.exists(new_source_log):
            logging.warning(
                '{} does not exit in new image description, skipping deleted lines detection'.format(
                    os.path.basename(old_source_log)
                )
            )

            continue
        new_srcs = SourcesFile(new_source_log)
        roots = []
        with open(old_source_log, 'r') as old_srcs, open(new_source_log, 'a') as new_log:
            for line in old_srcs:
                line = line.rstrip('\n')
                if line.startswith('root:'):
                    roots.append(line[line.find(':') + 1:])
                elif line.startswith('range:'):
                    range_mark, range_start, range_end, src_path = line.split(':', 3)
                    src_root, src_file = get_root_and_fname(src_path, roots)
                    for line_no in range(int(range_start), int(range_end) + 1):
                        if not new_srcs.line_covered(line_no, src_file, src_root):
                            new_log.write('deleted:{}:{}\n'.format(line_no, src_path))
