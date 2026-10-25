#!/usr/bin/env python3
"""release.py must judge the latest audit round, wherever AUDIT.md puts it (round 7, 2026-10-25: the file lists rounds
newest first, and the old gate read the last heading, round 5).   python3 checks/test_release.py   (from work/)"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import release

CASES = [  # (AUDIT.md text, the round the gate must judge)
    ('# Audit\n## Rounds\n### Round 7 — new\nCommit: aaaaaaa\n### Round 6 — old\nCommit: bbbbbbb\n### Round 5 — older\n', '7'),
    ('# Audit\n## Rounds\n### Round 1 — a\n### Round 2 — b\nCommit: ccccccc\n', '2'),
    ('# Audit\n### Round 4 follow-through, part 1\n### Round 10 — x\n### Round 9 — y\n', '10'),
    ('# Audit\nno rounds\n', None),
]
bad = 0
for text, want in CASES:
    got = release.latest_round(text)
    got = got.split()[2] if got else None
    if got != want:
        bad += 1
        print(f'WRONG: judged round {got}, want {want}')
print(f'release gate rounds: {len(CASES) - bad}/{len(CASES)} right')
sys.exit(1 if bad else 0)
