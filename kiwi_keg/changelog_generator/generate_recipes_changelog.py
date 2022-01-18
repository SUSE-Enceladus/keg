#!/usr/bin/python3
#
# Copyright (c) 2022 SUSE Software Solutions Germany GmbH. All rights reserved.
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

"""
Usage: generate_recipes_changelog [-o OUTPUT_FILE] [-r REV] [-f FORMAT]
                                  [-m MSG_FORMAT] [-t ROOT_TAG] [-C PATH] LOGFILE
       generate_recipes_changelog -h | --help

Arguments:
    LOGFILE    Path to file contaning Keg source log

Options:
    -o OUTPUT_FILE
        Write output to OUTPUT_FILE

    -r REV
        Set git revision range start to REV

    -f FORMAT
       Output format, 'text' or 'yaml' [default: yaml]

    -m MSG_FORMAT
       Format spec for commit messages (see 'format:<string>' in 'man git-log')
       [default: - %s] (only used with text format)

    -t ROOT_TAG
       Use ROOT_TAG for yaml output (e.g. image version)

    -C PATH
        Use PATH to git repository instead for current working dir.

"""

import docopt
import subprocess
import sys
import yaml

gitcmd = ['git']


class MultiStr(str):
    pass


def get_commits_from_range(start, end, filespec, rev=None):
    cmdargs = gitcmd + ['log', '--no-merges', '--format=%ct %H', '--no-patch']
    if rev:
        cmdargs.append(rev)
    cmdargs += ['-L{start},{end}:{filespec}'.format(start=start, end=end, filespec=filespec)]
    return get_commits(cmdargs)


def get_commits_from_path(pathspec, rev=None):
    cmdargs = gitcmd + ['log', '--no-merges', '--format=%ct %H']
    if rev:
        cmdargs.append(rev)
    cmdargs.append('--')
    cmdargs.append(pathspec)
    return get_commits(cmdargs)


def get_commits(gitargs):
    sp = subprocess.run(args=gitargs, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if sp.returncode != 0:
        raise Exception('git exited with error "{}"'.format(sp.stderr))
    commit_lines = sp.stdout.decode('utf-8').splitlines()
    return set(tuple(x.split()) for x in commit_lines)


def get_commit_message(chash, msgformat):
    gitargs = gitcmd + ['show', '--no-patch', '--format={}'.format(msgformat), chash]
    sp = subprocess.run(args=gitargs, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if sp.returncode != 0:
        raise Exception('git exited with error "{}"'.format(sp.stderr))
    return sp.stdout.decode('utf-8').rstrip('\n')


def repr_mstr(dumper, data):
    tag = u'tag:yaml.org,2002:str'
    return dumper.represent_scalar(tag, data, style='|')


def main():
    args = docopt.docopt(__doc__, version='0.1')
    global gitcmd

    if args['-f'] not in ['text', 'yaml']:
        sys.exit('Unsupported output format "{}".'.format(args['-f']))

    if args['-C']:
        gitcmd += ['-C', args['-C']]

    with open(args['LOGFILE'], 'r') as inf:
        sources = inf.read().splitlines()

    commits = set()
    for source in sources:
        if source.startswith('range:'):
            rspec = source.split(':')
            commits |= get_commits_from_range(rspec[1], rspec[2], rspec[3], args['-r'])
        else:
            commits |= get_commits_from_path(source, args['-r'])

    if args['-o']:
        outp = open(args['-o'], 'w')
    else:
        outp = sys.stdout

    if args['-f'] == 'text':
        for commit in sorted(commits, reverse=True):
            print(get_commit_message(commit[1], args['-m']), file=outp)
    else:
        msgs = []
        for commit in sorted(commits, reverse=True):
            sub = get_commit_message(commit[1], '%s').lstrip('- ')
            body = MultiStr(get_commit_message(commit[1], '%b').rstrip('\n'))
            if body:
                msgs.append({'change': sub, 'details': body})
            else:
                msgs.append({'change': sub})
        yaml.add_representer(MultiStr, repr_mstr, Dumper=yaml.SafeDumper)
        if args['-t']:
            log = {args['-t']: msgs}
        else:
            log = msgs
        yaml.safe_dump(log, outp)

    if args['-o']:
        outp.close()


if __name__ == '__main__':
    main()  # pragma: no cover
