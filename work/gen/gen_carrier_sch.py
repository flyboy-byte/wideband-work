#!/usr/bin/env python3
"""Generate hardware/board_carrier/board_carrier.kicad_sch: upstream's carrier plus our analog output.

  python3 work/gen/gen_carrier_sch.py          generate, then self-check (needs kicad-cli)
  python3 work/gen/gen_carrier_sch.py --check  self-check the existing file only

Base = upstream's carrier at `master`, upgraded to the KiCad 10 format (the upgrade keeps its netlist identical;
checked 2026-10-23). New parts come from KiCad's installed libraries and are connected with labels and power symbols
placed exactly on their pin ends, so no wires are drawn. UUIDs are derived from names, so a rerun gives the same file.
After writing, it exports the netlist and checks every new net below against it (the netlist self-check).
Design and the reason for every value: work/docs/carrier.md. Don't hand-edit the output; change this file.
"""
import math, os, re, subprocess, sys, tempfile, uuid, xml.etree.ElementTree as ET

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT = os.path.join(REPO, 'hardware/board_carrier/board_carrier.kicad_sch')
LIBS = '/usr/share/kicad/symbols'
NS = uuid.UUID('6f1c3a52-2f1e-4d55-9a0b-7a1f3c1d2e01')

# ---------------------------------------------------------------------------------------------------------------
# Parts: ref -> (lib, symbol, value, footprint, LCSC, (x, y) in mm, why)
# ---------------------------------------------------------------------------------------------------------------
R0603 = 'Resistor_SMD:R_0603_1608Metric'
C0603 = 'Capacitor_SMD:C_0603_1608Metric'
# 0402 where it fits the rating: the bottom-side area was too crowded to route with all-0603 (PCB runs r1-r12,
# 2026-10-23). Kept 0603: R6 (68k is Extended in 0402), R8 (fault current), C17 (18 V rail); R9 1206 (D1).
R0402 = 'Resistor_SMD:R_0402_1005Metric'
C0402 = 'Capacitor_SMD:C_0402_1005Metric'
PARTS = {
    'R3':  ('Device', 'R', '4.7k', R0402, 'C25900', (215.9, 40.64), 'pull-down: output at 0 V from reset until the app drives PB1. 4.7k, not 100k: the F042 pull-up on PB1 (25-55k) held 100k at 2.1-2.6 V, read as high (outside review B1, 2026-10-24); 4.7k gives 0.52 V worst case, under the buffer V_IL 0.8 V. C25900 Basic'),
    'U5':  ('Reference_Voltage', 'REF3030', 'REF3030', 'Package_TO_SOT_SMD:SOT-23', 'C38423', (254, 40.64),
            '3.000 V, the full-scale reference for the buffer'),
    'C11': ('Device', 'C', '100n', C0402, 'C1525', (292.1, 40.64), 'REF3030 input bypass'),
    'C12': ('Device', 'C', '100n', C0402, 'C1525', (317.5, 40.64),
            'REF3030 output cap (stable range 0.1-10 uF, TI SBVS032J) and buffer decoupling'),
    'U4':  ('74xGxx', '74LVC1G125', '74LVC1G125', 'Package_TO_SOT_SMD:SOT-353_SC-70-5', 'C12519', (241.3, 86.36),
            'buffer powered from 3.000 V: PWM amplitude = the reference, not the MCU LDO'),
    'R4':  ('Device', 'R', '3.3k', R0402, 'C25890', (215.9, 129.54), 'first RC stage (lambda-x2 values)'),
    'C13': ('Device', 'C', '100n', C0402, 'C1525', (241.3, 129.54), 'first RC stage'),
    'R5':  ('Device', 'R', '3.3k', R0402, 'C25890', (266.7, 129.54), 'second RC stage'),
    'C14': ('Device', 'C', '100n', C0402, 'C1525', (292.1, 129.54), 'second RC stage'),
    'U6':  ('Amplifier_Operational', 'LM2904', 'LM2904', 'Package_SO:SOIC-8_3.9x4.9mm_P1.27mm', 'C7934', None,
            'x1.68 to 5.04 V full scale; -40 C rated; on the clamped 12 V'),
    'R6':  ('Device', 'R', '68k', R0603, 'C23231', (279.4, 172.72), 'DC feedback from J3-5, after R11: no error from the receiver load (sim/load_accuracy.sh E)'),
    'R7':  ('Device', 'R', '100k', R0402, 'C25741', (304.8, 172.72), 'gain 1 + 68k/100k = 1.68'),
    'C15': ('Device', 'C', '1n', C0402, 'C1523', (330.2, 172.72),
            'AC feedback from the op-amp output: no oscillation with cable C (work/sim/stability.sh)'),
    'R8':  ('Device', 'R', '330', R0603, 'C23138', (355.6, 172.72), 'series output resistor, limits clamp current'),
    'D3':  ('Diode', '1N4148WS', '1N4148WS', 'Diode_SMD:D_SOD-323', 'C2128', (330.2, 213.36), 'clamp output to +5V'),
    'D4':  ('Diode', '1N4148WS', '1N4148WS', 'Diode_SMD:D_SOD-323', 'C2128', (355.6, 213.36), 'clamp output to GND'),
    # J3-5 sits between J3-6 (12V_RAW) and J3-4 (LSU_Heater+). Without R11, 12 V on J3-5 reaches +5V through D3 unlimited
    # (AUDIT.md round 2, O1); with it, (12 - 5.6) / 470 = 14 mA, 0.09 W. Inside the DC feedback since 2026-10-24 (R6 from
    # J3-5): the receiver's input, pull-up or pull-down, no longer shifts the output (sim/load_accuracy.sh, C2). C4502: 470R 1206 1 % 250 mW [REPORTED, LCSC datasheet listing]
    'R11': ('Device', 'R', '470', 'Resistor_SMD:R_1206_3216Metric', 'C4502', (381.0, 213.36),
            'series resistor at J3-5: a 12 V wiring fault cannot back-feed +5V through D3'),
    # 1206 (owner decision D1, 2026-10-23): load-dump current into the zener. C4410 UNI-ROYAL 1206W4F1001T5E 1 % 250 mW
    # [REPORTED, LCSC/JLC listing 2026-10-24]
    'R9':  ('Device', 'R', '1k', 'Resistor_SMD:R_1206_3216Metric', 'C4410', (215.9, 213.36), 'op-amp supply feed from the protected 12 V'),
    'D5':  ('Device', 'D_Zener', '18V', 'Diode_SMD:D_SOD-123', 'C173425', (241.3, 213.36),
            'clamps op-amp supply: TVS D1 (SMCJ24CA, C151279) lets the rail reach about 27-39 V; plain LM2904 is rated 26 V'),
    'C16': ('Device', 'C', '10u', 'Capacitor_SMD:C_1206_3216Metric', 'C13585', (266.7, 213.36), 'op-amp supply, 50 V'),
    'C17': ('Device', 'C', '100n', C0603, 'C14663', (292.1, 213.36), 'op-amp bypass'),
    'JP1': ('Jumper', 'SolderJumper_2_Open', 'TEST', 'Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm', '',
            (215.9, 243.84), 'SEL_2 to GND at power-up = analog-out test mode (bench test A1)'),
    'R10': ('Device', 'R', '120', R0402, 'C25079', (254, 243.84), 'optional CAN termination'),
    'JP2': ('Jumper', 'SolderJumper_2_Open', 'CAN_TERM', 'Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm', '',
            (279.4, 243.84), 'close for a bus with no other 120 R terminator'),
}
# LM2904 units: A = the output stage, B = unused (follower at 0 V), C = power
U6_UNITS = {1: (241.3, 172.72), 2: (317.5, 243.84), 3: (381.0, 172.72)}

# Nets: name -> [(ref, pin)]. GND/+5V become power symbols; the rest become local labels.
NETS = {
    'AOUT_PWM':   [('U3', '3'), ('R3', '1'), ('U4', '2')],
    'GND':        [('R3', '2'), ('U5', '3'), ('C11', '2'), ('C12', '2'), ('U4', '1'), ('U4', '3'), ('C13', '2'),
                   ('C14', '2'), ('R7', '2'), ('D4', '2'), ('D5', '2'), ('C16', '2'), ('C17', '2'), ('U6', '4'),
                   ('U6', '5'), ('JP1', '2'), ('J3', '7')],
    '+5V':        [('U5', '1'), ('C11', '1'), ('D3', '1')],
    'VREF3':      [('U5', '2'), ('C12', '1'), ('U4', '5')],
    'AOUT_BUF':   [('U4', '4'), ('R4', '1')],
    'AOUT_F1':    [('R4', '2'), ('C13', '1'), ('R5', '1')],
    'AOUT_F2':    [('R5', '2'), ('C14', '1'), ('U6', '3')],
    'AOUT_INN':   [('U6', '2'), ('R6', '2'), ('R7', '1'), ('C15', '2')],
    'AOUT_OA':    [('U6', '1'), ('C15', '1'), ('R8', '1')],
    'AOUT':       [('R8', '2'), ('D3', '2'), ('D4', '1'), ('R11', '1')],
    'AOUT_J':     [('R11', '2'), ('R6', '1'), ('J3', '5')],
    'LSU_Heater+': [('R9', '1')],
    'VOP12':      [('R9', '2'), ('D5', '1'), ('C16', '1'), ('C17', '1'), ('U6', '8')],
    'U6B_FB':     [('U6', '6'), ('U6', '7')],
    'TEST_SEL2':  [('U3', '4'), ('JP1', '1')],
    'CAN_H':      [('R10', '1')],
    'CAN_TERM':   [('R10', '2'), ('JP2', '1')],
    'CAN_L':      [('JP2', '2')],
}
POWER = {'GND': 'power:GND', '+5V': 'power:+5V'}
# ERC power flags, placed on a pin of each net that is fed through a passive part (resistor, diode), so ERC knows
# it is a supply: our op-amp rail, and three upstream nets that had no flag (ERC errors at upstream 2bb80d2)
PWR_FLAGS = [('R9', '2'),    # VOP12, through R9 from the protected 12 V
             ('U2', '1'),    # LSU_Heater+ (78M05 input), through the Schottky D2
             ('U1', '5'),    # TJA1051 VIO, through R1 from +5V
             ('C11', '2')]   # GND (only power symbols, no driver)


# ---------------------------------------------------------------------------------------------------------------
# S-expressions
# ---------------------------------------------------------------------------------------------------------------
class Q(str):
    """A quoted string."""

def parse(text):
    toks = re.findall(r'"(?:\\.|[^"\\])*"|\(|\)|[^\s()"]+', text)
    stack = [[]]
    for t in toks:
        if t == '(':
            stack.append([])
        elif t == ')':
            node = stack.pop(); stack[-1].append(node)
        elif t.startswith('"'):
            stack[-1].append(Q(t[1:-1].replace('\\"', '"').replace('\\\\', '\\')))
        else:
            stack[-1].append(t)
    return stack[0][0]

def dump(node, ind=0):
    if not isinstance(node, list):
        return '"%s"' % node.replace('\\', '\\\\').replace('"', '\\"') if isinstance(node, Q) else node
    if all(not isinstance(x, list) for x in node):
        return '(' + ' '.join(dump(x) for x in node) + ')'
    head = [x for x in node if not isinstance(x, list)]
    out = '(' + ' '.join(dump(x) for x in head)
    for x in node:
        if isinstance(x, list):
            out += '\n' + '\t' * (ind + 1) + dump(x, ind + 1)
    return out + '\n' + '\t' * ind + ')'

def find(node, tag):
    return [x for x in node if isinstance(x, list) and x and x[0] == tag]

def uid(*names):
    return Q(str(uuid.uuid5(NS, '/'.join(names))))

def f(v):
    return ('%.4f' % v).rstrip('0').rstrip('.')


# ---------------------------------------------------------------------------------------------------------------
# Library symbols, flattened ("extends" resolved) and renamed to Lib:Name for the schematic's cache
# ---------------------------------------------------------------------------------------------------------------
_libcache = {}

def lib_symbol(lib, name):
    if lib not in _libcache:
        _libcache[lib] = {s[1]: s for s in find(parse(open(f'{LIBS}/{lib}.kicad_sym').read()), 'symbol')}
    sym = [x for x in _libcache[lib][name]]
    ext = find(sym, 'extends')
    if ext:
        parent = lib_symbol(lib, ext[0][1])
        props = {p[1]: p for p in find(sym, 'property')}
        merged = []
        for x in parent:
            if isinstance(x, list) and x[0] == 'property' and x[1] in props:
                merged.append(props.pop(x[1]))
            elif isinstance(x, list) and x[0] == 'symbol':
                merged.append([x[0], Q(x[1].replace(parent[1].split(':')[-1] + '_', name + '_', 1))] + x[2:])
            else:
                merged.append(x)
        sym = merged[:merged.index(next(m for m in merged if isinstance(m, list)))] + list(props.values()) + \
            [m for m in merged if isinstance(m, list)]
    sym = [x for x in sym]
    sym[1] = Q(f'{lib}:{name}')
    return sym

def sym_pins(symnode, unit):
    """{number: (name, type, x, y)} for one unit (unit 0 = shared by all units), body style 1."""
    out = {}
    base = symnode[1].split(':')[-1]
    for sub in find(symnode, 'symbol'):
        m = re.fullmatch(re.escape(base) + r'_(\d+)_(\d+)', sub[1])
        if not m or m.group(2) not in ('0', '1') or int(m.group(1)) not in (0, unit):
            continue
        for p in find(sub, 'pin'):
            at = find(p, 'at')[0]
            out[find(p, 'number')[0][1]] = (find(p, 'name')[0][1], p[1], float(at[1]), float(at[2]))
    return out


# ---------------------------------------------------------------------------------------------------------------
def prop(name, value, x, y, hide=False):
    p = ['property', Q(name), Q(value), ['at', f(x), f(y), '0']]
    if hide:
        p.append(['hide', 'yes'])
    p.append(['effects', ['font', ['size', '1.27', '1.27']], ['justify', 'left']])
    return p

def instance(lib_id, ref, value, fp, lcsc, x, y, unit, pins, key):
    node = ['symbol', ['lib_id', Q(lib_id)], ['at', f(x), f(y), '0'], ['unit', str(unit)], ['body_style', '1'],
            ['exclude_from_sim', 'no'], ['in_bom', 'no' if ref.startswith('#') else 'yes'],
            ['on_board', 'no' if ref.startswith('#') else 'yes'], ['in_pos_files', 'yes'], ['dnp', 'no'],
            ['uuid', uid('sym', key)],
            prop('Reference', ref, x + 3.81, y - (13.97 if ref[0] == 'U' else 1.27), ref.startswith('#')),
            prop('Value', value, x + 3.81, y - (11.43 if ref[0] == 'U' else -1.27), ref.startswith('#')),
            prop('Footprint', fp, x, y, True), prop('Datasheet', '', x, y, True), prop('Description', '', x, y, True)]
    if lcsc:
        node.append(prop('LCSC', lcsc, x, y, True))
    for num in sorted(pins):
        node.append(['pin', Q(num), ['uuid', uid('pin', key, num)]])
    return node

def label(name, x, y, key):
    return ['label', Q(name), ['at', f(x), f(y), '0'],
            ['effects', ['font', ['size', '1.27', '1.27']], ['justify', 'left', 'bottom']], ['uuid', uid('lbl', key)]]


def main():
    base = subprocess.run(['git', '-C', REPO, 'show', 'master:hardware/board_carrier/board_carrier.kicad_sch'],
                          capture_output=True, text=True, check=True).stdout
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, 'board_carrier.kicad_sch')
        open(p, 'w').write(base)
        subprocess.run(['kicad-cli', 'sch', 'upgrade', p], capture_output=True, check=True)
        sch = parse(open(p).read())

    # A3 sheet: upstream's drawing stays where it is, our block goes in the free area to its right
    find(sch, 'paper')[0][1] = Q('A3')
    libsyms = find(sch, 'lib_symbols')[0]
    have = {s[1] for s in find(libsyms, 'symbol')}

    def need(lib_id):
        if lib_id not in have:
            lib, name = lib_id.split(':')
            libsyms.append(lib_symbol(lib, name)); have.add(lib_id)
        return next(s for s in find(libsyms, 'symbol') if s[1] == lib_id)

    # Pin end positions of the existing parts we connect to (U3 module, J3 connector), from the base file
    ends = {}
    for s in find(sch, 'symbol'):
        ref = next(p[2] for p in find(s, 'property') if p[1] == 'Reference')
        if ref in ('U1', 'U2', 'U3', 'J3'):
            at = find(s, 'at')[0]
            assert not find(s, 'mirror'), f'{ref} is mirrored; handle mirroring'
            a = math.radians(float(at[3]))
            for num, (_, _, px, py) in sym_pins(need(find(s, 'lib_id')[0][1]), int(find(s, 'unit')[0][1])).items():
                # local y points up, schematic y points down; rotation is counterclockwise on screen
                ends[(ref, num)] = (round(float(at[1]) + px * math.cos(a) - py * math.sin(a), 4),
                                    round(float(at[2]) - px * math.sin(a) - py * math.cos(a), 4))

    # Free J3-5 and J3-7 (and U3's SEL pads, which had nothing): drop no-connect flags sitting on pins we now use
    used = {ends[k] for net in NETS.values() for k in net if k in ends}
    sch[:] = [x for x in sch if not (isinstance(x, list) and x[0] == 'no_connect' and
                                     any(abs(float(find(x, 'at')[0][1]) - ux) < 0.01 and
                                         abs(float(find(x, 'at')[0][2]) - uy) < 0.01 for ux, uy in used))]

    # Upstream draws module pad Boot0 (U3-8) as a label that connects to nothing (ERC: input not driven). The module
    # pulls Boot0 down itself (R29 10k, module netlist), so mark the pad as intentionally unconnected instead.
    bx, by = ends[('U3', '8')]
    sch[:] = [x for x in sch if not (isinstance(x, list) and x[0] == 'label' and x[1] == 'Boot0')]
    new = [['no_connect', ['at', f(bx), f(by)], ['uuid', uid('nc', 'U3.8')]]]
    for ref, (lib, name, value, fp, lcsc, pos, _why) in PARTS.items():
        lib_id = f'{lib}:{name}'
        sym = need(lib_id)
        units = U6_UNITS if ref == 'U6' else {1: pos}
        for unit, (x, y) in units.items():
            pins = sym_pins(sym, unit)
            new.append(instance(lib_id, ref, value, fp, lcsc, x, y, unit, pins, f'{ref}.{unit}'))
            for num, (_, _, px, py) in pins.items():
                ends[(ref, num)] = (x + px, y - py)

    pwr = 0
    for net, members in NETS.items():
        for ref, num in members:
            x, y = ends[(ref, num)]
            if net in POWER:
                pwr += 1
                need(POWER[net])
                new.append(instance(POWER[net], f'#PWR02{pwr:02d}', net, '', '', x, y, 1, {'1': None},
                                    f'pwr.{ref}.{num}'))
            else:
                new.append(label(net, x, y, f'{net}.{ref}.{num}'))
    for i, (ref, num) in enumerate(PWR_FLAGS, 1):
        need('power:PWR_FLAG')
        x, y = ends[(ref, num)]
        new.append(instance('power:PWR_FLAG', f'#FLG02{i:02d}', 'PWR_FLAG', '', '', x, y, 1, {'1': None},
                            f'flag.{ref}.{num}'))

    insert_at = next(i for i, x in enumerate(sch) if isinstance(x, list) and x[0] == 'sheet_instances') \
        if find(sch, 'sheet_instances') else len(sch)
    sch[insert_at:insert_at] = new
    open(OUT, 'w').write(dump(sch) + '\n')
    print('wrote', os.path.relpath(OUT, REPO))
    return selfcheck()


def selfcheck():
    """Export the netlist and check every net in NETS: all listed pins together, nothing else from the new parts."""
    with tempfile.TemporaryDirectory() as td:
        xml = os.path.join(td, 'n.xml')
        subprocess.run(['kicad-cli', 'sch', 'export', 'netlist', '--format', 'kicadxml', '-o', xml, OUT],
                       capture_output=True, check=True)
        root = ET.parse(xml).getroot()
    nets = [{(n.get('ref'), n.get('pin')): n.get('pinfunction') for n in net.iter('node')} for net in root.iter('net')]
    bad = 0
    for name, members in NETS.items():
        homes = [n for n in nets if any(m in n for m in members)]
        if len(homes) != 1:
            print(f'FAIL {name}: its pins land in {len(homes)} nets'); bad += 1; continue
        extra = sorted(k for k in homes[0] if k[0] in PARTS and k not in members)
        if extra:
            print(f'FAIL {name}: also has {extra}'); bad += 1
    newpins = {k for n in nets for k in n if k[0] in PARTS}
    listed = {m for ms in NETS.values() for m in ms}
    for k in sorted(newpins - listed):
        print(f'FAIL pin {k} is on no listed net'); bad += 1
    print(f'netlist self-check: {len(NETS)} nets, {bad} problems')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(selfcheck() if '--check' in sys.argv else main())
