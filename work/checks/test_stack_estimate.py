#!/usr/bin/env python3
"""stack_estimate.py on small Cortex-M0 ELFs with known answers (from Codex's counterexample, R41-CX1, 2026-10-24):

  - HeaterThread calls a 400-byte helper through a pointer in a .text literal pool -> must report OVER (408 of 256 B)
  - the same with a 100-byte helper                                                -> must pass (108 of 256 B)
  - HeaterThread calls through a register no stored address explains               -> must fail as not bounded

  python3 checks/test_stack_estimate.py     needs arm-none-eabi-gcc; exit 1 on any wrong verdict"""
import subprocess, sys, tempfile
from pathlib import Path

CHECK = Path(__file__).resolve().parent / 'stack_estimate.py'
THREAD = '.global {n}\n.type {n},%function\n.thumb_func\n{n}:\n{body}\n.size {n}, .-{n}\n'
STACKS = '''.global __main_thread_stack_base__, __main_thread_stack_end__, __main_stack_base__, __main_stack_end__
.set __main_thread_stack_base__,0x20000000
.set __main_thread_stack_end__,0x20000200
.set __main_stack_base__,0x20000200
.set __main_stack_end__,0x20000400
'''


def program(heater_body, helper_bytes):
    s = '.syntax unified\n.cpu cortex-m0\n.thumb\n.section .text\n'
    s += THREAD.format(n='_Z12HeaterThreadPv', body=heater_body) + '.ltorg\n'
    s += THREAD.format(n='deep_helper', body=f'sub sp, #{helper_bytes}\nadd sp, #{helper_bytes}\nbx lr')
    for n in ['_Z10PumpThreadPv', '_Z14SamplingThreadPv', '_Z11CanTxThreadPv', '_Z11CanRxThreadPv', 'main']:
        s += THREAD.format(n=n, body='bx lr')
    return s + STACKS


CASES = [  # name, heater body, helper size, expected exit, text that must appear
    ('pointer in a literal pool, 400 B helper', 'push {r4,lr}\nldr r3, =deep_helper\nblx r3\npop {r4,pc}', 400, 1,
     'HeaterThread(void*)  408 of 256'),
    ('pointer in a literal pool, 100 B helper', 'push {r4,lr}\nldr r3, =deep_helper\nblx r3\npop {r4,pc}', 100, 0,
     'HeaterThread(void*)  108 of 256'),
    ('indirect call, no stored address', 'push {r4,lr}\nmovs r3, #1\nblx r3\npop {r4,pc}', 100, 1, 'not bounded'),
]


def main():
    bad = 0
    with tempfile.TemporaryDirectory(prefix='wb-stack-') as t:
        for i, (name, body, size, want, text) in enumerate(CASES):
            src, elf = Path(t) / f'c{i}.S', Path(t) / f'c{i}.elf'
            src.write_text(program(body, size))
            subprocess.run(['arm-none-eabi-gcc', '-mcpu=cortex-m0', '-mthumb', '-nostdlib', '-Wl,-Ttext=0x08002000',
                            '-Wl,-e,main', str(src), '-o', str(elf)], check=True, capture_output=True)
            p = subprocess.run([sys.executable, str(CHECK), str(elf)], capture_output=True, text=True)
            ok = p.returncode == want and text in p.stdout
            bad += not ok
            print(f"{'ok  ' if ok else 'FAIL'} {name:42} exit {p.returncode} (want {want})"
                  + ('' if ok else f', expected "{text}" in:\n{p.stdout}{p.stderr}'))
    print(f'stack checker cases: {len(CASES)}, {bad} wrong verdict(s)')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
