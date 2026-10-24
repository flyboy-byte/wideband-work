#!/usr/bin/env python3
"""Silkscreen for the new parts: readable labels where they fit, nothing over pads or other silkscreen.

  python3 work/gen/silk.py [PCB]      apply to a board file in place (default: the carrier); gen_carrier_pcb.py calls
                                      place_labels() itself, so this is for trying it on a copy

JLC's minimum legible silkscreen is 1.0 mm text with a 0.15 mm line, 0.15 mm from pads [REPORTED, JLC help center
"Capabilities", 2026-10-24]; the 0.8 mm / 0.12 mm references before were below it. The strip is too dense for 26 labels
at that size, so labels go in priority order (the solder jumpers the owner closes by hand, with their function, then
the ICs, then the rest) at the nearest free spot around the part; a label with no free spot is hidden (the assembly
render and the CPL still name every part). Upstream's own silkscreen is left as it is.
"""
import os, sys

import pcbnew

H, W = 1.0, 0.15            # text height, line width (mm)
PAD_GAP = 0.15              # from any pad
SILK_GAP = 0.1              # from other silkscreen
EDGE_GAP = 0.3
# Function labels beside the solder jumpers (what bridging them does: REQUIREMENTS bench test A1, CAN termination)
FUNCTION = {'JP1': 'TEST', 'JP2': '120R'}
# How far (mm) a label may sit from its part's courtyard: further for the jumpers' function labels and the ICs
REACH = {'JP1': 3.0, 'JP2': 3.0, 'U4': 2.4, 'U5': 2.4, 'U6': 2.4}
# A label must read as its own part's: the label's edge at least OWN_MARGIN mm closer to its own part's courtyard than to
# any other part's (a label beside the wrong part is worse than none: the owner probes by label with a meter)
OWN_MARGIN = 0.4
# Function labels that describe a group: the CAN terminator is JP2 and R10 together
GROUP = {'JP2': ['JP2', 'R10']}
PRIORITY = ['JP1', 'JP2', 'U6', 'U4', 'U5', 'R11', 'R9', 'D5', 'C16', 'D3', 'D4', 'R8', 'R6', 'R7', 'C15', 'C17', 'R3',
            'R4', 'R5', 'C11', 'C12', 'C13', 'C14', 'R10']


def _box(item, grow=0.0):
    # Text: the strokes themselves (what DRC judges); GetBoundingBox pads "120R" at 1 mm to 4.1 x 1.7 mm, strokes 3.6 x 1.15
    bb = item.GetEffectiveTextShape().BBox() if hasattr(item, 'GetEffectiveTextShape') else item.GetBoundingBox()
    T = pcbnew.ToMM
    return (T(bb.GetX()) - grow, T(bb.GetY()) - grow, T(bb.GetRight()) + grow, T(bb.GetBottom()) + grow)


def _hit(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def place_labels(board, refs=None):
    T, mm = pcbnew.ToMM, pcbnew.FromMM
    fps = {f.GetReference(): f for f in board.GetFootprints()}
    refs = [r for r in PRIORITY if r in fps] if refs is None else refs
    e = board.GetBoardEdgesBoundingBox()
    edge = (T(e.GetX()) + EDGE_GAP, T(e.GetY()) + EDGE_GAP, T(e.GetRight()) - EDGE_GAP, T(e.GetBottom()) - EDGE_GAP)

    # Obstacles: every pad (both sides' copper shows through the mask on top only for top pads, but keep clear of all
    # top-visible ones), every footprint's own silkscreen graphics, the holes, and labels we keep
    blocked = []
    for f in board.GetFootprints():
        for p in f.Pads():
            if p.IsOnLayer(pcbnew.F_Cu) or p.HasHole():
                blocked.append(_box(p, PAD_GAP))
        for g in f.GraphicalItems():
            if g.GetLayer() == pcbnew.F_SilkS:
                blocked.append(_box(g, SILK_GAP))
        if f.GetReference() not in refs:
            for fld in (f.Reference(), f.Value()):
                if fld.IsVisible() and fld.GetLayer() == pcbnew.F_SilkS:
                    blocked.append(_box(fld, SILK_GAP))
    for d in board.GetDrawings():
        if d.GetLayer() == pcbnew.F_SilkS:
            blocked.append(_box(d, SILK_GAP))
    for t in board.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T:
            blocked.append(_box(t, PAD_GAP))   # via pads are tented here, but silk over a via ring prints badly

    courts = {}
    for f in board.GetFootprints():
        bb = f.GetCourtyard(pcbnew.F_CrtYd).BBox()
        if bb.GetWidth() > 0:
            courts[f.GetReference()] = (T(bb.GetX()), T(bb.GetY()), T(bb.GetRight()), T(bb.GetBottom()))

    def gap(a, b):
        dx = max(b[0] - a[2], 0, a[0] - b[2])
        dy = max(b[1] - a[3], 0, a[1] - b[3])
        return (dx * dx + dy * dy) ** 0.5

    def try_place(text_item, owners, reach, rivals=None, margin=OWN_MARGIN):
        own = [courts[o] for o in owners if o in courts]
        cb = (min(b[0] for b in own), min(b[1] for b in own), max(b[2] for b in own), max(b[3] for b in own))
        cx, cy = (cb[0] + cb[2]) / 2, (cb[1] + cb[3]) / 2
        hw, hh = (cb[2] - cb[0]) / 2, (cb[3] - cb[1]) / 2
        others = [b for r, b in courts.items() if r not in owners and (rivals is None or r in rivals)]
        best = None
        for rot in (0, 90):
            text_item.SetTextAngleDegrees(rot)
            for step in range(0, int(reach / 0.2) + 1):
                d = 0.2 * step
                for ox, oy in ((0, -1), (0, 1), (-1, 0), (1, 0), (-1, -1), (1, -1), (-1, 1), (1, 1)):
                    text_item.SetPosition(pcbnew.VECTOR2I(mm(cx), mm(cy)))
                    b0 = _box(text_item)
                    tw, th = (b0[2] - b0[0]) / 2, (b0[3] - b0[1]) / 2
                    x = cx + ox * (hw + tw + d)
                    y = cy + oy * (hh + th + d)
                    text_item.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
                    b = _box(text_item)
                    if b[0] < edge[0] or b[1] < edge[1] or b[2] > edge[2] or b[3] > edge[3]:
                        continue
                    if any(_hit(b, o) for o in blocked):
                        continue
                    if min(gap(b, o) for o in own) + margin > min((gap(b, o) for o in others), default=99):
                        continue
                    dist = (x - cx) ** 2 + (y - cy) ** 2
                    if best is None or dist < best[0]:
                        best = (dist, x, y, rot)
                if best:
                    break
            if best and rot == 0:
                break   # prefer horizontal text when it fits
        if not best:
            return False
        _, x, y, rot = best
        text_item.SetTextAngleDegrees(rot)
        text_item.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
        blocked.append(_box(text_item, SILK_GAP))
        return True

    # Bottom side, for a function label with no room on top: directly behind its jumper (the strip's bottom has no parts
    # since r37), mirrored so it reads from below
    blocked_b = []
    for f in board.GetFootprints():
        for p in f.Pads():
            if p.IsOnLayer(pcbnew.B_Cu) or p.HasHole():
                blocked_b.append(_box(p, PAD_GAP))
    for d in board.GetDrawings():
        if d.GetLayer() == pcbnew.B_SilkS:
            blocked_b.append(_box(d, SILK_GAP))
    for t in board.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T:
            blocked_b.append(_box(t, PAD_GAP))

    def behind(text_item, fp):
        text_item.SetLayer(pcbnew.B_SilkS)
        text_item.SetMirrored(True)
        c = fp.GetPosition()
        for step in range(0, 6):
            for rot in (0, 90):
                text_item.SetTextAngleDegrees(rot)
                for ox, oy in ((0, 0), (0, -1), (0, 1), (-1, 0), (1, 0), (-1, -1), (1, -1), (-1, 1), (1, 1)):
                    if step == 0 and (ox, oy) != (0, 0):
                        continue
                    text_item.SetPosition(pcbnew.VECTOR2I(c.x + mm(0.2 * step * ox), c.y + mm(0.2 * step * oy)))
                    b = _box(text_item)
                    if b[0] < edge[0] or b[1] < edge[1] or b[2] > edge[2] or b[3] > edge[3]:
                        continue
                    if not any(_hit(b, o) for o in blocked_b):
                        blocked_b.append(_box(text_item, SILK_GAP))
                        return True
        return False

    shown, hidden = [], []
    for r in refs:
        fp = fps[r]
        jobs = []
        if r in FUNCTION:
            # A jumper gets its function instead of its reference: "TEST" says what bridging it does, "JP1" doesn't
            t = pcbnew.PCB_TEXT(board)
            t.SetText(FUNCTION[r])
            t.SetLayer(pcbnew.F_SilkS)
            board.Add(t)
            jobs.append((t, 'function'))
            fp.Reference().SetVisible(False)
        else:
            jobs.append((fp.Reference(), 'ref'))
        for item, kind in jobs:
            item.SetTextSize(pcbnew.VECTOR2I(mm(H), mm(H)))
            item.SetTextThickness(mm(W))
            item.SetKeepUpright(True)
            item.SetVisible(True)
            if kind == 'function':
                # "TEST" or "120R" names no part; the one mix-up that matters is which jumper it belongs to
                rivals = [g for j in FUNCTION if j != r for g in GROUP.get(j, [j])]
                ok = try_place(item, GROUP.get(r, [r]), REACH.get(r, 1.6), rivals, 0.5)
            else:
                ok = try_place(item, [r], REACH.get(r, 1.6))
            if ok:
                shown.append(item.GetText() if kind == 'function' else r)
            elif kind == 'function' and behind(item, fp):
                shown.append(item.GetText() + ' (bottom, behind ' + r + ')')
            elif kind == 'function':
                board.Remove(item)
                hidden.append(FUNCTION[r] + ' (function)')
            else:
                item.SetVisible(False)
                hidden.append(r)
    print(f'silkscreen: {len(shown)} labels placed ({", ".join(shown)}); hidden: {", ".join(hidden) or "none"}')
    return shown, hidden


if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), '..', '..',
                                                              'hardware/board_carrier/board_carrier.kicad_pcb')
    b = pcbnew.LoadBoard(path)
    place_labels(b)
    b.Save(path)
