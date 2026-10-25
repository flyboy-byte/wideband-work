#!/usr/bin/env python3
"""Counterexample: an actual indirect recursive call must not receive a finite PASS."""
import importlib.util,pathlib,subprocess,tempfile,sys
HERE=pathlib.Path(__file__).resolve().parent
WORK=HERE.parents[1]
spec=importlib.util.spec_from_file_location('regression',WORK/'checks/test_stack_estimate.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
s=m.program('push {r4,lr}\nbl deep_helper\npop {r4,pc}',100)
s=s.replace('sub sp, #100\nadd sp, #100\nbx lr','push {r4,lr}\nsub sp, #100\nldr r3, =deep_helper\nblx r3\nadd sp, #100\npop {r4,pc}')+'\n.ltorg\n'
src=HERE/'TK12-indirect-cycle.S';src.write_text(s)
b=pathlib.Path(tempfile.mkdtemp(prefix='wb_r6_cycle_'));elf=b/'cycle.elf'
subprocess.run(['arm-none-eabi-gcc','-mcpu=cortex-m0','-mthumb','-nostdlib','-Wl,-Ttext=0x08002000','-Wl,-e,main',str(src),'-o',str(elf)],check=True)
p=subprocess.run([sys.executable,str(WORK/'checks/stack_estimate.py'),str(elf)],capture_output=True,text=True,timeout=10)
print(p.stdout+p.stderr)
print('CHECKER_EXIT',p.returncode)
assert p.returncode==0,'Counterexample no longer passes: inspect whether checker fixed'
print('REPRODUCED: actual unbounded indirect recursion was accepted with a finite stack bound.')
