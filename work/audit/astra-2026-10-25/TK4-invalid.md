# TK4 invalid output paths

Sources reviewed: firmware/auxout.cpp:145-216, boards/f0_module/wideband_board_config.h:33, boards/f0_module/aux_curve.h, lambda_conversion.cpp, heater_control.cpp:33-36,110-159. MEASURED 21/21 existing production-code auxiliary tests pass with ASan/UBSan; TK4-aux.log.

| Condition | Command | Source/qualification |
| --- | --- | --- |
| Preheat/warmup/stopped/overheat/underheat |5.0V| IsRunningClosedLoop false; update on next CAN TX loop iteration |
| Nernst <=0.35 or >=0.55V, or NaN |5.0V| strict predicate in auxout.cpp:168; NaN comparisons false |
| Lambda <=0.6, negative, NaN, -infinity |5.0V| comparison fails |
| Lambda +infinity or very large finite |5.0V| passes lower bound but curve saturates at5V; same electrical result, not valid-data evidence |
| Lambda0.6..10/14.7, otherwise valid |0V| legitimate rich curve saturation; not classified as fault |
| Finite lambda within range and valid Nernst/heater |linear0..5V| compiled AFR10..20 curve |
| Boot before InitAuxDac |low command| TK3; invalid policy not running yet |
| auxCfg null |retains prior command| function returns; normal f0 InitAuxDac always obtains address of static config, so no normal-runtime null path found |
| SEL2 grounded at startup |1/2.5/4V stepping| explicit bench mode bypasses all validity checks; do not leave strap installed in operation |
| Sensor unplugged |not necessarily immediate5V| software must first detect changed Nernst/heater state; a stored valid sample can remain for an interval |
| Dead/stalled auxiliary thread |retains last voltage| heater-only watchdog coverage already accepted; no freshness supervisor here |

INFERRED verdict on failure level: yes,5V is preferable to0V for the stated lean-side fallback **when the receiver is configured for increasing voltage=increasing AFR and its correction limits are appropriate**. It is not an out-of-band fault code. Full lean can cause extra fuel, and on a gauge simply displays lean; it is not a universally safe condition. Speeduino EGO enable temperature/delay/correction bounds and the actual FlashPro/gauge voltage calibration must be checked in the actual configuration. No universal 'none supports a fault band' claim was verified. No new midrange command path found for a predicate that evaluates invalid.

Physical voltage may be below5V under the accepted low-5V/4.7k load limitation (TK6). Command5.000V and measured connector5.000V are different claims. Sensor-unplug latency needs a bench test; these host fakes substitute validity inputs and cannot validate physical detection.
