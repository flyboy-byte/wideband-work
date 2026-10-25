#!/bin/sh
# Build the read-only review pack for the current carrier revision (REVIEW.md, review/TASKS.md), plus one zip of it for
# a chat reviewer. Needs the fab candidate: run gen/export_fab.py first.   Run from work/:  sh checks/review_pack.sh [REV]
set -e
REV=${1:-carrier-f}
[ -f out/carrier/carrier-gerbers.zip ] || { echo "no fab candidate: run python3 gen/export_fab.py first"; exit 1; }
[ -f out/module/module-bom.csv ] || python3 gen/module_fab.py
. ./checks/upstream_ref.sh
git diff "$UPSTREAM_REF" -- ../firmware > out/firmware.diff
python3 checks/pack_extras.py ../hardware/board_carrier/board_carrier.kicad_pcb out/carrier
python3 checks/pack_extras.py ../hardware/board_module/wideband_controller.kicad_pcb out/module
DST=audit/$REV-$(date +%F)
[ -d "$DST" ] && chmod -R u+w "$DST" && rm -rf "$DST"   # generated each time; a reviewer's own folder has another name
python3 checks/audit_pack.py "$REV" \
  review/TASKS.md review/FINDINGS-TEMPLATE.md \
  ../hardware/board_carrier/board_carrier.kicad_sch ../hardware/board_carrier/board_carrier.kicad_pcb \
  out/carrier/carrier-gerbers.zip out/carrier/carrier-bom.csv out/carrier/carrier-cpl.csv \
  out/carrier/not-fitted.csv=carrier-not-fitted.csv out/carrier/README.md=carrier-README.md \
  out/carrier-parts.txt=carrier-parts.txt out/carrier-nets.txt=carrier-nets.txt \
  out/module/module-gerbers.zip out/module/module-bom.csv out/module/module-cpl.csv \
  out/module/not-fitted.csv=module-not-fitted.csv out/module/README.md=module-README.md \
  out/module-parts.txt=module-parts.txt out/module-nets.txt=module-nets.txt \
  out/firmware.diff ../firmware/watchdog.h ../firmware/heater_control.cpp \
  docs/carrier.md docs/firmware.md docs/ordering.md docs/wiring.md RELEASE_ASSESSMENT.md ROADMAP.md \
  sim/stability.sh sim/load_accuracy.sh sim/full_scale_corners.sh sim/full_scale_corners.out \
  checks/jlc_rotation.py checks/jlc_rotation.json checks/boot_level.py renders/module/swd-pads.png \
  checks/stack_estimate.py checks/test_stack_estimate.py checks/surge_budget.py checks/test_sim_failures.py \
  sim/completed.sh sim/stability.out
(cd audit && rm -f "$REV-$(date +%F).zip" && zip -qr "$REV-$(date +%F).zip" "$REV-$(date +%F)")
echo "zip for a chat reviewer: $DST.zip ($(du -h "$DST.zip" | cut -f1))"
