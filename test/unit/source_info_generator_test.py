from pytest import (fixture, raises)
import tempfile
import logging
import os

from kiwi_keg.source_info_generator import SourceInfoGenerator
from kiwi_keg.exceptions import KegError
from kiwi_keg.image_definition import KegImageDefinition
from kiwi_keg.annotated_mapping import AnnotatedMapping


class TestSourceInfoGenerator:
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    def setup(self):
        self.image_definition = KegImageDefinition(
            image_name='leap/15.2', recipes_root='../data', track_sources=True
        )

    def test_write_source_info(self):
        with tempfile.TemporaryDirectory() as tmpdirname:
            self.image_definition.populate()
            generator = SourceInfoGenerator(self.image_definition, tmpdirname)
            generator.write_source_info(
                overwrite=True
            )
            expected = sorted(open('../data/keg_output_source_info/log_sources_other', 'r').readlines())
            generated = sorted(open(os.path.join(tmpdirname, 'log_sources_other'), 'r').readlines())
            assert generated == expected

    def test_write_source_info_single_build(self):
        self.image_definition = KegImageDefinition(
            image_name='leap_single_build', recipes_root='../data', track_sources=True
        )
        with tempfile.TemporaryDirectory() as tmpdirname:
            self.image_definition.populate()
            generator = SourceInfoGenerator(self.image_definition, tmpdirname)
            generator.write_source_info(
                overwrite=False
            )
            expected = sorted(open('../data/keg_output_source_info/log_sources', 'r').readlines())
            generated = sorted(open(os.path.join(tmpdirname, 'log_sources'), 'r').readlines())
            assert generated == expected

    def test_write_source_info_nested(self):
        self.image_definition = KegImageDefinition(
            image_name='leap_nested_profiles/15.2', recipes_root='../data', track_sources=True
        )
        with tempfile.TemporaryDirectory() as tmpdirname:
            self.image_definition.populate()
            generator = SourceInfoGenerator(self.image_definition, tmpdirname)
            generator.write_source_info(
                overwrite=False
            )
            expected = sorted(open('../data/keg_output_source_info/log_sources_nested_one', 'r').readlines())
            generated = sorted(open(os.path.join(tmpdirname, 'log_sources_one'), 'r').readlines())
            assert generated == expected
            expected = sorted(open('../data/keg_output_source_info/log_sources_nested_other', 'r').readlines())
            generated = sorted(open(os.path.join(tmpdirname, 'log_sources_other'), 'r').readlines())
            assert generated == expected

    def test_write_source_info_raise_missing_dir(self):
        with raises(KegError) as err:
            SourceInfoGenerator(self.image_definition, 'no/such/dir')
        assert "Given destination directory: 'no/such/dir' does not exist" == str(err.value)

    def test_get_source_info_profile_non_existen(self):
        self.image_definition.populate()
        generator = SourceInfoGenerator(self.image_definition, '/tmp')
        with raises(KegError) as err:
            generator._get_source_info_profile('no_such_profile')
        assert 'Source info for nonexistent profile no_such_profile requested' == str(err.value)

    def test_get_mapping_sources_not_annotated(self):
        generator = SourceInfoGenerator(self.image_definition, '/tmp')
        with raises(KegError) as err:
            generator._get_mapping_sources({})
        assert '_get_source_info: Object is not AnnotatedMapping' in str(err.value)

    def test_get_mapping_sources_missing(self):
        generator = SourceInfoGenerator(self.image_definition, '/tmp')
        am = AnnotatedMapping({'foo': 'bar'})
        with self._caplog.at_level(logging.WARNING):
            generator._get_mapping_sources(am)
        assert 'Source information for key foo missing or incomplete' in self._caplog.text

    def test_get_archive_source_warning(self):
        generator = SourceInfoGenerator(self.image_definition, '/tmp')
        with self._caplog.at_level(logging.WARNING):
            generator._get_archive_sources(archives=['nope'])
        assert 'Error while looking up archive sources' in self._caplog.text
