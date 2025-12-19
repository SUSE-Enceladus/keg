from io import StringIO
import os
import sys

from pytest import raises
from unittest.mock import patch

from kiwi_keg.tools import update_kiwi_description

service_data = '''<services>
    <service name="some_other_service"/>
    <service name="compose_kiwi_description">
        <param name="param1">value1</param>
        <param name="param2">value2</param>
    </service>
</services>
'''


def test_update_kiwi_descripton_parse_service():
    update_kiwi_description.parse_service(StringIO(service_data))
    assert sys.argv[-2:] == ['--param1=value1', '--param2=value2']


def test_update_kiwi_descripton_main_help(capsys):
    sys.argv = ['update_kiwi_description', '--help']
    with raises(SystemExit):
        update_kiwi_description.main()
    assert 'Usage:' in capsys.readouterr().out


def test_update_kiwi_descripton_main_version(capsys):
    sys.argv = ['update_kiwi_description', '--version']
    with raises(SystemExit):
        update_kiwi_description.main()
    assert update_kiwi_description.__version__ in capsys.readouterr().out


def test_update_kiwi_descripton_destdir_missing():
    sys.argv = ['update_kiwi_description', '-d']
    with raises(SystemExit):
        update_kiwi_description.main()


@patch('kiwi_keg.tools.update_kiwi_description.parse_service')
@patch('kiwi_keg.tools.update_kiwi_description.compose_main')
@patch('tempfile.TemporaryDirectory')
@patch('shutil.copy')
@patch('os.listdir', return_value=['keg_file'])
@patch('os.chdir', return_value=True)
@patch('os.path.exists', return_value=True)
def test_update_kiwi_descripton_success(
        mock_path_exists,
        mock_chdir,
        mock_listdir,
        mock_copy,
        mock_tempdir,
        mock_compose_main,
        mock_parse_service):
    mock_tempdir.return_value.__enter__.return_value = 'tmpdir'
    sys.argv = ['update_kiwi_description', '-d', 'destdir']
    update_kiwi_description.main()
    mock_parse_service.assert_called_once_with(os.path.join('destdir', '_service'))
    mock_chdir.assert_called_with('destdir')
    assert '--outdir=tmpdir' in sys.argv
    mock_compose_main.assert_called_once()
    mock_copy.assert_called_with(os.path.join('tmpdir', 'keg_file'), '.')


@patch('kiwi_keg.tools.update_kiwi_description.parse_service')
@patch('os.path.exists', return_value=True)
def test_update_kiwi_descripton_parse_error(mock_path_exists, mock_parse_service, capsys):
    mock_parse_service.side_effect = Exception('nope')
    sys.argv = ['update_kiwi_description', '-d', 'destdir']
    with raises(Exception):
        update_kiwi_description.main()
    assert 'Could not parse _service file' in capsys.readouterr().err
