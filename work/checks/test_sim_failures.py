#!/usr/bin/env python3
"""The sim wrappers fail when ngspice gives no valid result (Codex R41-CX2, 2026-10-24): a fake ngspice that exits 1,
one that exits 0 with no measurement (what a failed operating point looks like), and one that answers, which must pass.
Runs a copy of sim/ with a placeholder model file, so it needs neither ngspice nor TI's model.
  python3 checks/test_sim_failures.py      exit 1 on any wrong verdict"""
import os, shutil, subprocess, sys, tempfile

SIM = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'sim')
FAKES = {  # name: (script body, expected exit is nonzero)
    'exits 1': ('echo "intentional simulator failure" >&2; exit 1', True),
    'exits 0, no measurement': ('echo "doAnalyses: TRAN:  Timestep too small"; exit 0', True),
    'exits 0, partial measurement': ('echo "RES 1.0 2.0"; exit 0', True),
    'answers, no settling crossing': ('if grep -q "let os" "$2"; then echo "RES 1.5 2.5 2.6 1.0 0.01"; else echo "RES 2.52"; fi', False),
    'answers': ('if grep -q "let os" "$2"; then echo "RES 1.5 2.5 2.6 1.0 0.01 120"; else echo "RES 2.52"; fi', False),
}


def main():
    bad = 0
    with tempfile.TemporaryDirectory(prefix='wb-simfail-') as t:
        sim = os.path.join(t, 'sim')
        os.makedirs(os.path.join(sim, 'models'))
        open(os.path.join(sim, 'models', 'lmx58_lm2904.lib'), 'w').close()
        for name in ('stability.sh', 'load_accuracy.sh'):
            shutil.copy(os.path.join(SIM, name), sim)
        bindir = os.path.join(t, 'bin')
        os.makedirs(bindir)
        for fake, (body, want_fail) in FAKES.items():
            stub = os.path.join(bindir, 'ngspice')
            open(stub, 'w').write('#!/bin/sh\n' + body + '\n')
            os.chmod(stub, 0o700)
            for name in ('stability.sh', 'load_accuracy.sh'):
                if name == 'load_accuracy.sh' and fake == 'exits 0, partial measurement':
                    continue  # it reads one value; covered by "no measurement"
                p = subprocess.run(['bash', os.path.join(sim, name)], capture_output=True, text=True, timeout=120,
                                   env=dict(os.environ, PATH=bindir + os.pathsep + os.environ['PATH']))
                ok = (p.returncode != 0) == want_fail
                bad += not ok
                print(f"{'ok  ' if ok else 'FAIL'} {name:17} ngspice {fake:28} -> exit {p.returncode}"
                      + ('' if ok else f' (want {"nonzero" if want_fail else "0"})\n' + p.stdout[-400:]))
    print(f'sim wrappers: {bad} wrong verdict(s)')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
