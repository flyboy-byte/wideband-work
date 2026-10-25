# Findings: Astra review / Codex, 2026-10-25 — round 6

Reviewed: `e0b802a5ca53d679b9fa85e5889658d3f74d6dab` on `analog-out`. Mode B, full repo (prior rounds visible, not blind).
Tools available: shell, KiCad, ngspice + locally licensed TI model, ARM compiler. No hardware. Review branch/folder dated as requested by owner.

## Verdict

Would I order these files as they are? **Not yet assessed**: review in progress; no release or hardware approval implied.

## Coverage (one row per task in TASKS.md; fill it in as you go, not at the end)

| Task | Status | Finding IDs | What I did (command, file, calculation) |
| --- | --- | --- | --- |
| TK1 Fab files | PARTLY | — | MEASURED: 26/26 BOM and 38/38 CPL rows match board and cached transforms; 6 not-fitted consistent. `TK1-rows.md`, `TK1-fab.log`, `TK1-rotation.log`. JLC machine placement preview not available. |
| TK2 Module files | OK | — | `TK2-rotation.log`: 57/57; four questions independently answered in `TK2-module.md`. Torex primary datasheet resolves U9 override; JLC preview still needed as for TK1. |
| TK3 Boot level | PARTLY | — | Digital fix checks out: primary datasheets, both board.h files, SEL1 compile guard. Worst old-pullup bound 0.575V at 3.6V including R3+1%; PWM load <0.774mA. Rail sequencing/analog reset transient not established; see TK3-boot.md. |
| TK4 Invalid output | PARTLY | — | 21/21 aux tests pass, source path table in TK4-invalid.md. Normal invalid states command5V; sensor fault detection and receiver response cannot be universalized from this logic. |
| TK5 Heater clamp | PARTLY | — | 70/70 host tests and 2 new production-code sequence tests pass. 60s clamp and30 recovery cycles; integrator bounded±3V. See TK5-heater.md; thermal plant/overshoot not simulated. |
| TK6 Analog DC | PARTLY | R6-S1 | Independent exact RC ripple0.658/0.421mV at50/80%; gain tolerance calculation; primary LM2904 limits. Full-scale sweep running; longer-window/zero cases queued for later evidence update. TK6-calculations.md. |
| TK7 Stability | PARTLY | — | Reviewed actual E topology and measurement validity; five nominal step cases queued serially behind TK6. No phase-margin/process-corner claim. TK7-stability.md. |
| TK8 Faults | FINDING | R6-S2 | Calculated12V injection13.6mA into held5V rail; no guaranteed sink. Grounded output~5.2mA in illustrative coupled-supply model. Open power ground routes heater current through receiver ground. TK8-faults.md. |
| TK9 Op-amp supply | FINDING | R6-S3 | At illustrative38.9V/400ms:R9 437mW/0.175J,D5 376mW/0.150J. Exact vendor pulse/thermal data missing; nominal ratings do not establish survival. TK9-surge.md. |
| TK10 Layout | FINDING | R6-S4 | DRC0new/0open; vias0new; layout0triggers. Supply-cap distances1.69/3.94/2.73mm; C11 body~1.60mm from edge vs JLC2.5mm rule. TK10-layout.md/log. |
| TK11 Wiring sheet | PARTLY | R6-S5 |12/12 J3 and6/6 J2 pad mappings match PCB; Tag-Connect primary drawing confirms1:1IDC cable. Clone/moulded housing identity and through-cutout reach remain physical checks. TK11-wiring.md. |
| TK12 Firmware diff | FINDING | R6-S6 | Read18changed files; fresh firmware package passes(21616Bapp,CRC984fc2b4). Existing checker passes but real indirect-recursion ELF falsely passes116/256B. Configured checks running; TK12-firmware.md. |
| TK13 These docs | OK | R6-S1,R6-S5 | Reviewed task/report/setup against sources and all25configured checks. Specific corrections below; checker itself reports docs consistent. |
| TK99 Beyond the list | | | |

Status: OK = checked and found right; FINDING = see the table below; PARTLY = say what is left; NOT CHECKED = say why
(no tool, no time, no file).

## Findings

| ID | Task | Severity | Location | Evidence (numbers) | Smallest fix |
| --- | --- | --- | --- | --- | --- |
| R6-S1 | TK6 | NOTE | `work/docs/carrier.md:134,143` | DOCUMENTED TI SLOS068AB5.8: plain LM2904 offset3mV typ/7mV max at25C,10mV over temperature; CALCULATED output offset bound11.76mV at25C vs cited5.04mV. | Correct accuracy budget to the exact ordered variant's limits; retain two-point calibration. |
| R6-S2 | TK8 | RISK | D3/+5V, `work/docs/carrier.md:91` | CALCULATED12V fault injects13.6mA if rail held5V; ST L78M has no guaranteed sink. Unpowered initial R11 load276mW. Previously open backfeed risk remains unqualified, especially receiver connected while board off. | Establish sink/clamp behavior and receiver protection for powered/off states, or isolate the clamp from the unsinkable rail. |
| R6-S3 | TK9 | RISK | R9 C4410 / D5 C173425 | CALCULATED38.9V/400ms ideal18V clamp:R9 0.437W/0.175J(1.75x nominal continuous rating); exact UNI-ROYAL/MDD pulse qualification absent. Not proof of failure, but survival is unestablished. | Qualify exact parts against protected waveform, or select a documented pulse-rated R9. |
| R6-S4 | TK10 | RISK | C11(50.4,104.4mm),lower edge | MEASURED center1.85mm/body~1.60mm from edge; DOCUMENTED JLC assembly terms require body clearance2.5mm. Bare-board assembly route not yet qualified. | Obtain JLC rail/panel acceptance;5mm tooling rails may avoid layout changes. |
| R6-S5 | TK11 | NOTE | `work/docs/wiring.md`,optional J3-7 fuse paragraph | DOCUMENTED claim promises250-500mA fuse opens before receiver damage; no time-current/I²t or receiver withstand evidence. Rating alone cannot prove coordination. | Qualify exact fuse/receiver combination or label it an unverified candidate. |
| R6-S6 | TK12 | BUG | `work/checks/stack_estimate.py:109` | MEASURED real indirect recursion with108B per level accepted as116/256B,exit0; verbose path hangs. Production's64B margin is not a proven bound. | Fail unresolved indirect cycles, or prove target exclusions; add the retained ARM regression. |

Severity: BLOCKER = don't order; BUG = wrong but workable; RISK = could bite (say when); NOTE = worth knowing.
Tag each piece of evidence: MEASURED (you ran it), CALCULATED (show the sum), DOCUMENTED (name the datasheet and page),
INFERRED (your reasoning). A finding without a number or a source is a NOTE.

### Two examples of the level we want (from earlier rounds)

- **Round 4, heater (BUG):** "`heater_control.cpp`: the effective heater voltage goes negative above the target
  temperature and is then squared into a duty. Feeding the host model a sensor at 806 C gives 65 % duty, at 840 C
  100 %, so a hotter sensor gets more heat. Fix: clamp the voltage at 0 before squaring." It has a location, a run
  with numbers, and a one-line fix.
- **Round 5, boot level (BUG):** "Both `board.h` files set PB1 as an input with its pull-up on (`board.h:335`,
  `bootloader/cfg/board.h:333`); the app only hands PB1 to TIM3 in `InitAuxDac()`. Pull-up 25-55k against R3 100k
  gives 2.13-2.64 V, a high at U4, so J3-5 sits at 5.04 V for about 0.8 s at every key-on, and indefinitely in the
  bootloader. Fix: R3 to 4.7k (0.52 V worst case), and/or a pull-down in both `board.h`." It cites the lines, does
  the sum, and names the condition that makes it matter.
- Not useful: "consider adding ESD protection to the output". Where, against what, and why is what's there not enough?

## Checked and found right

### TK1

MEASURED: the independent `placement_rows.py` checks every BOM/CPL row, including value, package, LCSC field, side, position and angle arithmetic. All match. Five high-risk pad-net/transform checks are recorded in `TK1-rows.md`: D2 cathode goes to protected supply (not raw); U2 tab is GND, leads input/output, offset 0.725 mm; U4 pins 1/3 GND, 2 PWM, 4 output, 5 reference; U5 pins 1/2/3 input/reference/GND; U6 pins 1/2/3 output/negative/positive, 4 GND, 8 supply, 6/7 tied as unused follower. These match the ST L78M, Nexperia 74LVC1G125, TI REF30 and LM2904 pin conventions inspected in the earlier source review. CAD values are not proof of delivered component identity. Independent arithmetic still shares the cached footprint data with the exporter; final JLC preview is outstanding. No definite reversed part found.

### TK2

DOCUMENTED/MEASURED: U9 pinout override is correct (Torex XC6206 ETR03005-009 p3). Q1 tab/drain is board pad 2; CPL correction and shift agree with the footprint fit. R10 keeps 61.9 ohm and improves initial tolerance; C3 is the 33 nF feedback capacitor in parallel with R33 10k, not a bypass cap. See `TK2-module.md` for calculations and primary sources.

### TK3

DOCUMENTED/CALCULATED: R3's digital low margin is adequate, PB1 is not read as a strap in this build, and PWM drive current is small relative to the specified GPIO capability. Bootloader/update/no-valid-app all retain the low command. That is a steady command guarantee, not proof that the connector is 0V during every supply ramp or immediately after a reset from full scale. `TK3-boot.md` gives the state table and measurement needed.

### TK4

MEASURED:21 auxiliary tests pass (`TK4-aux.log`). DOCUMENTED: every failed software validity predicate overrides the curve with5V; test mode intentionally bypasses it. INFERRED:5V is a reasonable lean-side fallback for a correctly configured AFR10-20 receiver, but is indistinguishable from a real lean reading and cannot guarantee safe fueling. Physical disconnect detection latency and specific receiver policies remain bench/configuration questions. See TK4-invalid.md.

### TK5

MEASURED: sustained zero clamp recovers; no permanent stuck state in30 cycles. CALCULATED: integrator can wind to its existing±3V limit, but cannot grow indefinitely. Recovery has one50ms derivative kick at the12V cap, then4.5V at target, then increasing heat on cooling. This verifies control-law sequences, not physical stability. See TK5-heater.md.

### TK6

CALCULATED exact periodic RC states give0.658mV p-p at50% and0.421mV at80%, residual<1e-15V (`TK6-filter.log`). Gain1.68, resistor-only extremes1.666535..1.693737. Full-scale and zero conclusions remain pending simulator completion; no result is inferred from the designer's saved output. Primary datasheet contradicts the3mV maximum offset in the accuracy documentation (R6-S1).

## Could not check

<what, and what you would need>

## TK13: what would have made this review faster

1. Keep exact ordered manufacturer/variant and primary datasheet URLs in the pack. U9's UNKNOWN pinout was readily settled from Torex's primary PDF; same-name MDD/Diodes zeners must not be conflated. R6-S1 corrects the plain LM2904 maximum offset.
2. TK9 still says35-48V though carrier.md corrects the SMCJ24CA assumption to~27-39V. Name the actual protected waveform and source impedance; a TVS headline clamp rating does not qualify400ms load dump.
3. TK6's11-13V op-amp rail description omits load-dependentR9 drop; the current full-scale run measures as low as7.02V. State supply input and measured op-amp rail separately.
4. Include the simulator initialization requirement explicitly: `work/sim/.spiceinit` sets `ngbehavior=psa`. TI's model fails outside that directory without the equivalent setting. My extra harness initially ran in the wrong cwd twice; raw failures are retained, not called circuit failures. Existing wrappers correctly cd into sim/.
5. Describe `boot_level.py` as a static digital-level check, not proof of every power-ramp/reset transient (TK3). Physical unplug latency and lower-priority thread freshness are separate from the validity predicate (TK4).
6. The optional signal-ground fuse paragraph promises coordination without fuse/receiver I²t data (R6-S5); remove the assurance until qualified.
7. Minor stale source comments: test/aux_out/test_aux_out.cpp's NaN-voltage test still says invalid lambda is replaced by0V; current policy is5V. can_helper.cpp comment says about9Hz but two100ms frame waits would be about5Hz; the nonblocking fix itself is correct and tested.
8. `run_all.py` rewrites the designer's STATE.md and tracked timestamped reports. A read-only/report-directory mode would make independent reviews easier. This audit ran all25configured checks through its own runner, preserving STATE.md; the module command verified existing staged files without regeneration.25checks finish with23zero exits and2accepted advisory DRC failures. Those passes do not invalidate the new stack-checker counterexample.
