import tarfile
import filecmp
import tempfile
import os
from mock import (
    patch, Mock, call
)
from pathlib import Path
from pytest import raises
import shutil

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

    @patch('os.path.isdir')
    def test_setup_raises_no_version_set(self, mock_os_path_is_dir):
        mock_os_path_is_dir.return_value = True
        self.image_definition.populate = Mock()
        self.image_definition.data['schema'] = 'vm'
        self.image_definition.data['image'] = {}
        with raises(KegError):
            KegGenerator(self.image_definition, 'image')

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
                    overwrite=True
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
                overwrite=True
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
            generator.create_custom_scripts(overwrite=True)
            assert filecmp.cmp(
                '../data/keg_output/config.sh', tmpdirname + '/config.sh'
            ) is True

    @patch('kiwi_keg.generator.KegGenerator._read_template')
    def test_create_custom_scripts_no_template(self, mock_read_template):
        with tempfile.TemporaryDirectory() as tmpdirname:
            mock_read_template.side_effect = KegError('no such teamplate')
            generator = KegGenerator(self.image_definition, tmpdirname)
            generator.create_custom_scripts(overwrite=True)
            assert filecmp.cmp(
                '../data/keg_output/config_fallback_header.sh', tmpdirname + '/config.sh'
            ) is True

    @patch('kiwi_keg.image_definition.datetime')
    @patch('kiwi_keg.image_definition.version')
    @patch('kiwi_keg.generator.shutil.rmtree')
    @patch('kiwi_keg.generator.tarfile.open')
    @patch('kiwi_keg.generator.os.makedirs')
    @patch('kiwi_keg.generator.shutil.copy')
    def test_create_overlays(
        self, mock_shutil_copy, mock_os_makedirs, mock_tarfile_open,
        mock_shutil_rmtree, mock_keg_version, mock_datetime
    ):
        mock_add = Mock()
        mock_tarfile_open.return_value.__enter__.return_value.add = mock_add

        mock_keg_version.__version__ = 'keg_version'
        utc_now = Mock()
        utc_now.strftime.return_value = 'time-string'
        mock_datetime.now.return_value = utc_now

        overlay_src_root = '../data/data/overlayfiles'
        with tempfile.TemporaryDirectory() as tmpdirname:
            shutil.copyfile('../data/keg_output/config.kiwi', tmpdirname + '/config.kiwi')
            fake_root = os.path.join(tmpdirname, 'root')
            os.mkdir(fake_root)

            generator = KegGenerator(self.image_definition, tmpdirname)
            generator.create_kiwi_description(overwrite=True)
            generator.create_overlays(disable_root_tar=True, overwrite=True)

            mock_shutil_rmtree.assert_called_once_with(fake_root)
            calls = [
                call(fake_root),
                call(os.path.join(fake_root, '.'), exist_ok=True),
                call(os.path.join(fake_root, 'etc'), exist_ok=True)
            ]
            mock_os_makedirs.assert_has_calls(calls)
            calls = [
                call(
                    os.path.join(overlay_src_root, 'base/etc/hosts'),
                    os.path.join(fake_root, 'etc'),
                    follow_symlinks=False
                ),
                call(
                    os.path.join(overlay_src_root, 'csp/aws/etc/resolv.conf'),
                    os.path.join(fake_root, 'etc'),
                    follow_symlinks=False
                )
            ]
            mock_shutil_copy.assert_has_calls(calls, any_order=True)

            leap_tarball_dir = os.path.join(tmpdirname, 'leap_15_2.tar.gz')
            other_tarball_dir = os.path.join(tmpdirname, 'other.tar.gz')

            assert mock_tarfile_open.call_args_list == [
                call(leap_tarball_dir, "w:gz"),
                call(other_tarball_dir, "w:gz")
            ]
            calls = [
                call(
                    name=os.path.join(overlay_src_root, 'products/leap/15.2/etc'),
                    arcname='etc',
                    filter=KegGenerator._tarinfo_set_root
                ),
                call(
                    name=os.path.join(overlay_src_root, 'products/leap/15.2/usr'),
                    arcname='usr',
                    filter=KegGenerator._tarinfo_set_root
                ),
                call(
                    name=os.path.join(overlay_src_root, 'csp/aws/etc'),
                    arcname='etc',
                    filter=KegGenerator._tarinfo_set_root
                )
            ]
            mock_add.assert_has_calls(calls, any_order=True)

            with raises(KegError) as kegerror:
                generator.create_overlays(disable_root_tar=True, overwrite=False)
                assert kegerror == KegError(
                    '{target} exists, use force to overwrite.'.format(target=fake_root)
                )

            assert filecmp.cmp(
                '../data/keg_output_overlay/config.kiwi', tmpdirname + '/config.kiwi'
            ) is True

    @patch('shutil.copy')
    def test_create_no_overlays_configuration_provided(self, mock_shutil_copy):
        image_definition = KegImageDefinition(
            image_name='leap_no_overlays', recipes_root='../data'
        )
        with tempfile.TemporaryDirectory() as tmpdirname:
            generator = KegGenerator(image_definition, tmpdirname)
            generator.create_overlays(False)
            assert not mock_shutil_copy.called

    def test_tarinfo_set_root(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            some_file = os.path.join(tmpdir, 'some_file')
            Path(some_file).touch()
            tar_path = os.path.join(tmpdir, 'tmp.tar')
            with tarfile.open(tar_path, 'w') as tar:
                tar.add(some_file, filter=KegGenerator._tarinfo_set_root)
            with tarfile.open(tar_path, 'r') as tar:
                for tarinfo in tar:
                    assert tarinfo.uid == tarinfo.gid == 0
                    assert tarinfo.uname == tarinfo.gname == 'root'

    def test_create_multibuild_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = KegGenerator(self.image_definition, tmpdir)
            generator.create_multibuild_file(overwrite=False)
            assert filecmp.cmp(
                '../data/keg_output/_multibuild', tmpdir + '/_multibuild'
            )
            with raises(KegError):
                generator.create_multibuild_file(overwrite=False)
