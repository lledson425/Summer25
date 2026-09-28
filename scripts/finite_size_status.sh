#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
state_dir="$repo_root/run_state"
pid_file="$state_dir/finite_size.pid"
log_file="$state_dir/finite_size.log"

if [[ -f "$pid_file" ]] && kill -0 "$(cat "$pid_file")" 2>/dev/null; then
  echo "RUNNING pid=$(cat "$pid_file")"
else
  echo "NOT RUNNING"
fi

for lattice_size in 32 64 128; do
  size_root="$repo_root/data/raw/finite_size/L${lattice_size}"
  completed=0
  if [[ -d "$size_root" ]]; then
    completed=$(find "$size_root" -mindepth 2 -maxdepth 2 -name simulation.log -type f \
      -exec grep -l '\*\*\* END OF SIMULATION \*\*\*' {} + 2>/dev/null | wc -l || true)
  fi
  printf 'L=%s complete=%s/1000\n' "$lattice_size" "$completed"
done

[[ -f "$log_file" ]] && tail -n 20 "$log_file"
