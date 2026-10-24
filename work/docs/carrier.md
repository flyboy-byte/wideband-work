# Our carrier: upstream carrier + analog output

Last updated 2026-10-23. Draft for the Requirements/Parts stages; nothing here is chosen until `STATE.md` says so.
Evidence tags as in `AGENTS.md`.

## Upstream carrier as it is

From the carrier netlist (`kicad-cli sch export netlist`, `hardware/board_carrier/board_carrier.kicad_sch`)
and `export/carrier_bom.csv` [DOCUMENTED]:

| Connector J3 (MX120G-12, 2x6) | Net |
| --- | --- |
| 1 | GND |
| 2 | LSU_Ip |
| 3 | LSU_Heater- |
| 4 | LSU_Heater+ (12 V after the reverse-polarity Schottky) |
| 5 | **unconnected** |
| 6 | 12V_RAW (input) |
| 7 | **unconnected** |
| 8 | LSU_Vm |
| 9 | LSU_Rtrim |
| 10 | LSU_Un |
| 11 | CAN_H |
| 12 | CAN_L |

- Power: 12V_RAW -> TVS D1 (SMC, C133648) -> Schottky D2 (SMA, C8678) -> LM78M05 (U2, TO-252, C58069) -> +5V for the
  module and the TJA1051T-3 CAN transceiver (U1, C38695). The 5 V rail is linear from 12 V.
- Module U3 pads SEL_1, SEL_2 and Boot0 are not connected. No CAN termination resistor on the carrier (47 pF to GND on
  each CAN line only) [DOCUMENTED; termination meaning INFERRED].
- 18 parts. Baseline checks at upstream `2bb80d2`: DRC 29 errors, ERC 8 errors, not yet judged (`STATE.md`).

## What the receivers want

| Receiver | Input | Tag | Source |
| --- | --- | --- | --- |
| rusEFI | CAN, rusEFI wideband format | DOCUMENTED | `firmware/can.cpp` |
| Speeduino | 0-5 V on the O2 input, curve set in TunerStudio; analog ground to signal ground | REPORTED | forum guides, no Speeduino doc found ([stangnet](https://stangnet.com/mustang-forums/threads/wiring-wideband-into-pnp.912251/)) |
| Hondata FlashPro | Analog only: "a wideband meter which has an analog output, preferably 0-5V with a linear relationship between voltage and lambda"; set by two voltage/lambda pairs ("more than two... cannot be used"); no CAN or serial input | DOCUMENTED | [Hondata help: wideband lambda interface](https://www.hondata.com/help/flashpro/wideband_lambda_interface.htm) |
| FlashPro standard scaling | PLX, later AEM and Innovate (when programmed) all output 0 V = 10:1, 5 V = 20:1 | DOCUMENTED | same page |
| 2006-2011 Civic Si ECU pin | B29 (EGRL, EGR lift input) "Wideband input", "Normally unused"; A23 (ELD) and A33 (ECT2) need that sensor disabled and the factory pin removed; C27 (SO2) not recommended, the ECU limits its voltage | DOCUMENTED (model-column mapping read from extracted text; check the rendered table) | [Hondata help: ECU connectors](https://www.hondata.com/help/flashpro/ecu_connectors.htm); forums agree on B29 ([8thcivic](https://www.8thcivic.com/threads/wideband-into-flashpro.187850/)) |
| Grounding (FlashPro, K-series) | "the lambda meter uses the same ground as the ECU, for both the power and analog output sections"; K-series point is G101 on the intake manifold; don't share the meter's ground wire; needing an offset "means you have a ground problem" | DOCUMENTED | wideband lambda interface page |
| Closed loop with FlashPro | Not a conflict: the stock ECU's closed loop reads the narrowband O2 voltage, so a 0-5 V wideband is for datalogging, not automatic fuel control. That is normal. A simulated-narrowband output would be needed for closed loop; we don't need it | OWNER (2026-10-23), consistent with the forum report |
| ECU pin terminal | Hondata reportedly sent free direct-fit pins on request | REPORTED | 8thcivic forum |
| Carb gauge or dash | 0-5 V or CAN depending on the unit | INFERRED | pick the unit later |

So: one linear 0-5 V output with a configurable curve, plus a separate signal-ground wire, covers every receiver on
the list. Default curve: 0 V = 10.0 AFR, 5 V = 20.0 AFR, linear. Hondata names this the standard output of PLX, later AEM and
Innovate [DOCUMENTED], so it is the curve to ship. That scale is 2 AFR per volt: 0.1 AFR = 0.05 V, and a 2% full-scale
error (0.1 V) is 0.2 AFR, which is why the reference buffer matters [INFERRED].

## Proposed changes

1. **Use the spare connector pins**: J3-5 = analog out, J3-7 = signal ground. (This said "tied to GND at one
   point near the output stage"; the board never did that: J3-7 sits on the ground pour beside J3-1. Corrected
   2026-10-23, see "Grounding and the output" below.) Same connector, no new terminal. Wiring note for FlashPro installs: Hondata wants the meter's power
   ground and analog ground both at the ECU's ground point (G101 on K-series), on wires not shared with anything else.
2. **Analog stage** (proposed 2026-10-23), after lambda-x2 (`docs/analog-out.md`) with a reference-powered buffer:

   ```
   module SEL_1 (PB1, 3.3 V PWM, 46.9 kHz)
     -> 100k pull-down (output 0 V while the MCU boots)
     -> 74LVC1G125 buffer, VCC = 3.000 V from REF3030, OE tied low   (full scale = the reference, not the LDO)
     -> 3.3k / 100n -> 3.3k / 100n                                   (lambda-x2's values)
     -> LM2904 non-inverting, gain 1 + 68k/100k = 1.68 -> full scale 5.04 V
        dual loop: DC feedback (68k) from AFTER the 330R, so the ECU's input load causes no error;
        AC feedback Cf = 1 nF (C0G) from the op-amp output to IN-, so cable capacitance can't make it oscillate
     -> 330R -> 1N4148W clamps to +5V and GND -> 470R (R11, 1206) -> J3-5
   LM2904 supply: protected 12 V (LSU_Heater+ net) through 1k, 18 V zener, 10u 50 V + 100n
   ```

   Why each choice [INFERRED unless tagged]:
   - 3.0 V reference, not 4.096 V: the buffer's input-high threshold is 0.7 x VCC; at 3.0 V that is 2.1 V against
     the MCU's 3.3 V, a wide margin. At 4.096 V it would be 2.87 V, too thin.
   - LM2904 on 12 V: reaches 5.04 V with headroom (output high is about V+ - 1.5 V); inputs work down to 0 V; rated
     -40 C (automotive LM358 family). It cannot swing to exactly 0 V, which only matters below about 10.0 AFR.
   - Dual loop: feedback taken plainly before the 330R reads 0.31% low into 100k (0.016 AFR at mid-scale); taken
     plainly after it, the stage oscillates with cable capacitance (stability table below). The 1 nF Cf fixes both.
   - 1N4148W clamps (Basic part, replaced the Extended BAT54S): if the op-amp fails high, the output is held near
     5.7 V and the 330R limits the current to about 15 mA. Their leakage sits inside the DC feedback loop (taken after
     the 330R), so it is corrected.
   - R11 470R between the clamps and J3-5 (added 2026-10-23, AUDIT.md round 2 O1): J3-5 sits between J3-6 (12V_RAW)
     and J3-4 (LSU_Heater+) [DOCUMENTED: J3 footprint pads]. Without it, 12 V on J3-5 reaches +5V through D3 with no
     limit (TJA1051, REF3030, module on that rail). With it: (12 - 5.6) / 470 = 14 mA into +5V, 0.09 W in R11 (1206,
     250 mW) [INFERRED, calculation]. This limits but does not prevent back-feed; power-off behavior and the rail's
     guaranteed sink current remain unverified (Codex audit C1, 2026-10-23). Outside the feedback, it reads 0.46 % low
     into 100k. Trim helps only while duty-cycle headroom remains: nominal full scale into 10k is 4.814 V and cannot
     be trimmed to 5 V (C2). Endpoint tolerance and receiver load must be budgeted together.
   - Op-amp supply clamp: upstream's input TVS is an SMCJ30CA (C133648: 30 V standoff, 35.1 V breakdown per the JLC
     listing), so the protected 12 V rail can reach about 35-48 V in a surge; the plain TI LM2904 is rated 26 V, not 32 V
     ([TI SLOS068AB](https://www.ti.com/lit/ds/symlink/lm358.pdf), supply tables; Codex audit C6). 1k + 18 V zener
     (BZT52C18, C173425) holds it below that; the op-amp draws about 1 mA, so the 1k costs about 1 V of headroom
     (fine down to about 7.5 V battery for a 5 V output) [INFERRED].
   - REF3030 output: 100 nF, inside the 0.1-10 uF stable range in TI's current datasheet (SBVS032J) [REPORTED via a
     search summary of the table; confirm it is the REF3030 row].

   Simulation (`work/sim/analog_out.cir`, ngspice 47, behavioral op-amp, feedback outside the 330R) [DOCUMENTED run]:

   | Duty | Output (mean) | Ripple p-p | Settles to 1% |
   | --- | --- | --- | --- |
   | 50% | 2.5122 V (ideal 2.520) | 0.68 mV (0.0014 AFR) | 4.1 ms |
   | 80% | 4.0192 V (ideal 4.032) | 0.44 mV | 4.1 ms |

   Stability with TI's LM2904 model (`work/sim/stability.sh`, model `LMX58_LM2904` Rev B from TI SNOM268, 12 V
   supply, 100 mV input step = 168 mV output step, 100k ECU load) [DOCUMENTED run, 2026-10-23]:

   | Feedback | Cable C | Overshoot | Still oscillating at 0.6 ms | Settles to 1% |
   | --- | --- | --- | --- | --- |
   | A: before 330R | 1 pF / 1 nF / 10 nF / 47 nF | 24% / 28% / 0% / 0% | no | 2-70 us |
   | B: after 330R | 1 pF / 1 nF / 10 nF / 47 nF | 24% / 72% / 106% / 86% | **yes at 10 nF (55 mV p-p) and 47 nF (16 mV)** | up to 795 us |
   | C: dual loop, Cf 100 pF | 1 pF / 1 nF / 10 nF / 47 nF | 0% / 0% / 11% / 39% | no | 9-161 us |
   | **C: dual loop, Cf 1 nF** | 1 pF / 1 nF / 10 nF / 47 nF | **0% at every load** | no | 145-254 us |
   | **D: C plus R11 470R to the connector** | 1 pF / 1 nF / 10 nF / 47 nF | **0% / 0% / 0% / 0.5%** | no | 175-254 us |

   D's final value: 1.8417 V against C's 1.8503 V, 0.46 % low into the 100k load (R11 outside the loop) [DOCUMENTED run,
   2026-10-23].

   Final value with C: 1.8503 V against 1.848 V ideal (the difference is the model's input offset). Not simulated:
   the clamp diodes, the 100k pull-down, temperature, and cable inductance.

   Resolution: 1024 PWM steps over 5.04 V = 4.9 mV = 0.0098 AFR. Accuracy budget: REF3030 ±0.2% initial and
   75 ppm/C (about ±0.45% over -40..+85 C), resistor tolerance (1%: about ±0.8% gain worst case; 0.1% parts or the
   trim fix it), LM2904 offset up to 3 mV [DOCUMENTED: JLC listings below] [budget INFERRED]. Trim at bring-up covers
   initial errors; drift stays.

   Parts (JLC/LCSC search 2026-10-23, all listed as Extended) [DOCUMENTED: JLC API listings]:

   | Part | LCSC | Package | Key specs from the listing | Stock |
   | --- | --- | --- | --- | --- |
   | REF3030AIDBZR | C38423 | SOT-23 | 3.0 V, ±0.2%, 75 ppm/C, 25 mA, Vin 3.05-5.5 V, -40..+125 C | 43,373 |
   | 74LVC1G125GW,125 | C12519 | SOT-353 | 1.65-5.5 V, 32 mA, -40..+125 C | 50,292 |
   | LM2904DR (TI) | C7934 | SOIC-8 | 3-32 V, 3 mV offset, -40..+125 C | 219,267 |
   | BZT52C18 | C173425 | SOD-123 | 17.1-18.9 V, 500 mW | 66,666 |

   Extended parts: these four (each carries JLC's per-part setup fee). The LM358DR2G (C7950) is Basic but rated
   0-70 C only, so the LM2904 stays. JLC's API does mark Basic parts ("base"), checked 2026-10-23.
   Basic: 1N4148W C81598; 0603 1% resistors 100R C22775, 120R C22787, 330R C23138, 1k C21190, 3.3k C22978,
   68k C23231, 100k C25803; caps 100n X7R C14663, 1n X7R C1588 (compensation; C0G not needed at these voltages),
   10u 50 V 1206 C13585. Full list with reasons: `work/gen/gen_carrier_sch.py` PARTS.
3. **TEST jumper**: a solder jumper from module SEL_2 to GND, open by default, for bench test A1.
4. **CAN termination**: decide whether to add an optional 120 ohm (solder jumper) for a bus with no other terminator.

## Layout (r36, 2026-10-23)

The board is upstream's 40.0 x 36.5 mm grown 15 mm at the bottom edge, away from the connector: **40.0 x 51.5 mm (1.57 x
2.03 in)**. The owner designs his own enclosure, so `case/case.STL` is no limit (STATE.md decision). The whole analog
stage sits in the new strip, on the bottom side, below the module's left pad column (pads 3 PWM, 4 TEST, 7 supply). The
right column (heater drive 11-12, sensor 13-16) is 3 mm or more above the strip and no new track runs beside its nets.
Upstream's tracks are all kept (r1-r33 deleted two to make room). Renders: `work/renders/carrier-e/`.
Bypass and feedback parts: C17 2.1 mm from U6 pin 8 (was 4.5 mm), C15 2.3 mm from pins 1-2, C11/C12 under 2.1 mm
from the REF3030 [DOCUMENTED: measured on the board file].

## Layout review checklist (any outline, placement or routing change; AGENTS.md rule 8)

| # | Item | How it is checked | r36 result |
| --- | --- | --- | --- |
| L1 | Every connection made, nothing new in DRC | `checks/drc_vs_upstream.py` | 0 new, 0 open |
| L2 | No vias in SMD pads | `checks/via_in_pad.py` | 0 |
| L3 | Noisy nets (PWM, heater drive, CAN) kept off sensitive ones (sensor, filter, reference, output) | `checks/layout_review.py` part 1 | nothing within 1 mm (r34 had CAN_L 0.3 mm beside the output for 6.8 mm; fixed by moving the CAN terminator) |
| L4 | Return path under every new signal track (GND on the other layer, or on both sides on its own layer) | `layout_review.py` part 2 (component metric repaired by Codex, C4) | largest uncovered component 6.8 mm (PWM, over the 5 mm review trigger: C7), 1.2 mm (output). C7 inspected 2026-10-23: the gap is JP2's opening in the bottom pour plus the PWM's own two-layer branch to R3/U4; low-current, low-speed signal next to its own filtered copy; accept recommended (`AUDIT.md` round 3) |
| L5 | GND pour joined, stitched in new copper | DRC unconnected (pour islands count) + `layout_review.py` part 3 | joined; 16 GND vias in the strip, farthest pour point 10.7 mm from one |
| L6 | Bypass caps at their pins | measured distances (above) | all under 2.4 mm |
| L7 | Output's ground reference vs the heater's return current | calculation below | about 1-2 mV on the board; the wiring matters more |
| L8 | Edge clearance on the new outline | DRC | no new violations |

## Grounding and the output

2026-10-23 audit qualification: the 1–2 mV estimate below is not a solved copper-current distribution or a measurement.
`layout_review.py` has an order-dependent gap metric (C4); its zero triggers do not validate this ground-offset estimate.

- **On the board.** The heater's return current (up to about 0-4 A, REPORTED for wideband heaters in general) flows from
  the module's GND pads 9-10 (x 72.7, y 71-73.5) through the pour to J3-1 (68.75, 66) [DOCUMENTED: pad positions]. The
  output stage's ground is the pour 20 mm away in the strip, a dead end with no heater current; J3-7 sits beside J3-1.
  Copper sheet: 1.68e-8 ohm m / 35 um = 0.48 mOhm per square per layer; the drop across that corner is of order
  1 mOhm x heater amps, and the strip sees about half of it: **about 1-2 mV = 0.002-0.004 AFR** [INFERRED, calculation].
- **In the car, the bigger one.** The receiver reads J3-5 against its own ground. Any voltage between the controller's
  ground and the receiver's ground adds 1:1 (10 mV = 0.02 AFR). J3-1 and J3-7 are joined on the board, so if both wires
  go to the vehicle, heater current splits between them and the J3-7 wire carries part of it: for example 1 A x 20 mOhm
  of wire = 20 mV = 0.04 AFR [INFERRED, example numbers]. Commercial controllers give the heater its own ground wire and
  tell the installer to tie the controller's ground to the receiver's ground source (Innovate LC-1/LC-2 wiring, REPORTED
  via forum and wiki posts; Hondata says the same for FlashPro: same ground as the ECU for power and analog, line 41
  above). This is upstream's grounding, not something the carrier changed.
- **Superseded instruction (2026-10-23, Codex C3):** ~~J3-1 to the ECU ground point and J3-7 to the receiver's sensor ground.~~
  J3-7 shares the heater-return net. It can carry part of the heater current, or become the sole return if J3-1's
  wire opens [INFERRED from documented same-net topology]. Do not connect it to a low-current ECU sensor-ground pin
  without receiver-specific approval. Use receiver-approved power/output grounding; exact wiring remains unresolved.
  A4's high-impedance voltage measurement does not qualify a sensor-ground wire for heater current. D7 remains open.

## Receiver load and the feedback point (2026-10-24, C2 build-around)

The owner can't measure the K20Z3/FlashPro input resistance, so the stage has to be right into an unknown input.
REPORTED (hondata.mobi forum): the usable wideband input on Honda ECUs is the EGR-lift pin, not the O2 input; an ELD input
reads about 4.8 V open (an internal pull-up), and users see the wideband read about 0.5 AFR lean. A pull-up pushes current
back through R11, which is outside the feedback loop as built, so the reading comes out high.

`sim/load_accuracy.sh` (TI LM2904 model, 12 V supply, ramped input; DOCUMENTED by the run, typical model only):

| Target | Load | As built (D, feedback before R11) | E: feedback at J3-5, after R11 |
| --- | --- | --- | --- |
| 5.00 V | 100k / 10k / 4.7k to GND | 4.979 / 4.778 / 4.548 | 5.002 / 5.002 / 5.002 |
| 2.50 V | 100k / 10k / 4.7k to GND | 2.491 / 2.390 / 2.275 | 2.502 / 2.502 / 2.502 |
| 2.50 V | 47k / 10k / 4.7k to 5 V | 2.527 / 2.615 / 2.730 | 2.502 / 2.502 / 2.502 |
| 1.00 V | 47k / 10k / 4.7k to 5 V | 1.042 / 1.182 / 1.366 | 1.002 / 1.002 / 1.331 |
| 0.10 V | 10k / 47k to 5 V | 0.974 / 0.634 | 0.971 / 0.629 |

- E holds every point from 1 V to 5 V within 3 mV into every load tried except a 4.7k pull-up at 1 V. That covers 12-20 AFR
  for any receiver, with no trim for the load (trim then only corrects parts tolerance).
- Below about 1 V (rich of 12 AFR) into a pull-up, both versions read high: the LM2904 sinks little current near ground
  (FROM MEMORY, datasheet: tens of uA at 200 mV out). Odd model result, UNKNOWN whether real: a 4.7k pull-down also floors
  at about 0.52 V, and a pull-down at the op-amp output made it worse (0.63 V floor) and stopped some runs converging. Not a
  fix; treat the bottom 1 V into a pull-up input as unverified until the bench.
- Stability, step through the output (TI model, `stability.sh` method): E with Cf 1 nF: no overshoot up to 10 nF on the
  cable, 9.4 % at 47 nF, 28 % at 100 nF (still settles); D: 0.5 % and 2.5 %. Cf 2.2 nF or 4.7 nF is worse (does not settle at
  some loads). Cable capacitance is about 100 pF per metre (FROM MEMORY), so a few nF at most: E with Cf 1 nF it is.
- Fault (C1, accepted risk): with 12 V on J3-5 the feedback now sees 12 V and drives the op-amp low; D did the same through
  the clamp node. R8 then carries about 5.6 V / 330R = 17 mA, about 95 mW in an 0603 rated 100 mW (INFERRED).

**Decision (2026-10-24, owner: "build around it"):** E, the 68k feedback resistor's top end moves from the 330R/R11 node to
J3-5 (net AOUT_J). One schematic connection, folded into the next board run with D1, D8 and D9. Firmware unchanged.

## Firmware changes (our fork; f0 has no UART or TunerStudio, `halconf.h` HAL_USE_UART/SERIAL FALSE)

- Done on branch `analog-out`, builds; details and budget in `firmware.md`. PB1 = TIM3_CH4 (AF1, confirmed in ST's
  pin data), sharing TIM3 with the pump DAC; SEL_1 strap read dropped.
- The config struct already has `auxOutBins/auxOutValues/auxOutputSource` and pads to 256 bytes in a 1 KB flash page
  (`firmware/boards/port.h`, `boards/f0_module/wideband_layout.ld:11`) [DOCUMENTED]. f0 has no
  `LoadDefaults()`, and there is no TunerStudio link to edit the curve, so the curve must be compiled in (presets,
  maybe chosen by the SEL_2 three-state strap) [INFERRED].
- A test mode that holds the output at fixed voltages (1.00, 2.50, 4.00 V) for the multimeter, and a gain/offset trim.
- Flash: 4.8 KB left; RAM: 8 bytes left, so no new threads (`firmware.md`).

## Draft bring-up tests for the analog output (owner to confirm, then they move into `REQUIREMENTS.md`)

| # | Do | Measure | Pass |
| --- | --- | --- | --- |
| A1 | Close the TEST jumper (module SEL_2 to GND), power up; output steps 1.00 / 2.50 / 4.00 V, 10 s each (firmware before 2026-10-23 stayed at 1.00 V: fixed, `firmware.md` F5). Meter J3-5 to J3-7 | DC volts at each step | before trim: within ±0.10 V; after trim and reflash: within ±0.02 V |
| A2 | Sensor in free air, warmed up | DC volts at J3-5 vs AFR the firmware reports over CAN | volts match the curve within ±0.05 V |
| A3 | Short J3-5 to GND briefly through the meter's current range | current | about 9 mA (R9 1k starves the op-amp supply, AUDIT round 2 O2); board survives |
| A4 | In the car, engine running, sensor hot: meter (mV range) between J3-7 at the controller and the receiver's sensor-ground pin | DC mV | under 20 mV (= 0.04 AFR at 0.5 V per AFR); more means a ground offset in the wiring (see "Grounding and the output") |
