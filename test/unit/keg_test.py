import logging
import sys
from pytest import (
    fixture, raises
)
from mock import (
    patch, Mock
)
from kiwi_keg.keg import main

from kiwi_keg.exceptions import KegError


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

    @patch('kiwi_keg.keg.KegImageDefinition')
    @patch('kiwi_keg.keg.KegGenerator')
    def test_keg(self, mock_KegGenerator, mock_KegImageDefinition):
        image_definition = Mock()
        mock_KegImageDefinition.return_value = image_definition
        image_generator = Mock()
        mock_KegGenerator.return_value = image_generator
        with self._caplog.at_level(logging.DEBUG):
            main()
            mock_KegImageDefinition.assert_called_once_with(
                image_name='../data/images/leap/15.2',
                recipes_root='../data',
                data_roots=[]
            )
            mock_KegGenerator.assert_called_once_with(
                image_definition=image_definition, dest_dir='some-target'
            )
            image_generator.create_kiwi_description.assert_called_once_with(
                False
            )
            image_generator.create_custom_scripts.assert_called_once_with(
                False
            )

    @patch('kiwi_keg.keg.KegImageDefinition')
    @patch('sys.exit')
    def test_keg_error_conditions(
        self, mock_exit, mock_KegImageDefinition
    ):
        mock_KegImageDefinition.side_effect = KegError('some-error')
        with self._caplog.at_level(logging.ERROR):
            main()
            assert 'some-error' in self._caplog.text
        mock_KegImageDefinition.side_effect = KeyboardInterrupt
        with self._caplog.at_level(logging.ERROR):
            main()
            assert 'keg aborted by keyboard interrupt' in self._caplog.text
        mock_KegImageDefinition.side_effect = Exception
        with self._caplog.at_level(logging.ERROR):
            with raises(Exception):
                main()
            assert 'Unexpected error' in self._caplog.text
