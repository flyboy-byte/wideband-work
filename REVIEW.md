# Reviewing this board (outside reviewers, people or AI)

Written 2026-10-24, board **r41** on branch `analog-out`. Nothing has been ordered, built or flashed. We are asking
for a review **before the first JLC order**: would you order these files as they are, and if not, why not?

The project is a fork of [mck1117/wideband](https://github.com/mck1117/wideband), the rusEFI LSU 4.9 controller.
The fork adds a 0-5 V analog output on the carrier board, and Claude designed it from code with the owner
directing. `README.md` covers the project. This page covers the review.

## Pick a mode

| Mode | What the reviewer sees | Independence | Can run checks |
| --- | --- | --- | --- |
| **A. Blind pack** (preferred for the first pass) | One read-only folder: hand-off, requirements, schematic, board, Gerbers, BOM, CPL, firmware diff, sim decks | High: no designer conclusions beyond the hand-off | No (reads and reasons, may write its own sims) |
| **B. Full repo** | Everything, including our docs, earlier audit rounds and every check script | Lower: our conclusions are in view | Yes |

Doing A first and then B is the best use of a second model. Whichever you do, check from the files and first
principles. Our documents are claims for you to test, not facts. Every claim in them carries a tag
(DOCUMENTED / REPORTED / INFERRED / FROM MEMORY / UNKNOWN); attack the INFERRED ones first.

## Setup (both modes)

```sh
git clone -b analog-out https://github.com/flyboy-byte/wideband-work && cd wideband-work
git submodule update --init test/googletest firmware/ChibiOS firmware/libfirmware firmware/ext/openblt
```

Tools, with the versions we used (2026-10-24, Arch Linux). Older versions may work, but we haven't tried them:

| Tool | Version | Needed for |
| --- | --- | --- |
| KiCad, with Python able to `import pcbnew` | 10.0.7 | board checks, DRC/ERC, fab export, renders |
| Python | 3.14 | all checks (standard library plus `pcbnew` only) |
| arm-none-eabi-gcc, make | 16.2 | firmware build |
| g++ | any recent | host test suites |
| qemu-system-arm | 11.1 | the Cortex-M0 fault-handler test (F9) |
| ngspice | 47 | `work/sim/*.sh` |
| TI LM2904 PSpice model | SNOM268 | sims: download https://www.ti.com/lit/zip/SNOM268 and put `lmx58_lm2904.lib` in `work/sim/models/` (not committed: licence) |

Freerouting and Java are only needed to regenerate the board, and a review doesn't need to regenerate it.

```sh
(cd firmware/boards/f0_module/bootloader && ./build_bootloader.sh)   # the app links the bootloader object
make -C firmware -j8 BOARD=f0_module                                  # 21.5 kB app; RAM full to the byte by design
cd work
python3 checks/fw_package.py build # bootloader + app image into work/fw-build/<commit>/ (adds 5 package-check cases)
python3 gen/export_fab.py          # writes the fab candidate to work/out/carrier/ (gitignored, so a clone lacks it)
python3 checks/run_all.py          # expect: 20 checks, 0 failed, 2 advisory failed (upstream's own raw DRC, owner decision D2)
```

**Mode A:** run `sh checks/review_pack.sh` from `work/`. It writes `work/audit/carrier-f-<date>/`. Give the model
**only that folder**, and paste its `PROMPT.md` first.

**Mode B:** point the model at the repo and paste the prompt below.

### Prompt for mode B

> You are an independent reviewer of a PCB before it is ordered. You did not design it. Repo: this checkout, branch
> `analog-out`. Read `REVIEW.md`, then the "Hand-off" section of `work/AUDIT.md` (what changed, what to check first,
> what is already known and accepted), then `work/REQUIREMENTS.md` (the bring-up tests that define "working").
> Don't trust our conclusions in `work/docs/`, `work/RELEASE_ASSESSMENT.md` or earlier audit rounds; check them from
> the board, schematic, fab files and firmware source, and run `work/checks/run_all.py` and the sims yourself. Don't
> change design files (generators, schematic, board, firmware behaviour). Propose fixes instead. You may add
> tests, sims and scripts in your own folder. Report in the format in `REVIEW.md`, with numbers as evidence.

## What to look at first

The priority list and the "known and accepted" list are in `work/AUDIT.md`, under "Hand-off". The short version:

1. **Fab files against the design.** Check every CPL rotation and offset, the BOM part numbers and the not-fitted
   list. D2 and U2 are the tricky parts. The rotation *sense* (JLC = KiCad, counter-clockwise from the top) is
   INFERRED.
2. **The analog stage.** R11 is inside the DC loop, with feedback taken at the connector. Check stability into
   cable capacitance, accuracy into pull-up and pull-down receivers, and what happens with 12 V on J3-5.
3. **Power.** The op-amp rail is 12 V → 1k → 18 V zener behind an SMCJ24CA TVS.
4. **Layout of the top-side stage.** Return paths and bypass distances.
5. **Firmware.** Check `git diff origin/master -- firmware`, especially `firmware/watchdog.h` and its use in
   `heater_thread.cpp`.

## Report format

Put your raw report in `work/audit/<reviewer>-<date>/FINDINGS.md` (for example `work/audit/opus-jdoe-2026-10-25/`),
together with any decks, scripts and raw numbers. Keep it in your own voice: we keep each reviewer's output
separate and don't merge it.

1. **Verdict first:** "Would I order these files as they are?" Answer yes or no, with one sentence why.
2. **Findings:**

   | ID | Severity | Location | Evidence (numbers) | Smallest fix |
   | --- | --- | --- | --- | --- |

   Severity: BLOCKER = don't order; BUG = wrong but workable; RISK = could bite (state the condition); NOTE.
   Location: file and line, or reference designator and board coordinates (mm).
3. **What you checked and found correct.** This tells us what is covered.
4. **What you could not check**, and what you would need in order to check it.

Don't re-report the items in "known and accepted". If you think one of them is wrong, say so once, as a NOTE.

## Sending it back

Either send the owner a pull request to `flyboy-byte/wideband-work`, adding only your `work/audit/<reviewer>-<date>/`
folder, or zip the folder and send it. The designer verifies each finding, then fixes it or answers it, and records
the round in `work/AUDIT.md` with your name and the commit you reviewed. Where two reviewers disagree, the owner
decides between their arguments. The later report doesn't win by default.

Out of scope for any reviewer: ordering, pushing to this repo, publishing, and choosing parts for an
engine-bay temperature rating (the owner has said it isn't a design driver for this prototype).

## Background for an AI reviewer (optional)

The design workflow is the `pcb-design` skill for Claude Code, which is public at
[flyboy-byte/scripts-docs-dotfiles, `skills/pcb-design/`](https://github.com/flyboy-byte/scripts-docs-dotfiles/tree/master/skills/pcb-design).
To install it, copy that folder to `~/.claude/skills/pcb-design/`. A review doesn't need it. It explains how the
board was made (generated from code, DRC against the upstream baseline, the audit loop) and its `reference/fab-files-audit-order.md`
lists the fab-file checks a reviewer would otherwise rediscover. `AGENTS.md` here is the model-agnostic rule book
(evidence tags, what a reviewer may change).
