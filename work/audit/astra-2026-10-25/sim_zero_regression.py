#!/usr/bin/env python3
import pathlib,subprocess,tempfile,shutil,os
from spice_validation import reached_window
HERE=pathlib.Path(__file__).resolve().parent;WORK=HERE.parents[1]
# Reclassify the actual real-model outputs. No simulator rerun is needed for this assertion.
for name,stop,want in [('long-ic11.6',.120,False),('long-ic0',.120,False),('zero-0',.015,True),('zero-five',.015,True)]:
    text=(HERE/('TK6c-'+name+'.out')).read_text();valid=reached_window(text,stop)
    print('REAL LOG',name,'complete',valid);assert valid==want
with tempfile.TemporaryDirectory(prefix='wb_r6_simzero_') as t:
    root=pathlib.Path(t);(root/'models').mkdir();(root/'models/lmx58_lm2904.lib').touch()
    shutil.copy(WORK/'sim/full_scale_corners.sh',root/'full_scale_corners.sh')
    (root/'bin').mkdir();shutil.copy(HERE/'ngspice-zero-fixture.sh',root/'bin/ngspice');(root/'bin/ngspice').chmod(0o700)
    p=subprocess.run(['bash',str(root/'full_scale_corners.sh')],env=dict(os.environ,PATH=str(root/'bin')+os.pathsep+os.environ['PATH']),capture_output=True,text=True,timeout=30)
    (HERE/'TK99-wrapper-zero.out').write_text(p.stdout+p.stderr)
    print('PRODUCTION WRAPPER EXIT',p.returncode,'(expected nonzero for abort)')
    print(p.stdout.splitlines()[0])
    assert p.returncode==0,'False-pass counterexample no longer reproduces; inspect fix'
    assert p.stdout.count('connector 0.0000')==27
    print('REPRODUCED: all27aborted zero-result fixtures accepted.')
