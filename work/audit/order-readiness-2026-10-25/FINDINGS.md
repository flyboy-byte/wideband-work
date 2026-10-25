# Ordering-readiness review — Codex, 2026-10-25

Reviewed `c07643c` on `analog-out`, released `work/fab/flyboy-o2-v1/` (release commit `a642c86`).
Independent worktree `review/order-readiness-2026-10-25`; audit-only changes. Template adapted to the owner's
new ordering focus, not another repetition of round 7 TK1–TK7. Shell, KiCad and public vendor data available.
Concurrent designer commit `a396bee` adds the owner's one-order-only requirement and holds the order for a first-run
risk pass; this review respects that hold. No purchase, upload, quote submission or design change.

## Verdict

**Pending remaining checks; do not treat this intermediate report as permission to order.**

## Coverage

| Task | Status | Findings | Evidence |
| --- | --- | --- | --- |
| O1 Frozen release integrity and provenance | OK | | `O1-release-final.log`, `release-sha256.json` |
| O2 Both boards' assembly mapping and module Gerber geometry | OK | | `O2-assembly.log`, `O2-module-geometry.log`, `O2-drc.log`, `O2-drift.log`, `O2-release-gate.log` |
| O3 Two-assembled stock and factory requirements | IN PROGRESS | | Live stock queries; JLC primary sources |
| O4 First-run recoverability and checkout handoff | NOT CHECKED | | Programming, hand-fitted parts, first-power plan |

## Findings

| ID | Task | Severity | Location | Evidence | Smallest fix |
| --- | --- | --- | --- | --- | --- |

## Checked and found right

- MEASURED: all eight frozen upload/not-fitted files match RELEASE.json's hash prefixes; full SHA-256 stored separately.
- MEASURED: all 27 recorded check results have no non-advisory failure; available checked files match their recorded
  hashes, resolving gitignored candidate files to their frozen release counterparts. This verifies recorded results,
  not a fresh run of all 27 checks.
- MEASURED: no hardware, firmware or generator differences from audited `18b6cef` or released `a642c86`.
- MEASURED: all nine carrier Gerber layers and both drill files equal fresh KiCad exports after ignoring date/software
  metadata only. Module ZIP is byte-identical to upstream rev C; geometric correspondence is O2, not assumed.
- MEASURED: module's four copper layers, both masks and outline have identical geometric primitives to fresh exports,
  retaining polarity-batch order (gerbonara 1.6.3); both drill files have identical drill commands. Both silks have
  identical dark geometry; the released KiCad-9 files additionally subtract 169/25 clear polygons (top/bottom).
  Seven negative controls reject deletion of an object. This comparison is independent of aperture numbering and
  plotting order, which change between KiCad 9 and 10; it does not silently ignore copper differences.
- MEASURED: all 52 BOM lines, 95 placed references and nine not-fitted entries cover both boards exactly once.
  Values, packages, LCSC IDs (including the two module substitutions), CPL position/rotation/side match the boards
  and measured correction tables. No paste on the nine not-fitted footprints. Rotation sense still needs preview.
- MEASURED: fresh DRC delta 0 new/0 unconnected; no drift; release-round regression 4/4.

## Attempt log

- O1 first attempt stopped on absent gitignored candidate paths in a clean worktree; use frozen release equivalents.
- O1 second attempt matched all Gerber layers but drill date comment differed; explicitly ignore `; DRILL file` metadata.
- O1 final attempt passes; failed attempts retained, not evidence of a release defect.

## Could not check yet

Factory placement preview, order-specific DFM acceptance, actual delivered boards and electrical bench behavior.
