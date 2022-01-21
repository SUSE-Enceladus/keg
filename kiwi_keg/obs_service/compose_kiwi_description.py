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
"""
Usage:
    compose_kiwi_description --git-recipes=<git_clone_source> ... --image-source=<path> --outdir=<obs_out>
        [--git-branch=<name>] ...
        [--disable-version-bump]
    compose_kiwi_description -h | --help
    compose_kiwi_description --version

Options:
    --git-recipes=<git_clone_source>
        Remote git repository containing keg-recipes (multiples allowed).

    --git-branch=<name>
        Recipes repository branch to check out (multiples allowed, optional).

    --image-source=<path>
        Keg path in git source pointing to the image description.
        The path must be relative to the images/ directory.

    --outdir=<obs_out>
        Output directory to store data produced by the service.
        At the time the service is called through the OBS API
        this option is set.

    --disable-version-bump
        Do not increment the patch version number
"""
import os
import docopt
import itertools
import sys

from kiwi.xml_description import XMLDescription
from kiwi.utils.temporary import Temporary
from kiwi.command import Command
from kiwi.path import Path
from kiwi_keg.version import __version__
from kiwi_keg.image_definition import KegImageDefinition
from kiwi_keg.generator import KegGenerator


def main() -> None:
    args = docopt.docopt(__doc__, version=__version__)

    if not os.path.exists(args['--outdir']):
        Path.create(args['--outdir'])

    if len(args['--git-branch']) > len(args['--git-recipes']):
        sys.exit('Number of --git-branch arguments must not exceed number of git repos.')

    temp_git_dirs = []
    for repo, branch in itertools.zip_longest(args['--git-recipes'], args['--git-branch']):
        temp_git_dir = Temporary(prefix='keg_recipes.').new_dir()
        if branch:
            Command.run(['git', 'clone', '-b', branch, repo, temp_git_dir.name])
        else:
            Command.run(['git', 'clone', repo, temp_git_dir.name])
        temp_git_dirs.append(temp_git_dir.name)

    print(temp_git_dirs)
    image_definition = KegImageDefinition(
        image_name=args['--image-source'],
        recipes_roots=temp_git_dirs
    )
    image_generator = KegGenerator(
        image_definition=image_definition,
        dest_dir=args['--outdir']
    )
    image_generator.create_kiwi_description(
        overwrite=True
    )
    image_generator.create_custom_scripts(
        overwrite=True
    )
    image_generator.create_overlays(
        disable_root_tar=False, overwrite=True
    )

    if not args['--disable-version-bump']:
        # Increment patch version number unless disabled
        kiwi_config = f'{args["--outdir"]}/config.kiwi'
        description = XMLDescription(kiwi_config)
        xml_data = description.load()
        for preferences in xml_data.get_preferences():
            # It is expected that the <version> setting exists only once
            # in a keg generated image description. KIWI allows for profiled
            # <preferences> which in theory also allows to distribute the
            # <version> information between several <preferences> sections
            # but this would be in general questionable and should not be
            # be done any case by keg managed recipes. Thus the following
            # code takes the first version setting it can find and takes
            # it as the only version information available
            if preferences.get_version():
                version = preferences.get_version()[0].split('.')
                version[2] = f'{int(version[2]) + 1}'
                preferences.set_version(['.'.join(version)])
                with open(kiwi_config, 'w') as kiwi:
                    xml_data.export(outfile=kiwi, level=0)
                break
