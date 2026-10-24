#!/bin/bash
# Small-signal step through the LM2904 output stage, using TI's model (SNOM268, lmx58_lm2904.lib in models/;
# fetched from https://www.ti.com/lit/zip/SNOM268, not committed). Run: ./stability.sh
# Gain 1 + 68k/100k, 330R series, 100k ECU input, cable capacitance Cload on the output.
# A: feedback before the 330R.  B: feedback after it.  C: B plus Cf from op-amp output to IN- (dual loop).
# D: C plus R11 470R in series to the connector, outside the feedback (fault protection, AUDIT O1 / decision D6).
# E: D with the DC feedback taken at the connector, after R11 (as built from r37, C2 build-around); Cf stays 1 nF.
# The load and cable sit on node conn; A-C join it to out through 1 mOhm (no effect).
cd "$(dirname "$0")"
[ -f models/lmx58_lm2904.lib ] || { echo "models/lmx58_lm2904.lib missing (TI SNOM268)"; exit 1; }
run() { # topology cload cf
  local f; f=$(mktemp --suffix=.cir)
  cat > "$f" <<CIR
* stability $1 Cload=$2 Cf=$3
.include models/lmx58_lm2904.lib
VCC vcc 0 12
VIN in 0 PULSE(1.00 1.10 400u 1n 1n 10 20)
XU in inn vcc 0 oa LMX58_LM2904
R3 oa out 330
R11 out conn ${4:-1m}
RL conn 0 100k
CL conn 0 $2
RG inn 0 100k
CIR
  case $1 in
    A) echo "RF oa inn 68k" >> "$f" ;;
    B) echo "RF out inn 68k" >> "$f" ;;
    C|D) printf 'RF out inn 68k\nCF oa inn %s\n' "$3" >> "$f" ;;
    E) printf 'RF conn inn 68k\nCF oa inn %s\n' "$3" >> "$f" ;;
  esac
  cat >> "$f" <<'CIR'
.save v(conn)
.tran 50n 1.2m 0 50n
.control
run
meas tran v0 AVG v(conn) from=300u to=395u
meas tran vf AVG v(conn) from=1.0m to=1.2m
meas tran vpk MAX v(conn) from=400u to=1.2m
meas tran vlo MIN v(conn) from=1.0m to=1.2m
meas tran vhi MAX v(conn) from=1.0m to=1.2m
let os = 100*(vpk-vf)/(vf-v0)
let late = 1000*(vhi-vlo)
let lo1 = vf - 0.01*(vf-v0)
meas tran t1 WHEN v(conn)=$&lo1 RISE=LAST
let ts = 1e6*(t1-400e-6)
echo "RES $&v0 $&vf $&vpk $&os $&late $&ts"
quit
.endc
.end
CIR
  local out rc r; out=$(ngspice -b "$f" 2>&1); rc=$?
  rm -f "$f"
  r=$(grep '^RES' <<< "$out" | head -1 | cut -d' ' -f2-)
  read -r v0 vf vpk os late ts <<< "$r"
  local num='^-?[0-9]+(\.[0-9]+)?([eE][-+]?[0-9]+)?$' x
  # the settling time is a WHEN crossing that may not exist (a stage that never settles into the 1 % band):
  # print it as not found; every voltage must be there
  [[ $ts =~ $num ]] || ts=nan
  for x in "$v0" "$vf" "$vpk" "$os" "$late"; do
    if [ $rc -ne 0 ] || ! [[ $x =~ $num ]]; then
      # a missing measurement used to print as 0 (Codex R41-CX2): report it and fail the sweep
      printf '%s  Cload=%-4s Cf=%-4s  FAILED (ngspice exit %s, measurements: %s)\n' "$1" "$2" "$3" "$rc" "${r:-none}"
      FAILED=$((FAILED + 1)); return
    fi
  done
  printf '%s  Cload=%-4s Cf=%-4s  before %.4f V  after %.4f V  peak %.4f V  overshoot %6.1f %%  ripple at end %6.2f mV  settles (1%%) %5s us\n' \
    "$1" "$2" "$3" "$v0" "$vf" "$vpk" "$os" "$late" "$( [ "$ts" = nan ] && echo 'not found' || printf '%.0f' "$ts")"
}
FAILED=0
for c in 1p 1n 10n 47n; do run A $c -; done
for c in 1p 1n 10n 47n; do run B $c -; done
for cf in 100p 1n; do for c in 1p 1n 10n 47n; do run C $c $cf; done; done
for c in 1p 1n 10n 47n; do run D $c 1n 470; done
for c in 1p 1n 10n 47n 100n; do run E $c 1n 470; done
[ "$FAILED" -eq 0 ] || { echo "$FAILED case(s) FAILED: no valid result; not a pass"; exit 1; }
