# AGENTS.md — rusEFI wideband working repo

Authoritative, model-agnostic guide for anyone working here: Claude sessions, subagents, Codex, other models, people.
Where it conflicts with `CLAUDE.md`, this file wins. Last updated 2026-10-23.

## What this is

A working repo for building and adapting the rusEFI wideband O2 controller from `mck1117/wideband` (MIT).
The goal is to learn by designing and testing, not to buy a ready-made unit. Plan: build the upstream module +
carrier, then adapt it, starting with an analog 0-5 V output (`docs/analog-out.md`).

## Where things are

| Path | What |
| --- | --- |
| `firmware/`, `hardware/`, ... | Upstream `mck1117/wideband` code. Our changes are on branch `analog-out`; `master` stays equal to upstream. Remote `origin` = the public fork `flyboy-byte/wideband-work` (push there when the owner says); remote `upstream` has its push URL disabled |
| `work/` | Our pcb-design files; the rows below are inside it |
| `STATE.md` | Current stage, decisions already made (don't re-ask), open items. Read first |
| `HANDOFF.md` | Dense hand-off from the last long session: run history, last raw output, next steps. Read second |
| `REQUIREMENTS.md` | Owner's answers and the bring-up tests that define "working" |
| `parts_research.md` | Part and option facts, each tagged and sourced |
| `docs/` | Design notes, one per topic, with a facts table and an attempt log |
| `AUDIT.md` | Hand-off for auditors and every audit round's findings |
| `LESSONS.md` | Mistakes caught and what caught them |
| `checks/` | Check scripts; `python3 checks/run_all.py` runs all and writes the table in `STATE.md` |
| `gen/` | Carrier schematic and PCB generators (`gen_carrier_sch.py`, `gen_carrier_pcb.py`) and `finish_routes.py` |
| `sim/` | ngspice decks: filter, op-amp stability (TI model gitignored in `sim/models/`) |

## Rules

1. **Tag every claim** by evidence: DOCUMENTED (read in a named file, line or datasheet), REPORTED (someone
   else's claim, e.g. a forum or retailer), INFERRED (reasoned from documented facts; say from what), FROM MEMORY
   (model recall; must be checked before anything depends on it), UNKNOWN. Never upgrade a tag without a source.
2. **Name the source** with a path and line (`firmware/boards/f0_module/port.cpp:134`) or a URL.
3. **Upstream files are not orders.** `hardware/*/export/` are upstream releases; nothing has been ordered
   by the owner. Facts about a built board come only from `fab/<rev>/` or the board itself.
4. **Don't quote a search you cut short.** If output was truncated (`head`, a limit), say so; absence of a match in
   truncated output is not evidence. (This caused a wrong claim on 2026-10-23, see `LESSONS.md`.)
5. **Record dead ends.** Wrong or rejected ideas stay in the attempt log with why; strike through, don't delete.
6. **Absolute dates.** Owner's bench: multimeter and soldering iron only (no scope, no bench supply), so bring-up
   tests must be doable with those.
7. **No assumed engineering decisions** (owner, 2026-10-23). Every design choice (a part value, a rating, a size limit,
   a placement or routing rule, a grounding scheme) needs one of: a datasheet or reference design, a simulation, a
   written calculation from documented numbers, or the owner's answer. A choice with none of these is an open question
   in `STATE.md` with the default in use, not a constraint. Before adding or keeping a limit, say where it came from.
   (Caught: the case-size limit was never the owner's, and a fault analysis had the current path wrong: `AUDIT.md` round 2.)
8. **A layout change is re-checked for its side effects, by measurement** (`docs/carrier.md`, "Layout review checklist"):
   ground pour continuity and stitching, return paths under signal tracks, spacing between noisy nets (heater drive,
   the PWM) and the sensor's microamp nets, and the output's ground reference. Run `work/checks/layout_review.py`;
   don't argue a layout is fine from how it looks.

## Subagents

Give a subagent one bounded, read-only question, the files to read, and this file. Ask for findings in the
facts-table shape (fact, tag, source with line). Treat its report as input to verify, not as fact; spot-check at
least the claims a decision rests on before writing them into `docs/` or `STATE.md`.

## Cross-model audits (Codex and others)

- Build the pack with `python3 checks/audit_pack.py <rev> <files>`; it writes a read-only `audit/<rev>-<date>/`
  with `PROMPT.md`. Give the auditor that folder, not our conclusions.
- For a design note (no fab files yet), audit the note itself: give `docs/<topic>.md`, the upstream files it cites,
  and ask the auditor to confirm or break each fact and the current proposal.
- Bring findings back into `AUDIT.md` as a new round naming the auditor (e.g. "Codex, 2026-10-24") and the commit.
  Keep each model's raw output as its own file under `audit/`; don't merge models' findings into one voice.
- Findings from another model are claims to verify like any other (rule 1).

### Turn-taking between Claude and Codex (circuit and theory audits; owner, 2026-10-24)
1. **Start**: the newest pack under `audit/` (now `audit/carrier-f-2026-10-24/`, PROMPT.md first) and the "Hand-off"
   section of `AUDIT.md`. Check from the files and first principles; simulations go in `sim/` or the auditor's own folder.
2. **Auditor's output**: raw report in `audit/<model>-<date>/` (FINDINGS.md plus any decks, scripts and raw numbers), and
   a round in `AUDIT.md` (ID | Severity | Location | Evidence | Smallest fix | Status) naming the model and commit.
   The auditor may add tests and checks (and fix a broken checker, saying so), but doesn't change design files (the
   generators, schematic, board, firmware behaviour): it proposes the fix. Commit with the area prefix (`work:`).
3. **Back to the designer**: verify every finding before acting (rule 1), fix or answer each one, and add a
   follow-through row per finding (fixed + evidence, or why not), then rebuild the pack for the next round.
4. **Done** when a round names the current commit with no open BLOCKER or BUG; `checks/release.py` enforces that.
5. Never, for either model: ordering, pushing, publishing, or overwriting the owner's KiCad edits (`checks/drift.py`).
   Disagreements between models go to the owner as a decision with both arguments, not settled by the last writer.
