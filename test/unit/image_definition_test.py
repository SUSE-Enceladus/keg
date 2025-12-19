import os
from pytest import raises, fixture
from unittest.mock import patch, DEFAULT, call
from datetime import datetime
from schema import SchemaError

from kiwi_keg.image_definition import KegImageDefinition
from kiwi_keg.exceptions import KegDataError
from kiwi_keg.annotated_mapping import AnnotatedMapping


@fixture
def patched_image_definition():
    with patch.multiple(
            'kiwi_keg.image_definition.KegImageDefinition',
            _check_recipes_paths_exist=DEFAULT,
            _check_image_path_exists=DEFAULT
    ) as mocks:
        mocks['_check_recipes_paths_exist'].return_value = True
        mocks['_check_image_path_exists'].return_value = True
        patch('datetime.now', return_value=datetime(2025, 12, 4))
        image_definition = KegImageDefinition('image_name', ['root'], '1.0.0')
        yield image_definition


@fixture
def patched_image_definition_tracking():
    with patch.multiple(
            'kiwi_keg.image_definition.KegImageDefinition',
            _check_recipes_paths_exist=DEFAULT,
            _check_image_path_exists=DEFAULT
    ) as mocks:
        mocks['_check_recipes_paths_exist'].return_value = True
        mocks['_check_image_path_exists'].return_value = True
        patch('datetime.now', return_value=datetime(2025, 12, 4))
        image_definition = KegImageDefinition('image_name', ['root'], '1.0.0', track_sources=True)
        yield image_definition


def test_image_object_with_tracking(patched_image_definition_tracking):
    pass


@patch('kiwi_keg.image_schema.ImageSchema.validate')
@patch('kiwi_keg.image_definition.KegImageDefinition._check_archive_refs')
@patch('kiwi_keg.image_definition.KegImageDefinition._generate_config_scripts')
@patch('kiwi_keg.image_definition.KegImageDefinition._generate_overlay_info')
@patch('kiwi_keg.image_definition.KegImageDefinition._expand_includes')
@patch('kiwi_keg.file_utils.get_recipes')
def test_image_definition_populate(
        mock_get_recipes,
        mock_expand_includes,
        mock_generate_overlay_info,
        mock_generate_config_scripts,
        mock_check_archive_refs,
        mock_image_schema_validate,
        patched_image_definition):
    mock_get_recipes.return_value = {'image': {'preferences': {'version': '0.9.9'}}}
    patched_image_definition.populate()
    mock_image_schema_validate.assert_called_once()
    mock_generate_config_scripts.assert_called_once()
    mock_generate_overlay_info.assert_called_once()
    mock_check_archive_refs.assert_called_once()


@patch('kiwi_keg.image_schema.ImageSchema.validate')
@patch('kiwi_keg.image_definition.KegImageDefinition._check_archive_refs')
@patch('kiwi_keg.image_definition.KegImageDefinition._generate_config_scripts')
@patch('kiwi_keg.image_definition.KegImageDefinition._generate_overlay_info')
@patch('kiwi_keg.image_definition.KegImageDefinition._expand_includes')
@patch('kiwi_keg.file_utils.get_recipes')
def test_image_definition_populate_prefs_list(
        mock_get_recipes,
        mock_expand_includes,
        mock_generate_overlay_info,
        mock_generate_config_scripts,
        mock_check_archive_refs,
        mock_image_schema_validate,
        patched_image_definition):
    mock_get_recipes.return_value = {'image': {'preferences': [{'version': '0.9.9'}]}}
    patched_image_definition.populate()
    mock_image_schema_validate.assert_called_once()
    mock_generate_config_scripts.assert_called_once()
    mock_generate_overlay_info.assert_called_once()
    mock_check_archive_refs.assert_called_once()


@patch('kiwi_keg.file_utils.get_recipes')
def test_image_definition_populate_parse_error(mock_get_recipes, patched_image_definition):
    mock_get_recipes.side_effect = KegDataError('fake parse error')
    with raises(KegDataError) as err:
        patched_image_definition.populate()
        assert 'Error parsing image data' in str(err)


@patch('kiwi_keg.image_schema.ImageSchema.validate')
@patch('kiwi_keg.image_definition.KegImageDefinition._check_archive_refs')
@patch('kiwi_keg.image_definition.KegImageDefinition._generate_config_scripts')
@patch('kiwi_keg.image_definition.KegImageDefinition._generate_overlay_info')
@patch('kiwi_keg.image_definition.KegImageDefinition._expand_includes')
@patch('kiwi_keg.file_utils.get_recipes')
def test_image_definition_populate_schema_error(
        mock_get_recipes,
        mock_expand_includes,
        mock_generate_overlay_info,
        mock_generate_config_scripts,
        mock_check_archive_refs,
        mock_image_schema_validate,
        patched_image_definition):
    mock_get_recipes.return_value = {'image': {'preferences': [{'version': '0.9.9'}]}}
    mock_image_schema_validate.side_effect = SchemaError('fake validation error')
    with raises(KegDataError) as err:
        patched_image_definition.populate()
        assert 'Image definition malformed' in str(err)


@patch('kiwi_keg.image_definition.KegImageDefinition._expand_includes')
@patch('kiwi_keg.file_utils.get_recipes')
def test_image_definition_populate_general_error(
        mock_get_recipes,
        mock_expand_includes,
        patched_image_definition):
    mock_get_recipes.return_value = {'image': {'preferences': [{'version': '0.9.9'}]}}
    mock_expand_includes.side_effect = Exception('fake error')
    with raises(KegDataError) as err:
        patched_image_definition.populate()
        assert 'Error generating profile data' in str(err)


@patch('kiwi_keg.image_definition.KegImageDefinition._expand_includes')
@patch('kiwi_keg.file_utils.get_recipes')
def test_image_definition_popluate_header(mock_get_recipes, mock_expand_includes, patched_image_definition):
    mock_get_recipes.return_value = {'image': {'description': {'foo': 'bar'}}}
    patched_image_definition.populate_header()
    mock_expand_includes.assert_called_once_with({'foo': 'bar'})


@patch('kiwi_keg.file_utils.get_recipes')
def test_image_definition_popluate_header_error(mock_get_recipes, patched_image_definition):
    mock_get_recipes.side_effect = Exception('fake exception')
    with raises(KegDataError) as err:
        patched_image_definition.populate_header()
        assert 'Error parsing image data' in str(err)


def test_get_profiles(patched_image_definition):
    patched_image_definition._data = {'image': {'profiles': {'profile': ['profile_one', 'profile_two']}}}
    assert patched_image_definition.get_profiles() == ['profile_one', 'profile_two']


def test_get_profiles_empty(patched_image_definition):
    patched_image_definition._data = {'image': {}}
    assert patched_image_definition.get_profiles() == []


def test_get_build_profile_names(patched_image_definition):
    patched_image_definition._data = {
        'image': {
            'preferences': [
                {'_attributes': {'profiles': ['profile_one']}},
                {'_attributes': {'profiles': ['profile_two', 'profile_three']}}
            ]
        }
    }
    assert patched_image_definition.get_build_profile_names() == ['profile_one', 'profile_two', 'profile_three']


def test_get_base_profile_names(patched_image_definition):
    patched_image_definition._data = {
        'image': {
            'profiles': {
                'profile': [
                    {
                        '_attributes': {'name': 'profile_one'},
                        'requires': {
                            '_attributes': {'profile': 'base_profile'}
                        }
                    }
                ]
            }
        }
    }
    assert patched_image_definition.get_base_profile_names('profile_one') == ['base_profile']


@patch('os.path.isdir', return_value=False)
def test_check_recipes_paths_exist_error(mock_isdir):
    with raises(KegDataError):
        KegImageDefinition('image_name', ['root'], '1.0.0')


@patch('kiwi_keg.image_definition.KegImageDefinition._check_recipes_paths_exist')
@patch('os.path.isdir', return_value=True)
def test_check_image_paths_exist(mock_isdir, mock_check_recipes_paths_exist):
    KegImageDefinition('image_name', ['root'], '1.0.0')


@patch('kiwi_keg.image_definition.KegImageDefinition._check_recipes_paths_exist')
@patch('os.path.isdir', return_value=False)
def test_check_image_paths_exist_error(mock_isdir, mock_check_recipes_paths_exist):
    with raises(KegDataError):
        KegImageDefinition('image_name', ['root'], '1.0.0')


def test_check_archive_refs_error(patched_image_definition, caplog):
    patched_image_definition._data = {
        'image': {
            'packages': [
                {
                    '_attributes': {'type': 'image'},
                    'archive': [{'_attributes': {'name': 'foo.tar.gz'}}]
                }
            ]
        },
        'archives': [
            {'name': 'bar.tar.gz'}
        ]
    }
    patched_image_definition._check_archive_refs()
    assert 'Referenced archive "foo.tar.gz" not defined' in caplog.text


@patch('kiwi_keg.image_definition.KegImageDefinition._expand_include')
def test_expand_includes(mock_expand_include, patched_image_definition):
    data = {'_include': ['some-include']}
    patched_image_definition._expand_includes(data)
    mock_expand_include.assert_called_once_with(data, None)


@patch('kiwi_keg.image_definition.KegImageDefinition._expand_include')
def test_expand_includes_list(mock_expand_include, patched_image_definition):
    data = [{'_include': ['some-include']}]
    patched_image_definition._expand_includes(data)
    mock_expand_include.assert_called_once_with(data[0], None)


@patch('kiwi_keg.file_utils.get_recipes')
@patch('os.path.exists', return_value=False)
def test_expand_include(mock_path_exists, mock_get_recipes, patched_image_definition):
    data = AnnotatedMapping({'_include': 'some-include'})
    mock_get_recipes.return_value = AnnotatedMapping({'root': {'included': 'data'}})
    patched_image_definition._expand_include(data, 'root')
    assert data == {'included': 'data'}


@patch('kiwi_keg.script_utils.get_config_script')
@patch('os.path.exists', return_value=True)
def test_generate_config_scripts(mock_path_exists, mock_get_config_script, patched_image_definition):
    patched_image_definition._data = {'config': {'fake_config': {}}, 'setup': {'fake_setup': {}}}
    patched_image_definition._generate_config_scripts()
    mock_get_config_script.assert_has_calls(
        [
            call({'fake_config': {}}, [os.path.join('root', 'data', 'scripts')]),
            call({'fake_setup': {}}, [os.path.join('root', 'data', 'scripts')])
        ]
    )


@patch('kiwi_keg.image_definition.KegImageDefinition._add_dir_to_archive')
def test_generate_overlay_info(mock_add_dir_to_archive, patched_image_definition):
    patched_image_definition._data = {'archive': [{'name': 'foo', '_namespace_foo': {'_include_overlays': ['overlay_dir']}}]}
    patched_image_definition._generate_overlay_info()
    mock_add_dir_to_archive.assert_called_once_with('foo', 'overlay_dir')


@patch('os.path.exists', return_value=True)
def test_add_dir_to_archive(mock_path_exists, patched_image_definition):
    patched_image_definition._data = {'archives': {}}
    patched_image_definition._add_dir_to_archive('foo-archive', 'overlay_module')
    assert patched_image_definition._data == {'archives': {'foo-archive': [os.path.join('root', 'data', 'overlayfiles', 'overlay_module')]}}


@patch('os.path.exists', return_value=False)
def test_add_dir_to_archive_missing(mock_path_exists, patched_image_definition):
    patched_image_definition._data = {'archives': {}}
    with raises(KegDataError) as err:
        patched_image_definition._add_dir_to_archive('foo-archive', 'no_such_overlay_module')
        assert 'No such overlay files module' in str(err)


def test_keg_image_definition_properties(patched_image_definition):
    patched_image_definition._data = {'archives': ['foo-archive']}
    patched_image_definition._config_script = 'config_script'
    patched_image_definition._images_script = 'images_script'
    assert patched_image_definition.data == patched_image_definition._data
    assert patched_image_definition.dict_type == patched_image_definition._dict_type
    assert patched_image_definition.recipes_roots == patched_image_definition._recipes_roots
    assert patched_image_definition.archives == ['foo-archive']
    assert patched_image_definition.config_script == 'config_script'
    assert patched_image_definition.images_script == 'images_script'
