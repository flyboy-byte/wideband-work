# Codex raw audit conclusions — 2026-10-23

Audited HEAD 34cd49d, design 986c803. Independent reviewer: Codex.
No board, schematic or firmware modifications.

1. R11 limits current into D3/+5V but does not prevent back-feed. Fault survival is not proven without a guaranteed sink/clamp in powered and unpowered states. Do not assert a specific resulting rail voltage from this current budget alone.
2. 5.04 V nominal stage full scale through 470R gives 4.813754 V into 10k. Software trim cannot exceed 100% duty. Explicit 1% feedback-resistor corner gives 4.976216 V even into 100k, before other errors. Endpoint tolerance remains a requirement to resolve.
3. Shared J3-1/J3-7 GND allows heater current into a connected sensor-ground wire. Main-ground disconnect makes this more consequential. Withdraw the unconditional sensor-ground instruction.
4. layout_review.py produces different longest-gap numbers with identical copper under track-list reversal/sorting. Reproducer exits 1, as expected. Whole-net upstream exemptions also omit added CAN-to-sensor checks.
5. Typical TI macro-model small-signal tests with R9 and both amplifier sections look stable at 12 V / 100k / 1p–47n. Full-scale DC attempt timed out at 60 s; this is unknown, not a failure or pass of the circuit.
6. Plain TI LM2904 rating is 26 V; 32 V belongs to LM2904V. A larger resistor package alone does not qualify pulse/sustained surge behavior.

Separate measured outputs: analog-results.jsonl, calculations.jsonl, layout-order.txt.
Durable sourced report: ../../docs/codex-audit-2026-10-23.md.
No hardware testing, fault injection, complete firmware audit, new host-test run, ordering or publishing performed.
