import filecmp
import tempfile
import os
from mock import (
    patch, Mock, call
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

    @patch('kiwi_keg.generator.shutil.rmtree')
    @patch('kiwi_keg.generator.tarfile.open')
    @patch('kiwi_keg.generator.os.makedirs')
    @patch('kiwi_keg.generator.shutil.copy')
    def test_create_overlays(
        self, mock_shutil_copy, mock_os_makedirs,
        mock_tarfile_open, mock_shutil_rmtree
    ):
        mock_add = Mock()
        mock_tarfile_open.return_value.__enter__.return_value.add = mock_add

        with tempfile.TemporaryDirectory() as tmpdirname:
            fake_root = os.path.join(tmpdirname, 'root')
            sub_root_etc = os.path.join(fake_root, 'etc')
            sub_root_usr = os.path.join(fake_root, 'usr')
            os.mkdir(fake_root)
            os.mkdir(sub_root_etc)
            os.mkdir(sub_root_usr)
            generator = KegGenerator(self.image_definition, tmpdirname)
            generator.create_overlays(True)

            dest_file = {}
            dest_file['base'] = os.path.join(tmpdirname, 'root', 'etc', 'hosts')
            dest_file['csp_aws'] = os.path.join(tmpdirname, 'root', 'etc', 'resolv.conf')
            dest_file['product'] = {
                'etc': os.path.join(tmpdirname, 'root', 'etc', 'motd'),
                'usr': os.path.join(tmpdirname, 'root', 'usr', 'lib', 'systemd', 'system', 'foo.service')
            }

            assert mock_shutil_copy.call_args_list == [
                call('../data/overlays/base/etc/hosts', dest_file.get('base')),
                call('../data/overlays/csp/aws/etc/resolv.conf', dest_file.get('csp_aws')),
                call('../data/overlays/products/leap/15.2/etc/motd', dest_file.get('product').get('etc')),
                call(
                    '../data/overlays/products/leap/15.2/usr/lib/systemd/system/foo.service',
                    dest_file.get('product').get('usr')
                )
            ]

            dest_base_dir = dest_file.get('base')
            dest_csp_dir = dest_file.get('csp_aws')
            dest_prod_dir_etc = dest_file.get('product').get('etc')
            dest_prod_dir_usr = dest_file.get('product').get('usr')

            assert mock_os_makedirs.call_args_list == [
                call(
                    os.path.dirname(dest_base_dir),
                    exist_ok=True
                ),
                call(
                    os.path.dirname(dest_csp_dir),
                    exist_ok=True
                ),
                call(
                    os.path.dirname(dest_prod_dir_etc),
                    exist_ok=True
                ),
                call(
                    os.path.dirname(dest_prod_dir_usr),
                    exist_ok=True
                )
            ]
            tarball_dir = os.path.join(tmpdirname, 'root.tar.gz')
            mock_tarfile_open.assert_called_with(tarball_dir, "w:gz")
            assert mock_add.call_args_list == [
                call(
                    sub_root_etc, arcname='etc'
                ),
                call(
                    sub_root_usr, arcname='usr'
                )
            ]

    @patch('shutil.copy')
    def test_create_no_overlays_provided(self, mock_shutil_copy):
        image_definition = KegImageDefinition(
            image_name='leap/15.1', recipes_root='../data'
        )
        with tempfile.TemporaryDirectory() as tmpdirname:
            generator = KegGenerator(image_definition, tmpdirname)
            generator.create_overlays(True)
            assert not mock_shutil_copy.called
