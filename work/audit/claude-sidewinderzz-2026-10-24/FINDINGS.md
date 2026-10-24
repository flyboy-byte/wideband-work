# Outside review, board r41, 2026-10-24

Reviewer: Claude (Anthropic), Claude Code cloud session, run for Shelby (GitHub `sidewinderzz`). Mode B (full repo),
done without reading `work/docs/` conclusions first: the netlist was read straight from the board file, the firmware
was rebuilt and its tests rerun, and the analog stage was re-modelled with the parts the existing decks leave out.
Commit reviewed: `fad8032` (branch `analog-out`). Evidence tags as in `AGENTS.md`.

## Verdict

**Would I order these files as they are? Not quite.** One cheap fix first: at every power-up, the 0-5 V output sits at
full scale (5.04 V = 20 AFR, full lean) for about 0.8 s while the bootloader runs. If the app is invalid, or a CAN
update is in progress, it stays there. The cause is PB1's internal pull-up against the 100k pull-down R3 (B1). Changing
R3 to 4.7k, or turning off PB1's pull-up in both `board.h` files, fixes it. Everything else I found is a RISK or a NOTE.

## Findings

| ID | Severity | Location | Evidence (numbers) | Smallest fix |
| --- | --- | --- | --- | --- |
| B1 | BUG | R3 (100k, 46.8, 96.8 mm) with module pad SEL_1 = PB1; `firmware/boards/f0_module/bootloader/cfg/board.h:333`, `firmware/boards/f0_module/board.h:335` | DOCUMENTED: both the bootloader and the app set PB1 as an input with its pull-up on (`PIN_PUPDR_PULLUP(GPIOB_PIN1)`). The bootloader blinks for 20 x 40 ms before it boots the app (`bootloader.cpp:251`), and it never boots while `bootloaderBusy \|\| !isAppValid()` (`:259`). The app only hands PB1 to TIM3 in `InitAuxDac()` (`main.cpp:40`). FROM MEMORY: F042 pull-up 25/40/55 k (min/typ/max); 74LVC1G125 V_IH = 2.0 V at VCC 2.7-3.6 V (`docs/carrier.md` uses 0.7 x VCC = 2.1 V). INFERRED: PB1 = 3.3 V x 100k / (100k + R_pu) = **2.64 / 2.36 / 2.13 V**, so the buffer reads it as high in every case (and is near its threshold at the weak end). The buffer outputs 3.000 V, and the stage drives J3-5 to **5.04 V (20 AFR)** within a few ms. It stays there **about 0.8 s at every key-on**, or indefinitely with an invalid app or a CAN firmware update. This contradicts the stated intent "100k pull-down (output 0 V while the MCU boots)" (`docs/carrier.md:61`, `gen/gen_carrier_sch.py:30`). Condition that makes it matter: a Speeduino using the input for closed-loop EGO correction sees full lean and adds fuel up to its authority limit. A logger or gauge shows a lean spike at every start. | Hardware, which works with any firmware: **R3 100k -> 4.7k** (same 0402 footprint, a Basic part). This gives 3.3 x 4.7 / (4.7 + 25) = 0.52 V worst case, below V_IL 0.8 V, with 0.7 mA load on PB1 while it drives the PWM. Firmware, which also works: `PIN_PUPDR_PULLDOWN(GPIOB_PIN1)` in both `board.h` (the strap read sets its own pulls, `port.cpp:readSelPin`, so the strap code is unaffected). This needs the bootloader reflashed. I would do both. |
| R1 | RISK | D3 clamp to +5V vs full scale into a low-resistance pull-down; `work/sim/load_accuracy.sh` | DOCUMENTED (the deck): `load_accuracy.sh` and `stability.sh` have no D3/D4, a fixed 12 V op-amp supply (no R9) and no +5V tolerance. The "5.002 V into 4.7k" result is therefore without the clamp. Modelled here (`clamp.sh`, behavioral op-amp with V_OH = VOP12 - 1.5 V, 1N4148 vendor model; both FROM MEMORY, **not TI's model**): to put 5.00 V on J3-5 into 4.7k, the 330R/R11 node must sit at about 5.5 V. With +5V at 4.8 V, D3 conducts 2-3 mA. The op-amp supplies that current through R9, VOP12 falls to about 7.8-8.4 V, and the op-amp runs out of headroom: **J3-5 = 4.935 V (25 C) / 4.836 V (85 C) at 13.8 V battery, 4.913 / 4.810 V at 12 V** (`clamp-results.txt`). That is 0.13-0.38 AFR low at the top. At +5V = 5.0 V and 25 C it holds 5.000 V. Into 10k and 100k it holds 5.000 V in every case. FROM MEMORY: L78M05AB is about +-2 % at 25 C, wider over temperature. | Re-run `load_accuracy.sh` with D3, D4, the R9/D5 supply and +5V at 4.8 / 5.0 / 5.2 V on TI's model. If it confirms, either state "receiver input >= 10k for full scale" in the wiring notes (most ECU inputs are, INFERRED), or lower R11 (which raises the C1 fault current, the trade-off Codex noted). No board change needed if the 4.7k case is out of scope. |
| N1 | NOTE | `AUXOUT_INVALID_VOLTS (0.0f)`, `wideband_board_config.h` | Raised once, as `REVIEW.md` allows for "known and accepted" items. The known item is accuracy below 1 V into a pull-up. Its consequence for the invalid state is new: the warm-up / invalid code is 0 V, and into a pull-up input the output floors at **0.63-0.97 V** (your `docs/carrier.md:214`, D/E rows). That reads as **11.3-11.9 AFR**, a plausible rich reading, not an obvious fault. The REPORTED Honda EGR-lift input pulls up. | Owner decision: keep 0 V and tell the receiver to ignore values below about 1 V (FlashPro can't), or make invalid = 5.0 V (20 AFR, clearly off-scale lean for a logger). One `#define`. |
| N2 | NOTE | `work/docs/carrier.md` op-amp headroom paragraph | INFERRED from `clamp-results.txt`: with a 4.7k load the op-amp needs about 5.9 V out and draws about 1.8 mA through R9. Full scale into 4.7k therefore needs roughly 10 V or more of battery even with the clamp ignored (the 7.5 V figure in `STATE.md` is for 100k). | Add the load to the stated supply corner. |
| N3 | NOTE | toolchain | DOCUMENTED (runs here): the firmware also builds with **arm-none-eabi-gcc 13.2** (Ubuntu 24.04), besides your 16.2. The app ends at 0x08006FC4, so it takes **22,468 B of the 25,600 B partition**, and the heap base = RAM end (0 B free, as stated). The bootloader builds. The host suite gives **69/69 PASS** under ASAN, and `test/aux_out` gives **21/21 PASS**. | none |

## Checked and found correct

- **Netlist read from the board file** (`netlist-from-board.txt`, parsed without pcbnew by `board_parse.py`). It matches
  the hand-off chain exactly: PB1 -> R3 100k to GND -> U4 74LVC1G125 (OE = GND, VCC = REF3030 out) -> R4 3.3k / C13 100n
  -> R5 3.3k / C14 100n -> U6A +IN. Gain: R6 68k from J3-5 (AOUT_J) and R7 100k to GND. C15 1 nF goes from U6A out to -IN.
  Then R8 330R -> D3 (K to +5V) / D4 (K to AOUT) -> R11 470R -> J3-5, with J3-7 = GND. VOP12 is LSU_Heater+ -> R9 1k ->
  D5 (K to VOP12) with C16 10u / C17 100n. U6B is a follower with its input at GND. Diode cathodes are on pad 1 for D2, D3,
  D4 and D5, which is the right polarity for each.
- **Part numbers against the EasyEDA records in `checks/easyeda/`**: C13585 is CL31A106**KB** (50 V), C1525 is 100n 16 V
  (used only on 3-5 V nets), C1523 is 1n 50 V, C4410 is 1k 1206, C4502 is 470R 1206, D1 C151279 is SMCJ24CA, and D2 C22452
  is SS54.
- **Mounting holes**: the nearest pad is 5.13 mm from H1's centre (U5 pin 2) and 5.88 mm from H2's (D5). That clears an
  M3 head or a 7 mm washer. Board outline 40.0 x 51.5 mm, and C11 is the part nearest the edge, at 1.85 mm (as stated).
- **Firmware diff** (`git diff origin/master -- firmware`): the watchdog sequence and its timeout. The reset values of
  0.4 s cover a dead LSI, and 400-666 ms over 30-50 kHz LSI is right for `PR=3`, `RLR=625`. It is kicked once per heater
  loop only, started after the 1 s settle, and frozen under a debugger. `SetAuxDac` trim and clamp; invalid -> 0 V; TIM3
  CH4 started once by the pump DAC; `TIME_IMMEDIATE` CAN send on this build. The bootloader bounds use
  `__appflash_size__` = 0x6400 = 25,600 B in the ELF built here.
- The TEST jumper also strapping CAN index 4 is already documented (`docs/firmware.md:47-49`), so it is not re-reported.

## What I could not check, and what it would take

- **Anything that needs pcbnew or KiCad 10.** Only KiCad 7 is packaged for this machine, and the KiCad PPA and
  ti.com were blocked by its network policy. So I did not regenerate the fab candidate (`work/out/` is gitignored) and
  did not check CPL rotations, Gerbers, DRC or the layout-review numbers. Next step: run `gen/export_fab.py` and
  `checks/run_all.py` on a machine with KiCad 10, and hand me (or the next reviewer) the CPL and Gerbers.
- **TI's LM2904 model** (SNOM268) could not be downloaded, so I did not reproduce stability or `load_accuracy.sh`. R1
  is from a behavioral model and needs the TI-model re-run described above.
- **JLC's CPL rotation sense** (left INFERRED in the hand-off) and LCSC stock or Basic/Extended status, because
  jlcpcb.com and lcsc.com were also blocked here.
- **Hardware behaviour**: B1 is from datasheet numbers I recalled (pull-up range, V_IH), not measured. On the bench,
  measure J3-5 with a meter at power-up, with no app flashed (bootloader only) and the board powered: it should read
  0 V and reads about 5 V if B1 is right.
