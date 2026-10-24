# Ordering the boards from JLCPCB

Written 2026-10-24 for board r41. Nothing has been ordered. Ordering is the owner's call, because it costs money. Prices and
JLC page details are REPORTED or UNKNOWN until the live quote page shows them. Read the quote, not this page, on the
day.

## What gets ordered

| Board | Files | Status |
| --- | --- | --- |
| Carrier (ours, r41) | `work/out/carrier/`: `carrier-gerbers.zip`, `carrier-bom.csv`, `carrier-cpl.csv`, `not-fitted.csv`, `README.md` | Candidate. Released only by `checks/release.py` after an audit round with no open BLOCKER or BUG (stage 9) |
| Module (upstream's, rev C) | upstream's `hardware/board_module/` exports, 2026-03-22 | Not prepared: our rotation and fab checks haven't been run on it yet (STATE, Open register) |
| SWD probe / cable for first flash | none | Owner's choice (D4, `docs/flashing-and-test-plan.md`) |

The module is 4-layer, 29.0 x 20.9 mm and has 60 parts. Its J1/J3 headers go on the bottom, which the owner hand-solders, and
J2 is a set of Tag-Connect pads (DOCUMENTED: upstream board). Both boards can go in one JLC cart, but they are two separate
PCB orders.

## Steps (carrier)

1. **Fresh candidate.** `cd work && python3 gen/export_fab.py`, then `python3 checks/run_all.py`. Expect every check to pass
   apart from the 2 advisory upstream DRC checks (D2). The exporter refuses to write files unless the DRC delta and the
   rotation check pass.
2. **Release.** `python3 checks/release.py <rev> out/carrier/carrier-gerbers.zip out/carrier/carrier-bom.csv
   out/carrier/carrier-cpl.csv out/carrier/not-fitted.csv`. It copies the files to `fab/<rev>/` only when everything is safe.
   Use a revision name that has never been used (`STATE.md`, "Revisions used").
3. **Upload to JLC** (jlcpcb.com → PCB quote):
   - Gerber zip: check that JLC's viewer reads 40.0 x 51.5 mm, 2 layers, and that the outline, both copper layers, the
     mask, the silk and the drills are all there.
   - PCB options: 1.6 mm FR-4, HASL (lead-free if wanted), green mask. Keep the defaults otherwise; the board needs no
     special stack-up or impedance control.
   - **PCB Assembly** on, **top side** only (every placed part is on the top, D9), **Economic** class if the quote offers
     it for this BOM. REPORTED from the session that exported the files, unchecked: Economic about $8 setup, Standard
     about $50. Read the quote.
   - Upload the BOM and CPL. Then, part by part:
     - **Every BOM line resolves to its LCSC number** (25 lines). There are 7 Extended parts, each with a loading fee:
       D1, D5, R11, U1, U4, U5, U6 (`parts_research.md`).
     - **Stock.** Look first at C13585 (10u 1206, x5 per board), C14663 (100n 0603, C17), C15849 (1u 0603, x3) and
       C7934 (LM2904DR), which were low or zero at LCSC on 2026-10-24. LCSC's warehouse isn't JLC's assembly stock;
       the quote page is the final word.
     - Not fitted: J3, U3, JP1, JP2, H1, H2 (`not-fitted.csv`). J3 is through-hole and the owner solders it. The jumpers
       are solder pads.
4. **Placement preview** (turn on "Confirm Parts Placement" if offered). This is the check that matters most, because the
   rotation sense is INFERRED (JLC = KiCad, counter-clockwise from the top):
   - **D2 SS54 first.** EasyEDA numbers its anode 1 and KiCad numbers its cathode 1. Our check paired them by pin name,
     so the cathode band must face the way the silkscreen shows.
   - D3, D4 (1N4148WS), D5 (BZT52C18): the cathode bands. D1 is an SMCJ24**CA**, which is bidirectional, so it has
     no polarity.
   - U1 (SOIC-8), U6 (SOIC-8): pin 1 dot. U4 (SC-70) and U5 (SOT-23): pin 1. U2 (TO-252): the tab over its big pad,
     shifted 0.725 mm on purpose (`checks/jlc_rotation.json`).
   - If any part is wrong, fix it in the generator or the correction table and re-export. Don't fix it on JLC's page,
     because the repo would then no longer match the order.
5. **Order remark:** "No substitutions: U5 REF3030, U6 LM2904DR, U4 74LVC1G125, D1 SMCJ24CA, D5 BZT52C18". The
   reference sets the output's full scale, and the rail parts set its voltage limits.
6. **The same day:** commit `fab/<rev>/` with its README (order number, date, options chosen), add a row to `ORDERS.md`,
   and add `<rev>` to "Revisions used" in `STATE.md`.

## Changing a part (substitution rule)

Never edit the BOM or CPL by hand. Instead:

1. Change the LCSC field (and the footprint, if the package changes) in `gen/gen_carrier_sch.py` and
   `gen/gen_carrier_pcb.py`.
2. Run `python3 checks/drift.py check` first: the owner may have edited the KiCad files.
3. Regenerate the board, run `python3 checks/jlc_rotation.py` (it fetches the new part's EasyEDA footprint into
   `checks/easyeda/`, then measures its rotation, origin and pin names), then run `gen/export_fab.py` and
   `checks/run_all.py`.
4. A substitute must keep the ratings: C16/C17 sit on the 18 V op-amp rail (25 V or more), R9 is 1206 for surge, and
   R11 is 1206. A plain resistor of the same value and package is the only swap that can skip the audit; anything
   active goes through an audit round.

## Data sources and APIs

- **EasyEDA component data** (the footprint JLC places with): `https://easyeda.com/api/products/<LCSC>/components?version=6.5.42`.
  - A plain request answered and a browser user agent was refused (403) (REPORTED, 2026-10-24).
  - Pads are in 10-mil units around the header origin.
  - Pin names are field 4 of the third `~`-separated segment of each `P~` shape.
  - The JSON also carries `lcsc.stock` and "JLCPCB Part Class".
  - Answers are cached in `checks/easyeda/` (committed), so the rotation check runs offline.
- **JLC parts search** (jlcpcb.com/parts) for live JLC stock, price and library class. We have no script for it (UNKNOWN
  endpoint). Check it by hand on quote day.
- **Datasheets:** maker PDFs, cited per part in `parts_research.md`. The maker's drawing beats EasyEDA when they
  disagree.

## After it arrives

Follow the bring-up tests in `REQUIREMENTS.md` and `docs/flashing-and-test-plan.md`: T1, then A1-A4, W1 and H1-H6, with a
multimeter only. Record the results in `STATE.md` (stage 11) and anything that went wrong in `ORDERS.md` and `LESSONS.md`.
