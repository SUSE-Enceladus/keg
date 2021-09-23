import logging
import sys
from pytest import fixture
from kiwi_keg.obs_service.fetch_from_keg import main


class TestFetchFromKeg:
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    def setup(self):
        sys.argv = [
            sys.argv[0],
            '--git-recipes',
            'https://github.com/SUSE-Enceladus/keg-recipes.git',
            '--image-source',
            'leap/jeos/15.2',
            '--branch',
            'develop'
        ]

    def test_fetch_from_keg(self):
        with self._caplog.at_level(logging.INFO):
            main()
