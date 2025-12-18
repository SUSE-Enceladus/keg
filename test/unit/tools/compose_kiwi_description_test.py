import datetime
import logging
import sys

from pytest import raises
from unittest.mock import patch, Mock, call

from kiwi_keg.tools import compose_kiwi_description


def test_compose_kiwi_description_get_changelog_format_error():
    with raises(SystemExit) as e_info:
        compose_kiwi_description.get_changelog_format('nope')
    assert 'Unknown changelog format' in str(e_info.value)


def test_compose_kiwi_description_get_changelog_format():
    assert compose_kiwi_description.get_changelog_format('osc') == 'txt'
    assert compose_kiwi_description.get_changelog_format('json') == 'json'
    assert compose_kiwi_description.get_changelog_format('yaml') == 'yaml'


def test_compose_kiwi_description_get_repos_param_error():
    args = {
        '--git-recipes': ['recipes'],
        '--git-branch': ['branch', 'excess_branch']
    }
    with raises(SystemExit) as e_info:
        compose_kiwi_description.get_repos(args)
    assert str(e_info.value) == 'Number of --git-branch arguments must not exceed number of git repos.'


@patch('kiwi_keg.tools.lib_repo.GitRepo')
def test_compose_kiwi_description_get_repos(mock_GitRepo):
    args = {
        '--git-recipes': ['recipes1', 'recipes2'],
        '--git-branch': ['branch1', 'branch2']
    }
    mock_repo1 = Mock()
    mock_repo2 = Mock()
    mock_repo1.has_commits.return_value = True
    mock_repo2.has_commits.return_value = False
    mock_GitRepo.side_effect = [mock_repo1, mock_repo2]
    repos = compose_kiwi_description.get_repos(args)
    assert len(repos) == 2
    assert repos.get('recipes1') == mock_repo1
    assert repos.get('recipes2') == mock_repo2


@patch('kiwi_keg.tools.lib_repo.GitRepo')
def test_compose_kiwi_description_get_repos_error_no_new_commits(mock_GitRepo, caplog):
    args = {
        '--git-recipes': ['recipes1', 'recipes2'],
        '--git-branch': ['branch1', 'branch2'],
        '--force': False
    }
    mock_repo1 = Mock()
    mock_repo2 = Mock()
    mock_repo1.has_commits.return_value = False
    mock_repo2.has_commits.return_value = False
    with raises(SystemExit), caplog.at_level(logging.INFO):
        compose_kiwi_description.get_repos(args)
    assert 'No repository has new commits' in caplog.text
    assert 'Aborting' in caplog.text


@patch('os.path.exists', return_value=True)
def test_compose_kiwi_description_get_new_image_version_supplied(mock_path_exist):
    args = {'--image-version': '1.2.3'}
    assert compose_kiwi_description.get_new_image_version(args) == ('1.2.3', True)


@patch('kiwi_keg.tools.lib_image.get_bumped_image_version', return_value='1.2.4')
@patch('os.path.exists', return_value=True)
def test_compose_kiwi_description_get_new_image_version_bumped(mock_path_exists, mock_get_bumped_image_version):
    args = {'--image-version': None, '--version-bump': 'true'}
    assert compose_kiwi_description.get_new_image_version(args) == ('1.2.4', True)


@patch('kiwi_keg.tools.lib_repo.checkout_head_commits')
@patch('kiwi_keg.tools.lib_repo.checkout_start_commits')
@patch('kiwi_keg.tools.lib_source.find_deleted_src_lines')
@patch('kiwi_keg.tools.lib_image.generate_image_description')
@patch('tempfile.TemporaryDirectory')
def test_compose_kiwi_description_generate_deleted_source_info(
        mock_tempdir,
        mock_generate_image_description,
        mock_find_deleted_src_lines,
        mock_checkout_start_commits,
        mock_checkout_head_commits
):
    args = {
        '--image-source': 'image_source',
        '--outdir': 'outdir',
        '--arch': ['arch']
    }
    compose_kiwi_description.generate_deleted_source_info(args, 'repos', 'image_version')
    mock_checkout_start_commits.assert_called_once_with('repos')
    mock_generate_image_description.assert_called_once_with(
        image_source='image_source',
        repos='repos',
        gen_src_log=True,
        image_version='image_version',
        gen_mbuild=False,
        outdir=mock_tempdir().__enter__(),
        archs=['arch']
    )
    mock_find_deleted_src_lines(mock_tempdir().__enter__(), 'outdir')
    mock_checkout_head_commits.assert_called_once_with('repos')


@patch('os.remove')
@patch('kiwi_keg.tools.lib_changelog.generate_and_update')
@patch('kiwi_keg.tools.lib_source.get_log_sources')
def test_compose_kiwi_description_generate_changelogs_new_image(
        mock_get_log_sources,
        mock_generate_and_update,
        mock_os_remove
):
    args = {
        '--outdir': 'outdir',
        '--new-image-change': 'new_image'
    }
    mock_datetime = datetime.datetime(2025, 12, 12, 12, 12)
    mock_get_log_sources.return_value = [('log_sources_one', 'one'), ('log_sources_two', 'two')]
    with patch('kiwi_keg.tools.compose_kiwi_description.datetime') as p:
        p.now.return_value = mock_datetime
        compose_kiwi_description.generate_changelogs(args, 'image_version', 'rev_args', False, 'log_ext')
    mock_get_log_sources.assert_called_once_with('outdir')
    mock_generate_and_update.assert_has_calls([
        call(
            outdir='outdir',
            prefix='one',
            log_ext='log_ext',
            changes={'image_version': [{'change': 'new_image', 'date': '2025-12-12T12:12'}]},
            source_log='log_sources_one',
            image_version='image_version',
            rev_args='rev_args'
        ),
        call(
            outdir='outdir',
            prefix='two',
            log_ext='log_ext',
            changes={'image_version': [{'change': 'new_image', 'date': '2025-12-12T12:12'}]},
            source_log='log_sources_two',
            image_version='image_version',
            rev_args='rev_args'
        )], any_order=True)
    mock_os_remove.assert_has_calls([call('log_sources_one'), call('log_sources_two')])


@patch('os.remove')
@patch('kiwi_keg.tools.lib_changelog.generate_and_update')
@patch('kiwi_keg.tools.lib_source.get_log_sources')
@patch('kiwi_keg.tools.lib_image.get_image_version', return_value='image_version')
def test_compose_kiwi_description_generate_changelogs_udpated_image(
        mock_get_image_version,
        mock_get_log_sources,
        mock_generate_and_update,
        mock_os_remove
):
    args = {'--outdir': 'outdir'}
    mock_get_log_sources.return_value = [('log_sources', '')]
    compose_kiwi_description.generate_changelogs(args, None, 'rev_args', True, 'log_ext')
    mock_get_log_sources.assert_called_once_with('outdir')
    mock_generate_and_update.assert_called_once_with(
        outdir='outdir',
        prefix='',
        log_ext='log_ext',
        changes=None,
        source_log='log_sources',
        image_version='image_version',
        rev_args='rev_args'
    )
    mock_os_remove.assert_called_once_with('log_sources')


@patch('kiwi_keg.tools.lib_repo.update_revisions')
@patch('kiwi_keg.tools.lib_repo.get_revision_args', return_value='rev_args')
@patch('kiwi_keg.tools.lib_fileutil.purge_files', return_value=['stale_file'])
@patch('kiwi_keg.tools.lib_image.generate_image_description')
@patch('kiwi_keg.tools.compose_kiwi_description.generate_changelogs', return_value=False)
@patch('kiwi_keg.tools.compose_kiwi_description.generate_deleted_source_info')
@patch('kiwi_keg.tools.compose_kiwi_description.get_repos', return_value='repos')
@patch('kiwi_keg.tools.compose_kiwi_description.get_changelog_format', return_value='json')
@patch('kiwi_keg.tools.compose_kiwi_description.get_new_image_version', return_value=('image_version', True))
@patch('os.remove')
@patch('os.mkdir')
@patch('os.path.exists', return_value=False)
def test_compose_kiwi_description_main(
        mock_path_exists,
        mock_mkdir,
        mock_remove,
        mock_get_new_image_version,
        mock_get_changelog_format,
        mock_get_repos,
        mock_generate_deleted_source_info,
        mock_generate_changelogs,
        mock_generate_image_description,
        mock_purge_files,
        mock_get_revision_args,
        mock_update_revisions
):
    sys.argv = [
        'compose_kiwi_description',
        '--git-recipes=recipes',
        '--git-branch=branch',
        '--image-source=image_source',
        '--arch=arch',
        '--outdir=outdir',
        '--image-version=image_version',
        '--version-bump=true',
        '--update-changelogs=true',
        '--update-revisions=true',
        '--force=true',
        '--generate-multibuild=true',
        '--new-image-change=new_image',
        '--changelog-format=json',
        '--purge-stale-files=true',
        '--purge-ignore=purge_ignore'
    ]
    compose_kiwi_description.main()
    mock_get_changelog_format.assert_called_with('json')
    mock_get_repos.assert_called()
    mock_get_new_image_version.assert_called()
    mock_mkdir.assert_called_with('outdir')
    mock_generate_image_description.assert_called_once_with(
        image_source='image_source',
        repos='repos',
        gen_src_log=True,
        image_version='image_version',
        gen_mbuild=True,
        outdir='outdir',
        archs=['arch']
    )
    mock_purge_files.assert_called_with('.', 'outdir', True, 'purge_ignore', True, False)
    mock_generate_deleted_source_info.assert_called()
    mock_generate_changelogs.assert_called()
    mock_update_revisions.assert_called_with('repos', 'outdir')
    mock_remove.assert_called_with('stale_file')


def test_compose_kiwi_description_main_version(capsys):
    sys.argv = ['compose_kiwi_description', '--version']
    with raises(SystemExit):
        compose_kiwi_description.main()
        assert capsys.readouterr().out == compose_kiwi_description.__version__ + '\n'
