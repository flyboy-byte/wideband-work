"""Pure geometry helpers; no board mutation or pcbnew dependency."""
import math


def cells(start, end, step):
    """Midpoint quadrature with exact length weights and endpoint coordinates."""
    length = math.dist(start, end)
    if not length:
        return []
    count = max(1, math.ceil(length / step))
    def point(i):
        return tuple(a + (b-a)*i/count for a, b in zip(start, end))
    return [(point(i), point(i+1), point(i+.5), length/count) for i in range(count)]


def uncovered_component(edges):
    """Largest summed uncovered component, not a longest simple path.

    Coordinates rounded to KiCad's nanometre grid. Layers intentionally ignored
    at coincident endpoints: conservative joining, including possible vias.
    Branch lengths are summed. Mid-segment junctions must already be split;
    this is a sampled track heuristic, not an impedance/current-path solver.
    """
    parent, weights = {}, []
    def key(p):
        return tuple(round(x * 1e6) for x in p)
    def root(p):
        parent.setdefault(p, p)
        while parent[p] != p:
            parent[p] = parent[parent[p]]
            p = parent[p]
        return p
    for a, b, length in edges:
        a, b = key(a), key(b)
        ra, rb = root(a), root(b)
        parent[rb] = ra
        weights.append((a, length))
    groups = {}
    for a, length in weights:
        groups.setdefault(root(a), []).append(length)
    return max((math.fsum(v) for v in groups.values()), default=0.)
