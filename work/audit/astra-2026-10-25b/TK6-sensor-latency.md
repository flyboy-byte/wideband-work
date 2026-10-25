# TK6 — production filter + heater latency, not physical unplug qualification

Picked round6 TK4's sensor-fault latency gap. **Added evidence, still PARTLY:** physical unplug waveforms and ADC cadence are not known from this host fixture. Power ramps, real thermal loop and TI startup-basin independence were not repeated.

MEASURED `run_sampler_latency.py` builds unchanged production sampling.cpp,heater_control.cpp,pid.cpp,timer.cpp with **the f0 board config**, ASan+UBSan.19stimulus/schedule cases pass. Source/command/raw values retained in sampler_latency.cpp and TK6-latency.log; no design edits. No fake temperature is supplied: real Sampler derives it from Nernst history and the actual ESR IIR.

Stimuli are explicitly synthetic, not claims about an unplugged LSU:

- Warmed sample stream represents300ohm,DC0.45V. After settling, ADC samples jump to a6000ohm-equivalent AC amplitude with **DC unchanged**. This uses the actual divider relation3.3*(ESR+10)/(22000+ESR+10),matching sampling.cpp:82-89 and f0 port.cpp:193-197. All sample voltages are asserted inside the f0 ADC-scaled range0..3.3/2.7V.
- Alternative fault changes DC0.45→1.00V while retaining300ohm AC. Third case stops all new samples while continuing time/heater updates.
- Assumed sample intervals100/400/1000us; three heater phases per interval,real50ms Update period. These timings are a sensitivity study, **not a measured/proven minimum sampling rate**. CAN auxiliary scheduling and analog output settling are not simulated here. Validity predicate is explicitly copied from auxout.cpp:165-171 with lambda fixed1.0; its actual implementation is covered separately by21shipped aux tests.

| Stimulus | Observed result |
| --- | --- |
| ESR300→6000,DC unchanged | Temperature drops below680C after46samples:4.6/18.4/46ms. Reported0C occurs at966samples:96.6/386.4/966ms. Heater stops and validity predicate clears after526–576ms across these schedules; duty0. |
| DC0.45→1.00V | Validity predicate clears on the first new sample:100/400/1000us. Heater need not stop because this stimulus retains a warm ESR. |
| No new samples,previously valid | After2s heater stillclosed-loop and predicate stillvalid. No freshness timeout appears in these paths. This is evidence for the **already known heater-only watchdog scope**, not a new unexpected watchdog defect. |

DOCUMENTED mechanism: sampling.cpp:110-112 updates unfiltered three-sample DC and ESR IIR alpha0.002; its approximate63% response is499.5samples. GetSensorTemperature returns0 only above5000ohm,but heater underheat threshold is already680C, so the0C transition is not the stop-time gate. heater_control.cpp:142-155 uses a strict elapsed>0.5s timer, checked every50ms. `can.cpp:41-44` updates aux output on its10ms loop when scheduled normally; add up to one such period **conditionally**, then analog/receiver response. This is not a hard scheduler WCET bound.

## Physical follow-up / scope fence

A plug-open can change both DC and AC,including clipping and bias paths; neither synthetic stimulus is a validated electrical sensor model. Actual unplug-to-voltage latency needs a benign sensor-open fixture and voltage capture, or a verified analog front-end model plus measured sample timing. The owner's multimeter alone cannot capture that timing. Do not disconnect a hot sensor as a casual test. A safe future test keeps the heater load separately controlled, injects known low-energy sample-side voltages, records raw samples/status/PWM and exercises Nernst open,Vm open,ADC-stall and reset cases. Any freshness-supervisor design change is a separate proposal,not implemented by this reviewer.
