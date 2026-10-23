#!/usr/bin/env python3
"""Build a read-only audit pack for an independent reviewer (another model, a person) on this commit.

  audit_pack.py REV [FILE...]    FILEs: BOM, CPL, Gerber zip, board/schematic files, datasheets to include

Writes audit/REV-DATE/ with PROMPT.md (paste this first), the hand-off from AUDIT.md, REQUIREMENTS.md (incl. the
bring-up tests), pinmap.csv, the last check results, renders/REV/*, and the given files, all read-only.
Bring the reviewer's findings back into AUDIT.md as a new round naming the auditor and this commit."""
import datetime, glob, os, re, shutil, stat, subprocess, sys

PROMPT = """# Independent PCB audit: {rev} at commit {head}

You are auditing a printed circuit board before it is ordered. You have only the files in this folder; you
did not design it. Don't trust the designer's conclusions; check from the files and first principles.

Read in this order: HANDOFF.md (what the board is, what changed, what to check first, what is already known and
accepted), REQUIREMENTS.md (including the numbered bring-up tests that define "working"), pinmap.csv, the check
results, then the fab files and pictures.

Report:
1. Verdict first: "Would I order these files as they are?" yes / no, one sentence why.
2. Findings table: ID | Severity | Location | Evidence (numbers) | Smallest fix
   Severity: BLOCKER = don't order; BUG = wrong but workable; RISK = could bite (state the condition); NOTE.
   Location = file and line, or reference designator and coordinates.
3. What you checked and found correct.
4. What you could not check, and what you would need to.
Don't re-report items listed as known and accepted.
"""


def main(rev, files):
    head = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], capture_output=True, text=True).stdout.strip() or 'no-git'
    dst = os.path.join('audit', f'{rev}-{datetime.date.today().isoformat()}')
    os.makedirs(dst, exist_ok=True)
    for f in os.listdir(dst):  # rebuilding the same day: make the old copies writable again
        os.chmod(os.path.join(dst, f), stat.S_IRUSR | stat.S_IWUSR)
    open(os.path.join(dst, 'PROMPT.md'), 'w').write(PROMPT.format(rev=rev, head=head))
    audit = open('AUDIT.md').read() if os.path.exists('AUDIT.md') else ''
    m = re.search(r'## Hand-off.*?(?=\n## )', audit, re.S)
    open(os.path.join(dst, 'HANDOFF.md'), 'w').write((m.group(0) if m else '## Hand-off\n(missing in AUDIT.md: fill it first)') + '\n')
    picked = ['REQUIREMENTS.md', 'pinmap.csv', 'checks/last_run.json'] + sorted(glob.glob(f'renders/{rev}/*')) + files
    missing = []
    for f in picked:
        if os.path.isfile(f):
            shutil.copy2(f, os.path.join(dst, os.path.basename(f)))
        else:
            missing.append(f)
    for f in os.listdir(dst):
        p = os.path.join(dst, f)
        os.chmod(p, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    print(f'audit pack: {dst}/ ({len(os.listdir(dst))} files, read-only). Paste PROMPT.md first, then attach the rest.')
    for f in missing:
        print(f'  not included (not found): {f}')
    if not m or re.search(r'<[^>\n]+>', m.group(0)):
        print('  WARNING: the hand-off in AUDIT.md still has <placeholders>; fill it before sending')
    return 0


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1], sys.argv[2:]))
