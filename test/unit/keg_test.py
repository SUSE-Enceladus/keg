import sys
from pytest import fixture, raises
from unittest.mock import Mock, patch, DEFAULT
import kiwi_keg.keg
from kiwi_keg.exceptions import KegError, KegKiwiValidationError


class FakeImageDefinition:
    def __init__(self):
        self.data = {
            'image': {
                '_attributes': {
                    'name': 'fake image'
                },
                'description': {
                    'specification': 'fake spec'
                },
                'preferences': {'version': '1.0.0'}
            }
        }

    def populate(self):
        pass

    def populate_header(self):
        pass


@fixture
def patched_keg():
    with patch.multiple(
        'kiwi_keg.keg',
        KegGenerator=DEFAULT,
        KegImageDefinition=DEFAULT,
        get_all_leaf_dirs=DEFAULT,
        SourceInfoGenerator=DEFAULT,
        AnnotatedPrettyPrinter=DEFAULT
    ) as mocks:
        mocks['get_all_leaf_dirs'].return_value = ['fake_image_src']
        mocks['KegImageDefinition'].return_value = FakeImageDefinition()
        pprinter = Mock()
        mocks['AnnotatedPrettyPrinter'].return_value = pprinter
        mocks['pprinter'] = pprinter
        yield mocks


def test_main_list_recipes(patched_keg, capsys):
    sys.argv = ['keg', '--verbose', '--recipes-root=fake_root', '--list-recipes']
    kiwi_keg.keg.main()
    patched_keg['get_all_leaf_dirs'].assert_called_once_with('fake_root/images')
    cap = capsys.readouterr()
    assert cap.out == 'Source         Name       Version Description\nfake_image_src fake image 1.0.0   fake spec\n'


def test_main_list_recipes_alt_version(patched_keg, capsys):
    sys.argv = ['keg', '--verbose', '--recipes-root=fake_root', '--list-recipes']
    patched_keg['KegImageDefinition']().data['image']['preferences'] = [{'version': '1.0.1'}]
    kiwi_keg.keg.main()
    patched_keg['get_all_leaf_dirs'].assert_called_once_with('fake_root/images')
    cap = capsys.readouterr()
    assert cap.out == 'Source         Name       Version Description\nfake_image_src fake image 1.0.1   fake spec\n'


def test_main_list_recipes_invalid_image(patched_keg, caplog):
    sys.argv = ['keg', '--verbose', '--recipes-root=fake_root', '--list-recipes']
    patched_keg['KegImageDefinition'].side_effect = KegError('fake error')
    kiwi_keg.keg.main()
    assert 'is not a valid image definition' in caplog.text


def test_main_list_recipes_missing_key(patched_keg, caplog):
    sys.argv = ['keg', '--verbose', '--recipes-root=fake_root', '--list-recipes']
    patched_keg['KegImageDefinition'].side_effect = KeyError('fake error')
    kiwi_keg.keg.main()
    assert 'is not a valid image definition, missing key' in caplog.text


def test_main_dump_dict(patched_keg):
    sys.argv = ['keg', '--verbose', '--recipes-root=fake_root', '--dest-dir=fake_dir', '--dump-dict', 'fake_image_src']
    kiwi_keg.keg.main()
    patched_keg['KegImageDefinition'].assert_called_once_with(
        image_name='fake_image_src',
        recipes_roots=['fake_root'],
        image_version=None,
        track_sources=False
    )
    patched_keg['pprinter'].pprint.assert_called_once_with(patched_keg['KegImageDefinition']().data)


def test_main_standard(patched_keg):
    sys.argv = ['keg', '--verbose', '--recipes-root=fake_root', '--dest-dir=fake_dir', '-s', 'fake_image_src']
    kiwi_keg.keg.main()
    patched_keg['KegImageDefinition'].assert_called_once_with(
        image_name='fake_image_src',
        recipes_roots=['fake_root'],
        image_version=None,
        track_sources=True
    )
    patched_keg['KegGenerator'].assert_called_once_with(
        image_definition=patched_keg['KegImageDefinition'](),
        dest_dir='fake_dir',
        archs=[],
        gen_profiles_comment=True
    )
    patched_keg['KegGenerator']().create_kiwi_description.assert_called_once()
    patched_keg['KegGenerator']().validate_kiwi_description.assert_called_once()
    patched_keg['KegGenerator']().create_custom_scripts.assert_called_once()
    patched_keg['KegGenerator']().create_overlays.assert_called_once()
    patched_keg['KegGenerator']().create_multibuild_file.assert_called_once()
    patched_keg['SourceInfoGenerator'].assert_called_once_with(
        image_definition=patched_keg['KegImageDefinition'](),
        dest_dir='fake_dir'
    )


def test_main_yaml(patched_keg):
    sys.argv = ['keg', '--verbose', '--recipes-root=fake_root', '--dest-dir=fake_dir', '--format-yaml', 'fake_image_src']
    kiwi_keg.keg.main()
    patched_keg['KegGenerator']().format_kiwi_description.assert_called_once_with('yaml')


def test_main_xml(patched_keg):
    sys.argv = ['keg', '--verbose', '--recipes-root=fake_root', '--dest-dir=fake_dir', '--format-xml', 'fake_image_src']
    kiwi_keg.keg.main()
    patched_keg['KegGenerator']().format_kiwi_description.assert_called_once_with('xml')


def test_main_validation_error(patched_keg, caplog):
    sys.argv = ['keg', '--verbose', '--recipes-root=fake_root', '--dest-dir=fake_dir', 'fake_image_src']
    patched_keg['KegGenerator']().validate_kiwi_description.side_effect = KegKiwiValidationError('fake validation error')
    with raises(SystemExit):
        kiwi_keg.keg.main()
    assert 'validation error' in caplog.text


def test_main_validation_error_force(patched_keg, caplog):
    sys.argv = ['keg', '--verbose', '--recipes-root=fake_root', '--dest-dir=fake_dir', '--force', 'fake_image_src']
    patched_keg['KegGenerator']().validate_kiwi_description.side_effect = KegKiwiValidationError('fake validation error')
    kiwi_keg.keg.main()
    assert 'Ignoring validation error' in caplog.text


def test_main_known_error(patched_keg, caplog):
    sys.argv = ['keg', '--verbose', '--recipes-root=fake_root', '--dest-dir=fake_dir', 'fake_image_src']
    patched_keg['KegImageDefinition'].side_effect = KegError('fake error')
    with raises(SystemExit):
        kiwi_keg.keg.main()
    assert 'fake error' in caplog.text


def test_main_keyboard_interrupt_error(patched_keg, caplog):
    sys.argv = ['keg', '--verbose', '--recipes-root=fake_root', '--dest-dir=fake_dir', 'fake_image_src']
    patched_keg['KegImageDefinition'].side_effect = KeyboardInterrupt
    with raises(SystemExit):
        kiwi_keg.keg.main()
    assert 'keg aborted by keyboard interrupt' in caplog.text


def test_main_unknown_error(patched_keg, caplog):
    sys.argv = ['keg', '--verbose', '--recipes-root=fake_root', '--dest-dir=fake_dir', 'fake_image_src']
    patched_keg['KegImageDefinition'].side_effect = Exception('fake error')
    with raises(Exception):
        kiwi_keg.keg.main()
    assert 'Unexpected error' in caplog.text
