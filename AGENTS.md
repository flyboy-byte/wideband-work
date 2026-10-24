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
