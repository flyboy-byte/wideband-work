#!/usr/bin/env python3
"""Stage the module board's JLC files in work/out/module/: upstream's rev C exports with order-day part substitutions.

  python3 gen/module_fab.py

The module board files stay exactly upstream's (checks/module_vs_upstream.py); only the BOM line's LCSC number changes,
for a part JLC can't supply. Each swap keeps the value and package and says why. Found with checks/bom_stock.py on
2026-10-24 (JLC stock). Re-run bom_stock.py on order day and add to SUBS if anything else ran out.
"""
import csv, os, shutil

WORK = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
SRC = os.path.join(WORK, '..', 'hardware', 'board_module', 'export', 'rev C')
OUT = os.path.join(WORK, 'out', 'module')

# designator: (upstream LCSC, substitute LCSC, why)
SUBS = {
    'R10': ('C23092', 'C2087389', '61.9R 0603: upstream UNI-ROYAL 1 % had 3 in stock at JLC (2026-10-24); Panasonic '
            'ERA-3AEB61R9V, same value and package, 0.1 % 25 ppm thin film (the LSU pump-current shunt value)'),
    'C3': ('C1585', 'C106862', '33n 0402: upstream Y5V part out of stock at JLC (2026-10-24); Yageo CC0402KRX7R9BB333, '
           '33n 50 V X7R 10 %, same package, a more stable dielectric'),
}

# Not assembled by JLC: through-hole on the bottom, the owner solders them (they join the module to the carrier)
NOT_FITTED = {'J1': '1x8 2.54 mm header, through-hole, bottom: owner solders', 'J3': '1x8 2.54 mm header, through-hole, '
              'bottom: owner solders', 'J2': 'Tag-Connect TC2030 pads, no part'}


def main():
    os.makedirs(OUT, exist_ok=True)
    rows = list(csv.DictReader(open(os.path.join(SRC, 'BOM-wideband_controller.csv'))))
    done = set()
    for r in rows:
        refs = r['Designator'].split(',')
        for d, (old, new, why) in SUBS.items():
            if d in refs:
                if r['LCSC'] != old:
                    raise SystemExit(f'{d}: upstream BOM has {r["LCSC"]}, expected {old}: re-check the substitution')
                if len(refs) != 1:
                    raise SystemExit(f'{d} shares a BOM line with {refs}: split it before substituting')
                r['LCSC'] = new
                done.add(d)
    rows = [r for r in rows if not set(r['Designator'].split(',')) & set(NOT_FITTED)]
    if done != set(SUBS):
        raise SystemExit(f'not found in the BOM: {sorted(set(SUBS) - done)}')
    with open(os.path.join(OUT, 'module-bom.csv'), 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    cpl = list(csv.DictReader(open(os.path.join(SRC, 'CPL-wideband_controller.csv'))))
    key = next(k for k in cpl[0] if 'Designator' in k)
    with open(os.path.join(OUT, 'module-cpl.csv'), 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(cpl[0].keys()))
        w.writeheader()
        w.writerows(r for r in cpl if r[key] not in NOT_FITTED)
    with open(os.path.join(OUT, 'not-fitted.csv'), 'w', newline='') as f:
        f.write('Designator,Reason\n' + ''.join(f'{d},"{why}"\n' for d, why in NOT_FITTED.items()))
    shutil.copy(os.path.join(SRC, 'GERBER-wideband_controller.zip'), os.path.join(OUT, 'module-gerbers.zip'))
    with open(os.path.join(OUT, 'README.md'), 'w') as f:
        f.write('# Module fab files (upstream rev C, 2026-03-22, with order-day substitutions)\n\n'
                'Gerbers are upstream\'s rev C exports, unchanged; the CPL is theirs without J1/J3. BOM changes:\n\n')
        for d, (old, new, why) in SUBS.items():
            f.write(f'- {d}: {old} -> {new}. {why}\n')
        f.write('\n4 layers, 29.0 x 20.9 mm, 57 SMD parts all on the top; J1/J3 (1x8 headers) and J2 (Tag-Connect pads) '
                'on the bottom, not assembled (not-fitted.csv). Not yet checked with our rotation check: read the JLC placement preview part by part, '
                'starting with U2 (STM32F042, LQFP-32) pin 1, Q1, U1, U3, U5 and the LEDs.\n')
    print(f'wrote {os.path.relpath(OUT, WORK)}: module-gerbers.zip, module-bom.csv ({len(rows)} lines, '
          f'{len(SUBS)} substituted), module-cpl.csv, not-fitted.csv, README.md')


if __name__ == '__main__':
    main()
