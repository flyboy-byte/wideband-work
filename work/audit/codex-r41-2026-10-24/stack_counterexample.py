"""Counterexample to F8's conservative-bound claim; never flashed.

A real ARMv6-M ELF calls a 400-byte helper through a .text literal, not
through a .rodata pointer table. No production firmware is modified.
"""
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[1]
assembly = '''.syntax unified
.cpu cortex-m0
.thumb
.section .text
.global _Z12HeaterThreadPv
.type _Z12HeaterThreadPv,%function
.thumb_func
_Z12HeaterThreadPv:
push {r4,lr}
ldr r3, =deep_helper
blx r3
pop {r4,pc}
.size _Z12HeaterThreadPv, .-_Z12HeaterThreadPv
.ltorg
.global deep_helper
.type deep_helper,%function
.thumb_func
deep_helper:
sub sp, #400
add sp, #400
bx lr
.size deep_helper, .-deep_helper
'''
for name in ['_Z10PumpThreadPv','_Z14SamplingThreadPv','_Z11CanTxThreadPv','_Z11CanRxThreadPv','main']:
    assembly += f'.global {name}\n.type {name},%function\n.thumb_func\n{name}:\nbx lr\n.size {name}, .-{name}\n'
assembly += '''.global __main_thread_stack_base__, __main_thread_stack_end__, __main_stack_base__, __main_stack_end__
.set __main_thread_stack_base__,0x20000000
.set __main_thread_stack_end__,0x20000200
.set __main_stack_base__,0x20000200
.set __main_stack_end__,0x20000400
'''
with tempfile.TemporaryDirectory(prefix='wideband-stack-review-') as tmp:
    source, elf = Path(tmp)/'case.S', Path(tmp)/'case.elf'
    source.write_text(assembly)
    subprocess.run(['arm-none-eabi-gcc','-mcpu=cortex-m0','-mthumb','-nostdlib','-Wl,-Ttext=0x08002000','-Wl,-e,main',str(source),'-o',str(elf)],check=True)
    disasm = subprocess.run(['arm-none-eabi-objdump','-d','-C',str(elf)],capture_output=True,text=True,check=True).stdout
    p = subprocess.run(['python3',str(WORK/'checks/stack_estimate.py'),str(elf)],capture_output=True,text=True)
    report = f'Actual nested frame: 8 + 400 = 408 bytes on configured 256-byte heater stack.\nChecker exit: {p.returncode}\n{p.stdout}{p.stderr}\n{disasm}'
    (HERE/'stack-counterexample.txt').write_text(report)
    print(report)
    if p.returncode != 0:
        raise SystemExit('Counterexample no longer silently passes: inspect output.')
