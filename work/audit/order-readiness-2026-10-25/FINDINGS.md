# Ordering-readiness review — Codex, 2026-10-25

Reviewed `c07643c` on `analog-out`, released `work/fab/flyboy-o2-v1/` (release commit `a642c86`).
Independent worktree `review/order-readiness-2026-10-25`; audit-only changes. Template adapted to the owner's
new ordering focus, not another repetition of round 7 TK1–TK7. Shell, KiCad and public vendor data available.
Concurrent designer commit `a396bee` adds the owner's one-order-only requirement and holds the order for a first-run
risk pass; this review respects that hold. No purchase, upload, quote submission or design change.

## Verdict

**No, not with the current hand-assembly shopping list.** OR1 is a confirmed header-fit BUG. The released PCB files
are internally consistent, but that does not establish physical assembly with the named header. Final recovery
handoff still in progress; no design change or new release has been made.

## Coverage

| Task | Status | Findings | Evidence |
| --- | --- | --- | --- |
| O1 Frozen release integrity and provenance | OK | | `O1-release-final.log`, `release-sha256.json` |
| O2 Both boards' assembly mapping and module Gerber geometry | OK | | `O2-assembly.log`, `O2-module-geometry.log`, `O2-drc.log`, `O2-drift.log`, `O2-release-gate.log` |
| O3 Two-assembled stock and factory requirements | PARTLY | OR3 | 52/52 lines available; `ORDER-CHECKLIST.md`; job-specific DFM/preview not performed |
| O4 First-run recoverability and checkout handoff | IN PROGRESS | OR1 | `O4-header-fit.log`; manufacturer drawing visually read |

## Findings

| ID | Task | Severity | Location | Evidence | Smallest fix |
| --- | --- | --- | --- | --- | --- |
| OR1 | O4 | BUG — hold order | `work/ROADMAP.md:116`; carrier U3 pins 1–16; released PTH drill | MEASURED holes 0.762 mm; DOCUMENTED Hanxia C32713274 drawing SQ 0.64 mm and recommended hole 1.02 mm. CALCULATED diagonal 0.9051 mm, 0.1431 mm larger than nominal hole. All 16 released holes checked (`O4-header-fit.log`). | Select and dimension-check a compatible interconnect (including tolerances, current, standoff and programming access). If retaining this header, designer must change/review/release larger holes. Do not assume drilling plated holes is a safe repair. |
| OR3 | O3 | NOTE | `work/docs/ordering.md:11–13,40`; `work/fab/flyboy-o2-v1/README.md:33`; `work/HANDOFF.md` next steps | DOCUMENTED old instructions point to candidates, stock-check five assemblies and use old pricing; current owner quantity is two per board. | Use the frozen-file, two-assembly checklist supplied here; designer updates canonical pointers. |

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

## OR1 manufacturer source

Hanxia drawing **HX PZ2.54-1x8P ZZ**, page 1/1, dated 2022/04/24; square-pin dimension and recommended PCB layout
visually inspected, not inferred from a product photo:
https://datasheet.lcsc.com/datasheet/pdf/85243369e68f3858b37abf71bad9b29e.pdf?productCode=C32713274
This is the exact part named in `ROADMAP.md`; no assertion that every possible 2.54 mm header fails.
