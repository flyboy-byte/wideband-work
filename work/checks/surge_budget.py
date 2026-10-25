#!/usr/bin/env python3
"""Load dump on the op-amp supply: power in R9 and D5 while the input TVS D1 clamps (Codex round 6, R6-S3, 2026-10-25).

  python3 checks/surge_budget.py [--self-test]      run from work/

D1 (SMCJ24CA) holds the protected 12 V rail at up to 38.9 V, its clamping voltage at rated pulse current, for the
length of a load dump (about 400 ms). R9 (1k) feeds D5 (18 V zener, BZT52C18 17.1-18.9 V) from that rail. The parts
must carry this power within their continuous rating: a pulse curve for 400 ms isn't published for the general-purpose
parts, and 400 ms is long enough to treat as steady. Ratings by LCSC number are from JLC's listings (REPORTED); the
part numbers are read from the board, so a BOM swap is checked. Temperature derating is not modelled.
"""
import os, sys

import pcbnew

BOARD = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'hardware/board_carrier/board_carrier.kicad_pcb')
V_CLAMP = 38.9                 # SMCJ24CA V_C at I_PP (docs/carrier.md, DOCUMENTED from the datasheet listing)
VZ = (17.1, 18.9)              # BZT52C18 zener voltage range (C173425 listing)
R9 = 1000.0
RATED_W = {                    # LCSC -> continuous power rating, W (JLC listing)
    'C4410': 0.25,             # UNI-ROYAL 1206W4F1001T5E, general purpose (up to 2026-10-24)
    'C844867': 0.75,           # Vishay CRCW12061K00FKEAHP, pulse-proof HP series (from 2026-10-25)
    'C173425': 0.5,            # BZT52C18, SOD-123
}


def problems(lcsc_r9, lcsc_d5):
    out, rows = [], []
    p_r9 = (V_CLAMP - VZ[0]) ** 2 / R9           # lowest zener voltage: most voltage across R9
    p_d5 = VZ[1] * (V_CLAMP - VZ[1]) / R9        # highest zener voltage: V x I worst for the zener
    for ref, lcsc, p in (('R9', lcsc_r9, p_r9), ('D5', lcsc_d5, p_d5)):
        rated = RATED_W.get(lcsc)
        if rated is None:
            out.append(f'{ref}: {lcsc} has no rating in surge_budget.py: add it from the part\'s datasheet')
            continue
        rows.append(f'  {ref} {lcsc}: {p:.3f} W at {V_CLAMP} V clamp, rated {rated} W ({p / rated:.0%})')
        if p > rated:
            out.append(f'{ref} {lcsc}: {p:.3f} W during a clamped load dump, over its {rated} W rating')
    return out, rows


def main():
    if '--self-test' in sys.argv:
        bad = problems('C4410', 'C173425')[0]       # the general-purpose R9 of r41 must fail
        good = problems('C844867', 'C173425')[0]
        ok = bool(bad) and not good
        print(f'surge budget self-test: {"ok" if ok else "WRONG"} (C4410 fails: {bool(bad)}, C844867 passes: {not good})')
        return 0 if ok else 1
    b = pcbnew.LoadBoard(BOARD)
    lcsc = {r: b.FindFootprintByReference(r).GetFieldText('LCSC') for r in ('R9', 'D5')}
    out, rows = problems(lcsc['R9'], lcsc['D5'])
    print('\n'.join(rows))
    for p in out:
        print('FAIL', p)
    print(f'surge budget: {len(out)} problem(s)')
    return 1 if out else 0


if __name__ == '__main__':
    sys.exit(main())
