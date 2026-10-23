# Lessons — rusEFI wideband

Every mistake caught on this board, with when and what caught it. At bring-up and after each order, propose the ones
that would help any board as a line for the `pcb-design` skill (see its "Lessons back to the skill" section).

| Date | Stage | What went wrong or nearly did | What caught it | General? | Sent to skill |
| --- | --- | --- | --- | --- | --- |
| 2026-10-23 | Requirements | Claimed module SEL pads were unused by firmware; the grep output was cut by `head -12` before the f0_module match | Re-check of the plan by a second model reading `port.cpp` | Yes: don't treat absence in truncated output as evidence | not yet |
| 2026-10-23 | Requirements | Counted module pads from the carrier-side symbol (14) instead of the module netlist (16) | Netlist export during the re-check | Yes: count pins from the board's own netlist, not a symbol drawn for another board | not yet |
| 2026-10-23 | Requirements | Proposed PA8 for PWM without checking which timer channel it shares; it is the heater's TIM1_CH1 complement | Re-check reading `io_pins.h` and the AF table | Yes: check timer and channel sharing before reusing a pin for PWM | not yet |
| 2026-10-23 | Checks | `kicad_check.py` wrote every board's report to the same `checks/out/drc.json`, so a two-board project kept only the last | Noticed when reading reports | Yes: skill script fix (report named after the file) | not yet |
| 2026-10-23 | Parts | Proposed taking op-amp feedback after the output's series resistor (to cancel load error) without checking stability; with TI's LM2904 model it oscillates at 10 nF and 47 nF of cable | `work/sim/stability.sh` with the maker's SPICE model | Yes: simulate any op-amp stage that drives a cable with the maker's model, across cable capacitance, before choosing the feedback point | not yet |
| 2026-10-23 | Layout | Said the bottom layer had no copper and removed 18 GND stitching vias; upstream's GND pour is on both layers (unfilled in the file), so the vias joined the pours | DRC unconnected items after refill | Yes: check every zone's layer set before calling stitching vias useless | not yet |
| 2026-10-23 | Layout | A new top-side track cut upstream's 12V_RAW pour in two | DRC unconnected (12V_RAW zone to itself) | Yes: when adding to an existing board, keep new tracks off other nets' pours (rule area during routing) | not yet |
| 2026-10-23 | Layout | Freerouting 2.5.0 necked tracks to 0.15-0.19 mm (below the 0.2 mm rule), ignored the module's inner Edge.Cuts cutout and the 0.5 mm board-edge clearance | DRC track_width / copper_edge_clearance | Yes: widen after SES import; give the router keep-out rule areas for cutouts and the edge, remove them after | not yet |
| 2026-10-23 | Layout | Upstream carrier silkscreen labels module pads TX/RX/nRESET; the current module has SEL_1/SEL_2/VBatt_Sense there | Comparing the bottom render with the module's own .kicad_pcb pad nets | Yes: check silkscreen pin labels against the mating board's pad nets | not yet |
