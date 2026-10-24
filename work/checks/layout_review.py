#!/usr/bin/env python3
"""Measure the side effects of a layout change that DRC doesn't judge (AGENTS.md rule 8, docs/carrier.md "Layout review
checklist"). Prints numbers; the review triggers below are where a human (or model) has to look and reason, not pass marks.

  python3 checks/layout_review.py [--pcb FILE] [-v]

1. Coupling: closest approach and side-by-side length between noisy nets and sensitive nets, same layer and stacked
   on opposite layers. Includes upstream net pairs: new routing can extend those nets.
2. Return path: share of each new signal track that has filled GND copper on the other layer underneath it, and the
   largest sampled uncovered component (conservative branch sum, not longest path).
3. GND pour: filled pieces per layer, and GND vias in the new strip with the farthest point of the strip's pour from one.
Exit 1 if a review trigger fires (so run_all.py shows it), 0 otherwise.
"""
import math, os, sys

import pcbnew
from layout_metrics import cells, uncovered_component

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
PCB = sys.argv[sys.argv.index('--pcb') + 1] if '--pcb' in sys.argv else \
    os.path.join(REPO, 'hardware/board_carrier/board_carrier.kicad_pcb')
VERBOSE = '-v' in sys.argv

# Noisy nets and why (sources: docs/analog-out.md F-facts and docs/carrier.md)
AGGRESSORS = {'/AOUT_PWM': 'SEL_1 PWM, 46.9 kHz, 3.3 V edges', '/AOUT_BUF': 'buffered PWM, 3.0 V edges',
              '/LSU_Heater-': 'heater low-side switch, amps', '/CAN_H': 'CAN 500 kbit/s', '/CAN_L': 'CAN 500 kbit/s'}
# Sensitive nets: the sensor's pump/Nernst/trim lines (microamps, millivolts) and our filtered analog nodes
VICTIMS = {'/LSU_Ip': 'pump current', '/LSU_Vm': 'virtual ground', '/LSU_Un': 'Nernst cell', '/LSU_Rtrim': 'trim',
           '/AOUT_F1': 'first filtered PWM node', '/AOUT_F2': 'filtered PWM, 3.3k source', '/AOUT_INN': 'op-amp IN-', '/VREF3': '3.000 V reference',
           '/AOUT': 'output (clamp node)', '/AOUT_J': 'output at J3-5'}
NEW_SIGNALS = ['/AOUT_PWM', '/AOUT_BUF', '/AOUT_F1', '/AOUT_F2', '/AOUT_INN', '/AOUT_OA', '/AOUT', '/AOUT_J', '/VREF3']
# (TEST_SEL2 is left out: a strap read once at power-up, docs/firmware.md; noise on it doesn't matter)
# Review triggers (where to look harder; chosen as review points, not from a standard: INFERRED)
NEAR_MM, NEAR_LEN_MM = 0.5, 3.0     # same layer: edge gap under 0.5 mm for more than 3 mm of run
STACK_LEN_MM = 2.0                  # opposite layers: more than 2 mm running on top of each other
STRIP_Y0 = 91.25                    # the grown strip starts here (gen_carrier_pcb.py GROW)
STEP = 0.25

T = pcbnew.ToMM
board = pcbnew.LoadBoard(PCB)
tracks = [t for t in board.GetTracks() if t.Type() == pcbnew.PCB_TRACE_T]


def samples(t):
    (x0, y0), (x1, y1) = (T(t.GetStart().x), T(t.GetStart().y)), (T(t.GetEnd().x), T(t.GetEnd().y))
    return cells((x0, y0), (x1, y1), STEP)


def seg_dist(p, t):
    (ax, ay), (bx, by) = (T(t.GetStart().x), T(t.GetStart().y)), (T(t.GetEnd().x), T(t.GetEnd().y))
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    u = 0 if L == 0 else max(0, min(1, ((p[0] - ax) * dx + (p[1] - ay) * dy) / L))
    return math.hypot(p[0] - (ax + u * dx), p[1] - (ay + u * dy))


by_net = {}
for t in tracks:
    by_net.setdefault(t.GetNetname(), []).append(t)

triggers = []
print('1. Coupling (noisy -> sensitive): closest edge gap, length within 0.5 mm same layer, length stacked on the other layer')
for a in AGGRESSORS:
    for v in VICTIMS:
        if a == v:
            continue
        gap, near, stack = 99.0, 0.0, 0.0
        for ta in by_net.get(a, []):
            wa = T(ta.GetWidth()) / 2
            for _, _, p, weight in samples(ta):
                same = [seg_dist(p, tv) - wa - T(tv.GetWidth()) / 2 for tv in by_net.get(v, []) if tv.GetLayer() == ta.GetLayer()]
                other = [seg_dist(p, tv) - wa - T(tv.GetWidth()) / 2 for tv in by_net.get(v, []) if tv.GetLayer() != ta.GetLayer()]
                if same:
                    g = min(same)
                    gap = min(gap, g)
                    if g < NEAR_MM:
                        near += weight
                if other and min(other) < 0:
                    stack += weight
        if gap < 99 or stack:
            flag = near > NEAR_LEN_MM or stack > STACK_LEN_MM
            if flag:
                triggers.append(f'coupling {a} -> {v}')
            if flag or VERBOSE or gap < 1.0:
                print(f'  {"REVIEW " if flag else "       "}{a:14s} -> {v:12s} gap {gap:5.2f} mm  near {near:4.1f} mm  stacked {stack:4.1f} mm')

print('2. Return path: share of each new signal track with filled GND on the other layer under it, or on its own layer')
print('   within 0.5 mm on both sides (coplanar); largest uncovered component, branch lengths summed')
print('   sampled track heuristic only; pads, unsplit junctions, impedance and actual current distribution are not solved')
gnd = [z for z in board.Zones() if not z.GetIsRuleArea() and z.GetNetname() == 'GND']
for name in NEW_SIGNALS:
    lengths, covered, gaps = [], [], []
    for t in by_net.get(name, []):
        own = t.GetLayer()
        other = pcbnew.B_Cu if own == pcbnew.F_Cu else pcbnew.F_Cu
        (ax, ay), (bx, by) = (T(t.GetStart().x), T(t.GetStart().y)), (T(t.GetEnd().x), T(t.GetEnd().y))
        L = math.hypot(bx - ax, by - ay) or 1
        nx, ny = -(by - ay) / L, (bx - ax) / L          # unit normal
        off = T(t.GetWidth()) / 2 + 0.5

        def filled(layer, x, y):
            return any(z.IsOnLayer(layer) and z.HitTestFilledArea(layer, pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))
                       for z in gnd)
        for start, end, (x, y), weight in samples(t):
            lengths.append(weight)
            hit = filled(other, x, y) or (filled(own, x + nx * off, y + ny * off) and filled(own, x - nx * off, y - ny * off))
            if hit:
                covered.append(weight)
            else:
                gaps.append((start, end, weight))
    if lengths:
        total = math.fsum(lengths)
        share = 100 * math.fsum(covered) / total
        worst = uncovered_component(gaps)
        flag = worst > 5.0
        if flag:
            triggers.append(f'return path {name}')
        print(f'  {"REVIEW " if flag else "       "}{name:12s} {total:5.1f} mm of track, {share:5.1f} % over GND, uncovered component {worst:4.1f} mm')

print('3. GND pour')
for layer, lname in ((pcbnew.F_Cu, 'F.Cu'), (pcbnew.B_Cu, 'B.Cu')):
    pieces = sum(z.GetFilledPolysList(layer).OutlineCount() for z in gnd if z.IsOnLayer(layer))
    print(f'  {lname}: {pieces} filled GND piece(s)')
vias = [(T(t.GetPosition().x), T(t.GetPosition().y)) for t in board.GetTracks()
        if t.Type() == pcbnew.PCB_VIA_T and t.GetNetname() == 'GND' and T(t.GetPosition().y) > STRIP_Y0]
e = board.GetBoardEdgesBoundingBox()
far = 0.0
x = T(e.GetX()) + 1
while x < T(e.GetRight()) - 1:
    y = STRIP_Y0 + 1
    while y < T(e.GetBottom()) - 1:
        if any(z.HitTestFilledArea(pcbnew.B_Cu, pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))) for z in gnd):
            far = max(far, min((math.hypot(x - vx, y - vy) for vx, vy in vias), default=99))
        y += 0.5
    x += 0.5
print(f'  strip (y > {STRIP_Y0}): {len(vias)} GND vias; farthest bottom-pour point from a via {far:.1f} mm')

print(f'review triggers: {len(triggers)}' + (f' ({", ".join(triggers)})' if triggers else ''))
sys.exit(1 if triggers else 0)
