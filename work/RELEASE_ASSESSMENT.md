# Release assessment — carrier board + analog output

Written 2026-10-23 (Claude Opus, same session as the r32 routing close). For Logan. Plain language; every claim is tagged
DOCUMENTED (a file or run I can point to), REPORTED (someone else's number), INFERRED (my reasoning, not measured), UNKNOWN.
Nothing here is ordered, pushed or published beyond the private status page.

## 1. The concept in one paragraph
The rusEFI wideband module (upstream, unchanged) sits on a carrier board that adds a 0-5 V output at connector pin J3-5
(AFR 10 = 0 V … 20 = 5 V, 0 V while the sensor is not valid). The module's spare pin SEL_1 makes a PWM at 46.9 kHz; a
74LVC1G125 on a 3.000 V reference squares it up; two RC filters smooth it; an LM2904 scales it ×1.68 to 5.04 V; a 330 Ω
resistor and two clamp diodes protect the output. rusEFI CAN keeps working as before. Receivers: Speeduino, FlashPro
(datalogging), a carb gauge.

## 2. The audit path (what has been checked, by what, how independent)
| Layer | Checked by | Result | Independence |
| --- | --- | --- | --- |
| Op-amp stability vs cable capacitance | ngspice + TI LM2904 model, re-run today (`sim/stability.sh`) | dual loop Cf 1 nF: 0 % overshoot at 1 pF-47 nF; single-loop after the 330 Ω rings. DOCUMENTED | model-based, no hardware |
| Filter ripple / settling | ngspice behavioural (`sim/analog_out.cir`) | 0.7 mV ripple, 4.1 ms. DOCUMENTED | model only |
| Schematic | ERC 0, generated netlist vs table 17/17 | DOCUMENTED | my own generator checking itself |
| PCB | KiCad DRC minus upstream's own errors: 0 new, 0 open; 0 new vias in pads; no drift | DOCUMENTED | same tool that routed it |
| Firmware | builds (f0_module, f1_dual), 43 upstream unit tests pass; diff read today | DOCUMENTED build; behaviour UNKNOWN (never on hardware) | I wrote it and I read it: weak |
| Second-model audit (Codex) | pack ready: `work/audit/carrier-d-2026-10-23/` | **not run yet** | this is the real independent step |
| Bench | nothing built | tests A1-A3 in `docs/carrier.md` | the only thing that settles the INFERRED items |

## 3. Confidence (my honest numbers, not a gate)
| Question | Confidence | Why |
| --- | --- | --- |
| The files fabricate and assemble at JLC without a surprise | 70 % | DRC clean, but BOM/CPL, rotation and stock checks have not been run yet |
| The module and heater behave exactly as upstream | 85 % | carrier adds nothing to the heater path; one touched thing is C1's ground return (0.5 mm via + 0.2 mm tie), INFERRED fine |
| The 0-5 V output works and trims to ±0.05 V | 80 % | simulated stable; firmware never run; the PWM path shares a timer with the pump DAC |
| It survives abuse (output shorted to +12 V, load-dump surge) | 60 % | two 0603 resistors are over their rating in those cases (finding R1, R2) |
| **First board works as a datalogging output with no smoke** | **about 75 %** | |

To reach about 80 %: run the Codex round, fix or accept R1/R2, BOM/CPL checks, and add the JLC quote. Bench tests A1-A3 then
move it to what a built board can tell us.

## 4. Findings from my self-audit (full table in `AUDIT.md`, round 1)
- **R1 RISK, R8 (330 Ω, 0603, 100 mW).** Output shorted to GND: 5 V / 330 Ω = 15 mA = 76 mW, inside the rating. Output shorted to
  +12 V (a wiring fault): current flows through D3 into the +5V rail, (12 − 5.6) / 330 = 19 mA = 120 mW, over the rating, steady.
  Outcome if it fails: R8 burns open, analog output lost, nothing else. Also pushes 19 mA into the +5V rail (the 78M05
  cannot sink; the module's own load of about 50 mA absorbs it, INFERRED). Fix: R8 to 1206 (250 mW). INFERRED, not simulated.
- **R2 RISK, R9 (1 kΩ, 0603) + D5 (18 V zener, 500 mW).** Normal use is a few mW. In a surge that the input TVS lets through
  (35-48 V) the pair sees 17-30 mA: R9 0.3-0.9 W, zener 0.3-0.5 W. A short pulse is fine; a long one (load-dump class) can open
  R9. Outcome: op-amp loses power, output goes to 0 V, the heater and CAN are not involved. Fix: R9 to 1206, or accept. INFERRED.
- **R3 RISK, C17 sits 4.5 mm from U6 pin 8** (op-amp supply bypass). Bipolar op-amp at low speed, C16 (10 µF) is close, so I expect
  no problem, INFERRED. I tried to pull it in (weighting the net in the placer, run r33): the placement moved and routing got
  worse (6 open), so I reverted. A hand move is possible but invalidates the D3 link coordinates.
- **R4 RISK, no CAN node on the bus** (the Speeduino / FlashPro case). `can_helper.cpp` waits up to 100 ms for a free mailbox
  when nothing acknowledges the frames; the analog output is updated from that same thread, so it would drop from 100 Hz to
  about 9 Hz. **Fixed today** (firmware only): this board drops the frame instead of waiting. Builds clean, +32 B flash, RAM
  unchanged. Needs a bench check with the CAN pins unconnected. My first reading was "freezes forever"; that was wrong (the
  wait has a timeout), which is why I read the code before changing anything.
- **R5 NOTE, REF3030 output capacitor.** The datasheet table (REF30 family) lists 0.1-22 µF stable and says no capacitor is
  needed; our 100 nF is at the low edge but inside. REPORTED via a search summary of the REF30E/REF30 datasheet (ti.com/lit/gpn/REF30E); open that table to confirm the REF3030 row.
- **R6 NOTE, untested firmware and curve.** 10 AFR = 0 V … 20 AFR = 5 V is compiled in; no way to edit it without a reflash.
- **R7 NOTE, silkscreen overlaps** (R3/C12, U5/C11). Cosmetic; JLC prints it anyway.

## 5. Decisions for you (defaults in use if you say nothing)
| # | Decision | Default I'm using | Cost of the other way |
| --- | --- | --- | --- |
| D1 | R8 → 1206 and R9 → 1206? | Keep 0603 and accept R1/R2 as RISK until the audit | Parts move; the placer and router must run again (about 4 min each, but `close_d3_link` may stop applying) |
| D2 | Release gate: the two raw DRC checks (module 11, carrier 22, all upstream's) always FAIL, so `release.py` can never pass | Not changed | Swap them in `checks.json` for the "vs upstream" check: **loosens your money gate, so your call** |
| D3 | Output value while the sensor is invalid | 0 V | A mid value would look like a real AFR to a tune |
| D4 | How the module gets flashed | Tag-Connect pads kept reachable | none yet |
| D5 | Hand-fix C17 and the silkscreen, or ship as is | Ship as is, note it | one more regeneration + re-check |

## 6. What "ready to order" still needs (in order)
1. Codex audit round on the pack, raw output kept under `work/audit/`, findings into `AUDIT.md`.
2. Decide D1, D2.
3. BOM/CPL for the carrier; run the rotation, pin-name and stock checks; JLC two-sided assembly quote (**you** approve the price).
4. `checks/run_all.py` all pass (see D2) → `checks/release.py` → files land in `fab/<rev>/`.
5. After boards arrive: tests A1-A3 and the CAN-unconnected check from R4.

## 7. What would change my mind
A second model finding a wrong pin or net in the analog stage (I would drop to about 60 %); R8 or R9 passing in a SPICE surge
run (R1/R2 closed); a bench reading outside ±0.10 V before trim (the filter or reference is off).
