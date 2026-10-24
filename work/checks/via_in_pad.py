#!/usr/bin/env python3
"""Vias whose drill overlaps an SMD pad, on vias upstream's carrier doesn't already have (solder wicks into them).

    python3 checks/via_in_pad.py      (from work/; needs KiCad's pcbnew Python module)

Upstream's own vias (git `master`) are reported as such and don't fail the check. Exit 0 when no new via is in a pad.
"""
import os, subprocess, sys, tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from upstream_ref import upstream_ref

import pcbnew

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
PCB = 'hardware/board_carrier/board_carrier.kicad_pcb'
T = pcbnew.ToMM


def vias(board):
    return [v for v in board.GetTracks() if v.Type() == pcbnew.PCB_VIA_T]


def main():
    with tempfile.TemporaryDirectory() as td:
        base = os.path.join(td, 'base.kicad_pcb')
        open(base, 'w').write(subprocess.run(['git', '-C', REPO, 'show', upstream_ref() + ':' + PCB], capture_output=True,
                                             text=True, check=True).stdout)
        subprocess.run(['kicad-cli', 'pcb', 'upgrade', base], capture_output=True, check=True)
        up = [(T(v.GetPosition().x), T(v.GetPosition().y)) for v in vias(pcbnew.LoadBoard(base))]
    board = pcbnew.LoadBoard(os.path.join(REPO, PCB))
    pads = [(f.GetReference(), p) for f in board.GetFootprints() for p in f.Pads()
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD and p.IsOnCopperLayer()]
    new, old = [], []
    for v in vias(board):
        x, y = T(v.GetPosition().x), T(v.GetPosition().y)
        for ref, p in pads:
            if p.HitTest(v.GetPosition(), v.GetDrillValue() // 2):
                is_up = any(abs(x - a) < 0.01 and abs(y - b) < 0.01 for a, b in up)
                (old if is_up else new).append(f'{ref}-{p.GetNumber()} {v.GetNetname()} @{x:.2f},{y:.2f}')
    print(f'via in pad: {len(new)} new, {len(old)} upstream' + (f' ({"; ".join(new)})' if new else ''))
    sys.exit(1 if new else 0)


if __name__ == '__main__':
    main()
