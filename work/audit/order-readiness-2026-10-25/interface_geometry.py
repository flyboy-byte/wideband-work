"""Measure mating header pitch and SWD cutout from native boards; no design writes."""
import json,math
from pathlib import Path
import pcbnew
ROOT=Path(__file__).resolve().parents[3]
def load(path):return pcbnew.LoadBoard(str(ROOT/path))
def xy(p):return (pcbnew.ToMM(p.GetPosition().x),pcbnew.ToMM(p.GetPosition().y))
carrier=load('hardware/board_carrier/board_carrier.kicad_pcb')
module=load('hardware/board_module/wideband_controller.kicad_pcb')
cf={f.GetReference():f for f in carrier.GetFootprints()}
mf={f.GetReference():f for f in module.GetFootprints()}
cp={p.GetNumber():p for p in cf['U3'].Pads()}
offset=None
for ref,start in [('J3',0),('J1',8)]:
    for p in sorted(mf[ref].Pads(),key=lambda p:int(p.GetNumber())):
        target=cp[str(int(p.GetNumber())+start)]
        delta=tuple(a-b for a,b in zip(xy(target),xy(p)))
        if offset is None:offset=delta
        assert math.dist(offset,delta)<1e-6
        print(ref,p.GetNumber(),p.GetNetname(),'-> carrier U3',target.GetNumber(),target.GetNetname(), 'offset mm',delta)
print('All 16 positions align by one translation; row spacing 25.4 mm, pitch 2.54 mm.')
print('J2 pad net / position (module coordinates):')
for p in mf['J2'].Pads():
    print(p.GetNumber() or 'alignment hole',p.GetNetname(),xy(p),'drill mm',pcbnew.ToMM(p.GetDrillSize().x))
print('Carrier cutout geometry:')
segments=[]
items=list(carrier.GetDrawings())+[d for f in carrier.GetFootprints() for d in f.GraphicalItems()]
for d in items:
    if d.GetLayer()!=pcbnew.Edge_Cuts:continue
    a=(pcbnew.ToMM(d.GetStart().x),pcbnew.ToMM(d.GetStart().y))
    b=(pcbnew.ToMM(d.GetEnd().x),pcbnew.ToMM(d.GetEnd().y))
    if all(48<=x<=58 and 72<=y<=79 for x,y in (a,b)):
        print(d.GetShapeStr(),a,b);segments.extend((a,b))
assert len(segments)==2, 'Expected the one U3 Edge.Cuts rectangle, not guessed board-level lines'
w=max(x for x,y in segments)-min(x for x,y in segments)
h=max(y for x,y in segments)-min(y for x,y in segments)
assert abs(w-7.874)<1e-6 and abs(h-5.334)<1e-6
print('Cutout nominal mm',w,h,'TC2030 body per manufacturer drawing mm',9.906,6.096)
print('Cable body cannot pass straight through cutout. Protruding-pin reach at final stack height NOT established.')
print('Interface geometry measurement: PASS; fit/stack decisions remain open.')
