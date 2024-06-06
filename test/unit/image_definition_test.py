import logging
from pytest import raises, fixture

from kiwi_keg.image_definition import KegImageDefinition
from kiwi_keg.exceptions import KegError


class TestKegImageDefinition:
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    def setup_method(self):
        self.keg_definition = KegImageDefinition(
            image_name='leap-jeos/15.2', recipes_roots=['../data'], image_version='1.0.0'
        )

    def test_setup_raises_recipes_root_not_existing(self):
        with raises(KegError):
            KegImageDefinition(
                image_name='leap-jeos/15.2', recipes_roots=['artificial']
            )

    def test_setup_raises_image_not_existing(self):
        with raises(KegError) as exception_info:
            KegImageDefinition(
                image_name='no/such/image', recipes_roots=['../data']
            )
        assert 'Image source path "no/such/image" does not exist' in \
            str(exception_info.value)

    def test_populate_raises_yaml_error(self):
        with raises(KegError) as exception_info:
            keg_definition = KegImageDefinition(
                image_name='broken-yaml', recipes_roots=['../data/broken']
            )
            keg_definition.populate()
        assert 'Error parsing image data' in \
            str(exception_info.value)

    def test_populate_raises_schema_error(self):
        with raises(KegError) as exception_info:
            keg_definition = KegImageDefinition(
                image_name='broken-schema', recipes_roots=['../data/broken']
            )
            keg_definition.populate()
        assert 'Image definition malformed' in \
            str(exception_info.value)

    def test_populate_raises_config_error(self):
        with raises(KegError) as exception_info:
            keg_definition = KegImageDefinition(
                image_name='broken-config', recipes_roots=['../data/broken']
            )
            keg_definition.populate()
        assert 'does not exist' in \
            str(exception_info.value)

    def test_populate_raises_overlay_error(self):
        with raises(KegError) as exception_info:
            keg_definition = KegImageDefinition(
                image_name='broken-overlay', recipes_roots=['../data/broken']
            )
            keg_definition.populate()
        assert 'No such overlay files module' in \
            str(exception_info.value)

    def test_include_logs_missing(self):
        keg_definition = KegImageDefinition(
            image_name='missing-include/15.2', recipes_roots=['../data'], image_version='1.0.0'
        )
        with self._caplog.at_level(logging.INFO):
            keg_definition.populate()
            assert 'Include "platform/notblue" does not exist' in self._caplog.text

    def test_check_archive_refs(self):
        with self._caplog.at_level(logging.INFO):
            self.keg_definition.populate()
            del self.keg_definition._data['archives']
            self.keg_definition._check_archive_refs()
            assert 'Referenced archive "blue.tar.gz" not defined' in self._caplog.text
