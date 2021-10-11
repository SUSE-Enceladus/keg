import logging
import sys
from pytest import fixture
from kiwi_keg.obs_service.compose_kiwi_description import main


class TestFetchFromKeg:
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    def setup(self):
        sys.argv = [
            sys.argv[0],
            '--main-git-recipes',
            'https://github.com/SUSE-Enceladus/keg-recipes.git',
            '--image-source',
            'leap/jeos/15.2',
            '--main-branch',
            'develop'
        ]

    def test_compose_kiwi_description(self):
        with self._caplog.at_level(logging.INFO):
            main()
