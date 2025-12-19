from pytest import raises
from unittest.mock import mock_open, patch, call

from kiwi_keg.tools import lib_source

sources = '''root:rootdir
range:1:2:rootdir/src_file
'''


def test_lib_source_sources_file():
    mock_file = mock_open(read_data=sources)
    with patch('builtins.open', mock_file):
        src_file = lib_source.SourcesFile('sources_file')
    assert src_file.roots == ['rootdir']
    assert len(src_file.ranges) == 1
    assert src_file.ranges[0].src_root == 'rootdir'
    assert src_file.ranges[0].src_file == 'src_file'
    assert src_file.ranges[0].range_start == 1
    assert src_file.ranges[0].range_end == 2
    assert src_file.line_covered(1, 'src_file', 'rootdir') is True
    assert src_file.line_covered(3, 'src_file', 'rootdir') is False
    assert src_file.line_covered(1, 'other_file', 'rootdir') is False
    assert src_file.line_covered(1, 'src_file', 'other_rootdir') is False


@patch('glob.glob', return_value=['logdir/log_sources_flavor1', 'logdir/log_sources_flavor2'])
def test_lib_source_get_log_sources(mock_glob):
    assert list(lib_source.get_log_sources('logdir')) == [
        ('logdir/log_sources_flavor1', 'flavor1'),
        ('logdir/log_sources_flavor2', 'flavor2')
    ]


def test_lib_source_get_root_and_fname():
    roots = ['rootdir']
    assert lib_source.get_root_and_fname('rootdir/src_file', roots) == ('rootdir', 'src_file')


def test_lib_source_get_root_and_fname_outside_root():
    roots = ['rootdir']
    with raises(RuntimeError) as e_info:
        lib_source.get_root_and_fname('other_dir/src_file', roots)
    assert 'outside root spec' in str(e_info.value)


@patch('kiwi_keg.tools.lib_source.get_log_sources', return_value=[('log_source_foo', 'foo')])
@patch('os.path.exists', return_value=True)
def test_lib_source_find_deleted_src_lines(mock_path_exists, mock_get_log_sources):
    mock_new_src_log = mock_open(read_data=sources)
    mock_old_src_log = mock_open(read_data=sources + 'range:2:3:rootdir/src_file\n')
    mock_new_src_log_write = mock_open()
    mock_opener = mock_open()
    mock_opener.side_effect = [mock_new_src_log.return_value, mock_old_src_log.return_value, mock_new_src_log_write.return_value]
    with patch('builtins.open', mock_opener):
        lib_source.find_deleted_src_lines('old_dir', 'new_dir')
        mock_new_src_log_write.assert_has_calls([call().write('deleted:3:rootdir/src_file\n')])


@patch('kiwi_keg.tools.lib_source.get_log_sources', return_value=[('log_source_foo', 'foo')])
@patch('os.path.exists', return_value=False)
def test_lib_source_find_deleted_src_lines_log_does_not_exit(mock_path_exists, mock_get_log_sources, caplog):
    lib_source.find_deleted_src_lines('old_dir', 'new_dir')
    assert 'does not exist in new image description' in caplog.text
