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

expected_list_output = """\
Source                         Name                           Version  Description
leap-jeos-single-platform/15.1 Leap15.1-JeOS                  1.0.0    Leap 15.1 guest image
leap-jeos-single-platform/15.2 Leap15.2-JeOS                  1.0.0    Leap 15.2 guest image
leap-jeos/15.1                 Leap15.1-JeOS                  1.0.0    Leap 15.1 guest image
leap-jeos/15.2                 Leap15.2-JeOS                  1.0.0    Leap 15.2 guest image
"""


class TestKeg:
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    def setup(self):
        sys.argv = [
            sys.argv[0], '--verbose',
            '--recipes-root', '../data',
            '--image-version=1.0.42',
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
                recipes_roots=['../data'],
                image_version='1.0.42',
                track_sources=False
            )
            mock_KegGenerator.assert_called_once_with(
                image_definition=image_definition,
                dest_dir='some-target',
                archs=[],
                gen_profiles_comment=True
            )
            image_generator.create_kiwi_description.assert_called_once_with(
                overwrite=False
            )
            image_generator.validate_kiwi_description.assert_called_once_with()
            image_generator.create_custom_scripts.assert_called_once_with(
                overwrite=False
            )
            image_generator.create_overlays.assert_called_once_with(
                disable_root_tar=False, overwrite=False
            )
            image_generator.create_multibuild_file.assert_called_once_with(
                overwrite=False
            )

    @patch('kiwi_keg.keg.SourceInfoGenerator')
    @patch('kiwi_keg.keg.KegImageDefinition')
    @patch('kiwi_keg.keg.KegGenerator')
    def test_keg_write_source_info(self, mock_KegGenerator, mock_KegImageDefinition, mock_SourceInfoGenerator):
        sys.argv += ['--write-source-info']
        image_definition = Mock()
        mock_KegImageDefinition.return_value = image_definition
        image_generator = Mock()
        mock_KegGenerator.return_value = image_generator
        source_info_generator = Mock()
        mock_SourceInfoGenerator.return_value = source_info_generator
        with self._caplog.at_level(logging.DEBUG):
            main()
            mock_KegImageDefinition.assert_called_once_with(
                image_name='../data/images/leap/15.2',
                recipes_roots=['../data'],
                image_version='1.0.42',
                track_sources=True
            )
            mock_KegGenerator.assert_called_once_with(
                image_definition=image_definition,
                dest_dir='some-target',
                archs=[],
                gen_profiles_comment=True
            )
            image_generator.create_kiwi_description.assert_called_once_with(
                overwrite=False
            )
            image_generator.validate_kiwi_description.assert_called_once_with()
            image_generator.create_custom_scripts.assert_called_once_with(
                overwrite=False
            )
            image_generator.create_overlays.assert_called_once_with(
                disable_root_tar=False, overwrite=False
            )
            image_generator.create_multibuild_file.assert_called_once_with(
                overwrite=False
            )
            source_info_generator.write_source_info.assert_called_once_with(
                overwrite=False
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

    def test_keg_list_recipes(self, capsys):
        sys.argv = [
            sys.argv[0], '--list-recipes',
            '--recipes-root', '../data'
        ]
        with self._caplog.at_level(logging.ERROR):
            main()
            cap = capsys.readouterr()
            assert cap.out == expected_list_output

    def test_keg_list_recipes_broken(self, capsys):
        sys.argv = [
            sys.argv[0], '--list-recipes',
            '--recipes-root', '../data/broken'
        ]
        with self._caplog.at_level(logging.ERROR):
            main()
            assert 'is not a valid image' in self._caplog.text

    @patch('kiwi_keg.keg.AnnotatedPrettyPrinter')
    @patch('kiwi_keg.keg.KegImageDefinition')
    @patch('kiwi_keg.keg.KegGenerator')
    def test_keg_dump(self, mock_KegGenerator, mock_KegImageDefinition, mock_pprinter):
        sys.argv = [
            sys.argv[0], '--verbose', '--dump-dict',
            '--recipes-root', '../data',
            '--dest-dir', 'some-target', '../data/images/leap/15.2'
        ]
        image_definition = Mock()
        mock_KegImageDefinition.return_value = image_definition
        pprinter = Mock()
        mock_pprinter.return_value = pprinter
        with self._caplog.at_level(logging.DEBUG):
            main()
            mock_KegImageDefinition.assert_called_once_with(
                image_name='../data/images/leap/15.2',
                recipes_roots=['../data'],
                image_version=None,
                track_sources=False
            )
            image_definition.populate.assert_called_once()
            pprinter.pprint.assert_called_once_with(image_definition.data)
