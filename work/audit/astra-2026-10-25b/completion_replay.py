#!/usr/bin/env python3
"""Replay actual prior ngspice aborts against the new helper, including diagnostic-free partial output."""
import pathlib,subprocess,re
here=pathlib.Path(__file__).resolve().parent;work=here.parents[1]
old=work/'audit/astra-2026-10-25'
for filename in ['TK6c-long-ic11.6.out','TK6c-long-ic0.out']:
    text=(old/filename).read_text()
    end=re.search(r'time = ([0-9.eE+-]+), timestep',text).group(1)
    for mode in ['actual-abort','partial-without-diagnostic']:
        sample=text if mode=='actual-abort' else 'RES 0 0 0 0 0\n'
        sample+='\nEND '+end+'\n'
        p=subprocess.run(['bash','-c','. "$1"; sample=$(cat); completed "$sample" 0.12','bash',str(work/'sim/completed.sh')],input=sample,capture_output=True,text=True)
        print(filename,mode,'helper exit',p.returncode);assert p.returncode!=0
for end,want in [('0.12',0),('0.119',1),('nan',1),('inf',1),('',1)]:
    p=subprocess.run(['bash','-c','. "$1"; completed "END $2" 0.12','bash',str(work/'sim/completed.sh'),end])
    print('END',repr(end),'exit',p.returncode);assert (p.returncode!=0)==bool(want)
