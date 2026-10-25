# TK2: simulator completion and baseline fix

MEASURED26shipped fixture verdicts all correct(TK2-fixtures.log). Independent completion_replay.py replays both actual round6 aborted outputs, plus diagnostic-free partial outputs carrying their real final times; all rejected. Valid0.12s accepted for0.12s request;0.119s,NaN,Inf,missingEND rejected(TK2-replay.log).

DOCUMENTED completed.sh checks END against the requested stop with1ppm numerical tolerance and rejects timestep-too-small,aborted,fatal-error,singular-matrix diagnostics. Each fresh ngspice process has one transient; END is computed from its current time vector after run. All wrappers also require simulator exit0 and their required numeric measurements. There is no earlier transient plot to supply a stale complete END in these decks. Missing or failed runs before time-vector creation cannot produce the required END. No realistic residual false-PASS mode established in these paths.

MEASURED real stability.sh25cases finish with completion/baseline guards,exit0,79.8s(TK2-stability.log). As-built E at1p/1n/10n/47n/100nF:overshoot0/0/0/9.2/22.4%;1%settling258/255/219/95/621us. Baselines all1.6823V. Current0..10nF conclusion is unchanged and supports nominal small-signal stability, not all process/supply/load corners or phase margin.

The0.5mV pre-step drift limit is0.30%of the168mV test step. It compares two means, so it is a DC-drift guard, not proof that an oscillatory waveform is settled. A/B include intentionally oscillatory controls: a sweep PASS means valid data, not that every topology is stable. For E100nF,terminal3.6-3.8ms window still has3.49mVexcursion and vf1.8509V vs1.8503V from the longer round6 run;22.4%vs22.8%is measurement-window dependence, not a new instability. Do not interpret the last decimal as a physical guarantee. Extending the final window would improve that diagnostic case; requested0..10nF result is unaffected.

No designer files changed. Full27case DC resweep is not needed to re-prove the completion logic; round6's independently retained successful corners remain separate evidence.
