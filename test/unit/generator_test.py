import filecmp
import tempfile
from mock import (
    patch, Mock
)
from pytest import raises

from kiwi_keg.generator import KegGenerator
from kiwi_keg.image_definition import KegImageDefinition
from kiwi_keg.exceptions import KegError


class TestKegGenerator:
    def setup(self):
        self.image_definition = KegImageDefinition(
            image_name='leap/15.2', recipes_root='../data'
        )

    @patch('os.path.isdir')
    def test_setup_raises_no_kiwi_schema_configured(self, mock_os_path_is_dir):
        mock_os_path_is_dir.return_value = True
        self.image_definition.populate = Mock()
        with raises(KegError):
            KegGenerator(self.image_definition, 'dest-dir')

    @patch('os.path.exists')
    @patch('os.path.isdir')
    def test_raises_on_dest_dir_data_exists(
        self, mock_os_path_is_dir, mock_os_path_exists
    ):
        mock_os_path_is_dir.return_value = True
        mock_os_path_exists.return_value = True
        generator = KegGenerator(self.image_definition, 'dest-dir')
        with raises(KegError):
            generator.create_kiwi_description()

    @patch('os.path.isdir')
    def test_raises_on_dest_dir_does_not_exist(self, mock_os_path_is_dir):
        mock_os_path_is_dir.return_value = False
        with raises(KegError) as exception_info:
            KegGenerator(self.image_definition, 'dest-dir')
        assert "Given destination directory: 'dest-dir' does not exist" in \
            str(exception_info.value)

    def test_create_kiwi_description_raises_template_not_found(self):
        with tempfile.TemporaryDirectory() as tmpdirname:
            generator = KegGenerator(self.image_definition, tmpdirname)
            generator.image_schema = 'non-existent-schema'
            with raises(KegError):
                generator.create_kiwi_description(
                    override=True
                )

    @patch('kiwi_keg.generator.KiwiDescription')
    def test_validate_kiwi_description(self, mock_KiwiDescription):
        kiwi = Mock()
        mock_KiwiDescription.return_value = kiwi
        with tempfile.TemporaryDirectory() as tmpdirname:
            generator = KegGenerator(self.image_definition, tmpdirname)
            generator.validate_kiwi_description()
            kiwi.validate_description.assert_called_once_with()

    @patch('kiwi_keg.image_definition.datetime')
    @patch('kiwi_keg.image_definition.version')
    def test_create_kiwi_description_by_keg(
        self, mock_keg_version, mock_datetime
    ):
        mock_keg_version.__version__ = 'keg_version'
        utc_now = Mock()
        utc_now.strftime.return_value = 'time-string'
        mock_datetime.now.return_value = utc_now
        with tempfile.TemporaryDirectory() as tmpdirname:
            generator = KegGenerator(self.image_definition, tmpdirname)
            generator.create_kiwi_description(
                override=True
            )
            assert filecmp.cmp(
                '../data/keg_output/config.kiwi', tmpdirname + '/config.kiwi'
            ) is True

    @patch('kiwi_keg.generator.KiwiDescription')
    def test_format_kiwi_description(self, mock_KiwiDescription):
        kiwi = Mock()
        mock_KiwiDescription.return_value = kiwi
        with tempfile.TemporaryDirectory() as tmpdirname:
            generator = KegGenerator(self.image_definition, tmpdirname)
            generator.format_kiwi_description('xml')
            kiwi.create_XML_description.assert_called_once_with(
                tmpdirname + '/config.kiwi'
            )
            generator.format_kiwi_description('yaml')
            kiwi.create_YAML_description.assert_called_once_with(
                tmpdirname + '/config.kiwi'
            )
            with raises(KegError):
                generator.format_kiwi_description('artificial')

    def test_create_custom_scripts(self):
        with tempfile.TemporaryDirectory() as tmpdirname:
            generator = KegGenerator(self.image_definition, tmpdirname)
            generator.create_custom_scripts(override=True)
            assert filecmp.cmp(
                '../data/keg_output/config.sh', tmpdirname + '/config.sh'
            ) is True
            assert filecmp.cmp(
                '../data/keg_output/images.sh', tmpdirname + '/images.sh'
            ) is True
