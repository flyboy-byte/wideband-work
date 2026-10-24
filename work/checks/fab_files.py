#!/usr/bin/env python3
"""Check the fab candidate in work/out/carrier/ (gen/export_fab.py) against the board, independently of the exporter:

  - the Gerber zip has every layer and both drill files, and its Edge_Cuts outline measures the board's size;
  - the Gerbers are from the current board (the copper Gerber is regenerated and compared, ignoring the date line);
  - every BOM designator has one CPL row and the reverse; BOM LCSC numbers equal the footprints' LCSC fields;
  - every CPL row is the footprint's position (Y negated) plus its measured shift, at its KiCad rotation plus the
    measured correction (checks/jlc_rotation.json), on the top;
  - nothing in not-fitted.csv is in the BOM, and every footprint is in exactly one of them.

  python3 checks/fab_files.py
Exit 1 on any mismatch. SKIPPED (exit 77) when there is no candidate yet.
"""
import csv, io, json, math, os, re, subprocess, sys, tempfile, zipfile

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.abspath(os.path.join(HERE, '..'))
REPO = os.path.abspath(os.path.join(WORK, '..'))
PCB = os.path.join(REPO, 'hardware/board_carrier/board_carrier.kicad_pcb')
OUT = os.path.join(WORK, 'out', 'carrier')
NEED = ['F_Cu.gtl', 'B_Cu.gbl', 'F_Mask.gts', 'B_Mask.gbs', 'F_Paste.gtp', 'F_Silkscreen.gto', 'B_Silkscreen.gbo',
        'Edge_Cuts.gm1', 'PTH.drl', 'NPTH.drl']

sys.path.insert(0, HERE)
from gerber_outline import outline


def main():
    if not os.path.isdir(OUT):
        print('no fab candidate (run gen/export_fab.py)')
        return 77
    bad = []
    T = pcbnew.ToMM
    board = pcbnew.LoadBoard(PCB)
    fps = {f.GetReference(): f for f in board.GetFootprints()}
    rot = json.load(open(os.path.join(HERE, 'jlc_rotation.json')))

    z = zipfile.ZipFile(os.path.join(OUT, 'carrier-gerbers.zip'))
    names = z.namelist()
    for n in NEED:
        if not any(x.endswith(n) for x in names):
            bad.append(f'gerber zip: no *{n}')
    edge = [x for x in names if x.endswith('Edge_Cuts.gm1')]
    if edge:
        pts = [p for sg in outline(z.read(edge[0]).decode()) for p in sg]
        w, h = max(p[0] for p in pts) - min(p[0] for p in pts), max(p[1] for p in pts) - min(p[1] for p in pts)
        e = board.GetBoardEdgesBoundingBox()
        bw, bh = T(e.GetWidth()), T(e.GetHeight())
        if abs(w - bw) > 0.2 or abs(h - bh) > 0.2:
            bad.append(f'outline {w:.2f} x {h:.2f} mm in the Gerber vs {bw:.2f} x {bh:.2f} on the board')
        outline_txt = f'{w:.2f} x {h:.2f} mm'
    # The copper Gerber is the current board's
    with tempfile.TemporaryDirectory() as td:
        subprocess.run(['kicad-cli', 'pcb', 'export', 'gerbers', '--layers', 'F.Cu', '-o', td + '/', PCB], capture_output=True)
        fresh = [f for f in os.listdir(td) if f.endswith('.gtl')]
        strip = lambda s: '\n'.join(l for l in s.splitlines() if 'CreationDate' not in l and 'GenerationSoftware' not in l and not l.startswith('G04 Created by'))
        cu = [x for x in names if x.endswith('F_Cu.gtl')]
        if not fresh or not cu or strip(open(os.path.join(td, fresh[0])).read()) != strip(z.read(cu[0]).decode()):
            bad.append('F_Cu Gerber differs from the current board: re-run gen/export_fab.py')

    bom = list(csv.DictReader(open(os.path.join(OUT, 'carrier-bom.csv'))))
    cpl = {r['Designator']: r for r in csv.DictReader(open(os.path.join(OUT, 'carrier-cpl.csv')))}
    nf = {r['Designator'] for r in csv.DictReader(open(os.path.join(OUT, 'not-fitted.csv')))}
    bom_refs = {}
    for r in bom:
        for d in r['Designator'].split(','):
            if d in bom_refs:
                bad.append(f'{d}: twice in the BOM')
            bom_refs[d] = r['LCSC Part #']
    for d, lcsc in bom_refs.items():
        f = fps.get(d)
        if not f:
            bad.append(f'{d}: in the BOM, not on the board'); continue
        field = f.GetFieldText('LCSC') if f.HasField('LCSC') else ''
        if field != lcsc:
            bad.append(f'{d}: BOM {lcsc}, footprint field {field!r}')
        if d not in cpl:
            bad.append(f'{d}: in the BOM, no CPL row')
    for d, r in cpl.items():
        f = fps.get(d)
        if d not in bom_refs:
            bad.append(f'{d}: CPL row, not in the BOM')
        if not f or d not in rot:
            bad.append(f'{d}: CPL row with no footprint or no rotation entry'); continue
        sx, sy = rot[d]['pos_shift_mm']
        ex, ey = T(f.GetPosition().x) + sx, -(T(f.GetPosition().y) + sy)
        if abs(float(r['Mid X']) - ex) > 0.005 or abs(float(r['Mid Y']) - ey) > 0.005:
            bad.append(f'{d}: CPL at {r["Mid X"]},{r["Mid Y"]}, expected {ex:.4f},{ey:.4f}')
        er = (f.GetOrientationDegrees() + rot[d]['correction']) % 360
        if (float(r['Rotation']) - er) % 360:
            bad.append(f'{d}: CPL rotation {r["Rotation"]}, expected {er:.0f}')
        if r['Layer'] != 'Top' or f.GetLayer() != pcbnew.F_Cu:
            bad.append(f'{d}: not on the top')
    for d in nf & set(bom_refs):
        bad.append(f'{d}: both in the BOM and not fitted')
    for d in fps:
        if d not in bom_refs and d not in nf:
            bad.append(f'{d}: neither in the BOM nor in not-fitted.csv')
    for b in bad:
        print('FAIL', b)
    print(f'fab files: {len(bom_refs)} placed, {len(nf)} not fitted, outline {outline_txt if edge else "?"}, '
          f'{len(bad)} problem(s)')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
