# TK6 measured results and limits

MEASURED: reran full_scale_corners.sh;27finite nominal results,exit0,711.37s (TK6-fullscale.log/json). They reproduce the designer's values:
- +5V4.8V,4.7k pull-down:4.9338V at protected13.4V,4.9129V at11.6V,4.8218V at9V: deficits66.2/87.1/178.2mV, the accepted R1 limitation.
-10k/100k pull-down across tested rails: about5.0021..5.0023V.
-9V protected input,+5V5V,4.7k:4.9628V(-37.2mV); low-input headroom matters even without a4.8V rail.
-Printed op-amp rail7.02..12.62V; last-window excursion<=0.03mV.

Qualification: the wrapper discards raw diagnostic logs and has R6-S8. Finite plausible results do not independently prove every case reached60ms. Three selected corners were additionally rerun with transparent raw capture and final-window validation in TK6-raw-selected.log; **all three reach60ms without abort**:13.4V/4.8V/4.7k=4.9338V,9V/4.8V/4.7k=4.8218V,11.6V/5V/10k=5.0022V. Raw decks and outputs are TK6-raw-{high,low,10k}.{cir,out}. This directly supports the accepted deficit endpoints and a normal10k point; do not extend raw-completion proof to all27cases.

Independent zero-input decks with12V ideal op-amp supply,+5V4.8V,1nF cable and4.7k receiver complete15ms (TK6c-zero-*.out):0.516541V into GND,1.29828V into4.8V. The pull-down floor reproduces the anomaly already documented in carrier.md:222; physical floor UNKNOWN. Pull-up floor is the known low-end sink limitation. These are macromodel predictions, not physical zero-output specifications.

Extended120ms runs with R9/C16 supply,cap starting11.6V or0V,20us maximum timestep abort at5.224us/179.768us. Zeros subsequently printed for115-120ms averages are invalid. The initial parser's PASS in TK6-extra-psa.log is superseded by TK99-zero-regression.log, which rejects both. No physical zero-voltage result follows from those failed analyses; startup-basin independence remains PARTLY.

Attempts: two extra-deck launches missed sim/.spiceinit and failed syntax; corrected cwd to work/sim(psa mode). The next runs exposed numerical aborts. Failed artifacts retained; no component parameters were tuned to manufacture a pass. See TK6-calculations.md for gain, ripple and datasheet accuracy.
