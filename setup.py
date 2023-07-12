#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from os import path
from setuptools import setup

from kiwi_keg.version import __version__

here = path.abspath(path.dirname(__file__))
with open(path.join(here, 'README.rst'), encoding='utf-8') as readme:
    long_description = readme.read()

config = {
    'name': 'kiwi_keg',
    'long_description': long_description,
    'long_description_content_type': 'text/x-rst',
    'description': 'KEG - Image Composition Tool',
    'author': 'Public Cloud Team',
    'url': 'https://github.com/SUSE-Enceladus/keg',
    'download_url':
        'https://download.opensuse.org',
    'author_email': 'public-cloud-dev@susecloud.net',
    'version': __version__,
    'license': 'GPLv3+',
    'install_requires': [
        'docopt',
        'Jinja2',
        'kiwi>=9.21.21',
        'PyYAML',
        'schema',
        'iso8601; python_version < "3.7.0"'
    ],
    'packages': ['kiwi_keg', 'kiwi_keg.tools'],
    'entry_points': {
        'console_scripts': [
            'keg=kiwi_keg.keg:main',
            'compose_kiwi_description=kiwi_keg.tools.compose_kiwi_description:main',
            'generate_recipes_changelog=kiwi_keg.tools.generate_recipes_changelog:main'
        ]
    },
    'include_package_data': True,
    'zip_safe': False,
    'classifiers': [
        # classifier: http://pypi.python.org/pypi?%3Aaction=list_classifiers
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: '
        'GNU General Public License v3 or later (GPLv3+)',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.10',
        'Topic :: System :: Operating System',
    ]
}

setup(**config)
