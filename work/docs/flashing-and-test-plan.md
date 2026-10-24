# Flashing and test plan — for Logan and Claude

2026-10-23, Codex; scoped against `4e4b5a5`. This is an implementation/test handoff, not permission to buy tools,
connect a vehicle, flash attached hardware, or publish. PCB and production firmware unchanged.

## Recommendation in plain language

Only the STM32 microcontroller gets firmware; the op-amp, reference and other analog chips do not.
Use an **ST-LINK-compatible SWD programmer for initial programming and recovery**, with a cable/adapter matched to the
module's Tag-Connect pads. This is a recommendation, not a purchased or owner-selected tool.
ST's [STM32CubeProgrammer](https://www.st.com/en/development-tools/stm32cubeprog.html) supports Linux, ST-LINK/SWD,
memory readback and verification (DOCUMENTED, checked 2026-10-23). Exact probe and cable remain UNKNOWN.
The board's CAN bootloader is a later update route; it must already be installed and healthy. A blank chip cannot run it.
Do not assume CubeProgrammer's CAN support speaks this project's custom rusEFI CAN protocol.

## Verified programming facts

| Fact | Evidence |
| --- | --- |
| MCU is STM32F042K6Tx | DOCUMENTED actual module PCB, U2; `firmware/boards/f0_module/board.h:53` |
| Module J2 is TC2030-IDC-NL, six pads | DOCUMENTED `hardware/board_module/wideband_controller.kicad_pcb`, footprint/pads inspected with pcbnew |
| J2 pad 1 +3V3; 2 SWDIO; 3 nRESET; 4 SWCLK; 5 GND; 6 unconnected SWO | DOCUMENTED PCB nets; MCU SWDIO at pad 23, SWCLK at pad 24, nRESET at pad 4 |
| Bootloader 0x08000000–0x080017FF; app 0x08001800–0x08007BFF; config 0x08007C00–0x08007FFF | DOCUMENTED linker expressions `firmware/boards/f0_module/wideband_layout.ld:5-11`; addresses calculated from those sizes |
| Packaged combined image is 31,744 bytes; app+CRC is 25,600 bytes; last four app bytes hold CRC | DOCUMENTED packaging operations `firmware/boards/f0_module/build_wideband.sh:26-40` and validation in `bootloader/bootloader.cpp:22-33` |
| Raw successful compilation is not a finished flash package | DOCUMENTED local `firmware/build/wideband.bin` is 27,088 bytes, whereas bootloader checks the padded app plus CRC; packaging is required |

The pad table is an engineering mapping, **not a ready-to-wire guide**. Before Logan connects anything, produce an annotated
board image showing pad 1 and cable orientation, and verify the exact probe's connector pinout. Use signal names, not a
generic cable color chart. Target-voltage sense is not permission to power the heater from the programmer. Select and
verify one power arrangement, common ground and target voltage first; avoid back-powering from simultaneous sources.

### F7 heater coverage — DONE, 2026-10-23 (Claude Opus 5.5)

`test/tests/test_heater_update.cpp`, 13 tests through `Update()`; two mutants caught; host suite 64/64. Found no bug; found
that f0 without CAN assumes 13 V (owner decision D11). Details in `firmware.md`. No real sensor was heated.

### F8 static stack estimate — DONE as an estimate, 2026-10-23 (Claude Opus 5.5)

`python3 work/checks/stack_estimate.py [ELF] [-v]` (in `run_all.py`): per-thread worst case from the f0 ELF's disassembly;
every thread fits, smallest margin 80 B (pump thread), CAN TX 312/512 B. Fails loudly on a non-f0 build or a missing thread.
Limits in `firmware.md`. The hardware high-water measurement in F8 remains to do at bring-up.

### F3-F6 aux-output host tests — DONE, 2026-10-23 (Claude Opus 5.5)

`test/aux_out/` (21 tests, production code on the f0 config, fakes record every PWM/GPIO/CAN call); details in
`firmware.md`. F5 found a real bug: test mode stayed at 1.00 V (16-bit system time wraps at 6.55 s); fixed and shown by
running the same tests against the old `auxout.cpp` (fails exactly at the 2.50/4.00 V points). Trim configuration is
rejected at compile time outside 0.8-1.2 gain / +-0.5 V offset. F6 (2026-10-23): the production CAN TX thread loop (`can.cpp`, unchanged) runs in the harness for a set number of 10 ms windows: one output update per cycle with frames acknowledged and with no node on the bus (every send `TIME_IMMEDIATE`, every window 100 ticks), through the 16-bit tick wrap, lambda through the thread, and test mode 1.00/2.50/4.00 V end to end with the bus down. Mutants: upstream's 100 ms blocking send fails 3 tests, the loop without `UpdateAuxOut()` fails 5. A host scheduler, not real-time proof on the chip. (F7 and F8 below.)

### F2 package build and validator — DONE 2026-10-23 (Claude Opus 5.5)

`python3 work/checks/fw_package.py build [OUT]` builds the bootloader and app into a fresh directory (default
`work/fw-build/<commit>/`, gitignored) with `BUILDDIR` and an explicit `ULIBS`, and never touches `firmware/build`,
`deliver/` or the tracked `for_rusefi/` files. It writes upstream's three files plus `manifest.json` (commit, tree-dirty
flag, tool versions, flash map, bytes used/free, CRC, SHA-256 of each file) and `build.log`.
`fw_package.py check FILE` validates any of the three: exact sizes (25600 / 31744), the CRC through the bootloader's own
`isAppValid()` (extracted from `bootloader.cpp`, compiled on the host with the project's `crc.cpp`) and through zlib, vector
tables (SP in RAM; reset, NMI, HardFault, SVCall, PendSV, SysTick and IRQ vectors Thumb and inside their own partition), no
config page; the layout constants are checked against `wideband_layout.ld`.
Evidence: upstream's shipped `for_rusefi/wideband_image.h` passes, and the header writer reproduces it byte-for-byte;
staged build at f2a437c: app 20,944 B used, 4,652 B free, CRC 429ca981, all checks pass; a second build in another
directory is byte-identical (all three files). `checks/test_fw_package.py`: 21 cases (bad CRC, swapped CRC order,
truncated, extended, linked without the bootloader offset, Thumb bit cleared, vector into the config page, SP outside RAM,
bad header name/length, config page appended, shifted app, bootloader vector into the app; vector faults carry a fresh CRC
so only the vector check can catch them; isAppValid() alone accepts/rejects), 0 wrong verdicts. Both checks in `run_all.py`.
Not covered: whether the chip boots it (hardware), the bootloader region beyond its vector table, option bytes.

### First-flash procedure to finish before hardware arrives

1. Produce a disposable/staged build with board identity, source commit, tool versions, image hashes and flash map.
   The upstream packaging script deletes build/delivery output and overwrites tracked `for_rusefi/` files; do not run it
   casually in the live checkout. Adapt its operations to a fresh output directory without changing the delivered format.
2. Independently verify package length, app offset, vector table ranges, CRC bytes and that no config-page bytes are included.
   Verify CRC against the project's implementation/test vectors, not just a packer validating its own checksum.
3. Confirm probe/cable orientation and rails with sensor, ECU and heater load disconnected. Establish a reviewed
   current-limited power arrangement before any power-up; exact source and limit still need design.
4. Connect/read chip identity first. Back up existing flash/config and record protection settings before an authorized write.
   No mass erase, readout-protection change or option-byte change as a troubleshooting default.
5. Once approved, program the validated combined image at 0x08000000, verify readback, reset and confirm application startup.
   Preserve configuration on subsequent updates. On an unfamiliar board, prove readback and recovery before any sensor test.

No flashing command is executed by this document or the new guard test.

## What we can test without owning the board

| Layer | Test value | What it cannot prove |
| --- | --- | --- |
| Native host tests | Real C++ logic with fake inputs/time/hardware; sanitizers and boundary cases | STM32 registers, interrupts, pin timing, actual sensor/heater behavior |
| ARM compilation + image inspection | Board configurations, link ranges, sizes, boot/app packaging and CRC | Successful boot, stack high-water margin or analog correctness |
| Circuit simulation | Filter/stability/load/supply/clamp hypotheses | Device tolerances absent from model, assembly faults, real transients |
| Full MCU emulation | Potential instruction/peripheral integration tests if exact models exist | Not a ready-made replacement for this PCB or LSU sensor |
| Hardware-assisted tests later | SWD register/stack inspection, meter endpoints, CAN behavior | A meter alone cannot demonstrate ripple, fast ringing or timing margins |

DOCUMENTED: local QEMU's machine list has STM32F100/F2/F4 boards, not this F042. Its [STM32 documentation](https://www.qemu.org/docs/master/system/arm/stm32.html)
also lists missing CAN/DMA support for that family of models. Therefore do not run an F042 binary on an unrelated board
and count it as a firmware test. Renode is not installed here; an exact F042 peripheral model has not been established.
INFERRED budget recommendation: prioritize native tests, image checks and targeted circuit simulations. Cap emulator
feasibility investigation at one short pass; no custom MCU model project without a separate decision.

## Tests designed for Claude to implement

Use actual production functions with fake HAL calls where possible. Copying an equation into a test proves the copy,
not the firmware. Keep test seams small and compile production paths for both f0_module and a non-f0 regression target.
Write down expected behavior before changing production code; preserve intentional failing tests as evidence.

| ID / priority | Stimulus | Required assertion / artifact |
| --- | --- | --- |
| F1 first | CAN boot DATA offsets 0, 1, 25592, 25598, 25600, 26622, 26624, 65534; lengths 0,1,2,7,8,10 | No write outside 25 KiB app partition, no payload over 8 bytes, alignment enforced. Capture ACK/NAK and write addresses. Existing guard fails; see below. |
| F2 | Package valid image, corrupt one app byte, swap CRC byte order, truncate/extend, wrong vector/offset | Independent validator accepts only matching image format; bad packages never reach a flasher; config excluded |
| F3 | Invoke actual auxiliary conversion below/within/above range; nonzero channel; trim offsets/gains | Correct clamped duty; only TIM3 channel index 3 changes; pump channel/frequency/period unchanged. Reject invalid trim configuration explicitly. |
| F4 | Nernst exactly at target +/-0.1, just inside/outside; lambda 0.6, below, NaN/infinity; heater warmup/fault | Output follows declared validity policy. Current comparisons use strict boundaries; non-finite handling must be tested and decided, not assumed. |
| F5 | SEL_2 boot strap low/high/floating; fake clock around 10s boundaries and wrap | 1/2.5/4 V test sequence when enabled, normal output otherwise; no pump-timer restart or accidental strap-mode change |
| F6 | CAN all mailboxes busy/no ACK, heavy RX traffic, reconnect | Analog update still occurs each scheduled cycle; f0 transmit uses immediate timeout; normal target behavior unchanged. Host scheduler test is not real-time hardware proof. |
| F7 | Heater preheat/ramp/closed-loop/timeout and synthetic sensor disconnect | Existing tests remain green; extend dropout and boundary coverage. Never demonstrate a failure by uncontrolled heating of a real sensor. |
| F8 | Boot and maximum-traffic instrumentation | Measure each stack's high-water mark, check overflow behavior and reset recovery; 0 heap free does not establish stack safety |
| C8 | Output-load sweep plus reference, feedback resistor and op-amp offset corners | Endpoint accuracy and monotonicity across an explicitly chosen load/error budget; include clamp conduction and actual supply feed |
| C9 | Output forced positive/negative, powered/unpowered, partial power sequencing | Bound +5V back-feed, device currents and resistor pulse/steady dissipation. Do not use an ideal sink as proof the rail survives. Simulation first, no battery short experiment. |
| C10 | Shared power/signal-ground resistance sweep and open main-ground wire | Account for receiver-ground current as well as output error; confirm receiver wiring policy before connection |

### Already executed during this scope

- DOCUMENTED: fresh host build in `/tmp/wideband-host-tests-08CvZQ`, 43/43 tests pass. ASan/bounds instrumentation is built;
  `ASAN_OPTIONS=detect_stack_use_after_return=1:detect_leaks=0` was used. Default run passed assertions then LeakSanitizer
  failed under the execution environment; leak checking is **not verified**, not silently counted as passed.
- DOCUMENTED: absolute `BUILDDIR` allows a fresh host build without moving ARM `firmware/build`. Reproduce from `test/`:
  create a fresh absolute temp directory, create its `obj`/`lst`, `make -j4 BUILDDIR=<absolute-directory>`, then run its binary.
  These 43 tests cover utilities, sampling and heater logic: `test/Makefile` and `firmware/wideband.mk` do not compile `auxout.cpp`.
- DOCUMENTED: `python3 work/checks/audit_bootloader_bounds.py` compiles the **actual source guard** with a recording flash stub.
  It does not execute a bootloader image. Offset 25600 / length 2 is accepted into config address 0x08007C00; offset 25598 /
  length 8 crosses the app/config boundary. These are valid-size CAN payload cases. Length 10 is a separate synthetic robustness case,
  not a claim that the CAN driver supplies it in practice. A zero-byte call makes no flash write and is excluded from failure counts.

### Bootloader finding to fix first — FIXED 2026-10-23 (Claude Opus 5.5)

Status: done as specified, protocol unchanged. `firmware/boards/f0_module/bootloader/bootloader_bounds.h` holds
`IsAppWriteAllowed(offset, length, appSize, wordSize)`: length at most 8, offset and length word-aligned, offset at most
`appSize`, `length <= appSize - offset` (offset checked first, so no wrap). `bootloader.cpp` passes `appFlashSize`
= address of linker symbol `__appflash_size__` (0x6400 = 25600 in the built ELF, read back from the binary). Zero-length
frames stay accepted with no write, as before. Evidence: `python3 work/checks/audit_bootloader_bounds.py` 52 cases,
0 unsafe accepts, 0 valid writes refused (4 new must-accept cases); with the old 26 KiB bound put back as a mutant it fails
(3 unsafe); 8 new gtest cases `BootloaderBounds.*`, host suite 51/51 with ASan and LeakSanitizer on (leak check runs on
this machine; it did not in Codex's environment). Bootloader 5520 of 6144 bytes (was 5508). Not done: no hardware,
no CAN updater run. Left as found (upstream): `sendNak()` is empty, so a refused frame gets no reply and the updater
times out; `isAppValid()` and `EraseAppPages()` still hard-code 25600 bytes / 25 pages (match the layout today).

Original finding:

`firmware/boards/f0_module/bootloader/bootloader.cpp:188-200` accepts offsets below **26 KiB**, while the linked app partition
is **25 KiB**, and never bounds offset + payload length. `shared/flash.cpp:75-93` applies the supplied address and length
without a partition guard. INFERRED consequence: malformed updater traffic can attempt to program config or cross flash end;
actual programming success depends on flash state. This is a pre-existing upstream bug, not caused by the analog-output change.
Minimum repair: derive bounds from linker-defined app size; validate DLC and alignment; check `length <= appSize - offset`
after validating offset, then test accepted/rejected packets and config preservation. Keep bootloader protocol unchanged.

## Meter-only hardware bring-up sequence (draft; not yet authorized wiring)

H1: unpowered continuity/short inspection against a net-specific expected resistance table. Do not use a universal
“all rails >1k” rule: legitimate circuitry can measure below that. No power until supply/current limiting is specified.
H2: sensor and receiver disconnected, verified current-limited supply; measure rails and confirm no unexpected heat.
H3: identify/read/verify programmed MCU and reset into application, still without sensor/heater load.
H4: approved test-strap wiring; measure each 10-second output plateau, first high-impedance meter only, then known
resistive loads. Record actual resistor values, meter accuracy, rails, output and temperature; endpoint budget must be set first.
H4b (W1, D10 watchdog): flash the `WB_WATCHDOG_SELFTEST` test build (`docs/firmware.md` "Watchdog"); the module must restart
about every 21 s (LED start-up pattern). Then reflash the release image.
H5: reset/no-CAN/reconnect tests; record visible sequence continuity. A meter is not a PWM timing instrument.
H6: only after heater/sensor wiring, power and current limits are reviewed, connect the LSU sensor for controlled bring-up.
No ECU connection, deliberately opened live heater ground, or output-to-battery short in this first test series.

## Bounded handoff

Claude: read AGENTS.md, STATE.md, this plan and audit round 3. First implement F1's bounds fix plus production-path tests;
then a non-destructive package validator (F2), then real aux-output host tests (F3–F6). Continue C8–C10 circuit verification
in parallel only as budget permits. Deliver logs with commit/tool identity, explicit skips and failed cases; no confidence percentages.
Do not regenerate PCB, buy equipment, flash hardware, push or publish as part of this handoff. Ask Logan only when an exact
probe/cable/power choice is needed; the unambiguous software tests can proceed now.
