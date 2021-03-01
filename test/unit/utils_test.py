from kiwi_keg.utils import (
    get_yaml_tree, load_scripts
)


class TestUtils:
    def test_create_yaml_tree(self):
        expected_output = {
            'schema': 'vm_singlebuild',
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
            'include-paths': ['jeos/leap'],
            'contents': {
                'include': ['base/jeos']
            }
        }
        assert get_yaml_tree(
            'leap_single_build', ['../data/images'], ['base/jeos/leap']
        ) == expected_output

    def test_load_scripts(self):
        expected_output = {'foo': 'bar\n'}
        assert load_scripts(
            'scripts', ['../data/data'], ['base/jeos/leap']
        ) == expected_output
