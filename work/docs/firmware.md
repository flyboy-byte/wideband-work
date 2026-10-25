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
  is `AUXOUT_INVALID_VOLTS` (5.0 V = 20 AFR, the lean end, since 2026-10-24; was 0 V). Reason: a closed-loop ECU that
  misses the fault then adds fuel instead of pulling it, and a log shows an off-scale value; 0 V read as a believable
  10 AFR and into a pull-up input floored at 11-12 AFR (outside review N1).
- **PB1 at boot:** the app's and the bootloader's `board.h` set PB1 pull-down (was pull-up), so with R3 4.7k the buffer
  reads low until `InitAuxDac()` hands PB1 to TIM3 (outside review B1). Changing the bootloader means the first flash
  must include the bootloader (SWD), which it does anyway.
- **Heater:** the closed-loop voltage is clamped at 0 V before it is squared into a duty (`heater_control.cpp`,
  upstream code): a sensor hotter than target got up to 100 % duty (Codex round 4 second pass, test
  `HeaterUpdate.HotterSensorNeverGetsMoreHeat`). Bounded before by the overheat stop, which lost the reading.
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

## Heater control tests (F7, 2026-10-23)

`test/tests/test_heater_update.cpp` (13 tests, in the upstream suite, now 64/64): the whole `HeaterControllerBase::Update()`
path every 50 ms with the board's preheat/warmup times, not just `GetNextState()`. Covered: duty = (V_eff/V_supply)^2;
preheat 2 V; supply below 3 V taken as 12 V; heater off at >= 23 V; ramp from 7 V at 0.4 V/s capped at 12 V; standalone
start without CAN (ramp at about 5.6 s with 13 V, about 10.5 s on f0 where the sampler reports 0 V for the first 5 s);
warmup timeout -> Stopped, duty 0; sensor disconnect (reads 0 C) in closed loop stops within 0.5 s and stays stopped;
exact boundaries (closed loop above 750 C, over/underheat beyond 880/680 C for > 0.5 s); CAN "no heat" holds preheat.
Mutants (23 -> 24 V cut-off; > -> >= on closed-loop entry) each fail a test.

Recorded, not changed (upstream's design): **without CAN the f0 assumes a 13 V supply** (`Sampler::GetInternalHeaterVoltage()`
returns 13 after 5 s; `port.cpp` sets the measured value to 0, "TODO"). At 14.4 V running the open-loop phases get about
11 % more effective voltage than intended (preheat about 2.2 V against the 2 V condensation limit in the code's comment;
ramp end about 13.3 V); closed loop corrects through ESR [INFERRED, calculation]. The module already has the hardware:
VBatt_Sense (module pad 7, our protected 12 V) -> R20 100k / R21 10k, C6 1 uF -> MCU PB0 [DOCUMENTED: module PCB nets].
Reading it costs one ADC channel in the sample buffer (about 48 B RAM at 24 samples, INFERRED) with 0 B free: owner
decision D11.

## Analog output host tests (F3-F6) and the test-mode bug they found (2026-10-23)

`test/aux_out/` builds the production `auxout.cpp`, `pump_dac.cpp` and `can_helper.cpp` against the real f0_module board
config, with fake ChibiOS headers (`shim/hal.h`; system time typed from the board's own `chconf.h`) and recording fakes
for the Pwm wrapper, GPIO, CAN and the sensor/heater/config functions. `make -C test/aux_out run`; in `run_all.py`.
21 tests (16 + 5 for F6), expected values from the design, not the code: volts to duty against 5.04 V full scale, clamping, channel 1
ignored, only TIM3 channel index 3 written (pump channel and the one TIM3 start untouched), zero duty before PB1 goes to
AF1; the curve (AFR 10 = 0 V ... 20 = 5 V, clamped); validity (heater not closed loop, Nernst window strict at 0.35/0.55 V,
NaN lambda -> 0 V); test mode; CAN frames sent with TIME_IMMEDIATE.

F6 (2026-10-23): the production CAN TX thread loop (`can.cpp`, unchanged) runs in the harness for a set number of 10 ms windows: one output update per cycle with frames acknowledged and with no node on the bus (every send `TIME_IMMEDIATE`, every window 100 ticks), through the 16-bit tick wrap, lambda through the thread, and test mode 1.00/2.50/4.00 V end to end with the bus down. Mutants: upstream's 100 ms blocking send fails 3 tests, the loop without `UpdateAuxOut()` fails 5. A host scheduler, not real-time proof on the chip.

**Bug found (F5): test mode never left 1.00 V.** The step was `TIME_I2MS(chVTGetSystemTime()) / 10000 % 3`. On the f0,
`CH_CFG_ST_RESOLUTION` is 16 and `CH_CFG_ST_FREQUENCY` 10000 (`boards/f0_module/chconf.h`), so `systime_t` is 16 bits and
wraps every 6.55 s: the millisecond value never reaches 10000 and the step is always 0 [DOCUMENTED: ChibiOS `chtime.h`
typedefs; the host test fails against the old code at 10, 13.2, 20, 29.9, 40, 50 and 3599 s and passes in the first
10 s]. Bench test A1 would have shown 1.00 V only. Fixed: the step comes from `chVTGetTimeStamp()` (64-bit ticks since
boot, what `util/timer.cpp` already uses): no RAM, +544 B flash (64-bit division), 4,108 B flash left.
Other changes for testability, no behaviour change: the compiled-in curve moved to `boards/f0_module/aux_curve.h`
(`port.cpp` and the tests both call it); `AUXOUT_TRIM_GAIN` / `AUXOUT_TRIM_OFFSET_VOLTS` can be set per build
(`make BOARD=f0_module UDEFS='-DAUXOUT_TRIM_GAIN=1.012f'`, after `touch auxout.cpp`: make doesn't rebuild on flag
changes) and a `static_assert` refuses a gain outside 0.8-1.2 or an offset beyond +-0.5 V (a trim corrects 1-2 %).
Recorded, not changed: `SetAuxDac(NaN)` gives full scale (`clampF`; nothing passes NaN today); a +infinite lambda passes
the validity test and reads 5 V; closing the TEST jumper also moves the CAN ID offset to 4 (`GetConfiguration()` reads
SEL_2 as a CAN strap), harmless on the bench. Not covered by host tests: that the CAN TX thread calls `UpdateAuxOut()`
every cycle (the thread loop isn't separable without a refactor), real timer/pin behaviour, stack use (F8).

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
~~Still open: no watchdog~~ added 2026-10-24 (D10, next section).

## Watchdog (D10, added 2026-10-24)

Owner decision D10: a hang that is not a fault must not leave the heater PWM at its last duty. `firmware/watchdog.h`
starts the independent watchdog (IWDG) from the heater thread, after its 1 s settle, and the heater loop refreshes it every
50 ms (`heater_thread.cpp`, under `WB_WATCHDOG`, defined only in the f0 board config). Registers only: 0 B RAM (heap still
0 B, `__heap_base__` = `__heap_end__`), +44 B flash (21,532 B), heater thread stack estimate unchanged (176 of 256 B).
- Timeout LSI/32 x 625: 400 ms at 50 kHz, 500 ms at 40 kHz, 666 ms at 30 kHz (LSI 30-50 kHz FROM MEMORY, F042 datasheet).
  `static_assert`s keep it at least 300 ms (8 heater periods, room for a flash page erase stall) and at most 1 s.
- Halted debugger: the IWDG is frozen while the core is halted (`DBGMCU_APB1_FZ_DBG_IWDG_STOP`), so SWD sessions work.
- Bootloader: a software-started IWDG stops at any reset, including the `NVIC_SystemReset()` that enters the bootloader
  [REPORTED, ST training deck], so flashing over CAN is not interrupted. Assumes option byte WDG_SW at its factory default
  (software watchdog) [FROM MEMORY]: a chip with the hardware-watchdog option set would reset the bootloader too.
- What it catches: the heater loop not running (any hang or busy loop at equal or higher priority, ChibiOS `chSysHalt()`).
  What it doesn't: a thread that blocks forever while the heater loop keeps running (for example the sampler stalling, so
  the heater acts on stale readings). Catching that needs a check-in per thread, which needs RAM: none is free.
- Evidence: disassembly of the f0 ELF: IWDG base 0x40003000, keys 0xCCCC/0x5555/0xAAAA in `HeaterThread`, the 0xAAAA
  store between `Update()` and the 50 ms sleep in the loop. Host tests `test/tests/test_watchdog.cpp` (5): register
  sequence, wait for SR, kick, timeout range, limits. Mutants: no SR wait and values-before-unlock each fail 2 tests;
  a 1.3 s timeout fails to compile. `BOARD=f1_dual` still builds (no watchdog there).
- Bench test W1 (needs the module, LED only): build with `make BOARD=f0_module UDEFS=-DWB_WATCHDOG_SELFTEST`; the heater loop
  stops refreshing 20 s after boot, so the module must restart about every 20.4-20.7 s (LED back to the start-up pattern).
  The release image never has that flag. Not tested on hardware.

## Not verified yet

- On hardware: nothing. Needs the module, a carrier with the filter, and a meter (draft tests A1-A3 in `carrier.md`).
- CAN TX thread stack (512 B) now also runs `UpdateAuxOut()`. Static worst case (F8, `work/checks/stack_estimate.py`,
  2026-10-23, build 1c8f942): CAN TX 312 of 512 B; heater 168/256, pump 176/256, sampling 164/256, CAN RX 220/512, main
  188/1024, deepest single interrupt 184/1024 (nesting not modelled). Smallest margin 80 B (pump). It is an estimate from the
  disassembly: indirect calls are charged the deepest address-taken function (overestimates), ChibiOS's reserved context
  space is counted again (overestimates), interrupt nesting is not counted (underestimates the exception stack). A runtime
  high-water mark on the board (ChibiOS fills stacks when CH_DBG_FILL_THREADS is on) is still the real measurement.
- ~~The 0 V invalid output reads as 10 AFR on a receiver. Owner to decide.~~ Decided 2026-10-24 (owner delegated): 5.0 V, see "Invalid lambda".
- Trim needs a reflash per board, so how the owner flashes the module (SWD probe on the Tag-Connect pads, or rusEFI
  over CAN) is an open question.
