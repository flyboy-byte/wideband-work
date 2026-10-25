# TK8 fault-current bounds

DOCUMENTED from carrier PCB net membership: J3.5 -> R11.2; R11.1 is D3 anode/D4 cathode/R8.2; D3 cathode+5V; R8.1 op-amp output. J3.1 and J3.7 bothGND. `carrier-nets.txt` matches pcbnew inspection from TK1. ST [L78M DS0425](https://www.st.com/resource/en/datasheet/l78m.pdf) pp7-8 specifies output **source** regulation, not guaranteed current sinking.

## 12V applied to output
CALCULATED **if +5V stays at5V** and diode drop0.6V: I=(12-5-.6)/470=13.62mA, R11 dissipation87.1mW. At16V:22.13mA and230.1mW. These are conditional operating points, not proof the rail stays5V. With no guaranteed rail sink/minimum load, injected current charges the rail and stresses the transceiver/reference/module; U2 cannot be assumed to absorb it. With the board off and rail initially0V,12V fault gives24.26mA and276.5mW until rail rises (above nominal0.25W R11 during that transient). Reverse/back-powered component paths are not bounded by a resistor-only calculation.

INFERRED: R11 limits injection substantially, but cannot establish 'does not damage ECU' or hold a safe rail. Board survival at12-16V is explicitly not required; protecting an external receiver still depends on its input protection, ground, power state and which fault is being applied. This is the previously unresolved backfeed issue, not a newly discovered omission of R11. Proposed next test: unpowered/operating board at bounded injected current, recording+5V and receiver pin current; or isolate the output clamp from a rail that cannot sink. A meter and iron alone cannot establish this without a controlled source.

## Output grounded
CALCULATED illustrative bound with protected input11.6V, op-amp high-side drop1.5V and both-amplifier supply current0.7mA: output current=(11.6-1.5-0.7)/1800=5.22mA; rail5.68V; R8=9.0mW,R11=12.8mW,R9=35.1mW. Op-amp heat estimate1.5V*5.22mA+5.68V*0.7mA=11.8mW. No resistor overload indicated.1.5V drop/0.7mA are illustrative typical assumptions, not guaranteed worst-case constants; source current and rail self-limit together. At protected15.6V same approximation gives7.44mA,R9~66mW.

## Power ground open
INFERRED from exact same-net connection: receiver ground becomes the power return if J3.1 opens and J3.7 remains connected. If heater current is2A (illustration, not a measured cold-sensor maximum), a0.1ohm receiver return dissipates0.4W and produces200mV error;1ohm gives4W/2V, until supply/current protection changes operation or something opens. Actual current/damage requires harness and receiver impedances, absent here. A low-current signal-ground fuse has no guaranteed coordination without its time-current/I²t and receiver withstand data. This existing system wiring risk cannot be removed by claiming J3.7 is a separate ground on the PCB.
