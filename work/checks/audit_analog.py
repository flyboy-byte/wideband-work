#!/usr/bin/env python3
"""Independent, bounded analog audit. Does not alter the board or existing sims.

Uses the locally supplied TI model; reports evidence, not a hardware pass/fail.
Run from any directory: python3 work/checks/audit_analog.py
"""
import json
import argparse
import subprocess
import tempfile
from pathlib import Path

import numpy as np

WORK = Path(__file__).resolve().parents[1]
MODEL = WORK / 'sim/models/lmx58_lm2904.lib'


def simulate(name, vin, supply=12, load=100000, cable='1n', feed=True, transient=False):
    with tempfile.TemporaryDirectory(prefix='wideband-audit-') as tmp:
        directory = Path(tmp)
        deck = f'''* Independent audit: {name}
.include {MODEL}
VBAT battery 0 {supply}
R9 battery vcc {1000 if feed else 0.001}
C16 vcc 0 10u
C17 vcc 0 100n
VIN input 0 {vin}
XACTIVE input inv vcc 0 oa LMX58_LM2904
XUNUSED 0 unused vcc 0 unused LMX58_LM2904
R6 clamp inv 68k
R7 inv 0 100k
C15 oa inv 1n
R8 oa clamp 330
R11 clamp connector 470
RL connector 0 {load}
CL connector 0 {cable}
* Deliberately omit fault diodes: these cases stay in normal operating range.
* This does not simulate fault survival or power-off behavior.
.control
set wr_singlescale
set wr_vecnames
{'tran 200n 8m' if transient else 'op'}
wrdata {directory / 'data.txt'} v(input) v(vcc) v(oa) v(clamp) v(connector)
quit
.endc
.end
'''
        (directory / 'case.cir').write_text(deck)
        result = subprocess.run(['ngspice', '-b', str(directory / 'case.cir')],
                                cwd=WORK / 'sim', capture_output=True, text=True, timeout=60)
        if result.returncode or not (directory / 'data.txt').exists():
            raise RuntimeError(f'{name}: ngspice failed\n{result.stdout}\n{result.stderr}')
        data = np.loadtxt(directory / 'data.txt', skiprows=1, ndmin=2)
        record = {'case': name, 'feed_1k': feed, 'supply_V': supply, 'load_ohm': load,
                  'vcc_V': float(data[-1, 2]), 'connector_V': float(data[-1, 5])}
        if transient:
            time, output = data[:, 0], data[:, 5]
            before = float(np.mean(output[(time > .0035) & (time < .0039)]))
            final = float(np.mean(output[time > .0075]))
            step = final - before
            peak = float(np.max(output[time > .004]))
            outside = np.flatnonzero((time >= .004) & (np.abs(output - final) > .01 * abs(step)))
            record.update(before_V=before, final_V=final,
                          overshoot_pct=100 * max(0, peak - final) / abs(step),
                          late_ripple_mV=float(np.ptp(output[time > .0075]) * 1000),
                          settling_us=None if len(outside) and outside[-1] == len(time)-1 else
                          float((time[outside[-1]+1]-.004)*1e6) if len(outside) else 0)
        return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--calculations-only', action='store_true')
    parser.add_argument('--full-scale', action='store_true', help='Ramped endpoint tests instead of small-signal cable sweep')
    args = parser.parse_args()
    if not args.calculations_only and not MODEL.exists():
        raise SystemExit(f'TI model not available: {MODEL}')
    for cable in (() if args.calculations_only or args.full_scale else ('1p', '1n', '10n', '47n')):
        print(json.dumps(simulate(f'small_step_{cable}', 'PULSE(1 1.1 4m 1n 1n 1 2)',
                                  cable=cable, transient=True)), flush=True)
    if args.full_scale and not args.calculations_only:
        for supply, load in ((12, 100000), (12, 10000), (7.5, 100000), (7.5, 10000)):
            print(json.dumps(simulate('full_scale_ramped', 'PULSE(1 3 4m 1u 1u 1 2)',
                                      supply=supply, load=load, transient=True)), flush=True)
    # Direct full-scale DC op timed out; ramped tests avoid that convergence problem.
    # Sink-current requirement at a 5.5 V rail and a deliberately explicit 0.6 V diode approximation.
    # This is a conservative injection budget ignoring any op-amp absorption, not a board model.
    for fault in (12, 14.4, 16):
        current = (fault - 5.5 - .6) / 470
        print(json.dumps({'case': 'fault_injection_budget', 'fault_V': fault,
                          'rail_ceiling_V': 5.5, 'required_sink_mA': current*1000,
                          'R11_W': current*current*470}), flush=True)
    # Full-scale headroom: 1% feedback resistors and nominal reference, no offset or reference error.
    for load in (100000, 10000):
        low = 3 * (1 + 68000*.99/(100000*1.01)) * load/(load+470)
        print(json.dumps({'case': 'low_gain_full_scale', 'load_ohm': load,
                          'nominal_connector_V': 5.04 * load/(load+470),
                          'maximum_connector_V': low}), flush=True)
    # These limits assume ideal feedback and nominal reference, and ignore clamp conduction.
    print(json.dumps({'case': 'resistance_tradeoff',
                      'minimum_nominal_load_for_5V_ohm': 470*5/(5.04-5),
                      'maximum_series_R_for_5V_into_10k_ohm': 10000*(5.04/5-1),
                      'fault_16V_sink_at_5p5V_with_80R_mA': (16-5.5-.6)/80*1000}), flush=True)


if __name__ == '__main__':
    main()
