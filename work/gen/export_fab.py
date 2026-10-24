#!/usr/bin/env python3
"""Fab files for JLCPCB from the carrier board, into work/out/carrier/ (gitignored). Only checks/release.py copies them
into fab/<rev>/; nothing here orders anything.

  python3 work/gen/export_fab.py

Refuses to write unless the board passes checks/drc_vs_upstream.py and checks/jlc_rotation.py (pcb-design skill: the
export step runs its own checks on the exact board). Writes:
  carrier-gerbers.zip   copper, mask, paste, silkscreen, outline, drill (PTH and NPTH)
  carrier-bom.csv       Comment, Designator, Footprint, LCSC Part #   (JLC's column names)
  carrier-cpl.csv       Designator, Mid X, Mid Y, Layer, Rotation      (Y up, rotation and position corrected for
                        each part's EasyEDA footprint from checks/jlc_rotation.json)
  not-fitted.csv        every footprint JLC does not place, and why
  README.md             what was checked, at which commit
Upstream's own hardware/board_carrier/export/ files are stale (BOM 2023-01-05: SMCJ30CA and SS34 where the board and
schematic of 2023-02-03 have SMCJ24CA and SS54; positions from before the 2023-02-03 re-placement), so nothing comes from them.
"""
import csv, datetime, json, os, shutil, subprocess, sys, tempfile, zipfile

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.abspath(os.path.join(HERE, '..'))
REPO = os.path.abspath(os.path.join(WORK, '..'))
PCB = os.path.join(REPO, 'hardware/board_carrier/board_carrier.kicad_pcb')
OUT = os.path.join(WORK, 'out', 'carrier')
# Footprints JLC doesn't place, with the reason (REQUIREMENTS: JLC places SMD, the owner hand-solders through-hole)
NOT_FITTED = {
    'J3': 'through-hole connector (mx120g-12): owner hand-solders',
    'U3': 'the wideband module: a separate board, soldered on by the owner',
    'JP1': 'solder jumper TEST: left open, owner bridges it for bench test A1 (no paste on its pads)',
    'JP2': 'solder jumper 120R: left open, owner bridges it on a bus with no other terminator (no paste on its pads)',
    'H1': 'M3 mounting hole (NPTH), no part',
    'H2': 'M3 mounting hole (NPTH), no part',
}
LAYERS = 'F.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts'


def sh(*cmd, cwd=WORK):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()


def main():
    why = []
    for check in (['python3', 'checks/drc_vs_upstream.py'], ['python3', 'checks/jlc_rotation.py']):
        rc, out = sh(*check)
        last = [l for l in out.splitlines() if l and 'Debug' not in l][-1:]
        print(f'{"ok  " if rc == 0 else "FAIL"} {" ".join(check[1:])}: {last[0] if last else ""}')
        if rc:
            why.append(check[1])
    if why:
        sys.exit(f'refused: {", ".join(why)} failed; no files written')

    T = pcbnew.ToMM
    board = pcbnew.LoadBoard(PCB)
    rot = json.load(open(os.path.join(WORK, 'checks/jlc_rotation.json')))
    fps = {f.GetReference(): f for f in board.GetFootprints()}
    problems = []
    for ref, f in fps.items():
        if ref not in rot and ref not in NOT_FITTED:
            problems.append(f'{ref}: neither placed (no LCSC/rotation entry) nor in NOT_FITTED')
        if ref in rot and ref in NOT_FITTED:
            problems.append(f'{ref}: both placed and not fitted')
        if ref in NOT_FITTED and any(p.IsOnLayer(pcbnew.F_Paste) for p in f.Pads()):
            problems.append(f'{ref}: not fitted but has solder paste')
    for ref in NOT_FITTED:
        if ref not in fps:
            problems.append(f'{ref}: in NOT_FITTED but not on the board')
    if problems:
        sys.exit('refused:\n  ' + '\n  '.join(problems))

    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    with tempfile.TemporaryDirectory() as td:
        g = os.path.join(td, 'gerbers')
        os.makedirs(g)
        rc, out = sh('kicad-cli', 'pcb', 'export', 'gerbers', '--layers', LAYERS, '-o', g + '/', PCB)
        if rc:
            sys.exit('gerber export failed: ' + out[-300:])
        rc, out = sh('kicad-cli', 'pcb', 'export', 'drill', '--format', 'excellon', '--excellon-separate-th',
                     '--excellon-units', 'mm', '-o', g + '/', PCB)
        if rc:
            sys.exit('drill export failed: ' + out[-300:])
        names = sorted(os.listdir(g))
        with zipfile.ZipFile(os.path.join(OUT, 'carrier-gerbers.zip'), 'w', zipfile.ZIP_DEFLATED) as z:
            for n in names:
                z.write(os.path.join(g, n), n)
    print(f'gerbers: {len(names)} files ({", ".join(names)})')

    # BOM, grouped by LCSC number
    groups = {}
    for ref, r in rot.items():
        f = fps[ref]
        key = r['lcsc']
        groups.setdefault(key, {'value': f.GetValue(), 'fp': f.GetFPID().GetLibItemName().wx_str(), 'refs': []})['refs'].append(ref)
    def refkey(r):
        return (r.rstrip('0123456789'), int(r[len(r.rstrip('0123456789')):] or 0))
    with open(os.path.join(OUT, 'carrier-bom.csv'), 'w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['Comment', 'Designator', 'Footprint', 'LCSC Part #'])
        for lcsc, gr in sorted(groups.items(), key=lambda kv: refkey(sorted(kv[1]['refs'], key=refkey)[0])):
            w.writerow([gr['value'], ','.join(sorted(gr['refs'], key=refkey)), gr['fp'], lcsc])

    # CPL: KiCad's coordinates with Y negated (JLC's Y points up), moved and turned for the EasyEDA footprint
    with open(os.path.join(OUT, 'carrier-cpl.csv'), 'w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['Designator', 'Mid X', 'Mid Y', 'Layer', 'Rotation'])
        for ref in sorted(rot, key=refkey):
            f, r = fps[ref], rot[ref]
            if f.GetLayer() != pcbnew.F_Cu:
                sys.exit(f'{ref} is not on the top: this export assumes one-sided assembly (D9)')
            x, y = T(f.GetPosition().x) + r['pos_shift_mm'][0], T(f.GetPosition().y) + r['pos_shift_mm'][1]
            w.writerow([ref, f'{x:.4f}', f'{-y:.4f}', 'Top', f'{r["cpl_rot"] % 360:.0f}'])

    with open(os.path.join(OUT, 'not-fitted.csv'), 'w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['Designator', 'Reason'])
        for ref, why_nf in NOT_FITTED.items():
            w.writerow([ref, why_nf])

    rc, head = sh('git', 'rev-parse', '--short', 'HEAD')
    rc2, dirty = sh('git', 'status', '--porcelain', '--untracked-files=no')
    corr = {k: v for k, v in rot.items() if v['correction'] or any(v['pos_shift_mm'])}
    open(os.path.join(OUT, 'README.md'), 'w').write(
        f"# Carrier fab files (candidate, not released)\n\nExported {datetime.date.today().isoformat()} from commit {head}"
        f"{' with uncommitted changes' if dirty else ''} by `work/gen/export_fab.py`. Checked first: "
        "`checks/drc_vs_upstream.py` (0 new errors or fab-relevant warnings, 0 unconnected) and `checks/jlc_rotation.py` "
        "(every part's EasyEDA footprint measured).\n\n"
        f"- {sum(len(g['refs']) for g in groups.values())} placed parts, {len(groups)} BOM lines, all on the top "
        "(Economic assembly).\n"
        "- CPL rotation and position corrections from the EasyEDA footprints: "
        + ', '.join(f"{k} {v['correction']} deg" + (f" shift {v['pos_shift_mm']} mm" if any(v['pos_shift_mm']) else '')
                    for k, v in sorted(corr.items())) + ".\n"
        "- Check every IC and diode in JLC's placement preview before paying (rotation sense is INFERRED); D2 (SS54) is "
        "the one where EasyEDA numbers the pads the other way round.\n"
        "- Not fitted: see `not-fitted.csv`.\n")
    print(f'wrote {os.path.relpath(OUT, REPO)}: carrier-gerbers.zip, carrier-bom.csv ({len(groups)} lines), '
          f'carrier-cpl.csv ({len(rot)} parts), not-fitted.csv ({len(NOT_FITTED)}), README.md')


if __name__ == '__main__':
    main()
