from pytest import raises
from kiwi_keg import script_utils
from kiwi_keg.exceptions import KegError


class TestScriptUtils:
    def test_get_sections_errors(self):
        mock_data = [{'wrongtags': 'foo'}]
        with raises(KegError):
            script_utils.get_sysconfig_section(mock_data, 'fake-section')
        with raises(KegError):
            script_utils.get_files_section(mock_data, 'fake-section')
        with raises(KegError):
            script_utils.get_services_section(mock_data, 'fake-section')
        mock_data = ['nosuchscript']
        with raises(KegError):
            script_utils.get_scripts_section(mock_data, 'fake-section', [])
