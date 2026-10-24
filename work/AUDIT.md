# Audit — <board name>

## Hand-off (give this to each auditor with a read-only copy; not your conclusions)
- Board: carrier PCB for the rusEFI wideband module (LSU 4.9 controller) adding a 0-5 V analog output (AFR 10 = 0 V, 20 = 5 V)
  for Speeduino / Hondata FlashPro / a gauge. Analog stage: PB1 PWM -> 74LVC1G125 on a REF3030 3.000 V -> 2x RC (3.3k/100n)
  -> LM2904 x1.68 (dual-loop feedback) -> 330R -> 1N4148WS clamps -> J3-5. Firmware: branch `analog-out`.
- Commit and files: the commit that adds this text (see `git log -1 -- work/AUDIT.md`); `hardware/board_carrier/board_carrier.kicad_{sch,pcb}`,
  `firmware/` diff (`git diff master -- firmware`), `work/docs/{analog-out,carrier,firmware}.md`, `work/sim/`.
- Changed since last audit: no audit has happened yet (this is round 1). Newest change (2026-10-23, run r32): the last open
  connection was closed by `gen/gen_carrier_pcb.py: close_d3_link` (D3 +5V -> U2 pin 3 on the top layer, 0.25 mm; GND via at 66.00,79.35
  tied to C1 pin 2 by 0.2 mm; C2 pin 2 given a solid pour connection).
- Check, in priority order (owner: effort goes to circuits, power, heater drive, control loops, firmware):
  1. **Analog stage from first principles**: op-amp stability with cable capacitance (`sim/stability.sh`, TI model), output
     clamps and the 0.7 mV ripple / 4.1 ms settling claim, behaviour with the output shorted to GND or +12 V.
  2. **Power**: LM2904 supply (12 V -> 1k -> 18 V zener; input TVS SMCJ30CA lets the rail reach ~35-48 V). R8 (330R) and R9 (1k)
     are 0603 (100 mW): INFERRED too small for a sustained AOUT short or a surge; not simulated.
  3. **New in r32**: C1 is the LSU heater supply bypass (upstream part). Its GND now returns through one 0.5 mm via and a 0.2 mm
     tie (was a pour connection). INFERRED fine for a bypass cap, not measured. Is a heater-drive transient a concern?
  4. **Firmware**: `git diff master -- firmware`: TIM3_CH4 on PB1 shared with the pump DAC, update from the CAN TX thread,
     0 V while lambda invalid, test mode when SEL_2 is low at power-up, RAM full to the byte.
  5. Layout of what moved; silkscreen; BOM/stock (nothing ordered; no fab files exist yet).
- Known and accepted (don't re-report): module DRC 11 and carrier DRC 22 errors that are upstream's own (`checks/drc_vs_upstream.py`
  subtracts them); upstream's thermal-relief warning on one pad; no fab files yet (nothing to compare against).
- Report format below.

Build the pack for an outside reviewer with `checks/audit_pack.py <rev> <files>` (see AGENTS.md, "Cross-model audits").

## Report format
Verdict first: "Would I order these files as they are?"

| ID | Severity | Location | Evidence (numbers) | Smallest fix | Status |
| --- | --- | --- | --- | --- | --- |

Status: open / fixed (commit) / accepted (why). `checks/release.py` refuses while a BLOCKER or BUG is open.

Severity: BLOCKER = don't order; BUG = wrong but workable; RISK = could bite (state the condition);
NOTE. Then: what was checked and found correct, and what couldn't be checked.

## Rounds
### Round 1 — <YYYY-MM-DD>, <auditor>
Commit: <short hash audited>
Verdict: <would I order these files as they are?>

| ID | Severity | Location | Evidence (numbers) | Smallest fix | Status |
| --- | --- | --- | --- | --- | --- |
