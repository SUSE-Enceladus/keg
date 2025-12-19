from pytest import raises
from kiwi_keg import dict_utils
from kiwi_keg.annotated_mapping import AnnotatedMapping
from kiwi_keg.exceptions import KegDataError


def test_rmerge_dict():
    src_dict = {'string': 'new_string', 'dict': {3: 'c'}, 'del_key': None}
    dest_dict = {'string': 'orig_string', 'dict': {1: 'a', 2: 'b'}, 'del_key': 'foo'}

    dict_utils.rmerge(src_dict, dest_dict)
    assert dest_dict == {'string': 'new_string', 'dict': {1: 'a', 2: 'b', 3: 'c'}}


def test_rmerge_annotated_mapping():
    src_dict = AnnotatedMapping({'string': 'new_string', 'dict': {3: 'c'}, 'del_key': None})
    dest_dict = AnnotatedMapping({'string': 'orig_string', 'dict': {1: 'a', 2: 'b'}, 'del_key': 'foo', '__hidden_key__': 'hidden_val'})

    dict_utils.rmerge(src_dict, dest_dict)
    assert dict(dest_dict.all_items()) == {
        'string': 'new_string',
        'dict': {1: 'a', 2: 'b', 3: 'c'},
        '__hidden_key__': 'hidden_val',
        '__deleted_del_key': {}
    }


def test_get_attribute():
    data = {'_attributes': {'foo': 'bar'}}
    assert dict_utils.get_attribute(data, 'foo') == 'bar'


def test_get_attribute_defaults():
    data = {'_attributes': {'foo': 'bar'}}
    assert dict_utils.get_attribute(data, 'baz', 42) == 42


def test_get_merged_list():
    data = {
        '_namespace_one': {
            'key': [1, 2]
        },
        '_namespace_two': {
            'key': [3]
        }
    }
    assert dict_utils.get_merged_list(data, 'key') == [1, 2, 3]


def test_rmerge_data_exception():
    a_dict = {'some_key': 1}
    not_a_dict = None
    with raises(KegDataError):
        dict_utils.rmerge(a_dict, not_a_dict)
    with raises(KegDataError):
        dict_utils.rmerge(not_a_dict, a_dict)
