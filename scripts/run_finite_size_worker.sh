#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
runs=1000
jobs=60
base_seed=20260927
sizes="32 64 128"
output_root="$repo_root/data/raw/finite_size"
binary="$repo_root/src/simulation/on"

while (($#)); do
  case "$1" in
    --runs) runs=$2; shift 2 ;;
    --jobs) jobs=$2; shift 2 ;;
    --base-seed) base_seed=$2; shift 2 ;;
    --sizes) sizes=$2; shift 2 ;;
    --output-dir) output_root=$2; shift 2 ;;
    --binary) binary=$2; shift 2 ;;
    *) echo "Unknown option: $1" >&2; exit 2 ;;
  esac
done

[[ -x "$binary" ]] || make -C "$repo_root/src/simulation" -j 4
mkdir -p "$output_root"

run_one() {
  local task=$1
  local lattice_size=${task%%:*}
  local index=${task##*:}
  local seed=$((base_seed + lattice_size * 1000000 + index))
  local run_name="ising${lattice_size}_tc_${index}"
  local size_root="$output_root/L${lattice_size}"
  local run_dir="$size_root/$run_name"
  local template="$repo_root/configs/params_ising${lattice_size}_tc.txt"
  local param_file="$run_dir/params_${run_name}.txt"
  local log_file="$run_dir/simulation.log"

  if [[ -s "$run_dir/bins_${run_name}.txt" ]] &&
     [[ -s "$run_dir/spinConfigs_${run_name}.txt" ]] &&
     grep -q '\*\*\* END OF SIMULATION \*\*\*' "$log_file" 2>/dev/null; then
    printf 'Already complete: %s\n' "$run_name"
    return 0
  fi

  mkdir -p "$run_dir"
  cp "$template" "$param_file"
  sed -i -E "s/^([[:space:]]*)Seed[[:space:]]*=[[:space:]]*[0-9]+/\1Seed = $seed/" "$param_file"
  (
    cd "$run_dir"
    "$binary" "$run_name" > "$log_file" 2>&1
  )
  printf 'Completed %s (seed=%s)\n' "$run_name" "$seed"
}

export -f run_one
export base_seed output_root repo_root binary

task_file=$(mktemp)
trap 'rm -f "$task_file"' EXIT
for lattice_size in $sizes; do
  [[ -f "$repo_root/configs/params_ising${lattice_size}_tc.txt" ]] || {
    echo "Missing configuration for L=$lattice_size" >&2
    exit 1
  }
  for ((index = 0; index < runs; index++)); do
    printf '%s:%s\n' "$lattice_size" "$index" >> "$task_file"
  done
done

total=$(wc -l < "$task_file")
printf 'Starting %s finite-size runs with %s workers: L={%s}\n' "$total" "$jobs" "$sizes"
xargs -r -n 1 -P "$jobs" bash -c 'run_one "$1"' _ < "$task_file"
printf 'All finite-size simulations complete.\n'
