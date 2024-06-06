from unittest.mock import patch
from pytest import raises

from kiwi_keg.logger import Logger

from kiwi_keg.exceptions import KegLogFileSetupFailed


class TestLogger:
    def setup_method(self):
        self.log = Logger('keg')

    @patch('logging.FileHandler')
    def test_set_logfile(self, mock_file_handler):
        self.log.set_logfile('logfile')
        mock_file_handler.assert_called_once_with(
            filename='logfile', encoding='utf-8'
        )
        assert self.log.get_logfile() == 'logfile'

    @patch('logging.FileHandler')
    def test_set_logfile_raise(self, mock_file_handler):
        mock_file_handler.side_effect = KegLogFileSetupFailed('error')
        with raises(KegLogFileSetupFailed):
            self.log.set_logfile('logfile')

    def test_getLogLevel(self):
        self.log.setLogLevel(42)
        assert self.log.getLogLevel() == 42
