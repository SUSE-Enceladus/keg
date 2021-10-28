import sys
from mock import (
    Mock, patch, call
)
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
            'develop',
            '--outdir',
            'obs_out'
        ]

    @patch('kiwi_keg.obs_service.compose_kiwi_description.Temporary.new_dir')
    @patch('kiwi_keg.obs_service.compose_kiwi_description.KegImageDefinition')
    @patch('kiwi_keg.obs_service.compose_kiwi_description.KegGenerator')
    @patch('kiwi_keg.obs_service.compose_kiwi_description.Command.run')
    @patch('kiwi_keg.obs_service.compose_kiwi_description.Path.create')
    @patch('os.path.exists')
    def test_compose_kiwi_description(
        self, mock_path_exists, mock_Path_create, mock_Command_run,
        mock_KegGenerator, mock_KegImageDefinition, mock_Temporary_new_dir
    ):
        mock_path_exists.return_value = False
        image_definition = Mock()
        mock_KegImageDefinition.return_value = image_definition
        image_generator = Mock()
        mock_KegGenerator.return_value = image_generator
        temp_dir = Mock()
        mock_Temporary_new_dir.return_value = temp_dir
        main()
        mock_Path_create.assert_called_once_with('obs_out')
        assert mock_Command_run.call_args_list == [
            call(
                [
                    'git', 'clone',
                    'https://github.com/SUSE-Enceladus/keg-recipes.git',
                    temp_dir.name
                ]
            ),
            call(
                [
                    'git', '-C', temp_dir.name, 'checkout', 'develop'
                ]
            )
        ]
        mock_KegImageDefinition.assert_called_once_with(
            image_name='leap/jeos/15.2',
            recipes_root=temp_dir.name,
            data_roots=None,
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
