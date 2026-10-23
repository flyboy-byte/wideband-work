# Lessons — rusEFI wideband

Every mistake caught on this board, with when and what caught it. At bring-up and after each order, propose the ones
that would help any board as a line for the `pcb-design` skill (see its "Lessons back to the skill" section).

| Date | Stage | What went wrong or nearly did | What caught it | General? | Sent to skill |
| --- | --- | --- | --- | --- | --- |
| 2026-10-23 | Requirements | Claimed module SEL pads were unused by firmware; the grep output was cut by `head -12` before the f0_module match | Re-check of the plan by a second model reading `port.cpp` | Yes: don't treat absence in truncated output as evidence | not yet |
| 2026-10-23 | Requirements | Counted module pads from the carrier-side symbol (14) instead of the module netlist (16) | Netlist export during the re-check | Yes: count pins from the board's own netlist, not a symbol drawn for another board | not yet |
| 2026-10-23 | Requirements | Proposed PA8 for PWM without checking which timer channel it shares; it is the heater's TIM1_CH1 complement | Re-check reading `io_pins.h` and the AF table | Yes: check timer and channel sharing before reusing a pin for PWM | not yet |
| 2026-10-23 | Checks | `kicad_check.py` wrote every board's report to the same `checks/out/drc.json`, so a two-board project kept only the last | Noticed when reading reports | Yes: skill script fix (report named after the file) | not yet |
