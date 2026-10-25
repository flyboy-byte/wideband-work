#!/bin/sh
# Build the read-only review pack for the current carrier revision with the standard file list (REVIEW.md, AUDIT.md
# hand-off). Needs the fab candidate: run gen/export_fab.py first.   Run from work/:  sh checks/review_pack.sh [REV]
set -e
REV=${1:-carrier-f}
[ -f out/carrier/carrier-gerbers.zip ] || { echo "no fab candidate: run python3 gen/export_fab.py first"; exit 1; }
[ -f out/module/module-bom.csv ] || python3 gen/module_fab.py
. ./checks/upstream_ref.sh
git diff "$UPSTREAM_REF" -- ../firmware > out/firmware.diff
python3 checks/audit_pack.py "$REV" \
  ../hardware/board_carrier/board_carrier.kicad_sch ../hardware/board_carrier/board_carrier.kicad_pcb \
  out/carrier/carrier-gerbers.zip out/carrier/carrier-bom.csv out/carrier/carrier-cpl.csv \
  out/carrier/not-fitted.csv out/carrier/README.md out/firmware.diff \
  docs/carrier.md docs/firmware.md RELEASE_ASSESSMENT.md \
  sim/stability.sh sim/load_accuracy.sh sim/full_scale_corners.sh sim/full_scale_corners.out \
  checks/jlc_rotation.py checks/jlc_rotation.json checks/boot_level.py ../firmware/watchdog.h ../firmware/heater_control.cpp \
  out/module/module-bom.csv out/module/module-cpl.csv out/module/not-fitted.csv out/module/README.md \
  docs/ordering.md ROADMAP.md
