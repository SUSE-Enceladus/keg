# Copyright (c) 2024 SUSE Software Solutions Germany GmbH. All rights reserved.
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
                                  [-m MSG_FORMAT] [-t ROOT_TAG] [-a AUTHOR_STRING] LOGFILE
       generate_recipes_changelog -h | --help

Arguments:
    LOGFILE    Path to file contaning Keg source log

Options:
    -o OUTPUT_FILE
        Write output to OUTPUT_FILE (stdout if omitted)

    -r PATH:REV
        Set git revision range to REV for repo at PATH

    -f FORMAT
        Output format, 'text','yaml', 'json', or 'osc' [default: json]

    -m MSG_FORMAT
        Format spec for commit messages (see 'format:<string>' in 'man git-log')
        [default: - %s] (only used with text format)

    -t ROOT_TAG
        Use ROOT_TAG for yaml or json output (e.g. image version)

    -a AUTHOR_STRING
        Use AUTHOR_STRING (typically name + email) for OSC change log entries
"""

import docopt
import logging
import json
import subprocess
import sys
import yaml
from datetime import datetime, timezone

log = logging.getLogger('generate_recipes_changelog')
log.setLevel(logging.INFO)


class MultiStr(str):
    pass


class RangeFile:
    def __init__(self):
        self.lines = []

    def add_range(self, line_start, line_end):
        self.lines += range(line_start, line_end + 1)

    def get_ranges(self):
        ranges = []
        rstart = None
        rend = None
        for i in sorted(set(self.lines)):
            if not rstart:
                rstart = i
                rend = i
                continue
            if i == rend + 1:
                rend += 1
            else:
                ranges.append((rstart, rend))
                rstart = i
                rend = i
        if rend:
            ranges.append((rstart, rend))
        return ranges


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


def get_deletion_commit(line_no, filespec, gitroot, rev):
    # To find a commit that deleted a line, use git blame to find the last commit
    # that still had the line in question.
    cmdargs = ['git', '-C', gitroot, 'blame', '--no-merges', '--reverse', rev, '-L', f'{line_no},{line_no}', '--', filespec]
    sp = subprocess.run(args=cmdargs, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if sp.returncode != 0:
        raise Exception('git exited with error "{}"'.format(sp.stderr))
    last_commit_with_line = sp.stdout.decode('utf-8').split(' ')[0].lstrip('^')

    # Find the next commit in line, assuming that it is the one that deleted the line.
    cmdargs = ['git', '-C', gitroot, 'log', '--format=%ct %H', last_commit_with_line + '..', '--', filespec]
    sp = subprocess.run(args=cmdargs, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if sp.returncode != 0:
        raise Exception('git exited with error "{}"'.format(sp.stderr))
    commits = sp.stdout.decode('utf-8').splitlines()
    if not commits:
        # No commit means the line was probably not deleted but just moved
        log.debug(f'Source log indicates {filespec}:{line_no} was deleted but cannot find commit')
        return None
    deletion_commit = commits[-1]
    return tuple(deletion_commit.split() + [gitroot])


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

    if args['-f'] not in ['text', 'yaml', 'json', 'osc']:
        sys.exit('Unsupported output format "{}".'.format(args['-f']))

    with open(args['LOGFILE'], 'r') as inf:
        sources = inf.read().splitlines()

    revisions = {}
    if args['-r']:
        for r in args['-r']:
            fields = r.rsplit(':', 1)
            if len(fields) != 2:
                sys.exit('Malformed revision specification "{}"'.format(r))
            revisions[fields[0]] = fields[1]
            if git_log_empty(*fields):
                revisions[fields[0]] = ''

    commits = set()
    roots = []
    range_files = {}

    for source in sources:
        if source.startswith('root:'):
            roots.append(source.split(':', 1)[1])
        elif source.startswith('range:'):
            rspec = source.split(':', 3)
            rf = range_files.get(rspec[3])
            if not rf:
                rf = RangeFile()
                range_files[rspec[3]] = rf
            rf.add_range(int(rspec[1]), int(rspec[2]))
        elif source.startswith('deleted:'):
            rspec = source.split(':', 2)
            gitroot, fpath = split_path(rspec[2], roots)
            rev = revisions.get(gitroot)
            if rev:
                del_commit = get_deletion_commit(rspec[1], fpath, gitroot, rev)
                if del_commit:
                    commits.add(del_commit)
        else:
            gitroot, fpath = split_path(source, roots)
            commits |= get_commits_from_path(fpath, gitroot, revisions.get(gitroot))

    for f in range_files:
        gitroot, fpath = split_path(f, roots)
        for r in range_files[f].get_ranges():
            commits |= get_commits_from_range(r[0], r[1], fpath, gitroot, revisions.get(gitroot))

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
        if args['-f'] == 'yaml':
            yaml.add_representer(MultiStr, repr_mstr, Dumper=yaml.SafeDumper)
            if args['-t']:
                log = {args['-t']: msgs}
            else:
                log = msgs
            yaml.safe_dump(log, outp)
        elif args['-f'] == 'json':
            if args['-t']:
                log = {args['-t']: msgs}
            else:
                log = msgs
            json.dump(log, outp, indent=2)
        elif args['-f'] == 'osc':
            print('-------------------------------------------------------------------', file=outp)
            outp.write((datetime.now(timezone.utc).strftime('%c %Z')))
            if args['-a']:
                outp.write(' - ')
                outp.write(args['-a'])
            outp.write('\n\n')
            indent = '- '
            if args['-t']:
                print('- Update to {}'.format(args['-t']), file=outp)
                indent = '  + '
            for msg in msgs:
                outp.write(indent)
                print(msg['change'], file=outp)
            outp.write('\n')

    if args['-o']:
        outp.close()

    if not commits:
        sys.exit(2)


if __name__ == '__main__':
    main()  # pragma: no cover
