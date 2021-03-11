from kiwi_keg.utils import KegUtils


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
        assert KegUtils.get_recipes(
            ['../data/images'], 'leap_single_build', ['base/jeos/leap']
        ) == expected_output

    def test_load_scripts(self):
        expected_output = {'foo': 'bar\n', 'name': 'bob\n'}
        assert KegUtils.load_scripts(
            ['../data/data'], 'scripts', ['base/jeos/leap']
        ) == expected_output
