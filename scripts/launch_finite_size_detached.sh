#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
state_dir="$repo_root/run_state"
mkdir -p "$state_dir"
pid_file="$state_dir/finite_size.pid"
log_file="$state_dir/finite_size.log"

if [[ -f "$pid_file" ]]; then
  old_pid=$(cat "$pid_file")
  if kill -0 "$old_pid" 2>/dev/null; then
    echo "Finite-size worker is already running as PID $old_pid"
    exit 0
  fi
fi

nohup setsid "$repo_root/scripts/run_finite_size_worker.sh" "$@" \
  >> "$log_file" 2>&1 < /dev/null &
pid=$!
printf '%s\n' "$pid" > "$pid_file"
sleep 1
if ! kill -0 "$pid" 2>/dev/null; then
  echo "Worker failed to start; inspect $log_file" >&2
  exit 1
fi

echo "Started finite-size simulations as PID $pid"
echo "Log: $log_file"
