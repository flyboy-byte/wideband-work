# Sourced by the sim wrappers. completed "$out" STOP: true only if the transient reached STOP seconds and ngspice printed
# no abort message. Each deck prints "END <last time point>" after `run`. ngspice can abort a transient part-way, exit 0
# and still print finite measurements (zeros) for a window it never reached (Codex R6-S8, 2026-10-25), so the exit
# code and "the numbers parse" are not enough.
completed() {
  local end
  end=$(grep -m1 '^END ' <<< "$1" | cut -d' ' -f2)
  grep -qiE 'timestep too small|aborted|fatal error|singular matrix' <<< "$1" && return 1
  [[ $end =~ ^[0-9.]+([eE][-+]?[0-9]+)?$ ]] || return 1
  awk -v e="$end" -v s="$2" 'BEGIN { exit !(e >= s * (1 - 1e-6)) }'
}
