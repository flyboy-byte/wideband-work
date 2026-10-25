#!/usr/bin/env python3
"""Live JLC assembly stock, library class and part price for every line of the carrier BOM, for N boards.

  python3 checks/bom_stock.py [N] [BOM.csv]   default N = 5, the carrier BOM; writes out/bom-stock[-NAME].json (live data,
                                              not committed). Reads JLC-style BOMs: 'LCSC Part #' or 'LCSC', 'Designator'

Asks the JSON endpoint behind jlcpcb.com/parts (the idea comes from the pcb-design skill author's v2, 2026-10-24), one
part a second: stockCount is JLC's own assembly stock, which is not LCSC's warehouse (C7934 read 112 at LCSC and 219,277
at JLC on the same day). componentLibraryType 'base' = Basic (no loading fee); 'expand' = Extended (a loading fee per
distinct part per order) unless preferredComponentFlag says Preferred (no fee). Need = qty per board x N + attrition
(lossNumber when JLC gives one, else 2 for passives). Unofficial endpoint (REPORTED: it answered a plain POST with no key,
2026-10-24); the quote page is still the final word. Exit 1 if a line is missing or short.
"""
import csv, json, os, subprocess, sys, time

WORK = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
BOM = os.path.join(WORK, 'out', 'carrier', 'carrier-bom.csv')
URL = 'https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList'


def lookup(lcsc):
    body = json.dumps({'keyword': lcsc, 'currentPage': 1, 'pageSize': 5})
    r = subprocess.run(['curl', '-sf', '-m', '20', '-X', 'POST', URL, '-H', 'Content-Type: application/json', '-d', body],
                       capture_output=True, text=True)
    if r.returncode:
        return None
    for c in json.loads(r.stdout).get('data', {}).get('componentPageInfo', {}).get('list') or []:
        if c.get('componentCode') == lcsc:
            return c
    return None


def price_at(c, qty):
    for p in c.get('componentPrices') or []:
        if p['startNumber'] <= qty and (p.get('endNumber') in (None, -1) or qty <= p['endNumber']):
            return p['productPrice']
    return (c.get('componentPrices') or [{'productPrice': None}])[-1]['productPrice']


def main():
    n = int(next((a for a in sys.argv[1:] if a.isdigit()), 5))
    bom = next((a for a in sys.argv[1:] if a.endswith('.csv')), BOM)
    tag = '' if bom == BOM else '-' + os.path.splitext(os.path.basename(bom))[0]
    if not os.path.exists(bom):
        print('no BOM: run gen/export_fab.py first')
        return 77
    rows, bad, parts_cost, fees = [], 0, 0.0, []
    for line in csv.DictReader(open(bom)):
        lcsc, refs = line.get('LCSC Part #') or line.get('LCSC', ''), line['Designator'].split(',')
        if not lcsc:
            print(f'     {",".join(refs):14} no LCSC number (not assembled)')
            continue
        c = lookup(lcsc)
        time.sleep(1)
        if not c:
            print(f'FAIL {lcsc:9} {",".join(refs):14} not found at JLC')
            bad += 1
            continue
        kind = 'Basic' if c['componentLibraryType'] == 'base' else ('Preferred' if c.get('preferredComponentFlag') else 'Extended')
        need = len(refs) * n + (c.get('lossNumber') or (2 if refs[0][0] in 'RC' else 0))
        unit = price_at(c, need)
        cost = unit * need if unit is not None else 0
        parts_cost += cost
        if kind == 'Extended':
            fees.append(lcsc)
        short = c['stockCount'] < need
        bad += short
        rows.append({'lcsc': lcsc, 'refs': refs, 'model': c.get('componentModelEn'), 'class': kind,
                     'stock': c['stockCount'], 'need': need, 'unit_usd': unit, 'cost_usd': round(cost, 4)})
        print(f"{'FAIL' if short else 'ok  '} {lcsc:9} {','.join(refs):14} {c.get('componentModelEn', '')[:22]:22} "
              f"{kind:9} stock {c['stockCount']:>9}  need {need:>3}  ${cost:6.2f}")
    os.makedirs(os.path.join(WORK, 'out'), exist_ok=True)
    json.dump({'boards': n, 'date': time.strftime('%Y-%m-%d'), 'lines': rows, 'parts_usd': round(parts_cost, 2),
               'extended': fees}, open(os.path.join(WORK, 'out', f'bom-stock{tag}.json'), 'w'), indent=1)
    print(f'bom stock for {n} boards: {len(rows)} lines found, {bad} problem(s); parts about ${parts_cost:.2f}; '
          f'{len(fees)} Extended (loading fee each): {", ".join(fees)}')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
