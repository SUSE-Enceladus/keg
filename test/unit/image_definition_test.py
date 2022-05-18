from pytest import raises

from kiwi_keg.image_definition import KegImageDefinition
from kiwi_keg.exceptions import KegError


class TestKegImageDefinition:
    def setup(self):
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
