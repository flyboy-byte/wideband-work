# Fab files: flyboy-o2-v1

Released 2026-10-25 by `checks/release.py` at commit `a642c86` (branch `analog-out`). **Not ordered yet**: when it is,
add the date, the JLC order number(s) and the order remark here and in `../../ORDERS.md`. These are the files to upload,
unchanged; if any file changes, it is a new revision (`flyboy-o2-v2`), never an edit here.

Two boards, one order: our carrier (with the 0-5 V analog output) and upstream's module, rev C, unchanged copper.

| File | What | sha256 (first 12) |
| --- | --- | --- |
| `carrier-gerbers.zip` | Carrier Gerbers and drill: 2 layers, 40.0 x 51.5 mm, r41 layout | c6d03f1de870 |
| `carrier-bom.csv` | Carrier BOM, 26 lines (8 Extended, incl. R9 C844867: don't swap it) | 4929cced2179 |
| `carrier-cpl.csv` | Carrier CPL, 38 parts, all top; corrections U1/U6 270, U4/U5 180, U2 shifted 0.725 mm | 66a7fdc2200c |
| `carrier-not-fitted.csv` | 6 carrier parts not assembled (through-hole, hand-soldered) | 36e2ae5c65c5 |
| `module-gerbers.zip` | Module Gerbers: upstream rev C exports, 4 layers, 29.0 x 20.9 mm | 7b7f18362efd |
| `module-bom.csv` | Module BOM, 26 lines; R10 -> C2087389 and C3 -> C106862 (upstream parts out of stock) | ed5c6cf281b2 |
| `module-cpl.csv` | Module CPL, 57 parts; Q1 0 deg (upstream's 180 would put the tab on the leads) | c35ba1cd8456 |
| `module-not-fitted.csv` | J1/J3 headers and J2 Tag-Connect pads, not assembled | a55f5466c524 |
| `RELEASE.json` | Commit, hashes and every check result at release | |

## Check table (all at `a642c86`; full list in `RELEASE.json`)
| Check | Result |
| --- | --- |
| Carrier DRC vs upstream's own board | 0 new violations, 0 unconnected (raw DRC: upstream's 23 errors, advisory, owner decision D2) |
| Module DRC | upstream's 11 errors, advisory (D2); copper identical to upstream rev C |
| Via-in-pad | 0 new |
| CPL rotation (EasyEDA footprints measured) | carrier 38 parts, module 57 parts, 0 problems |
| CPL against the board | 38 placed, 6 not fitted, outline 40.00 x 51.50 mm |
| Firmware, stack, sims, surge, boot level | pass (27 checks, 0 failed) |
| Audit | round 7 (Codex/Astra, PR #3): no open BLOCKER or BUG (`../../AUDIT.md`) |

## On the order page (`../../docs/ordering.md` has the full steps)
- Run `python3 checks/bom_stock.py 5` the same day.
- Carrier: add edge rails (C11 sits near the edge, R6-S4).
- In the placement preview, check before paying: module Q1 (tab), then U2 pin 1, U9, U1, U3, U5, LEDs; carrier D2
  (SS54, EasyEDA numbers its pads the other way round), then every IC.
- Order remark: "No substitutions" for R9 (C844867) and module R10 (C2087389).
