#!/usr/bin/env python3
"""Serialize the audit's remaining sims after the already-running full-scale sweep."""
import os,time,subprocess,pathlib,sys
here=pathlib.Path(__file__).resolve().parent
pid=int(sys.argv[1]); deadline=time.monotonic()+1100
while time.monotonic()<deadline:
    try:os.kill(pid,0)
    except ProcessLookupError:break
    time.sleep(2)
else:raise SystemExit('Sweep still running; queued sims NOT RUN')
# A timed-out shell could leave its simulator alive briefly. Never overlap ngspice runs.
deadline=time.monotonic()+320
while subprocess.run(['pgrep','-x','ngspice'],capture_output=True).returncode==0:
    if time.monotonic()>deadline:raise SystemExit('Another ngspice still running; queued sims NOT RUN')
    time.sleep(2)
for label,cmd in [('TK6-extra',['python3','audit/astra-2026-10-25/analog_extra.py']),('TK7-stability',['python3','audit/astra-2026-10-25/stability_current.py'])]:
    subprocess.run(['python3',str(here/'capture.py'),label,*cmd],check=False)
