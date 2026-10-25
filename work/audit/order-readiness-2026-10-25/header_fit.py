"""Known-issue test: named 0.64 mm square header against the actual released plated holes."""
import math,re,zipfile
from pathlib import Path
import pcbnew
ROOT=Path(__file__).resolve().parents[3]
b=pcbnew.LoadBoard(str(ROOT/'hardware/board_carrier/board_carrier.kicad_pcb'))
f=next(f for f in b.GetFootprints() if f.GetReference()=='U3')
with zipfile.ZipFile(ROOT/'work/fab/flyboy-o2-v1/carrier-gerbers.zip') as z:
    drill=z.read('board_carrier-PTH.drl').decode()
assert 'METRIC' in drill
tools={m[1]:float(m[2]) for m in re.finditer(r'^T(\d+)C([\d.]+)',drill,re.M)}
hits={};tool=None
for line in drill.splitlines():
    t=re.fullmatch(r'T(\d+)',line)
    if t:tool=t[1]
    m=re.fullmatch(r'X(-?[\d.]+)Y(-?[\d.]+)',line)
    if m:hits[(float(m[1]),float(m[2]))]=tools[tool]
hole=[]
for p in f.Pads():
    xy=(round(pcbnew.ToMM(p.GetPosition().x),4),round(-pcbnew.ToMM(p.GetPosition().y),4))
    d=hits[xy];hole.append(d)
    assert abs(d-pcbnew.ToMM(p.GetDrillSize().x))<1e-6
    print('U3',p.GetNumber(),p.GetNetname(),'released PTH mm',d,'xy',xy)
# Manufacturer drawing: Hanxia HX PZ2.54-1x8P ZZ, 2022/04/24, SQ 0.64; recommended PCB diameter 1.02.
diag=0.64*math.sqrt(2)
print('Named header nominal pin diagonal mm',diag,'max square side fitting nominal hole',min(hole)/math.sqrt(2))
print('Nominal interference mm',diag-min(hole))
assert all(diag>d for d in hole)
print('CONFIRMED BUG: C32713274 nominal square pins do not fit any of the 16 released carrier module holes.')
print('Do not drill out plated holes as an assumed repair. Select/verify compatible tails or propose a new PCB release.')
