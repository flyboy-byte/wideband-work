#!/usr/bin/env python3
"""Transparent proxy retaining raw output/deck for selected production-wrapper cases."""
import pathlib,subprocess,os,sys,shutil
here=pathlib.Path(__file__).resolve().parent
label=os.environ['WB_AUDIT_CASE']
shutil.copy(sys.argv[-1],here/(label+'.cir'))
p=subprocess.run([os.environ['WB_REAL_NGSPICE'],*sys.argv[1:]],capture_output=True,text=True)
(here/(label+'.out')).write_text(p.stdout+p.stderr)
sys.stdout.write(p.stdout);sys.stderr.write(p.stderr)
raise SystemExit(p.returncode)
