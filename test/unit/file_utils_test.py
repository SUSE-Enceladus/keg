from mock import patch
from pytest import raises
from kiwi_keg import file_utils
import yaml


class TestUtils:
    def test_create_yaml_tree(self):
        expected_output = {
            'archive': [{'_include': ['base/common'], 'name': 'root.tar.gz'},
                        {'_include': ['platform/blue'], 'name': 'blue.tar.gz'}],
            'config': [{'_include': ['base/common']},
                       {'_include': ['platform/blue'], '_profiles': ['Blue']},
                       {'_include': ['platform/orange'], '_profiles': ['Orange']},
                       {'_include': ['platform/common'], '_profiles': ['Blue', 'Orange']}],
            'image': {'_attributes': {'schemaversion': '6.2'},
                      'description': {'_attributes': {'type': 'system'},
                                      'author': 'The Team',
                                      'contact': 'bob@example.net'},
                      'packages': [{'_attributes': {'type': 'bootstrap'},
                                    '_include': ['base/bootstrap']},
                                   {'_attributes': {'type': 'image'},
                                    '_include': ['base/common']},
                                   {'_attributes': {'profiles': ['Blue'], 'type': 'image'},
                                    '_include': ['platform/blue'],
                                    'archive': [{'_attributes': {'name': 'blue.tar.gz'}}]},
                                   {'_attributes': {'profiles': ['Orange'], 'type': 'image'},
                                    '_include': ['platform/orange']}],
                      'preferences': [{'_include': 'base/common'},
                                      {'_attributes': {'profiles': ['Blue']},
                                       '_include': ['platform/blue']},
                                      {'_attributes': {'profiles': ['Orange']},
                                       '_include': ['platform/orange']}],
                      'profiles': {'profile': [{'_attributes': {'description': 'Image for '
                                                                               'Blue '
                                                                               'Platform',
                                                                'name': 'Blue'}},
                                               {'_attributes': {'description': 'Image for '
                                                                               'Orange '
                                                                               'Platform',
                                                                'name': 'Orange'}}]},
                      'repository': [{'_attributes': {'type': 'rpm-md'},
                                      'source': {'_attributes': {'path': 'obsrepositories:/'}}}],
                      'users': {'user': [{'_attributes': {'groups': 'root',
                                                          'home': '/root',
                                                          'name': 'root',
                                                          'password': 'foo'}}]}},
            'image-config-comments': {'obs-multibuild': 'OBS-Profiles: @BUILD_FLAVOR@'},
            'setup': [{'_include': ['base/common']}],
        }

        assert file_utils.get_recipes(
            ['../data/images'], ['leap-jeos'], []
        ) == expected_output

    def test_load_scripts(self):
        expected_output = {
            'orange-stuff': 'Configure some orange parameters\n',
            'base-stuff': 'Some fundamental config stuff\n',
            'common-stuff': 'Some common config stuff\n',
            'blue-stuff': 'Configure some blue parameters\n'
        }
        assert file_utils.load_scripts(
            ['../data/data'], 'scripts', []
        ) == expected_output

    @patch('file_utils.os.walk')
    def get_all_leaf_dirs(self, mock_os_walk):
        mock_os_walk.return_value = ['foo', [], []]
        assert file_utils.get_all_leaf_dirs('foo') == ['foo']

    def test_tracker_loader_constructor_error(self):
        with open('../data/images/defaults.yaml', 'r') as f:
            stl = file_utils.SafeTrackerLoader(f)
            with raises(yaml.constructor.ConstructorError) as err:
                stl.construct_mapping(yaml.nodes.ScalarNode('no', 'mapping'))
            assert 'expected a mapping node' in str(err)
            with raises(yaml.constructor.ConstructorError) as err:
                broken_node = yaml.nodes.MappingNode(
                    tag='tag:yaml.org,2002:map',
                    value=[(yaml.nodes.ScalarNode(tag='tag:yaml.org,2002:str', value=['not', 'hashable']), yaml.nodes.ScalarNode(tag='tag:yaml.org,2002:str', value='foo'))]
                )
                stl.construct_mapping(broken_node)
            assert 'found unhashable key' in str(err)
