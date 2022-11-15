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
Usage: generate_recipes_changelog [-o OUTPUT_FILE] [-r REV]... [-f FORMAT]
                                  [-m MSG_FORMAT] [-t ROOT_TAG] LOGFILE
       generate_recipes_changelog -h | --help

Arguments:
    LOGFILE    Path to file contaning Keg source log

Options:
    -o OUTPUT_FILE
        Write output to OUTPUT_FILE (stdout if omitted)

    -r PATH:REV
        Set git revision range to REV for repo at PATH

    -f FORMAT
        Output format, 'text' or 'yaml' [default: yaml]

    -m MSG_FORMAT
        Format spec for commit messages (see 'format:<string>' in 'man git-log')
        [default: - %s] (only used with text format)

    -t ROOT_TAG
        Use ROOT_TAG for yaml output (e.g. image version)
"""

import docopt
import subprocess
import sys
import yaml
from datetime import datetime


class MultiStr(str):
    pass


def get_commits_from_range(start, end, filespec, gitroot, rev=None):
    if rev == '':
        return set()
    cmdargs = ['git', '-C', gitroot, 'log', '--no-merges', '--format=%ct %H', '--no-patch']
    if rev:
        cmdargs.append(rev)
    cmdargs += ['-L{start},{end}:{filespec}'.format(start=start, end=end, filespec=filespec)]
    return get_commits(cmdargs, gitroot)


def get_commits_from_path(pathspec, gitroot, rev=None):
    if rev == '':
        return set()
    cmdargs = ['git', '-C', gitroot, 'log', '--no-merges', '--format=%ct %H']
    if rev:
        cmdargs.append(rev)
    cmdargs.append('--')
    cmdargs.append(pathspec)
    return get_commits(cmdargs, gitroot)


def get_commits(gitargs, gitroot):
    sp = subprocess.run(args=gitargs, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if sp.returncode != 0:
        raise Exception('git exited with error "{}"'.format(sp.stderr))
    commit_lines = sp.stdout.decode('utf-8').splitlines()
    return set(tuple(x.split() + [gitroot]) for x in commit_lines)


def get_commit_message(chash, gitroot, msgformat):
    gitargs = ['git', '-C', gitroot, 'show', '--no-patch', '--format={}'.format(msgformat), chash]
    sp = subprocess.run(args=gitargs, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if sp.returncode != 0:
        raise Exception('git exited with error "{}"'.format(sp.stderr))
    return sp.stdout.decode('utf-8').rstrip('\n')


def git_log_empty(gitroot, rev):
    cmdargs = ['git', '-C', gitroot, 'log', '--format=%H', '--no-patch', rev]
    commits = get_commits(cmdargs, gitroot)
    return commits == set()


def repr_mstr(dumper, data):
    tag = u'tag:yaml.org,2002:str'
    return dumper.represent_scalar(tag, data, style='|')


def split_path(path, roots):
    for r in roots:
        if path.startswith(r + '/'):
            return path[:len(r)], path[len(r) + 1:]
    sys.exit('path "{}" is outside git roots'.format(path))


def get_date_from_epoch(epoch):
    return datetime.utcfromtimestamp(int(epoch)).isoformat()


def main():
    args = docopt.docopt(__doc__, version='0.1')

    if args['-f'] not in ['text', 'yaml']:
        sys.exit('Unsupported output format "{}".'.format(args['-f']))

    with open(args['LOGFILE'], 'r') as inf:
        sources = inf.read().splitlines()

    revisions = {}
    if args['-r']:
        for r in args['-r']:
            fields = r.split(':')
            if len(fields) != 2:
                sys.exit('Malformed revision specification "{}"'.format(r))
            revisions[fields[0]] = fields[1]
            if git_log_empty(*fields):
                revisions[fields[0]] = ''

    commits = set()
    roots = []
    for source in sources:
        if source.startswith('root:'):
            roots.append(source.split(':')[1])
        elif source.startswith('range:'):
            rspec = source.split(':')
            gitroot, fpath = split_path(rspec[3], roots)
            commits |= get_commits_from_range(rspec[1], rspec[2], fpath, gitroot, revisions.get(gitroot))
        else:
            gitroot, fpath = split_path(source, roots)
            commits |= get_commits_from_path(fpath, gitroot, revisions.get(gitroot))

    if args['-o']:
        outp = open(args['-o'], 'w')
    else:
        outp = sys.stdout

    if args['-f'] == 'text':
        for commit in sorted(commits, reverse=True):
            print(get_commit_message(commit[1], commit[2], args['-m']), file=outp)
    else:
        msgs = []
        for commit in sorted(commits, reverse=True):
            sub = get_commit_message(commit[1], commit[2], '%s').lstrip('- ')
            body = MultiStr(get_commit_message(commit[1], commit[2], '%b').rstrip('\n'))
            if body:
                msgs.append(
                    {
                        'change': sub,
                        'date': get_date_from_epoch(commit[0]),
                        'details': body
                    }
                )
            else:
                msgs.append({'change': sub,
                             'date': get_date_from_epoch(commit[0])})
        yaml.add_representer(MultiStr, repr_mstr, Dumper=yaml.SafeDumper)
        if args['-t']:
            log = {args['-t']: msgs}
        else:
            log = msgs
        yaml.safe_dump(log, outp)

    if args['-o']:
        outp.close()

    if not commits:
        sys.exit(2)


if __name__ == '__main__':
    main()  # pragma: no cover
