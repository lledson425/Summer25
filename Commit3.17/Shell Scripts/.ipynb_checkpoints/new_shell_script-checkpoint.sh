#!/bin/bash

ITERATIONS=500               # Total runs
MAX_JOBS=31                     # Max parallel jobs
BASE_NAME="test2"
BASE_PARAM="params_${BASE_NAME}.txt"
OUTPUT_DIR="testXY64.2"

mkdir -p "$OUTPUT_DIR"

run_simulation() {
    i=$1
    seed=$((1234 + i))s
    run_name="thread_${i}"
    param_file="params_${run_name}.txt"
    output_file="spinConfigs_${run_name}.txt"

    # Copy and modify param files
    cp "$BASE_PARAM" "$param_file"
    sed -i -E "s/^seed *= *[0-9]+/seed = $seed/" "$param_file"

    # Run simulation
    ./on "$run_name" > /dev/null

    # Save output if exists
    if [[ -f "$output_file" ]]; then
        cp "$output_file" "$OUTPUT_DIR/run${seed}.txt"
    else
        echo "No output for run $i (seed=$seed)"
    fi

    # Optional: cleanup
    rm -f "$param_file" "$output_file"
    rm -f bins_thread_[0-9]*.txt
}

# Main loop with process control
job_count=0
for ((i = 0; i < ITERATIONS; i++)); do
    run_simulation "$i" &

    ((job_count++))
    if (( job_count >= MAX_JOBS )); then
        wait
        job_count=0
    fi
done

# Wait for any remaining jobs
wait

