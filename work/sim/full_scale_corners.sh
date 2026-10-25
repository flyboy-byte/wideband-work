#!/bin/bash
# Full scale (5.0 V wanted) at the connector with the parts load_accuracy.sh leaves out: clamp diodes D3/D4, the op-amp
# supply through R9 (1k) with C16/C17, both LM2904 halves, and the +5V rail at 4.8 / 5.0 / 5.2 V (outside review R1,
# 2026-10-24). TI's LM2904 model (models/, see stability.sh); 1N4148 parameters for D3/D4 (generic, FROM MEMORY).
# The supply is the protected rail after the input Schottky (battery minus about 0.4 V). The zener D5 (18 V) is left out:
# every case is below it. The operating point can't be solved through R9 with this model (Codex's decks failed there,
# 2026-10-24), so the run skips it (uic) with C16 charged to the supply, and the input steps up at 2-6 ms;
# results are averaged over 55-60 ms, after C16 settles (tau 10 ms). One ngspice at a time, only measured nodes saved.
#   ./full_scale_corners.sh      -> one line per case; exit 1 if any case has no valid result
cd "$(dirname "$0")"
. ./completed.sh
[ -f models/lmx58_lm2904.lib ] || { echo "models/lmx58_lm2904.lib missing (TI SNOM268)"; exit 1; }
FAILED=0
num='^-?[0-9]+(\.[0-9]+)?([eE][-+]?[0-9]+)?$'
run() { # supply rail5 load
  local f; f=$(mktemp --suffix=.cir)
  cat > "$f" <<CIR
* full scale corner: supply $1 V, +5V $2 V, load $3
.include models/lmx58_lm2904.lib
VBAT battery 0 $1
R9 battery vcc 1k
C16 vcc 0 10u
C17 vcc 0 100n
V5 five 0 $2
VIN input 0 PWL(0 1 2m 1 6m 2.976190476)
XA input inv vcc 0 oa LMX58_LM2904
XB 0 unused vcc 0 unused LMX58_LM2904
R6 conn inv 68k
R7 inv 0 100k
C15 oa inv 1n
R8 oa clamp 330
R11 clamp conn 470
RL conn 0 $3
CL conn 0 1n
.model d4148 D(Is=2.52n N=1.752 Rs=.568 Cjo=4p)
D3 clamp five d4148
D4 0 clamp d4148
.ic v(vcc)=$1
.save v(conn) v(vcc) i(V5)
.tran 2u 60m 0 5u uic
.control
run
let tend = time[length(time)-1]
echo "END \$&tend"
meas tran vout AVG v(conn) from=55m to=60m
meas tran vcc AVG v(vcc) from=55m to=60m
meas tran i5 AVG i(V5) from=55m to=60m
meas tran vlo MIN v(conn) from=55m to=60m
meas tran vhi MAX v(conn) from=55m to=60m
echo "RES \$&vout \$&vcc \$&i5 \$&vlo \$&vhi"
quit
.endc
.end
CIR
  local out rc r; out=$(timeout 300 nice -n 19 ngspice -b "$f" 2>&1); rc=$?; rm -f "$f"
  completed "$out" 60e-3 || rc="$rc, run incomplete: ended at $(grep -m1 '^END ' <<< "$out" | cut -d' ' -f2) s"
  r=$(grep '^RES' <<< "$out" | head -1 | cut -d' ' -f2-)
  read -r vout vcc i5 vlo vhi <<< "$r"
  for x in "$vout" "$vcc" "$i5" "$vlo" "$vhi"; do
    if [ "$rc" != 0 ] || ! [[ $x =~ $num ]]; then
      printf 'supply %5s V  +5V %s V  load %-5s  FAILED (ngspice exit %s, measurements: %s)\n' "$1" "$2" "$3" "$rc" "${r:-none}"
      FAILED=$((FAILED + 1)); return
    fi
  done
  # i(V5): ngspice's current through the source, positive into its + terminal = D3 pushing current into the +5V rail.
  # Arithmetic in awk: ngspice may print 3.3e-07, which bc can't read
  awk -v s="$1" -v r="$2" -v l="$3" -v v="$vout" -v c="$vcc" -v i="$i5" -v lo="$vlo" -v hi="$vhi" 'BEGIN {
    printf "supply %5s V  +5V %s V  load %-5s  connector %.4f V (%+.0f mV)  op-amp rail %.2f V  D3 into +5V %.2f mA  settled %.2f mV\n",
      s, r, l, v, (v - 5.0) * 1000, c, i * 1000, (hi - lo) * 1000 }'
}
for s in 13.4 11.6 9.0; do for v5 in 4.8 5.0 5.2; do for l in 4.7k 10k 100k; do run $s $v5 $l; done; done; done
[ "$FAILED" -eq 0 ] || { echo "$FAILED case(s) FAILED: no valid result; not a pass"; exit 1; }
