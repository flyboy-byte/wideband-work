# Independent r41 review — Codex, 2026-10-24

**Would I order these files as they are? No—not on this round's evidence:** two verification tools can conceal missing coverage, and this is not yet a complete electrical/fabrication sign-off. Neither finding establishes a physical board defect. Keep the circuit unchanged until the designer evaluates the evidence.

Reviewed commit: `fad803240534f08eb3fbd7ce15ddc386e75148bb`, r41; pack was at `8ad4b28`. Mode B, full repository; not a blind review. Model-specific branding is not asserted. This report follows `REVIEW.md` and `AUDIT.md`'s hand-off, using the PCB skill's measurement-first audit procedure. No generators, schematic, board, or production firmware changed.

## Findings for the designer

| ID | Severity | Location | Evidence | Smallest fix |
| --- | --- | --- | --- | --- |
| R41-CX1 | BUG | `work/checks/stack_estimate.py:83` (target discovery), `:116` (indirect depth) | DOCUMENTED by `stack_counterexample.py` and `stack-counterexample.txt`: a real ARMv6-M ELF uses an 8-byte caller frame plus a 400-byte callee through `blx r3`; pointer is in a `.text` literal pool. Checker discovers zero targets, reports 8/256 bytes, exits 0. Actual nested frame is 408/256. | Fail as unbounded when indirect targets cannot be established. Audit actual ELF targets explicitly or use a sound conservative superset; add this counterexample as a regression. Do not advertise a worst-case bound until recursion/cycle and indirect-target assumptions are justified. |
| R41-CX2 | BUG | `work/sim/load_accuracy.sh:35-36` | DOCUMENTED by `sim_failure_test.py` / `sim-failure.txt`: replace only the child-process simulator with one that always exits 1; all 48 cases have missing voltages, yet wrapper exits 0. `stability.sh:51-55` also formats missing values as zero, although this all-failure test exits 1 through printf errors. | Require simulator success **and** finite complete measurements per case; preserve stderr and mark failures explicitly; fail the whole sweep if any case fails. Exit status alone is insufficient: actual ngspice failed to converge on two independent decks while exiting 0. |

Both are open. R41-CX1 is a defect in the verifier, **not a claim that the production firmware overflows its stack**. R41-CX2 does not invalidate previously recorded finite measurements; it prevents trusting future unattended runs merely because their process exits successfully.

## Circuitry and theory checked

DOCUMENTED topology: `work/gen/gen_carrier_sch.py:74-88` connects R6 to J3-5, R8 then R11 in series, C15 from op-amp output to the inverting input, and R9 feeding the op-amp supply. Netlist self-check and board checks were rerun separately; the generator table alone is not electrical proof.

INFERRED from those values: at DC, when the amplifier remains linear, `Vconnector = Vinput * (1 + 68k/100k)`. Thus moving feedback past R11 removes its former load-divider error. It does **not** remove the load current, output swing requirement, clamp conduction, resistor tolerance or offset. The amplifier must supply both receiver current and the feedback divider current. At 5 V into 4.7k, R11 carries approximately `5/4700 + 5/168000 = 1.094 mA`; the clamp node must be about `5 + .001094*470 = 5.514 V`. D3 conduction can therefore matter during ordinary full-scale operation, not only a wiring fault.

DOCUMENTED independent runs (`circuit_tests.py`, saved `.cir`, `.log`, `circuit-results.json`):

| Case | Connector result | Other observation |
| --- | --- | --- |
| 1→1.1 V input, 100k load, 10nF cable | 1.68227→1.85027 V; 0% overshoot | Model's late range rounds to 0 mV |
| Same, 47nF cable | 1.68227→1.85027 V; 9.238% overshoot | Peak 1.86579 V; late range rounds to 0 mV |
| 5 V target, 4.7k load, 12 V protected supply | 5.00211 V | Supply after R9 8.9103 V; clamp node 5.51631 V; 0.223 mA into ideal 5 V source |
| 5 V target, 10k load, 12 V supply | **No valid result** | Initial operating point failed to converge |
| 5 V target, 4.7k load, 7 V supply | **No valid result** | Initial operating point failed to converge |

These independently reproduce the small-signal cable result and support the connector-feedback change at one full-scale load. Failed convergence is neither a hardware failure nor a pass. Do not interpolate the 7 V case from the 12 V result.

Model boundaries: TI SNOM268 LM2904 macro-model, both amplifier instances, actual 1k feed and 10u/100n decoupling. Added silicon diodes are a **sensitivity model**, not a qualified C2128 model; 5 V is an ideal source capable of sinking injected current. The resulting injection is a prompt to include the real 5 V rail/load in the next model, not proof of actual backfeed behavior. Zener is omitted because these cases are at/below 12 V. Protected supply is AFTER the input Schottky, not raw battery. Typical macro-model, no Monte Carlo, no guaranteed temperature/process corners, no PCB/cable inductance. Two amplifier instances do not establish actual package quiescent current accuracy.

INFERRED filter check: with the two equal unbuffered RC sections (3.3k/100n, high-impedance amplifier input), `H(s)=1/(1+3sRC+(sRC)^2)`, not the transfer of two buffered isolated poles. DC gain is unity; PWM averaging is plausible, but ripple/settling must use that loaded ladder plus the output stage. C15 makes feedback frequency-dependent; a DC gain calculation cannot establish stability. The independent transient runs support only the stated loads/steps.

INFERRED supply arithmetic: using the stated 39 V protected-rail endpoint and nominal 18 V zener, `(39-18)^2/1000 = 0.441 W` in R9, exceeding its stated 0.25 W continuous rating. A larger package alone is not surge qualification; pulse duration, actual TVS clamp current, resistor pulse rating and zener tolerance/current remain necessary. This is a coverage limit on the existing known surge risk, not a new demand for automotive qualification. No 12–16 V output-fault survival requirement has been invented.

DOCUMENTED external primary source checked: [TI LM2904 family datasheet](https://www.ti.com/lit/ds/symlink/lm2904.pdf), SLOS068AB. Plain LM2904 and B/V variants must not be conflated. Typical-model results cannot replace guaranteed limits for the fitted part.

## Checks and firmware evidence

DOCUMENTED `checks.json` in this folder records all 20 configured commands, full captured output, return codes and durations, without replacing the designer's STATE or last_run summary. Carrier delta is zero new violations/open nets; ERC, drift, layout, netlist, rotation and fab-candidate checks succeed. The two raw DRC failures are the documented accepted upstream baseline.

Initial host suites printed 69 and 21 passing tests but exited unsuccessfully under the tracing sandbox. Aux suite explicitly reported LeakSanitizer's ptrace incompatibility. Retried both outside that sandbox, **without disabling sanitizers**: `python3 checks/host_tests.py && make -s -C ../test/aux_out run` returned 0, with 69 and 21 passing tests. Keep the initial failures visible in `checks.json`; do not rewrite them as passes. `make -C firmware -j8 BOARD=f0_module` returned 0 with “Nothing to be done”; that is not a fresh independent build.

Bootloader guard, package checker and M0 fault-entry checks succeed. Watchdog source starts/refreshes in the heater thread, consistent with the owner's selected coverage; the fake-register tests are not an on-chip timeout/heater shutdown measurement. Static stack check currently passes the production ELF, but CX1 prevents interpreting that as a proven upper bound.

Fab/rotation: reran the 38-part cached EasyEDA fitting and candidate check; read the pairing/origin transform implementation. This verifies consistency with those cached assumptions, not an independent manufacturer's pin-drawing audit of every part, Gerber visual inspection, or JLC placement preview. Those remain unfinished; no order-ready claim.

## Follow-through / next bounded work

1. Designer verify CX1/CX2 with the supplied reproducers, fix the checkers, and retain failure-path tests. No circuit change implied.
2. Resolve the failed convergence cases without silently changing the circuit. Add real clamp/vendor model and finite 5 V rail/source loads; include receiver pull-ups, large steps and supply/load corners. Preserve accepted low-output pull-up limitation.
3. Independently inspect D2 polarity, U2 origin/tab and every active-part pinout against manufacturer drawings; visually inspect Gerbers/JLC placement before money gate.
4. Review the entire upstream sensing/heater/control loop and new firmware behavior separately; this round is **not** an exhaustive proof of those systems. On-chip flashing, reset/heater-safe-state tests and stack high-water checks still require hardware.

Nothing ordered, flashed, regenerated or merged. Owner's open KiCad lock left untouched. This is a hand-back for Opus to verify, not a silently applied design fix.
