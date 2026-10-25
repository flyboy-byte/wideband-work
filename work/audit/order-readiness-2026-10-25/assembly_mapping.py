"""Check frozen BOM/CPL/not-fitted coverage against both native boards."""
import csv, json, math
from pathlib import Path
import pcbnew
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
WORK=REPO/'work'
FAB=WORK/'fab/flyboy-o2-v1'
def rows(p):
    with p.open(encoding='utf-8-sig',newline='') as f: return list(csv.DictReader(f))
for kind,boardname in [('carrier','board_carrier'),('module','wideband_controller')]:
    board=pcbnew.LoadBoard(str(REPO/f'hardware/board_{kind}/{boardname}.kicad_pcb'))
    fps={f.GetReference():f for f in board.GetFootprints()}
    rot=json.loads((WORK/f'checks/jlc_rotation{"_module" if kind=="module" else ""}.json').read_text())
    bom=rows(FAB/f'{kind}-bom.csv'); cpl=rows(FAB/f'{kind}-cpl.csv'); nf=rows(FAB/f'{kind}-not-fitted.csv')
    fitted={}
    for row in bom:
        refs=row['Designator'].split(',')
        if 'Quantity' in row: assert int(row['Quantity'])==len(refs),row
        for ref in refs:
            assert ref not in fitted,ref
            fitted[ref]=row
            fp=fps[ref]
            expected=fp.GetFieldText('LCSC')
            if kind=='module' and ref in {'R10','C3'}:
                expected={'R10':'C2087389','C3':'C106862'}[ref]
            assert (row.get('LCSC Part #') or row['LCSC'])==expected,(ref,row,expected)
            assert row['Comment']==fp.GetValue(),(ref,row['Comment'],fp.GetValue())
            assert row['Footprint']==str(fp.GetFPID().GetLibItemName()),(ref,row['Footprint'])
    cr=[r['Designator'] for r in cpl]; nr=[r['Designator'] for r in nf]
    assert len(cr)==len(set(cr)) and len(nr)==len(set(nr))
    assert set(cr)==set(fitted)
    assert not set(cr)&set(nr)
    assert set(cr)|set(nr)==set(fps)
    for row in cpl:
        ref=row['Designator'];fp=fps[ref]; r=rot[ref]
        x,y=pcbnew.ToMM(fp.GetPosition().x),pcbnew.ToMM(fp.GetPosition().y)
        dx,dy=r['pos_shift_mm']
        ex,ey=x+dx,-y-dy
        assert math.hypot(float(row['Mid X'])-ex,float(row['Mid Y'])-ey)<0.005,(kind,ref,'position')
        er=(fp.GetOrientationDegrees()+r['correction'])%360
        assert abs((float(row['Rotation'])-er+180)%360-180)<0.001,(kind,ref,'angle')
        assert row['Layer'].lower()=='top' and fp.GetLayer()==pcbnew.F_Cu,(kind,ref,'side')
    print(kind,':',len(bom),'BOM rows,',len(cr),'CPL rows,',len(nr),'not fitted: all identities/values/packages/positions/rotations/sides agree')
    for ref in nr:
        pasted=[p.GetNumber() for p in fps[ref].Pads() if p.IsOnLayer(pcbnew.F_Paste) or p.IsOnLayer(pcbnew.B_Paste)]
        print('NOT FITTED',kind,ref,'paste pads:',pasted)
        assert not pasted,(kind,ref,'unfitted paste')
    print('PCB thickness mm',pcbnew.ToMM(board.GetDesignSettings().GetBoardThickness()))
    edge=board.GetBoardEdgesBoundingBox()
    print('PCB outline bbox mm',pcbnew.ToMM(edge.GetWidth()),pcbnew.ToMM(edge.GetHeight()))
print('Frozen assembly mapping: PASS (rotation convention still requires factory preview).')
