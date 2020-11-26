#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from setuptools import setup
from setuptools.command import sdist as setuptools_sdist

import distutils
import subprocess

from keg.version import __version__


class sdist(setuptools_sdist.sdist):
    """
    Custom sdist command
    Host requirements: git
    """
    def run(self):
        """
        Run first the git commit format update $Format:%H$
        and after that the usual Python sdist
        """
        # git attributes
        command = ['make', 'git_attributes']
        self.announce(
            'Running make git_attributes target: %s' % str(command),
            level=distutils.log.INFO
        )
        self.announce(
            subprocess.check_output(command).decode(),
            level=distutils.log.INFO
        )

        # standard sdist process
        setuptools_sdist.sdist.run(self)

        # cleanup attributes
        command = ['make', 'clean_git_attributes']
        self.announce(
            subprocess.check_output(command).decode(),
            level=distutils.log.INFO
        )


config = {
    'name': 'keg',
    'description': 'KEG - Image Composition Tool',
    'author': 'Public Cloud Team',
    'url': 'https://github.com/SUSE-Enceladus/keg',
    'download_url':
        'https://download.opensuse.org',
    'author_email': 'public-cloud-dev@suse.de',
    'version': __version__,
    'license' : 'GPLv3+',
    'install_requires': [
        'docopt',
        'kiwi>=9.21.21',
        'PyYAML'
    ],
    'packages': ['keg'],
    'entry_points': {
        'console_scripts': [
            'keg=keg.keg:main'
        ]
    },
    'include_package_data': True,
    'zip_safe': False,
    'classifiers': [
       # classifier: http://pypi.python.org/pypi?%3Aaction=list_classifiers
       'Development Status :: 2 - Pre-Alpha',
       'Intended Audience :: Developers',
       'License :: OSI Approved :: '
       'GNU General Public License v3 or later (GPLv3+)',
       'Operating System :: POSIX :: Linux',
       'Programming Language :: Python :: 3.6',
       'Programming Language :: Python :: 3.8',
       'Topic :: System :: Operating System',
    ]
}

setup(**config)
