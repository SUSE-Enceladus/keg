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
import os
import shutil
import sys
import tempfile
import xml.etree.ElementTree as ET

from kiwi_keg.version import __version__
from kiwi_keg.tools.compose_kiwi_description import main as compose_main

usage_str = """
Usage:
    update_kiwi_description [-d <path>] [compose_kiwi_description_parameter] ...
    update_kiwi_description -h | --help
    update_kiwi_description --version

Options:
    -d <path>
        Path to existing keg generated image description. [default: .]

update_kiwi_description inspects the given directory (defaults to current
working directory) for a keg generated image description and tries to update
it. It uses the parameters from an existing _service file if avaialble. Any
compose_kiwi_description parameters can be given on the command line and will
overwrite parameters from the _service file.
"""


def parse_service(service_file):
    tree = ET.parse(service_file)
    append_args = []
    for service in tree.findall('service'):
        if service.attrib.get('name') != 'compose_kiwi_description':
            continue
        for param in service.findall('param'):
            param_name = f'--{param.attrib["name"]}'
            if param_name not in [x.split('=')[0] for x in sys.argv]:
                append_args.append(f'{param_name}={param.text}')
    sys.argv += append_args


def main() -> int:
    if len(sys.argv) > 1 and (sys.argv[1] == '-h' or sys.argv[1] == '--help'):
        print(usage_str)
        sys.exit(0)

    if len(sys.argv) > 1 and sys.argv[1] == '--version':
        print(__version__)
        sys.exit(0)

    desc_dir = os.getcwd()
    if len(sys.argv) > 1 and sys.argv[1] == '-d':
        if len(sys.argv) < 3:
            print(usage_str)
            sys.exit(1)
        desc_dir = sys.argv[2]
        sys.argv = ['update_kiwi_description'] + sys.argv[3:]

    if os.path.exists(os.path.join(desc_dir, '_service')):
        try:
            parse_service(os.path.join(desc_dir, '_service'))
        except Exception:
            print('Could not parse _service file.', file=sys.stderr)
            raise

    with tempfile.TemporaryDirectory(prefix='update_kiwi_description.') as tmpdir:
        os.chdir(desc_dir)
        sys.argv.append(f'--outdir={tmpdir}')
        compose_main()
        for f in os.listdir(tmpdir):
            shutil.copy(os.path.join(tmpdir, f), '.')

    return 0


if __name__ == '__main__':
    sys.exit(main())  # pragma: nocover
