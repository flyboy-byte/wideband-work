#!/usr/bin/env python3
"""What-if routing: try candidate tracks on a scratch copy of the carrier and score each with drc_vs_upstream.

    python3 checks/whatif_route.py                    run every candidate in CANDIDATES, print one line each
    python3 checks/whatif_route.py NAME [--keep]      one candidate; --keep leaves the scratch board for a look

A candidate is (net, layer, width_mm, [(x, y), ...]) per segment chain, optionally with vias ('via', x, y). ~10 s each, so
a fix for one open connection can be tried and measured without the 4 min regeneration. A winner is then written into the
generator (gen_carrier_pcb.py) so it survives a regeneration; this script never touches the repo's board file.
Needs pcbnew and kicad-cli.
"""
import os, subprocess, sys, tempfile
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(HERE, '..', '..', 'hardware', 'board_carrier', 'board_carrier.kicad_pcb')
MM = 1_000_000

# name: list of (net, layer, width, points) chains; ('via', x, y) entries add a through via on the chain's net
CANDIDATES = {
    # The fix the generator applies (2026-10-23, run r32): D3's +5V via -> U2 pin 3 on the top, a GND via for C1 pin 2 that
    # the new track cuts off, and a solid pour connection for C2 pin 2 (thermal spokes starved). 0 new / 0 open.
    'FIX_D3': [('+5V', 'F.Cu', 0.25, [(60.10, 78.15), (64.35, 78.15), (64.35, 80.50), (64.90, 80.50)]),
               ('via', 'GND', 66.00, 79.35, 0.5, 0.3), ('GND', 'F.Cu', 0.20, [(66.00, 79.35), (65.31, 78.70)]),
               ('padsolid', 'C2', '2')],
    # D3's +5V fan-out via (60.10, 78.15) east on the top, then south onto upstream's +5V track end (63.29, 80.90)
    'top-east-y78.15': [('+5V', 'F.Cu', 0.25, [(60.10, 78.15), (64.00, 78.15), (64.00, 80.90)])],
    'east+gndvias': [('+5V', 'F.Cu', 0.25, [(60.10, 78.15), (64.00, 78.15), (64.00, 80.90)]),
                     ('via', 'GND', 65.40, 79.70, 0.6, 0.3), ('via', 'GND', 62.85, 78.95, 0.6, 0.3)],
    'east+gnd-c1': [('+5V', 'F.Cu', 0.25, [(60.10, 78.15), (64.00, 78.15), (64.00, 80.90)]),
                    ('via', 'GND', 65.40, 79.70, 0.6, 0.3)],
    'east-x63.8+gnd': [('+5V', 'F.Cu', 0.25, [(60.10, 78.15), (63.80, 78.15), (63.80, 80.90)]),
                       ('via', 'GND', 65.40, 79.70, 0.6, 0.3)],
    'y77.95+gnd-ties': [('+5V', 'F.Cu', 0.25, [(60.10, 78.15), (60.10, 77.95), (64.00, 77.95), (64.00, 80.90)]),
                        ('via', 'GND', 63.10, 78.50, 0.45, 0.2), ('GND', 'F.Cu', 0.25, [(63.10, 78.50), (63.10, 79.51)]),
                        ('via', 'GND', 65.31, 79.60, 0.5, 0.25), ('GND', 'F.Cu', 0.25, [(65.31, 79.60), (65.31, 78.70)])],
    'y77.95+gnd-c1only': [('+5V', 'F.Cu', 0.25, [(60.10, 78.15), (60.10, 77.95), (64.00, 77.95), (64.00, 80.90)]),
                          ('via', 'GND', 65.31, 79.60, 0.5, 0.25), ('GND', 'F.Cu', 0.25, [(65.31, 79.60), (65.31, 78.70)])],
    'to-u2pad3': [('+5V', 'F.Cu', 0.25, [(60.10, 78.15), (64.35, 78.15), (64.35, 80.50), (64.90, 80.50)])],
    'to-u2pad3-w0.2': [('+5V', 'F.Cu', 0.20, [(60.10, 78.15), (64.35, 78.15), (64.35, 80.50), (64.90, 80.50)])],
    'to-u2pad3-diag': [('+5V', 'F.Cu', 0.25, [(60.10, 78.15), (63.75, 78.15), (64.35, 78.75), (64.35, 80.50), (64.90, 80.50)])],
    # to U2 pin 3 + a GND via south-east of C1 pin 2 (found by a grid search: only C2 pin 2 thermal remains)
    'u2pad3+c1via': [('+5V', 'F.Cu', 0.25, [(60.10, 78.15), (64.35, 78.15), (64.35, 80.50), (64.90, 80.50)]),
                     ('via', 'GND', 66.00, 79.35, 0.5, 0.3), ('GND', 'F.Cu', 0.20, [(66.00, 79.35), (65.31, 78.70)])],
    'u2pad3+c1via+c2solid': [('+5V', 'F.Cu', 0.25, [(60.10, 78.15), (64.35, 78.15), (64.35, 80.50), (64.90, 80.50)]),
                             ('via', 'GND', 66.00, 79.35, 0.5, 0.3), ('GND', 'F.Cu', 0.20, [(66.00, 79.35), (65.31, 78.70)]),
                             ('padsolid', 'C2', '2')],
    'top-diag': [('+5V', 'F.Cu', 0.25, [(60.10, 78.15), (62.00, 78.15), (63.60, 79.75), (63.60, 80.90)])],
    'top-to-c2pad': [('+5V', 'F.Cu', 0.25, [(60.10, 78.15), (62.30, 78.15), (63.90, 79.75), (63.90, 81.09), (63.10, 81.09)])],
}


def build(chains, out):
    b = pcbnew.LoadBoard(PCB)
    apply(b, chains)
    pcbnew.SaveBoard(out, b)


def apply(b, chains):
    """Add the chains to board b in place and refill the pours (gen_carrier_pcb.py uses this for FIX_D3)."""
    for ch in chains:
        if ch[0] == 'via':                                  # ('via', net, x, y, dia, drill)
            _, net, x, y, dia, drill = ch
            v = pcbnew.PCB_VIA(b)
            v.SetPosition(pcbnew.VECTOR2I(int(x * MM), int(y * MM)))
            v.SetWidth(int(dia * MM)); v.SetDrill(int(drill * MM)); v.SetNet(b.FindNet(net))
            b.Add(v)
            continue
        if ch[0] == 'padsolid':                              # ('padsolid', ref, pad): solid pour connection, no thermal spokes
            for pad in b.FindFootprintByReference(ch[1]).Pads():
                if pad.GetNumber() == ch[2]:
                    pad.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
            continue
        net, layer, w, pts = ch
        n = b.FindNet(net)
        lay = b.GetLayerID(layer)
        for a, c in zip(pts, pts[1:]):
            t = pcbnew.PCB_TRACK(b)
            t.SetStart(pcbnew.VECTOR2I(int(a[0] * MM), int(a[1] * MM)))
            t.SetEnd(pcbnew.VECTOR2I(int(c[0] * MM), int(c[1] * MM)))
            t.SetWidth(int(w * MM)); t.SetLayer(lay); t.SetNet(n)
            b.Add(t)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())


def score(path):
    r = subprocess.run([sys.executable, os.path.join(HERE, 'drc_vs_upstream.py'), '-v', '--pcb', path],
                       capture_output=True, text=True)
    return r.stdout.strip().splitlines()


def main():
    names = [a for a in sys.argv[1:] if not a.startswith('--')] or list(CANDIDATES)
    for name in names:
        out = os.path.join(tempfile.gettempdir(), f'whatif-{name}.kicad_pcb') if '--keep' in sys.argv else tempfile.mktemp(suffix='.kicad_pcb')
        build(CANDIDATES[name], out)
        lines = score(out)
        print(f'{name:22s} {lines[0] if lines else "no output"}')
        for l in lines[1:]:
            print('     ', l)
        if '--keep' in sys.argv:
            print('      kept', out)
        elif os.path.exists(out):
            os.remove(out)


if __name__ == '__main__':
    main()
