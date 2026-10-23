# Our carrier: upstream carrier + analog output

Last updated 2026-10-23. Draft for the Requirements/Parts stages; nothing here is chosen until `STATE.md` says so.
Evidence tags as in `AGENTS.md`.

## Upstream carrier as it is

From the carrier netlist (`kicad-cli sch export netlist`, `upstream/hardware/board_carrier/board_carrier.kicad_sch`)
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
| rusEFI | CAN, rusEFI wideband format | DOCUMENTED | `upstream/firmware/can.cpp` |
| Speeduino | 0-5 V on the O2 input, curve set in TunerStudio; analog ground to signal ground | REPORTED | forum guides, no Speeduino doc found ([stangnet](https://stangnet.com/mustang-forums/threads/wiring-wideband-into-pnp.912251/)) |
| Hondata FlashPro (K20Z3) | 0-5 V into a spare ECU input; one S2000 install used 0 V = 10:1, 5 V = 20:1; Hondata says reference the ECU ground point, don't splice into it | REPORTED | [hondata forum](https://www.hondata.mobi/forum/viewtopic.php?p=51503), [hondata forum](https://hondata.mobi/forum/viewtopic.php?p=42579) |
| K20Z3 ECU pin for the wideband | not found | UNKNOWN | check the K20Z3 ECU wiring diagram / Hondata support |
| Carb gauge or dash | 0-5 V or CAN depending on the unit | INFERRED | pick the unit later |

So: one linear 0-5 V output with a configurable curve, plus a separate signal-ground wire, covers every receiver on
the list. Default curve proposal: 0 V = 10.0 AFR, 5 V = 20.0 AFR (matches the reported FlashPro setup) [INFERRED].

## Proposed changes

1. **Use the spare connector pins**: J3-5 = analog out, J3-7 = signal ground (tied to GND at one point near the
   output stage). Same connector, no new terminal.
2. **Analog stage**, after lambda-x2 (`docs/analog-out.md`), with our improvement:
   module SEL_1 (PB1 PWM) -> small CMOS buffer powered from a precision reference (full scale no longer follows the
   module's 3.3 V LDO) -> two RC stages (lambda-x2: 3.3k/100n twice) -> non-inverting op-amp with gain set so the
   reference maps to 5.0 V -> series resistor and clamp -> J3-5.
3. **Op-amp supply**: the carrier has only 5 V and 12 V. A 5 V-supplied rail-to-rail op-amp (lambda-x2's MCP6002)
   cannot quite reach 5.0 V; one on the protected 12 V rail can, but then the output needs a clamp so a fault can't put
   12 V into an ECU input. Recommendation: 12 V-capable rail-to-rail-output op-amp with a 5.1 V clamp and series
   resistor [INFERRED; part not chosen].
4. **CAN termination**: decide whether to add an optional 120 ohm (solder jumper) for a bus with no other terminator.

## Firmware changes (our fork; f0 has no UART or TunerStudio, `halconf.h` HAL_USE_UART/SERIAL FALSE)

- PB1 to TIM3_CH4 (confirmed in the KiCad STM32F042K symbol's alternate list; the AF number still to check in
  ST DS10152), sharing TIM3 with the pump DAC; drop the SEL_1 strap read.
- The config struct already has `auxOutBins/auxOutValues/auxOutputSource` and pads to 256 bytes in a 1 KB flash page
  (`upstream/firmware/boards/port.h`, `boards/f0_module/wideband_layout.ld:11`) [DOCUMENTED]. f0 has no
  `LoadDefaults()`, and there is no TunerStudio link to edit the curve, so the curve must be compiled in (presets,
  maybe chosen by the SEL_2 three-state strap) [INFERRED].
- A test mode that holds the output at fixed voltages (1.00, 2.50, 4.00 V) for the multimeter, and a gain/offset trim.
- Flash headroom on the 32 KB F042: UNKNOWN until we build it.

## Draft bring-up tests for the analog output (owner to confirm, then they move into `REQUIREMENTS.md`)

| # | Do | Measure | Pass |
| --- | --- | --- | --- |
| A1 | Test mode 1.00 / 2.50 / 4.00 V, meter J3-5 to J3-7 | DC volts | within ±0.02 V after trim |
| A2 | Sensor in free air, warmed up | DC volts at J3-5 vs AFR the firmware reports over CAN | volts match the curve within ±0.05 V |
| A3 | Short J3-5 to GND briefly through the meter's current range | current | limited by the series resistor (value TBD), board survives |
