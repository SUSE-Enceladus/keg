import yaml
from io import StringIO
from unittest.mock import patch, mock_open
from pytest import raises
import kiwi_keg.file_utils
from kiwi_keg.exceptions import KegError


@patch('kiwi_keg.file_utils._get_source_files')
@patch("builtins.open", new_callable=mock_open, read_data='foo: bar')
def test_get_recipes(mock_open, mock_get_source_files):
    mock_get_source_files.return_value = ['fake.yaml']
    data = kiwi_keg.file_utils.get_recipes(['fake_root'], ['fake_dirs'], ['fake_includes'])
    assert data == {'foo': 'bar'}


@patch('kiwi_keg.file_utils._get_source_files')
@patch("builtins.open", new_callable=mock_open, read_data='foo: bar')
def test_get_recipes_source_tracking(mock_open, mock_get_source_files):
    mock_get_source_files.return_value = ['fake.yaml']
    data = kiwi_keg.file_utils.get_recipes(['fake_root'], ['fake_dirs'], ['fake_includes'], True)
    assert dict(data.all_items()) == {
        '__foo_line_end__': 1,
        '__foo_line_start__': 1,
        '__foo_source__': mock_open().name,
        'foo': 'bar'
    }


@patch('kiwi_keg.file_utils.os.walk')
def test_get_all_leaf_dirs(mock_os_walk):
    mock_os_walk.return_value = [('base', ['foo'], []), ('base/foo', [], [])]
    assert kiwi_keg.file_utils.get_all_leaf_dirs('base') == ['foo']


class FakeStream(StringIO):
    @property
    def name(self):
        return 'fake.yaml'


def test_tracker_loader_constructor_error():
    buf = FakeStream()
    stl = kiwi_keg.file_utils.SafeTrackerLoader(buf)
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


@patch('kiwi_keg.file_utils._get_source_files')
@patch("builtins.open", new_callable=mock_open, read_data='script_content')
def test_load_scripts(mock_open, mock_get_source_files):
    mock_get_source_files.return_value = ['dir/script_file.sh']
    scripts = kiwi_keg.file_utils.load_scripts(['fake_root'], ['fake_dirs'], ['fake_includes'])
    assert scripts == {'script_file': 'script_content'}


@patch('os.path.exists')
def test_raise_on_file_exists(mock_path_exists):
    mock_path_exists.return_value = True
    with raises(KegError):
        kiwi_keg.file_utils.raise_on_file_exists('fake_path', False)


@patch('kiwi_keg.file_utils.glob')
def test_get_source_files(mock_glob):
    mock_glob.side_effect = [['root/sub/l2.yaml'], ['root/sub/_inc/l3.yaml'], ['root/l1.yaml'], ['root/_inc/l1.5.yaml']]
    sources = kiwi_keg.file_utils._get_source_files(['root'], 'sub', 'yaml', ['_inc'])
    assert sources == [
        'root/l1.yaml',
        'root/_inc/l1.5.yaml',
        'root/sub/l2.yaml',
        'root/sub/_inc/l3.yaml'
    ]
