#!/usr/bin/env python3
"""Upstream's gtest suite plus ours (test/Makefile: sampler, heater, heater Update() F7, bootloader bounds F1, watchdog D10),
built on the host with ASan into a fresh absolute build directory (a relative one picks up ARM objects from
firmware/build: CLAUDE.md "Test-build quirk"). Prints gtest's last line; exit 1 on a build or test failure."""
import os, shutil, subprocess, sys, tempfile

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
b = tempfile.mkdtemp(prefix='wb_host_')
try:
    os.makedirs(os.path.join(b, 'obj')); os.makedirs(os.path.join(b, 'lst'))
    r = subprocess.run(['nice', '-n', '10', 'make', '-j4', f'BUILDDIR={b}'], cwd=os.path.join(REPO, 'test'),
                       capture_output=True, text=True)
    if r.returncode:
        print('\n'.join((r.stdout + r.stderr).splitlines()[-5:]))
        print('host test build failed')
        sys.exit(1)
    r = subprocess.run([os.path.join(b, 'wideband_test')], capture_output=True, text=True,
                       env=dict(os.environ, ASAN_OPTIONS='detect_stack_use_after_return=1'))
    lines = [l for l in r.stdout.splitlines() if l.startswith('[  PASSED  ]') or l.startswith('[  FAILED  ]')]
    print(lines[0] if r.returncode == 0 and lines else '\n'.join(lines[-5:]) or f'exit {r.returncode}')
    sys.exit(r.returncode != 0)
finally:
    shutil.rmtree(b, ignore_errors=True)
