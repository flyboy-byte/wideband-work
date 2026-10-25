# TK99 finite measurements can still be failed simulations

MEASURED: extra120ms supply-start tests with the real TI model abort at5.22409us(charged supply) and179.768us(zero supply). ngspice47 exits0, then its measurement commands print finite zeros for averages requested115-120ms; real raw outputs are TK6c-long-ic11.6.out/TK6c-long-ic0.out. Their `.meas` output explicitly has ending time before starting time. These are **failed numerical analyses**, not zero-output hardware predictions.

My first audit parser also checked only exit status/finite measurements and incorrectly printed PASS. That log is retained as an attempt, **superseded** by `sim_zero_regression.py` plus `spice_validation.py`, which reject both actual abort logs and accept the two completed zero-input logs. No conclusion relies on those incorrect PASS labels.

Production finding: full_scale_corners.sh checks exit status and five numeric fields but no abort diagnostic or final simulated time. The regression injects output shaped like the real abort (RES0 0 0 0 0,exit0,explicit abort diagnostic) into an untouched temporary copy of that production wrapper. It reports27connector0.0000cases and returns0. TK99-zero-regression.log and TK99-wrapper-zero.out preserve the test. This is a wrapper fault injection supported by an actual ngspice failure mode, not a claim that the original27-case sweep failed.

Smallest fix: retain raw diagnostic output, reject an aborted analysis, and record/check the final time vector against the requested window. Do not simply reject zero: valid physical measurements can be zero. Existing test_sim_failures.py covers missing measurements in older wrappers, not the new full-scale wrapper or aborted finite-zero results. Add this case to fail-closed tests.

The exact extended deck failed after changing maximum timestep from5us to20us and stop60ms->120ms; this demonstrates numerical sensitivity, not a circuit instability. No attempt to force convergence or alter device parameters was used to call it passed. The valid original27cases remain nominal model evidence; startup-basin independence is still not established.
