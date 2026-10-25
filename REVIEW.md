# Reviewing this board (outside reviewers, people or AI)

Updated 2026-10-24 for **round 6**: the r41 layout with that day's fixes (R3 4.7k, invalid = 5 V, heater clamp) on
branch `analog-out`. Nothing has been ordered, built or flashed. The question for a reviewer: **would you order these
files as they are, and if not, why not?**

The project is a fork of [mck1117/wideband](https://github.com/mck1117/wideband), the rusEFI LSU 4.9 controller,
adding a 0-5 V analog output on the carrier board. Claude designed it from code with the owner directing.
`README.md` covers the project. This page covers the review.

## Start here (two minutes)

| File | What it is |
| --- | --- |
| [`work/review/TASKS.md`](work/review/TASKS.md) | **The work list** (TK1, TK2, ... for this round), in order of value, each with a question, the files, how to check it with or without a shell, and what "done" means. Replaced each round. |
| [`work/review/FINDINGS-TEMPLATE.md`](work/review/FINDINGS-TEMPLATE.md) | The report to fill in: verdict, one coverage row per task, findings, two worked examples of the level we want |
| [`work/AUDIT.md`](work/AUDIT.md), "Hand-off" | What changed since the last round, what's open, and what's **known and accepted** (don't re-report) |
| [`work/review/PROMPT.md`](work/review/PROMPT.md) | The prompt a chat reviewer gets with the pack |

Three rules matter more than the rest. Earlier rounds lost time or findings on each of them:

1. **Work through the list without waiting.** Nobody watches live; the owner reads the report later on his phone.
   Make an assumption and write it in the finding rather than asking.
2. **Write as you go.** After each task, add its coverage row and findings to `FINDINGS.md` and commit. Round 4 ran
   out of credits with its best finding (the heater bug) not yet written down.
3. **Budget:** when about a quarter is left, stop starting tasks and finish the verdict and coverage table.

## Pick your route

| Route | For | What you get | Can run checks |
| --- | --- | --- | --- |
| **B. Agent with the repo** (Codex, Claude Code, a person with a shell) | the main route | everything, including our docs and every check script | yes |
| **A. Chat with the pack** (ChatGPT, claude.ai: uploaded files only) | a blind or no-tools pass | one zip: board, schematic, fab files, plain-text part and net lists, firmware diff, sims, task list | only what its own sandbox runs |

Route A is more independent, because it shows fewer of our conclusions. Route B can verify. Doing A and then B is the best use
of a second model. Either way, our documents are claims for you to test, not facts. Each claim carries an
evidence tag (DOCUMENTED / REPORTED / INFERRED / FROM MEMORY / UNKNOWN); attack the INFERRED ones first.

### Route B: prompt for an agent (paste this)

> You are an independent reviewer of a PCB and its firmware before the first order. You did not design it. Repo:
> this checkout, branch `analog-out`. Read `REVIEW.md`, then `work/review/TASKS.md`, then the "Hand-off" section
> of `work/AUDIT.md`. Work in your own worktree so the designer's checkout stays on its branch:
> `git worktree add ../wideband-review-<you> -b review/<you>-<date>` (then `cd` there and init the submodules). Create
> the folder `work/audit/<you>-<date>/`, and copy
> `work/review/FINDINGS-TEMPLATE.md` there as `FINDINGS.md`. Do the setup in `REVIEW.md`, then work through the TK tasks
> in order without waiting for replies. After each task, update `FINDINGS.md` and commit. Don't trust our
> conclusions in `work/docs/`, `work/RELEASE_ASSESSMENT.md` or earlier rounds: check them from the board, the
> schematic, the fab files and the firmware source, and run the checks and sims yourself. Don't change design
> files (generators, schematic, board, firmware behaviour); propose fixes instead. Your own tests and scripts go
> in your folder. When about a quarter of your budget is left, finish the verdict and coverage table, commit, and
> push the branch (open a PR if you can).

### Route A: the pack for a chat model

From `work/`, after the setup below: `sh checks/review_pack.sh`. It writes `work/audit/carrier-f-<date>/` (about
47 files, read-only) and one zip of it, `work/audit/carrier-f-<date>.zip` (about 4 MB). Upload the zip, then paste
the pack's `PROMPT.md` as the first message. The pack's `INDEX.md` lists each file and where it came from. For a
model that can't open KiCad files, `carrier-parts.txt`, `carrier-nets.txt`, `module-parts.txt` and `module-nets.txt`
hold every part's position and rotation and every net's pads as plain text. In a chat, ask it to put the coverage
table in every reply, so a cut-off chat still leaves a record.

## Setup (route B, and building the pack)

```sh
git clone -b analog-out https://github.com/flyboy-byte/wideband-work && cd wideband-work
git submodule update --init test/googletest firmware/ChibiOS firmware/libfirmware firmware/ext/openblt
```

Tools, with the versions we used (2026-10-24, Arch Linux). Older versions may work, but we haven't tried them:

| Tool | Version | Needed for |
| --- | --- | --- |
| KiCad, with Python able to `import pcbnew` | 10.0.7 | board checks, DRC/ERC, fab export, renders, the pack |
| Python | 3.14 | all checks (standard library plus `pcbnew` only) |
| arm-none-eabi-gcc, make | 16.2 | firmware build |
| g++ | any recent | host test suites |
| qemu-system-arm | 11.1 | the Cortex-M0 fault-handler test (F9) |
| ngspice | 47 | `work/sim/*.sh` |
| TI LM2904 PSpice model | SNOM268 | sims: download https://www.ti.com/lit/zip/SNOM268 and put `lmx58_lm2904.lib` in `work/sim/models/` (not committed: licence) |

The sims run from `work/sim/`, where `.spiceinit` sets `ngbehavior=psa`; TI's model fails to load without it, so a deck of your
own must run there or set the same option (Codex round 6). Freerouting and Java are only needed to regenerate the board, and a review doesn't need to regenerate it.

```sh
(cd firmware/boards/f0_module/bootloader && ./build_bootloader.sh)   # the app links the bootloader object
make -C firmware -j8 BOARD=f0_module                                  # 21.5 kB app; RAM full to the byte by design
cd work
python3 checks/fw_package.py build # bootloader + app image into work/fw-build/<commit>/ (adds 5 package-check cases)
python3 gen/module_fab.py          # stages the module's JLC files in work/out/module/ (upstream rev C, 2 BOM swaps)
python3 gen/export_fab.py          # writes the fab candidate to work/out/carrier/ (gitignored, so a clone lacks it)
python3 checks/run_all.py          # expect: 26 checks, 0 failed, 2 advisory failed (upstream's own raw DRC, owner decision D2)
```

Missing a tool? Skip what needs it, mark those tasks PARTLY or NOT CHECKED with the reason, and carry on. A check
whose tool isn't installed reports SKIPPED, never PASS.

## Sending it back

Push your `review/<you>-<date>` branch to your fork and open a pull request to `flyboy-byte/wideband-work` that
adds only `work/audit/<you>-<date>/`. If you can't, zip the folder and send it to the owner. Keep it in your own voice. We
keep each reviewer's output as it is and don't merge reports.

The designer verifies each finding, then fixes it or answers it, and records the round in `work/AUDIT.md` with your
name and the commit you reviewed. Where two reviewers disagree, the owner decides between their arguments; the later
report doesn't win by default. A design change made because of a finding gets its own check, a bench test and an
item in the next round's `TASKS.md`.

Out of scope for any reviewer:
- ordering, pushing to `analog-out`, and publishing;
- engine-bay temperature ratings (the owner has said they aren't a design driver for this prototype);
- the items in the hand-off's "known and accepted" list. If you think one of them is wrong, say so once, as a NOTE.

## For the designer: starting the next round

1. Rewrite `work/review/TASKS.md` for what changed (keep the TK numbering, and move answered questions out).
2. Update the "Hand-off" in `work/AUDIT.md`, then run `python3 checks/review_docs.py`. It fails if the docs and the
   checks disagree (task IDs, file names, check count).
3. Run `sh checks/review_pack.sh` and give the reviewer this page or the zip.

## Background for an AI reviewer (optional)

The design workflow is the `pcb-design` skill for Claude Code, public at
[flyboy-byte/scripts-docs-dotfiles, `skills/pcb-design/`](https://github.com/flyboy-byte/scripts-docs-dotfiles/tree/master/skills/pcb-design).
A review doesn't need it. It explains how the board was made: generated from code, DRC against the upstream
baseline, the audit loop. Its `reference/fab-files-audit-order.md` lists the fab-file checks a reviewer would
otherwise rediscover. `AGENTS.md` here is the model-agnostic rule book (evidence tags, what a reviewer may change).
