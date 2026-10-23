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

1. **Use the spare connector pins**: J3-5 = analog out, J3-7 = signal ground (tied to GND at one point near the
   output stage). Same connector, no new terminal. Wiring note for FlashPro installs: Hondata wants the meter's power
   ground and analog ground both at the ECU's ground point (G101 on K-series), on wires not shared with anything else.
2. **Analog stage** (proposed 2026-10-23), after lambda-x2 (`docs/analog-out.md`) with a reference-powered buffer:

   ```
   module SEL_1 (PB1, 3.3 V PWM, 46.9 kHz)
     -> 100k pull-down (output 0 V while the MCU boots)
     -> 74LVC1G125 buffer, VCC = 3.000 V from REF3030, OE tied low   (full scale = the reference, not the LDO)
     -> 3.3k / 100n -> 3.3k / 100n                                   (lambda-x2's values)
     -> LM2904 non-inverting, gain 1 + 68k/100k = 1.68 -> full scale 5.04 V
        feedback taken AFTER the 330R series resistor, so the ECU's input load causes no error
     -> 330R -> BAT54S clamp to +5V and GND -> J3-5
   LM2904 supply: protected 12 V (LSU_Heater+ net) through 100R + 10u
   ```

   Why each choice [INFERRED unless tagged]:
   - 3.0 V reference, not 4.096 V: the buffer's input-high threshold is 0.7 x VCC; at 3.0 V that is 2.1 V against
     the MCU's 3.3 V, a wide margin. At 4.096 V it would be 2.87 V, too thin.
   - LM2904 on 12 V: reaches 5.04 V with headroom (output high is about V+ - 1.5 V); inputs work down to 0 V; rated
     -40 C (automotive LM358 family). It cannot swing to exactly 0 V, which only matters below about 10.0 AFR.
   - Feedback after the 330R: the simulation with feedback before it read 0.31% low into 100k (0.016 AFR at
     mid-scale). Stability with a cable load on the feedback node is to be checked with a real op-amp model.
   - BAT54S clamp to +5V: if the op-amp fails high, the output is held near 5.3 V and the 330R limits the current to
     about 15 mA. Schottky leakage at 5.0 V is small, unlike a 5.1 V zener's soft knee.

   Simulation (`work/sim/analog_out.cir`, ngspice 47, behavioral op-amp, feedback outside the 330R) [DOCUMENTED run]:

   | Duty | Output (mean) | Ripple p-p | Settles to 1% |
   | --- | --- | --- | --- |
   | 50% | 2.5122 V (ideal 2.520) | 0.68 mV (0.0014 AFR) | 4.1 ms |
   | 80% | 4.0192 V (ideal 4.032) | 0.44 mV | 4.1 ms |

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
   | BAT54S,215 | C47546 | SOT-23 | 30 V, 200 mA, series pair | 290,694 |

   Passives: 0603 1% from JLC's Basic list, LCSC numbers to be confirmed when the BOM is generated. Open: does REF3030
   need or tolerate an output capacitor next to the buffer (check the TI datasheet); whether JLC's API marks Basic
   parts differently (every result above said Extended, including parts expected to be Basic).
3. **CAN termination**: decide whether to add an optional 120 ohm (solder jumper) for a bus with no other terminator.

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
| A1 | Test mode 1.00 / 2.50 / 4.00 V, meter J3-5 to J3-7 | DC volts | within ±0.02 V after trim |
| A2 | Sensor in free air, warmed up | DC volts at J3-5 vs AFR the firmware reports over CAN | volts match the curve within ±0.05 V |
| A3 | Short J3-5 to GND briefly through the meter's current range | current | limited by the series resistor (value TBD), board survives |
