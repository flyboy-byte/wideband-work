#!/usr/bin/env python3
"""Plain-text views of a board for a reviewer who can't open KiCad (a chat model reading uploaded files).

  python3 checks/pack_extras.py BOARD.kicad_pcb OUT_PREFIX     writes OUT_PREFIX-parts.txt and OUT_PREFIX-nets.txt

parts: one line per footprint: ref, value, footprint, side, x/y (mm, KiCad top view, y down), rotation, DNP.
nets:  one line per net: the pads on it as REF.PAD(pin function).
Both are read from the .kicad_pcb (pcbnew), so they are the layout's view, not the schematic's. LCSC part numbers are
in the order BOM, not here.
"""
import sys

import pcbnew

T = pcbnew.ToMM


def main(pcb, prefix):
    b = pcbnew.LoadBoard(pcb)
    fps = sorted(b.GetFootprints(), key=lambda f: (f.GetReference()[0], len(f.GetReference()), f.GetReference()))
    rows = ['# ref | value | footprint | side | x mm | y mm | rot deg | DNP',
            f'# from {pcb}; KiCad top-view coordinates, y grows downward; rotation counter-clockwise seen from the top']
    for f in fps:
        p = f.GetPosition()
        rows.append(' | '.join([f.GetReference(), f.GetValue(), f.GetFPIDAsString().split(':')[-1],
                                'bottom' if f.IsFlipped() else 'top', f'{T(p.x):.3f}', f'{T(p.y):.3f}',
                                f'{f.GetOrientationDegrees():.1f}', 'DNP' if f.IsDNP() else '']))
    open(prefix + '-parts.txt', 'w').write('\n'.join(rows) + '\n')
    nets = {}
    for f in fps:
        for p in f.Pads():
            n = p.GetNetname()
            if n:
                fn = p.GetPinFunction()
                nets.setdefault(n, []).append(f'{f.GetReference()}.{p.GetNumber()}' + (f'({fn})' if fn and fn != p.GetNumber() else ''))
    out = [f'# net: pads (REF.PAD(pin function)); from {pcb}']
    out += [f'{n}: ' + ' '.join(sorted(set(v))) for n, v in sorted(nets.items())]
    open(prefix + '-nets.txt', 'w').write('\n'.join(out) + '\n')
    print(f'{prefix}-parts.txt ({len(fps)} parts), {prefix}-nets.txt ({len(nets)} nets)')


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
