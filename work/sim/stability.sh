#!/bin/bash
# Small-signal step through the LM2904 output stage, using TI's model (SNOM268, lmx58_lm2904.lib in models/;
# fetched from https://www.ti.com/lit/zip/SNOM268, not committed). Run: ./stability.sh
# Gain 1 + 68k/100k, 330R series, 100k ECU input, cable capacitance Cload on the output.
# A: feedback before the 330R.  B: feedback after it.  C: B plus Cf from op-amp output to IN- (dual loop).
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
RL out 0 100k
CL out 0 $2
RG inn 0 100k
CIR
  case $1 in
    A) echo "RF oa inn 68k" >> "$f" ;;
    B) echo "RF out inn 68k" >> "$f" ;;
    C) printf 'RF out inn 68k\nCF oa inn %s\n' "$3" >> "$f" ;;
  esac
  cat >> "$f" <<'CIR'
.tran 50n 1.2m 0 50n
.control
run
meas tran v0 AVG v(out) from=300u to=395u
meas tran vf AVG v(out) from=1.0m to=1.2m
meas tran vpk MAX v(out) from=400u to=1.2m
meas tran vlo MIN v(out) from=1.0m to=1.2m
meas tran vhi MAX v(out) from=1.0m to=1.2m
let os = 100*(vpk-vf)/(vf-v0)
let late = 1000*(vhi-vlo)
let lo1 = vf - 0.01*(vf-v0)
meas tran t1 WHEN v(out)=$&lo1 RISE=LAST
let ts = 1e6*(t1-400e-6)
echo "RES $&v0 $&vf $&vpk $&os $&late $&ts"
quit
.endc
.end
CIR
  local r; r=$(ngspice -b "$f" 2>/dev/null | grep '^RES' | cut -d' ' -f2-)
  rm -f "$f"
  read -r v0 vf vpk os late ts <<< "$r"
  printf '%s  Cload=%-4s Cf=%-4s  before %.4f V  after %.4f V  peak %.4f V  overshoot %6.1f %%  ripple at end %6.2f mV  settles (1%%) %5.0f us\n' \
    "$1" "$2" "$3" "$v0" "$vf" "$vpk" "$os" "$late" "$ts"
}
for c in 1p 1n 10n 47n; do run A $c -; done
for c in 1p 1n 10n 47n; do run B $c -; done
for cf in 100p 1n; do for c in 1p 1n 10n 47n; do run C $c $cf; done; done
