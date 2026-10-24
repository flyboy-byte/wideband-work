"""Check fail-closed behavior by replacing ngspice in a child process only."""
import os
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[1]
with tempfile.TemporaryDirectory(prefix='wb-sim-failure-') as tmp:
    stub = Path(tmp)/'ngspice'
    stub.write_text('#!/bin/sh\necho "intentional simulator failure" >&2\nexit 1\n')
    stub.chmod(0o700)
    report = []
    for name in ('stability.sh', 'load_accuracy.sh'):
        p = subprocess.run(['bash',str(WORK/'sim'/name)],capture_output=True,text=True,
                           env=dict(os.environ,PATH=tmp+os.pathsep+os.environ['PATH']),timeout=20)
        report.append(f'{name}: simulator always exits 1; wrapper exits {p.returncode}\n{p.stdout}{p.stderr}')
    text = '\n'.join(report)
    (HERE/'sim-failure.txt').write_text(text)
    print(text)
