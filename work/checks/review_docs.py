#!/usr/bin/env python3
"""The reviewer docs agree with the repo: REVIEW.md, review/TASKS.md, review/FINDINGS-TEMPLATE.md, review_pack.sh.

  python3 checks/review_docs.py [--self-test]      run from work/

Fails when:
  - REVIEW.md's "expect: N checks" is not the number of checks in checks/checks.json;
  - the task IDs in TASKS.md's table, its ### sections and the template's coverage table differ;
  - a file a task names (backticked, in its "Files:" line, outside parentheses) is not in the review pack;
  - a script a task tells you to run (checks/, gen/, sim/) doesn't exist;
  - a file linked from REVIEW.md doesn't exist;
  - the AUDIT.md hand-off still has <placeholders>.
--self-test feeds it broken copies and expects each failure.
"""
import fnmatch, glob, json, os, re, shlex, sys

WORK = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
BUILTIN = {'PROMPT.md', 'HANDOFF.md', 'INDEX.md', 'REQUIREMENTS.md', 'pinmap.csv', 'last_run.json'}


def pack_names(pack_sh, rev='carrier-f'):
    """File names in the pack: the arguments to audit_pack.py in review_pack.sh, renamed by =NAME, plus renders."""
    m = re.search(r'audit_pack\.py "\$REV"(.*?)\n(?!\s)', pack_sh, re.S)
    args = shlex.split(m.group(1).replace('\\\n', ' ')) if m else []
    names = {a.partition('=')[2] or os.path.basename(a) for a in args}
    names |= {os.path.basename(p) for p in glob.glob(os.path.join(WORK, 'renders', rev, '*'))}
    return names | BUILTIN


def problems(review, tasks, template, pack_sh, checks, handoff):
    out = []
    m = re.search(r'expect: (\d+) checks', review)
    if not m or int(m.group(1)) != len(checks):
        out.append(f'REVIEW.md expects {m.group(1) if m else "no"} checks; checks.json has {len(checks)}')
    table = re.findall(r'^\| (TK\d+) \|', tasks, re.M)
    sections = re.findall(r'^### (TK\d+)\.', tasks, re.M)
    cover = [t for t in re.findall(r'^\| (TK\d+) ', template, re.M) if t != 'TK99']
    if not table or table != sections or table != cover:
        out.append(f'task IDs differ: table {table}, sections {sections}, template coverage {cover}')
    names = pack_names(pack_sh)
    for line in re.findall(r'^- \*\*Files:\*\*(.*)$', tasks, re.M):
        for f in re.findall(r'`([^`/ ]+\.[a-z_]+)`', re.sub(r'\([^)]*\)', '', line)):   # parentheses: notes, not files
            if not fnmatch.filter(names, f):
                out.append(f'TASKS.md names {f}, which is not in the review pack')
    for s in sorted(set(re.findall(r'\b((?:checks|gen|sim)/[\w.-]+\.(?:py|sh))', tasks + review))):
        if not os.path.exists(os.path.join(WORK, s)):
            out.append(f'a doc tells you to run {s}, which does not exist')
    for link in re.findall(r'\]\(((?:work/)[^)#]+)\)', review):
        if not os.path.exists(os.path.join(WORK, '..', link)):
            out.append(f'REVIEW.md links {link}, which does not exist')
    if re.search(r'<[^>\n]+>', handoff):
        out.append('the AUDIT.md hand-off still has <placeholders>')
    return out


def load():
    r = lambda p: open(os.path.join(WORK, p)).read()
    audit = r('AUDIT.md')
    m = re.search(r'## Hand-off.*?(?=\n## )', audit, re.S)
    return (r('../REVIEW.md'), r('review/TASKS.md'), r('review/FINDINGS-TEMPLATE.md'), r('checks/review_pack.sh'),
            json.load(open(os.path.join(WORK, 'checks/checks.json'))), m.group(0) if m else '<missing>')


def self_test():
    good = load()
    if problems(*good):
        return print('self-test: the real docs fail; fix them first') or 1
    cases = {
        'check count': (good[0].replace('expect: ', 'expect: 9', 1),) + good[1:],
        'task IDs': (good[0], re.sub(r'^### TK\d+\.', '### TK98.', good[1], count=1, flags=re.M), *good[2:]),
        'pack file': (good[0], good[1].replace('`carrier-cpl.csv`', '`no-such-file.csv`', 1), *good[2:]),
        'script': (good[0], good[1].replace('checks/fab_files.py', 'checks/no_such.py', 1), *good[2:]),
        'placeholder': good[:5] + (good[5] + '\n<fill me>',),
    }
    bad = [k for k, c in cases.items() if not problems(*c)]
    print(f'review docs self-test: {len(cases) - len(bad)}/{len(cases)} broken copies caught' + (f'; missed {bad}' if bad else ''))
    return 1 if bad else 0


def main():
    if '--self-test' in sys.argv:
        return self_test()
    p = problems(*load())
    for x in p:
        print('  ' + x)
    print(f'review docs: {len(p)} problem(s)')
    return 1 if p else 0


if __name__ == '__main__':
    sys.exit(main())
