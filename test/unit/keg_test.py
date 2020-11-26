import logging
from pytest import fixture

from keg.keg import main
from keg.version import __version__


class TestKeg:
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    def test_keg(self):
        with self._caplog.at_level(logging.INFO):
            main()
            assert __version__ in self._caplog.text
