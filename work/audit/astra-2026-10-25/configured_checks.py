#!/usr/bin/env python3
"""Run configured checks, keeping reports here instead of rewriting designer STATE.md."""
import pathlib,subprocess,json,time
HERE=pathlib.Path(__file__).resolve().parent;WORK=HERE.parents[1]
rows=[]
for i,c in enumerate(json.loads((WORK/'checks/checks.json').read_text()),1):
    cmd=c['cmd']
    if cmd==['sh','-c','python3 gen/module_fab.py >/dev/null && python3 checks/jlc_rotation.py --board module']:
        cmd=['python3','checks/jlc_rotation.py','--board','module'] # verify existing output, don't restage it
    start=time.monotonic()
    try:
        p=subprocess.run(cmd,cwd=WORK,capture_output=True,text=True,timeout=180)
        rc,out=p.returncode,p.stdout+p.stderr
    except subprocess.TimeoutExpired as e:
        rc,out=124,(e.stdout or b'').decode(errors='replace')+'\nTIMEOUT: NOT PASS\n'
    name=f'TK12-check-{i:02d}.log';(HERE/name).write_text(out)
    row=dict(name=c['name'],command=cmd,returncode=rc,advisory=bool(c.get('advisory')),seconds=round(time.monotonic()-start,2),log=name)
    rows.append(row);(HERE/'TK12-checks.json').write_text(json.dumps(rows,indent=2)+'\n')
    print(i,rc,c['name'],flush=True)
raise SystemExit(any(r['returncode'] and not r['advisory'] for r in rows))
