# Independent Codex audit — 2026-10-23

Auditor: Codex. Audited commit: `34cd49d` (board design `986c803`).
Scope: bounded electrical and verification audit, not a redesign or hardware certification.
Verdict: keep the larger board, but do not treat R11, calibration, or zero layout-review triggers as proof of readiness.
Board, schematic, firmware and release gate were not changed. No purchase, push or publication.

## Findings

| ID | Finding and evidence | Tag / source | Next action |
| --- | --- | --- | --- |
| C1 | R11 limits back-feed; it does not prevent it. Path is J3-5 -> 470R -> D3 -> +5V. At a 5.5 V rail and assumed 0.6 V diode drop, 12/14.4/16 V faults give injection budgets of 12.55/17.66/21.06 mA. Op-amp absorption can reduce these; these are not simulated rail voltages. A guaranteed minimum rail sink, including unpowered operation, has not been established. | DOCUMENTED topology: `gen/gen_carrier_sch.py:49-55,76,83-84`, checked against actual PCB pads. INFERRED current budgets: `checks/audit_analog.py`. NXP [TJA1051 datasheet](https://www.nxp.com/docs/en/data-sheet/TJA1051.pdf), quick-reference table: recommended VCC 4.5–5.5 V, normal recessive minimum supply current 2.5 mA, not a guaranteed tens-of-mA clamp. | Reopen O1's survival claim. Establish power-on/off fault behavior and a sink/clamp solution if fault survival is required. Do not apply battery voltage to an assembled prototype merely to test this. |
| C2 | Gain calibration cannot overcome duty-cycle saturation. Nominal 5.04 V becomes 5.0164 V into 100k or 4.8138 V into 10k through R11. With R6 -1% and R7 +1%, maximum is 4.9762 V into 100k or 4.7752 V into 10k, even before reference error, offset and supply headroom. This disproves unconditional full-scale recovery by trim, not necessarily the owner's eventual allowed error band. | DOCUMENTED values: `gen/gen_carrier_sch.py:44-54`; duty clamp: `firmware/auxout.cpp:126-131`. INFERRED ideal-circuit calculation: `checks/audit_analog.py`. The 1% corner is an explicit assumption, pending exact BOM verification. | Define receiver load and endpoint tolerance; calculate gain headroom across tolerances before changing values. Verify endpoint and intermediate voltages after trim. |
| C3 | J3-1 and J3-7 are the same GND. The heater MOSFET source returns through module header pins 9/10 into this ground. A sensor-ground wire is consequently a parallel heater-return path; if the main ground opens it may become the only return. Actual division depends on wiring impedances. | DOCUMENTED PCB pad/net inspection: carrier J3 and U3, module Q1 and J1. INFERRED parallel-path consequence. `docs/carrier.md:169-178` itself acknowledges sharing, then recommends a sensor-ground wire. | Withdraw blanket sensor-ground wiring instruction. Use receiver-approved grounding; receiver pin current capacity and fault path remain unresolved. A meter offset reading alone does not qualify the wire for heater current. |
| C4 | The layout check's longest-gap result depends on track enumeration rather than connected path order. Same board: PWM 3.8 -> 4.5 mm under list reversal; VREF3 1.2 -> 2.5 mm under coordinate sorting. No geometry changed. It also skips CAN-to-sensor pairs solely by net name even though CAN termination routing was added. | DOCUMENTED reproduction: `checks/audit_layout_order.py`; algorithm: `checks/layout_review.py:76-77,101-129`; new CAN nets: `gen/gen_carrier_sch.py:89-91`. | Fix path traversal and segment length weighting; compare actual unchanged copper, not whole net names, for exemptions. Keep zero triggers labeled heuristic, not clearance/return-path signoff. |
| C5 | The original stability deck has an ideal 12 V supply and a one-sided settling crossing; it omits R9 supply drop and the unused amplifier. The independent deck includes these and waits 4 ms before the small step. Four cable cases settle without sustained oscillation. | DOCUMENTED original: `sim/stability.sh:15-17,33-42`; new run: `checks/audit_analog.py`, results below. | Preserve positive result with its scope: typical macro-model, 12 V, 100k, small signal. Fault survival, startup and low-voltage full-scale remain unverified. |
| C6 | The plain TI LM2904 is rated 26 V, not the 32 V quoted in the generator and carrier note; LM2904V is the 32 V variant. An 18 V nominal zener is still below 26 V, but surge qualification needs clamp tolerance and pulse energy. A 250 mW resistor is not sufficient for 0.9 W indefinitely. | DOCUMENTED [TI combined datasheet](https://www.ti.com/lit/ds/symlink/lm358.pdf), SLOS068AB, absolute/recommended supply tables; selected device `gen/gen_carrier_sch.py:42`, incorrect comment at 58. INFERRED R9 power at 48 V with ideal 18 V clamp: (48-18)^2/1000 = 0.9 W. | Correct rating references; establish pulse duration/energy before selecting a package. Do not claim a larger footprint alone solves surge survival. |

## Tests and limitations

DOCUMENTED runs on this checkout:

| Check | Result |
| --- | --- |
| `drc_vs_upstream.py` | 0 new violations, 0 unconnected; inherited DRC errors remain, not certified harmless |
| `drift.py check` | No owner drift before audit |
| Independent small step, 1 pF / 1 nF / 10 nF / 47 nF, 100k load | Overshoot approximately 0 / 0 / 0 / 0.511%; 1% settling 255 / 254 / 244 / 176 us; final 1.84166 V; modeled supply about 10.409 V |
| Full-scale DC macro-model attempt | Timed out at 60 s on first 12 V/100k case; no DC simulation result claimed. Removed from default run to avoid repeated stalls. Subsequent supply/load cases were not run. |
| Track enumeration regression | FAIL as expected: same PCB gives different longest-gap measurements |

The independent analog deck omits clamp diodes deliberately: it tests normal small-signal behavior, not fault behavior.
It uses the existing local TI model and ngspice compatibility configuration in `sim/`; no downloaded model is committed.
The exact board's cold-start, negative fault, powered-off injection, temperature corners and cable inductance have not been tested.
Prior 43 host-test passes are REPORTED history, not a new run and not demonstrated coverage of the added PWM output.
Firmware inspection found the intended new shared-timer channel path and duty clamp; this is not a complete concurrency audit.
No confidence percentage is assigned: simulation and DRC cannot establish hardware success probability.

## Reproduce / hand off

Run `python3 work/checks/audit_analog.py` (requires numpy, ngspice and local TI model), or `--calculations-only` for arithmetic without the model.
Run `python3 work/checks/audit_layout_order.py` (requires pcbnew); exit 1 currently demonstrates the checker bug, not an electrically defective board.
Raw session outputs live separately in `work/audit/codex-2026-10-23/` (gitignored).
Next bounded pass: C1 fault-state circuit analysis, C2 receiver-load/tolerance budget, C3 grounding paths, then C4 checker repair.
Do not regenerate the board merely to repair audit wording. Check drift before any future design regeneration.

## Follow-up — 2026-10-23, same design, checker repaired

DOCUMENTED: `checks/layout_metrics.py` integrates midpoint samples with true lengths, and joins uncovered sample edges
by coordinate rather than track enumeration. The result is explicitly a component length (branches summed), not a
longest path or electrical impedance. Coincident endpoints across layers are conservatively joined. Unsplit junctions,
pads and current distribution remain outside this approximation. All noisy/sensitive net pairs are now inspected,
including upstream net names and the first filter node. Three geometry tests and three real-board track orders pass.
PWM now flags a **6.8 mm sampled uncovered component**, above the existing 5 mm review trigger. No coupling-length
triggers fired. This is a review item, not proof of electrical failure. Do not retune the threshold to clear it.

### Circuit verification

The failed direct DC attempt is retained above. A 1-to-3 V ramp at 4 ms succeeds using the same TI model, both amplifier
sections, 1k supply feed, 10u/100n supply capacitors, and 470R connector resistor.
Reproduce: `python3 work/checks/audit_analog.py --full-scale`.

| Protected supply input | Receiver load | Settled connector output | Modeled op-amp supply |
| --- | --- | --- | --- |
| 12 V | 100k | 5.018745 V | 10.3923 V |
| 12 V | 10k | 4.815852 V | 9.3163 V |
| 7.5 V | 100k | 5.018599 V | 6.7556 V |
| 7.5 V | 10k | 4.815796 V | 6.5184 V |

DOCUMENTED model results, not hardware readings. Settling to each model final value is about 257–267 us. These confirm
loading error rather than supply clipping in these four typical cases. They omit clamp diodes, temperature corners,
reference/buffer dropout and cold startup. The supply is the protected rail, not the battery terminal.

INFERRED resistance tradeoff from nominal 5.04 V and 470R: exactly 5 V requires at least 58.75k receiver load, even with
ideal parts. Into 10k, R11 must be at most 80R for nominal 5 V. But 80R raises the 16 V fault injection budget at a 5.5 V
rail / assumed 0.6 V diode to **123.75 mA**, versus 21.06 mA with 470R. Reducing R11 is not a standalone fix.
Increasing gain also needs clamp analysis: delivering 5 V into 10k requires 5.235 V at the clamp node, where diode
current depends on actual +5V and temperature.

Default retained: no component change until load/tolerance and clamp/sink behavior are jointly budgeted. Next circuit
experiment: powered/unpowered clamp model with verified device models or bounded parameters, not an ideal 5 V source
silently absorbing unlimited current. Receiver load, endpoint tolerance, guaranteed sink and allowed fault duration
remain UNKNOWN. No hardware fault-injection instruction issued. Board and firmware remain unchanged.
