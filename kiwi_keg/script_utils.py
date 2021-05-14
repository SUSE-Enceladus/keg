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
from textwrap import indent
from typing import (
    List, Dict
)

# project
from kiwi_keg.exceptions import KegError


def get_config_script(profiles_dict: Dict, config_key: str, script_dirs: List[str]):
    content = ''
    profile = profiles_dict.get('common')
    if profile:
        config_root = profile.get(config_key)
        if config_root:
            content += get_profile_section(config_root, script_dirs)
    for profile, profile_data in profiles_dict.items():
        if profile == 'common':
            continue
        config_root = profile_data.get(config_key)
        if config_root:
            content += 'if [[ $kiwi_profiles = {profile} ]]; then\n'.format(profile=profile)
            content += indent(get_profile_section(config_root, script_dirs), '    ')
            content += 'fi\n'
    return content


def get_profile_section(config_section: Dict, script_dirs: List[str]):
    content = ''
    config_sysconfig = config_section.get('sysconfig')
    if config_sysconfig:
        for ns, items in config_sysconfig.items():
            content += '# keg: included from {}\n'.format(ns)
            content += get_sysconfig_section(items, ns)
            content += '\n'
    config_files = config_section.get('files')
    if config_files:
        for ns, items in config_files.items():
            content += '# keg: included from {}\n'.format(ns)
            content += get_files_section(items, ns)
            content += '\n'
    config_scripts = config_section.get('scripts')
    if config_scripts:
        for ns, items in config_scripts.items():
            content += '# keg: included from {}\n'.format(ns)
            content += get_scripts_section(items, ns, script_dirs)
            content += '\n'
    config_services = config_section.get('services')
    if config_services:
        for ns, items in config_services.items():
            content += '# keg: included from {}\n'.format(ns)
            content += get_services_section(items, ns)
            content += '\n'
    return content


def get_sysconfig_section(sysconfig_items: Dict, ns: str):
    content = ''
    try:
        for item in sysconfig_items:
            content += 'baseUpdateSysConfig {file} {variable} "{value}"\n'.format(
                file=item['file'],
                variable=item['name'],
                value=item['value']
            )
        return content
    except KeyError:
        raise KegError('sysconfig section "{namespace}" malformed'.format(namespace=ns))


def get_files_section(files_items: Dict, ns: str):
    content = ''
    try:
        for item in files_items:
            content += 'cat >'
            if item.get('append'):
                content += '>'
            content += ' "{filename}" <<EOF\n{content}\nEOF\n'.format(
                filename=item['path'],
                content=item['content']
            )
        return content
    except KeyError:
        raise KegError('files section "{namespace}" malformed'.format(namespace=ns))


def get_services_section(service_items: Dict, ns: str):
    content = ''
    try:
        for item in service_items:
            if isinstance(item, str):
                service_name = item
                enable = True
            else:
                service_name = item['name']
                enable = item['enable']
            if service_name.endswith('timer'):
                content += 'systemctl enable {}\n'.format(service_name)
            else:
                if enable:
                    content += 'baseInsertService {}\n'.format(service_name)
                else:
                    content += 'baseRemoveService {}\n'.format(service_name)
        return content
    except KeyError:
        raise KegError('service section "{namespace}" malformed'.format(namespace=ns))


def get_scripts_section(script_items: Dict, ns: str, script_dirs: List[str]):
    content = ''
    for script_name in script_items:
        script_path = get_script_path(script_dirs, script_name)
        if script_path:
            with open(script_path, 'r') as script_file:
                content += script_file.read()
        else:
            raise KegError(
                'script "{scriptname}" included in "{namespace}" does not exist'.format(
                    scriptname=script_name,
                    namespace=ns
                )
            )
    return content


def get_script_path(script_dirs: List[str], script_name: str):
    script_path = None
    for script_dir in script_dirs:
        for entry in os.scandir(script_dir):
            if entry.is_file() and '{}.sh'.format(script_name) == entry.name:
                script_path = entry.path
    return script_path
