from mock import patch
from pytest import raises
from kiwi_keg import file_utils
from kiwi_keg.exceptions import KegDataError


class TestUtils:
    def test_create_yaml_tree(self):
        expected_output = {
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
                    'home': '/root', 'password': 'foo'
                }
            ],
            'include-paths': ['leap15/1', 'leap15/2'],
            'profiles': {
                'common': {
                    'include': ['base/jeos']
                }
            }
        }
        assert file_utils.get_recipes(
            ['../data/images'], ['leap_single_build'], ['base/jeos/leap']
        ) == expected_output

    def test_load_scripts(self):
        expected_output = {'foo': 'bar\n', 'name': 'bob\n'}
        assert file_utils.load_scripts(
            ['../data/data'], 'scripts', ['base/jeos/leap']
        ) == expected_output

    @patch('file_utils.os.walk')
    def get_all_leaf_dirs(self, mock_os_walk):
        mock_os_walk.return_value = ['foo', [], []]
        assert file_utils.get_all_leaf_dirs('foo') == ['foo']

    def test_rmerge_data_exception(self):
        a_dict = {'some_key': 1}
        not_a_dict = None
        with raises(KegDataError):
            file_utils.rmerge(a_dict, not_a_dict)
        with raises(KegDataError):
            file_utils.rmerge(not_a_dict, a_dict)
