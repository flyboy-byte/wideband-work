# Analog output for the f0 module + carrier

Last verified: 2026-10-23 (Opus 5.5 re-check of the Sonnet 5.5 plan, same day). Upstream at `2bb80d2` (2026-10-20).

## Why

The owner wants one board that works with rusEFI (CAN), Speeduino, a Honda K20Z3 on Hondata FlashPro, and a
carburetor setup with a dash or gauge. The upstream module + carrier only sends the rusEFI CAN format. The others
are assumed to want a 0-5 V wideband signal [INFERRED, general knowledge; Speeduino and FlashPro inputs not yet
checked in their docs].

## Facts (each with its source)

Evidence tags: DOCUMENTED = read in a named file or datasheet; INFERRED = reasoned from documented facts;
FROM MEMORY = model recall, must be checked; UNKNOWN = not found.

| # | Fact | Tag | Source |
| --- | --- | --- | --- |
| F1 | MCU is STM32F042K6T (U2), 32-pin | DOCUMENTED | module netlist (`kicad-cli sch export netlist`, `upstream/hardware/board_module/wideband_controller.kicad_sch`) |
| F2 | Module has two 8-pin edge connectors, J1 (sensor side) and J3 (power, CAN, straps); 16 pads, not 14 | DOCUMENTED | module netlist. The 14-pin `wideband_module.kicad_sym` is the carrier-side symbol |
| F3 | J3-3 `SEL_1` = PB1 (pin 15), J3-4 `SEL_2` = PA8 (pin 18), no resistors on either net on the module | DOCUMENTED | module netlist |
| F4 | SEL_1/SEL_2 are **used**: a three-state CAN-index strap (high/low/floating each), read on every `GetConfiguration()` call; both floating = no override | DOCUMENTED | `upstream/firmware/boards/f0_module/port.cpp:134-150`, `io/io_pins.h` |
| F5 | PB1 and PA8 have internal pull-ups enabled in the GPIO setup | DOCUMENTED | `boards/f0_module/board.h:238,335` |
| F6 | CAN index can also be set over CAN and is saved to flash | DOCUMENTED | `upstream/firmware/can.cpp:148`, `port.cpp` `SetConfiguration()` |
| F7 | Heater PWM = TIM1 channel 1 (`PWMD1`, ch 0) on PA7; 400 kHz counter / 1024 = 390 Hz | DOCUMENTED | `io/io_pins.h`, `heater_thread.cpp:12-13` |
| F8 | PA7 runs as alternate function 2 | DOCUMENTED | `board.h` GPIOA comment |
| F9 | Pump DAC = TIM3 channel 1 (`PWMD3`, ch 0) on PA6; SYSCLK / 1024 = 46.9 kHz at 48 MHz; config enables all four TIM3 channels active-high | DOCUMENTED | `io/io_pins.h`, `pump_dac.cpp:10-30` |
| F10 | TIM14 is the system tick | DOCUMENTED | `mcuconf.h:143` (`STM32_ST_USE_TIMER 14`), upstream commit `2bb80d2` |
| F11 | PA7 has TIM1_CH1N, PA8 has TIM1_CH1, PB1 has TIM3_CH4 (and TIM14_CH1, TIM1_CH3N) | DOCUMENTED | KiCad 10 library `MCU_ST_STM32F0.kicad_sym`, symbol `STM32F042K_4-6_Tx` alternates. AF numbers (AF1 for PB1/TIM3) still FROM MEMORY: check DS10152 |
| F12 | Unrouted MCU pins on the module: PA4, PA5, PA9, PA10, PA15, PF0, PF1 | DOCUMENTED | module netlist (`unconnected-(U2-...)` nets) |
| F13 | Sensor type is fixed to LSU 4.9 in f0 firmware; ESR drive on PB7 through 22k (R6); 4.2 (PB3, 6.8k) and ADV (PB4, 47k) drives are separate pins, so no lambda-x2-style crosstalk | DOCUMENTED | `port.cpp` `GetSensorType()`, module netlist |
| F14 | F1 boards scale their aux output by (82+160)/160 = 1.51, so 3.3 V full scale is about 5.0 V | INFERRED | constant `AUXOUT_GAIN` in `boards/f1_rev3/wideband_board_config.h:47`; resistor values not read from a schematic |
| F15 | The analog-output code (`auxout.cpp`, 8-point curve per output) is only built for boards that define `AUXOUT_DAC_PWM_DEVICE` (F1 boards); f0 does not | DOCUMENTED | `grep AUXOUT_DAC_PWM_DEVICE boards/*/*` |
| F16 | f0 shares the `Configuration` struct that already holds the aux curves (256 bytes, 1 KB flash page); f0 has no UART/TunerStudio and no `LoadDefaults()`, so the curve must be compiled in | DOCUMENTED / INFERRED | `boards/port.h`, `boards/f0_module/wideband_layout.ld:11`, `halconf.h` |

## Attempt log

| # | Proposal | By | Result |
| --- | --- | --- | --- |
| A1 | Module has no free pin, so analog out needs a module change | Sonnet 5.5 | **Wrong premise.** Counted 14 pads from the carrier symbol; the module has 16 (F2), and two strap pads exist (F3) |
| A2 | Reuse SEL_2 (PA8) for PWM, "SEL pads unused by firmware" | Sonnet 5.5 | **Rejected.** SEL pads are a CAN-ID strap (F4); the grep that "showed" them unused was cut off by `head`. PA8's TIM1_CH1 is the complementary pair of the heater's TIM1_CH1N (F7, F8, F11), so it cannot carry an independent duty without disturbing the heater timer |
| A3 | Reuse SEL_1 (PB1) as TIM3_CH4 | Opus 5.5 | **Current proposal**, below. Needs F11 confirmed |

## Current proposal (A3)

- **Pin:** module pad J3-3 (`SEL_1`, PB1) becomes the analog-out PWM, TIM3 channel 4, same 46.9 kHz period as the
  pump DAC (F9), 1024 steps (about 4.9 mV per step at 5 V full scale) [INFERRED].
- **Cost:** the strap no longer sets the CAN index on this build. CAN-set index (F6) still works. SEL_2 stays a strap
  input but alone it can only pick a subset of indexes; simplest is to drop strapping on this build.
- **Firmware (our fork, not upstream):** in `f0_module`, set PB1 to alternate function 1, remove the strap read for
  PB1, define `AUXOUT_DAC_PWM_DEVICE PWMD3` with channel 3, share TIM3 with the pump DAC (don't start TIM3 twice),
  and add the aux curve to the f0 configuration (F16).
- **Carrier:** RC (or two-stage RC) low-pass from J3-3, then a non-inverting op-amp with gain about 1.5 to reach
  0-5 V, output through a series resistor to a new terminal, with clamp diodes. The op-amp must swing to 5 V, so
  either a rail-to-rail part on a supply above 5 V or a stated lower full scale. Values not chosen yet.
- **No module change.** The proven module stays as upstream built it.

## Weak points of A3 (2026-10-23)

| Risk | Assessment | Tag |
| --- | --- | --- |
| PWM couples into analog on the module | SEL_1 trace is 6.0 mm on F.Cu; nearest same-layer nets are GND and `Net-(U2-PB0)` (battery-sense ADC, 100k/10k divider with 1 uF C6) at about 0.72 mm (centerline estimate). No pump/Nernst nets nearby. Low risk; inner layers not checked | DOCUMENTED (module `.kicad_pcb` parse) / INFERRED (risk) |
| Output accuracy follows the MCU's 3.3 V LDO (XC6206, U9), not the 3.0 V reference (REF3033, U3) | A PWM DAC's full scale is its supply. LDO tolerance (about 2%, FROM MEMORY) on a 10-20 AFR / 0-5 V scale is about 0.2 AFR | INFERRED |
| Ground offset between the wideband and the receiving ECU | Heater current returns through ground; a single-ended 0-5 V input sees the offset. Every analog wideband has this; needs a signal-ground wire to the ECU's sensor ground | INFERRED |
| Shares TIM3 with the pump DAC | Same period, independent duty per channel; pump loop untouched if TIM3 is started once | INFERRED from F9 |
| Running upstream firmware on the new carrier | PB1's pull-up into the carrier filter reads as a strap and changes the CAN index. Our firmware must be flashed first | INFERRED from F4, F5 |

Mitigations to adopt: on the carrier, square the PWM with a small CMOS buffer powered from a precision reference so full
scale no longer depends on the LDO; add a firmware gain/offset trim checked with a multimeter at bring-up; bring out a
signal-ground terminal next to the analog output.

## Comparison with lambda-x2 (2026-10-23)

From the lambda-x2 netlist (`../rusefi-hardware/lambda-x2/lambda-x2.kicad_sch`, KiCad 10 export) [DOCUMENTED]:
- Analog out is the same idea as A3: MCU PWM (PC6, PC8) -> two RC stages (3.3k/100n, twice) -> MCP6002 (U7)
  non-inverting, feedback 82k/160k (gain 1.51) -> 330R and ESD5V0D9B -> connector. Its 3.3 V is also an XC6206
  with a REF3033 for the ADC, so it has the same supply-tied accuracy.
- It also uses a hardware CAN-ID strap (`ID_SEL1` on PC13 in `upstream/firmware/boards/f1_dual*/io/io_pins.h`).
- 291 parts, STM32F103RCT6, JDY-33 Bluetooth, two EGT chips, 24-pin automotive connector.

So switching boards gives the same analog circuit already routed, not a better one. Decision proposed: keep the f0
module and copy lambda-x2's output stage onto our carrier, plus the reference buffer and trim above.

## Alternatives kept on record

- **Module revision:** route PA9 or PA10 (unrouted, F12) to a new pad. These are TIM1 channels [FROM MEMORY], so they
  would run at the heater's 390 Hz (F7) and need heavier filtering, or a timer change. More work, new module.
- **Carrier-side MCU:** a small MCU on the carrier listens to CAN and outputs the voltage. No module or module-firmware
  change, but a second firmware to write and keep.

## Open questions

1. AF number for PB1/TIM3_CH4 (DS10152).
2. Flash headroom on the 32 KB F042 (build it).
3. What 0-5 V scaling do Speeduino and FlashPro expect, and is 10-bit at 46.9 kHz plus filtering fast enough (lambda
   updates around 100 Hz)?
4. Carrier design: see `docs/carrier.md`.
