#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
state_dir="$repo_root/run_state"
pid_file="$state_dir/ising32_wide_dense.pid"
log_file="$state_dir/ising32_wide_dense.log"
mkdir -p "$state_dir"

if [[ -f "$pid_file" ]] && kill -0 "$(cat "$pid_file")" 2>/dev/null; then
  echo "L=32 wide-dense worker already running as PID $(cat "$pid_file")"
  exit 0
fi

nohup setsid "$repo_root/scripts/run_ising32_wide_dense_worker.sh" "$@" \
  >> "$log_file" 2>&1 < /dev/null &
pid=$!
printf '%s\n' "$pid" > "$pid_file"
sleep 1
kill -0 "$pid"
echo "Started L=32 wide-dense simulations as PID $pid"
echo "Log: $log_file"
