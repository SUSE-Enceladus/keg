import logging
import os
import sys
import tempfile
from unittest.mock import (
    Mock, patch, call
)
from pytest import fixture, raises
from kiwi_keg.tools.compose_kiwi_description import (
    main,
    generate_changelog,
    get_image_version,
    get_revision_args,
    parse_revisions,
    update_revisions,
    update_changelog,
    RepoInfo
)


class TestFetchFromKeg:
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    def setup(self):
        sys.argv = [
            sys.argv[0],
            '--git-recipes',
            'https://github.com/SUSE-Enceladus/keg-recipes.git',
            '--git-recipes',
            'https://github.com/SUSE-Enceladus/keg-recipes2.git',
            '--image-source',
            'leap/jeos/15.2',
            '--git-branch',
            'develop',
            '--outdir',
            'obs_out'
        ]

    @patch('kiwi_keg.tools.compose_kiwi_description.update_revisions')
    @patch('os.remove')
    @patch('kiwi_keg.tools.compose_kiwi_description.get_revision_args')
    @patch('glob.glob')
    @patch('kiwi_keg.tools.compose_kiwi_description.SourceInfoGenerator')
    @patch('kiwi_keg.tools.compose_kiwi_description.XMLDescription')
    @patch('kiwi_keg.tools.compose_kiwi_description.Temporary.new_dir')
    @patch('kiwi_keg.tools.compose_kiwi_description.KegImageDefinition')
    @patch('kiwi_keg.tools.compose_kiwi_description.KegGenerator')
    @patch('kiwi_keg.tools.compose_kiwi_description.Command.run')
    @patch('kiwi_keg.tools.compose_kiwi_description.Path.create')
    @patch('os.path.exists')
    def test_compose_kiwi_description(
        self, mock_path_exists, mock_Path_create, mock_Command_run,
        mock_KegGenerator, mock_KegImageDefinition, mock_Temporary_new_dir,
        mock_XMLDescription, mock_SourceInfoGenerator, mock_glob,
        mock_get_revision_args, mock_remove, mock_update_revisions
    ):
        xml_data = Mock()
        preferences = Mock()
        preferences.get_version.return_value = ['1.1.1']
        xml_data.get_preferences.return_value = [preferences]
        description = Mock()
        description.load.return_value = xml_data
        mock_XMLDescription.return_value = description
        mock_path_exists.side_effect = [False, False, True, True, True, False]
        image_definition = Mock()
        mock_KegImageDefinition.return_value = image_definition
        image_generator = Mock()
        mock_KegGenerator.return_value = image_generator
        temp_dir = Mock()
        mock_Temporary_new_dir.return_value = temp_dir
        source_info_generator = Mock()
        mock_SourceInfoGenerator.return_value = source_info_generator
        mock_glob.return_value = ['obs_out/log_sources_flavor1', 'obs_out/log_sources_flavor2']
        mock_get_revision_args.return_value = ['-r', 'fake_repo:fake_rev..']
        mock_result = Mock()
        mock_result.returncode = 0
        mock_Command_run.return_value = mock_result

        with patch('builtins.open', create=True):
            main()

        mock_Path_create.assert_called_once_with('obs_out')
        assert mock_Command_run.call_args_list == [
            call(
                [
                    'git', 'clone', '-b', 'develop',
                    'https://github.com/SUSE-Enceladus/keg-recipes.git',
                    temp_dir.name
                ]
            ),
            call(
                [
                    'git', '-C', temp_dir.name,
                    'show', '--no-patch', '--format=%H', 'HEAD'
                ]
            ),
            call(
                [
                    'git', 'clone',
                    'https://github.com/SUSE-Enceladus/keg-recipes2.git',
                    temp_dir.name
                ]
            ),
            call(
                [
                    'git', '-C', temp_dir.name,
                    'show', '--no-patch', '--format=%H', 'HEAD'
                ]
            ),
            call(
                [
                    'generate_recipes_changelog',
                    '-o', 'obs_out/flavor1.changes.yaml',
                    '-f', 'yaml',
                    '-t', '1.1.2',
                    '-r', 'fake_repo:fake_rev..',
                    'obs_out/log_sources_flavor1'
                ], raise_on_error=False
            ),
            call(
                [
                    'generate_recipes_changelog',
                    '-o', 'obs_out/flavor2.changes.yaml',
                    '-f', 'yaml',
                    '-t', '1.1.2',
                    '-r', 'fake_repo:fake_rev..',
                    'obs_out/log_sources_flavor2'
                ], raise_on_error=False
            )
        ]
        mock_KegImageDefinition.assert_called_once_with(
            image_name='leap/jeos/15.2',
            recipes_roots=[temp_dir.name, temp_dir.name],
            track_sources=True,
            image_version='1.1.2'
        )
        mock_KegGenerator.assert_called_once_with(
            image_definition=image_definition, dest_dir='obs_out', archs=[]
        )
        image_generator.create_kiwi_description.assert_called_once_with(
            overwrite=True
        )
        image_generator.create_custom_scripts.assert_called_once_with(
            overwrite=True
        )
        image_generator.create_overlays.assert_called_once_with(
            disable_root_tar=False, overwrite=True
        )
        mock_XMLDescription.assert_called_once_with(
            'config.kiwi'
        )
        assert mock_remove.call_args_list == [
            call('obs_out/log_sources_flavor1'),
            call('obs_out/log_sources_flavor2')
        ]
        source_info_generator.write_source_info.assert_called_once()
        mock_update_revisions.assert_called_once()

    @patch('kiwi_keg.tools.compose_kiwi_description.update_revisions')
    @patch('os.walk')
    @patch('os.remove')
    @patch('kiwi_keg.tools.compose_kiwi_description.get_revision_args')
    @patch('glob.glob')
    @patch('kiwi_keg.tools.compose_kiwi_description.SourceInfoGenerator')
    @patch('kiwi_keg.tools.compose_kiwi_description.XMLDescription')
    @patch('kiwi_keg.tools.compose_kiwi_description.Temporary.new_dir')
    @patch('kiwi_keg.tools.compose_kiwi_description.KegImageDefinition')
    @patch('kiwi_keg.tools.compose_kiwi_description.KegGenerator')
    @patch('kiwi_keg.tools.compose_kiwi_description.Command.run')
    @patch('kiwi_keg.tools.compose_kiwi_description.Path.create')
    @patch('os.path.exists')
    def test_compose_kiwi_description_no_version_bump(
        self, mock_path_exists, mock_Path_create, mock_Command_run,
        mock_KegGenerator, mock_KegImageDefinition, mock_Temporary_new_dir,
        mock_XMLDescription, mock_SourceInfoGenerator, mock_glob,
        mock_get_revision_args, mock_remove, mock_walk, mock_update_revisions
    ):
        sys.argv = [
            sys.argv[0],
            '--git-recipes',
            'https://github.com/SUSE-Enceladus/keg-recipes.git',
            '--image-source',
            'leap/jeos/15.2',
            '--git-branch',
            'develop',
            '--outdir',
            'obs_out',
            '--version-bump=false'
        ]
        xml_data = Mock()
        preferences = Mock()
        preferences.get_version.return_value = ['1.1.1']
        xml_data.get_preferences.return_value = [preferences]
        description = Mock()
        description.load.return_value = xml_data
        mock_XMLDescription.return_value = description
        mock_path_exists.side_effect = [False, True, True, True]
        image_definition = Mock()
        mock_KegImageDefinition.return_value = image_definition
        image_generator = Mock()
        mock_KegGenerator.return_value = image_generator
        temp_dir = Mock()
        mock_Temporary_new_dir.return_value = temp_dir
        source_info_generator = Mock()
        mock_SourceInfoGenerator.return_value = source_info_generator
        mock_glob.return_value = ['obs_out/log_sources']
        mock_get_revision_args.return_value = ['-r', 'fake_repo:fake_rev..']
        mock_result = Mock()
        mock_result.returncode = 2
        mock_Command_run.return_value = mock_result
        mock_walk.return_value = iter([('obs_out', [], ['config.kiwi'])])

        with patch('builtins.open', create=True), raises(SystemExit), self._caplog.at_level(logging.WARNING):
            main()

        assert 'Image has no changes.' in self._caplog.text

        mock_Path_create.assert_called_once_with('obs_out')
        assert mock_Command_run.call_args_list == [
            call(
                [
                    'git', 'clone', '-b', 'develop',
                    'https://github.com/SUSE-Enceladus/keg-recipes.git',
                    temp_dir.name
                ]
            ),
            call(
                [
                    'git', '-C', temp_dir.name,
                    'show', '--no-patch', '--format=%H', 'HEAD'
                ]
            ),
            call(
                [
                    'generate_recipes_changelog',
                    '-o', 'obs_out/changes.yaml',
                    '-f', 'yaml',
                    '-t', '1.1.1',
                    '-r', 'fake_repo:fake_rev..',
                    'obs_out/log_sources'
                ], raise_on_error=False
            )
        ]
        mock_KegImageDefinition.assert_called_once_with(
            image_name='leap/jeos/15.2',
            recipes_roots=[temp_dir.name],
            track_sources=True,
            image_version=None
        )
        mock_KegGenerator.assert_called_once_with(
            image_definition=image_definition, dest_dir='obs_out', archs=[]
        )
        image_generator.create_kiwi_description.assert_called_once_with(
            overwrite=True
        )
        image_generator.create_custom_scripts.assert_called_once_with(
            overwrite=True
        )
        image_generator.create_overlays.assert_called_once_with(
            disable_root_tar=False, overwrite=True
        )
        mock_XMLDescription.assert_called_once_with(
            'obs_out/config.kiwi'
        )
        preferences.set_version.assert_not_called()
        source_info_generator.write_source_info.assert_called_once()
        mock_remove.assert_called_once_with('obs_out/config.kiwi')

    @patch('os.path.exists')
    def test_too_many_branch_args(self, mock_path_exists):
        mock_path_exists.return_value = True
        sys.argv += ['--git-branch=foo', '--git-branch=bar']
        with raises(SystemExit) as sysex:
            main()
        assert sysex.value.code == 'Number of --git-branch arguments must not exceed number of git repos.'

    def test_update_revisions(self):
        mock_repo = Mock()
        mock_repo.path = 'fake_dir'
        mock_repo.head_commit = '1234'
        repos = {'fake_repo': mock_repo}

        with tempfile.TemporaryDirectory() as tmpdirname:
            update_revisions(repos, tmpdirname)
            assert open(os.path.join(tmpdirname, '_keg_revisions'), 'r').read() == 'fake_repo 1234\n'

    @patch('kiwi_keg.tools.compose_kiwi_description.XMLDescription')
    def test_image_version_error(self, mock_XMLDescription):
        xml_data = Mock()
        preferences = Mock()
        preferences.get_version.return_value = None
        xml_data.get_preferences.return_value = [preferences]
        description = Mock()
        description.load.return_value = xml_data
        mock_XMLDescription.return_value = description
        with raises(SystemExit) as sysex:
            get_image_version(mock_XMLDescription)
        assert sysex.value.code == 'Cannot determine image version.'

    @patch('kiwi_keg.tools.compose_kiwi_description.get_head_commit_hash')
    def test_parse_revisions(self, mock_get_head_commit_hash):
        mock_dir = Mock()
        mock_dir.name = 'dir1'
        mock_get_head_commit_hash.return_value = '1234'
        repo = RepoInfo(mock_dir)
        repos = {'repo1': repo}
        with tempfile.TemporaryDirectory() as tmpdirname:
            with open(os.path.join(tmpdirname, '_keg_revisions'), 'w') as outf:
                outf.write('repo1 hash1\nrepo2 hash2\n')

            old_wd = os.getcwd()
            os.chdir(tmpdirname)

            with self._caplog.at_level(logging.WARNING):
                parse_revisions(repos)
                assert 'Cannot map URL "repo2" to repository.' in self._caplog.text

            os.remove('_keg_revisions')
            with self._caplog.at_level(logging.WARNING):
                parse_revisions(repos)
                assert 'No _keg_revision file.' in self._caplog.text

            with open(os.path.join(tmpdirname, '_keg_revisions'), 'w') as outf:
                outf.write('INVALID')

            with raises(SystemExit) as sysex:
                parse_revisions(repos)
            assert sysex.value.code == 'Malformed revision spec "INVALID".'

            os.chdir(old_wd)

    @patch('kiwi_keg.tools.compose_kiwi_description.get_head_commit_hash')
    def test_get_revision_args(self, mock_get_head_commit_hash):
        mock_dir = Mock()
        mock_dir.name = 'dir1'
        mock_get_head_commit_hash.return_value = '5678'
        repo = RepoInfo(mock_dir)
        repo.set_start_commit('1234')
        repos = {'repo1': repo}
        assert repo.head_commit == '5678'
        assert get_revision_args(repos) == ['-r', 'dir1:1234..']

    @patch('kiwi_keg.tools.compose_kiwi_description.Command.run')
    def test_changelog_prepend(self, mock_run):
        with tempfile.TemporaryDirectory() as tmpdirname:
            old_wd = os.getcwd()
            os.chdir(tmpdirname)
            open('changes.yaml', 'w').write('old entry\n')
            open('changes.yaml.new', 'w').write('new entry\n')
            update_changelog('changes.yaml', 'changes.yaml.new')
            assert open('changes.yaml.new', 'r').read() == 'new entry\nold entry\n'
            os.chdir(old_wd)

    @patch('kiwi_keg.tools.compose_kiwi_description.parse_revisions')
    @patch('kiwi_keg.tools.compose_kiwi_description.RepoInfo')
    @patch('kiwi_keg.tools.compose_kiwi_description.Command.run')
    @patch('os.path.exists')
    def test_no_new_commits(self, mock_path_exists, mock_run, mock_repo_info, mock_parse_revisions):
        mock_path_exists.return_value = True
        mock_repo_info.has_commits.return_value = False
        with self._caplog.at_level(logging.INFO):
            with raises(SystemExit):
                main()
            assert 'No repository has new commits.' in self._caplog.text
            assert 'Aborting.' in self._caplog.text

    @patch('kiwi_keg.tools.compose_kiwi_description.Command.run')
    def test_generate_changelog_error(self, mock_Command_run):
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.error = 'That went totally wrong'
        mock_Command_run.return_value = mock_result
        with raises(SystemExit) as sysex:
            generate_changelog('log_sources', 'changes.yaml', '1.1.1', ['-r', 'fakerev'])
        assert sysex.value.code == 'Error generating change log: That went totally wrong'
