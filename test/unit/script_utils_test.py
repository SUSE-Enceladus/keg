import os
from pytest import raises
from unittest.mock import patch, call, mock_open, Mock
from kiwi_keg import script_utils
from kiwi_keg.exceptions import KegError


config_data = [
    {
        'files': {
            'files_namespace': [
                {
                    'path': 'some_config_file',
                    'append': True,
                    'content': 'content_to_append'
                }
            ]
        },
        'scripts': {
            'scripts_namespace': [
                'config_scriptlet'
            ]
        },
        'services': {
            'services_namespace': [
                'service_one',
                {
                    'name': 'service_two',
                    'enable': False
                },
                'timer_one.timer',
                {
                    'name': 'timer_two.timer',
                    'enable': False
                },
            ]
        }
    },
    {
        'sysconfig': {
            'sysconfig_namespace': [
                {
                    'file': 'sysconfig_file',
                    'name': 'sysconfig_var',
                    'value': 'sysconfig_val'
                }
            ]
        }
    }
]


@patch('kiwi_keg.script_utils.get_script_section')
def test_script_utils_get_config_script_no_profiles(mock_get_script_section):
    mock_get_script_section.return_value = 'script_data'
    output = script_utils.get_config_script(config_data, ['scripts'])
    mock_get_script_section.assert_has_calls([
        call(config_data[0], ['scripts']),
        call(config_data[1], ['scripts']),
    ])
    assert output == 'script_data\nscript_data'


expected_output = '''
profiles="${kiwi_profiles/,/|}"
if [[ profile_one =~ ^(${profiles})$ || profile_two =~ ^(${profiles})$ ]]; then
    script_data
fi
'''


@patch('kiwi_keg.script_utils.get_script_section')
def test_script_utils_get_config_script_with_profiles(mock_get_script_section):
    cd = config_data.copy()
    cd[0]['profiles'] = ['profile_one', 'profile_two']
    del cd[1]
    mock_get_script_section.return_value = '    script_data\n'
    output = script_utils.get_config_script(cd, ['scripts'])
    mock_get_script_section.assert_called_with(cd[0], ['scripts'], '    ')
    assert output == expected_output


@patch('kiwi_keg.script_utils.get_sysconfig_section')
@patch('kiwi_keg.script_utils.get_services_section')
@patch('kiwi_keg.script_utils.get_scripts_section')
@patch('kiwi_keg.script_utils.get_files_section')
def test_script_utils_get_script_section(mock_files, mock_scripts, mock_services, mock_sysconfig):
    script_utils.get_script_section(config_data[0], ['scripts'], 'indent')
    script_utils.get_script_section(config_data[1], ['scripts'], 'indent')
    mock_files.assert_called_once_with(config_data[0]['files']['files_namespace'], 'files_namespace', 'indent')
    mock_scripts.assert_called_once_with(config_data[0]['scripts']['scripts_namespace'], 'scripts_namespace', ['scripts'])
    mock_services.assert_called_once_with(config_data[0]['services']['services_namespace'], 'services_namespace')
    mock_sysconfig.assert_called_once_with(config_data[1]['sysconfig']['sysconfig_namespace'], 'sysconfig_namespace')


def test_script_utils_get_sysconfig_section():
    data = script_utils.get_sysconfig_section(config_data[1]['sysconfig']['sysconfig_namespace'], 'sysconfig_namespace')
    assert data == 'baseUpdateSysConfig sysconfig_file sysconfig_var "sysconfig_val"\n'


def test_script_utils_get_sysconfig_section_malformed():
    with raises(KegError):
        script_utils.get_sysconfig_section([{'not': 'valid'}], 'not_valid')


def test_script_utils_get_files_section():
    data = script_utils.get_files_section(config_data[0]['files']['files_namespace'], 'files_namespace', ' ')
    assert data == ' cat >> "some_config_file" <<EOF\ncontent_to_append\nEOF\n'


def test_script_utils_get_files_section_malformed():
    with raises(KegError):
        script_utils.get_files_section([{'not': 'valid'}], ' ')


def test_script_utils_get_services_section():
    data = script_utils.get_services_section(config_data[0]['services']['services_namespace'], 'services_namespace')
    assert data == 'baseInsertService service_one\nbaseRemoveService service_two\nsystemctl enable timer_one.timer\nsystemctl disable timer_two.timer\n'


def test_script_utils_get_services_section_malformed():
    with raises(KegError):
        script_utils.get_services_section([{'not': 'valid'}], 'not_valid')


@patch('kiwi_keg.script_utils.get_script_path')
def test_script_utils_get_scripts_section(mock_get_script_path):
    mo = mock_open(read_data='script_content')
    with patch('builtins.open', mo):
        data = script_utils.get_scripts_section(config_data[0]['scripts']['scripts_namespace'], 'scripts_namespace', ['scripts'])
    assert data == 'script_content'
    mock_get_script_path.assert_called_once_with(['scripts'], 'config_scriptlet')


@patch('kiwi_keg.script_utils.get_script_path', return_value=None)
def test_script_utils_get_scripts_section_malformed(mock_get_script_path):
    with raises(KegError):
        script_utils.get_scripts_section(['no_such_script'], 'not_valid', ['scripts'])


@patch('os.scandir')
def test_script_utils_get_script_path(mock_scandir):
    mock_entry = Mock()
    mock_entry.name = 'script_name.sh'
    mock_entry.path = os.path.join('scripts', 'script_name.sh')
    mock_scandir.return_value = [mock_entry]
    data = script_utils.get_script_path(['scripts'], 'script_name')
    assert data == os.path.join('scripts', 'script_name.sh')
