"""Independent R9 delta and exact exported row checks, no design changes."""
import csv,hashlib,json,subprocess,shutil
from pathlib import Path
import pcbnew
here=Path(__file__).resolve().parent
root=here.parents[2]
work=root/'work'
board='hardware/board_carrier/board_carrier.kicad_pcb'
old=subprocess.check_output(['git','show','43cc114:'+board],cwd=root)
new=(root/board).read_bytes()
assert old.count(b'(property "LCSC" "C4410"')==1
assert new==old.replace(b'(property "LCSC" "C4410"',b'(property "LCSC" "C844867"')
b=pcbnew.LoadBoard(str(root/board)); f=b.FindFootprintByReference('R9')
bom=list(csv.DictReader((work/'out/carrier/carrier-bom.csv').open()))
cpl=list(csv.DictReader((work/'out/carrier/carrier-cpl.csv').open()))
br=next(r for r in bom if 'R9' in r['Designator'].split(','))
cr=next(r for r in cpl if r['Designator']=='R9')
assert br['LCSC Part #']==f.GetFieldText('LCSC')=='C844867'
assert '1206' in br['Footprint']
info=dict(board_lcsc=f.GetFieldText('LCSC'),position_mm=[pcbnew.ToMM(f.GetPosition().x),pcbnew.ToMM(f.GetPosition().y)],rotation=f.GetOrientationDegrees(),footprint=f.GetFPID().GetLibItemName().wx_str(),bom=br,cpl=cr,only_board_delta='C4410 -> C844867',candidate_hashes={})
for name in ['carrier-bom.csv','carrier-cpl.csv','not-fitted.csv','carrier-gerbers.zip']:
    p=work/'out/carrier'/name
    info['candidate_hashes'][name]=hashlib.sha256(p.read_bytes()).hexdigest()
    if name.endswith('.csv'): shutil.copyfile(p,here/('TK5-'+name))
shutil.copyfile(work/'out/bom-stock.json',here/'TK5-bom-stock.json')
print(json.dumps(info,indent=2))
