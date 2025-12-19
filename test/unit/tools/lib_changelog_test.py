from pytest import raises
from unittest.mock import mock_open, call, patch, Mock

import json
import logging
import os
import yaml

from kiwi_keg.tools import lib_changelog


def test_lib_changelog_repr_mstr():
    yaml.add_representer(str, lib_changelog.repr_mstr, Dumper=yaml.SafeDumper)
    assert yaml.safe_dump({'key': 'single_line'}, sort_keys=False) == 'key: single_line\n'


def test_lib_changelog_repr_mstr_newline():
    yaml.add_representer(str, lib_changelog.repr_mstr, Dumper=yaml.SafeDumper)
    assert yaml.safe_dump({'key': 'multi\nline'}, sort_keys=False) == 'key: |-\n  multi\n  line\n'


def test_lib_changelog_read_changelog_txt():
    mo = mock_open()
    with patch('builtins.open', mo):
        lib_changelog.read_changelog('changelog.txt')


@patch('yaml.safe_load')
def test_lib_changelog_read_changelog_yaml(mock_yaml_safe_load):
    mo = mock_open()
    with patch('builtins.open', mo):
        lib_changelog.read_changelog('changelog.yaml')
    mo.assert_called_with('changelog.yaml', 'r')
    mock_yaml_safe_load.assert_called_with(mo())


@patch('yaml.safe_load')
def test_lib_changelog_read_changelog_yaml_error(mock_yaml_safe_load):
    mock_yaml_safe_load.side_effect = yaml.YAMLError('parse error')
    mo = mock_open()
    with patch('builtins.open', mo), raises(RuntimeError) as e_info:
        lib_changelog.read_changelog('changelog.yaml')
    assert 'Error parsing' in str(e_info.value)


@patch('json.load')
def test_lib_changelog_read_changelog_json(mock_json_load):
    mo = mock_open()
    with patch('builtins.open', mo):
        lib_changelog.read_changelog('changelog.json')
    mo.assert_called_with('changelog.json', 'r')
    mock_json_load.assert_called_with(mo())


@patch('json.load')
def test_lib_changelog_read_changelog_json_error(mock_json_load):
    mock_json_load.side_effect = json.JSONDecodeError('parse error', 'doc', 1)
    mo = mock_open()
    with patch('builtins.open', mo), raises(RuntimeError) as e_info:
        lib_changelog.read_changelog('changelog.json')
    assert 'Error parsing' in str(e_info.value)


def test_lib_changelog_read_changelog_unsupported():
    with raises(RuntimeError) as e_info:
        lib_changelog.read_changelog('changelog.foo')
    assert 'Unsupported log format' in str(e_info.value)


@patch('kiwi_keg.tools.lib_changelog.get_osc_log')
def test_lib_changelog_write_changelog_text(mock_get_osc_log):
    data = {'version': ['changes']}
    mo = mock_open()
    with patch('builtins.open', mo):
        lib_changelog.write_changelog('changelog.txt', 'txt', data)
    mo.assert_called_with('changelog.txt', 'w')
    mock_get_osc_log.assert_called_once_with('version', ['changes'])


@patch('kiwi_keg.tools.lib_changelog.get_osc_log')
def test_lib_changelog_write_changelog_text_append(mock_get_osc_log):
    data = {'version': ['changes']}
    mo = mock_open()
    with patch('builtins.open', mo):
        lib_changelog.write_changelog('changelog.txt', 'txt', data, append=True)
    mo.assert_called_with('changelog.txt', 'a')
    mock_get_osc_log.assert_called_once_with('version', ['changes'])


@patch('yaml.safe_dump')
@patch('yaml.add_representer')
def test_lib_changelog_write_changelog_yaml(mock_add_representer, mock_safe_dump):
    data = {'version': ['changes']}
    mo = mock_open()
    with patch('builtins.open', mo):
        lib_changelog.write_changelog('changelog.yaml', 'yaml', data)
    mo.assert_called_with('changelog.yaml', 'w')
    mock_add_representer.assert_called_once_with(str, lib_changelog.repr_mstr, Dumper=yaml.SafeDumper)
    mock_safe_dump.assert_called_once_with(data, mo(), sort_keys=False)


@patch('json.dump')
def test_lib_changelog_write_changelog_json(mock_dump):
    data = {'version': ['changes']}
    mo = mock_open()
    with patch('builtins.open', mo):
        lib_changelog.write_changelog('changelog.json', 'json', data)
    mo.assert_called_with('changelog.json', 'w')
    mock_dump.assert_called_once_with(data, mo(), indent=2, default=str)


@patch('subprocess.run')
def test_lib_changelog_generate_recipes_changelog(mock_run):
    mock_return = Mock
    mock_return.returncode = 0
    mock_run.return_value = mock_return
    assert lib_changelog.generate_recipes_changelog('source_log', 'changelog.yaml', 'yaml', 'image_version', ['rev_arg']) is True
    mock_run.assert_called_once_with([
        'generate_recipes_changelog',
        '-o', 'changelog.yaml',
        '-f', 'yaml',
        '-t', 'image_version',
        'rev_arg',
        'source_log'
    ])


@patch('subprocess.run')
def test_lib_changelog_generate_recipes_changelog_no_changes(mock_run):
    mock_return = Mock
    mock_return.returncode = 2
    mock_run.return_value = mock_return
    assert lib_changelog.generate_recipes_changelog('source_log', 'changelog.yaml', 'yaml', 'image_version', ['rev_arg']) is False
    mock_run.assert_called_once_with([
        'generate_recipes_changelog',
        '-o', 'changelog.yaml',
        '-f', 'yaml',
        '-t', 'image_version',
        'rev_arg',
        'source_log'
    ])


@patch('subprocess.run')
def test_lib_changelog_generate_recipes_changelog_error(mock_run):
    mock_return = Mock
    mock_return.returncode = 1
    mock_run.return_value = mock_return
    with raises(RuntimeError) as e_info:
        lib_changelog.generate_recipes_changelog('source_log', 'changelog.yaml', 'yaml', 'image_version', ['rev_arg'])
    assert str(e_info.value) == 'Error generating change log.'


expected_result = '''-------------------------------------------------------------------
Wed Apr 30 00:00:00 2025 UTC

- Update to version
  + Change summary
'''


def test_lib_changelog_get_osc_log():
    data = [{
        'change': 'Change summary',
        'date': '2025-04-30T00:00:00',
        'details': 'Change details'
    }]
    assert lib_changelog.get_osc_log('version', data) == expected_result


def multi_mock_open(*file_contents):
    mock_files = [mock_open(read_data=content).return_value for content in file_contents]
    mock_opener = mock_open()
    mock_opener.side_effect = mock_files
    return mock_opener


@patch('glob.glob', return_value=['old_log.yaml'])
def test_lib_changelog_update_changelog_yaml_concat(mock_glob):
    mock_new_log = mock_open()
    mock_old_log = mock_open(read_data='old_log_data')
    mo = mock_open()
    mo.side_effect = [mock_new_log.return_value, mock_old_log.return_value]
    with patch('builtins.open', mo):
        lib_changelog.update_changelog('changelog.yaml', 'yaml', 'image_version')
    mock_old_log().read.assert_called()
    mock_new_log().write.assert_called_with('old_log_data')


@patch('glob.glob', return_value=[])
def test_lib_changelog_update_changelog_no_old_log(mock_glob, caplog):
    with caplog.at_level(logging.INFO):
        lib_changelog.update_changelog('changelog.yaml', 'yaml', 'image_version')
    assert 'No old log' in caplog.text


@patch('glob.glob', return_value=['old_log.txt', 'old_log.yaml'])
def test_lib_changelog_update_changelog_txt(mock_glob, caplog):
    with caplog.at_level(logging.INFO):
        lib_changelog.update_changelog('changelog.yaml', 'yaml', 'image_version')
    assert 'More than one format for old log' in caplog.text
    assert 'Converting text log files is not supported' in caplog.text


@patch('kiwi_keg.tools.lib_changelog.write_changelog')
@patch('kiwi_keg.tools.lib_changelog.read_changelog', return_value='old_changes')
@patch('glob.glob', return_value=['old_log.yaml'])
def test_lib_changelog_update_changelog_yaml_to_txt(mock_glob, mock_read_changelog, mock_write_changelog):
    lib_changelog.update_changelog('changelog.txt', 'osc', 'image_version')
    mock_read_changelog.assert_called_once_with('old_log.yaml')
    mock_write_changelog.assert_called_once_with('changelog.txt', 'osc', 'old_changes', append=True)


@patch('kiwi_keg.tools.lib_changelog.write_changelog')
@patch('kiwi_keg.tools.lib_changelog.read_changelog')
@patch('glob.glob', return_value=['old_log.yaml'])
def test_lib_changelog_update_changelog_yaml_to_json(mock_glob, mock_read_changelog, mock_write_changelog):
    old_log = {
        '1.0.0': [
            {
                'change': 'old change'
            }
        ]
    }
    new_log = {
        '1.0.1': [
            {
                'change': 'new change'
            }
        ]
    }
    mock_read_changelog.side_effect = [old_log, new_log]
    lib_changelog.update_changelog('changelog.json', 'json', '1.0.1')
    mock_read_changelog.assert_has_calls([
        call('old_log.yaml'),
        call('changelog.json')
    ])
    old_log.update(new_log)
    mock_write_changelog.assert_called_once_with('changelog.json', 'json', old_log)


@patch('kiwi_keg.tools.lib_changelog.write_changelog')
@patch('kiwi_keg.tools.lib_changelog.read_changelog')
@patch('glob.glob', return_value=['old_log.yaml'])
def test_lib_changelog_update_changelog_yaml_to_json_merge_version(mock_glob, mock_read_changelog, mock_write_changelog):
    old_log = {
        '1.0.0': [
            {
                'change': 'old change'
            }
        ]
    }
    new_log = {
        '1.0.0': [
            {
                'change': 'new change'
            }
        ]
    }
    mock_read_changelog.side_effect = [old_log, new_log]
    lib_changelog.update_changelog('changelog.json', 'json', '1.0.0')
    mock_read_changelog.assert_has_calls([
        call('old_log.yaml'),
        call('changelog.json')
    ])
    old_log['1.0.0'] += new_log['1.0.0']
    mock_write_changelog.assert_called_once_with('changelog.json', 'json', old_log)


@patch('kiwi_keg.tools.lib_changelog.generate_recipes_changelog')
@patch('kiwi_keg.tools.lib_changelog.update_changelog')
def test_lib_changelog_generate_and_update(mock_update_changelog, mock_generate_recipes_changelog):
    lib_changelog.generate_and_update('outdir', 'prefix', 'log_ext', None, 'source_log', 'image_version', 'rev_args')
    mock_generate_recipes_changelog.assert_called_once_with(
        'source_log',
        os.path.join('outdir', 'prefix.changes.log_ext'),
        'log_ext',
        'image_version',
        'rev_args'
    )
    mock_update_changelog.assert_called_once_with(os.path.join('outdir', 'prefix.changes.log_ext'), 'log_ext', 'image_version')


@patch('kiwi_keg.tools.lib_changelog.write_changelog')
def test_lib_changelog_generate_and_update_supplied_changes(mock_write_changelog):
    lib_changelog.generate_and_update('outdir', '', 'log_ext', 'supplied_changes', None, 'image_version', 'rev_args')
    mock_write_changelog.assert_called_once_with(os.path.join('outdir', 'changes.log_ext'), 'log_ext', 'supplied_changes')


def test_lib_changelog_generate_and_update_bug():
    with raises(Exception):
        lib_changelog.generate_and_update('outdir', '', 'log_ext', None, None, 'image_version', 'rev_args')
