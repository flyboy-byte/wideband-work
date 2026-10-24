#!/usr/bin/env python3
"""Carrier DRC against upstream's own baseline: only violations our changes added, plus every unconnected item.

    python3 checks/drc_vs_upstream.py            (from work/)
    python3 checks/drc_vs_upstream.py -v         also list each new violation and unconnected pair
    python3 checks/drc_vs_upstream.py --pcb FILE score another board file (what-if copies) instead of the repo's

Upstream's carrier (git `master`, upgraded to KiCad 10) already has courtyard and edge errors of its own; this
subtracts them by (type, sorted item descriptions). Exit 0 only when there are no new violations and nothing is
unconnected. Needs kicad-cli.

Errors of every type count, and so do the warning types in FAB_WARNINGS: things a fab or the board itself cares about
that KiCad's default severities rate as warnings. Added 2026-10-24 after r26-r37 all carried two +5V vias drilled
0.225 mm apart (hole_to_hole, a warning), hidden behind "0 new".
"""
import json, os, subprocess, sys, tempfile

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
PCB = 'hardware/board_carrier/board_carrier.kicad_pcb'
FAB_WARNINGS = {'hole_to_hole', 'hole_clearance', 'drill_out_of_range', 'annular_width', 'via_diameter', 'track_width',
                'copper_sliver', 'track_dangling', 'via_dangling', 'isolated_copper', 'solder_mask_bridge', 'clearance',
                'copper_edge_clearance', 'shorting_items', 'unconnected_items', 'npth_inside_courtyard', 'pth_inside_courtyard'}


def drc(path, parity, out):
    cmd = ['kicad-cli', 'pcb', 'drc', '--severity-all', '--format', 'json', '-o', out, path]
    if parity:
        cmd.insert(3, '--schematic-parity')
    subprocess.run(cmd, capture_output=True, check=True)
    d = json.load(open(out))
    d['violations'] = [v for v in d['violations'] if v.get('severity') == 'error' or v['type'] in FAB_WARNINGS]
    return d


def key(v):
    return (v['type'], tuple(sorted(i['description'] for i in v['items'])))


def main():
    with tempfile.TemporaryDirectory() as td:
        base = os.path.join(td, 'base.kicad_pcb')
        open(base, 'w').write(subprocess.run(['git', '-C', REPO, 'show', 'master:' + PCB], capture_output=True,
                                             text=True, check=True).stdout)
        subprocess.run(['kicad-cli', 'pcb', 'upgrade', base], capture_output=True, check=True)
        b = [key(v) for v in drc(base, False, os.path.join(td, 'base.json'))['violations']]
        target = sys.argv[sys.argv.index('--pcb') + 1] if '--pcb' in sys.argv else os.path.join(REPO, PCB)
        cur = drc(target, True, os.path.join(td, 'cur.json'))
    new = []
    for v in cur['violations']:
        k = key(v)
        if k in b:
            b.remove(k)
        else:
            new.append(k)
    un = cur.get('unconnected_items', [])
    print(f'DRC vs upstream: {len(new)} new violations, {len(un)} unconnected')
    if '-v' in sys.argv:
        for k in new:
            print('  new:', k[0], '|', ' / '.join(k[1]))
        for u in un:
            print('  open:', ' / '.join(f"{i['description']} @{i['pos']['x']:.2f},{i['pos']['y']:.2f}" for i in u['items']))
    sys.exit(0 if not new and not un else 1)


if __name__ == '__main__':
    main()
