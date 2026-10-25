#!/usr/bin/env python3
"""Independent corner/initial-condition checks. Run from any cwd; retains decks and outputs."""
from pathlib import Path
import subprocess,re,math
HERE=Path(__file__).resolve().parent
MODEL=HERE.parents[1]/'sim/models/lmx58_lm2904.lib'
def run(name,source,load,stop,initial=None,feed=False):
    supply='VBAT bat 0 11.6\nR9 bat vcc 1k\nC16 vcc 0 10u\nC17 vcc 0 100n' if feed else 'VCC vcc 0 12'
    deck=f'''* Independent {name}
.include {MODEL}
{supply}
V5 five 0 4.8
VIN input 0 {source}
XA input inv vcc 0 oa LMX58_LM2904
XB 0 unused vcc 0 unused LMX58_LM2904
R6 conn inv 68k
R7 inv 0 100k
C15 oa inv 1n
R8 oa clamp 330
R11 clamp conn 470
RL conn {load} 4.7k
CL conn 0 1n
.model dx D(Is=2.52n N=1.752 Rs=.568 Cjo=4p)
D3 clamp five dx
D4 0 clamp dx
{'.ic v(vcc)='+str(initial) if initial is not None else ''}
.save v(conn) v(vcc)
.tran 5u {stop}m 0 20u {'uic' if initial is not None else ''}
.control
run
meas tran vout AVG v(conn) from={stop-5}m to={stop}m
meas tran vlo MIN v(conn) from={stop-5}m to={stop}m
meas tran vhi MAX v(conn) from={stop-5}m to={stop}m
meas tran rail AVG v(vcc) from={stop-5}m to={stop}m
echo RES $&vout $&vlo $&vhi $&rail
quit
.endc
.end
'''
    path=HERE/(name+'.cir');path.write_text(deck)
    try:
        p=subprocess.run(['ngspice','-b',str(path)],capture_output=True,text=True,timeout=180)
        out=p.stdout+p.stderr
    except subprocess.TimeoutExpired as e:
        out=(e.stdout or b'').decode(errors='replace')+'\nTIMEOUT\n';p=None
    (HERE/(name+'.out')).write_text(out)
    match=re.search(r'^RES (.*)$',out,re.M)
    values=match.group(1).split() if match else []
    good=len(values)==4 and all(re.fullmatch(r'[-+\d.eE]+',x) and math.isfinite(float(x)) for x in values)
    print(name, 'PASS measurements '+str(values) if p and p.returncode==0 and good else 'FAILED; see raw output',flush=True)
    return bool(p and p.returncode==0 and good)
ok=True
for init in [11.6,0]:
    ok=run('TK6-long-ic'+str(init),'PWL(0 1 2m 1 6m 2.976190476)','0',120,init,True) and ok
for load in ['0','five']:
    ok=run('TK6-zero-'+load,'PWL(0 1 0.5m 1 4.5m 0)',load,15) and ok
raise SystemExit(not ok)
