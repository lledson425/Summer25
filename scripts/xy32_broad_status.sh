#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
output_root="$repo_root/data/raw/xy32_broad"
pid_file="$repo_root/run_state/xy32_broad.pid"
log_file="$repo_root/run_state/xy32_broad.log"

pid=""
[[ -f "$pid_file" ]] && pid=$(cat "$pid_file")
if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
  echo "worker=running pid=$pid"
else
  echo "worker=stopped pid=${pid:-unknown}"
fi

dirs=$({ find "$output_root" -mindepth 1 -maxdepth 1 -type d -name 'xy32_broad_*' 2>/dev/null || true; } | wc -l)
complete=$({ grep -l '\*\*\* END OF SIMULATION \*\*\*' "$output_root"/*/simulation.log 2>/dev/null || true; } | wc -l)
spins=$({ find "$output_root" -mindepth 2 -maxdepth 2 -type f -name 'spinConfigs_*.txt' -size +0c 2>/dev/null || true; } | wc -l)
echo "created=$dirs complete=$complete spin_files=$spins target=10000"
du -sh "$output_root" 2>/dev/null || true
tail -10 "$log_file" 2>/dev/null || true
