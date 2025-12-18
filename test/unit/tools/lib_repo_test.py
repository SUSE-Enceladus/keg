import logging
import os
import subprocess

from pytest import raises
from unittest.mock import patch, mock_open, Mock, call

from kiwi_keg.tools import lib_repo


@patch('tempfile.TemporaryDirectory')
@patch('subprocess.run')
def test_lib_repo_gitrepo(mock_run, mock_tempdir):
    mock_checkout_result = Mock()
    mock_get_head_commit_hash_result = Mock()
    mock_get_head_commit_hash_result.stdout = 'head_commit_hash\n'
    mock_run.side_effect = [mock_checkout_result, mock_get_head_commit_hash_result]
    gitrepo = lib_repo.GitRepo('repo_src')
    assert gitrepo.head_commit == 'head_commit_hash'
    assert gitrepo.pathname == mock_tempdir().name


@patch('tempfile.TemporaryDirectory')
@patch('subprocess.run')
def test_lib_repo_gitrepo_with_branch(mock_run, mock_tempdir):
    mock_checkout_result = Mock()
    mock_get_head_commit_hash_result = Mock()
    mock_get_head_commit_hash_result.stdout = 'head_commit_hash\n'
    mock_run.side_effect = [mock_checkout_result, mock_get_head_commit_hash_result]
    gitrepo = lib_repo.GitRepo('repo_src', 'branch')
    assert gitrepo.head_commit == 'head_commit_hash'
    assert gitrepo.pathname == mock_tempdir().name
    assert gitrepo.branchname == 'branch'


@patch('kiwi_keg.tools.lib_repo.GitRepo._get_head_commit_hash', return_value='head_commit_hash')
@patch('kiwi_keg.tools.lib_repo.GitRepo._checkout', return_value='repo_path')
def test_lib_repo_gitrepo_commits(mock_checkout, mock_get_head_commit):
    gitrepo = lib_repo.GitRepo('repo_src', 'branch')
    gitrepo.set_start_commit('start_commit_hash')
    assert gitrepo.head_commit == 'head_commit_hash'
    assert gitrepo.start_commit == 'start_commit_hash'
    assert gitrepo.has_commits() is True


@patch('os.path.exists', return_value=True)
def test_lib_repo_parse_revisions(mock_path_exists):
    mock_file = mock_open(read_data='repo_url rev\n')
    mock_repos = {'repo_url': Mock()}
    with patch('builtins.open', mock_file):
        lib_repo.parse_revisions(mock_repos)
    mock_repos['repo_url'].set_start_commit.assert_called_with('rev')


@patch('os.path.exists', return_value=False)
def test_lib_repo_parse_revisions_file_missing(mock_path_exists, caplog):
    with caplog.at_level(logging.INFO):
        lib_repo.parse_revisions(None)
    assert 'No _keg_revisions file.' in caplog.text


@patch('os.path.exists', return_value=True)
def test_lib_repo_parse_revisions_malformed(mock_path_exists):
    mock_file = mock_open(read_data='invalid\n')
    mock_repos = {'repo_url': Mock()}
    with patch('builtins.open', mock_file), raises(SystemExit) as e_info:
        lib_repo.parse_revisions(mock_repos)
    assert str(e_info.value) == 'Malformed revision spec "invalid".'


@patch('os.path.exists', return_value=True)
def test_lib_repo_parse_revisions_repo_missing(mock_path_exists, caplog):
    mock_file = mock_open(read_data='repo_url rev\n')
    with patch('builtins.open', mock_file):
        lib_repo.parse_revisions({})
    assert 'Cannot map URL "repo_url" to repository.' in caplog.text


def test_lib_repo_revisions_args():
    mock_repos = {'repo_url': Mock()}
    mock_repos['repo_url'].start_commit = 'start_commit'
    mock_repos['repo_url'].pathname = 'repo_path'
    assert lib_repo.get_revision_args(mock_repos) == ['-r', 'repo_path:start_commit..']


def test_lib_repo_update_revisions():
    mock_file = mock_open()
    mock_repos = {'repo_url': Mock()}
    mock_repos['repo_url'].head_commit = 'head_commit'
    with patch('builtins.open', mock_file):
        lib_repo.update_revisions(mock_repos, 'outdir')
    mock_file.assert_has_calls([
        call(os.path.join('outdir', '_keg_revisions'), 'w'),
        call().__enter__(),
        call().write('repo_url head_commit')
    ])


@patch('subprocess.run')
def test_lib_repo_checkout_start_commits(mock_run):
    mock_repos = {'repo_url': Mock()}
    mock_repos['repo_url'].start_commit = 'start_commit'
    mock_repos['repo_url'].pathname = 'repo_pathname'
    lib_repo.checkout_start_commits(mock_repos)
    mock_run.assert_called_once_with(['git', '-C', 'repo_pathname', 'checkout', 'start_commit'], stderr=subprocess.DEVNULL)


@patch('subprocess.run')
def test_lib_repo_checkout_head_commits(mock_run):
    mock_repos = {'repo_url': Mock()}
    mock_repos['repo_url'].pathname = 'repo_pathname'
    lib_repo.checkout_head_commits(mock_repos)
    mock_run.assert_called_once_with(
        ['git', '-C', 'repo_pathname', 'checkout', '-'],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
