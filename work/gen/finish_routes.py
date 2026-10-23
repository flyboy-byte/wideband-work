"""Finisher: route the connections Freerouting leaves open, with a plain two-layer grid router (A*, 0.1 mm grid).

Freerouting completes all but 1-3 connections on this crowded bottom side, and which ones differs with every
placement (runs r10-r16, 2026-10-23). This routes each remaining connection between the two items DRC names, keeping
`CLEAR` from other nets' pads, tracks and vias, `EDGE` from the board edge and module cutout, and out of rule areas
that forbid tracks or vias. Pours are not obstacles: they refill around new copper. DRC judges the result afterwards.

    finish(board, pcb_path)   # pcb_path: the board as saved, so kicad-cli can list the open connections
"""
import heapq, json, math, os, subprocess, tempfile

import pcbnew

G = 0.1           # grid, mm
W = 0.25          # track width, mm
CLEAR = 0.25      # copper clearance: board rule 0.2 + 0.05 for grid rounding and diagonal corners, mm
EDGE = 0.5        # copper to edge (board rule), mm
VIA, DRILL = 0.6, 0.3
VIA_COST = 2.0    # mm of track a via is worth
LAYERS = (pcbnew.F_Cu, pcbnew.B_Cu)
T = pcbnew.ToMM


def mm(v):
    return pcbnew.FromMM(v)


def open_connections(pcb_path):
    """[(net, (x, y), (x, y))] for non-GND unconnected pairs, from kicad-cli DRC."""
    with tempfile.TemporaryDirectory() as td:
        out = os.path.join(td, 'd.json')
        subprocess.run(['kicad-cli', 'pcb', 'drc', '--format', 'json', '-o', out, pcb_path], capture_output=True)
        d = json.load(open(out))
    pairs = []
    for u in d.get('unconnected_items', []):
        items = u['items']
        if len(items) != 2:
            continue
        net = items[0]['description'].split('[', 1)[-1].split(']', 1)[0]
        if net == 'GND' or 'Zone' in items[0]['description'] or 'Zone' in items[1]['description']:
            continue
        pairs.append((net, (items[0]['pos']['x'], items[0]['pos']['y']), (items[1]['pos']['x'], items[1]['pos']['y'])))
    return pairs


class Grid:
    def __init__(self, board):
        self.board = board
        e = board.GetBoardEdgesBoundingBox()
        self.x0, self.y0 = T(e.GetX()), T(e.GetY())
        self.nx, self.ny = int(T(e.GetWidth()) / G) + 1, int(T(e.GetHeight()) / G) + 1
        self.edges = [d for d in board.GetDrawings() if d.GetLayer() == pcbnew.Edge_Cuts]
        self.edges += [g for f in board.GetFootprints() for g in f.GraphicalItems() if g.GetLayer() == pcbnew.Edge_Cuts]
        outline = pcbnew.SHAPE_POLY_SET()
        board.GetBoardPolygonOutlines(outline, True)
        self.outline = outline
        self.keepouts = [z for z in board.Zones() if z.GetIsRuleArea() and z.GetZoneName() not in os.environ.get('FINISH_IGNORE', 'top_no_new_tracks_1').split(',')]

    def pt(self, i, j):
        return pcbnew.VECTOR2I(mm(self.x0 + i * G), mm(self.y0 + j * G))

    def cells_near(self, bbox, margin):
        i0 = max(0, int((T(bbox.GetX()) - margin - self.x0) / G))
        j0 = max(0, int((T(bbox.GetY()) - margin - self.y0) / G))
        i1 = min(self.nx - 1, int((T(bbox.GetRight()) + margin - self.x0) / G) + 1)
        j1 = min(self.ny - 1, int((T(bbox.GetBottom()) + margin - self.y0) / G) + 1)
        for i in range(i0, i1 + 1):
            for j in range(j0, j1 + 1):
                yield i, j

    def blocked(self, net, r):
        """Per layer, the set of cells where copper of radius r on `net` would break a rule."""
        out = {l: set() for l in LAYERS}
        items = [p for f in self.board.GetFootprints() for p in f.Pads() if p.IsOnCopperLayer()]
        items += list(self.board.GetTracks())
        for it in items:
            if it.GetNetname() == net and net:
                continue
            for l in LAYERS:
                if not it.IsOnLayer(l):
                    continue
                for i, j in self.cells_near(it.GetBoundingBox(), r + CLEAR):
                    if (i, j) not in out[l] and it.HitTest(self.pt(i, j), mm(r + CLEAR)):
                        out[l].add((i, j))
        # board edge and cutout: every cell closer than EDGE + r to an Edge.Cuts line, or outside the board
        edge_cells = set()
        for d in self.edges:
            for i, j in self.cells_near(d.GetBoundingBox(), r + EDGE):
                if d.HitTest(self.pt(i, j), mm(r + EDGE)):
                    edge_cells.add((i, j))
        for i in range(self.nx):
            for j in range(self.ny):
                if not self.outline.Contains(self.pt(i, j)):
                    edge_cells.add((i, j))
        for l in LAYERS:
            out[l] |= edge_cells
        return out

    def rule_area_cells(self, kind):
        out = {l: set() for l in LAYERS}
        for z in self.keepouts:
            if (kind == 'track' and not z.GetDoNotAllowTracks()) or (kind == 'via' and not z.GetDoNotAllowVias()):
                continue
            poly = z.Outline()
            for l in LAYERS:
                if not z.IsOnLayer(l):
                    continue
                for i, j in self.cells_near(z.GetBoundingBox(), 0):
                    if poly.Contains(self.pt(i, j)):
                        out[l].add((i, j))
        return out


def item_cells(board, grid, net, xy):
    """(layer, i, j) cells covered by the copper item of `net` at DRC position xy (a pad, track or via)."""
    p = pcbnew.VECTOR2I(mm(xy[0]), mm(xy[1]))
    items = [q for f in board.GetFootprints() for q in f.Pads() if q.GetNetname() == net]
    items += [t for t in board.GetTracks() if t.GetNetname() == net]
    hit = [it for it in items if it.HitTest(p, mm(0.05))]
    if not hit:
        return set()
    it = hit[0]
    cells = set()
    for l in LAYERS:
        if it.IsOnLayer(l):
            for i, j in grid.cells_near(it.GetBoundingBox(), 0):
                if it.HitTest(grid.pt(i, j), 0):
                    cells.add((l, i, j))
    return cells


def astar(grid, start, goal, block_track, block_via):
    gl = list(goal)
    gx = sum(c[1] for c in gl) / len(gl)
    gy = sum(c[2] for c in gl) / len(gl)

    def h(i, j):
        return math.hypot(i - gx, j - gy) * G * 0.9

    dist, prev, pq = {}, {}, []
    for c in start:
        dist[c] = 0.0
        heapq.heappush(pq, (h(c[1], c[2]), 0.0, c))
    steps = [(1, 0, G), (-1, 0, G), (0, 1, G), (0, -1, G),
             (1, 1, G * 1.4142), (1, -1, G * 1.4142), (-1, 1, G * 1.4142), (-1, -1, G * 1.4142)]
    while pq:
        f, d, c = heapq.heappop(pq)
        if d > dist.get(c, 1e9):
            continue
        if c in goal:
            path = [c]
            while path[-1] in prev:
                path.append(prev[path[-1]])
            return path[::-1]
        l, i, j = c
        nbrs = []
        for di, dj, cost in steps:
            n = (l, i + di, j + dj)
            if 0 <= n[1] < grid.nx and 0 <= n[2] < grid.ny and ((n[1], n[2]) not in block_track[l] or n in goal):
                nbrs.append((n, cost))
        other = LAYERS[1] if l == LAYERS[0] else LAYERS[0]
        if all((i, j) not in block_via[k] for k in LAYERS):
            nbrs.append(((other, i, j), VIA_COST))
        for n, cost in nbrs:
            nd = d + cost
            if nd < dist.get(n, 1e9):
                dist[n] = nd
                prev[n] = c
                heapq.heappush(pq, (nd + h(n[1], n[2]), nd, n))
    return None


def add_path(board, grid, net, path):
    """Track segments (collinear runs merged) and vias along a grid path."""
    n = board.FindNet(net)
    added = 0
    run = [path[0]]

    def flush(run):
        if len(run) < 2:
            return 0
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(grid.pt(run[0][1], run[0][2])); t.SetEnd(grid.pt(run[-1][1], run[-1][2]))
        t.SetWidth(mm(W)); t.SetLayer(run[0][0]); t.SetNet(n)
        board.Add(t)
        return 1

    for a, b in zip(path, path[1:]):
        if a[0] != b[0]:
            added += flush(run)
            v = pcbnew.PCB_VIA(board)
            v.SetPosition(grid.pt(a[1], a[2])); v.SetWidth(mm(VIA)); v.SetDrill(mm(DRILL)); v.SetNet(n)
            board.Add(v)
            run = [b]
            continue
        if len(run) >= 2:
            d0 = (run[-1][1] - run[-2][1], run[-1][2] - run[-2][2])
            if (b[1] - a[1], b[2] - a[2]) != d0:
                added += flush(run)
                run = [a]
        run.append(b)
    added += flush(run)
    return added


def finish(board, pcb_path):
    pairs = open_connections(pcb_path)
    if not pairs:
        print('finisher: nothing open')
        return 0
    grid = Grid(board)
    keep_track, keep_via = grid.rule_area_cells('track'), grid.rule_area_cells('via')
    done = 0
    for net, a, b in pairs:
        start, goal = item_cells(board, grid, net, a), item_cells(board, grid, net, b)
        if not start or not goal:
            print(f'finisher: {net}: could not find the items at {a} / {b}')
            continue
        bt = grid.blocked(net, W / 2)
        bv = grid.blocked(net, VIA / 2)
        for l in LAYERS:
            bt[l] |= keep_track[l]
            bv[l] |= keep_via[l]
        path = astar(grid, start, goal, bt, bv)
        if not path:
            print(f'finisher: {net}: no path')
            continue
        segs = add_path(board, grid, net, path)
        vias = sum(1 for p, q in zip(path, path[1:]) if p[0] != q[0])
        print(f'finisher: {net}: {segs} segments, {vias} vias, {len(path) * G:.1f} mm')
        done += 1
    return done
