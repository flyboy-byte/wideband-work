#!/usr/bin/env python3
"""Three current-wrapper corners with independently checked raw completion."""
import pathlib,subprocess,tempfile,shutil,os
from spice_validation import reached_window
here=pathlib.Path(__file__).resolve().parent;sim=here.parents[1]/'sim'
source=(sim/'full_scale_corners.sh').read_text()
prefix=source.split('for s in 13.4 11.6 9.0;')[0].replace('cd "$(dirname "$0")"','cd '+str(sim))
assert prefix!=source
real=shutil.which('ngspice');assert real
with tempfile.TemporaryDirectory(prefix='wb_r6_spice_proxy_') as t:
    proxy=pathlib.Path(t)/'ngspice';proxy.symlink_to(here/'spice_capture.py')
    # Invoke via a tiny shell launcher so the tracked Python proxy need not have executable metadata.
    proxy.unlink();proxy.write_text('#!/bin/sh\nexec python3 "'+str(here/'spice_capture.py')+'" "$@"\n');proxy.chmod(0o700)
    env=dict(os.environ,PATH=t+os.pathsep+os.environ['PATH'],WB_REAL_NGSPICE=real)
    cases=[('TK6-raw-high',13.4,4.8,'4.7k'),('TK6-raw-low',9.0,4.8,'4.7k'),('TK6-raw-10k',11.6,5.0,'10k')]
    bad=0
    for label,v,v5,load in cases:
        p=subprocess.run(['bash','-s'],input=prefix+f'\nrun {v} {v5} {load}\n[ "$FAILED" -eq 0 ]\n',env=dict(env,WB_AUDIT_CASE=label),capture_output=True,text=True,timeout=320)
        out=(here/(label+'.out')).read_text();good=p.returncode==0 and reached_window(out,.060)
        print(label,'raw completion',good,p.stdout.strip(),flush=True);bad+=not good
    raise SystemExit(bool(bad))
