import logging
import os
import sys
import tempfile
from mock import (
    Mock, patch, call
)
from pytest import fixture, raises
from kiwi_keg.obs_service.compose_kiwi_description import (
    main,
    generate_changelog,
    get_image_version,
    get_revision_args,
    update_revisions
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

    @patch('kiwi_keg.obs_service.compose_kiwi_description.update_revisions')
    @patch('os.remove')
    @patch('os.rename')
    @patch('kiwi_keg.obs_service.compose_kiwi_description.get_revision_args')
    @patch('glob.glob')
    @patch('kiwi_keg.obs_service.compose_kiwi_description.SourceInfoGenerator')
    @patch('kiwi_keg.obs_service.compose_kiwi_description.XMLDescription')
    @patch('kiwi_keg.obs_service.compose_kiwi_description.Temporary.new_dir')
    @patch('kiwi_keg.obs_service.compose_kiwi_description.KegImageDefinition')
    @patch('kiwi_keg.obs_service.compose_kiwi_description.KegGenerator')
    @patch('kiwi_keg.obs_service.compose_kiwi_description.Command.run')
    @patch('kiwi_keg.obs_service.compose_kiwi_description.Path.create')
    @patch('os.path.exists')
    def test_compose_kiwi_description(
        self, mock_path_exists, mock_Path_create, mock_Command_run,
        mock_KegGenerator, mock_KegImageDefinition, mock_Temporary_new_dir,
        mock_XMLDescription, mock_SourceInfoGenerator, mock_glob,
        mock_get_revision_args, mock_rename, mock_remove,
        mock_update_revisions
    ):
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
        mock_glob.return_value = ['obs_out/log_sources_flavor1', 'obs_out/log_sources_flavor2']
        mock_get_revision_args.return_value = ['-r', 'fake_repo:fake_rev..']

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
                    'git', 'clone',
                    'https://github.com/SUSE-Enceladus/keg-recipes2.git',
                    temp_dir.name
                ]
            ),
            call(
                [
                    'generate_recipes_changelog',
                    '-o', 'obs_out/flavor1.changes.yaml.tmp',
                    '-f', 'yaml',
                    '-t', '1.1.2',
                    '-r', 'fake_repo:fake_rev..',
                    'obs_out/log_sources_flavor1'
                ]
            ),
            call(
                [
                    'generate_recipes_changelog',
                    '-o', 'obs_out/flavor2.changes.yaml.tmp',
                    '-f', 'yaml',
                    '-t', '1.1.2',
                    '-r', 'fake_repo:fake_rev..',
                    'obs_out/log_sources_flavor2'
                ]
            )
        ]
        mock_KegImageDefinition.assert_called_once_with(
            image_name='leap/jeos/15.2',
            recipes_roots=[temp_dir.name, temp_dir.name],
            track_sources=True,
            image_version='1.1.2'
        )
        mock_KegGenerator.assert_called_once_with(
            image_definition=image_definition, dest_dir='obs_out'
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
        source_info_generator.write_source_info.assert_called_once()
        mock_rename.assert_has_calls(
            [
                call('obs_out/flavor1.changes.yaml.tmp', 'obs_out/flavor1.changes.yaml'),
                call('obs_out/flavor2.changes.yaml.tmp', 'obs_out/flavor2.changes.yaml')
            ]
        )
        mock_remove.assert_has_calls(
            [
                call('obs_out/log_sources_flavor1'),
                call('obs_out/log_sources_flavor2')
            ]
        )
        mock_update_revisions.called_once_with([temp_dir.name, temp_dir.name])

    @patch('kiwi_keg.obs_service.compose_kiwi_description.update_revisions')
    @patch('os.remove')
    @patch('os.rename')
    @patch('kiwi_keg.obs_service.compose_kiwi_description.get_revision_args')
    @patch('glob.glob')
    @patch('kiwi_keg.obs_service.compose_kiwi_description.SourceInfoGenerator')
    @patch('kiwi_keg.obs_service.compose_kiwi_description.XMLDescription')
    @patch('kiwi_keg.obs_service.compose_kiwi_description.Temporary.new_dir')
    @patch('kiwi_keg.obs_service.compose_kiwi_description.KegImageDefinition')
    @patch('kiwi_keg.obs_service.compose_kiwi_description.KegGenerator')
    @patch('kiwi_keg.obs_service.compose_kiwi_description.Command.run')
    @patch('kiwi_keg.obs_service.compose_kiwi_description.Path.create')
    @patch('os.path.exists')
    def test_compose_kiwi_description_no_version_bump(
        self, mock_path_exists, mock_Path_create, mock_Command_run,
        mock_KegGenerator, mock_KegImageDefinition, mock_Temporary_new_dir,
        mock_XMLDescription, mock_SourceInfoGenerator, mock_glob,
        mock_get_revision_args, mock_rename, mock_remove,
        mock_update_revisions
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
            '--disable-version-bump'
        ]
        xml_data = Mock()
        preferences = Mock()
        preferences.get_version.return_value = ['1.1.1']
        xml_data.get_preferences.return_value = [preferences]
        description = Mock()
        description.load.return_value = xml_data
        mock_XMLDescription.return_value = description
        mock_path_exists.side_effect = [False, True, True]
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
                    'generate_recipes_changelog',
                    '-o', 'obs_out/changes.yaml.tmp',
                    '-f', 'yaml',
                    '-t', '1.1.1',
                    '-r', 'fake_repo:fake_rev..',
                    'obs_out/log_sources'
                ]
            )
        ]
        mock_KegImageDefinition.assert_called_once_with(
            image_name='leap/jeos/15.2',
            recipes_roots=[temp_dir.name],
            track_sources=True,
            image_version=None
        )
        mock_KegGenerator.assert_called_once_with(
            image_definition=image_definition, dest_dir='obs_out'
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
        mock_rename.assert_has_calls(
            [
                call('obs_out/changes.yaml.tmp', 'obs_out/changes.yaml')
            ]
        )
        mock_remove.assert_has_calls(
            [
                call('obs_out/log_sources'),
            ]
        )
        mock_update_revisions.called_once_with([temp_dir.name, temp_dir.name])

    def test_too_many_branch_args(self):
        sys.argv += ['--git-branch=foo', '--git-branch=bar']
        with raises(SystemExit) as sysex:
            main()
        assert sysex.value.code == 'Number of --git-branch arguments must not exceed number of git repos.'

    @patch('kiwi_keg.obs_service.compose_kiwi_description.Command.run')
    def test_update_revisions(self, mock_run):
        mock_dir = Mock()
        mock_dir.name = 'fake_dir'
        repos = {'fake_repo': mock_dir}
        mock_result = Mock()
        mock_result.output = '1234'
        mock_run.return_value = mock_result

        with tempfile.TemporaryDirectory() as tmpdirname:
            update_revisions(repos, tmpdirname)
            mock_run.assert_called_once_with(
                ['git', '-C', 'fake_dir', 'show', '--no-patch', '--format=%H', 'HEAD']
            )
            assert open(os.path.join(tmpdirname, '_keg_revisions'), 'r').read() == 'fake_repo 1234\n'

    @patch('kiwi_keg.obs_service.compose_kiwi_description.XMLDescription')
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

    def test_get_revision_args(self):
        mock_dir = Mock()
        mock_dir.name = 'dir1'
        repos = {'repo1': mock_dir}
        with tempfile.TemporaryDirectory() as tmpdirname:
            with open(os.path.join(tmpdirname, '_keg_revisions'), 'w') as outf:
                outf.write('repo1 hash1\nrepo2 hash2\n')

            old_wd = os.getcwd()
            os.chdir(tmpdirname)

            with self._caplog.at_level(logging.WARNING):
                get_revision_args(repos)
                assert 'Warning: Cannot map URL "repo2" to repository.' in self._caplog.text

            os.remove('_keg_revisions')
            with self._caplog.at_level(logging.WARNING):
                get_revision_args(repos)
                assert 'Warning: no _keg_revision file.' in self._caplog.text

            with open(os.path.join(tmpdirname, '_keg_revisions'), 'w') as outf:
                outf.write('INVALID')

            with raises(SystemExit) as sysex:
                get_revision_args(repos)
            assert sysex.value.code == 'Malformed revision spec "INVALID".'

            os.chdir(old_wd)

    @patch('kiwi_keg.obs_service.compose_kiwi_description.Command.run')
    def test_changelog_prepend(self, mock_run):
        with tempfile.TemporaryDirectory() as tmpdirname:
            old_wd = os.getcwd()
            os.chdir(tmpdirname)
            open('changes.yaml', 'w').write('old entry\n')
            open('changes.yaml.tmp', 'w').write('new entry\n')
            generate_changelog('log_sources', tmpdirname, '', '1.1.1', (1, 2))
            assert open('changes.yaml', 'r').read() == 'new entry\nold entry\n'
            assert not os.path.exists('changes.yaml.tmp')
            os.chdir(old_wd)
