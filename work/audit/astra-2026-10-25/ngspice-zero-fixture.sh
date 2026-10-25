#!/bin/sh
# Fault injection shaped like the real ngspice-47 early-abort logs retained in TK6c-*.out.
echo 'No. of Data Rows : 499'
echo 'RES 0 0 0 0 0'
echo 'doAnalyses: TRAN: Timestep too small' >&2
echo 'run simulation(s) aborted' >&2
exit 0
