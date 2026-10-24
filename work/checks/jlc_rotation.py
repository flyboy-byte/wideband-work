#!/usr/bin/env python3
"""JLC places each part with its EasyEDA footprint, whose zero rotation and origin differ from KiCad's per package
(pcb-design skill, fab-files reference). For every SMD part with an LCSC number this measures, from the EasyEDA data:

  1. the rotation correction: the turn of EasyEDA's footprint that puts each of its pads on our pad with the same pin
     function (pads are paired by pin name where both sides name them, by number otherwise: C22452 SS54 numbers its
     anode 1 where KiCad's D_SMA has the cathode as 1, so pairing by number alone would place it backwards);
  2. the origin offset left after that turn (JLC centres on EasyEDA's origin): written as a position correction;
  3. pin names: EasyEDA's symbol pin name on each pad against our schematic's pin name there (reversed diodes, ICs
     turned 180, a different pinout under the same package).

  python3 checks/jlc_rotation.py [-v] [--fetch]     writes checks/jlc_rotation.json (designator -> CPL rotation)

EasyEDA data is cached in checks/easyeda/<LCSC>.json (public part data; --fetch gets missing ones from
easyeda.com/api/products/<LCSC>/components, one request a second). Exit 1 on: a part with no data, no quarter turn that
fits clearly better than the others, an origin offset over MAX_OFFSET (2 mm: more than a land-pattern difference), or a
pad we can't pair.

Rotation sense: KiCad's, counter-clockwise seen from the top; JLC's CPL rotation is taken to be the same sense, as
KiCad's own JLC export assumes [INFERRED: JLC's placement preview before paying is the check; look at every IC and diode
there].
"""
import json, math, os, re, subprocess, sys, time, urllib.request, xml.etree.ElementTree as ET

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
PCB = os.path.join(REPO, 'hardware/board_carrier/board_carrier.kicad_pcb')
SCH = os.path.join(REPO, 'hardware/board_carrier/board_carrier.kicad_sch')
CACHE = os.path.join(HERE, 'easyeda')
OUT = os.path.join(HERE, 'jlc_rotation.json')
VERBOSE = '-v' in sys.argv
UNIT = 0.254          # EasyEDA footprint unit: 10 mil
MAX_OFFSET = 2.0      # mm; smaller offsets go into the CPL position
REPORT_OFFSET = 0.1   # mm; listed
# Pin names that mean the same, normalised (upper case, letters and digits only)
SAME = [{'VI', 'IN', 'VIN', 'INPUT'}, {'VO', 'OUT', 'VOUT', 'OUTPUT'}, {'K', 'CATHODE'}, {'A', 'ANODE'}]


def fetch(lcsc):
    path = os.path.join(CACHE, lcsc + '.json')
    if os.path.exists(path):
        return json.load(open(path))
    if '--fetch' not in sys.argv:
        return None
    os.makedirs(CACHE, exist_ok=True)
    # a browser-like user agent gets a 403 from easyeda.com's CDN; the plain one is answered (2026-10-24)
    with urllib.request.urlopen(f'https://easyeda.com/api/products/{lcsc}/components?version=6.5.42', timeout=20) as r:
        d = json.load(r)
    time.sleep(1)
    if d.get('success'):
        json.dump(d, open(path, 'w'))
        return d
    return None


def easyeda_pads(d):
    pk = d['result']['packageDetail']['dataStr']
    ox, oy = float(pk['head']['x']), float(pk['head']['y'])
    pads = {}
    for s in pk['shape']:
        if s.startswith('PAD~'):
            f = s.split('~')
            pads[f[8]] = ((float(f[2]) - ox) * UNIT, (float(f[3]) - oy) * UNIT)
    return pads


def easyeda_cathode(d, pads):
    """The pad nearest EasyEDA's cathode band: the top-silkscreen solid region (layer 3) on two-pin diode footprints."""
    pk = d['result']['packageDetail']['dataStr']
    ox, oy = float(pk['head']['x']), float(pk['head']['y'])
    for s in pk['shape']:
        f = s.split('~')
        if f[0] == 'SOLIDREGION' and f[1] == '3':
            nums = [float(v) for v in re.findall(r'-?\d+\.?\d*', f[3])]
            xs, ys = nums[0::2], nums[1::2]
            cx, cy = (sum(xs) / len(xs) - ox) * UNIT, (sum(ys) / len(ys) - oy) * UNIT
            return min(pads, key=lambda n: math.hypot(pads[n][0] - cx, pads[n][1] - cy))
    # No filled band: a band drawn as silk lines across the body between the pads (C173425 BZT52 draws two)
    (p1, q1), (p2, q2) = list(pads.values())[:2]
    horiz = abs(p1 - p2) > abs(q1 - q2)
    lo, hi = sorted((p1, p2) if horiz else (q1, q2))
    marks = []
    for s in pk['shape']:
        f = s.split('~')
        if f[0] == 'TRACK' and f[2] == '3':
            v = [float(x) for x in f[4].split()]
            xs, ys = [(x - ox) * UNIT for x in v[0::2]], [(y - oy) * UNIT for y in v[1::2]]
            along, across = (xs, ys) if horiz else (ys, xs)
            if max(along) - min(along) < 0.2 and max(across) - min(across) > 0.8 and lo < sum(along) / len(along) < hi:
                marks.append(sum(along) / len(along))
    if marks:
        m = sum(marks) / len(marks)
        if abs(m - (lo + hi) / 2) > 0.2:      # a line in the middle says nothing about the side
            return min(pads, key=lambda n: abs((pads[n][0] if horiz else pads[n][1]) - m))
    return None


def easyeda_pin_names(d):
    names = {}
    for s in d['result']['dataStr']['shape']:
        if s.startswith('P~'):
            seg = s.split('^^')
            num = seg[0].split('~')[3]
            name = seg[3].split('~')[4] if len(seg) > 3 else ''
            names[num] = name
    return names


def norm(n):
    return re.sub(r'[^A-Z0-9]', '', re.sub(r'_\d+$', '', n.upper()))


def rot(p, deg):
    """KiCad's orientation sense in y-down board coordinates (counter-clockwise on screen)."""
    a = math.radians(deg)
    return (p[0] * math.cos(a) + p[1] * math.sin(a), -p[0] * math.sin(a) + p[1] * math.cos(a))


def schematic_pins():
    xml = os.path.join('/tmp', f'jlc_rot_{os.getpid()}.xml')
    subprocess.run(['kicad-cli', 'sch', 'export', 'netlist', '--format', 'kicadxml', '-o', xml, SCH], capture_output=True,
                   check=True)
    pins = {}
    for node in ET.parse(xml).getroot().iter('node'):
        pins[(node.get('ref'), node.get('pin'))] = node.get('pinfunction') or ''
    os.remove(xml)
    return pins


def main():
    T = pcbnew.ToMM
    board = pcbnew.LoadBoard(PCB)
    sch = schematic_pins()
    problems, table = [], {}
    for fp in sorted(board.GetFootprints(), key=lambda f: f.GetReference()):
        ref = fp.GetReference()
        lcsc = fp.GetFieldText('LCSC') if fp.HasField('LCSC') else ''
        pads = [p for p in fp.Pads() if p.GetNumber()]
        if not lcsc or not pads or any(p.GetAttribute() != pcbnew.PAD_ATTRIB_SMD for p in pads):
            continue
        d = fetch(lcsc)
        if not d:
            problems.append(f'{ref} {lcsc}: no EasyEDA data (run with --fetch)')
            continue
        ours = {}
        for p in pads:
            r = p.GetFPRelativePosition()
            ours.setdefault(p.GetNumber(), []).append((T(r.x), T(r.y)))
        ours = {n: (sum(q[0] for q in v) / len(v), sum(q[1] for q in v) / len(v)) for n, v in ours.items()}
        theirs = easyeda_pads(d)
        names = easyeda_pin_names(d)
        # Pair our pads with theirs: by pin name when both name the pin with letters, else by number
        def canon(n):
            n = norm(n)
            for g in SAME:
                if n in g:
                    return min(g)
            return n
        their_by_name = {}
        for num, nm in names.items():
            if re.search('[A-Z]', norm(nm)) and num in theirs:
                their_by_name.setdefault(canon(nm), []).append(num)
        pair, how = {}, {}
        for n in ours:
            sname = canon(sch.get((ref, n), ''))
            cands = their_by_name.get(sname, []) if re.search('[A-Z]', sname) else []
            if len(cands) == 1 and ref[0] not in 'RC':
                pair[n], how[n] = cands[0], 'name'
            elif n in theirs:
                pair[n], how[n] = n, 'number'
        # A diode whose EasyEDA pins are only numbered: pair by the cathode band instead
        sk = [n for n in ours if canon(sch.get((ref, n), '')) == 'CATHODE']
        if ref[0] == 'D' and len(ours) == 2 and sk and not their_by_name:
            band = easyeda_cathode(d, theirs)
            if band:
                other_ours = [n for n in ours if n != sk[0]][0]
                other_theirs = [n for n in theirs if n != band][0]
                pair = {sk[0]: band, other_ours: other_theirs}
                how = {sk[0]: 'band', other_ours: 'band'}
        unpaired = sorted(set(ours) - set(pair))
        if unpaired:
            print(f'  {ref}: our pads {unpaired} have no EasyEDA pad (EasyEDA pads {sorted(theirs)}); fitted on the rest')
        if len(pair) < 2:
            problems.append(f'{ref} {lcsc}: fewer than 2 pads paired')
            continue
        if any(pair[n] != n for n in pair):
            print(f'  {ref}: paired by pin name: ' + ', '.join(f'our {n} = EasyEDA {pair[n]}' for n in sorted(pair) if pair[n] != n))
        common = sorted(pair)
        theirs = {n: theirs[pair[n]] for n in common}
        # Shape fit after centring both pad sets, for each quarter turn
        def centre(pts):
            return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))
        # Thermal tabs (a pad over 3x the median area) vary most between libraries; leads follow the package drawing, so
        # the fit and the origin are measured on the leads when there are at least two
        area = {p.GetNumber(): T(p.GetSize(pcbnew.F_Cu).x) * T(p.GetSize(pcbnew.F_Cu).y) for p in pads}
        med = sorted(area[n] for n in common)[len(common) // 2]
        leads = [n for n in common if area[n] <= 3 * med]
        if len(leads) >= 2 and len(leads) < len(common):
            print(f'  {ref}: tab pad(s) {sorted(set(common) - set(leads))} left out of the fit and origin')
            common = leads
        co, ct = centre([ours[n] for n in common]), centre([theirs[n] for n in common])
        fits = []
        for c in (0, 90, 180, 270):
            err = 0.0
            for n in common:
                tx, ty = rot((theirs[n][0] - ct[0], theirs[n][1] - ct[1]), c)
                err = max(err, math.hypot(tx - (ours[n][0] - co[0]), ty - (ours[n][1] - co[1])))
            fits.append((err, c))
        fits.sort()
        err, c = fits[0]
        # EasyEDA's land patterns are often longer, so pad centres sit up to about 0.5 mm further out: the best turn has
        # to fit within 0.8 mm and beat the next one by 0.5 mm (a wrong quarter turn is off by a pad pitch or more)
        two_pin = len(common) == 2
        polar = ref[0] == 'D' and not all(re.fullmatch(r'A?\d', norm(sch.get((ref, n), '')) or '') for n in common)
        if err > 0.8:
            problems.append(f'{ref} {lcsc}: no quarter turn puts EasyEDA pads on ours (best {c} deg, {err:.2f} mm off)')
        elif fits[1][0] < err + 0.5 and not (two_pin and fits[1][1] == (c + 180) % 360):
            problems.append(f'{ref} {lcsc}: ambiguous: {fits[0][1]} and {fits[1][1]} deg fit within 0.5 mm')
        if two_pin and not polar:
            c = min(c, (c + 180) % 360)   # a resistor or capacitor fits either way round: keep the smaller turn
        # Origin: where EasyEDA's origin lands in our footprint's frame after the turn; JLC centres the part there, so the
        # CPL position is our origin moved by this vector (turned with the footprint)
        ox, oy = rot((-ct[0], -ct[1]), c)
        vx, vy = co[0] + ox, co[1] + oy
        off = math.hypot(vx, vy)
        if off > MAX_OFFSET:
            problems.append(f'{ref} {lcsc}: origin offset {off:.2f} mm after the turn')
        # Pin names on the paired pads, for the record (a pairing by number of named pins that disagree is a failure)
        mism = []
        for n in common:
            a, bname = canon(sch.get((ref, n), '')), canon(names.get(pair[n], ''))
            if ref[0] in 'RC' or not a or not bname or a == bname:
                continue
            if re.fullmatch(r'A?(\d)', a) and re.fullmatch(r'\d', bname) and a[-1] == bname:
                continue              # A1/A2 against 1/2: a bidirectional TVS
            if how.get(n) == 'band':
                continue              # polarity settled by the cathode band above
            mism.append(f'pad {n}: schematic {a}, EasyEDA {bname}')
        if mism:
            problems.append(f'{ref} {lcsc}: pin names: ' + '; '.join(mism))
        bx, by = rot((vx, vy), fp.GetOrientationDegrees())
        kicad_rot = fp.GetOrientationDegrees() % 360
        table[ref] = {'lcsc': lcsc, 'kicad_rot': kicad_rot, 'correction': c, 'cpl_rot': (kicad_rot + c) % 360,
                      'fit_mm': round(err, 3), 'origin_offset_mm': round(off, 3), 'pins': len(common),
                      'pos_shift_mm': [round(bx, 3), round(by, 3)] if off > REPORT_OFFSET else [0.0, 0.0],
                      'paired_by': sorted(set(how.values())), 'polarized': polar}
        if VERBOSE or c not in (0,) or mism or off > REPORT_OFFSET:
            print(f'  {ref:4s} {lcsc:8s} {d["result"]["title"][:22]:22s} correction {c:3d}  CPL {table[ref]["cpl_rot"]:5.0f}'
                  f'  fit {err:.2f} mm  offset {off:.2f} mm' + (f'  PIN NAMES: {mism}' if mism else ''))
    json.dump(table, open(OUT, 'w'), indent=1, sort_keys=True)
    for p in problems:
        print('FAIL', p)
    print(f'jlc rotation: {len(table)} parts measured, {sum(t["correction"] != 0 for t in table.values())} need a '
          f'correction, {len(problems)} problem(s)')
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())
