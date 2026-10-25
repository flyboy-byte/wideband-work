"""Save one bounded command's complete evidence, run from work/ by default."""
import json
import subprocess
import sys
import time
from pathlib import Path
HERE=Path(__file__).resolve().parent
WORK=HERE.parents[1]
label,*cmd=sys.argv[1:]
start=time.monotonic()
try:
    p=subprocess.run(cmd,cwd=WORK,capture_output=True,text=True,timeout=900)
    rc,output=p.returncode,p.stdout+p.stderr
except subprocess.TimeoutExpired as e:
    rc=124
    output=(e.stdout or b'').decode(errors='replace')+(e.stderr or b'').decode(errors='replace')+'\nTIMEOUT, NOT A PASS\n'
(HERE/(label+'.log')).write_text(output)
(HERE/(label+'.json')).write_text(json.dumps(dict(command=cmd,cwd=str(WORK),returncode=rc,seconds=round(time.monotonic()-start,2)),indent=2)+'\n')
print(f'{label}: exit {rc}; {time.monotonic()-start:.1f}s\n'+output[-2000:])
raise SystemExit(rc)
