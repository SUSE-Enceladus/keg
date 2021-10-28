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
    compose_kiwi_description --main-git-recipes=<git_clone_source> --image-source=<path> --outdir=<obs_out>
        [--main-branch=<name>]
        [--add-on-git-recipes=<add_on_git_clone_source>]
        [--add-on-branch=<name>]
    compose_kiwi_description -h | --help
    compose_kiwi_description --version

Options:
    --main-git-recipes=<git_clone_source>
        Main git clone location to fetch keg recipes.

    --image-source=<path>
        Keg path in git source pointing to the image description.
        The path must be relative to the images/ directory

    --main-branch=<name>
        Branch in main git source [default: released].

    --add-on-git-recipes=<add_on_git_clone_source>
        Additional git clone location to fetch other keg recipes.

    --add-on-branch=<name>
        Branch in additional git source [default: released].

    --outdir=<obs_out>
        Output directory to store data produced by the service.
        At the time the service is called through the OBS API
        this option is set.
"""
import os
import docopt

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

    # TODO: How should the version be handled, open discussion
    image_version = None

    temp_git_dir = Temporary(prefix='keg_recipes.').new_dir()
    Command.run(
        ['git', 'clone', args['--main-git-recipes'], temp_git_dir.name]
    )
    Command.run(
        ['git', '-C', temp_git_dir.name, 'checkout', args['--main-branch']]
    )

    image_definition = KegImageDefinition(
        image_name=args['--image-source'],
        recipes_root=temp_git_dir.name,
        data_roots=args['--add-on-git-recipes'],
        image_version=image_version
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
