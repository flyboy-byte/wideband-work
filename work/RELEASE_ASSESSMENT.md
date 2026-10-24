# Release assessment — carrier board + analog output

Written 2026-10-23 by Claude Sonnet 5.5 (same session as the r32 routing close); reviewed and corrected the same day by Claude
Opus 5.5 (AUDIT.md round 2: R1 rewritten, R4 rate corrected, R8 added). For Logan. Plain language; every claim is tagged
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
| Review of the self-audit | Claude Opus 5.5, AUDIT.md round 2 | topology re-derived from the board file; one finding reversed | different model, same session context: medium |
| Second-model audit (Codex) | pack: newest `work/audit/carrier-*-2026-10-23/` | **not run yet** | this is the real independent step |
| Bench | nothing built | tests A1-A3 in `docs/carrier.md` | the only thing that settles the INFERRED items |

## 3. Confidence (my honest numbers, not a gate)
| Question | Confidence | Why |
| --- | --- | --- |
| The files fabricate and assemble at JLC without a surprise | 70 % | DRC clean, but BOM/CPL, rotation and stock checks have not been run yet |
| The module and heater behave exactly as upstream | 85 % | carrier adds nothing to the heater path; one touched thing is C1's ground return (0.5 mm via + 0.2 mm tie), INFERRED fine |
| The 0-5 V output works and trims to ±0.05 V | 80 % | simulated stable; firmware never run; the PWM path shares a timer with the pump DAC |
| It survives the output shorted to GND | 90 % | the 1k op-amp supply resistor R9 limits it to about 9 mA (R1) |
| It survives J3-5 shorted to 12 V (a wiring fault) | 20 % | D3 feeds the 12 V straight onto the +5V rail: CAN transceiver, REF3030 and the module see about 11 V (R1) |
| **First board works as a datalogging output with no smoke, wired correctly** | **about 75 %** | |

To reach about 80 %: decide R1 (D6), run the Codex round, fix or accept R2, BOM/CPL checks, and add the JLC quote. Bench tests A1-A3 then
move it to what a built board can tell us.

## 4. Findings from my self-audit (full table in `AUDIT.md`, round 1)
- **R1 RISK (high consequence), output clamp D3 ties J3-5 to the +5V rail with no resistor in between** (corrected by Opus;
  the first version of this finding blamed R8 and got the current path wrong). The board file: R8 sits between the op-amp and
  `/AOUT`; `/AOUT` *is* J3-5, and D3 (to +5V) and D4 (to GND) clamp that node directly.
  - J3-5 shorted to 12 V (a crimping or pin mix-up; J3-6 is 12V_RAW on the same connector): D3 conducts from the 12 V wire into
    +5V, limited only by the wiring. The 78M05 cannot sink, so the rail rises toward 11 V. On +5V: the TJA1051 CAN transceiver,
    the REF3030, the module and C2/C6/C11. Expected outcome: dead transceiver and reference, probably the module too
    (absolute maximum ratings around 6 V, FROM MEMORY, not re-checked). R8 meanwhile sinks 12 V / 330 = 36 mA = 0.43 W into the
    op-amp. INFERRED, not simulated. lambda-x2's stage is the same shape, so this is inherited, not new.
  - J3-5 shorted to GND (test A3): the DC loop drives the op-amp high, but R9 (1k) starves its supply: about 9 mA, R8 27 mW,
    R9 81 mW. Fine. INFERRED. (The first version said 15 mA / 76 mW from the wrong reasoning; the conclusion stood.)
  - Smallest fix: a series resistor between the clamp node and J3-5, outside the feedback, e.g. 470 Ω 1206: a 12 V short then
    puts (12 − 5.6) / 470 = 14 mA into +5V (absorbed by the module's own load) and 0.1 W into the resistor; cost is 0.5 % gain
    error into a 100k input, which the trim removes for one receiver. It changes schematic, placement and routing (the D3 link
    must be redone). **Owner decision D6.**
- **R2 RISK, R9 (1 kΩ, 0603) + D5 (18 V zener, 500 mW).** Normal use is a few mW. In a surge that the input TVS lets through
  (35-48 V) the pair sees 17-30 mA: R9 0.3-0.9 W, zener 0.3-0.5 W. A short pulse is fine; a long one (load-dump class) can open
  R9. Outcome: op-amp loses power, output goes to 0 V, the heater and CAN are not involved. Fix: R9 to 1206, or accept. INFERRED.
- **R3 RISK, C17 sits 4.5 mm from U6 pin 8** (op-amp supply bypass). Bipolar op-amp at low speed, C16 (10 µF) is close, so I expect
  no problem, INFERRED. I tried to pull it in (weighting the net in the placer, run r33): the placement moved and routing got
  worse (6 open), so I reverted. A hand move is possible but invalidates the D3 link coordinates.
- **R4 RISK, no CAN node on the bus** (the Speeduino / FlashPro case). `can_helper.cpp` waits up to 100 ms for a free mailbox
  when nothing acknowledges the frames; the analog output is updated from that same thread, so it would drop from 100 Hz to
  about 5 Hz (two frames per loop, each waiting 100 ms; first version said 9 Hz). **Fixed today** (firmware only): this board drops the frame instead of waiting. Builds clean, +32 B flash, RAM
  unchanged. Needs a bench check with the CAN pins unconnected. My first reading was "freezes forever"; that was wrong (the
  wait has a timeout), which is why I read the code before changing anything.
- **R5 NOTE, REF3030 output capacitor.** The datasheet table (REF30 family) lists 0.1-22 µF stable and says no capacitor is
  needed; our 100 nF is at the low edge but inside. REPORTED via a search summary of the REF30E/REF30 datasheet (ti.com/lit/gpn/REF30E); open that table to confirm the REF3030 row.
- **R6 NOTE, untested firmware and curve.** 10 AFR = 0 V … 20 AFR = 5 V is compiled in; no way to edit it without a reflash.
- **R7 NOTE, silkscreen overlaps** (R3/C12, U5/C11). Cosmetic; JLC prints it anyway.

## 5. Decisions for you (defaults in use if you say nothing)
| # | Decision | Default I'm using | Cost of the other way |
| --- | --- | --- | --- |
| D1 | R9 → 1206? (R8 needs no change: fine in a GND short, and the 12 V short is fixed by D6, not by a bigger R8) | Keep 0603 and accept R2 as RISK until the audit | Parts move; the placer and router must run again (about 4 min each, but `close_d3_link` may stop applying) |
| D2 | Release gate: the two raw DRC checks (module 11, carrier 22, all upstream's) always FAIL, so `release.py` can never pass | Not changed | Swap them in `checks.json` for the "vs upstream" check: **loosens your money gate, so your call** |
| D3 | Output value while the sensor is invalid | 0 V | A mid value would look like a real AFR to a tune |
| D4 | How the module gets flashed | Tag-Connect pads kept reachable | none yet |
| D5 | Hand-fix C17 and the silkscreen, or ship as is | Ship as is, note it | one more regeneration + re-check |
| D6 | Series resistor at J3-5 so a 12 V wiring fault can't reach +5V (R1) | Not done; recommend yes before ordering | one part, a regeneration, the D3 link redone |

## 6. What "ready to order" still needs (in order)
1. Codex audit round on the pack, raw output kept under `work/audit/`, findings into `AUDIT.md`.
2. Decide D1, D2.
3. BOM/CPL for the carrier; run the rotation, pin-name and stock checks; JLC two-sided assembly quote (**you** approve the price).
4. `checks/run_all.py` all pass (see D2) → `checks/release.py` → files land in `fab/<rev>/`.
5. After boards arrive: tests A1-A3 and the CAN-unconnected check from R4.

## 7. What would change my mind
A second model finding a wrong pin or net in the analog stage (I would drop to about 60 %); R8 or R9 passing in a SPICE surge
run (R1/R2 closed); a bench reading outside ±0.10 V before trim (the filter or reference is off).
