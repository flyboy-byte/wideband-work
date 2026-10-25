#!/usr/bin/env python3
"""The 0-5 V output is low from reset until the app drives PB1 (outside review B1, 2026-10-24).

Before the app hands PB1 to TIM3, the bootloader (about 0.8 s, longer with no valid app or during a CAN update) and the
app's early init leave PB1 an input with the pull set in each board.h. R3 on the carrier pulls the same node to GND, and
U4 (74LVC1G125 on 3.0 V) buffers it. With 100k and the MCU pull-up on, PB1 sat at 2.1-2.6 V, a logic high: full scale
(5.04 V, 20 AFR) at every key-on. This reads R3's value from the board and the PB1 pull from both board.h files, and
checks the worst-case PB1 voltage against the buffer's V_IL.

  python3 checks/boot_level.py      exit 1 if the buffer could read PB1 as high (or undefined) during boot

Numbers, FROM MEMORY (re-check against the datasheets): STM32F042 pull-up/down 25-55 k (typ 40 k); 74LVC1G125
V_IL max 0.8 V at VCC 2.7-3.6 V; VDD 3.3 V (+-0.1 V margin used: 3.4 V).
"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
PCB = os.path.join(REPO, 'hardware/board_carrier/board_carrier.kicad_pcb')
BOARD_H = ['firmware/boards/f0_module/board.h', 'firmware/boards/f0_module/bootloader/cfg/board.h']
VDD, R_PULL, V_IL = 3.4, (25e3, 55e3), 0.8


def ohms(v):
    m = re.fullmatch(r'([\d.]+)\s*([kKmM]?)', v.replace('Ω', '').strip())
    return float(m.group(1)) * {'': 1, 'k': 1e3, 'K': 1e3, 'm': 1e6, 'M': 1e6}[m.group(2)]


def worst_high(r3, pull):
    """Highest PB1 voltage with R3 to GND and the MCU pull given (UP / DOWN / FLOATING)."""
    if pull == 'PULLUP':
        return VDD * r3 / (r3 + R_PULL[0])
    return 0.0   # pull-down or floating: R3 alone holds it at GND


def main():
    s = open(PCB).read()
    m = re.search(r'\(property "Reference" "R3".*?\(property "Value" "([^"]+)"', s, re.S)
    if not m:
        print('R3 not found on the board'); return 1
    r3 = ohms(m.group(1))
    bad = 0
    for p in BOARD_H:
        pull = re.search(r'PIN_PUPDR_(\w+)\(GPIOB_PIN1\)', open(os.path.join(REPO, p)).read()).group(1)
        v = worst_high(r3, pull)
        ok = v < V_IL
        bad += not ok
        print(f"{'ok  ' if ok else 'FAIL'} {p}: PB1 {pull.lower()}, R3 {m.group(1)}: PB1 at most {v:.2f} V "
              f"(buffer V_IL {V_IL} V)")
    # The configuration B1 found must fail here, or this check can't see the bug
    if worst_high(100e3, 'PULLUP') < V_IL:
        print('FAIL self-test: 100k with the pull-up passes, the check is blind'); bad += 1
    print(f'boot level: {"output low from reset" if not bad else f"{bad} problem(s)"}')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
