# Release assessment — carrier board + analog output

Current as of 2026-10-24, board r41 (Claude Opus 5.5). For Logan, plain language. Claims are tagged DOCUMENTED (a file or
run I can point to), REPORTED (someone else's number), INFERRED (reasoning, not measured), FROM MEMORY, UNKNOWN. The
r32-r36 assessment is kept under "History" at the end; its percentages were judgement, not test results (Codex, round 3).
Nothing is ordered, pushed or flashed.

## 1. The concept
The rusEFI wideband module (upstream, unchanged) sits on a carrier board, grown to 40.0 x 51.5 mm (1.57 x 2.03 in), that
adds a 0-5 V output at J3-5 (AFR 10 = 0 V ... 20 = 5 V, 0 V while the sensor is not valid). The module's spare pin SEL_1
makes a 46.9 kHz PWM; a 74LVC1G125 on a 3.000 V reference squares it; two RC filters smooth it; an LM2904 scales it x1.68;
330R, clamp diodes and a 470R series resistor protect the pin. The DC feedback is taken at J3-5 itself, so whatever input
the receiver has (pull-up or pull-down, 4.7k-100k) doesn't shift the reading (simulated). Every SMD part is on the top
(JLC Economic assembly). Firmware adds the output, a bench test mode, and an independent watchdog on the heater loop.
rusEFI CAN works as before. Receivers: Speeduino, Hondata FlashPro (datalogging), an AFR gauge, rusEFI.

## 2. The audit path (what has been checked, by what, how independent)
| Layer | Checked by | Result | Independence |
| --- | --- | --- | --- |
| Stability into cable capacitance | ngspice + TI LM2904 model (`sim/stability.sh`, topology E = as built) | no overshoot to 10 nF, 9.4 % at 47 nF, 28 % at 100 nF (settles). DOCUMENTED | model only |
| DC accuracy into unknown receiver inputs | `sim/load_accuracy.sh` | 1-5 V within 3 mV into 4.7k-100k pull-downs and 10k-47k pull-ups; below 1 V into a pull-up reads high (unresolved). DOCUMENTED | model only |
| Filter ripple / settling | `sim/analog_out.cir` | 0.7 mV, 4.1 ms. DOCUMENTED | behavioural model |
| Schematic | ERC 0, netlist self-check 18/18 | DOCUMENTED | generator checking itself |
| PCB | DRC vs upstream incl. fab-relevant warnings 0 new / 0 open; vias in pads 0; layout review 0 triggers; renders looked at | DOCUMENTED | same tools that routed it |
| Fab files | `gen/export_fab.py` + `checks/fab_files.py` (BOM/CPL/Gerbers against the board) + `checks/jlc_rotation.py` (EasyEDA footprints: rotation, origin, pin names) | 38 parts, 4 corrections, D2 polarity caught, U2 shifted 0.725 mm. DOCUMENTED | my tools; rotation sense INFERRED |
| Firmware | host tests 69 + 21, QEMU M0 fault entry, bootloader bounds 52 cases, package checker 21 cases, static stack estimate, mutants | DOCUMENTED | I wrote much of it; Codex planned the tests |
| Independent audits | rounds 1 (Sonnet self), 2 (Opus review), 3 (Codex, r36) in `AUDIT.md` | round 3 findings answered | **round 4 on r41 not run yet** |
| Bench | nothing built | tests A1-A4, W1 drafted | the only thing that settles the INFERRED items |

## 3. Confidence (judgement, not a gate)
- **Fabricates and assembles without a surprise: good, not proven.** Checked: DRC with fab warnings, every part's EasyEDA
  footprint, BOM/CPL against the board, outline, drills. Not checked: the Gerbers in a viewer (JLC's at upload), JLC's
  own stock (LCSC shows 0 for C13585 and C14663), edge rails (C11 is 1.85 mm from the edge), the rotation sense.
- **Module and heater behave as upstream: high.** The carrier adds nothing to the heater path; the watchdog only adds a
  reset when the heater loop stops.
- **Output reads within +-0.05 V after a one-time trim: medium.** Simulated with the real op-amp model, load-independent from
  1 to 5 V; firmware host-tested; nothing has run on hardware.
- **Survives the output shorted to GND: high** (about 6 mA, INFERRED). **To 12 V: no requirement** (owner, C1): R11
  limits, doesn't block.
- What would change it: round 4 finding a wrong net, pin or rotation; JLC's preview disagreeing with a corrected rotation;
  a bench reading outside +-0.10 V before trim.

## 4. Open caveats (known, accepted or waiting)
- Below about 1 V (rich of 12 AFR) into a receiver with a pull-up, the output reads high (op-amp sink near ground).
- Watchdog covers the heater loop only; a stalled sampler is not caught (no RAM for check-ins).
- 13 small passives have no silkscreen label (assembly drawing `renders/carrier-f/assembly-top.svg` names them).
- Upstream's raw DRC errors (module 11, carrier 23) are advisory (D2); upstream's exported BOM/CPL are stale and unused.
- Mounting holes are isolated (no copper within 3.6 mm); a plastic washer works too.

## 5. What "ready to order" still needs (in order)
1. Audit round 4 (Codex) on `audit/carrier-f-<date>/`; answer each finding (`AGENTS.md`, turn-taking).
2. JLC quote (**you** approve the price): upload `work/out/carrier/`, read the placement preview for every IC and diode (D2
   first), check stock and edge rails.
3. `checks/release.py <rev>` (you pick the revision letter) -> `fab/<rev>/`, committed the day you order, row in `ORDERS.md`.
4. After the boards arrive: T1, A1-A4, W1 (watchdog self-test build).

## 6. Decisions for you (defaults in use if you say nothing)
| # | Decision | Default I'm using | Cost of the other way |
| --- | --- | --- | --- |
| D1 | R9 → 1206? (still open; room exists now) (R8 needs no change: fine in a GND short, and the 12 V short is fixed by D6, not by a bigger R8) | Keep 0603 and accept R2 as RISK until the audit | Parts move; the placer and router must run again (about 4 min each, but `close_d3_link` may stop applying) | **Decided: 1206 (owner 2026-10-23); done r37 (C4410)**
| D2 | Release gate: the two raw DRC checks (module 11, carrier 23, all upstream's) always FAIL, and since 2026-10-23 so does the layout review (C7, 6.8 mm PWM return gap, inspected, accept recommended in `AUDIT.md`), so `release.py` can never pass | Not changed | Swap the DRC checks in `checks.json` for the "vs upstream" check, and either accept C7 as a recorded, dated waiver or move JP2 and re-run the board: **loosens your money gate, so your call** | **Decided: DRC vs upstream + dated C7 waiver (owner 2026-10-23); done 2026-10-24: raw DRC checks marked advisory in `checks.json`, new "Module board identical to upstream" check; C7 needs no waiver (r37 layout review 0 triggers)**
| D3 | Output value while the sensor is invalid | 0 V | A mid value would look like a real AFR to a tune |
| D4 | How the module gets flashed | Tag-Connect pads kept reachable | none yet |
| D5 | ~~C17~~ done (r36, 2.1 mm); silkscreen overlaps remain (cosmetic) | Ship as is | a label pass |
| D6 | ~~Series resistor at J3-5~~ | **Done r36** (owner agreed): R11 470R 1206, C4502 | 0.46 % low into 100k, trimmed |
| D7 | Separate analog ground for J3-7 on the board? | No board change; wiring instruction + bring-up test A4 measures the real offset first (`docs/carrier.md`, "Grounding and the output") | a net-tie and re-route; would not stop heater current sharing the J3-7 wire | **Decided: no board change (owner 2026-10-23)**
| D8 | Mounting holes in the new bottom corners (only the two upstream holes at the connector end exist) | None added | two holes for your enclosure; say where | **Decided: two M3 holes, new bottom corners (owner 2026-10-23); done r37 (H1/H2, 3.5 mm in)**
| D10 | Independent watchdog (IWDG) so a firmware hang can't leave the heater PWM at its last duty (F9 fixed the fault path only; `docs/firmware.md`) | None (upstream has none on any board) | small code, a kick from the heater loop, its own host and bench tests; changes upstream behaviour | **Decided: add IWDG (owner 2026-10-23); done 2026-10-24 (`firmware/watchdog.h`, 0 B RAM, 5 host tests, bench test W1; `docs/firmware.md` "Watchdog")**
| D11 | Measure the real battery on f0 (module PB0 already has a 100k/10k divider from VBatt_Sense) instead of assuming 13 V without CAN | Assume 13 V (upstream) | about 48 B RAM with 0 B free: something else must shrink; firmware change + tests (`docs/firmware.md` F7) | **Decided: keep 13 V (owner 2026-10-23)**
| D9 | Move the analog stage to the top of the strip (one-sided JLC assembly, cheaper; R10/JP2 too) | Bottom (as routed) | generator side switch, a new run; saves the two-sided assembly fee (price unchecked) | **Decided: move to top (owner 2026-10-23); done r37 (Economic $8 vs Standard two-sided $50 setup, REPORTED JLC help 2025-09)**


## History (r32-r36 assessment, 2026-10-23; superseded by the sections above)

### 0. Update, r36 (2026-10-23 evening, Opus 5.5)
The board grew 15 mm (40.0 x 51.5 mm, 1.57 x 2.03 in; owner: no case limit, function first). The analog stage moved into
the new strip, R11 470R went in at J3-5 (D6 done), C17 and C15 sit at their pins (R3 done), the C1 ground workaround
is gone (R6 done: C1 is back to upstream's own connection). Routing closed on the first run. A new measurement script
(`checks/layout_review.py`) covers coupling, return paths and the ground pour; it found one coupling problem (r34), fixed
in r35. New owner question D7 (output ground in the car). Sections below are the earlier assessment with statuses
updated; `docs/carrier.md` "Layout" and "Grounding and the output" have the detail.

### 1. The concept in one paragraph
The rusEFI wideband module (upstream, unchanged) sits on a carrier board that adds a 0-5 V output at connector pin J3-5
(AFR 10 = 0 V … 20 = 5 V, 0 V while the sensor is not valid). The module's spare pin SEL_1 makes a PWM at 46.9 kHz; a
74LVC1G125 on a 3.000 V reference squares it up; two RC filters smooth it; an LM2904 scales it ×1.68 to 5.04 V; a 330 Ω
resistor, two clamp diodes and a 470 Ω series resistor at the pin protect the output. rusEFI CAN keeps working as before. Receivers: Speeduino, FlashPro
(datalogging), a carb gauge.

### 2. The audit path (what has been checked, by what, how independent)
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

### 3. Confidence (my honest numbers, not a gate)
| Question | Confidence | Why |
| --- | --- | --- |
| The files fabricate and assemble at JLC without a surprise | 70 % | DRC clean, but BOM/CPL, rotation and stock checks have not been run yet |
| The module and heater behave exactly as upstream | 85 % | carrier adds nothing to the heater path; one touched thing is C1's ground return (0.5 mm via + 0.2 mm tie), INFERRED fine |
| The 0-5 V output works and trims to ±0.05 V | 80 % | simulated stable; firmware never run; the PWM path shares a timer with the pump DAC |
| It survives the output shorted to GND | 90 % | the 1k op-amp supply resistor R9 limits it to about 9 mA (R1) |
| It survives J3-5 shorted to 12 V (a wiring fault) | 85 % | R11 limits it to 14 mA into +5V, absorbed by the module's load (calculation, not simulated) |
| **First board works as a datalogging output with no smoke, wired correctly** | **about 75 %** | |

To reach about 80 %: decide R1 (D6), run the Codex round, fix or accept R2, BOM/CPL checks, and add the JLC quote. Bench tests A1-A3 then
move it to what a built board can tell us.

### 4. Findings from my self-audit (full table in `AUDIT.md`, round 1)
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

### 6. What "ready to order" still needs (in order)
1. Codex audit round on the pack, raw output kept under `work/audit/`, findings into `AUDIT.md`.
2. Decide D1, D2.
3. BOM/CPL for the carrier; run the rotation, pin-name and stock checks; JLC two-sided assembly quote (**you** approve the price).
4. `checks/run_all.py` all pass (see D2) → `checks/release.py` → files land in `fab/<rev>/`.
5. After boards arrive: tests A1-A3 and the CAN-unconnected check from R4.

### 7. What would change my mind
A second model finding a wrong pin or net in the analog stage (I would drop to about 60 %); R8 or R9 passing in a SPICE surge
run (R1/R2 closed); a bench reading outside ±0.10 V before trim (the filter or reference is off).
