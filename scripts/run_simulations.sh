#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
runs=10
jobs=4
base_name="spin"
base_seed=1234
params="$repo_root/configs/params_example.txt"
output_root="$repo_root/data/raw"
binary="$repo_root/src/simulation/on"

usage() {
  cat <<'EOF'
Usage: scripts/run_simulations.sh [options]

Options:
  --runs N          Number of simulations (default: 10)
  --jobs N          Maximum concurrent simulations (default: 4)
  --base-name NAME  Run-name prefix (default: spin)
  --base-seed N     First random seed (default: 1234)
  --params PATH     Parameter template
  --output-dir PATH Output root (default: data/raw)
  --binary PATH     Simulator executable
  -h, --help        Show this help
EOF
}

while (($#)); do
  case "$1" in
    --runs) runs=$2; shift 2 ;;
    --jobs) jobs=$2; shift 2 ;;
    --base-name) base_name=$2; shift 2 ;;
    --base-seed) base_seed=$2; shift 2 ;;
    --params) params=$2; shift 2 ;;
    --output-dir) output_root=$2; shift 2 ;;
    --binary) binary=$2; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
done

[[ -f "$params" ]] || { echo "Parameter template not found: $params" >&2; exit 1; }
[[ -x "$binary" ]] || {
  echo "Simulator not found; building it in src/simulation..."
  make -C "$repo_root/src/simulation"
}

run_one() {
  local index=$1
  local seed=$((base_seed + index))
  local run_name="${base_name}_${index}"
  local run_dir="$output_root/$run_name"
  local param_file="$run_dir/params_${run_name}.txt"

  mkdir -p "$run_dir"
  cp "$params" "$param_file"
  sed -i -E "s/^([[:space:]]*)Seed[[:space:]]*=[[:space:]]*[0-9]+/\1Seed = $seed/" "$param_file"
  (
    cd "$run_dir"
    "$binary" "$run_name" > simulation.log
  )
  printf 'Completed %s (seed=%s)\n' "$run_name" "$seed"
}

export -f run_one
export base_seed base_name output_root params binary
seq 0 $((runs - 1)) | xargs -r -n 1 -P "$jobs" bash -c 'run_one "$1"' _
