#!/usr/bin/env bash
# Full reproducible run. Existing coursework and output folders are preserved.
set -euo pipefail
BUCK_REPO="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
export BUCK_REPO
cd "$BUCK_REPO"
BUCK_RUN_DIR="${1:-artifacts/buck-$(date +%Y%m%dT%H%M%S)}"
if [[ "$BUCK_RUN_DIR" != /* ]]; then BUCK_RUN_DIR="$BUCK_REPO/$BUCK_RUN_DIR"; fi
export BUCK_RUN_DIR
if [[ -e "$BUCK_RUN_DIR" ]]; then
    echo "Output already exists: $BUCK_RUN_DIR" >&2
    exit 1
fi
BUCK_MATLAB="${BUCK_MATLAB:-matlab}"
BUCK_PYTHON="${BUCK_PYTHON:-python}"
BUCK_NGSPICE="${BUCK_NGSPICE:-ngspice}"
BUCK_MATLAB="$(command -v "$BUCK_MATLAB")"
BUCK_PYTHON="$(command -v "$BUCK_PYTHON")"
BUCK_NGSPICE="$(command -v "$BUCK_NGSPICE")"
command -v gcc >/dev/null
mkdir -p "$BUCK_RUN_DIR"
# MATLAB helper processes can inherit stdout after MATLAB itself exits.
# A regular log file avoids waiting forever for those helpers to close a pipe.
if "$BUCK_MATLAB" -batch "addpath(fullfile(getenv('BUCK_REPO'),'project','matlab')); run_buck(fullfile(getenv('BUCK_RUN_DIR'),'matlab')); validate_buck_model(fullfile(getenv('BUCK_RUN_DIR'),'simulink'));" > "$BUCK_RUN_DIR/matlab.log" 2>&1; then
    cat "$BUCK_RUN_DIR/matlab.log"
else
    matlab_status=$?
    cat "$BUCK_RUN_DIR/matlab.log" >&2
    exit "$matlab_status"
fi
"$BUCK_PYTHON" -B project/python/analyze_buck.py --matlab-results "$BUCK_RUN_DIR/matlab" --output "$BUCK_RUN_DIR/simulation" --ngspice "$BUCK_NGSPICE" 2>&1 | tee "$BUCK_RUN_DIR/simulation.log"
"$BUCK_PYTHON" -B -m unittest discover -s project/python -p 'test_*.py' -v 2>&1 | tee "$BUCK_RUN_DIR/python-tests.log"
gcc -std=c11 -Wall -Wextra -Werror -pedantic -fsanitize=address,undefined -g project/hardware/buck_control.c project/hardware/test_buck_control.c -lm -o "$BUCK_RUN_DIR/test_control"
"$BUCK_RUN_DIR/test_control" 2>&1 | tee "$BUCK_RUN_DIR/controller-tests.log"
"$BUCK_PYTHON" -B project/python/build_reports.py --matlab-results "$BUCK_RUN_DIR/matlab" --analysis-results "$BUCK_RUN_DIR/simulation" --output "$BUCK_RUN_DIR/reports" 2>&1 | tee "$BUCK_RUN_DIR/reports.log"
printf 'PASS: complete numerical run at %s\n' "$BUCK_RUN_DIR"
