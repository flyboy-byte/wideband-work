# TK5 heater clamp and recovery

MEASURED: existing70/70 host tests pass (TK4-host.log). Two additional tests in heater_recovery.cpp run actual heater_control.cpp/pid.cpp with mock time and sampler (TK5-recovery-fixed.log):
-60s at ESR200ohm,840C stays ClosedLoop and zero duty.
- Returning to ESR300,780C gives first duty0.852071 (12V effective at13V supply), then0.119822 (4.5V effective) after1s.
- ESR320,771C then produces12V effective within1s.
-30 hot/cool cycles retain ClosedLoop, hot duty0 and recovered duty in(0,(12/13)^2].

DOCUMENTED: pid.cpp:7-30 updates integrator then clamps±3V. heater_control.cpp:186 returns7.5-PID, Update clamps0..12V before squaring. CALCULATED: hot ESR200 vs target300 gives error100, proportional30V, so steady integrator+3 and command7.5-33<0 ->0. At exact target after the derivative transient, PID=3 so4.5V. With error-20, integrator changes-0.3V each50ms and can traverse+3 to-3 in1s. No unbounded wind-up; no stuck zero state under cooling. At target, the integral remains+3 until a nonzero error changes it, which is ordinary integral memory.

The abrupt100ohm error change produces derivative-20V for one50ms cycle, hence the measured12V cap. This is a synthetic step; no thermal plant or measured ESR noise spectrum is modeled. It is not evidence of actual temperature overshoot, and it does not establish phase margin/robust closed-loop stability. A thermal model or logged real sensor response would be required for that stronger claim. A conditional anti-windup redesign is not justified by a stuck state here.

Attempt log: first harness compile failed because the audit file omitted<cmath>; TK5-recovery.log retained. Added header and reran; two tests pass under ASan/UBSan. Test sources and runner are confined to this audit folder.
