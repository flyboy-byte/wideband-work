import subprocess
import tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
with tempfile.TemporaryDirectory(prefix='wb-heater-review-') as tmp:
    binary=Path(tmp)/'heater'
    cmd=['g++','-std=c++20','-DMOCK_TIMER','-DWB_PROD=0',
         '-I'+str(ROOT/'firmware/boards/f0_module'),'-I'+str(ROOT/'test'),
         '-I'+str(ROOT/'firmware'),'-I'+str(ROOT/'firmware/util'),
         str(HERE/'heater_negative_voltage.cpp'),str(ROOT/'firmware/heater_control.cpp'),
         str(ROOT/'firmware/pid.cpp'),str(ROOT/'firmware/util/timer.cpp'),'-o',str(binary)]
    subprocess.run(cmd,check=True)
    p=subprocess.run([str(binary)],capture_output=True,text=True,check=True)
    (HERE/'heater-negative-voltage.txt').write_text('Production f0 configuration; mock time and sampler only.\n'+p.stdout)
    print(p.stdout)
