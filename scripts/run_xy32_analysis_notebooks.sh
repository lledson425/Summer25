#!/usr/bin/env bash
set -euo pipefail

repo="/home/lledson/scratch/senior thesis"
notebooks="$repo/notebooks/xy"
jupyter=/home/lledson/.conda/envs/myenv/bin/jupyter
state=/home/lledson/senior-thesis/run_state
mkdir -p "$state"
rm -f "$state/xy32_analysis.complete" "$state/xy32_analysis.failed"
trap 'touch "$state/xy32_analysis.failed"' ERR

for notebook in \
  "$notebooks/xy32_resnet_analysis.ipynb" \
  "$notebooks/xy32_raw_pca_analysis.ipynb" \
  "$notebooks/xy32_representation_comparison.ipynb"
do
  echo "[$(date -Is)] Executing $(basename "$notebook")"
  "$jupyter" nbconvert --to notebook --execute --inplace \
    --ExecutePreprocessor.timeout=-1 \
    --ExecutePreprocessor.kernel_name=python3 \
    "$notebook"
  echo "[$(date -Is)] Completed $(basename "$notebook")"
done

touch "$state/xy32_analysis.complete"
echo "[$(date -Is)] All XY notebooks completed"
