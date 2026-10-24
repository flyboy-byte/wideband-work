#!/usr/bin/env python3
"""F8 (docs/flashing-and-test-plan.md), before hardware: worst-case stack depth of each thread, from the built ELF.

  python3 checks/stack_estimate.py [ELF] [-v]      default firmware/build/wideband.elf (build f0_module first)

Static estimate, not a measurement. From the disassembly: each function's frame is its pushes plus `sub sp, #n`; edges are
direct calls (`bl`) and tail branches into another function. An indirect call (`blx rN`: virtual calls, function
pointers) is charged the deepest function whose address appears in flash data (vtables, pointer tables), so the result
can only overestimate there. Recursion is reported, not followed. ChibiOS reserves the exception frame and interrupt
headroom outside the n of THD_WORKING_AREA(wa, n) (PORT_WA_SIZE), so each thread's depth is compared with n.
Exit 1 if any thread's estimate exceeds its stack, or the analysis meets something it can't bound.
"""
import re, subprocess, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ELF = Path(next((a for a in sys.argv[1:] if not a.startswith('-')), REPO / 'firmware/build/wideband.elf'))
VERBOSE = '-v' in sys.argv

# Thread entry -> stack n bytes (THD_WORKING_AREA in the named source)
THREADS = {'HeaterThread': (256, 'heater_thread.cpp'), 'PumpThread': (256, 'pump_control.cpp'),
           'SamplingThread': (256, 'sampling_thread.cpp'), 'CanTxThread': (512, 'can.cpp'),
           'CanRxThread': (512, 'can.cpp'), 'IndicationThread': (128, 'indication.cpp')}
OPTIONAL = {'IndicationThread'}   # not built for f0_module


def run(*cmd):
    return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout


def main():
    # Thread stack sizes, re-read from the sources so this can't go stale silently
    problems = []
    for name, (n, src) in THREADS.items():
        text = (REPO / 'firmware' / src).read_text()
        if not re.search(r'THD_WORKING_AREA\(\w+,\s*%d\)' % n, text):
            problems.append(f'{src}: no THD_WORKING_AREA(..., {n}) any more for {name}: update THREADS')

    if not ELF.exists():
        print(f'no {ELF}: build the bootloader, then the app (REVIEW.md, Setup)')
        return 1
    syms = {}
    other = {}
    for line in run('arm-none-eabi-nm', '-C', '-S', '--defined-only', str(ELF)).splitlines():
        p = line.split(maxsplit=3)
        if len(p) == 4 and p[2] in 'TtWw':
            syms[int(p[0], 16)] = (p[3], int(p[1], 16))
    for line in run('arm-none-eabi-nm', '-C', '--defined-only', str(ELF)).splitlines():
        p = line.split(maxsplit=2)
        if len(p) == 3:
            other[p[2]] = int(p[0], 16)
            if p[1] in 'TtWw':
                syms.setdefault(int(p[0], 16), (p[2], 0))   # labels without a size (asm, weak aliases)
    starts = {a & ~1: n for a, (n, _) in syms.items()}

    frame, calls, indirect = {}, {}, {}
    cur = None
    for line in run('arm-none-eabi-objdump', '-d', '-C', '--no-show-raw-insn', str(ELF)).splitlines():
        m = re.match(r'^([0-9a-f]+) <(.+)>:$', line)
        if m:
            cur = m.group(2)
            frame.setdefault(cur, 0)
            calls.setdefault(cur, set())
            indirect.setdefault(cur, 0)
            continue
        if cur is None or ':\t' not in line:
            continue
        ins = line.split(':\t', 1)[1].strip()
        if m := re.match(r'push\s+\{([^}]*)\}', ins):
            frame[cur] += 4 * len(m.group(1).split(','))
        elif m := re.match(r'sub\s+sp,\s*(?:sp,\s*)?#(\d+)', ins):
            frame[cur] += int(m.group(1))
        elif m := re.match(r'bl\s+([0-9a-f]+) <', ins):
            calls[cur].add(starts.get(int(m.group(1), 16), f'?{m.group(1)}'))
        elif m := re.match(r'b(?:\.n|\.w)?\s+([0-9a-f]+) <', ins):
            t = starts.get(int(m.group(1), 16))
            if t and t != cur:
                calls[cur].add(t)              # tail call into another function
        elif re.match(r'blx\s+r\d+', ins):
            indirect[cur] += 1

    # Functions whose address is stored in flash data: the possible targets of an indirect call
    words = set()
    for sec in ('.rodata', '.data'):
        try:
            dump = run('arm-none-eabi-objdump', '-s', '-j', sec, str(ELF))
        except subprocess.CalledProcessError:
            continue
        for line in dump.splitlines():
            m = re.match(r'^ ([0-9a-f]+) ((?:[0-9a-f]{8} ?){1,4})', line)
            if m:
                for w in m.group(2).split():
                    words.add(int.from_bytes(bytes.fromhex(w), 'little'))
    targets = {starts[w & ~1] for w in words if w & 1 and (w & ~1) in starts} - set(THREADS) - {'main'}

    memo, stack, kinds = {}, [], []
    recursion, cut = set(), set()

    def depth(f, kind='direct'):
        if f in memo:
            return memo[f]
        if f in stack:
            i = stack.index(f)
            loop = ' -> '.join(stack[i:] + [f])
            # A loop through an indirect hop comes from charging every address-taken function to every indirect call;
            # only a loop of direct calls is real recursion
            (cut if 'indirect' in kinds[i + 1:] + [kind] else recursion).add(loop)
            return (0, None)
        stack.append(f)
        kinds.append(kind)
        sub = [(depth(c)[0], c) for c in calls.get(f, ())]
        if indirect.get(f):
            sub += [(depth(t, 'indirect')[0], f'*{t}') for t in targets]
        stack.pop()
        kinds.pop()
        best = max(sub, default=(0, None))
        memo[f] = (frame.get(f, 0) + best[0], best[1])
        return memo[f]

    def path(f):
        out = []
        while f:
            name = f.lstrip('*')
            out.append(f'{f}({frame.get(name, 0)})')
            f = memo.get(name, (0, None))[1]
        return ' > '.join(out)

    print(f'{ELF.relative_to(REPO) if ELF.is_relative_to(REPO) else ELF}: {len(frame)} functions, '
          f'{len(targets)} indirect-call targets (address in flash data)')
    worst_margin = None
    entries = {}
    for name, (n, src) in THREADS.items():
        fn = next((f for f in frame if f.startswith(name + '(')), None)
        entries[name] = (fn, n)
    # main() runs on the main thread stack; interrupts on the exception (MSP) stack: sizes from the linker symbols
    entries['main'] = ('main', other.get('__main_thread_stack_end__', 0) - other.get('__main_thread_stack_base__', 0))
    vec = run('arm-none-eabi-objdump', '-s', '--start-address=0x08001800', '--stop-address=0x080018c0', str(ELF))
    handlers = set()
    for line in vec.splitlines():
        m = re.match(r'^ ([0-9a-f]+) ((?:[0-9a-f]{8} ?){1,4})', line)
        if m:
            for w in m.group(2).split()[(1 if m.group(1) == '8001800' else 0):]:
                a = int.from_bytes(bytes.fromhex(w), 'little')
                if a & 1 and (a & ~1) in starts and 'Reset' not in starts[a & ~1]:
                    handlers.add(starts[a & ~1])
    msp = other.get('__main_stack_end__', 0) - other.get('__main_stack_base__', 0)
    if 'v6S-M' not in run('arm-none-eabi-readelf', '-A', str(ELF)):
        problems.append(f'{ELF.name} is not an ARMv6-M (f0_module) build: make BOARD=f0_module first')
    for name, (fn, n) in entries.items():
        if fn is None:
            print(f'  {name:16s} not in this build')
            if name not in OPTIONAL:
                problems.append(f'{name} not found: nothing was checked for it')
            continue
        d, _ = depth(fn)
        name = fn
        margin = n - d
        worst_margin = margin if worst_margin is None else min(worst_margin, margin)
        flag = 'OVER' if margin < 0 else 'ok  '
        print(f'  {flag} {name:16s} {d:4d} of {n} B ({margin:+d})')
        if VERBOSE or margin < 0:
            print(f'       {path(name)}')
        if margin < 0:
            problems.append(f'{name}: estimated {d} B on a {n} B stack')
    isr = max(((depth(h)[0], h) for h in handlers), default=(0, None))
    print(f'  {"ok  " if isr[0] <= msp else "OVER"} {"interrupts (one)":16s} {isr[0]:4d} of {msp} B exception stack '
          f'({msp - isr[0]:+d}), deepest handler {isr[1]}; nesting of interrupts not modelled')
    if VERBOSE and isr[1]:
        print(f'       {path(isr[1])}')
    if isr[0] > msp:
        problems.append(f'interrupt handler {isr[1]}: {isr[0]} B on a {msp} B exception stack')
    unresolved = sorted({c for cs in calls.values() for c in cs if c.startswith('?')})
    if unresolved:
        problems.append(f'calls to addresses with no symbol: {unresolved[:5]}')
    if cut:
        print(f'  note: {len(cut)} loop(s) through indirect calls cut (an artefact of the over-approximation, -v lists them)')
        if VERBOSE:
            for c in sorted(cut):
                print(f'       {c}')
    for r in sorted(recursion):
        problems.append(f'recursion, not bounded: {r}')
    for p in problems:
        print('FAIL', p)
    print(f'stack estimate: {"ok" if not problems else f"{len(problems)} problem(s)"}'
          + (f', smallest margin {worst_margin} B' if worst_margin is not None else ''))
    return 1 if problems else 0


if __name__ == '__main__':
    raise SystemExit(main())
