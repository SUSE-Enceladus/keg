import logging
import sys
from pytest import (
    fixture, raises
)
from mock import patch
from keg.keg import main

from keg.exceptions import KegError


class TestKeg:
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    def setup(self):
        sys.argv = [
            sys.argv[0], '--verbose',
            '--recipes-root', '../data',
            '--dest-dir', 'some-target', '../data/images/leap/15.2'
        ]

    @patch('keg.keg.create_image_description')
    def test_keg(self, mock_create_image_description):
        with self._caplog.at_level(logging.DEBUG):
            main()
            mock_create_image_description.assert_called_once_with(
                '../data/images/leap/15.2', '../data', [],
                'some-target',
                False
            )

    @patch('keg.keg.create_image_description')
    @patch('sys.exit')
    def test_keg_error_conditions(
        self, mock_exit, mock_create_image_description
    ):
        mock_create_image_description.side_effect = KegError('some-error')
        with self._caplog.at_level(logging.ERROR):
            main()
            assert 'some-error' in self._caplog.text
        mock_create_image_description.side_effect = KeyboardInterrupt
        with self._caplog.at_level(logging.ERROR):
            main()
            assert 'keg aborted by keyboard interrupt' in self._caplog.text
        mock_create_image_description.side_effect = Exception
        with self._caplog.at_level(logging.ERROR):
            with raises(Exception):
                main()
            assert 'Unexpected error' in self._caplog.text
