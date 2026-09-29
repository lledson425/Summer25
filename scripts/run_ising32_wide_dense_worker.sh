#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
runs=10000
jobs=60
base_seed=420000000
output_root="$repo_root/data/raw/ising32_wide_dense"
binary="$repo_root/src/simulation/on"
template="$repo_root/configs/params_ising32_wide_dense.txt"

while (($#)); do
  case "$1" in
    --runs) runs=$2; shift 2 ;;
    --jobs) jobs=$2; shift 2 ;;
    --base-seed) base_seed=$2; shift 2 ;;
    --output-dir) output_root=$2; shift 2 ;;
    *) echo "Unknown option: $1" >&2; exit 2 ;;
  esac
done

[[ -x "$binary" ]] || make -C "$repo_root/src/simulation" -j 4
[[ -f "$template" ]] || { echo "Missing $template" >&2; exit 1; }
mkdir -p "$output_root"

run_one() {
  local index=$1
  local seed=$((base_seed + index))
  local run_name
  run_name=$(printf 'ising32_wide_dense_%05d' "$index")
  local run_dir="$output_root/$run_name"
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
export base_seed output_root binary template
seq 0 $((runs - 1)) | xargs -r -n 1 -P "$jobs" bash -c 'run_one "$1"' _
echo "All L=32 wide-dense simulations complete."
