import tempfile
import yaml
from xmldiff import main
from pytest import raises, fail
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
            '../data/output/invalid/config_invalid.xml'
        )
        with raises(KegKiwiValidationError):
            kiwi_invalid.validate_description()

    @patch('shutil.copy')
    def test_create_description_failed(self, mock_shutil_copy):
        mock_shutil_copy.side_effect = Exception
        kiwi = KiwiDescription('../data/output/xml/config.xml')
        with raises(KegKiwiDescriptionError):
            kiwi._create_description('/tmp/outfile', 'xml')

    def test_create_XML_description(self):
        kiwi = KiwiDescription('../data/output/xml/config.kiwi')
        with tempfile.NamedTemporaryFile() as tmpfile:
            kiwi.create_XML_description(tmpfile.name)
            diff = main.diff_files(
                '../data/output/xml/config.xml', tmpfile.name
            )
            if len(diff):
                if len(diff) == 1 and diff[0].name == 'schemaversion':
                    # allow schemaversion to diff, may happen with newer kiwi
                    pass
                else:
                    fail('configs differ: diff')

    def test_create_YAML_description(self):
        kiwi = KiwiDescription('../data/output/yaml/config.kiwi')
        with tempfile.NamedTemporaryFile() as tmpfile:
            kiwi.create_YAML_description(tmpfile.name)
            y1 = yaml.safe_load(open('../data/output/yaml/config.yaml', 'r').read())
            y2 = yaml.safe_load(open(tmpfile.name, 'r').read())
            # allow schemaversion to diff, may happen with newer kiwi
            y1['image']['@schemaversion'] = y2['image']['@schemaversion']
            assert y1 == y2
