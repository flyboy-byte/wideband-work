#!/usr/bin/env python3
"""Generate hardware/board_carrier/board_carrier.kicad_pcb: upstream's carrier plus our analog output stage.

  python3 work/gen/gen_carrier_pcb.py            place, route with Freerouting, fill zones, write the board
  python3 work/gen/gen_carrier_pcb.py --no-route place only (to look at placement)

Base = upstream's board at `master`, upgraded to KiCad 10. Every pad's net is set from the generated schematic's
netlist (work/gen/gen_carrier_sch.py writes it), so board and schematic match. The board is upstream's
40 x 36.5 mm grown by GROW mm at the bottom edge, away from the connector (the owner designs his own enclosure, so
case/case.STL is no limit, 2026-10-23). New parts go in that strip, on the side named by SIDE (top since 2026-10-24,
owner decision D9: one-sided JLC assembly; r1-r36 put them on the bottom).
Upstream's tracks and vias are locked before routing, so Freerouting only adds the new connections.
"""
import json, math, os, re, shutil, subprocess, sys, tempfile, xml.etree.ElementTree as ET

import pcbnew

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SCH = os.path.join(REPO, 'hardware/board_carrier/board_carrier.kicad_sch')
OUT = os.path.join(REPO, 'hardware/board_carrier/board_carrier.kicad_pcb')
FPLIB = '/usr/share/kicad/footprints'
FREEROUTING = os.path.expanduser('~/.local/share/freerouting/freerouting-2.5.0.jar')

# New parts on the bottom. Each has a target (x, y) in board coordinates seen from the top; the placer puts it at the
# nearest legal spot (rotation 0 or 90), checking its courtyard against the module's bottom courtyards (header rows
# and the cutout at x 48.8-56.8 / y 72.8-78.3), the board edge, upstream's bottom tracks, vias, through-hole pads,
# and parts already placed. Floorplan: op-amp and output right of the cutout, next to the connector (short run to
# J3-5); buffer, reference and RC chain below the cutout, fed from module pad 3; op-amp supply parts lower left, fed
# from module pad 7 (VBatt_Sense, the same protected 12 V net as LSU_Heater+). Placed in this order.
GROW = 15.0   # mm added at the bottom edge (y 91.25 -> 106.25)
# Side of the new parts. 'top' (D9, 2026-10-24): every SMD part then sits on the top, so JLC's Economic assembly
# applies ($8 setup, against $50 for Standard two-sided [REPORTED, JLC help "PCB assembly price", updated 2025-09]).
# The strip's top is free: the module's courtyard ends at y 90.7 and only the GND pour reaches below (checked 2026-10-24).
SIDE = os.environ.get('SIDE', 'top')
CU = pcbnew.F_Cu if SIDE == 'top' else pcbnew.B_Cu            # the new parts' copper layer
FAR = pcbnew.B_Cu if SIDE == 'top' else pcbnew.F_Cu           # the other layer (fan-out vias reach its GND pour)
CRT = pcbnew.F_CrtYd if SIDE == 'top' else pcbnew.B_CrtYd
# M3 mounting holes in the strip's corners (owner decision D8, 2026-10-23), centres 3.5 mm in from both edges.
# MountingHole_3.2mm_M3: plain NPTH, no copper, courtyard about 3.45 mm radius
HOLES = [('H1', (39.975 + 3.5, 106.275 - 3.5)), ('H2', (80.025 - 3.5, 106.275 - 3.5))]
# No copper (tracks, vias, pour) under a screw head and washer, both sides: an M3 washer is about 7 mm across [FROM
# MEMORY, DIN 125], so 3.6 mm radius. The holes stay isolated: a metal screw into a grounded case must not tie board GND
# to it (the output's ground is the ECU sensor ground, owner answer C3). Default 2026-10-24 (r41: r37-r40 had GND pour
# 0.3 mm from the hole and a +5V track 3.0 mm from H1's centre); grounding the case through a plated hole is the
# owner's call.
HOLE_KEEPOUT = 3.6
# Floorplan in the strip (bottom side, coordinates seen from the top): the stage sits below the module's LEFT pad column
# (pads 3 SEL_1 PWM, 4 SEL_2, 7 LSU_Heater+), away from the right column (heater drive pads 11-12, sensor pads 13-16).
# PWM in at the left, filter left to right, op-amp in the middle, its supply right of it. The output (R8, clamps, R11)
# sits under the free corridor right of the module cutout, the straight way up to J3-5 (r34 put R11 at the far left; its
# 53 mm track then ran 7 mm beside CAN_L at 0.3 mm, layout_review.py). The CAN terminator goes to the left end, where
# CAN_H/L already run down the left side (r34 had it on the output's corridor). The annealer moves them from here.
TARGETS = [
    ('U6',  (61.0, 97.6)),   # LM2904
    ('C15', (56.4, 98.8)),   # Cf, beside pins 1-2 (lower left on the bottom side)
    ('R6',  (56.6, 97.0)),
    ('R7',  (56.6, 101.0)),
    ('C17', (64.0, 101.6)),  # op-amp bypass, at pin 8 (bottom side, rotation 0: pin 8 is lower right; r35 started it
                             # above the chip and the annealer could not get it round, 6.1 mm)
    ('R9',  (67.0, 94.0)),   # op-amp supply
    ('D5',  (67.0, 97.0)),
    ('C16', (67.0, 100.0)),  # 1206
    ('R8',  (57.6, 94.6)),   # output side
    ('D3',  (57.0, 92.6)),
    ('D4',  (54.4, 92.6)),
    ('R11', (60.2, 92.8)),   # 1206, last before J3-5
    ('JP1', (42.6, 100.6)),  # TEST jumper
    ('R3',  (46.6, 96.6)),   # pull-down on the buffer input
    ('U4',  (49.0, 97.0)),   # buffer
    ('U5',  (49.0, 101.4)),  # REF3030
    ('C12', (46.6, 101.4)),  # VREF3 cap
    ('C11', (51.6, 101.4)),  # REF input cap
    ('R4',  (51.6, 97.0)),   # RC chain
    ('C13', (51.6, 99.0)),
    ('R5',  (54.0, 97.0)),
    ('C14', (54.0, 99.0)),
    ('R10', (42.6, 93.0)),   # CAN terminator
    ('JP2', (42.6, 96.4)),
]
CLEAR = 0.25                 # mm between a courtyard and any obstacle
AREA = (41.0, 91.8, 79.0, 91.25 + GROW - 0.8)   # bottom placement area: the new strip, inside the edge keep-out
# Upstream bottom tracks that cross the free area and carry little current; deleted so the router can redo them:
# the battery-sense branch to module pad 7 (0.2 mm) and the module's +5V feed (0.5 mm, about 50 mA).
# The 0.5 mm LSU_Heater+ bottom path (J3-4 to the regulator side) is a parallel supply path and stays.
REROUTE = []   # with the strip there is room: upstream's tracks all stay (r1-r33 deleted two to make room)
# REROUTE_r33 = [('/LSU_Heater+', (47.0, 78.0, 56.0, 87.0)), ('+5V', (45.5, 84.0, 61.0, 91.0))]
# (keeping the LSU_Heater+ branch changes the obstacles and so the placement; it did worse on r27)
# (keeping the +5V feed instead left no room to place everything, r9)
CUTOUT = (48.41, 72.49, 57.11, 78.65)   # module cutout 48.76-56.76 x 72.84-78.30, grown 0.35 mm
# (0.5 mm would cover upstream's own top tracks, which pass about 0.4 mm from the cutout)
EDGE_KEEP = 0.6                          # mm strip inside the board edge with no new tracks or vias (rule: 0.5)
TOP_NO_TRACKS = json.loads(os.environ['TOP_NO_TRACKS']) if 'TOP_NO_TRACKS' in os.environ else [(57.5, 77.0, 71.0, 90.0)]   # top area around C1/C2/C3/C6/U1 where new tracks cut the GND pour (r6)
KEEP_THERMAL_VIAS_X = 66.9   # GND vias right of this (under the TVS and regulator) are thermal: never removed


def netlist():
    """{(ref, pad): net name}, {ref: (footprint, value, LCSC)} from the generated schematic."""
    with tempfile.TemporaryDirectory() as td:
        xml = os.path.join(td, 'n.xml')
        subprocess.run(['kicad-cli', 'sch', 'export', 'netlist', '--format', 'kicadxml', '-o', xml, SCH],
                       capture_output=True, check=True)
        root = ET.parse(xml).getroot()
    nets = {}
    for net in root.iter('net'):
        for n in net.iter('node'):
            nets[(n.get('ref'), n.get('pin'))] = net.get('name')
    comps = {}
    for c in root.iter('comp'):
        fields = {f.get('name'): f.text for f in c.iter('field')}
        comps[c.get('ref')] = (c.findtext('footprint'), c.findtext('value'), fields.get('LCSC', ''))
    return nets, comps


def mm(v):
    return pcbnew.FromMM(v)


def courtyard_box(fp):
    """(x0, y0, x1, y1) in mm of the footprint's courtyard on the new parts' side, grown by CLEAR."""
    bb = fp.GetCourtyard(CRT).BBox()
    return (pcbnew.ToMM(bb.GetX()) - CLEAR, pcbnew.ToMM(bb.GetY()) - CLEAR,
            pcbnew.ToMM(bb.GetRight()) + CLEAR, pcbnew.ToMM(bb.GetBottom()) + CLEAR)


def obstacle_shapes(board):
    """Boxes (x0, y0, x1, y1) and circles (x, y, r) in mm that new parts must keep out of (on their side)."""
    T = pcbnew.ToMM
    boxes, circles = [], []
    for fp in board.GetFootprints():
        for g in fp.GraphicalItems():
            if g.GetLayer() in (CRT, pcbnew.Edge_Cuts):
                bb = g.GetBoundingBox()
                boxes.append((T(bb.GetX()), T(bb.GetY()), T(bb.GetRight()), T(bb.GetBottom())))
        for pad in fp.Pads():
            if pad.GetAttribute() != pcbnew.PAD_ATTRIB_SMD:
                circles.append((T(pad.GetPosition().x), T(pad.GetPosition().y), T(pad.GetSize(pcbnew.F_Cu).x) / 2))
    for t in board.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T:
            x, y = T(t.GetPosition().x), T(t.GetPosition().y)
            if t.GetNetname() != 'GND' or x >= KEEP_THERMAL_VIAS_X:    # stray GND stitching vias may be removed
                circles.append((x, y, T(t.GetWidth(pcbnew.F_Cu)) / 2))
        elif t.GetLayer() == CU:
            (x0, y0), (x1, y1) = (T(t.GetStart().x), T(t.GetStart().y)), (T(t.GetEnd().x), T(t.GetEnd().y))
            n = max(1, int(((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5 / 0.2))
            for i in range(n + 1):
                circles.append((x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n, T(t.GetWidth()) / 2))
    return boxes, circles, AREA


def legal(box, obstacles, placed):
    boxes, circles, edge = obstacles
    x0, y0, x1, y1 = box
    if x0 < edge[0] or y0 < edge[1] or x1 > edge[2] or y1 > edge[3]:
        return False
    for b in boxes + placed:
        if x0 < b[2] and b[0] < x1 and y0 < b[3] and b[1] < y1:
            return False
    for cx, cy, r in circles:
        nx, ny = min(max(cx, x0), x1), min(max(cy, y0), y1)
        if (nx - cx) ** 2 + (ny - cy) ** 2 < r * r:
            return False
    return True


def find_spot(fp, tx, ty, obstacles, placed):
    """Nearest legal (x, y, rotation) to the target on a 0.2 mm grid, searching rings outward up to 18 mm."""
    cands = sorted(((dx * 0.2, dy * 0.2) for dx in range(-90, 91) for dy in range(-90, 91)),
                   key=lambda d: d[0] ** 2 + d[1] ** 2)
    for dx, dy in cands:
        for rot in (0, 90):
            fp.SetOrientationDegrees(rot)
            fp.SetPosition(pcbnew.VECTOR2I(mm(tx + dx), mm(ty + dy)))
            if legal(courtyard_box(fp), obstacles, placed):
                return tx + dx, ty + dy, rot
    return None


# Finisher before Freerouting, locked: every net local to the new stage, tightest first. Freerouting then only joins the
# stage to upstream copper (+5V, LSU_Heater+, CAN, the module pads)
PREROUTE = ['/AOUT_OA', '/AOUT', '/AOUT_INN', '/AOUT_F2', '/VREF3', '/AOUT_F1', '/AOUT_BUF', '/U6B_FB', '/VOP12',
            '/CAN_TERM']
# (r1-r33 also pre-routed AOUT_PWM, TEST_SEL2 and local branches of LSU_Heater+, CAN_H/L, +5V on the crowded board;
# in the strip those are long runs to upstream copper, left to Freerouting)
# (+5V's local branch here made the rest fail: r24-r25.) LSU_Heater+: only the corner around module pad 7 and R9, where
# the deleted battery-sense branch was
LOCAL_BOX = {'/LSU_Heater+': (46.0, 79.0, 54.5, 89.5),
             '/CAN_H': (44.5, 64.0, 54.0, 72.5), '/CAN_L': (44.5, 64.0, 54.0, 72.5),   # terminator to the CAN tracks
             '+5V': (57.5, 76.5, 65.5, 83.0)}   # D3's clamp to the top +5V track (whole +5V branch: r24-r25 failed)
CROSS_MM = 2.0    # placement cost of one crossing of an upstream bottom track, in mm of net length
# The op-amp's feedback loop (output, Cf, inverting input) and its filtered input weigh more: a small loop is better
# for stability, and a loose C15 left the output unrouted on r13
NET_WEIGHT = {'/AOUT_OA': 3.0, '/AOUT_INN': 3.0, '/AOUT_F2': 2.0, '/VOP12': 2.0, '/AOUT_PWM': 2.0, '/AOUT_J': 2.0}
BYPASS = {'~C17': [('C17', '1'), ('U6', '8')],    # op-amp supply pin
          '~C11': [('C11', '1'), ('U5', '1')],    # REF3030 input
          '~C12': [('C12', '1'), ('U5', '2')],    # REF3030 output
          '~C15a': [('C15', '1'), ('U6', '1')],   # Cf across the op-amp: a short AC feedback loop
          '~C15b': [('C15', '2'), ('U6', '2')]}
NET_WEIGHT.update({n: 8.0 for n in BYPASS})   # 4.0 left C17 6.1 mm and C15 6.6 mm from their pins (r35)
# VOP12: C17 at pin 8 (r33 weighted it on the crowded board and broke routing; the strip has room). AOUT_PWM: keep the
# 46.9 kHz edges short


def anneal(board, nets, obstacles, seed=1, iters=200000):
    """Improve the greedy placement: move the new parts among legal spots (0.2 mm grid, rotation 0/90/180/270) to
    shorten their nets. Cost per net = half-perimeter of its new pads + distance from them to the nearest copper the
    net already has (upstream pads and tracks). GND is left out: the pour and fan-out vias connect it. The greedy
    spots from TARGETS are the starting point, so the result is never worse than that by this measure."""
    import numpy as np, random
    rnd = random.Random(seed)
    T = pcbnew.ToMM
    refs = [r for r, _ in TARGETS]
    fps = {f.GetReference(): f for f in board.GetFootprints() if f.GetReference() in refs}
    rots = (0, 90, 180, 270)
    G = 0.2
    nx, ny = int((AREA[2] - AREA[0]) / G) + 1, int((AREA[3] - AREA[1]) / G) + 1
    X, Y = np.meshgrid(AREA[0] + np.arange(nx) * G, AREA[1] + np.arange(ny) * G, indexing='ij')
    boxes, circles, edge = obstacles
    cb = np.array(boxes) if boxes else np.zeros((0, 4))
    cc = np.array(circles) if circles else np.zeros((0, 3))

    # Per part and rotation: courtyard box and pad offsets relative to the footprint position, and the legal mask
    box, pads, legal_mask, start = {}, {}, {}, {}
    for r in refs:
        fp = fps[r]
        p0, rot0 = fp.GetPosition(), fp.GetOrientationDegrees()
        start[r] = (rots.index(int(round(rot0)) % 360), int(round((T(p0.x) - AREA[0]) / G)), int(round((T(p0.y) - AREA[1]) / G)))
        for k, rot in enumerate(rots):
            fp.SetOrientationDegrees(rot)
            fp.SetPosition(pcbnew.VECTOR2I(0, 0))
            box[r, k] = courtyard_box(fp)
            pads[r, k] = {p.GetNumber(): (T(p.GetPosition().x), T(p.GetPosition().y)) for p in fp.Pads() if p.GetNumber()}
            bx0, by0, bx1, by1 = box[r, k]
            x0, y0, x1, y1 = X + bx0, Y + by0, X + bx1, Y + by1
            m = (x0 >= edge[0]) & (y0 >= edge[1]) & (x1 <= edge[2]) & (y1 <= edge[3])
            for ob in cb:
                m &= ~((x0 < ob[2]) & (ob[0] < x1) & (y0 < ob[3]) & (ob[1] < y1))
            for cx, cy, rad in cc:
                dx = np.clip(cx, x0, x1) - cx
                dy = np.clip(cy, y0, y1) - cy
                m &= dx * dx + dy * dy >= rad * rad
            legal_mask[r, k] = m
        fp.SetOrientationDegrees(rot0)
        fp.SetPosition(p0)
        k, i, j = start[r]
        legal_mask[r, k][i, j] = True     # the greedy spot passed the same test; keep it reachable despite rounding

    # Nets of the new parts, with anchors (existing copper on that net outside the new parts)
    netpads, anchors = {}, {}
    for (ref, pad), name in nets.items():
        if ref in refs and name != 'GND':
            netpads.setdefault(name, []).append((ref, pad))
    for name in netpads:
        pts = [(T(p.GetPosition().x), T(p.GetPosition().y)) for f in board.GetFootprints() if f.GetReference() not in refs
               for p in f.Pads() if p.GetNetname() == name]
        for t in board.GetTracks():
            if t.GetNetname() == name and t.Type() == pcbnew.PCB_TRACE_T:
                (ax, ay), (bx, by) = (T(t.GetStart().x), T(t.GetStart().y)), (T(t.GetEnd().x), T(t.GetEnd().y))
                n = max(1, int(math.hypot(bx - ax, by - ay) / 0.5))
                pts += [(ax + (bx - ax) * s / n, ay + (by - ay) * s / n) for s in range(n + 1)]
        anchors[name] = np.array(pts) if pts else None
    # Bypass caps: a net's half-perimeter doesn't care where a cap sits inside it, so each cap is also tied to its IC pin
    for name, pair in BYPASS.items():
        netpads[name], anchors[name] = list(pair), None
    part_nets = {r: [n for n, ps in netpads.items() if any(q[0] == r for q in ps)] for r in refs}
    # Upstream bottom tracks: a straight pad-to-pad connection that crosses one needs a via pair or a long detour
    # (seed 7 of r13 left the op-amp output unrouted with C15 and R8 on opposite sides of two sensor tracks)
    segs = np.array([(T(t.GetStart().x), T(t.GetStart().y), T(t.GetEnd().x), T(t.GetEnd().y))
                     for t in board.GetTracks() if t.Type() == pcbnew.PCB_TRACE_T and t.GetLayer() == CU])

    def crossings(x0, y0, x1, y1):
        if not len(segs):
            return 0
        ax, ay, bx, by = segs[:, 0], segs[:, 1], segs[:, 2], segs[:, 3]
        d1 = (bx - ax) * (y0 - ay) - (by - ay) * (x0 - ax)
        d2 = (bx - ax) * (y1 - ay) - (by - ay) * (x1 - ax)
        d3 = (x1 - x0) * (ay - y0) - (y1 - y0) * (ax - x0)
        d4 = (x1 - x0) * (by - y0) - (y1 - y0) * (bx - x0)
        return int(np.count_nonzero((d1 * d2 < 0) & (d3 * d4 < 0)))

    state = dict(start)

    def where(r, pad):
        k, i, j = state[r]
        ox, oy = pads[r, k][pad]
        return AREA[0] + i * G + ox, AREA[1] + j * G + oy

    def net_cost(name):
        pts = [where(r, p) for r, p in netpads[name]]
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        c = max(xs) - min(xs) + max(ys) - min(ys)
        # chain the pads nearest-first and charge CROSS_MM per upstream track each link crosses
        rest, cur = pts[1:], pts[0]
        while rest:
            nxt = min(rest, key=lambda q: abs(q[0] - cur[0]) + abs(q[1] - cur[1]))
            c += CROSS_MM * crossings(cur[0], cur[1], nxt[0], nxt[1])
            rest.remove(nxt); cur = nxt
        a = anchors[name]
        if a is not None:
            c += min(float(np.min(np.abs(a[:, 0] - x) + np.abs(a[:, 1] - y))) for x, y in pts)
        return c * NET_WEIGHT.get(name, 1.0)

    def abs_box(r):
        k, i, j = state[r]
        b = box[r, k]
        return (AREA[0] + i * G + b[0], AREA[1] + j * G + b[1], AREA[0] + i * G + b[2], AREA[1] + j * G + b[3])

    def overlaps(r):
        a = abs_box(r)
        for o in refs:
            if o != r:
                b = abs_box(o)
                if a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]:
                    return True
        return False

    cost = {n: net_cost(n) for n in netpads}
    total = sum(cost.values())
    first = total
    t0, t1 = 2.0, 0.02
    for it in range(iters):
        temp = t0 * (t1 / t0) ** (it / iters)
        r = rnd.choice(refs)
        old = state[r]
        k, i, j = old
        reach = max(1, int(temp * 8))
        if rnd.random() < 0.15:
            k = rnd.randrange(4)
        i += rnd.randint(-reach, reach)
        j += rnd.randint(-reach, reach)
        if not (0 <= i < nx and 0 <= j < ny) or not legal_mask[r, k][i, j]:
            continue
        state[r] = (k, i, j)
        if overlaps(r):
            state[r] = old
            continue
        new = {n: net_cost(n) for n in part_nets[r]}
        delta = sum(new.values()) - sum(cost[n] for n in part_nets[r])
        if delta <= 0 or rnd.random() < math.exp(-delta / temp):
            cost.update(new)
            total += delta
        else:
            state[r] = old
    print(f'placement: net length {first:.1f} -> {total:.1f} mm')
    for r in refs:
        k, i, j = state[r]
        fps[r].SetOrientationDegrees(rots[k])
        fps[r].SetPosition(pcbnew.VECTOR2I(mm(AREA[0] + i * G), mm(AREA[1] + j * G)))
        print(f'  {r:4s} at {AREA[0] + i * G:.1f},{AREA[1] + j * G:.1f} rot {rots[k]}')


def main(route=True):
    nets, comps = netlist()
    td = tempfile.mkdtemp()
    base = os.path.join(td, 'board_carrier.kicad_pcb')
    open(base, 'w').write(subprocess.run(['git', '-C', REPO, 'show', 'master:hardware/board_carrier/board_carrier.kicad_pcb'],
                                         capture_output=True, text=True, check=True).stdout)
    subprocess.run(['kicad-cli', 'pcb', 'upgrade', base], capture_output=True, check=True)
    board = pcbnew.LoadBoard(base)
    grow_board(board, GROW)

    def net(name):
        n = board.FindNet(name)
        if not n:
            n = pcbnew.NETINFO_ITEM(board, name)
            board.Add(n)
        return n

    # Delete the low-current upstream bottom tracks listed in REROUTE, then lock everything else upstream routed
    def inside(pt, box):
        x, y = pcbnew.ToMM(pt.x), pcbnew.ToMM(pt.y)
        return box[0] <= x <= box[2] and box[1] <= y <= box[3]
    doomed = []
    for t in board.GetTracks():
        for netname, box in REROUTE:
            if t.GetNetname() != netname:
                continue
            if (t.Type() == pcbnew.PCB_VIA_T and inside(t.GetPosition(), box)) or \
                    (t.Type() == pcbnew.PCB_TRACE_T and t.GetLayer() == pcbnew.B_Cu and
                     (inside(t.GetStart(), box) or inside(t.GetEnd(), box))):
                doomed.append(t)
                break
    for t in doomed:
        board.Delete(t)
    print(f'deleted {len(doomed)} upstream bottom track pieces to reroute')
    for t in board.GetTracks():
        t.SetLocked(True)

    # Mounting holes first, so the placer keeps parts off them
    for ref, (hx, hy) in HOLES:
        h = pcbnew.FootprintLoad(os.path.join(FPLIB, 'MountingHole.pretty'), 'MountingHole_3.2mm_M3')
        h.SetReference(ref)
        h.Reference().SetVisible(False)
        h.Value().SetVisible(False)
        h.SetPosition(pcbnew.VECTOR2I(mm(hx), mm(hy)))
        h.SetLocked(True)
        board.Add(h)
        ko = pcbnew.ZONE(board)
        ko.SetIsRuleArea(True)
        ko.SetDoNotAllowTracks(True)
        ko.SetDoNotAllowVias(True)
        ko.SetDoNotAllowZoneFills(True)
        ko.SetDoNotAllowPads(False)
        ko.SetDoNotAllowFootprints(False)
        kls = pcbnew.LSET(); kls.AddLayer(pcbnew.F_Cu); kls.AddLayer(pcbnew.B_Cu)
        ko.SetLayerSet(kls)
        o = ko.Outline(); o.NewOutline()
        for k in range(36):
            a = k * math.pi / 18
            o.Append(mm(hx + HOLE_KEEPOUT * math.cos(a)), mm(hy + HOLE_KEEPOUT * math.sin(a)))
        ko.SetZoneName(f'{ref}_screw_keepout')   # permanent (not in AIDS): the pour stays out after the refill
        board.Add(ko)
    # New footprints on SIDE, placed one by one at the nearest legal spot to their target
    obstacles = obstacle_shapes(board)
    placed = []
    for ref, (tx, ty) in TARGETS:
        fpid, value, lcsc = comps[ref]
        lib, name = fpid.split(':')
        fp = pcbnew.FootprintLoad(os.path.join(FPLIB, lib + '.pretty'), name)
        fp.SetReference(ref)
        fp.SetValue(value)
        if lcsc:
            fp.SetField('LCSC', lcsc)
            fp.GetField('LCSC').SetVisible(False)
        fp.Value().SetVisible(False)
        fp.Reference().SetTextSize(pcbnew.VECTOR2I(mm(0.8), mm(0.8)))
        fp.Reference().SetTextThickness(mm(0.12))
        board.Add(fp)
        if SIDE != 'top':
            fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        spot = find_spot(fp, tx, ty, obstacles, placed)
        if not spot:
            sys.exit(f'no legal spot for {ref} near {tx},{ty}')
        placed.append(courtyard_box(fp))
        print(f'  {ref:4s} at {spot[0]:.1f},{spot[1]:.1f} rot {spot[2]}')

    # Every pad's net from the schematic (upstream parts included, so the board matches the schematic exactly)
    missing = []
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            key = (fp.GetReference(), pad.GetNumber())
            if not pad.GetNumber():
                continue
            if key in nets:
                pad.SetNet(net(nets[key]))
            else:
                missing.append(key)
    if missing:
        print('pads with no schematic net:', missing)
    anneal(board, nets, obstacles, seed=int(os.environ.get('SEED', '7')))

    # Stray GND stitching vias under new parts: remove (they joined the top GND pour to a bottom with no copper)
    new_boxes = []
    for fp in board.GetFootprints():
        if fp.GetReference() in dict(TARGETS):
            bb = fp.GetCourtyard(CRT).BBox()
            bb.Inflate(mm(0.35))
            new_boxes.append(bb)
    stray = [t for t in board.GetTracks() if t.Type() == pcbnew.PCB_VIA_T and t.GetNetname() == 'GND' and
             pcbnew.ToMM(t.GetPosition().x) < KEEP_THERMAL_VIAS_X and
             any(bb.Contains(t.GetPosition()) for bb in new_boxes)]
    for t in stray:
        board.Delete(t)
    print(f'removed {len(stray)} GND stitching vias under new parts')

    # Upstream's GND pour already covers both copper layers (it was only unfilled on the bottom); it is refilled at
    # the end. New small pads join it solid: thermal spokes on SC-70/0603 pads came out "starved" in DRC.
    for fp in board.GetFootprints():
        if fp.GetReference() in dict(TARGETS):
            for pad in fp.Pads():
                pad.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)

    fanout_gnd(board)
    # D3's +5V pad gets its own via: the 5 mm link to the top +5V track was the one left open on r26 (seed 7)
    fanout_gnd(board, '+5V', ['D3'])
    tap_top_track(board, '+5V', ['U5', 'C11', 'D3'])

    # Keep tracks and vias 0.5 mm off the module cutout (the router doesn't treat that inner Edge.Cuts as an edge)
    x0, y0, x1, y1 = CUTOUT
    keep = pcbnew.ZONE(board)
    keep.SetIsRuleArea(True)
    keep.SetDoNotAllowTracks(True)
    keep.SetDoNotAllowVias(True)
    keep.SetDoNotAllowZoneFills(True)
    keep.SetDoNotAllowPads(False)
    keep.SetDoNotAllowFootprints(False)
    ls = pcbnew.LSET(); ls.AddLayer(pcbnew.F_Cu); ls.AddLayer(pcbnew.B_Cu)
    keep.SetLayerSet(ls)
    o = keep.Outline(); o.NewOutline()
    for x, y in [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]:
        o.Append(mm(x), mm(y))
    keep.SetZoneName('cutout_keepout')
    board.Add(keep)
    # Same along the board edge: the router ignores the 0.5 mm copper-to-edge rule
    e = board.GetBoardEdgesBoundingBox()
    ex0, ey0, ex1, ey1 = (pcbnew.ToMM(v) for v in (e.GetX(), e.GetY(), e.GetRight(), e.GetBottom()))
    k = EDGE_KEEP
    for i, (a0, b0, a1, b1) in enumerate([(ex0, ey0, ex1, ey0 + k), (ex0, ey1 - k, ex1, ey1),
                                          (ex0, ey0, ex0 + k, ey1), (ex1 - k, ey0, ex1, ey1)]):
        z = pcbnew.ZONE(board)
        z.SetIsRuleArea(True)
        z.SetDoNotAllowTracks(True)
        z.SetDoNotAllowVias(True)
        z.SetDoNotAllowZoneFills(False)
        z.SetDoNotAllowPads(False)
        z.SetDoNotAllowFootprints(False)
        z.SetLayerSet(ls)
        o = z.Outline(); o.NewOutline()
        for x, y in [(a0, b0), (a1, b0), (a1, b1), (a0, b1)]:
            o.Append(mm(x), mm(y))
        z.SetZoneName(f'edge_keepout_{i}')
        board.Add(z)
    # No new top-side tracks over upstream's 12V_RAW pour (one cut it in two on r3) or among the regulator and
    # transceiver caps (they cut the top GND pour there on r6; bottom-only routing left 7-10 connections open on r4
    # and r7). Vias are still allowed: a via only punches a hole in a pour.
    v12 = [q for q in board.Zones() if not q.GetIsRuleArea() and q.GetNetname() == '12V_RAW'][0].GetBoundingBox()
    v12.Inflate(mm(0.5))
    T = pcbnew.ToMM
    for n, (a0, b0, a1, b1) in enumerate([(T(v12.GetX()), T(v12.GetY()), T(v12.GetRight()), T(v12.GetBottom()))] +
                                         TOP_NO_TRACKS):
        z = pcbnew.ZONE(board)
        z.SetIsRuleArea(True)
        z.SetDoNotAllowTracks(True)
        z.SetDoNotAllowVias(False)
        z.SetDoNotAllowZoneFills(False)
        z.SetDoNotAllowPads(False)
        z.SetDoNotAllowFootprints(False)
        z.SetLayer(pcbnew.F_Cu)
        o = z.Outline(); o.NewOutline()
        for x, y in [(a0, b0), (a1, b0), (a1, b1), (a0, b1)]:
            o.Append(mm(x), mm(y))
        z.SetZoneName(f'top_no_new_tracks_{n}')
        board.Add(z)

    # Design rules for the new routing: 0.25 mm default track (was 0.2, the board minimum, and the router went
    # under it); solder mask minimum web 0.1 mm (was 0.25, which flags every 0.65 mm-pitch part such as the SC-70
    # buffer; 0.1 mm is about what JLC states for green mask [FROM MEMORY, check JLC's capabilities page])
    ds = board.GetDesignSettings()
    ds.m_NetSettings.GetDefaultNetclass().SetTrackWidth(mm(0.25))
    ds.m_SolderMaskMinWidth = mm(0.1)

    # Bottom silkscreen: upstream's labels name module pads for an older module revision (TX/RX/nRESET);
    # the current module has SEL_1/SEL_2/VBatt_Sense there. Fix the labels; drop the title our strip now covers.
    # Upstream's '12V' under J3-6 stays (r1-r41 deleted it, from when our parts were on the bottom; restored 2026-10-24),
    # and the two J3 pins we put to use get labels in the same style: J3-5 OUT (the 0-5 V output), J3-7 GND (the output's reference ground)
    relabel = {'TX': 'AOUT', 'RX': 'TEST', 'nRESET': 'VBAT', 'v1.1': 'v1.1-aout'}
    template = None
    for d in list(board.GetDrawings()):
        if d.GetLayer() == pcbnew.B_SilkS and d.Type() == pcbnew.PCB_TEXT_T:
            if d.GetText() in relabel:
                d.SetText(relabel[d.GetText()])
            elif d.GetText() == 'rusEFI LSU 4.9 Controller':
                board.Remove(d)
            elif d.GetText() == '1' and template is None:
                template = d
    j3 = {p.GetNumber(): p.GetPosition() for p in board.FindFootprintByReference('J3').Pads()}
    # 'OUT', not 'AOUT': four characters at 1.0 mm ran into '12V' on the 3.5 mm pitch
    for pin, text, side in (('5', 'OUT', +1), ('7', 'GND', -1)):
        t = template.Duplicate()
        t.SetText(text)
        t.SetTextSize(pcbnew.VECTOR2I(mm(1.0), mm(1.0)))   # JLC's minimum (silk.py H, W), smaller than upstream's
        t.SetTextThickness(mm(0.16))
        # same rows as upstream's labels: below the 1-6 row (pin centre + 2.5 mm), above the 7-12 row (- 2.25 mm)
        t.SetPosition(pcbnew.VECTOR2I(j3[pin].x, j3[pin].y + mm(2.5 if side > 0 else -2.25)))
        board.Add(t)

    board.Save(base)
    sys.path.insert(0, os.path.dirname(__file__))
    import finish_routes
    if route:
        # The op-amp's own short nets first, locked, so Freerouting works around them: left to the router they were
        # the ones walled in (r16: AOUT_OA, VREF3, AOUT_F2 open)
        finish_routes.negotiate(board, PREROUTE, local=LOCAL_BOX)
        board.Save(base)
        route_board(board, base, td)
        board = pcbnew.LoadBoard(base)
        # Freerouting leaves 1-3 connections open here; the finisher routes them (keep-out aids still in place)
        for _ in range(3):
            if not finish_routes.finish(board, base):
                break
            board.Save(base)
    # The rule areas above only steer the router; DRC's own edge and clearance rules judge the result
    for z in [z for z in board.Zones() if z.GetIsRuleArea() and z.GetZoneName() in AIDS]:
        board.Delete(z)
    # Drop pour fragments that reach nothing on their net (upstream kept them; new parts cut a few off, r28)
    for z in board.Zones():
        if not z.GetIsRuleArea() and z.GetNetname() == 'GND':
            z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    close_d3_link(board)
    merge_close_vias(board)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    if stitch_islands(board):
        pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    if join_gnd_pieces(board):
        pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    # Silkscreen last, when every pad, via and track is where it stays (gen/silk.py)
    import silk
    silk.place_labels(board)
    board.Save(OUT)
    shutil.rmtree(td)
    print('wrote', os.path.relpath(OUT, REPO))


def merge_close_vias(board, gap=0.25):
    """Same-net vias whose holes are closer than `gap` mm (KiCad's hole_to_hole minimum here): keep one, move the
    track ends that met the other onto it, delete the other. The pre-placed vias (fan-out, taps) are locked and win
    over the router's. r26-r37 all shipped one such pair (+5V or GND, 0.225 mm apart) hidden as a DRC warning."""
    T = pcbnew.ToMM
    vias = [t for t in board.GetTracks() if t.Type() == pcbnew.PCB_VIA_T]
    gone = set()
    for i, a in enumerate(vias):
        for b in vias[i + 1:]:
            if id(a) in gone or id(b) in gone or a.GetNetCode() != b.GetNetCode():
                continue
            pa, pb = a.GetPosition(), b.GetPosition()
            d = math.hypot(T(pa.x - pb.x), T(pa.y - pb.y)) - T(a.GetDrill()) / 2 - T(b.GetDrill()) / 2
            if d >= gap:
                continue
            keep, drop = (a, b) if a.IsLocked() or not b.IsLocked() else (b, a)
            kp, dp = keep.GetPosition(), drop.GetPosition()
            moved = 0
            for t in board.GetTracks():
                if t.Type() == pcbnew.PCB_TRACE_T and t.GetNetCode() == keep.GetNetCode():
                    if t.GetStart() == dp:
                        t.SetStart(kp); moved += 1
                    if t.GetEnd() == dp:
                        t.SetEnd(kp); moved += 1
            board.Delete(drop)
            gone.add(id(drop))
            print(f'merged via at {T(dp.x):.2f},{T(dp.y):.2f} into {T(kp.x):.2f},{T(kp.y):.2f} ({keep.GetNetname()}, '
                  f'{moved} track ends moved)')
    # zero-length tracks left behind by the move
    for t in [t for t in board.GetTracks() if t.Type() == pcbnew.PCB_TRACE_T and t.GetStart() == t.GetEnd()]:
        board.Delete(t)


def grow_board(board, dy):
    """Move the bottom edge of the outline (and of every copper pour that reaches it) down by dy mm."""
    T, D = pcbnew.ToMM, pcbnew.FromMM(dy)
    y_cut = 87.0   # below this: the bottom corner arcs and the bottom edge line
    for d in board.GetDrawings():
        if d.GetLayer() != pcbnew.Edge_Cuts:
            continue
        a, b = d.GetStart(), d.GetEnd()
        if T(d.GetBoundingBox().GetY()) > y_cut:
            d.Move(pcbnew.VECTOR2I(0, D))                      # bottom arcs and line: shift
        elif d.GetShape() == pcbnew.SHAPE_T_SEGMENT and abs(T(a.x) - T(b.x)) < 0.1:
            if T(a.y) > T(b.y):                                # side lines: stretch the lower end
                d.SetStart(pcbnew.VECTOR2I(a.x, a.y + D))
            else:
                d.SetEnd(pcbnew.VECTOR2I(b.x, b.y + D))
    for z in board.Zones():
        o = z.Outline()
        for i in range(o.TotalVertices()):
            v = o.CVertex(i)
            if T(v.y) > y_cut:
                o.SetVertex(i, pcbnew.VECTOR2I(v.x, v.y + D))
    e = board.GetBoardEdgesBoundingBox()
    print(f'board grown by {dy} mm: {T(e.GetWidth()):.1f} x {T(e.GetHeight()):.1f} mm')


def close_d3_link(board):
    """D3's +5V pad ends up an island (r30 left it 1 open). A fixed top-side link, found with checks/whatif_route.py; it only
    applies when D3 sits where the seed-7 placement put it (the coordinates belong to that layout)."""
    d3 = board.FindFootprintByReference('D3').FindPadByNumber('1').GetPosition()
    if abs(d3.x / 1e6 - 59.20) > 0.05 or abs(d3.y / 1e6 - 78.15) > 0.05:
        print('close_d3_link: D3 is not at the seed-7 spot, skipped')
        return
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'checks'))
    import whatif_route
    whatif_route.apply(board, whatif_route.CANDIDATES['FIX_D3'])
    print('close_d3_link: D3 +5V linked to U2 pin 3 (top), C1 pin 2 GND via, C2 pin 2 solid')


AIDS = {'cutout_keepout'} | {f'edge_keepout_{i}' for i in range(4)} | {f'top_no_new_tracks_{i}' for i in range(8)}


def tap_top_track(board, netname, refs):
    """For each listed part's pad on `netname`, put a locked via on the nearest point of an upstream top-side track of
    that net that clears other copper on both layers (0.3 mm pad + 0.3 mm). The bottom pads then need only a short hop
    instead of a route across the crowded bottom (r5-r9 left +5V unconnected)."""
    T, net = pcbnew.ToMM, board.FindNet(netname)
    others = [p for f in board.GetFootprints() for p in f.Pads() if p.GetNetname() != netname and p.IsOnCopperLayer()]
    copper = [t for t in board.GetTracks() if t.GetNetname() != netname]
    pts = []
    for t in board.GetTracks():
        if t.GetNetname() == netname and t.Type() == pcbnew.PCB_TRACE_T and t.GetLayer() == pcbnew.F_Cu:
            (ax, ay), (bx, by) = (T(t.GetStart().x), T(t.GetStart().y)), (T(t.GetEnd().x), T(t.GetEnd().y))
            n = max(1, int(math.hypot(bx - ax, by - ay) / 0.1))
            pts += [(ax + (bx - ax) * s / n, ay + (by - ay) * s / n) for s in range(n + 1)]
    smd_all = [p for f in board.GetFootprints() for p in f.Pads() if p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD
               and p.IsOnCopperLayer()]
    ok = [(x, y) for x, y in pts if not any(p.HitTest(pcbnew.VECTOR2I(mm(x), mm(y)), mm(0.6)) for p in others)
          and not any(p.HitTest(pcbnew.VECTOR2I(mm(x), mm(y)), mm(0.4)) for p in smd_all)
          and not any(c.HitTest(pcbnew.VECTOR2I(mm(x), mm(y)), mm(0.6)) for c in copper)]
    placed = []
    for fp in board.GetFootprints():
        if fp.GetReference() not in refs:
            continue
        for pad in fp.Pads():
            if pad.GetNetname() != netname or not ok:
                continue
            px, py = T(pad.GetPosition().x), T(pad.GetPosition().y)
            x, y = min(ok, key=lambda q: math.hypot(q[0] - px, q[1] - py))
            if any(math.hypot(x - a, y - b) < 1.5 for a, b in placed):
                continue
            v = pcbnew.PCB_VIA(board)
            v.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y))); v.SetWidth(mm(0.6)); v.SetDrill(mm(0.3))
            v.SetNet(net); v.SetLocked(True)
            board.Add(v)
            placed.append((x, y))
            print(f'  {netname} tap via at {x:.2f},{y:.2f} for {fp.GetReference()}-{pad.GetNumber()}')
    if not ok:
        print(f'  no clear spot on a top {netname} track')


def fanout_gnd(board, netname='GND', refs=None):
    """(Any net via `netname`/`refs`: then the top-pour test is skipped.) Give every new bottom GND pad its own via to the top GND pour (short 0.3 mm stub, via 0.6/0.3), placed before
    routing and locked, so the bottom pour's islands don't depend on where the router leaves gaps. A spot is used
    only if the via clears other nets' copper by 0.2 mm, sits inside the top GND fill and off the edge and cutout."""
    T, net = pcbnew.ToMM, board.FindNet(netname)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    gnd = [z for z in board.Zones() if not z.GetIsRuleArea() and z.GetNetname() == 'GND'][0]
    top = gnd.GetFilledPolysList(FAR)   # the via must land in the other layer's GND fill
    e = board.GetBoardEdgesBoundingBox()
    ex0, ey0, ex1, ey1 = (T(v) for v in (e.GetX(), e.GetY(), e.GetRight(), e.GetBottom()))
    others = [p for f in board.GetFootprints() for p in f.Pads() if p.GetNetname() != netname and p.IsOnCopperLayer()]
    copper = [t for t in board.GetTracks() if t.GetNetname() != netname]
    smd_all = [p for f in board.GetFootprints() for p in f.Pads() if p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD
               and p.IsOnCopperLayer()]

    def clear(pt, r):
        return not any(p.HitTest(pt, mm(r)) for p in others) and not any(t.HitTest(pt, mm(r)) for t in copper)

    added = 0
    for fp in board.GetFootprints():
        if fp.GetReference() not in (refs or dict(TARGETS)):
            continue
        for pad in fp.Pads():
            if pad.GetNetname() != netname:
                continue
            px, py = T(pad.GetPosition().x), T(pad.GetPosition().y)
            best = None
            for d in (0.9, 1.1, 1.3, 1.6, 2.0):
                for k in range(16):
                    a = k * 3.14159265 / 8
                    x, y = px + d * math.cos(a), py + d * math.sin(a)
                    if not (ex0 + 0.9 < x < ex1 - 0.9 and ey0 + 0.9 < y < ey1 - 0.9):
                        continue
                    if CUTOUT[0] - 0.3 < x < CUTOUT[2] + 0.3 and CUTOUT[1] - 0.3 < y < CUTOUT[3] + 0.3:
                        continue
                    pt = pcbnew.VECTOR2I(mm(x), mm(y))
                    ring = [pcbnew.VECTOR2I(mm(x + 0.4 * math.cos(b * math.pi / 4)), mm(y + 0.4 * math.sin(b * math.pi / 4)))
                            for b in range(8)] + [pt]
                    if (netname == 'GND' and not all(top.Contains(q) for q in ring)) or not clear(pt, 0.3 + 0.3) \
                            or any(q.HitTest(pt, mm(0.3 + 0.1)) for q in smd_all):
                        continue
                    # the stub (0.3 mm wide) from pad to via must clear other copper too
                    if not all(clear(pcbnew.VECTOR2I(mm(px + (x - px) * s / 6), mm(py + (y - py) * s / 6)), 0.15 + 0.22)
                               for s in range(1, 6)):
                        continue
                    best = pt
                    break
                if best:
                    break
            if not best:
                print(f'  no GND fan-out spot for {fp.GetReference()}-{pad.GetNumber()}')
                continue
            v = pcbnew.PCB_VIA(board)
            v.SetPosition(best); v.SetWidth(mm(0.6)); v.SetDrill(mm(0.3)); v.SetNet(net); v.SetLocked(True)
            board.Add(v)
            t = pcbnew.PCB_TRACK(board)
            t.SetStart(pad.GetPosition()); t.SetEnd(best); t.SetWidth(mm(0.3)); t.SetLayer(CU)
            t.SetNet(net); t.SetLocked(True)
            board.Add(t)
            added += 1
    print(f'GND fan-out: {added} vias')


def join_gnd_pieces(board):
    """Join GND pour pieces that vias and through-hole pads don't connect to the main pour: one via where a piece
    overlaps the main pour on the other layer, clear of other nets and holes. SMD pads and tracks also join pieces, so
    this can add a via between pieces that were already joined; that only adds stitching. Returns vias added."""
    T, net = pcbnew.ToMM, board.FindNet('GND')
    z = [q for q in board.Zones() if not q.GetIsRuleArea() and q.GetNetname() == 'GND'][0]
    pieces = []
    for k, L in enumerate((pcbnew.F_Cu, pcbnew.B_Cu)):
        f = z.GetFilledPolysList(L)
        for i in range(f.OutlineCount()):
            sp = pcbnew.SHAPE_POLY_SET(); sp.AddOutline(f.Outline(i))
            pieces.append((k, sp, f.Outline(i).BBox()))
    par = list(range(len(pieces)))

    def find(a):
        while par[a] != a:
            a = par[a]
        return a
    links = [t.GetPosition() for t in board.GetTracks() if t.GetNetname() == 'GND' and t.Type() == pcbnew.PCB_VIA_T]
    links += [p.GetPosition() for f in board.GetFootprints() for p in f.Pads()
              if p.GetNetname() == 'GND' and p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH]
    for pos in links:
        hit = [k for k, (_, sp, _) in enumerate(pieces) if sp.Contains(pos)]
        for k in hit[1:]:
            par[find(k)] = find(hit[0])
    groups = {}
    for k in range(len(pieces)):
        groups.setdefault(find(k), []).append(k)
    main = max(groups.values(), key=lambda ks: sum(pieces[k][1].Area() for k in ks))
    others = [p for f in board.GetFootprints() for p in f.Pads() if p.GetNetname() != 'GND' and p.IsOnCopperLayer()]
    copper = [t for t in board.GetTracks() if t.GetNetname() != 'GND']
    holes = [p for f in board.GetFootprints() for p in f.Pads() if p.GetDrillSize().x > 0 and p.GetNetname() != 'GND']

    def ok(pt):
        if any(p.HitTest(pt, mm(0.55)) for p in others) or any(t.HitTest(pt, mm(0.55)) for t in copper):
            return False
        return all(math.hypot(T(pt.x - h.GetPosition().x), T(pt.y - h.GetPosition().y)) >
                   T(h.GetDrillSize().x) / 2 + 0.6 for h in holes)
    added = 0
    for ks in groups.values():
        if ks is main or sum(pieces[k][1].Area() for k in ks) / 1e12 < 3.0:
            continue
        done = False
        for k in ks:
            layer, sp, bb = pieces[k]
            targets = [pieces[m][1] for m in main if pieces[m][0] != layer]
            for fx in [i / 20 for i in range(1, 20)]:
                for fy in [i / 20 for i in range(1, 20)]:
                    pt = pcbnew.VECTOR2I(int(bb.GetX() + bb.GetWidth() * fx), int(bb.GetY() + bb.GetHeight() * fy))
                    ring = [pcbnew.VECTOR2I(pt.x + dx, pt.y + dy) for dx, dy in
                            [(0, 0), (mm(0.35), 0), (-mm(0.35), 0), (0, mm(0.35)), (0, -mm(0.35))]]
                    if all(sp.Contains(q) for q in ring) and any(all(t.Contains(q) for q in ring) for t in targets) \
                            and ok(pt):
                        v = pcbnew.PCB_VIA(board)
                        v.SetPosition(pt); v.SetWidth(mm(0.6)); v.SetDrill(mm(0.3)); v.SetNet(net)
                        board.Add(v); added += 1; done = True
                        print(f'  GND join via at {T(pt.x):.2f},{T(pt.y):.2f}')
                        break
                if done:
                    break
            if done:
                break
        if not done:
            # no overlap to drop a via in: route a GND track from the piece to the main pour (finisher's A*)
            import finish_routes as fr
            grid = fr.Grid(board)
            lay = {0: pcbnew.F_Cu, 1: pcbnew.B_Cu}

            def cells(idx):
                out = set()
                for k in idx:
                    layer, sp, bb = pieces[k]
                    for i, j in grid.cells_near(bb, 0):
                        if sp.Contains(grid.pt(i, j)):
                            out.add((lay[layer], i, j))
                return out
            start, goal = cells(ks), cells(main)
            bt, bv = grid.blocked('GND', fr.W / 2), grid.blocked('GND', fr.VIA / 2)
            path = fr.astar(grid, start, goal, bt, bv)
            if path:
                fr.add_path(board, grid, 'GND', path, lock=True)
                added += 1
                print(f'  GND join track, {len(path) * fr.G:.1f} mm, from a {sum(pieces[k][1].Area() for k in ks) / 1e12:.0f} mm2 piece')
            else:
                print(f'  GND piece of {sum(pieces[k][1].Area() for k in ks) / 1e12:.0f} mm2 could not be joined')
    print(f'joined {added} GND pour pieces')
    return added


def stitch_islands(board):
    """Add a GND via to each bottom GND pour island that has no via or GND through-hole pad, at a point where the
    top GND pour is also present and the via clears everything. Returns the number of vias added."""
    gnd = [z for z in board.Zones() if not z.GetIsRuleArea() and z.GetNetname() == 'GND'][0]
    net = board.FindNet('GND')
    bottom, top = gnd.GetFilledPolysList(pcbnew.B_Cu), gnd.GetFilledPolysList(pcbnew.F_Cu)
    anchors = [t.GetPosition() for t in board.GetTracks() if t.Type() == pcbnew.PCB_VIA_T and t.GetNetname() == 'GND']
    anchors += [p.GetPosition() for f in board.GetFootprints() for p in f.Pads()
                if p.GetNetname() == 'GND' and p.GetAttribute() != pcbnew.PAD_ATTRIB_SMD]
    added = 0
    for i in range(bottom.OutlineCount()):
        island = pcbnew.SHAPE_POLY_SET(); island.AddOutline(bottom.Outline(i))
        if any(island.Contains(a) for a in anchors):
            continue
        bb = bottom.Outline(i).BBox()
        done = False
        for fx in [k / 10 for k in range(1, 10)]:
            for fy in [k / 10 for k in range(1, 10)]:
                pt = pcbnew.VECTOR2I(int(bb.GetX() + bb.GetWidth() * fx), int(bb.GetY() + bb.GetHeight() * fy))
                # via pad 0.6 mm: its whole pad must sit inside both pours
                ring = [pcbnew.VECTOR2I(pt.x + dx, pt.y + dy) for dx, dy in
                        [(0, 0), (mm(0.35), 0), (-mm(0.35), 0), (0, mm(0.35)), (0, -mm(0.35))]]
                if all(island.Contains(q) and top.Contains(q) for q in ring):
                    v = pcbnew.PCB_VIA(board)
                    v.SetPosition(pt); v.SetWidth(mm(0.6)); v.SetDrill(mm(0.3)); v.SetNet(net)
                    board.Add(v); added += 1; done = True
                    break
            if done:
                break
    print(f'stitched {added} bottom GND islands')
    return added


def route_board(board, path, td):
    dsn, ses = os.path.join(td, 'b.dsn'), os.path.join(td, 'b.ses')
    # Route with 0.25 mm clearance so that widening necked tracks afterwards (below) still clears 0.2 mm
    nc = board.GetDesignSettings().m_NetSettings.GetDefaultNetclass()
    clearance = nc.GetClearance()
    nc.SetClearance(mm(float(os.environ.get('ROUTE_CLEARANCE', '0.25'))))
    pcbnew.ExportSpecctraDSN(board, dsn)
    nc.SetClearance(clearance)
    r = subprocess.run(['java', '-Djava.awt.headless=true', '-jar', FREEROUTING, '-de', dsn, '-do', ses, '-mp', os.environ.get('PASSES', '40'),
                        '--gui.enabled=false', '--router.automatic_neckdown=false'], capture_output=True, text=True, timeout=1200)
    open(os.path.join(REPO, 'work/gen/freerouting.log'), 'w').write(r.stdout + r.stderr)
    tail = '\n'.join((r.stdout + r.stderr).splitlines()[-6:])
    print('freerouting:', tail)
    if not os.path.exists(ses) or os.path.getsize(ses) < 100:
        sys.exit('freerouting wrote no session')
    pcbnew.ImportSpecctraSES(board, ses)
    # Freerouting necks tracks down (0.15-0.19 mm) at small pads; the board minimum is 0.2 mm. Widen them back;
    # DRC then shows whether clearance still holds.
    thin = [t for t in board.GetTracks() if t.Type() == pcbnew.PCB_TRACE_T and not t.IsLocked()
            and t.GetWidth() < mm(0.2)]
    for t in thin:
        t.SetWidth(mm(0.2))
    print(f'widened {len(thin)} necked-down tracks to 0.2 mm')
    board.Save(path)


if __name__ == '__main__':
    main(route='--no-route' not in sys.argv)
