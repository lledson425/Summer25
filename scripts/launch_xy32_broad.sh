#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
state_dir="$repo_root/run_state"
pid_file="$state_dir/xy32_broad.pid"
log_file="$state_dir/xy32_broad.log"
mkdir -p "$state_dir"

if [[ -f "$pid_file" ]] && kill -0 "$(cat "$pid_file")" 2>/dev/null; then
  echo "L=32 XY broad-grid worker already running as PID $(cat "$pid_file")"
  exit 0
fi

nohup setsid "$repo_root/scripts/run_xy32_broad_worker.sh" "$@" \
  >> "$log_file" 2>&1 < /dev/null &
pid=$!
printf '%s\n' "$pid" > "$pid_file"
sleep 1
kill -0 "$pid"
echo "Started L=32 XY broad-grid simulations as PID $pid"
echo "Log: $log_file"
