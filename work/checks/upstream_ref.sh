# Sourced by shell checks: UPSTREAM_REF = the ref holding upstream's files (see upstream_ref.py).
UPSTREAM_REF=$(python3 -c 'import sys; sys.path.insert(0, "checks"); from upstream_ref import upstream_ref; print(upstream_ref())')
