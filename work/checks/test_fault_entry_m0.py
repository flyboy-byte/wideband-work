#!/usr/bin/env python3
"""F9: does a HardFault on a Cortex-M0 reach HardFault_Handler_C (and so its reset), or lock the core up?

  python3 checks/test_fault_entry_m0.py

Builds `fault_m0/harness.c` (a bare-metal program that executes UDF to force a HardFault and prints through semihosting
when the C handler runs) with the repo's `firmware/main_hardfault_asm.S`, and runs it on QEMU's `microbit` machine, a
Cortex-M0. This tests the fault entry's instruction set on an M0 core model only: not the STM32F042, not this firmware,
not hardware. Cases:
  current handler                        -> must reach the C handler
  upstream's handler (git master)        -> must lock up (shows the test can see the bug)
  current handler, then BKPT #0 in C     -> locks up with no debugger: why bkpt() is empty on the M0 (main.cpp)
Also checks the f0_module build (firmware/build/wideband.elf, if present) has no Thumb-2-only instructions in its fault
entries. Exit 1 on any unexpected result; 2 if QEMU or the ARM toolchain is missing.
"""
import shutil, subprocess, sys, tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from upstream_ref import upstream_ref

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ASM = REPO / 'firmware/main_hardfault_asm.S'
REACHED, LOCKUP = 'REACHED HardFault_Handler_C', 'Lockup'


def run(tmp, name, asm, cflags=()):
    elf = tmp / f'{name}.elf'
    subprocess.run(['arm-none-eabi-gcc', '-mcpu=cortex-m0', '-mthumb', '-O1', '-nostdlib', '-ffreestanding',
                    '-T', str(HERE / 'fault_m0/link.ld'), *cflags, str(HERE / 'fault_m0/harness.c'), str(asm), '-o', str(elf)],
                   check=True, capture_output=True)
    try:
        r = subprocess.run(['qemu-system-arm', '-M', 'microbit', '-nographic', '-semihosting-config', 'enable=on,target=native',
                            '-kernel', str(elf)], capture_output=True, text=True, timeout=20)
        out = r.stdout + r.stderr
    except subprocess.TimeoutExpired as e:
        out = (e.stdout or b'').decode() + ' (timed out)'
    # lockup wins: the BKPT case prints REACHED first, then locks up
    return 'lockup' if LOCKUP in out else 'reached' if REACHED in out else 'other: ' + out.strip()[-120:]


def main():
    for tool in ('qemu-system-arm', 'arm-none-eabi-gcc', 'arm-none-eabi-objdump'):
        if not shutil.which(tool):
            print(f'SKIPPED: {tool} not installed')
            return 2
    bad = 0
    with tempfile.TemporaryDirectory(prefix='wideband-m0fault-') as t:
        tmp = Path(t)
        old = tmp / 'upstream_hardfault_asm.S'
        old.write_text(subprocess.run(['git', '-C', str(REPO), 'show', upstream_ref() + ':firmware/main_hardfault_asm.S'],
                                      capture_output=True, text=True, check=True).stdout)
        for name, asm, flags, want in [('current handler', ASM, (), 'reached'),
                                       ("upstream's handler (master)", old, (), 'lockup'),
                                       ('current handler, then BKPT #0', ASM, ('-DDO_BKPT',), 'lockup')]:
            got = run(tmp, name.split()[0] + str(len(flags)) + str(asm == old), asm, flags)
            ok = got == want
            bad += not ok
            print(f'{"ok  " if ok else "WRONG"} {name}: {got} (expected {want})')
    elf = REPO / 'firmware/build/wideband.elf'
    if elf.exists():
        dis = subprocess.run(['arm-none-eabi-objdump', '-d', str(elf)], capture_output=True, text=True).stdout
        block, keep = [], False
        for line in dis.splitlines():
            if line.endswith('<HardFault_Handler>:') or line.endswith('<BusFault_Handler>:'):
                keep = True
            elif keep and line.endswith('>:') and 'Fault_Handler' not in line and 'MemManage_Handler' not in line:
                break
            if keep:
                block.append(line)
        thumb2 = [l for l in block if any(f'\t{m}' in l for m in ('it', 'ite', 'itt', 'tst.w', 'b.w', 'mrseq', 'mrsne'))]
        board = subprocess.run(['arm-none-eabi-readelf', '-A', str(elf)], capture_output=True, text=True).stdout
        if 'v6S-M' not in board and 'v6-M' not in board:
            print(f'SKIP build check: {elf.relative_to(REPO)} is not an ARMv6-M (f0_module) build')
        elif not block:
            print('WRONG f0 build: fault entry not found in the disassembly')
            bad += 1
        else:
            print(f'{"ok  " if not thumb2 else "WRONG"} f0 build fault entries: {len(block)} lines, '
                  f'{len(thumb2)} Thumb-2-only instructions' + ('' if not thumb2 else f': {thumb2[:3]}'))
            bad += bool(thumb2)
    else:
        print('SKIP build check: no firmware/build/wideband.elf')
    print(f'fault entry on Cortex-M0: {"as expected" if not bad else f"{bad} unexpected result(s)"}')
    return 1 if bad else 0


if __name__ == '__main__':
    raise SystemExit(main())
