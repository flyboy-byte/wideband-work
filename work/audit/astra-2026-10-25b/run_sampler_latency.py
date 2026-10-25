import os,subprocess,tempfile
from pathlib import Path
here=Path(__file__).resolve().parent
root=here.parents[2]; fw=root/'firmware'
with tempfile.TemporaryDirectory(prefix='wb-r7-latency-') as td:
    out=str(Path(td)/'latency')
    cmd=['g++','-std=c++20','-O1','-g','-include','initializer_list','-fsanitize=address,undefined','-fno-omit-frame-pointer','-DMOCK_TIMER','-DWB_PROD=0']
    for inc in ['boards/f0_module','boards/f0_module/io','boards','','util','libfirmware/util/include']:
        cmd+=['-I'+str(fw/inc)]
    cmd += [str(here/'sampler_latency.cpp')]+[str(fw/x) for x in ['sampling.cpp','heater_control.cpp','pid.cpp','util/timer.cpp']]+['-o',out]
    print('Compile:', ' '.join(cmd),flush=True)
    subprocess.run(cmd,check=True)
    subprocess.run([out],check=True,env=dict(os.environ,ASAN_OPTIONS='detect_stack_use_after_return=1'))
