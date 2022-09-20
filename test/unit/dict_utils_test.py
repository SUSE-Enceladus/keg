from pytest import raises
from kiwi_keg import dict_utils
from kiwi_keg.exceptions import KegDataError


class TestUtils:
    def test_rmerge_data_exception(self):
        a_dict = {'some_key': 1}
        not_a_dict = None
        with raises(KegDataError):
            dict_utils.rmerge(a_dict, not_a_dict)
        with raises(KegDataError):
            dict_utils.rmerge(not_a_dict, a_dict)
