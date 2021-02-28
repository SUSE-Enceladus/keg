import filecmp
import tempfile
from mock import (
    patch, Mock
)
from pytest import raises

from keg.generator import KegGenerator
from keg.image_definition import KegImageDefinition
from keg.exceptions import KegError


class TestKegGenerator:
    def setup(self):
        self.image_definition = KegImageDefinition(
            image_name='leap/15.2', recipes_root='../data'
        )

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

    @patch('keg.generator.KiwiDescription')
    @patch('keg.image_definition.datetime')
    def test_create_kiwi_description_by_keg(
        self, mock_datetime, mock_KiwiDescription
    ):
        utc_now = Mock()
        utc_now.strftime.return_value = 'time-string'
        mock_datetime.now.return_value = utc_now
        kiwi = Mock()
        mock_KiwiDescription.return_value = kiwi
        with tempfile.TemporaryDirectory() as tmpdirname:
            generator = KegGenerator(self.image_definition, tmpdirname)
            generator.create_kiwi_description(
                markup='xml', override=True
            )
            assert filecmp.cmp(
                '../data/keg_output/config.kiwi', tmpdirname + '/config.kiwi'
            ) is True

    @patch('keg.generator.KiwiDescription')
    def test_create_kiwi_description_markup(self, mock_KiwiDescription):
        kiwi = Mock()
        mock_KiwiDescription.return_value = kiwi
        with tempfile.TemporaryDirectory() as tmpdirname:
            generator = KegGenerator(self.image_definition, tmpdirname)
            generator.create_kiwi_description(
                markup='xml', override=True
            )
            kiwi.create_XML_description.assert_called_once_with(
                tmpdirname + '/config.kiwi'
            )
            generator.create_kiwi_description(
                markup='yaml', override=True
            )
            kiwi.create_YAML_description.assert_called_once_with(
                tmpdirname + '/config.kiwi'
            )

    def test_create_custom_scripts(self):
        with tempfile.TemporaryDirectory() as tmpdirname:
            generator = KegGenerator(self.image_definition, tmpdirname)
            generator.create_custom_scripts(override=True)
            assert filecmp.cmp(
                '../data/keg_output/config.sh', tmpdirname + '/config.sh'
            ) is True
