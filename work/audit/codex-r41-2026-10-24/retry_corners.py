"""Retry failed operating points with numerical guesses, never change circuit values.
Also tests a 5V pull-up receiver at a 2.5V target (accepted low-output case excluded).
"""
import json
import re
import subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
WORK=HERE.parents[1]
results=[]
cases=[('full_10k','full_10k',None),('low_supply_4k7','low_supply_4k7',None),
       ('pullup_4k7_midscale','full_4k7','pullup'),('full_4k7_9V','full_4k7','9V')]
for name,source,variant in cases:
    text=(HERE/(source+'.cir')).read_text()
    if variant=='pullup':
        text=text.replace('RL connector 0 4700','RL connector five 4700').replace('4.5m 2.976190476','4.5m 1.488095238')
    if variant=='9V':
        text=text.replace('VBAT battery 0 12','VBAT battery 0 9')
    text=text.replace('.save ','.nodeset v(vcc)=5 v(oa)=1.8 v(clamp)=1.7 v(connector)=1.68 v(inv)=1 v(unused)=.003\n.save ')
    path=HERE/('retry_'+name+'.cir')
    path.write_text(text)
    try:
        p=subprocess.run(['nice','-n','10','ngspice','-b',str(path)],cwd=WORK/'sim',capture_output=True,text=True,timeout=60)
        output=p.stdout+p.stderr
        (HERE/('retry_'+name+'.log')).write_text(output)
        values={k:float(v) for k,v in re.findall(r'^(before|final|peak|late_min|late_max|rail|clamp_voltage|injection)\s*=\s*([-+\d.eE]+)',output,re.M)}
        record=dict(case=name,complete=len(values)==8,returncode=p.returncode,values=values)
    except subprocess.TimeoutExpired:
        record=dict(case=name,complete=False,timeout_seconds=60)
    results.append(record)
    (HERE/'retry-results.json').write_text(json.dumps(results,indent=2)+'\n')
    print(record,flush=True)
