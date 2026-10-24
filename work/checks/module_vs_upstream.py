#!/usr/bin/env python3
"""The module board files are exactly upstream's (branch master = mck1117/wideband), so its raw DRC errors are upstream's
own (owner decision D2, 2026-10-23: raw DRC is advisory; this and drc_vs_upstream.py gate instead). Exit 1 if any
file under hardware/board_module differs from master."""
import subprocess, sys

r = subprocess.run(['git', 'diff', '--name-only', 'master', '--', '../hardware/board_module'], capture_output=True, text=True)
if r.returncode:
    print('git diff failed:', r.stderr.strip())
    sys.exit(1)
changed = [f for f in r.stdout.splitlines() if f]
print(f'module board vs upstream master: {len(changed)} file(s) differ' + (f": {', '.join(changed[:5])}" if changed else ''))
sys.exit(1 if changed else 0)
