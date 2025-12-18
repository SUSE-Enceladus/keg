import datetime
import logging
import sys
from pytest import raises
from unittest.mock import patch, Mock, mock_open

from kiwi_keg.tools import generate_recipes_changelog


@patch('kiwi_keg.tools.generate_recipes_changelog.get_commits')
def test_generate_recipes_changelog_get_commits_from_range(mock_get_commits):
    generate_recipes_changelog.get_commits_from_range('start', 'end', 'filespec', 'gitroot', 'rev')
    mock_get_commits.assert_called_with(
        [
            'git',
            '-C',
            'gitroot',
            'log',
            '--no-merges',
            '--format=%ct %H',
            '--no-patch',
            'rev',
            '-Lstart,end:filespec'
        ],
        'gitroot'
    )


def test_generate_recipes_changelog_get_commits_from_range_empty_rev():
    assert generate_recipes_changelog.get_commits_from_range('start', 'end', 'filespec', 'gitroot', '') == set()


@patch('kiwi_keg.tools.generate_recipes_changelog.get_commits')
def test_generate_recipes_changelog_get_commits_from_path(mock_get_commits):
    generate_recipes_changelog.get_commits_from_path('pathspec', 'gitroot', 'rev')
    mock_get_commits.assert_called_with(
        [
            'git',
            '-C',
            'gitroot',
            'log',
            '--no-merges',
            '--format=%ct %H',
            'rev',
            '--',
            'pathspec'
        ],
        'gitroot'
    )


def test_generate_recipes_changelog_get_commits_from_path_empty_rev():
    assert generate_recipes_changelog.get_commits_from_path('pathspec', 'gitroot', '') == set()


@patch('subprocess.run')
def test_generate_recipes_changelog_get_deletion_commit_blame_exception(mock_subprocess_run):
    mock_subprocess_run.return_value.returncode = 1
    mock_subprocess_run.return_value.stderr = b'blame fail\n'
    with raises(Exception) as e_info:
        generate_recipes_changelog.get_deletion_commit('line_no', 'filespec', 'gitroot', 'rev')
        assert str(e_info.value) == 'git exited with error "blame fail"'


@patch('subprocess.run')
def test_generate_recipes_changelog_get_deletion_commit_log_exception(mock_subprocess_run):
    mock_sp_blame = Mock()
    mock_sp_log = Mock()
    mock_sp_blame.returncode = 0
    mock_sp_blame.stdout = b'last_commit\n'
    mock_sp_log.returncode = 1
    mock_sp_log.stderr = b'log fail\n'
    mock_subprocess_run.side_effect = [mock_sp_blame, mock_sp_log]
    with raises(Exception) as e_info:
        generate_recipes_changelog.get_deletion_commit('line_no', 'filespec', 'gitroot', 'rev')
        assert str(e_info.value) == 'git exited with error "log fail"'


@patch('subprocess.run')
def test_generate_recipes_changelog_get_deletion_commit_no_commits(mock_subprocess_run, caplog):
    mock_sp_blame = Mock()
    mock_sp_log = Mock()
    mock_sp_blame.returncode = 0
    mock_sp_blame.stdout = b'last_commit\n'
    mock_sp_log.returncode = 0
    mock_sp_log.stdout = b''
    mock_subprocess_run.side_effect = [mock_sp_blame, mock_sp_log]
    with caplog.at_level(logging.DEBUG):
        generate_recipes_changelog.log.setLevel(logging.DEBUG)
        generate_recipes_changelog.get_deletion_commit('line_no', 'filespec', 'gitroot', 'rev')
    assert 'Source log indicates filespec:line_no was deleted but cannot find commit' in caplog.text


@patch('subprocess.run')
def test_generate_recipes_changelog_get_deletion_commit(mock_subprocess_run):
    mock_sp_blame = Mock()
    mock_sp_log = Mock()
    mock_sp_blame.returncode = 0
    mock_sp_blame.stdout = b'last_commit\n'
    mock_sp_log.returncode = 0
    mock_sp_log.stdout = b'deletion_commit_time deletion_commit_hash'
    mock_subprocess_run.side_effect = [mock_sp_blame, mock_sp_log]
    assert generate_recipes_changelog.get_deletion_commit(
        'line_no',
        'filespec',
        'gitroot',
        'rev') == ('deletion_commit_time', 'deletion_commit_hash', 'gitroot')


@patch('subprocess.run')
def test_generate_recipes_changelog_get_commits_exception(mock_subprocess_run):
    mock_subprocess_run.return_value.returncode = 1
    with raises(Exception):
        generate_recipes_changelog.get_commits('gitargs', 'gitroot')


@patch('subprocess.run')
def test_generate_recipes_changelog_get_commits(mock_subprocess_run):
    mock_subprocess_run.return_value.returncode = 0
    mock_subprocess_run.return_value.stdout = b'timestamp1 hash1\ntimestamp2 hash2\n'
    expected_result = set([tuple(['timestamp1', 'hash1', 'gitroot']), tuple(['timestamp2', 'hash2', 'gitroot'])])
    assert generate_recipes_changelog.get_commits('gitargs', 'gitroot') == expected_result


@patch('subprocess.run')
def test_generate_recipes_changelog_get_commit_message_exception(mock_subprocess_run):
    mock_subprocess_run.return_value.returncode = 1
    with raises(Exception):
        generate_recipes_changelog.get_commit_message('gitargs', 'gitroot', 'msgformat')


@patch('subprocess.run')
def test_generate_recipes_changelog_get_commit_message(mock_subprocess_run):
    mock_subprocess_run.return_value.returncode = 0
    mock_subprocess_run.return_value.stdout = b'commit message\n'
    assert generate_recipes_changelog.get_commit_message('gitargs', 'gitroot', 'msgformat') == 'commit message'


@patch('kiwi_keg.tools.generate_recipes_changelog.get_commits', return_value=set())
def test_generate_recipes_changelog_git_log_empty(mock_get_commits):
    assert generate_recipes_changelog.git_log_empty('gitroot', 'rev') is True
    mock_get_commits.assert_called_with(['git', '-C', 'gitroot', 'log', '--format=%H', '--no-patch', 'rev'], 'gitroot')


def test_generate_recipes_changelog_split_path():
    assert generate_recipes_changelog.split_path('/root1/file', ['/root1', '/root2']) == ('/root1', 'file')


def test_generate_recipes_changelog_split_path_outside_roots():
    with raises(SystemExit) as e_info:
        generate_recipes_changelog.split_path('/no_such_root/file', ['/root1', '/root2'])
    assert str(e_info.value) == 'path "/no_such_root/file" is outside git roots'


def test_generate_recipes_changelog_get_date_from_epoch():
    assert generate_recipes_changelog.get_date_from_epoch('1765880000') == '2025-12-16T10:13:20'


def test_generate_recipes_changelog_main_unsupported_format():
    sys.argv = ['generate_recipes_changelog', '-f', 'foo', 'logfile']
    with raises(SystemExit) as e_info:
        generate_recipes_changelog.main()
    assert str(e_info.value) == 'Unsupported output format "foo".'


source_info = '''root:/root
range:1:2:/root/range_file
/root/full_file
deleted:3:/root/range_file'''


@patch('json.dump')
@patch('kiwi_keg.tools.generate_recipes_changelog.get_deletion_commit')
@patch('kiwi_keg.tools.generate_recipes_changelog.get_commits_from_path')
@patch('kiwi_keg.tools.generate_recipes_changelog.get_commits_from_range')
@patch('kiwi_keg.tools.generate_recipes_changelog.get_commit_message')
@patch('kiwi_keg.tools.generate_recipes_changelog.git_log_empty', return_value=False)
def test_generate_recipes_changelog_main_json(
        mock_git_log_empty,
        mock_get_commit_message,
        mock_get_commits_from_range,
        mock_get_commits_from_path,
        mock_get_deletion_commit,
        mock_json_dump
):
    mock_get_commits_from_path.return_value = set([('1', 'commit1', '/root')])
    mock_get_commits_from_range.return_value = set([('2', 'commit2', '/root')])
    mock_get_deletion_commit.return_value = ('3', 'commit3', '/root')
    mock_get_commit_message.side_effect = ['sub1', 'msg1', 'sub2', 'msg2', 'sub3', 'msg3']
    sys.argv = ['generate_recipes_changelog', '-f', 'json', '-r', '/root:rev', 'logfile']
    mock_file = mock_open(read_data=source_info)
    with patch('builtins.open', mock_file):
        generate_recipes_changelog.main()
    mock_get_deletion_commit.assert_called_with('3', 'range_file', '/root', 'rev')
    mock_json_dump.assert_called_with([
        {'change': 'sub1', 'date': '1970-01-01T00:00:03', 'details': 'msg1'},
        {'change': 'sub2', 'date': '1970-01-01T00:00:02', 'details': 'msg2'},
        {'change': 'sub3', 'date': '1970-01-01T00:00:01', 'details': 'msg3'}
    ], sys.stdout, indent=2)


@patch('json.dump')
@patch('kiwi_keg.tools.generate_recipes_changelog.get_deletion_commit')
@patch('kiwi_keg.tools.generate_recipes_changelog.get_commits_from_path')
@patch('kiwi_keg.tools.generate_recipes_changelog.get_commits_from_range')
@patch('kiwi_keg.tools.generate_recipes_changelog.get_commit_message')
@patch('kiwi_keg.tools.generate_recipes_changelog.git_log_empty', return_value=False)
def test_generate_recipes_changelog_main_json_root_tag_file_out(
        mock_git_log_empty,
        mock_get_commit_message,
        mock_get_commits_from_range,
        mock_get_commits_from_path,
        mock_get_deletion_commit,
        mock_json_dump
):
    mock_get_commits_from_path.return_value = set([('1', 'commit1', '/root')])
    mock_get_commits_from_range.return_value = set([('2', 'commit2', '/root')])
    mock_get_deletion_commit.return_value = ('3', 'commit3', '/root')
    mock_get_commit_message.side_effect = ['sub1', 'msg1', 'sub2', 'msg2', 'sub3', 'msg3']
    sys.argv = ['generate_recipes_changelog', '-f', 'json', '-r', '/root:rev', '-t', 'root_tag', '-o', 'outfile', 'logfile']
    mock_file = mock_open(read_data=source_info)
    with patch('builtins.open', mock_file):
        generate_recipes_changelog.main()
    mock_get_deletion_commit.assert_called_with('3', 'range_file', '/root', 'rev')
    mock_json_dump.assert_called_with({
        'root_tag': [
            {'change': 'sub1', 'date': '1970-01-01T00:00:03', 'details': 'msg1'},
            {'change': 'sub2', 'date': '1970-01-01T00:00:02', 'details': 'msg2'},
            {'change': 'sub3', 'date': '1970-01-01T00:00:01', 'details': 'msg3'}
        ]
    }, mock_file(), indent=2)


@patch('yaml.safe_dump')
@patch('kiwi_keg.tools.generate_recipes_changelog.get_deletion_commit')
@patch('kiwi_keg.tools.generate_recipes_changelog.get_commits_from_path')
@patch('kiwi_keg.tools.generate_recipes_changelog.get_commits_from_range')
@patch('kiwi_keg.tools.generate_recipes_changelog.get_commit_message')
@patch('kiwi_keg.tools.generate_recipes_changelog.git_log_empty', return_value=False)
def test_generate_recipes_changelog_main_yaml(
        mock_git_log_empty,
        mock_get_commit_message,
        mock_get_commits_from_range,
        mock_get_commits_from_path,
        mock_get_deletion_commit,
        mock_yaml_safe_dump
):
    mock_get_commits_from_path.return_value = set([('1', 'commit1', '/root')])
    mock_get_commits_from_range.return_value = set([('2', 'commit2', '/root')])
    mock_get_deletion_commit.return_value = ('3', 'commit3', '/root')
    mock_get_commit_message.side_effect = ['sub1', 'msg1', 'sub2', 'msg2', 'sub3', '']
    sys.argv = ['generate_recipes_changelog', '-f', 'yaml', '-r', '/root:rev', 'logfile']
    mock_file = mock_open(read_data=source_info)
    with patch('builtins.open', mock_file):
        generate_recipes_changelog.main()
    mock_get_deletion_commit.assert_called_with('3', 'range_file', '/root', 'rev')
    mock_yaml_safe_dump.assert_called_with([
        {'change': 'sub1', 'date': '1970-01-01T00:00:03', 'details': 'msg1'},
        {'change': 'sub2', 'date': '1970-01-01T00:00:02', 'details': 'msg2'},
        {'change': 'sub3', 'date': '1970-01-01T00:00:01'}
    ], sys.stdout)


@patch('yaml.safe_dump')
@patch('kiwi_keg.tools.generate_recipes_changelog.get_deletion_commit')
@patch('kiwi_keg.tools.generate_recipes_changelog.get_commits_from_path')
@patch('kiwi_keg.tools.generate_recipes_changelog.get_commits_from_range')
@patch('kiwi_keg.tools.generate_recipes_changelog.get_commit_message')
@patch('kiwi_keg.tools.generate_recipes_changelog.git_log_empty', return_value=False)
def test_generate_recipes_changelog_main_yaml_root_tag(
        mock_git_log_empty,
        mock_get_commit_message,
        mock_get_commits_from_range,
        mock_get_commits_from_path,
        mock_get_deletion_commit,
        mock_yaml_safe_dump
):
    mock_get_commits_from_path.return_value = set([('1', 'commit1', '/root')])
    mock_get_commits_from_range.return_value = set([('2', 'commit2', '/root')])
    mock_get_deletion_commit.return_value = ('3', 'commit3', '/root')
    mock_get_commit_message.side_effect = ['sub1', 'msg1', 'sub2', 'msg2', 'sub3', '']
    sys.argv = ['generate_recipes_changelog', '-f', 'yaml', '-r', '/root:rev', '-t', 'root_tag', 'logfile']
    mock_file = mock_open(read_data=source_info)
    with patch('builtins.open', mock_file):
        generate_recipes_changelog.main()
    mock_get_deletion_commit.assert_called_with('3', 'range_file', '/root', 'rev')
    mock_yaml_safe_dump.assert_called_with({
        'root_tag': [
            {'change': 'sub1', 'date': '1970-01-01T00:00:03', 'details': 'msg1'},
            {'change': 'sub2', 'date': '1970-01-01T00:00:02', 'details': 'msg2'},
            {'change': 'sub3', 'date': '1970-01-01T00:00:01'}
        ]
    }, sys.stdout)


def test_generate_recipes_changelog_main_malformed_rev_spec():
    sys.argv = ['generate_recipes_changelog', '-f', 'json', '-r', 'invalid_rev_spec', 'logfile']
    mock_file = mock_open(read_data=source_info)
    with patch('builtins.open', mock_file), raises(SystemExit) as e_info:
        generate_recipes_changelog.main()
    assert str(e_info.value) == 'Malformed revision specification "invalid_rev_spec"'


@patch('kiwi_keg.tools.generate_recipes_changelog.get_deletion_commit')
@patch('kiwi_keg.tools.generate_recipes_changelog.get_commits_from_path')
@patch('kiwi_keg.tools.generate_recipes_changelog.get_commits_from_range')
@patch('kiwi_keg.tools.generate_recipes_changelog.get_commit_message')
@patch('kiwi_keg.tools.generate_recipes_changelog.git_log_empty', return_value=True)
def test_generate_recipes_changelog_main_text(
        mock_git_log_empty,
        mock_get_commit_message,
        mock_get_commits_from_range,
        mock_get_commits_from_path,
        mock_get_deletion_commit,
        capsys
):
    mock_get_commits_from_path.return_value = set([('1', 'commit1', '/root')])
    mock_get_commits_from_range.return_value = set([('2', 'commit2', '/root')])
    mock_get_deletion_commit.return_value = ('3', 'commit3', '/root')
    mock_get_commit_message.side_effect = ['sub1', 'sub2']
    sys.argv = ['generate_recipes_changelog', '-f', 'text', '-r', '/root:rev', 'logfile']
    mock_file = mock_open(read_data=source_info)
    with patch('builtins.open', mock_file):
        generate_recipes_changelog.main()
    assert capsys.readouterr().out == 'sub1\nsub2\n'


expected_result = '''-------------------------------------------------------------------
Fri Dec 12 12:12:00 2025  - author

- Update to tag
  + sub1
  + sub2

'''


@patch('kiwi_keg.tools.generate_recipes_changelog.get_deletion_commit')
@patch('kiwi_keg.tools.generate_recipes_changelog.get_commits_from_path')
@patch('kiwi_keg.tools.generate_recipes_changelog.get_commits_from_range')
@patch('kiwi_keg.tools.generate_recipes_changelog.get_commit_message')
@patch('kiwi_keg.tools.generate_recipes_changelog.git_log_empty', return_value=True)
def test_generate_recipes_changelog_main_osc(
        mock_git_log_empty,
        mock_get_commit_message,
        mock_get_commits_from_range,
        mock_get_commits_from_path,
        mock_get_deletion_commit,
        capsys
):
    mock_get_commits_from_path.return_value = set([('1', 'commit1', '/root')])
    mock_get_commits_from_range.return_value = set([('2', 'commit2', '/root')])
    mock_get_deletion_commit.return_value = ('3', 'commit3', '/root')
    mock_get_commit_message.side_effect = ['sub1', 'msg1', 'sub2', 'msg2']
    sys.argv = ['generate_recipes_changelog', '-f', 'osc', '-r', '/root:rev', '-t', 'tag', '-a', 'author', 'logfile']
    mock_file = mock_open(read_data=source_info)
    with patch('builtins.open', mock_file), patch('kiwi_keg.tools.generate_recipes_changelog.datetime') as p_dt:
        p_dt.now.return_value = datetime.datetime(2025, 12, 12, 12, 12)
        generate_recipes_changelog.main()
    assert capsys.readouterr().out == expected_result


@patch('kiwi_keg.tools.generate_recipes_changelog.git_log_empty', return_value=True)
def test_generate_recipes_changelog_no_commits(mock_git_log_empty):
    mock_file = mock_open(read_data='')
    with patch('builtins.open', mock_file), raises(SystemExit) as e_info:
        generate_recipes_changelog.main()
    assert e_info.value.code == 2


def test_generate_recipes_changelog_repr_mstr():
    dumper = Mock()
    generate_recipes_changelog.repr_mstr(dumper, 'data')
    dumper.represent_scalar.assert_called_once()


def test_rangefile_get_ranges_multiple_unconnected_ranges():
    rf = generate_recipes_changelog.RangeFile()
    rf.add_range(2, 3)
    rf.add_range(3, 4)
    rf.add_range(7, 8)
    assert rf.get_ranges() == [(2, 4), (7, 8)]
