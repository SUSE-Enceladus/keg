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
import json
import logging
import os
import pathlib
import subprocess
import yaml
from datetime import datetime


def repr_mstr(dumper, data):
    """Helper representer to print strings with newlines as scalar blocks"""
    if '\n' in data:
        tag = u'tag:yaml.org,2002:str'
        return dumper.represent_scalar(tag, data, style='|')
    return dumper.represent_str(data)


def get_log_extension(log_format):
    log_ext = None
    if log_format == 'osc':
        log_ext = 'txt'
    elif log_format in ['json', 'yaml']:
        log_ext = log_format
    return log_ext


def read_changelog(log_file: str) -> dict:
    """Read changes from given file and return change log dict"""
    changes = dict()
    if log_file.endswith('.txt'):
        # parsing text log files is not supported
        pass
    elif log_file.endswith('.yaml'):
        with open(log_file, 'r') as inf:
            changes = yaml.safe_load(inf)
    elif log_file.endswith('.json'):
        with open(log_file, 'r') as inf:
            changes = json.load(inf)
    else:
        raise RuntimeError('Unsupported log format extensions {}'.format(log_file))
    return changes


def write_changelog(log_file: str, log_format: str, changes: dict, append: bool = False):
    """Write change log file to given location in given format"""
    open_mode = 'a' if append else 'w'
    with open(log_file, open_mode) as outf:
        if log_format in ['osc', 'txt']:
            for image_version in changes:
                if changes[image_version]:
                    print(get_osc_log(image_version, changes[image_version]), file=outf)
        elif log_format == 'yaml':
            yaml.add_representer(str, repr_mstr, Dumper=yaml.SafeDumper)
            yaml.safe_dump(changes, outf, sort_keys=False)
        elif log_format == 'json':
            json.dump(changes, outf, indent=2, default=str)


def generate_recipes_changelog(source_log, changes_file, log_format, image_version, rev_args) -> bool:
    result = subprocess.run(
        [
            'generate_recipes_changelog',
            '-o', changes_file,
            '-f', log_format,
            '-t', image_version,
            *rev_args,
            source_log
        ]
    )
    if result.returncode == 1:
        raise RuntimeError('Error generating change log.')
    # generate_recipes_changelog returns 2 in case there were no changes
    # return True or False accordingly
    return result.returncode == 0


def get_osc_log(ver, entries):
    change = '-------------------------------------------------------------------\n'
    change += datetime.fromisoformat(entries[0]['date']).strftime('%c UTC')
    change += '\n'
    indent = '- '
    if ver:
        change += '\n- Update to {}\n'.format(ver)
        indent = '  + '
    for entry in entries:
        change += indent
        change += '{}\n'.format(entry['change'])
    return change


def update_changelog(log_file, log_format, image_version):
    old_logs = glob.glob(pathlib.Path(log_file).stem + '.*')
    if old_logs:
        old_log = old_logs[0]
        if len(old_logs) > 1:
            logging.warning('More than one format for old log, using {}'.format(old_log))
    else:
        logging.info(f'No old log for {log_file}')
        return

    old_log_format = pathlib.Path(old_log).suffix[1:]

    if log_format != 'json' and log_format == old_log_format:
        # simply concatenate old log to new one
        with open(log_file, 'a') as outf, open(old_log) as inf:
            logging.info('Appending old changes to {}'.format(log_file))
            outf.write(inf.read())
    else:
        if old_log_format == 'txt':
            logging.warning('Converting text log files is not supported, losing history')
            return
        else:
            # different formats, or both json which needs merge
            logging.info('Reading old changes from {}'.format(old_log))
            old_changes = read_changelog(old_log)
            if old_changes:
                if log_format == 'osc':
                    logging.info('Appending old changes to {}'.format(pathlib.Path(log_file).name))
                    write_changelog(log_file, log_format, old_changes, append=True)
                else:
                    new_changes = read_changelog(log_file)
                    if old_changes.get(image_version) and new_changes.get(image_version):
                        logging.warning('Old change log already contains version {}, merging'.format(image_version))
                        old_changes[image_version] += new_changes[image_version]
                    new_changes.update(old_changes)
                    logging.info('Writing merged changes to {}'.format(pathlib.Path(log_file).name))
                    write_changelog(log_file, log_format, new_changes)


def generate_and_update(outdir, prefix, log_ext, changes, source_log, image_version, rev_args):
    changes_filename = f'{prefix}{"." if prefix else ""}changes.{log_ext}'
    changes_path = os.path.join(outdir, changes_filename)
    have_changes = False

    if changes:
        logging.info('Writing {}'.format(changes_path))
        write_changelog(changes_path, log_ext, changes)
        have_changes = True
    elif source_log:
        have_changes = generate_recipes_changelog(source_log, changes_path, log_ext, image_version, rev_args)
        update_changelog(changes_path, log_ext, image_version)
    else:
        raise Exception('Bug! generate_changelog() called without changes or source log')
    return have_changes
