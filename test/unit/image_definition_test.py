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

    def test_populate_raises_on_no_such_overlay(self):
        with raises(KegError):
            keg_definition = KegImageDefinition(
                image_name='leap_broken_overlay', recipes_root='../data'
            )
            keg_definition.populate()

    @patch('kiwi_keg.image_definition.datetime')
    def test_populate_composed_image(self, mock_datetime):
        utc_now = Mock()
        utc_now.strftime.return_value = 'time-string'
        mock_datetime.now.return_value = utc_now

        self.keg_definition.populate()

        assert self.keg_definition.data == {
            'generator': 'keg {0}'.format(version.__version__),
            'archives': {'leap_15_2': ['../data/data/overlayfiles/products/leap/15.2'],
                         'other': ['../data/data/overlayfiles/csp/aws'],
                         'root': ['../data/data/overlayfiles/base',
                                  '../data/data/overlayfiles/csp/aws']},
            'archs': ['x86_64'],
            'image': {'author': 'The Team',
                      'contact': 'bob@example.net',
                      'name': 'Leap15.2-JeOS',
                      'specification': 'Leap 15.2 guest image',
                      'version': '1.0.42'},
            'image source path': 'leap/15.2',
            'include-paths': ['leap15/1', 'leap15/2'],
            'profiles': {'common': {'config': {'config_script': {'JeOS-config': ['foo', 'name'],
                                                                 'files': {'JeOS-files': [{'append': True,
                                                                                           'content': 'CONSOLE_ENCODING="UTF-8"',
                                                                                           'path': '/etc/sysconfig/console'}]},
                                                                 'services': {'JeOS-services': ['sshd', {'enable': False,
                                                                                                         'name': 'kbd'}]},
                                                                 'sysconfig': {'JeOS-sysconfig': [{'file': '/etc/sysconfig/language',
                                                                                                           'name': 'INSTALLED_LANGUAGES',
                                                                                                           'value': ''}]}},
                                               'image_script': {'JeOS-image': ['name']}},
                                    'include': ['base/jeos'],
                                    'overlayfiles': {'azure-common': {'include': ['base']},
                                                     'azure-extra-stuff': {'include': ['products/leap/15.2'],
                                                                           'archivename': 'leap_15_2'},
                                                     'azure-sle15-sp3': {'include': ['csp/aws']}},
                                    'packages': {'image': {'archive': [{'name': 'leap_15_2.tar.gz'}],
                                                           'jeos': [{'arch': 'x86_64',
                                                                     'name': 'grub2-x86_64-efi'},
                                                                    'patterns-base-minimal_base']}}},
                         'other': {'description': 'Some Other Profile',
                                   'include': ['foo_profile/overlay-addon'],
                                   'overlayfiles': {'foo-addon': {'include': ['csp/aws']}},
                                   'packages': {'image': {'archive': [{'name': 'other.tar.gz'}],
                                                          'foo-profile-package': [{'arch': 'x86_64',
                                                                                   'name': 'some-foo'}]}},
                                   'profile': {'bootloader': {'name': 'grub2',
                                                              'timeout': 1},
                                               'parameters': {'bootpartition': 'false',
                                                              'devicepersistency': 'by-label',
                                                              'filesystem': 'xfs',
                                                              'firmware': 'uefi',
                                                              'image': 'vmx',
                                                              'kernelcmdline': {'console': 'ttyS0',
                                                                                'dis_ucode_ldr': [],
                                                                                'net.ifnames': 0}},
                                               'size': 10240}}},
            'schema': 'vm',
            'timestamp': 'time-string',
            'users': [{'groups': ['root'],
                       'home': '/root',
                       'name': 'root',
                       'password': 'foo'}]}

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

    def test_list_recipes(self):
        assert self.keg_definition.list_recipes() == [
            'leap/15',
            'leap/15.1',
            'leap/15.2',
            'leap_broken_overlay',
            'leap_no_overlays',
            'leap_single_build'
        ]
