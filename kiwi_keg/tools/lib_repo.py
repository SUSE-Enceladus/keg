# Copyright (c) 2025 SUSE Software Solutions Germany GmbH. All rights reserved.
#
# This file is part of keg.
#
# keg is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# keg is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with keg. If not, see <http://www.gnu.org/licenses/>
#
import logging
import os
import subprocess
import tempfile
import sys


class GitRepo:
    def __init__(self, repo_src, branch=None):
        self._repo_src = repo_src
        self._branch = branch
        self._path = self._checkout()
        self._start_commit = None
        self._head_commit = self._get_head_commit_hash()

    @property
    def pathname(self):
        return self._path.name

    @property
    def branchname(self):
        return self._branch

    @property
    def head_commit(self):
        return self._head_commit

    @property
    def start_commit(self):
        return self._start_commit

    def set_start_commit(self, commit):
        self._start_commit = commit

    def has_commits(self):
        return self._start_commit != self._head_commit

    def _get_head_commit_hash(self):
        result = subprocess.run(
            ['git', '-C', self._path.name, 'show', '--no-patch', '--format=%H', 'HEAD'],
            stdout=subprocess.PIPE,
            encoding='UTF-8'
        )
        return result.stdout.strip('\n')

    def _checkout(self):
        temp_git_dir = tempfile.TemporaryDirectory(prefix='keg_recipes.', dir='.')
        if self._branch:
            subprocess.run(
                ['git', 'clone', '-b', self._branch, self._repo_src, temp_git_dir.name],
                stderr=subprocess.DEVNULL
            )
        else:
            subprocess.run(['git', 'clone', self._repo_src, temp_git_dir.name], stderr=subprocess.DEVNULL)
        return temp_git_dir


def parse_revisions(repos):
    if os.path.exists('_keg_revisions'):
        with open('_keg_revisions') as inf:
            for line in inf.readlines():
                rev_spec = line.strip('\n').split(' ')
                if len(rev_spec) != 2:
                    sys.exit('Malformed revision spec "{}".'.format(line.strip('\n')))
                repo = repos.get(rev_spec[0])
                if not repo:
                    logging.warning('Cannot map URL "{}" to repository.'.format(rev_spec[0]))
                else:
                    repo.set_start_commit(rev_spec[1])
    else:
        logging.info(
            'No _keg_revisions file.'
        )


def get_revision_args(repos):
    rev_args = []
    for repo in repos.values():
        if repo.start_commit:
            rev_args += ['-r', '{}:{}..'.format(repo.pathname, repo.start_commit)]
    return rev_args


def update_revisions(repos, outdir):
    with open(os.path.join(outdir, '_keg_revisions'), 'w') as outf:
        for rname, rinfo in repos.items():
            print('{} {}'.format(rname, rinfo.head_commit), file=outf)


def checkout_start_commits(repos):
    for repo in repos.values():
        subprocess.run(['git', '-C', repo.pathname, 'checkout', repo.start_commit], stderr=subprocess.DEVNULL)


def checkout_head_commits(repos):
    for repo in repos.values():
        subprocess.run(['git', '-C', repo.pathname, 'checkout', '-'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
