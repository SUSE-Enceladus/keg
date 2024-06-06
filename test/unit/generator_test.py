import glob
import tarfile
import tempfile
import os
from unittest.mock import (
    patch, Mock
)
from pathlib import Path
from pytest import raises

from kiwi_keg.generator import KegGenerator, NodeAttributes
from kiwi_keg.image_definition import KegImageDefinition
from kiwi_keg.exceptions import KegError


def assert_files_equal(file1, file2):
    assert open(file1, 'r').read() == open(file2, 'r').read()


class TestKegGenerator:
    def setup_method(self):
        self.image_definition = KegImageDefinition(
            image_name='leap-jeos/15.2', recipes_roots=['../data'], image_version='1.0.0'
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
            generator = KegGenerator(self.image_definition, tmpdirname, archs=['x86_64'])
            generator.create_kiwi_description(
                overwrite=True
            )
            assert_files_equal('../data/output/leap-jeos/config.kiwi', tmpdirname + '/config.kiwi')

    @patch('kiwi_keg.image_definition.datetime')
    @patch('kiwi_keg.image_definition.version')
    def test_create_kiwi_description_single_build(
        self, mock_keg_version, mock_datetime
    ):
        self.image_definition = KegImageDefinition(
            image_name='leap-jeos-single-platform/15.2', recipes_roots=['../data'], image_version='1.0.0'
        )
        mock_keg_version.__version__ = 'keg_version'
        utc_now = Mock()
        utc_now.strftime.return_value = 'time-string'
        mock_datetime.now.return_value = utc_now
        with tempfile.TemporaryDirectory() as tmpdirname:
            generator = KegGenerator(self.image_definition, tmpdirname)
            generator.create_kiwi_description(
                overwrite=True
            )
            assert_files_equal('../data/output/leap-jeos-single-platform/config.kiwi', tmpdirname + '/config.kiwi')
            assert not os.path.exists(os.path.join(tmpdirname, '_multibuild'))

    def test_create_template_description(self):
        with tempfile.TemporaryDirectory() as tmpdirname:
            generator = KegGenerator(self.image_definition, tmpdirname)
            with raises(KegError) as exception_info:
                generator.create_template_description()
            assert 'No template schema defined' in str(exception_info.value)
            generator.image_schema = 'vm'
            generator.create_template_description()

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
            assert_files_equal(
                '../data/output/leap-jeos/config.sh', tmpdirname + '/config.sh'
            )

    @patch('kiwi_keg.generator.KegGenerator._read_template')
    def test_create_custom_scripts_no_template(self, mock_read_template):
        with tempfile.TemporaryDirectory() as tmpdirname:
            mock_read_template.side_effect = KegError('no such teamplate')
            generator = KegGenerator(self.image_definition, tmpdirname)
            generator.create_custom_scripts(overwrite=True)
            assert_files_equal(
                '../data/output/leap-jeos/config_fallback_header.sh', tmpdirname + '/config.sh'
            )

    def test_create_overlays(self):
        with tempfile.TemporaryDirectory() as tmpdirname:
            os.mkdir(os.path.join(tmpdirname, 'root'))
            generator = KegGenerator(self.image_definition, tmpdirname)
            generator.create_overlays(disable_root_tar=True, overwrite=True)

            tf_gen = tarfile.open(os.path.join(tmpdirname, 'blue.tar.gz'), 'r')
            tf_ref = tarfile.open('../data/output/leap-jeos/blue.tar.gz', 'r')
            assert tf_gen.list() == tf_ref.list()
            assert os.path.exists(os.path.join(tmpdirname, 'root/etc/motd'))

            with raises(KegError) as exception_info:
                generator.create_overlays(disable_root_tar=True, overwrite=False)

            expected_err = '{target}/root exists, use force to overwrite.'.format(target=tmpdirname)
            assert str(exception_info.value) == expected_err

    def test_create_overlays_no_archive(self):
        with tempfile.TemporaryDirectory() as tmpdirname:
            generator = KegGenerator(self.image_definition, tmpdirname)
            del self.image_definition._data['archives']
            generator.create_overlays()
            assert glob.glob(os.path.join(tmpdirname, '*tar.gz')) == []

    def test_add_dir_to_tar(self):
        image_definition = KegImageDefinition(
            image_name='leap-jeos/15.2', recipes_roots=['../data']
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            dir1_path = os.path.join(tmpdir, 'dir1')
            dir2_path = os.path.join(tmpdir, 'dir2')
            os.mkdir(dir1_path)
            os.mkdir(dir2_path)
            os.mkdir(os.path.join(dir1_path, 'etc'))
            os.mkdir(os.path.join(dir2_path, 'etc'))
            Path(os.path.join(dir1_path, 'etc', 'foo')).touch()
            Path(os.path.join(dir2_path, 'etc', 'foo')).touch()
            tar_path = os.path.join(tmpdir, 'tmp.tar')
            generator = KegGenerator(image_definition, tmpdir)
            with tarfile.open(tar_path, 'w') as tar:
                generator._add_dir_to_tar(tar, dir1_path)
                generator._add_dir_to_tar(tar, dir2_path)

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
            assert_files_equal(
                '../data/output/leap-jeos/_multibuild', tmpdir + '/_multibuild'
            )
            with raises(KegError):
                generator.create_multibuild_file(overwrite=False)

    def test_nodeattributes(self):
        attribs = {'str': 'strval', 'dict': {'item': 'value', 'flagitem': []}, 'list': ['item1', 'item2']}
        na = NodeAttributes(attribs)
        assert str(na) == "{'str': 'strval', 'dict': 'item=value flagitem', 'list': 'item1,item2'}"

    def test_create_custom_files(self):
        with tempfile.TemporaryDirectory() as tmpdirname:
            generator = KegGenerator(self.image_definition, tmpdirname, archs=['x86_64'])
            generator.create_custom_files(overwrite=True)
            assert_files_equal('../data/output/leap-jeos/_constraints', tmpdirname + '/_constraints')

    def test_create_custom_files_file_exists(self):
        with tempfile.TemporaryDirectory() as tmpdirname:
            open(os.path.join(tmpdirname, '_constraints'), 'w')
            generator = KegGenerator(self.image_definition, tmpdirname, archs=['x86_64'])
            with raises(KegError) as exception_info:
                generator.create_custom_files(overwrite=False)
            assert "{} exists".format(os.path.join(tmpdirname, '_constraints')) in \
                str(exception_info.value)
