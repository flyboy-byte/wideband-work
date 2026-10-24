#!/bin/bash
# DC accuracy of the output stage into different receiver inputs, TI's LM2904 model (models/, see stability.sh).
# D: DC feedback (68k) taken at the 330R/R11 node, as built r36.  E: taken at the connector, after R11 (R11 inside the loop).
# Loads: pull-downs to GND and pull-ups to 5 V (REPORTED: a Honda ELD input reads about 4.8 V open, so some ECU inputs pull up).
# Fixed 12 V supply, input held at 1.0 V then ramped to the target over 4 ms (a direct .op lands in bogus states with this
# model; the same ramp Codex used). Runs one ngspice at a time and saves only the nodes it measures: saving every node of the
# TI model took about 1 GB per run, and 12 in parallel ran a 14 GB machine out of memory (2026-10-24).
#   ./load_accuracy.sh            -> one line per case: topology, target V, load, V at the connector
cd "$(dirname "$0")"
[ -f models/lmx58_lm2904.lib ] || { echo "models/lmx58_lm2904.lib missing (TI SNOM268)"; exit 1; }
run() { # topology vin load-line
  local f fb=out; f=$(mktemp --suffix=.cir); [ "$1" = E ] && fb=conn
  cat > "$f" <<CIR
.include models/lmx58_lm2904.lib
VCC vcc 0 12
V5 v5 0 5
VIN in 0 PWL(0 1.0 0.5m 1.0 4.5m $2)
XU in inn vcc 0 oa LMX58_LM2904
R3 oa out 330
R11 out conn 470
$3
RG inn 0 100k
RF $fb inn 68k
CF oa inn 1n
.save v(conn)
.tran 1u 6m 0 2u
.control
run
meas tran v AVG v(conn) from=5.5m to=6m
echo "RES \$&v"
quit
.endc
.end
CIR
  local out rc r; out=$(timeout 300 nice -n 19 ngspice -b "$f" 2>&1); rc=$?; rm -f "$f"
  r=$(grep '^RES' <<< "$out" | head -1); r=${r#RES }; r=${r// /}
  if [ $rc -ne 0 ] || ! [[ $r =~ ^-?[0-9]+(\.[0-9]+)?([eE][-+]?[0-9]+)?$ ]]; then
    # ngspice can exit 0 after a failed operating point and print no value (Codex R41-CX2): count it as a failure
    printf '%s  target %.3f V  %-16s -> FAILED (ngspice exit %s, %s)\n' "$1" "$(echo "$2 * 1.68" | bc -l)" "${3#RL }" \
      "$rc" "$(grep -m1 -i 'error\|fail\|singular\|timestep' <<< "$out" || echo 'no measurement')"
    FAILED=$((FAILED + 1)); return
  fi
  printf '%s  target %.3f V  %-16s -> %s V\n' "$1" "$(echo "$2 * 1.68" | bc -l)" "${3#RL }" "$r"
}
FAILED=0
for t in D E; do for v in 0.05952 0.5952 1.4881 2.9762; do
  for l in "RL conn 0 100k" "RL conn 0 10k" "RL conn 0 4.7k" "RL conn v5 47k" "RL conn v5 10k" "RL conn v5 4.7k"; do run $t $v "$l"; done
done; done
[ "$FAILED" -eq 0 ] || { echo "$FAILED case(s) FAILED: no valid result; not a pass"; exit 1; }
