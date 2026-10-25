# Codex second pass, unfinished (2026-10-24)

Codex started a second pass on r41 and ran out of usage credits before writing it up. The files listed below were left
uncommitted in the owner's working tree. Claude committed them unchanged on 2026-10-24, with the owner's go-ahead, so the
evidence is kept. Codex wrote no findings for them; what they show was read and verified by the designer (`AUDIT.md`,
round 4 follow-through):

- `heater_negative_voltage.cpp`, `run_heater_test.py`, `heater-negative-voltage.txt`: a sensor hotter than target
  gets a large heater duty (the negative closed-loop voltage is squared). Verified; fixed by clamping the voltage at 0
  (`firmware/heater_control.cpp`, test `HeaterUpdate.HotterSensorNeverGetsMoreHeat`).
- `retry_*.cir/.log`, `retry_corners.py`, `retry-results.json`: four full-scale corners with the supply fed through R9.
  None converged, because the operating point can't be solved through R9 with TI's model. `sim/full_scale_corners.sh`
  starts with C16 charged (uic) and runs them.
- `render_gerbers.py`, `gerber-*.png/svg`, `gerber-render.json`: both sides rendered from the Gerber zip. Codex
  wrote no observations about them.
