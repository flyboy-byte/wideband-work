# Firmware: building, and our analog-output change

Last verified: 2026-10-23, branch `analog-out`, arm-none-eabi-gcc 16.2.0 (Arch), on top of upstream `2bb80d2`.

## Build

```bash
git submodule update --init --depth 1 firmware/ChibiOS firmware/libfirmware firmware/ext/openblt
cd firmware/boards/f0_module/bootloader && bash build_bootloader.sh   # once; the app links the bootloader .o
cd ../../.. && make -j12 BOARD=f0_module                              # app: firmware/build/wideband.elf
arm-none-eabi-size -A build/wideband.elf
```

`boards/f0_module/build_wideband.sh` does both and packages images, but it also overwrites the tracked files in
`for_rusefi/`; don't commit those unless we mean to. `cmsis-svd`, `kicad-libraries` and `test/googletest` aren't needed
for the firmware build. Unit tests (`test/`) not run yet.

## Budget on the STM32F042K6 (measured with `arm-none-eabi-size -A`)

| | Stock `2bb80d2` | `analog-out` | Limit |
| --- | --- | --- | --- |
| App flash (vectors + xtors + text + rodata + data) | 20,316 B | 20,756 B | 25,596 B (32k - 6k bootloader - 1k config - 4 CRC, `build_wideband.sh`) |
| RAM left (`.heap`) | 16 B | 8 B | 5,888 B ram0 total; 2 KB is the two stacks |

RAM, not flash, is the constraint: there is no room for another thread. That is why our change has none.

## The change (`git diff master -- firmware`)

All behind `AUXOUT_SEL1_PWM_CHANNEL`, defined only in `boards/f0_module/wideband_board_config.h`:

- **Pin and timer:** module pad SEL_1 = PB1, alternate function 1 = TIM3_CH4 [DOCUMENTED: ST
  `STM32_open_pin_data`, `GPIO-STM32F042_gpio_v1_0_Modes.xml`, `GPIO_AF1_TIM3` on PB1]. TIM3 is the pump DAC timer
  (`PWMD3`, 1024 counts, 46.9 kHz at 48 MHz), already started with all four channels active-high, so the output is just
  another channel's duty (`SetPumpTimerDuty()` in `pump_dac.cpp`). The pump DAC's period and channel 1 are untouched.
- **Update:** `UpdateAuxOut()` (in `auxout.cpp`) runs once per CAN TX period from the existing CAN TX thread
  (`can.cpp`), not from its own thread. Other boards keep their aux thread unchanged.
- **Curve:** compiled in, in `boards/f0_module/port.cpp` `GetConfiguration()`: AFR 10.0 = 0 V to AFR 20.0 = 5 V,
  linear, 8 points; source = AFR channel 0 (14.7 x lambda). f0 has no UART/TunerStudio to edit it.
- **Invalid lambda:** while the heater isn't in closed loop or lambda fails the CAN frame's validity test, the output
  is `AUXOUT_INVALID_VOLTS` (0.0 V).
- **Strap:** SEL_1 is never read as a strap (its pad mode is never changed back to input); it counts as floating.
  SEL_2 still straps: low = CAN index 4, floating = no override, high = index 1. CAN-set index still works.
- **Scale:** `AUXOUT_FULL_SCALE_VOLTS` (5.0) = output at 100% duty. Must match the carrier's reference and gain once
  chosen; a trim step comes with bring-up.

## Not verified yet

- On hardware: nothing. Needs the module, a carrier with the filter, and a meter (draft tests A1-A3 in `carrier.md`).
- CAN TX thread stack (512 B) now also runs `UpdateAuxOut()`. ChibiOS stack checking is on (`chconf.h`), so an
  overflow halts rather than corrupts, but the margin is unmeasured.
- The 0 V invalid output reads as 10 AFR on a receiver. Owner to decide if another value is better.
- The test mode for fixed voltages (1.00/2.50/4.00 V) and the trim are not written yet.
