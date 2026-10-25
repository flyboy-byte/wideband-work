"""Independent per-row carrier BOM/CPL comparison; rotation source stays explicit."""
import csv,json,math
from pathlib import Path
import pcbnew
HERE=Path(__file__).resolve().parent
WORK=HERE.parents[1]
board=pcbnew.LoadBoard(str(WORK.parent/'hardware/board_carrier/board_carrier.kicad_pcb'))
fps={f.GetReference():f for f in board.GetFootprints()}
rot=json.loads((WORK/'checks/jlc_rotation.json').read_text())
bom=list(csv.DictReader((WORK/'out/carrier/carrier-bom.csv').open()))
cpl=list(csv.DictReader((WORK/'out/carrier/carrier-cpl.csv').open()))
lines=['# Carrier row-by-row checks','', 'Rotation corrections are checked against the cached measurement, not a JLC placement guarantee.','',
       '| BOM line | Refs | Value / LCSC / footprint matches board |','| --- | --- | --- |']
for i,row in enumerate(bom,1):
    refs=row['Designator'].split(',')
    ok=all(fps[r].GetValue()==row['Comment'] and fps[r].GetFieldText('LCSC')==row['LCSC Part #']
           and fps[r].GetFPID().GetLibItemName().wx_str()==row['Footprint'] for r in refs)
    lines.append(f"| {i} | {','.join(refs)} | {'OK' if ok else 'MISMATCH'} |")
    assert ok,row
lines+=['','| CPL ref | position residual mm | rotation matches measured correction | Top |','| --- | --- | --- | --- |']
for row in cpl:
    ref=row['Designator']; f=fps[ref]; t=rot[ref]
    dx=float(row['Mid X'])-pcbnew.ToMM(f.GetPosition().x)-t['pos_shift_mm'][0]
    dy=-float(row['Mid Y'])-pcbnew.ToMM(f.GetPosition().y)-t['pos_shift_mm'][1]
    error=math.hypot(dx,dy)
    angle=(float(row['Rotation'])-f.GetOrientationDegrees()-t['correction'])%360
    angle=min(angle,360-angle)
    top=f.GetLayer()==pcbnew.F_Cu and row['Layer']=='Top'
    lines.append(f'| {ref} | {error:.6f} | {angle:.6f} degrees | {top} |')
    assert error<.001 and angle<.001 and top,row
lines+=['','## Five high-risk parts: board pad nets and measured assembly transform','']
for ref in ['D2','U2','U4','U5','U6']:
    f=fps[ref]
    lines.append(f"- {ref}: {json.dumps(rot[ref])}; pads "+', '.join(p.GetNumber()+':'+p.GetNetname() for p in f.Pads() if p.GetNumber()))
(HERE/'TK1-rows.md').write_text('\n'.join(lines)+'\n')
print(f'{len(bom)} BOM rows and {len(cpl)} CPL rows match; independent arithmetic, shared rotation inputs.')
