#!/usr/bin/env python3
"""Draw the module's SWD pads (J2, Tag-Connect TC2030) as seen from below, from the board files.

  python3 gen/swd_diagram.py      writes renders/module/swd-pads.svg and .png

Two panels, both seen from below (so left and right are mirrored against KiCad's top view):
  1. the module on its own, upside down, before it is soldered to the carrier: all pads exposed;
  2. the carrier from below, with the module fitted: J2 through the carrier's cutout.
Geometry comes from hardware/board_module and hardware/board_carrier (pcbnew); the module sits on the carrier where
module J3 pin 1 meets carrier U3 pad 1. Pad signals are the module netlist's.
"""
import os, subprocess

import pcbnew

WORK = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
REPO = os.path.join(WORK, '..')
OUT = os.path.join(WORK, 'renders', 'module')
T = pcbnew.ToMM
SIG = {'+3V3': '3.3 V (target sense)', '/SWDIO': 'SWDIO', '/nRESET': 'nRESET', '/SWCLK': 'SWCLK', 'GND': 'GND'}
HDR = {}   # (header, pin) -> the carrier net that pin lands on, filled in main() from the carrier's U3 pads


def module_geometry():
    m = pcbnew.LoadBoard(os.path.join(REPO, 'hardware/board_module/wideband_controller.kicad_pcb'))
    e = m.GetBoardEdgesBoundingBox()
    box = (T(e.GetX()), T(e.GetY()), T(e.GetRight()), T(e.GetBottom()))
    j2 = m.FindFootprintByReference('J2')
    pads = [(p.GetNumber(), p.GetNetname(), T(p.GetPosition().x), T(p.GetPosition().y), T(p.GetSize(pcbnew.B_Cu).x))
            for p in j2.Pads()]
    hdr = {}
    for r in ('J1', 'J3'):
        f = m.FindFootprintByReference(r)
        hdr[r] = sorted((int(p.GetNumber()), T(p.GetPosition().x), T(p.GetPosition().y)) for p in f.Pads())
    return box, pads, hdr


def carrier_geometry():
    c = pcbnew.LoadBoard(os.path.join(REPO, 'hardware/board_carrier/board_carrier.kicad_pcb'))
    e = c.GetBoardEdgesBoundingBox()
    u3 = c.FindFootprintByReference('U3')
    cut = None
    for g in u3.GraphicalItems():
        if g.GetLayer() == pcbnew.Edge_Cuts:
            b = g.GetBoundingBox()
            cut = (T(b.GetX()), T(b.GetY()), T(b.GetRight()), T(b.GetBottom()))
    pad1 = next(p for p in u3.Pads() if p.GetNumber() == '1')
    u3pads = [(T(p.GetPosition().x), T(p.GetPosition().y), p.GetNetname()) for p in u3.Pads()]
    return (T(e.GetX()), T(e.GetY()), T(e.GetRight()), T(e.GetBottom())), cut, (T(pad1.GetPosition().x), T(pad1.GetPosition().y)), u3pads


def panel(svg, px, py, pw, ph, win, title, carrier=None, cut=None, pads=(), hdr=None, note='', cid='c'):
    """A view from below of the board area win = (x0, y0, x1, y1) in KiCad (top-view) mm, fitted into the pixel box
    (px, py, pw, ph): KiCad x is mirrored (larger x to the left), y kept."""
    s = min(pw / (win[2] - win[0]), ph / (win[3] - win[1]))

    def U(x):
        return px + (win[2] - x) * s

    def V(y):
        return py + (y - win[1]) * s

    def rect(b, **kw):
        a = ' '.join(f'{k.replace("_", "-")}="{v}"' for k, v in kw.items())
        return f'<rect x="{U(b[2])}" y="{V(b[1])}" width="{(b[2] - b[0]) * s}" height="{(b[3] - b[1]) * s}" {a}/>'

    svg.append(f'<text x="{px}" y="{py - 14}" font-size="16" font-weight="600">{title}</text>')
    svg.append(f'<clipPath id="{cid}"><rect x="{px}" y="{py}" width="{(win[2] - win[0]) * s}" height="{(win[3] - win[1]) * s}"/></clipPath>')
    svg.append(f'<g clip-path="url(#{cid})">')
    if carrier:
        svg.append(rect(carrier, fill='#2f5d34'))
        svg.append(rect(cut, fill='#f4f1e8', stroke='#000', stroke_width='2'))
    for b in (hdr or {}).get('_box', []):
        svg.append(rect(b, rx='6', fill='#2f5d34', stroke='#183a1c', stroke_width='2'))
    for r, rows in (hdr or {}).items():
        if r == '_box':
            continue
        for n, x, y in rows:
            svg.append(f'<circle cx="{U(x)}" cy="{V(y)}" r="{0.85 * s}" fill="#d4a017" stroke="#6b5200"/>')
    for num, net, x, y, size in pads:
        if num:
            svg.append(f'<circle cx="{U(x)}" cy="{V(y)}" r="{size / 2 * s}" fill="#e8c35a" stroke="#000"/>')
            svg.append(f'<text x="{U(x)}" y="{V(y) + 0.25 * s}" font-size="{max(11, 0.55 * s):.0f}" font-weight="700" '
                       f'text-anchor="middle">{num}</text>')
        else:
            svg.append(f'<circle cx="{U(x)}" cy="{V(y)}" r="{size / 2 * s}" fill="#111"/>')
    svg.append('</g>')
    # header labels outside the clip, beside each pin
    for r, rows in (hdr or {}).items():
        if r == '_box':
            continue
        for n, x, y in rows:
            left = U(x) < px + (win[2] - win[0]) * s / 2
            svg.append(f'<text x="{U(x) + (-2.3 if left else 2.3) * s}" y="{V(y) + 4}" font-size="11" '
                       f'text-anchor="{"end" if left else "start"}">{r}-{n} {HDR.get((r, n), "?")}</text>')
    if cut:
        svg.append(f'<text x="{px}" y="{V(win[3]) + 18}" font-size="12">Cutout {cut[2] - cut[0]:.1f} x {cut[3] - cut[1]:.1f} mm; '
                   f'carrier 1.6 mm thick. {note}</text>')
    return U, V


def main():
    box, pads, hdr = module_geometry()
    cbox, cut, u3p1, u3pads = carrier_geometry()
    j3p1 = hdr['J3'][0]
    shift = (u3p1[0] - j3p1[1], u3p1[1] - j3p1[2])      # module -> carrier coordinates
    for r, rows in hdr.items():
        for n, x, y in rows:
            net = min(u3pads, key=lambda q: (q[0] - x - shift[0]) ** 2 + (q[1] - y - shift[1]) ** 2)
            if (net[0] - x - shift[0]) ** 2 + (net[1] - y - shift[1]) ** 2 > 0.01:
                raise SystemExit(f'{r}-{n} lands on no carrier pad')
            HDR[(r, n)] = 'not connected (Boot0)' if 'unconnected' in net[2] else net[2].lstrip('/')
    W, H = 1500, 760
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
           f'font-family="DejaVu Sans, sans-serif"><rect width="{W}" height="{H}" fill="#fff"/>']
    hdr1 = dict(hdr, _box=[box])
    m = 1.5
    panel(svg, 150, 60, 520, 380, (box[0] - m, box[1] - m, box[2] + m, box[3] + m),
          '1. Module alone, upside down (seen from below): flash it here first', pads=pads, hdr=hdr1, cid='p1')
    moved = [(n, net, x + shift[0], y + shift[1], sz) for n, net, x, y, sz in pads]
    win = (cut[0] - 5, cut[1] - 4, cut[2] + 5, cut[3] + 4)
    panel(svg, 860, 60, 560, 380, win, '2. Carrier from below, module fitted: J2 in the cutout', carrier=cbox, cut=cut,
          pads=moved, note='Plug body fit: UNKNOWN until tried.', cid='p2')
    # Legend: pad -> signal
    y = 520
    svg.append(f'<text x="120" y="{y}" font-size="15" font-weight="600">J2 pads (module netlist)</text>')
    for i, (num, net, *_rest) in enumerate(sorted((p for p in pads if p[0]), key=lambda p: p[0])):
        name = SIG.get(net, 'SWO: not connected' if 'unconnected' in net else net)
        svg.append(f'<text x="120" y="{y + 24 + 20 * i}" font-size="13">pad {num}: {name}</text>')
    svg.append(f'<text x="420" y="{y + 24}" font-size="13">Black dots: the plug\'s three locating holes (2 on one side, 1 on the other),</text>')
    svg.append(f'<text x="420" y="{y + 44}" font-size="13">so a TC2030 "-NL" plug only fits one way round.</text>')
    svg.append(f'<text x="420" y="{y + 64}" font-size="13">Pinout matches Tag-Connect\'s ARM Cortex mapping (FROM MEMORY): TC2030-CTX-NL cable.</text>')
    svg.append(f'<text x="420" y="{y + 84}" font-size="13">Pad 1 is the target-voltage sense: power the board from its own supply, not the probe.</text>')
    svg.append(f'<text x="420" y="{y + 124}" font-size="12" fill="#555">Generated by work/gen/swd_diagram.py from the KiCad files; both panels mirrored (view from below).</text>')
    svg.append('</svg>')
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, 'swd-pads.svg')
    open(p, 'w').write('\n'.join(svg))
    subprocess.run(['magick', p, p[:-4] + '.png'], check=True)
    print(f'wrote {os.path.relpath(p, WORK)} and .png (module shift to carrier {shift[0]:.3f}, {shift[1]:.3f} mm)')


if __name__ == '__main__':
    main()
