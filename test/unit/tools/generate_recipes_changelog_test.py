import json
import os
import sys
from unittest.mock import Mock, patch
from pytest import raises
from tempfile import TemporaryDirectory
from kiwi_keg.tools.generate_recipes_changelog import (
    main,
    get_commits,
    get_commit_message
)

expected_output = """\
- change1
- change2
"""

expected_output_yaml = """\
- change: change1
  date: '1970-01-01T00:00:01'
- change: change2
  date: '1970-01-01T00:00:00'
  details: |-
    verbose msg
"""

expected_output_json = [
    {'change': 'change1', 'date': '1970-01-01T00:00:01'},
    {'change': 'change2', 'date': '1970-01-01T00:00:00', 'details': 'verbose msg'}
]

expected_output_osc = """\
-------------------------------------------------------------------
Thu Jan  1 00:00:01 UTC 1970 - Author

- change1
- change2

"""

expected_output_osc_tag = """\
-------------------------------------------------------------------
Thu Jan  1 00:00:01 UTC 1970

- Update to 1.0
  + change1
  + change2

"""

side_effects_text = [
    'fake_commits\n',
    '0 fake_commit_id1\n',
    '1 fake_commit_id2\n',
    '- change1\n',
    '- change2\n'
]

side_effects_yaml = [
    'fake_commits\n',
    '0 fake_commit_id1\n',
    '1 fake_commit_id2\n',
    'change1\n',
    '',
    'change2\n',
    'verbose msg\n'
]


class TestGenerateRecipesChangelog:
    def setup(self):
        sys.argv = [
            sys.argv[0],
            '-r', 'fake_root:fake_commit..',
            '-f', 'text',
            os.path.join(os.path.dirname(__file__), '../../data/output/source_info/log_sources_fake')
        ]

    @patch('subprocess.run')
    def test_generate_recipes_changelog(self, mock_run, capsys):
        mock_stdout = Mock()
        mock_stdout.stdout.decode.side_effect = side_effects_text
        mock_stdout.returncode = 0
        mock_run.return_value = mock_stdout
        main()
        cap = capsys.readouterr()
        assert cap.out == expected_output

    @patch('subprocess.run')
    def test_generate_recipes_changelog_yaml(self, mock_run):
        mock_stdout = Mock()
        mock_stdout.stdout.decode.side_effect = side_effects_yaml
        mock_stdout.returncode = 0
        mock_run.return_value = mock_stdout
        sys.argv[4] = 'yaml'
        with TemporaryDirectory() as tmpdir:
            tmpfile = os.path.join(tmpdir, 'out')
            sys.argv.append('-o')
            sys.argv.append(tmpfile)
            main()
            assert open(tmpfile, 'r').read() == expected_output_yaml

    @patch('subprocess.run')
    def test_generate_recipes_changelog_yaml_empty_log(self, mock_run):
        mock_stdout = Mock()
        mock_stdout.stdout.decode.side_effect = ['', '']
        mock_stdout.returncode = 0
        mock_run.return_value = mock_stdout
        sys.argv[4] = 'yaml'
        with TemporaryDirectory() as tmpdir:
            tmpfile = os.path.join(tmpdir, 'out')
            sys.argv.append('-o')
            sys.argv.append(tmpfile)
            with raises(SystemExit) as sysex:
                main()
                assert sysex.value.code == 2
            assert open(tmpfile, 'r').read() == '[]\n'

    @patch('subprocess.run')
    def test_generate_recipes_changelog_yaml_title(self, mock_run, capsys):
        mock_stdout = Mock()
        mock_stdout.stdout.decode.side_effect = side_effects_yaml
        mock_stdout.returncode = 0
        mock_run.return_value = mock_stdout
        sys.argv[4] = 'yaml'
        sys.argv.append('-t')
        sys.argv.append('title')
        main()
        cap = capsys.readouterr()
        assert cap.out == 'title:\n' + expected_output_yaml

    @patch('subprocess.run')
    def test_generate_recipes_changelog_json(self, mock_run):
        mock_stdout = Mock()
        mock_stdout.stdout.decode.side_effect = side_effects_yaml
        mock_stdout.returncode = 0
        mock_run.return_value = mock_stdout
        sys.argv[4] = 'json'
        with TemporaryDirectory() as tmpdir:
            tmpfile = os.path.join(tmpdir, 'out')
            sys.argv.append('-o')
            sys.argv.append(tmpfile)
            main()
            assert json.loads(open(tmpfile, 'r').read()) == expected_output_json

    @patch('subprocess.run')
    def test_generate_recipes_changelog_json_tag(self, mock_run):
        mock_stdout = Mock()
        mock_stdout.stdout.decode.side_effect = side_effects_yaml
        mock_stdout.returncode = 0
        mock_run.return_value = mock_stdout
        sys.argv[4] = 'json'
        sys.argv += ['-t', 'tag']
        with TemporaryDirectory() as tmpdir:
            tmpfile = os.path.join(tmpdir, 'out')
            sys.argv.append('-o')
            sys.argv.append(tmpfile)
            main()
            assert json.loads(open(tmpfile, 'r').read()) == {'tag': expected_output_json}

    @patch('kiwi_keg.tools.generate_recipes_changelog.datetime')
    @patch('subprocess.run')
    def test_generate_recipes_changelog_osc(self, mock_run, mock_datetime):
        mock_stdout = Mock()
        mock_stdout.stdout.decode.side_effect = side_effects_yaml
        mock_stdout.returncode = 0
        mock_run.return_value = mock_stdout
        mock_now = Mock()
        mock_now.strftime.return_value = 'Thu Jan  1 00:00:01 UTC 1970'
        mock_datetime.now.return_value = mock_now
        sys.argv[4] = 'osc'
        sys.argv += ['-a', 'Author']
        with TemporaryDirectory() as tmpdir:
            tmpfile = os.path.join(tmpdir, 'out')
            sys.argv.append('-o')
            sys.argv.append(tmpfile)
            main()
            assert open(tmpfile, 'r').read() == expected_output_osc

    @patch('kiwi_keg.tools.generate_recipes_changelog.datetime')
    @patch('subprocess.run')
    def test_generate_recipes_changelog_osc_tag(self, mock_run, mock_datetime):
        mock_stdout = Mock()
        mock_stdout.stdout.decode.side_effect = side_effects_yaml
        mock_stdout.returncode = 0
        mock_run.return_value = mock_stdout
        mock_now = Mock()
        mock_now.strftime.return_value = 'Thu Jan  1 00:00:01 UTC 1970'
        mock_datetime.now.return_value = mock_now
        sys.argv[4] = 'osc'
        sys.argv += ['-t', '1.0']
        with TemporaryDirectory() as tmpdir:
            tmpfile = os.path.join(tmpdir, 'out')
            sys.argv.append('-o')
            sys.argv.append(tmpfile)
            main()
            assert open(tmpfile, 'r').read() == expected_output_osc_tag

    def test_get_commits_error(self):
        with raises(Exception) as err:
            gitcmd = ['git', 'log', 'no_such_path']
            get_commits(gitcmd, 'fake_root')
        assert 'git exited with error' in str(err.value)

    def test_get_commit_message_error(self):
        with raises(Exception) as err:
            get_commit_message('no_such_hash', '.', '%s')
        assert 'git exited with error' in str(err.value)

    def test_unsupported_format_error(self):
        sys.argv[4] = 'foo'
        with raises(SystemExit) as err:
            main()
        assert str(err.value) == 'Unsupported output format "foo".'

    def test_broken_log(self):
        sys.argv = [
            sys.argv[0],
            os.path.join(os.path.dirname(__file__), '../../data/output/source_info/log_sources_broken')
        ]
        with raises(SystemExit) as err:
            main()
        assert str(err.value) == 'path "not_that_root/some_path" is outside git roots'

    def test_malformed_rev_arg(self):
        sys.argv = [
            sys.argv[0],
            '-r', 'INVALID',
            os.path.join(os.path.dirname(__file__), '../../data/output/source_info/log_sources_broken')
        ]
        with raises(SystemExit) as err:
            main()
        assert str(err.value) == 'Malformed revision specification "INVALID"'
