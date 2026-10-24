#!/bin/bash
# Full-scale output with the D3/D4 clamps and the R9/VOP12 supply in the circuit (load_accuracy.sh leaves both out).
# Behavioral op-amp, NOT TI's model: gain 1e5, output limited to V(VOP12) - VDROP (LM2904 high-side drop; 1.5 V
# typical at light load, FROM MEMORY), supply current 0.7 mA (FROM MEMORY) plus whatever it sources.
# 1N4148 model: common vendor parameters (FROM MEMORY). SS54 drop lumped as 0.45 V. DC operating point.
#   ./clamp.sh   -> one line per case
cd "$(dirname "$0")"
run() { # vbat v5 temp load target vdrop
local f; f=$(mktemp --suffix=.cir)
cat > "$f" <<CIR
* clamp
.model D1N4148 D(IS=2.52n RS=0.568 N=1.752 CJO=4p M=0.4 TT=20n)
.temp $3
VB vh 0 {$1-0.45}
R9 vh vop 1k
V5 v5 0 $2
VIN in 0 {$5/1.68}
Bopa oai 0 V = min(max(1e5*(v(in)-v(inn)), 0.0), v(vop)-$6)
Vs oai oa 0
Bsup vop 0 I = 0.7m + max(i(Vs), 0)
R8 oa aout 330
D3 aout d3k D1N4148
VD3 d3k v5 0
D4 0 aout D1N4148
R11 aout conn 470
RL conn 0 $4
RF conn inn 68k
RG inn 0 100k
.control
op
print v(conn) v(oa) v(vop) i(VD3)
.endc
.end
CIR
ngspice -b "$f" 2>/dev/null | awk -v vb=$1 -v v5=$2 -v t=$3 -v rl=$4 -v tg=$5 -v vd=$6 '
 /^v\(conn\)/{c=$3} /^v\(oa\)/{o=$3} /^v\(vop\)/{p=$3} /^i\(vd3\)/{d=$3}
 END{printf "Vbat %5.1f  +5V %.1f  %2d C  drop %.1f  load %-5s  target %.2f V -> J3-5 %.3f V  (op-amp out %.2f V, VOP12 %.2f V, D3 %.2f mA)\n",vb,v5,t,vd,rl,tg,c,o,p,d*1e3}'
rm -f "$f"
}
for t in 25 85; do for v5 in 5.0 4.8; do for vb in 13.8 12.0; do for rl in 4.7k 10k 100k; do run $vb $v5 $t $rl 5.0 1.5; done; done; done; done
