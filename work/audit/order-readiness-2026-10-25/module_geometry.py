"""Compare released KiCad-9 module geometry to fresh KiCad-10, without relying on plot order.
Requires gerbonara==1.6.3 in an isolated environment. No design/release writes.
"""
from collections import Counter
from itertools import groupby
from pathlib import Path
import subprocess,tempfile,zipfile
from gerbonara import GerberFile,ExcellonFile
from gerbonara.utils import MM
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
def primitives(f): return [p for o in f.objects for p in o.to_primitives(unit=MM)]
def ordered_polarity_batches(f):
    return [(pol,Counter(repr(p) for p in batch)) for pol,batch in groupby(primitives(f),lambda p:p.polarity_dark)]
def norm_drill(s):
    return '\n'.join(l for l in s.splitlines() if not any(t in l for t in ('; DRILL file','CreationDate','GenerationSoftware')))
mapping={'CuTop':'F_Cu.gtl','CuIn1':'In1_Cu.g1','CuIn2':'In2_Cu.g2','CuBottom':'B_Cu.gbl',
         'MaskTop':'F_Mask.gts','MaskBottom':'B_Mask.gbs','EdgeCuts':'Edge_Cuts.gm1',
         'SilkTop':'F_Silkscreen.gto','SilkBottom':'B_Silkscreen.gbo'}
with tempfile.TemporaryDirectory(prefix='wb-order-module-') as td:
    pcb=REPO/'hardware/board_module/wideband_controller.kicad_pcb'
    for args in [ ['gerbers','--layers','F.Cu,In1.Cu,In2.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,Edge.Cuts'],
                  ['drill','--format','excellon','--excellon-separate-th','--excellon-units','in'] ]:
        subprocess.run(['kicad-cli','pcb','export',*args,'-o',td+'/',str(pcb)],check=True,capture_output=True)
    with zipfile.ZipFile(REPO/'work/fab/flyboy-o2-v1/module-gerbers.zip') as z:
        for old,new in mapping.items():
            a=GerberFile.from_string(z.read('wideband_controller-'+old+'.gbr').decode())
            b=GerberFile.open(Path(td)/('wideband_controller-'+new))
            if old.startswith('Silk'):
                # Old plot includes explicit clear-polarity solder-mask subtraction polygons.
                da=Counter(repr(p) for p in primitives(a) if p.polarity_dark)
                db=Counter(repr(p) for p in primitives(b) if p.polarity_dark)
                assert da==db, old+' dark silk geometry differs'
                clear=sum(not p.polarity_dark for p in primitives(a))
                assert all(p.polarity_dark for p in primitives(b))
                print(old,'all dark silk primitives identical;',clear,'additional clear primitives in released plot; not claiming byte identity')
            else:
                assert ordered_polarity_batches(a)==ordered_polarity_batches(b),old
                print(old,len(primitives(a)),'primitives identical with polarity-batch ordering preserved')
                # Known-failure control: deleting any real primitive must fail the comparison.
                before=ordered_polarity_batches(b)
                b.objects.pop(0)
                assert ordered_polarity_batches(b)!=before
        for name in ('PTH','NPTH'):
            name='wideband_controller-'+name+'.drl'
            assert norm_drill(z.read(name).decode())==norm_drill((Path(td)/name).read_text()),name
            print(name,'all drill commands identical')
print('Module copper/mask/outline/drills + dark silkscreen geometry: PASS; 7 negative controls reject a removed object.')
