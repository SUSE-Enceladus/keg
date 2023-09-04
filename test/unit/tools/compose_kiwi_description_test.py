import json
import logging
import os
import subprocess
import sys
import tempfile
import yaml
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


fake_changes_txt_new = '''-------------------------------------------------------------------
Fri May 12 16:37:47 2023 UTC

- new entry

'''

fake_changes_txt_merged = '''-------------------------------------------------------------------
Fri May 12 16:37:47 2023 UTC

- new entry

-------------------------------------------------------------------
Thu May 11 09:41:50 2023 UTC

- Update to 1.0
  + old entry

'''


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

    @patch('kiwi_keg.tools.compose_kiwi_description.update_changelog')
    @patch('kiwi_keg.tools.compose_kiwi_description.update_revisions')
    @patch('os.remove')
    @patch('kiwi_keg.tools.compose_kiwi_description.get_revision_args')
    @patch('glob.glob')
    @patch('kiwi_keg.tools.compose_kiwi_description.SourceInfoGenerator')
    @patch('kiwi_keg.tools.compose_kiwi_description.ET')
    @patch('kiwi_keg.tools.compose_kiwi_description.tempfile.TemporaryDirectory')
    @patch('kiwi_keg.tools.compose_kiwi_description.KegImageDefinition')
    @patch('kiwi_keg.tools.compose_kiwi_description.KegGenerator')
    @patch('kiwi_keg.tools.compose_kiwi_description.subprocess.run')
    @patch('kiwi_keg.tools.compose_kiwi_description.os.mkdir')
    @patch('os.path.exists')
    def test_compose_kiwi_description(
        self, mock_path_exists, mock_mkdir, mock_subprocess_run,
        mock_KegGenerator, mock_KegImageDefinition, mock_TemporaryDirectory,
        mock_ET, mock_SourceInfoGenerator, mock_glob,
        mock_get_revision_args, mock_remove, mock_update_revisions,
        mock_update_changelog
    ):
        mock_tree = Mock()
        mock_root = Mock()
        mock_prefs = Mock()
        mock_ver = Mock()
        mock_ET.parse.return_value = mock_tree
        mock_tree.getroot.return_value = mock_root
        mock_root.findall.return_value = [mock_prefs]
        mock_prefs.find.return_value = mock_ver
        mock_ver.text = '1.1.1'
        mock_path_exists.side_effect = [False, False, True, True, True, False]
        image_definition = Mock()
        mock_KegImageDefinition.return_value = image_definition
        image_generator = Mock()
        mock_KegGenerator.return_value = image_generator
        temp_dir = Mock()
        mock_TemporaryDirectory.return_value = temp_dir
        source_info_generator = Mock()
        mock_SourceInfoGenerator.return_value = source_info_generator
        mock_glob.return_value = ['obs_out/log_sources_flavor1', 'obs_out/log_sources_flavor2']
        mock_get_revision_args.return_value = ['-r', 'fake_repo:fake_rev..']
        mock_result = Mock()
        mock_result.returncode = 0
        mock_subprocess_run.return_value = mock_result

        with patch('builtins.open', create=True):
            main()

        mock_mkdir.assert_called_once_with('obs_out')
        assert mock_subprocess_run.call_args_list == [
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
                ],
                stdout=subprocess.PIPE, encoding='UTF-8'
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
                ],
                stdout=subprocess.PIPE, encoding='UTF-8'
            ),
            call(
                [
                    'generate_recipes_changelog',
                    '-o', 'obs_out/flavor1.changes.json',
                    '-f', 'json',
                    '-t', '1.1.2',
                    '-r', 'fake_repo:fake_rev..',
                    'obs_out/log_sources_flavor1'
                ]
            ),
            call(
                [
                    'generate_recipes_changelog',
                    '-o', 'obs_out/flavor2.changes.json',
                    '-f', 'json',
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
        mock_ET.parse.assert_called_once_with(
            'config.kiwi'
        )
        assert mock_remove.call_args_list == [
            call('obs_out/log_sources_flavor1'),
            call('obs_out/log_sources_flavor2')
        ]
        source_info_generator.write_source_info.assert_called_once()
        mock_update_revisions.assert_called_once()
        assert mock_update_changelog.call_args_list == [
            call('obs_out/flavor1.changes.json', 'json'),
            call('obs_out/flavor2.changes.json', 'json')
        ]

    @patch('kiwi_keg.tools.compose_kiwi_description.update_revisions')
    @patch('os.walk')
    @patch('os.remove')
    @patch('kiwi_keg.tools.compose_kiwi_description.get_revision_args')
    @patch('glob.glob')
    @patch('kiwi_keg.tools.compose_kiwi_description.SourceInfoGenerator')
    @patch('kiwi_keg.tools.compose_kiwi_description.ET')
    @patch('tempfile.TemporaryDirectory')
    @patch('kiwi_keg.tools.compose_kiwi_description.KegImageDefinition')
    @patch('kiwi_keg.tools.compose_kiwi_description.KegGenerator')
    @patch('kiwi_keg.tools.compose_kiwi_description.subprocess.run')
    @patch('os.mkdir')
    @patch('os.path.exists')
    def test_compose_kiwi_description_no_version_bump(
        self, mock_path_exists, mock_mkdir, mock_subprocess_run,
        mock_KegGenerator, mock_KegImageDefinition, mock_TemporaryDirectory,
        mock_ET, mock_SourceInfoGenerator, mock_glob,
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
            '--version-bump=false',
            '--changelog-format=yaml'
        ]
        mock_tree = Mock()
        mock_root = Mock()
        mock_prefs = Mock()
        mock_ver = Mock()
        mock_ET.parse.return_value = mock_tree
        mock_tree.getroot.return_value = mock_root
        mock_root.findall.return_value = [mock_prefs]
        mock_prefs.find.return_value = mock_ver
        mock_ver.text = '1.1.1'
        mock_path_exists.side_effect = [False, True, True, True]
        image_definition = Mock()
        mock_KegImageDefinition.return_value = image_definition
        image_generator = Mock()
        mock_KegGenerator.return_value = image_generator
        temp_dir = Mock()
        mock_TemporaryDirectory.return_value = temp_dir
        source_info_generator = Mock()
        mock_SourceInfoGenerator.return_value = source_info_generator
        mock_glob.return_value = ['obs_out/log_sources']
        mock_get_revision_args.return_value = ['-r', 'fake_repo:fake_rev..']
        mock_result = Mock()
        mock_result.returncode = 2
        mock_subprocess_run.return_value = mock_result
        mock_walk.return_value = iter([('obs_out', [], ['config.kiwi'])])

        with patch('builtins.open', create=True), raises(SystemExit), self._caplog.at_level(logging.WARNING):
            main()

        assert 'Image has no changes.' in self._caplog.text

        mock_mkdir.assert_called_once_with('obs_out')
        assert mock_subprocess_run.call_args_list == [
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
                ],
                stdout=subprocess.PIPE, encoding='UTF-8'
            ),
            call(
                [
                    'generate_recipes_changelog',
                    '-o', 'obs_out/changes.yaml',
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
        mock_ET.parse.assert_called_once_with(
            'obs_out/config.kiwi'
        )
        source_info_generator.write_source_info.assert_called_once()
        mock_remove.assert_called_once_with('obs_out/config.kiwi')

    @patch('kiwi_keg.tools.compose_kiwi_description.datetime')
    @patch('kiwi_keg.tools.compose_kiwi_description.write_changelog')
    @patch('kiwi_keg.tools.compose_kiwi_description.update_revisions')
    @patch('os.remove')
    @patch('kiwi_keg.tools.compose_kiwi_description.get_revision_args')
    @patch('glob.glob')
    @patch('kiwi_keg.tools.compose_kiwi_description.SourceInfoGenerator')
    @patch('kiwi_keg.tools.compose_kiwi_description.ET')
    @patch('tempfile.TemporaryDirectory')
    @patch('kiwi_keg.tools.compose_kiwi_description.KegImageDefinition')
    @patch('kiwi_keg.tools.compose_kiwi_description.KegGenerator')
    @patch('kiwi_keg.tools.compose_kiwi_description.subprocess.run')
    @patch('os.mkdir')
    @patch('os.path.exists')
    def test_compose_kiwi_description_new_image(
        self, mock_path_exists, mock_mkdir, mock_subprocess_run,
        mock_KegGenerator, mock_KegImageDefinition, mock_TemporaryDirectory,
        mock_ET, mock_SourceInfoGenerator, mock_glob,
        mock_get_revision_args, mock_remove, mock_update_revisions,
        mock_write_changelog, mock_datetime
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
            '--version-bump=false',
            '--changelog-format=json',
            '--new-image-change=new image'
        ]
        mock_tree = Mock()
        mock_root = Mock()
        mock_prefs = Mock()
        mock_ver = Mock()
        mock_ET.parse.return_value = mock_tree
        mock_tree.getroot.return_value = mock_root
        mock_root.findall.return_value = [mock_prefs]
        mock_prefs.find.return_value = mock_ver
        mock_ver.text = '1.1.1'
        mock_path_exists.side_effect = [False, False, False, True]
        image_definition = Mock()
        mock_KegImageDefinition.return_value = image_definition
        image_generator = Mock()
        mock_KegGenerator.return_value = image_generator
        temp_dir = Mock()
        mock_TemporaryDirectory.return_value = temp_dir
        source_info_generator = Mock()
        mock_SourceInfoGenerator.return_value = source_info_generator
        mock_glob.return_value = ['obs_out/log_sources']
        mock_get_revision_args.return_value = ['-r', 'fake_repo:fake_rev..']
        mock_result = Mock()
        mock_result.returncode = 2
        mock_subprocess_run.return_value = mock_result
        mock_timestamp = Mock()
        mock_timestamp.isoformat.return_value = 'TIMESTAMP'
        mock_datetime.now.return_value = mock_timestamp

        with patch('builtins.open', create=True):
            main()

        mock_mkdir.assert_called_once_with('obs_out')
        assert mock_subprocess_run.call_args_list == [
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
                ],
                stdout=subprocess.PIPE, encoding='UTF-8'
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
        mock_ET.parse.assert_called_once_with(
            'obs_out/config.kiwi'
        )
        source_info_generator.write_source_info.assert_called_once()
        mock_remove.assert_called_once_with('obs_out/log_sources')
        expected_changelog = {'1.1.1': [{'change': 'new image', 'date': 'TIMESTAMP'}]}
        mock_write_changelog.assert_called_once_with(
            'obs_out/changes.json',
            'json',
            expected_changelog
        )

    @patch('kiwi_keg.tools.compose_kiwi_description.update_changelog')
    @patch('kiwi_keg.tools.compose_kiwi_description.update_revisions')
    @patch('os.remove')
    @patch('kiwi_keg.tools.compose_kiwi_description.get_revision_args')
    @patch('glob.glob')
    @patch('kiwi_keg.tools.compose_kiwi_description.SourceInfoGenerator')
    @patch('kiwi_keg.tools.compose_kiwi_description.ET')
    @patch('kiwi_keg.tools.compose_kiwi_description.tempfile.TemporaryDirectory')
    @patch('kiwi_keg.tools.compose_kiwi_description.KegImageDefinition')
    @patch('kiwi_keg.tools.compose_kiwi_description.KegGenerator')
    @patch('kiwi_keg.tools.compose_kiwi_description.subprocess.run')
    @patch('kiwi_keg.tools.compose_kiwi_description.os.mkdir')
    @patch('os.path.exists')
    def test_compose_kiwi_description_osc_log(
        self, mock_path_exists, mock_mkdir, mock_subprocess_run,
        mock_KegGenerator, mock_KegImageDefinition, mock_TemporaryDirectory,
        mock_ET, mock_SourceInfoGenerator, mock_glob,
        mock_get_revision_args, mock_remove, mock_update_revisions,
        mock_update_changelog
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
            '--changelog-format=osc'
        ]
        mock_tree = Mock()
        mock_root = Mock()
        mock_prefs = Mock()
        mock_ver = Mock()
        mock_ET.parse.return_value = mock_tree
        mock_tree.getroot.return_value = mock_root
        mock_root.findall.return_value = [mock_prefs]
        mock_prefs.find.return_value = mock_ver
        mock_ver.text = '1.1.1'
        mock_path_exists.side_effect = [False, False, True, True, True, False]
        image_definition = Mock()
        mock_KegImageDefinition.return_value = image_definition
        image_generator = Mock()
        mock_KegGenerator.return_value = image_generator
        temp_dir = Mock()
        mock_TemporaryDirectory.return_value = temp_dir
        source_info_generator = Mock()
        mock_SourceInfoGenerator.return_value = source_info_generator
        mock_glob.return_value = ['obs_out/log_sources_flavor1', 'obs_out/log_sources_flavor2']
        mock_get_revision_args.return_value = ['-r', 'fake_repo:fake_rev..']
        mock_result = Mock()
        mock_result.returncode = 0
        mock_subprocess_run.return_value = mock_result

        with patch('builtins.open', create=True):
            main()

        mock_mkdir.assert_called_once_with('obs_out')
        assert mock_subprocess_run.call_args_list == [
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
                ], stdout=subprocess.PIPE, encoding='UTF-8'
            ),
            call(
                [
                    'generate_recipes_changelog',
                    '-o', 'obs_out/flavor1.changes.txt',
                    '-f', 'osc',
                    '-t', '1.1.2',
                    '-r', 'fake_repo:fake_rev..',
                    'obs_out/log_sources_flavor1'
                ]
            ),
            call(
                [
                    'generate_recipes_changelog',
                    '-o', 'obs_out/flavor2.changes.txt',
                    '-f', 'osc',
                    '-t', '1.1.2',
                    '-r', 'fake_repo:fake_rev..',
                    'obs_out/log_sources_flavor2'
                ]
            )
        ]
        mock_KegImageDefinition.assert_called_once_with(
            image_name='leap/jeos/15.2',
            recipes_roots=[temp_dir.name],
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
        mock_ET.parse.assert_called_once_with(
            'config.kiwi'
        )
        assert mock_remove.call_args_list == [
            call('obs_out/log_sources_flavor1'),
            call('obs_out/log_sources_flavor2')
        ]
        source_info_generator.write_source_info.assert_called_once()
        mock_update_revisions.assert_called_once()
        assert mock_update_changelog.call_args_list == [
            call('obs_out/flavor1.changes.txt', 'osc'),
            call('obs_out/flavor2.changes.txt', 'osc')
        ]

    def test_compose_kiwi_description_unknown_log_format(self):
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
            '--changelog-format=foo'
        ]
        with raises(SystemExit) as sysex:
            main()
        assert sysex.value.code == 'Unknown changelog format foo'

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

    @patch('kiwi_keg.tools.compose_kiwi_description.ET')
    def test_image_version_error(self, mock_ET):
        mock_tree = Mock()
        mock_root = Mock()
        mock_prefs = Mock()
        mock_ET.parse.return_value = mock_tree
        mock_tree.getroot.return_value = mock_root
        mock_root.findall.return_value = [mock_prefs]
        mock_prefs.find.return_value = None
        with raises(SystemExit) as sysex:
            get_image_version('fake')
        assert sysex.value.code == 'Cannot determine image version.'

    @patch('kiwi_keg.tools.compose_kiwi_description.get_head_commit_hash')
    def test_parse_revisions(self, mock_get_head_commit_hash):
        mock_dir = Mock()
        mock_dir.name = 'dir1'
        mock_get_head_commit_hash.return_value = '1234'
        repo = RepoInfo(mock_dir)
        repos = {'repo1': repo}
        with tempfile.TemporaryDirectory() as tmpdirname:
            os.chdir(tmpdirname)

            with self._caplog.at_level(logging.INFO):
                parse_revisions(repos)
                assert 'No _keg_revision file.' in self._caplog.text

            with open(os.path.join(tmpdirname, '_keg_revisions'), 'w') as outf:
                outf.write('repo1 hash1\nrepo2 hash2\n')

            with self._caplog.at_level(logging.WARNING):
                parse_revisions(repos)
                assert 'Cannot map URL "repo2" to repository.' in self._caplog.text

            with open(os.path.join(tmpdirname, '_keg_revisions'), 'w') as outf:
                outf.write('INVALID')

            with raises(SystemExit) as sysex:
                parse_revisions(repos)
            assert sysex.value.code == 'Malformed revision spec "INVALID".'

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

    def test_update_changelog_yaml(self):
        with tempfile.TemporaryDirectory() as tmpdirname:
            os.chdir(tmpdirname)
            os.mkdir('out')
            open('changes.yaml', 'w').write('- change: old entry\n')
            open('out/changes.yaml', 'w').write('- change: new entry\n')
            update_changelog('out/changes.yaml', 'yaml')
            assert open('out/changes.yaml', 'r').read() == '- change: new entry\n- change: old entry\n'

    def test_update_changelog_yaml_to_json(self):
        with tempfile.TemporaryDirectory() as tmpdirname:
            os.chdir(tmpdirname)
            os.mkdir('out')
            open('changes.yaml', 'w').write('"1.0":\n  - change: old entry\n')
            open('out/changes.json', 'w').write('{ "1.1": [{"change": "new entry"}] }\n')
            update_changelog('out/changes.json', 'json')
            assert json.loads(open('out/changes.json', 'r').read()) == {
                "1.1": [{"change": "new entry"}],
                "1.0": [{"change": "old entry"}]
            }

    def test_update_changelog_json_to_yaml(self):
        with tempfile.TemporaryDirectory() as tmpdirname:
            os.chdir(tmpdirname)
            os.mkdir('out')
            open('changes.json', 'w').write('{ "1.0": [{"change": "old entry"}] }\n')
            open('out/changes.yaml', 'w').write('"1.1":\n  - change: new entry\n    details: |-\n      details\n      more details\n')
            update_changelog('out/changes.yaml', 'yaml')
            assert yaml.safe_load(open('out/changes.yaml', 'r').read()) == {
                "1.1": [{"change": "new entry", "details": "details\nmore details"}],
                "1.0": [{"change": "old entry"}]
            }

    def test_update_changelog_json_to_osc(self):
        with tempfile.TemporaryDirectory() as tmpdirname:
            os.chdir(tmpdirname)
            os.mkdir('out')
            open('changes.json', 'w').write('{ "1.0": [{"change": "old entry", "date": "2023-05-11T09:41:50"}]}\n')
            open('out/changes.txt', 'w').write(fake_changes_txt_new)
            update_changelog('out/changes.txt', 'osc')
            assert open('out/changes.txt', 'r').read() == fake_changes_txt_merged

    def test_update_changelog_osc_to_yaml(self):
        with tempfile.TemporaryDirectory() as tmpdirname:
            os.chdir(tmpdirname)
            os.mkdir('out')
            open('changes.txt', 'w').write('not convertable')
            open('out/changes.yaml', 'w').write('- change: new entry\n')
            update_changelog('out/changes.yaml', 'yaml')
            assert open('out/changes.yaml', 'r').read() == '- change: new entry\n'

    def test_update_changelog_unsupported_format(self):
        with tempfile.TemporaryDirectory() as tmpdirname:
            os.chdir(tmpdirname)
            os.mkdir('out')
            open('changes.foo', 'w').write('foo format')
            open('out/changes.yaml', 'w').write('- change: new entry\n')
            update_changelog('out/changes.yaml', 'yaml')
            assert open('out/changes.yaml', 'r').read() == '- change: new entry\n'
            assert 'Unsupported log format' in self._caplog.text

    def test_update_changelog_no_old_log(self):
        with tempfile.TemporaryDirectory() as tmpdirname:
            os.chdir(tmpdirname)
            update_changelog('out/changes.yaml', 'yaml')
            assert 'No old log' in self._caplog.text

    def test_update_changelog_multiple_old_logs(self):
        with tempfile.TemporaryDirectory() as tmpdirname:
            os.chdir(tmpdirname)
            open('changes.txt', 'w').write('- some change')
            open('changes.json', 'w').write('{"1.0.0": [{"change": "old entry"}]}')
            os.mkdir('out')
            open('out/changes.json', 'w').write('{"1.0.1": [{"change": "new entry"}]}')
            update_changelog('out/changes.json', 'json')
            assert 'More than one format for old log' in self._caplog.text

    @patch('kiwi_keg.tools.compose_kiwi_description.parse_revisions')
    @patch('kiwi_keg.tools.compose_kiwi_description.RepoInfo')
    @patch('tempfile.TemporaryDirectory')
    @patch('subprocess.run')
    @patch('os.path.exists')
    def test_no_new_commits(self, mock_path_exists, mock_run, mock_tempdir,
                            mock_repo_info, mock_parse_revisions):
        mock_path_exists.return_value = True
        mock_repo_info.has_commits.return_value = False
        with self._caplog.at_level(logging.INFO):
            with raises(SystemExit):
                main()
            assert 'No repository has new commits.' in self._caplog.text
            assert 'Aborting.' in self._caplog.text

    @patch('subprocess.run')
    def test_generate_changelog_error(self, mock_subprocess_run):
        mock_result = Mock()
        mock_result.returncode = 1
        mock_subprocess_run.return_value = mock_result
        with raises(SystemExit) as sysex:
            generate_changelog('log_sources', 'changes.yaml', 'yaml', '1.1.1', ['-r', 'fakerev'])
        assert sysex.value.code == 'Error generating change log.'
