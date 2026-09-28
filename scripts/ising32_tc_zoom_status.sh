#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
pid_file="$repo_root/run_state/ising32_tc_zoom.pid"
log_file="$repo_root/run_state/ising32_tc_zoom.log"
output_root="$repo_root/data/raw/ising32_tc_zoom"

if [[ -f "$pid_file" ]] && kill -0 "$(cat "$pid_file")" 2>/dev/null; then
  echo "RUNNING pid=$(cat "$pid_file")"
else
  echo "NOT RUNNING"
fi

completed=0
if [[ -d "$output_root" ]]; then
  completed=$(find "$output_root" -mindepth 2 -maxdepth 2 -name simulation.log -type f \
    -exec grep -l '\*\*\* END OF SIMULATION \*\*\*' {} + 2>/dev/null | wc -l || true)
fi
printf 'L=32 Tc zoom complete=%s/10000\n' "$completed"
[[ -f "$log_file" ]] && tail -n 20 "$log_file"
