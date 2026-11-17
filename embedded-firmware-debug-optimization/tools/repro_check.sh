#!/usr/bin/env bash
# Copies the sources to a clean directory, regenerates inputs, re-runs tests + benchmark and compares with the stored results.
set -u
SRC="$(cd "$(dirname "$0")/.." && pwd)"
T=$(mktemp -d)
tar --exclude=build --exclude=results --exclude=charts --exclude=report -cf - -C "$SRC" . | tar -xf - -C "$T"
cd "$T" || exit 1
python3 tools/gen_trace.py >/dev/null && python3 tools/gen_lut.py 4 >/dev/null
diff -q common/adc_trace.h "$SRC/common/adc_trace.h" && echo "trace header: identical"
diff -q v3_optimized/thermo_lut.h "$SRC/v3_optimized/thermo_lut.h" && echo "LUT header: identical"
./tools/bench.sh >/dev/null 2>&1
if diff <(cut -d, -f1-13 results/bench.csv) <(cut -d, -f1-13 "$SRC/results/bench.csv"); then echo "benchmark: IDENTICAL to stored results (deterministic)"; else echo "benchmark: DIFFERS"; fi
./tools/run_tests.sh >/dev/null 2>&1
if diff results/test_summary.txt "$SRC/results/test_summary.txt"; then echo "test summary: IDENTICAL to stored results"; else echo "test summary: DIFFERS"; fi
echo "workdir: $T"
