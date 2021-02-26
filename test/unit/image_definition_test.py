from mock import (
    patch, Mock
)
from pytest import raises

from keg.image_definition import KegImageDefinition
from keg.exceptions import KegError


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

    @patch('keg.image_definition.utils.parse_yaml_tree')
    def test_populate_raises_on_parse_yaml_tree(
        self, mock_utils_parse_yaml_tree
    ):
        mock_utils_parse_yaml_tree.side_effect = Exception
        with raises(KegError):
            self.keg_definition.populate()

    @patch('keg.image_definition.datetime')
    def test_populate_composed_image(self, mock_datetime):
        utc_now = Mock()
        utc_now.strftime.return_value = 'time-string'
        mock_datetime.now.return_value = utc_now

        self.keg_definition.populate()

        assert self.keg_definition.get_data() == {
            'generator': 'keg 0.0.1',
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
                        'files': {
                            'JeOS-sysconfig': [
                                {
                                    'path': '/etc/sysconfig/console',
                                    'append': True,
                                    'content': 'CONSOLE_ENCODING="UTF-8"'
                                }
                            ]
                        },
                        'scripts': {
                            'JeOS-config': ['remove-root-pw']
                        },
                        'services': {
                            'JeOS-services': [
                                'sshd', {
                                    'name': 'kbd',
                                    'enable': False
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

    @patch('keg.image_definition.datetime')
    def test_populate_single_build(self, mock_datetime):
        utc_now = Mock()
        utc_now.strftime.return_value = 'time-string'
        mock_datetime.now.return_value = utc_now
        keg_definition = KegImageDefinition(
            image_name='leap_single_build', recipes_root='../data'
        )

        keg_definition.populate()

        assert keg_definition.get_data()['schema'] == 'vm_singlebuild'
