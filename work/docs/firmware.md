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
for the firmware build. Update 2026-10-23: fresh host build passes 43 tests with leak checking disabled due the execution
environment; these do not compile the added aux-output code. See `flashing-and-test-plan.md` for coverage and first-flash planning.

## Budget on the STM32F042K6 (measured with `arm-none-eabi-size -A`)

| | Stock `2bb80d2` | `analog-out` | Limit |
| --- | --- | --- | --- |
| App flash (vectors + xtors + text + rodata + data) | 20,316 B | 20,900 B | 25,596 B (32k - 6k bootloader - 1k config - 4 CRC, `build_wideband.sh`) |
| RAM left (`.heap`) | 16 B | **0 B** | 5,888 B ram0 total; 2 KB is the two stacks |

RAM, not flash, is the constraint: there is no room for another thread, which is why our change has none. RAM is now
full to the byte. No dynamic allocation (`CH_CFG_USE_HEAP`, `CH_CFG_USE_MEMCORE`,
`CH_CFG_USE_MEMPOOLS` are FALSE in `boards/f0_module/chconf.h`) avoids heap growth, but does not establish stack safety;
stack high-water measurement remains required. Any further RAM must come out of something else
(the largest are the CAN RX/TX thread areas, 680 B each, and the two 1 KB stacks).

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
- **Test mode:** SEL_2 tied low at power-up makes the output step 1.00 -> 2.50 -> 4.00 V, 10 s each, repeating,
  instead of the AFR (bench test A1). SEL_2 low also sets CAN index 4 through the strap; harmless on the bench.
- **Trim:** `AUXOUT_TRIM_GAIN` and `AUXOUT_TRIM_OFFSET_VOLTS` in `wideband_board_config.h`, from the A1 readings:
  fit measured = gain x wanted + offset over the three levels, enter both, rebuild and reflash.
- **Scale:** `AUXOUT_FULL_SCALE_VOLTS` = 3.0 x 1.68 = 5.04 V at 100% duty, matching the proposed carrier stage
  (REF3030 buffer, gain 1 + 68k/100k, `carrier.md`). A trim step comes with bring-up.

## Bootloader bounds (fixed 2026-10-23)

The f0 CAN bootloader accepted DATA writes up to 26 KiB into a 25 KiB app partition, reaching the config page (Codex F1).
Fixed with `bootloader/bootloader_bounds.h`, bounds from the linker script; details and evidence in
`flashing-and-test-plan.md`. Upstream's bug, not ours; a candidate to report upstream (owner's call).

## Fault handler on the Cortex-M0 (F9, fixed 2026-10-23)

Found while writing the F2 vector check. `main_hardfault_asm.S` was assembled for `cortex-m3` (`.cpu` directive), so the
f0 build's HardFault entry was `tst.w lr, #4` / `ite eq` / `mrseq` / `mrsne` / `b.w` [DOCUMENTED: objdump of
`firmware/build/wideband.elf`; `arm-none-eabi-as` refuses the same file for cortex-m0: "cannot honor width suffix",
"selected processor does not support `ite EQ'"]. The STM32F042's core is a Cortex-M0 (`stm32f042x6.h` lists only NMI,
HardFault, SVCall, PendSV, SysTick as core exceptions). On QEMU's Cortex-M0 (`microbit`), a forced HardFault through that
entry ends in "Lockup: can't escalate 3 to HardFault" and the C handler never runs [DOCUMENTED run,
`checks/test_fault_entry_m0.py`; an M0 core model, not this chip]. The C handler's `bkpt()` does the same when no debugger
is attached (QEMU run; BKPT escalating to HardFault without a debugger is REPORTED in ST/Nordic forum threads, and M0
software can't read DHCSR to check, also REPORTED). Upstream intended: fault -> save context -> breakpoint for a debugger
-> `NVIC_SystemReset()`. On f0 it was: fault -> lockup, with the heater's hardware timer PWM still running at its last
duty and no watchdog (`HAL_USE_WDG FALSE`) [INFERRED: a timer keeps running while the core is stalled; not tested here].
Fix: the entry uses ARMv6-M instructions only (`.cpu cortex-m0`, also valid on the f1 boards' M3, which build), and
`bkpt()` is empty on the M0 and checks `DHCSR.C_DEBUGEN` on the M3. Test: current entry reaches the C handler; upstream's
entry and a BKPT inside the handler both lock up; the f0 build has 0 Thumb-2-only instructions in its fault entries.
Not tested: the real chip; what the STM32F042 does on lockup. Upstream's bug, a candidate to report (owner's call).
Still open (owner decision D10 in `RELEASE_ASSESSMENT.md`): no watchdog, so a hang that is not a fault leaves the heater
PWM at its last duty.

## Not verified yet

- On hardware: nothing. Needs the module, a carrier with the filter, and a meter (draft tests A1-A3 in `carrier.md`).
- CAN TX thread stack (512 B) now also runs `UpdateAuxOut()`. ChibiOS stack checking is on (`chconf.h`), so an
  overflow halts rather than corrupts, but the margin is unmeasured.
- The 0 V invalid output reads as 10 AFR on a receiver. Owner to decide if another value is better.
- Trim needs a reflash per board, so how the owner flashes the module (SWD probe on the Tag-Connect pads, or rusEFI
  over CAN) is an open question.
