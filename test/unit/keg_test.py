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
                override=False
            )
            image_generator.validate_kiwi_description.assert_called_once_with()
            image_generator.create_custom_scripts.assert_called_once_with(
                override=False
            )
            image_generator.create_overlays.assert_called_once_with(
                disable_root_tar=False
            )

    @patch('kiwi_keg.keg.KegImageDefinition')
    @patch('kiwi_keg.keg.KegGenerator')
    def test_keg_format_xml(self, mock_KegGenerator, mock_KegImageDefinition):
        sys.argv += ['--format-xml']
        image_definition = Mock()
        mock_KegImageDefinition.return_value = image_definition
        image_generator = Mock()
        mock_KegGenerator.return_value = image_generator
        with self._caplog.at_level(logging.DEBUG):
            main()
            image_generator.format_kiwi_description.assert_called_once_with(
                'xml'
            )

    @patch('kiwi_keg.keg.KegImageDefinition')
    @patch('kiwi_keg.keg.KegGenerator')
    def test_keg_format_yaml(self, mock_KegGenerator, mock_KegImageDefinition):
        sys.argv += ['--format-yaml']
        image_definition = Mock()
        mock_KegImageDefinition.return_value = image_definition
        image_generator = Mock()
        mock_KegGenerator.return_value = image_generator
        with self._caplog.at_level(logging.DEBUG):
            main()
            image_generator.format_kiwi_description.assert_called_once_with(
                'yaml'
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

    @patch('kiwi_keg.keg.KegImageDefinition')
    def test_keg_list_recipes(self, mock_KegImageDefinition):
        sys.argv = [
            sys.argv[0], '--list-recipes',
            '--recipes-root', '../data'
        ]
        image_definition = Mock()
        image_definition.list_recipes.return_value = []
        mock_KegImageDefinition.return_value = image_definition
        with self._caplog.at_level(logging.ERROR):
            main()
            mock_KegImageDefinition.assert_called_once_with(
                image_name='',
                recipes_root='../data',
                data_roots=[]
            )
            assert image_definition.list_recipes.called

    @patch('pprint.pprint')
    @patch('kiwi_keg.keg.KegImageDefinition')
    @patch('kiwi_keg.keg.KegGenerator')
    def test_keg_dump(self, mock_KegGenerator, mock_KegImageDefinition, mock_pprint):
        sys.argv = [
            sys.argv[0], '--verbose', '--dump',
            '--recipes-root', '../data',
            '--dest-dir', 'some-target', '../data/images/leap/15.2'
        ]
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
            mock_pprint.assert_called_once_with(image_definition.data, indent=2)
