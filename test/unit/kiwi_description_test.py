import tempfile
import filecmp
from xmldiff import main
from pytest import raises
from mock import patch

from kiwi_keg.kiwi_description import KiwiDescription

from kiwi_keg.exceptions import (
    KegDescriptionNotFound,
    KegKiwiValidationError,
    KegKiwiDescriptionError
)


class TestKiwiDescription:
    def test_init_raises(self):
        with raises(KegDescriptionNotFound):
            KiwiDescription('does-not-exist')

    def test_validate_description_from_Keg_invalid_XML(self):
        kiwi_invalid = KiwiDescription(
            '../data/keg_output_invalid/config_invalid.xml'
        )
        with raises(KegKiwiValidationError):
            kiwi_invalid.validate_description()

    @patch('shutil.copy')
    def test_create_description_failed(self, mock_shutil_copy):
        mock_shutil_copy.side_effect = Exception
        kiwi = KiwiDescription('../data/keg_output_xml/config.xml')
        with raises(KegKiwiDescriptionError):
            kiwi._create_description('/tmp/outfile', 'xml')

    def test_create_XML_description(self):
        kiwi = KiwiDescription('../data/keg_output_xml/config.kiwi')
        with tempfile.NamedTemporaryFile() as tmpfile:
            kiwi.create_XML_description(tmpfile.name)
            diff = main.diff_files(
                '../data/keg_output_xml/config.xml', tmpfile.name
            )
            assert len(diff) == 0

    def test_create_YAML_description(self):
        kiwi = KiwiDescription('../data/keg_output_yaml/config.kiwi')
        with tempfile.NamedTemporaryFile() as tmpfile:
            kiwi.create_YAML_description(tmpfile.name)
            assert filecmp.cmp(
                '../data/keg_output_yaml/config.yaml', tmpfile.name
            ) is True
