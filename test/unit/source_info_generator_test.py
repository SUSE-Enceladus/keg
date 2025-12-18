from pytest import (fixture, raises)
from unittest.mock import patch, mock_open, call
import os

import kiwi_keg.source_info_generator
from kiwi_keg.exceptions import KegError
from kiwi_keg.image_definition import KegImageDefinition
from kiwi_keg.annotated_mapping import AnnotatedMapping


@fixture
def patched_source_info_generator():
    with patch('os.path.isdir', return_value=True):
        kid = KegImageDefinition('image_name', ['root'], image_version='1.0.0', track_sources=True)
        sig = kiwi_keg.source_info_generator.SourceInfoGenerator(kid, 'dest_dir')
        yield sig


@patch('kiwi_keg.image_definition.KegImageDefinition._check_image_path_exists', return_value=True)
@patch('kiwi_keg.image_definition.KegImageDefinition._check_recipes_paths_exist', return_value=True)
@patch('os.path.isdir', return_value=False)
def test_source_info_generator_create_object_missing_dir(mock_isdir, mock_recipes_paths_exist, mock_image_path_exists):
    with raises(KegError):
        kiwi_keg.source_info_generator.SourceInfoGenerator(KegImageDefinition('image_name', ['root'], image_version='1.0.0'), 'dest_dir')


@patch('kiwi_keg.image_definition.KegImageDefinition.get_build_profile_names', return_value=[])
@patch('kiwi_keg.source_info_generator.SourceInfoGenerator._get_archive_sources', return_value=['root/overlayfiles/overlay_dir'])
@patch('kiwi_keg.source_info_generator.SourceInfoGenerator._get_script_sources', return_value=['root/script.sh'])
@patch('kiwi_keg.source_info_generator.SourceInfoGenerator._get_mapping_sources', return_value=['range:1:2:root/file.yaml'])
def test_source_info_generator_write_source_info(
        mock_get_mapping_sources,
        mock_get_script_sources,
        mock_get_archive_sources,
        mock_get_build_profile_names,
        patched_source_info_generator):
    mo = mock_open()
    patched_source_info_generator.image_definition._data = AnnotatedMapping({'foo': 'bar'})
    with patch('builtins.open', mo):
        patched_source_info_generator.write_source_info()
    mock_get_mapping_sources.assert_called_once_with(
        AnnotatedMapping({'foo': 'bar'}),
        profile=None,
        skip_keys=patched_source_info_generator.internal_toplevel_keys
    )
    mock_get_script_sources.assert_called_once()
    mock_get_archive_sources.assert_called_once()
    mo.assert_has_calls([
        call(os.path.join('dest_dir', 'log_sources'), 'w'),
        call().__enter__(),
        call().write('root:root\n'),
        call().write('range:1:2:root/file.yaml\nroot/script.sh\nroot/overlayfiles/overlay_dir')
    ])


@patch('kiwi_keg.image_definition.KegImageDefinition.get_base_profile_names', return_value=[])
@patch('kiwi_keg.image_definition.KegImageDefinition.get_build_profile_names', return_value=['profile_one'])
@patch('kiwi_keg.source_info_generator.SourceInfoGenerator._get_archive_sources', return_value=['root/overlayfiles/overlay_dir'])
@patch('kiwi_keg.source_info_generator.SourceInfoGenerator._get_script_sources', return_value=['root/script.sh'])
@patch('kiwi_keg.source_info_generator.SourceInfoGenerator._get_mapping_sources', return_value=['range:1:2:root/file.yaml'])
def test_source_info_generator_write_source_info_profiles(
        mock_get_mapping_sources,
        mock_get_script_sources,
        mock_get_archive_sources,
        mock_get_build_profile_names,
        mock_get_base_profile_names,
        patched_source_info_generator):
    mo = mock_open()
    patched_source_info_generator.image_definition._data = AnnotatedMapping({'foo': 'bar'})
    with patch('builtins.open', mo):
        patched_source_info_generator.write_source_info()
    mock_get_mapping_sources.assert_called_once_with(
        AnnotatedMapping({'foo': 'bar'}),
        profile='profile_one',
        skip_keys=patched_source_info_generator.internal_toplevel_keys
    )
    mock_get_script_sources.assert_called_once_with('profile_one')
    mock_get_archive_sources.assert_called_once_with('profile_one')
    mo.assert_has_calls([
        call(os.path.join('dest_dir', 'log_sources_profile_one'), 'w'),
        call().__enter__(),
        call().write('root:root\n'),
        call().write('range:1:2:root/file.yaml\nroot/script.sh\nroot/overlayfiles/overlay_dir')
    ])


@patch('kiwi_keg.source_info_generator.SourceInfoGenerator._get_key_sources')
def test_source_info_generator_get_mapping_sources_string(mock_get_key_sources, patched_source_info_generator):
    data = AnnotatedMapping({'foo': 'bar', '__foo_line_start__': 1, '__foo_line_end__': 2, '__foo_source__': 'foo_source'})
    patched_source_info_generator._get_mapping_sources(data)
    mock_get_key_sources.assert_called_once_with('foo', data)


@patch('kiwi_keg.source_info_generator.SourceInfoGenerator._get_key_def_source')
@patch('kiwi_keg.source_info_generator.SourceInfoGenerator._get_key_sources')
def test_source_info_generator_get_mapping_sources_dict(mock_get_key_sources, mock_get_key_def_source, patched_source_info_generator):
    data = AnnotatedMapping({'foo': AnnotatedMapping({'bar': 'baz'}), '__foo_line_start__': 1, '__foo_line_end__': 2, '__foo_source__': 'foo_source'})
    patched_source_info_generator._get_mapping_sources(data)
    mock_get_key_def_source.assert_called_once_with('foo', data)
    mock_get_key_sources.assert_called_once_with('bar', data['foo'])


@patch('kiwi_keg.source_info_generator.SourceInfoGenerator._get_key_def_source')
@patch('kiwi_keg.source_info_generator.SourceInfoGenerator._get_key_sources')
def test_source_info_generator_get_mapping_sources_list_dict(mock_get_key_sources, mock_get_key_def_source, patched_source_info_generator):
    data = AnnotatedMapping({'foo': [AnnotatedMapping({'bar': 'baz'})], '__foo_line_start__': 1, '__foo_line_end__': 2, '__foo_source__': 'foo_source'})
    patched_source_info_generator._get_mapping_sources(data)
    mock_get_key_def_source.assert_called_once_with('foo', data)
    mock_get_key_sources.assert_called_once_with('bar', data['foo'][0])


@patch('kiwi_keg.source_info_generator.SourceInfoGenerator._get_key_def_source')
@patch('kiwi_keg.source_info_generator.SourceInfoGenerator._get_key_sources')
def test_source_info_generator_get_mapping_sources_list_pod(mock_get_key_sources, mock_get_key_def_source, patched_source_info_generator):
    data = AnnotatedMapping({'foo': ['bar'], '__foo_line_start__': 1, '__foo_line_end__': 2, '__foo_source__': 'foo_source'})
    patched_source_info_generator._get_mapping_sources(data)
    mock_get_key_sources.assert_called_once_with('foo', data)


def test_source_info_generator_get_mapping_sources_not_iterable(patched_source_info_generator):
    assert patched_source_info_generator._get_mapping_sources(42) == []


def test_source_info_generator_get_mapping_sources_other_profile(patched_source_info_generator):
    data = AnnotatedMapping({'_attributes': {'profiles': ['profile_one']}, 'foo': 'bar', '__foo_line_start__': 1, '__foo_line_end__': 2, '__foo_source__': 'foo_source'})
    assert patched_source_info_generator._get_mapping_sources(data, profile='profile_two') == []


def test_source_info_generator_get_mapping_sources_skipped_key(patched_source_info_generator):
    data = AnnotatedMapping({'foo': 'bar', '__foo_line_start__': 1, '__foo_line_end__': 2, '__foo_source__': 'foo_source'})
    assert patched_source_info_generator._get_mapping_sources(data, skip_keys=['foo']) == []


@patch('kiwi_keg.source_info_generator.SourceInfoGenerator._get_key_sources')
def test_source_info_generator_get_mapping_sources_profiles_section(mock_get_key_sources, patched_source_info_generator):
    data = AnnotatedMapping({
        'profile': [
            AnnotatedMapping({
                '_attributes': {'name': 'profile_one'},
                'foo': 'bar', '__foo_line_start__': 1, '__foo_line_end__': 2, '__foo_source__': 'foo_source'
            })
        ]
    })
    patched_source_info_generator._get_mapping_sources(data, profile='profile_one')
    mock_get_key_sources.assert_has_calls([
        call('_attributes', data['profile'][0]),
        call('foo', data['profile'][0])
    ])


@patch('kiwi_keg.source_info_generator.SourceInfoGenerator._get_key_sources')
def test_source_info_generator_get_mapping_deleted_key(mock_get_key_sources, patched_source_info_generator):
    data = AnnotatedMapping({'__deleted_foo': {}, '__foo_line_start__': 1, '__foo_line_end__': 2, '__foo_source__': 'foo_source'})
    patched_source_info_generator._get_mapping_sources(data)
    mock_get_key_sources.assert_called_once_with('foo', data)


def test_source_info_generator_get_key_sources(patched_source_info_generator):
    data = AnnotatedMapping({'foo': 'bar', '__foo_line_start__': 1, '__foo_line_end__': 2, '__foo_source__': 'foo_source'})
    assert patched_source_info_generator._get_key_sources('foo', data) == 'range:1:2:foo_source'


def test_source_info_generator_get_key_sources_missing(patched_source_info_generator, caplog):
    data = AnnotatedMapping({'foo': 'bar'})
    assert patched_source_info_generator._get_key_sources('foo', data) is None
    assert 'Source information for key foo missing' in caplog.text


def test_source_info_generator_get_key_def_source(patched_source_info_generator):
    data = AnnotatedMapping({'foo': 'bar', '__foo_line_start__': 1, '__foo_line_end__': 2, '__foo_source__': 'foo_source'})
    assert patched_source_info_generator._get_key_def_source('foo', data) == 'range:1:1:foo_source'


def test_source_info_generator_get_key_def_source_missing(patched_source_info_generator, caplog):
    data = AnnotatedMapping({'foo': 'bar'})
    assert patched_source_info_generator._get_key_def_source('foo', data) is None
    assert 'Source information for key foo missing' in caplog.text


def test_source_info_generator_get_profiles_attrib_no_annotated_mapping(patched_source_info_generator):
    data = {'foo': 'bar'}
    assert patched_source_info_generator._get_profiles_attrib(data) == [None]


def test_source_info_generator_get_profiles_attrib_profiles(patched_source_info_generator):
    data = AnnotatedMapping({'profiles': AnnotatedMapping()})
    assert patched_source_info_generator._get_profiles_attrib(data) is None


def test_source_info_generator_get_profiles_attrib(patched_source_info_generator):
    data = AnnotatedMapping({'_attributes': {'profiles': ['profile_one']}})
    assert patched_source_info_generator._get_profiles_attrib(data) == ['profile_one']


def test_source_info_generator_get_archive_profiles(patched_source_info_generator):
    patched_source_info_generator.image_definition._data = {
        'image': {
            'packages': [{
                'archive': [{
                    '_attributes': {
                        'name': 'archive_one'
                    }
                }],
                '_attributes': {
                    'profiles': ['profile_one']
                }
            }]
        }
    }
    assert patched_source_info_generator._get_archive_profiles('archive_one') == ['profile_one']


@patch('kiwi_keg.image_definition.KegImageDefinition.get_base_profile_names', return_value=[])
@patch('kiwi_keg.source_info_generator.SourceInfoGenerator._get_archive_profiles', return_value=['profile_one'])
@patch('kiwi_keg.source_info_generator.SourceInfoGenerator._get_mapping_sources', return_value=['archive_sources'])
def test_source_info_generator_get_archive_sources(
        mock_get_mapping_sources,
        mock_get_archive_profiles,
        mock_get_base_profile_names,
        patched_source_info_generator):
    patched_source_info_generator.image_definition._data = {
        'archive': [{
            'name': 'archive.tar.gz'
        }],
        'archives': {
            'archive.tar.gz': ['overlay_dir_one', 'overlay_dir_two']
        }
    }
    result = patched_source_info_generator._get_archive_sources(profile='profile_one')
    mock_get_base_profile_names.assert_called_with('profile_one')
    mock_get_archive_profiles.assert_called_with('archive.tar.gz')
    mock_get_mapping_sources.assert_called_with({'name': 'archive.tar.gz'})
    assert result == ['archive_sources', 'overlay_dir_one', 'overlay_dir_two']


@patch('kiwi_keg.image_definition.KegImageDefinition.get_base_profile_names', return_value=[])
@patch('kiwi_keg.source_info_generator.SourceInfoGenerator._get_archive_profiles', return_value=['profile_two'])
@patch('kiwi_keg.source_info_generator.SourceInfoGenerator._get_mapping_sources', return_value=['archive_sources'])
def test_source_info_generator_get_archive_sources_no_match(
        mock_get_mapping_sources,
        mock_get_archive_profiles,
        mock_get_base_profile_names,
        patched_source_info_generator):
    patched_source_info_generator.image_definition._data = {
        'archive': [{
            'name': 'archive.tar.gz'
        }],
        'archives': {
            'archive.tar.gz': ['overlay_dir_one', 'overlay_dir_two']
        }
    }
    result = patched_source_info_generator._get_archive_sources(profile='profile_one')
    mock_get_base_profile_names.assert_called_with('profile_one')
    mock_get_archive_profiles.assert_called_with('archive.tar.gz')
    mock_get_mapping_sources.assert_not_called()
    assert result == []


@patch('kiwi_keg.source_info_generator.script_utils.get_script_path', return_value='scriptlet_path')
@patch('kiwi_keg.source_info_generator.SourceInfoGenerator._get_profiles_attrib', return_value=['profile_one'])
@patch('os.path.exists', return_value=True)
def test_source_info_generator_get_script_sources(mock_path_exists, mock_get_profiles_attrib, mock_get_script_path, patched_source_info_generator):
    patched_source_info_generator.image_definition._data = {
        'config': [
            {
                'scripts': {
                    'scripts_namespace': [
                        'scriptlet'
                    ]
                }
            }
        ]
    }
    result = patched_source_info_generator._get_script_sources(profile='profile_one')
    mock_get_profiles_attrib.assert_called_with({'scripts': {'scripts_namespace': ['scriptlet']}})
    assert result == ['scriptlet_path']


@patch('kiwi_keg.source_info_generator.script_utils.get_script_path')
@patch('kiwi_keg.source_info_generator.SourceInfoGenerator._get_profiles_attrib', return_value=['profile_two'])
@patch('os.path.exists', return_value=True)
def test_source_info_generator_get_script_sources_no_match(
        mock_path_exists,
        mock_get_profiles_attrib,
        mock_get_script_path,
        patched_source_info_generator):
    patched_source_info_generator.image_definition._data = {
        'config': [
            {
                'scripts': {
                    'scripts_namespace': [
                        'scriptlet'
                    ]
                }
            }
        ]
    }
    result = patched_source_info_generator._get_script_sources(profile='profile_one')
    mock_get_script_path.assert_not_called()
    assert result == []
