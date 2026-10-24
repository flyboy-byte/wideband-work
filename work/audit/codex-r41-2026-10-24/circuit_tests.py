"""Independent r41 typical-model tests, not hardware or tolerance qualification.

Includes both amplifier channels and the real 1k supply feed. Diodes are an
explicit sensitivity model, NOT the manufacturer's qualified clamp model.
Each case has a timeout; missing measurements cannot count as success.
"""
import json
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[1]
MODEL = WORK / 'sim/models/lmx58_lm2904.lib'
cases = [('step_10n',12,100000,'10n',True), ('step_47n',12,100000,'47n',True),
         ('full_10k',12,10000,'1n',False), ('full_4k7',12,4700,'1n',False),
         ('low_supply_4k7',7,4700,'1n',False)]
results = []
for name, supply, load, cable, step in cases:
    vin = 'PULSE(1 1.1 4m 10n 10n 1 2)' if step else 'PWL(0 1 0.5m 1 4.5m 2.976190476)'
    deck = f'''* r41 independent case {name}; supply is protected rail AFTER D2
.include {MODEL}
VBAT battery 0 {supply}
R9 battery vcc 1k
C16 vcc 0 10u
C17 vcc 0 100n
V5 five 0 5
VIN input 0 {vin}
XACTIVE input inv vcc 0 oa LMX58_LM2904
XUNUSED 0 unused vcc 0 unused LMX58_LM2904
R6 connector inv 68k
R7 inv 0 100k
C15 oa inv 1n
R8 oa clamp 330
R11 clamp connector 470
RL connector 0 {load}
CL connector 0 {cable}
* Illustrative silicon diode only: sensitivity, not a production-part guarantee.
.model sensitivity D(Is=2.52n N=1.752 Rs=.568 Cjo=4p)
D3 clamp five sensitivity
D4 0 clamp sensitivity
* Zener omitted: supply never exceeds 12V in these cases.
.save v(connector) v(vcc) v(clamp) v(oa) i(V5)
.tran 1u 8m 0 2u
.control
set ngbehavior=psa
run
meas tran before AVG v(connector) from=3.5m to=3.9m
meas tran final AVG v(connector) from=7.5m to=8m
meas tran peak MAX v(connector) from=4m to=8m
meas tran late_min MIN v(connector) from=7.5m to=8m
meas tran late_max MAX v(connector) from=7.5m to=8m
meas tran rail AVG v(vcc) from=7.5m to=8m
meas tran clamp_voltage AVG v(clamp) from=7.5m to=8m
meas tran injection AVG i(V5) from=7.5m to=8m
quit
.endc
.end
'''
    path = HERE / (name + '.cir')
    path.write_text(deck)
    try:
        p = subprocess.run(['nice','-n','10','ngspice','-b',str(path)], cwd=WORK/'sim',
                           capture_output=True, text=True, timeout=90)
        output = p.stdout + p.stderr
        (HERE / (name + '.log')).write_text(output)
        values = {k:float(v) for k,v in re.findall(r'^(before|final|peak|late_min|late_max|rail|clamp_voltage|injection)\s*=\s*([-+\d.eE]+)', output,re.M)}
        result = dict(case=name,returncode=p.returncode,complete=len(values)==8,values=values)
        if step and len(values)==8:
            result['overshoot_pct'] = 100*max(0,values['peak']-values['final'])/abs(values['final']-values['before'])
            result['late_ripple_mV'] = 1000*(values['late_max']-values['late_min'])
    except subprocess.TimeoutExpired:
        result = dict(case=name,complete=False,timeout_seconds=90)
    results.append(result)
    (HERE/'circuit-results.json').write_text(json.dumps(results,indent=2)+'\n')
    print(json.dumps(result),flush=True)
