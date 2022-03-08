import os
import sys
from mock import Mock, patch
from pytest import raises
from tempfile import TemporaryDirectory
from kiwi_keg.changelog_generator.generate_recipes_changelog import (
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
            '../data/keg_output_source_info/log_sources_fake'
        ]

    @patch('kiwi_keg.changelog_generator.generate_recipes_changelog.subprocess.run')
    def test_generate_recipes_changelog(self, mock_run, capsys):
        mock_stdout = Mock()
        mock_stdout.stdout.decode.side_effect = side_effects_text
        mock_stdout.returncode = 0
        mock_run.return_value = mock_stdout
        main()
        cap = capsys.readouterr()
        assert cap.out == expected_output

    @patch('kiwi_keg.changelog_generator.generate_recipes_changelog.subprocess.run')
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

    @patch('kiwi_keg.changelog_generator.generate_recipes_changelog.subprocess.run')
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

    @patch('kiwi_keg.changelog_generator.generate_recipes_changelog.subprocess.run')
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

    def test_get_commits_error(self):
        gitcmd = ['git', 'log', 'no_such_path']
        with raises(Exception) as err:
            get_commits(gitcmd, 'fake_root')
        assert 'unknown revision or path not in the working tree' in str(err.value)

    def test_get_commit_message_error(self):
        with raises(Exception) as err:
            get_commit_message('no_such_hash', '.', '%s')
        assert 'unknown revision or path not in the working tree' in str(err.value)

    def test_unsupported_format_error(self):
        sys.argv[4] = 'foo'
        with raises(SystemExit) as err:
            main()
        assert str(err.value) == 'Unsupported output format "foo".'

    def test_broken_log(self):
        sys.argv = [
            sys.argv[0],
            '../data/keg_output_source_info/log_sources_broken'
        ]
        with raises(SystemExit) as err:
            main()
        assert str(err.value) == 'path "not_that_root/some_path" is outside git roots'

    def test_malformed_rev_arg(self):
        sys.argv = [
            sys.argv[0],
            '-r', 'INVALID',
            '../data/keg_output_source_info/log_sources_broken'
        ]
        with raises(SystemExit) as err:
            main()
        assert str(err.value) == 'Malformed revision specification "INVALID"'
