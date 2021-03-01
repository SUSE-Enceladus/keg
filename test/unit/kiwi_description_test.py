from pytest import raises
from mock import patch

from keg.kiwi_description import KiwiDescription

from keg.exceptions import (
    KegDescriptionNotFound,
    KegKiwiValidationError,
    KegKiwiDescriptionError
)


class TestKiwiDescription:
    def setup(self):
        # OK to test
        self.kiwi = KiwiDescription(
            '../data/keg_description/config.kiwi'
        )
        # Failed to validate schema and/or schematron rules
        self.kiwi_invalid = KiwiDescription(
            '../data/keg_description/config_invalid.kiwi'
        )

    def test_init_raises(self):
        with raises(KegDescriptionNotFound):
            KiwiDescription('does-not-exist')

    def test_create_XML_description_invalid_XML(self):
        with raises(KegKiwiValidationError):
            self.kiwi_invalid.create_XML_description('/tmp/outfile')

    @patch('shutil.copy')
    def test_create_XML_description_failed(self, mock_shutil_copy):
        mock_shutil_copy.side_effect = Exception
        with raises(KegKiwiDescriptionError):
            self.kiwi.create_XML_description('/tmp/outfile')

    @patch('shutil.copy')
    def test_create_XML_description(self, mock_shutil_copy):
        self.kiwi.create_XML_description('/tmp/outfile')
        call_arguments = mock_shutil_copy.call_args[0]
        assert call_arguments[0].startswith('/tmp/xslt-') is True
        assert call_arguments[1] == '/tmp/outfile'

    @patch('shutil.copy')
    def test_create_YAML_description(self, mock_shutil_copy):
        self.kiwi.create_YAML_description('/tmp/outfile')
        call_arguments = mock_shutil_copy.call_args[0]
        assert call_arguments[0].startswith('/tmp/xslt-') is True
        assert call_arguments[1] == '/tmp/outfile'
