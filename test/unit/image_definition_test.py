from mock import (
    patch, Mock
)
from pytest import raises

from kiwi_keg import version
from kiwi_keg.image_definition import KegImageDefinition
from kiwi_keg.exceptions import KegError


class TestKegImageDefinition:
    def setup(self):
        self.keg_definition = KegImageDefinition(
            image_name='leap/15.2', recipes_root='../data'
        )

    def test_setup_with_additional_data_root(self):
        keg_definition = KegImageDefinition(
            image_name='leap/15.2', recipes_root='../data',
            data_roots=['data2', 'data3']
        )
        assert keg_definition._data_roots == [
            '../data/data', 'data2', 'data3'
        ]

    def test_setup_raises_recipes_root_not_existing(self):
        with raises(KegError):
            KegImageDefinition(
                image_name='leap/15.2', recipes_root='artificial'
            )

    @patch('kiwi_keg.utils.KegUtils.get_recipes')
    def test_populate_raises_on_get_recipes(
        self, mock_utils_get_recipes
    ):
        mock_utils_get_recipes.side_effect = Exception
        with raises(KegError):
            self.keg_definition.populate()

    @patch('kiwi_keg.image_definition.datetime')
    def test_populate_composed_image(self, mock_datetime):
        utc_now = Mock()
        utc_now.strftime.return_value = 'time-string'
        mock_datetime.now.return_value = utc_now

        self.keg_definition.populate()

        print(self.keg_definition.data)
        assert self.keg_definition.data == {
            'generator': 'keg {0}'.format(version.__version__),
            'timestamp': 'time-string',
            'image source path': 'leap/15.2',
            'schema': 'vm',
            'image': {
                'author': 'The Team',
                'contact': 'bob@example.net',
                'name': 'Leap15.2-JeOS',
                'specification': 'Leap 15.2 guest image',
                'version': '1.0.42'
            },
            'archs': ['x86_64'],
            'users': [
                {
                    'name': 'root',
                    'groups': ['root'],
                    'home': '/root',
                    'password': 'foo'
                }
            ],
            'profiles': {
                'common': {
                    'include': ['defaults'],
                    'packages': {
                        'image': {
                            'jeos': [
                                {
                                    'name': 'grub2-x86_64-efi',
                                    'arch': 'x86_64'
                                },
                                'patterns-base-minimal_base'
                            ]
                        }
                    },
                    'config': {
                        'config_script': {
                            'JeOS-config': ['foo', 'name'],
                            'files': {
                                'JeOS-files': [
                                    {
                                        'path': '/etc/sysconfig/console',
                                        'append': True,
                                        'content': 'CONSOLE_ENCODING="UTF-8"'
                                    }
                                ]
                            },
                            'sysconfig': {
                                'JeOS-sysconfig': [
                                    {
                                        'file': '/etc/sysconfig/language',
                                        'name': 'INSTALLED_LANGUAGES',
                                        'value': ''
                                    }
                                ]
                            },
                            'services': {
                                'JeOS-services': [
                                    'sshd', {
                                        'name': 'kbd',
                                        'enable': False
                                    }
                                ]
                            }
                        },
                        'image_script': {
                            'JeOS-image': ['name']
                        }
                    },
                    'profile': {
                        'bootloader': {
                            'name': 'grub2',
                            'timeout': 1
                        },
                        'parameters': {
                            'bootpartition': 'false',
                            'firmware': 'uefi',
                            'devicepersistency': 'by-label',
                            'filesystem': 'xfs',
                            'image': 'vmx',
                            'kernelcmdline': {
                                'console': 'ttyS0',
                                'net.ifnames': 0,
                                'dis_ucode_ldr': []
                            }
                        },
                        'size': 10240
                    }
                },
                'other': {
                    'description': 'Some Other Profile'
                }
            },
            'include-paths': ['base/jeos/leap']
        }

    @patch('kiwi_keg.image_definition.datetime')
    def test_populate_single_build(self, mock_datetime):
        utc_now = Mock()
        utc_now.strftime.return_value = 'time-string'
        mock_datetime.now.return_value = utc_now
        keg_definition = KegImageDefinition(
            image_name='leap_single_build', recipes_root='../data'
        )

        keg_definition.populate()

        assert keg_definition.data['schema'] == 'vm_singlebuild'
