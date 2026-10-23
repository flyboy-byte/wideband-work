#!/usr/bin/env python3
"""Generate hardware/board_carrier/board_carrier.kicad_pcb: upstream's carrier plus our analog output stage.

  python3 work/gen/gen_carrier_pcb.py            place, route with Freerouting, fill zones, write the board
  python3 work/gen/gen_carrier_pcb.py --no-route place only (to look at placement)

Base = upstream's board at `master`, upgraded to KiCad 10. Every pad's net is set from the generated schematic's
netlist (work/gen/gen_carrier_sch.py writes it), so board and schematic match. New parts go on the BOTTOM side: the
board can't grow (case/case.STL is 47.5 x 44 mm outside around this 40 x 36.5 mm board) and the top is full; the case
leaves about 6 mm under the board (INFERRED from the STL's horizontal faces, work/docs/carrier.md).
Upstream's tracks and vias are locked before routing, so Freerouting only adds the new connections.
"""
import os, re, shutil, subprocess, sys, tempfile, xml.etree.ElementTree as ET

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
TARGETS = [
    ('U6',  (67.6, 76.8)),   # LM2904, right of the cutout
    ('C15', (64.4, 75.8)),   # Cf, next to its pins
    ('R6',  (64.4, 77.8)),
    ('R7',  (64.4, 79.8)),
    ('R8',  (60.2, 72.0)),   # output side, toward J3-5
    ('D3',  (60.2, 74.6)),
    ('D4',  (60.2, 77.2)),
    ('C17', (70.0, 80.6)),   # op-amp bypass, at pin 8
    ('JP1', (50.2, 80.6)),   # TEST jumper, next to U3-4
    ('R3',  (52.6, 80.6)),   # pull-down on the buffer input
    ('U4',  (55.4, 81.2)),   # buffer
    ('U5',  (58.8, 81.2)),   # REF3030
    ('C12', (61.4, 81.2)),   # VREF3 cap
    ('C11', (63.4, 81.2)),   # REF input cap
    ('R4',  (55.4, 84.2)),   # RC chain
    ('C13', (57.4, 84.2)),
    ('R5',  (59.4, 84.2)),
    ('C14', (61.4, 84.2)),
    ('R9',  (50.4, 88.0)),   # supply from module pad 7
    ('D5',  (53.6, 88.4)),
    ('C16', (57.6, 88.4)),   # 1206
    ('R10', (52.4, 68.6)),   # CAN terminator, near the CAN pins
    ('JP2', (56.0, 68.6)),
]
CLEAR = 0.25                 # mm between a courtyard and any obstacle
AREA = (48.8, 67.3, 71.2, 90.5)   # bottom placement area: between the module header rows, keeps the pin labels clear
# Upstream bottom tracks that cross the free area and carry little current; deleted so the router can redo them:
# the battery-sense branch to module pad 7 (0.2 mm) and the module's +5V feed (0.5 mm, about 50 mA).
# The 0.5 mm LSU_Heater+ bottom path (J3-4 to the regulator side) is a parallel supply path and stays.
REROUTE = [('/LSU_Heater+', (47.0, 78.0, 56.0, 87.0)), ('+5V', (45.5, 84.0, 61.0, 91.0))]
CUTOUT = (48.41, 72.49, 57.11, 78.65)   # module cutout 48.76-56.76 x 72.84-78.30, grown 0.35 mm
# (0.5 mm would cover upstream's own top tracks, which pass about 0.4 mm from the cutout)
EDGE_KEEP = 0.6                          # mm strip inside the board edge with no new tracks or vias (rule: 0.5)
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
    """(x0, y0, x1, y1) in mm of the footprint's bottom courtyard, grown by CLEAR."""
    bb = fp.GetCourtyard(pcbnew.B_CrtYd).BBox()
    return (pcbnew.ToMM(bb.GetX()) - CLEAR, pcbnew.ToMM(bb.GetY()) - CLEAR,
            pcbnew.ToMM(bb.GetRight()) + CLEAR, pcbnew.ToMM(bb.GetBottom()) + CLEAR)


def obstacle_shapes(board):
    """Boxes (x0, y0, x1, y1) and circles (x, y, r) in mm that bottom parts must keep out of."""
    T = pcbnew.ToMM
    boxes, circles = [], []
    for fp in board.GetFootprints():
        for g in fp.GraphicalItems():
            if g.GetLayer() in (pcbnew.B_CrtYd, pcbnew.Edge_Cuts):
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
        elif t.GetLayer() == pcbnew.B_Cu:
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


def main(route=True):
    nets, comps = netlist()
    td = tempfile.mkdtemp()
    base = os.path.join(td, 'board_carrier.kicad_pcb')
    open(base, 'w').write(subprocess.run(['git', '-C', REPO, 'show', 'master:hardware/board_carrier/board_carrier.kicad_pcb'],
                                         capture_output=True, text=True, check=True).stdout)
    subprocess.run(['kicad-cli', 'pcb', 'upgrade', base], capture_output=True, check=True)
    board = pcbnew.LoadBoard(base)

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

    # New footprints on the bottom, placed one by one at the nearest legal spot to their target
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

    # Stray GND stitching vias under new parts: remove (they joined the top GND pour to a bottom with no copper)
    new_boxes = []
    for fp in board.GetFootprints():
        if fp.GetReference() in dict(TARGETS):
            bb = fp.GetCourtyard(pcbnew.B_CrtYd).BBox()
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
    # No new top-side tracks over upstream's 12V_RAW pour (one cut it in two on an earlier run; bottom-only routing
    # left connections unfinished). Vias are still allowed: a via only punches a hole in a pour.
    z = pcbnew.ZONE(board)
    z.SetIsRuleArea(True)
    z.SetDoNotAllowTracks(True)
    z.SetDoNotAllowVias(False)
    z.SetDoNotAllowZoneFills(False)
    z.SetDoNotAllowPads(False)
    z.SetDoNotAllowFootprints(False)
    z.SetLayer(pcbnew.F_Cu)
    o = z.Outline(); o.NewOutline()
    v12 = [q for q in board.Zones() if not q.GetIsRuleArea() and q.GetNetname() == '12V_RAW'][0].GetBoundingBox()
    v12.Inflate(mm(0.5))
    for x, y in [(v12.GetX(), v12.GetY()), (v12.GetRight(), v12.GetY()), (v12.GetRight(), v12.GetBottom()),
                 (v12.GetX(), v12.GetBottom())]:
        o.Append(x, y)
    z.SetZoneName('top_no_new_tracks')
    board.Add(z)

    # Design rules for the new routing: 0.25 mm default track (was 0.2, the board minimum, and the router went
    # under it); solder mask minimum web 0.1 mm (was 0.25, which flags every 0.65 mm-pitch part such as the SC-70
    # buffer; 0.1 mm is about what JLC states for green mask [FROM MEMORY, check JLC's capabilities page])
    ds = board.GetDesignSettings()
    ds.m_NetSettings.GetDefaultNetclass().SetTrackWidth(mm(0.25))
    ds.m_SolderMaskMinWidth = mm(0.1)

    # Bottom silkscreen: upstream's labels name module pads for an older module revision (TX/RX/nRESET);
    # the current module has SEL_1/SEL_2/VBatt_Sense there. Fix the labels; drop texts our parts now cover.
    relabel = {'TX': 'AOUT', 'RX': 'TEST', 'nRESET': 'VBAT', 'v1.1': 'v1.1-aout'}
    for d in list(board.GetDrawings()):
        if d.GetLayer() == pcbnew.B_SilkS and d.Type() == pcbnew.PCB_TEXT_T:
            if d.GetText() in relabel:
                d.SetText(relabel[d.GetText()])
            elif d.GetText() in ('rusEFI LSU 4.9 Controller', '12V'):
                board.Remove(d)

    board.Save(base)
    if route:
        route_board(board, base, td)
        board = pcbnew.LoadBoard(base)
    # The rule areas above only steer the router; DRC's own edge and clearance rules judge the result
    for z in [z for z in board.Zones() if z.GetIsRuleArea() and z.GetZoneName() in AIDS]:
        board.Delete(z)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    if stitch_islands(board):
        pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    board.Save(OUT)
    shutil.rmtree(td)
    print('wrote', os.path.relpath(OUT, REPO))


AIDS = {'cutout_keepout', 'top_no_new_tracks'} | {f'edge_keepout_{i}' for i in range(4)}


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
    pcbnew.ExportSpecctraDSN(board, dsn)
    r = subprocess.run(['java', '-Djava.awt.headless=true', '-jar', FREEROUTING, '-de', dsn, '-do', ses, '-mp', '40',
                        '--gui.enabled=false'], capture_output=True, text=True, timeout=1200)
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
