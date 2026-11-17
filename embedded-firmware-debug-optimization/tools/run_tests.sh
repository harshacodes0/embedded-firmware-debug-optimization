#!/usr/bin/env bash
# Host-side debugging session: plain run, UBSan, ASan, valgrind, static analysis -- all logs saved in results/
cd "$(dirname "$0")/.."
mkdir -p build results
TESTS="ringbuf_fifo ringbuf_overwrite filter_constant filter_fullscale thermo_fault thermo_accuracy alarm_negative_temp alarm_hysteresis cmd_set_valid cmd_set_garbage cmd_set_range cmd_long_input cmd_get app_trace"
build() { # version outname flags...
  v=$1; out=$2; shift 2
  gcc -std=gnu11 -g -Wall -Wextra "$@" -I$v -Icommon $(ls $v/*.c | grep -v /main.c) common/hal_host.c tests/test_all.c -lm -o build/$out
}
for v in v1_buggy v2_fixed v3_optimized; do
  build $v t_$v -O1 2>results/build_$v.txt
  : > results/tests_$v.log
  for t in $TESTS; do timeout 20 ./build/t_$v $t >> results/tests_$v.log 2>&1 || true; rc=$?; done
done
# per-test outcome table (a crash shows up as a missing PASS/FAIL line)
for v in v1_buggy v2_fixed v3_optimized; do
  echo "== $v"; for t in $TESTS; do
    if grep -q "\[PASS\] $t\$" results/tests_$v.log; then echo "PASS $t"; elif grep -q "\[FAIL\] $t\$" results/tests_$v.log; then echo "FAIL $t"; else echo "CRASH $t"; fi
  done
done > results/test_summary.txt
cat results/test_summary.txt
# --- v1 under UBSan (all checks, report and continue)
build v1_buggy t_v1_ubsan -O1 -fsanitize=undefined,float-cast-overflow -fno-omit-frame-pointer 2>/dev/null
for t in ringbuf_fifo app_trace; do ./build/t_v1_ubsan $t 2>&1 | head -12; done > results/v1_ubsan.log 2>&1
# --- v1 under ASan
build v1_buggy t_v1_asan -O1 -fsanitize=address -fno-omit-frame-pointer 2>/dev/null
for t in cmd_long_input app_trace; do ./build/t_v1_asan $t 2>&1 | head -25; done > results/v1_asan.log 2>&1
# --- v1 under valgrind (uninitialised value)
build v1_buggy t_v1_vg -O0 2>/dev/null
valgrind --track-origins=yes --error-exitcode=9 ./build/t_v1_vg alarm_hysteresis > results/v1_valgrind.log 2>&1
# --- static analysis
gcc -fsyntax-only -Wall -Wextra -O2 -Iv1_buggy -Icommon v1_buggy/*.c > results/v1_gcc_warnings.log 2>&1
cppcheck --enable=warning,style,portability --inconclusive --std=c11 -Iv1_buggy -Icommon v1_buggy/*.c > results/v1_cppcheck.log 2>&1
cppcheck --enable=warning,style,portability --inconclusive --std=c11 -Iv3_optimized -Icommon v3_optimized/*.c > results/v3_cppcheck.log 2>&1
# --- fixed versions under all sanitizers + valgrind
for v in v2_fixed v3_optimized; do
  build $v t_${v}_san -O1 -fsanitize=address,undefined,float-cast-overflow -fno-sanitize-recover=all 2>/dev/null
  ./build/t_${v}_san > results/${v}_sanitizers.log 2>&1; echo "$v sanitizers exit=$?"
  build $v t_${v}_vg -O0 2>/dev/null
  valgrind --error-exitcode=9 --leak-check=full ./build/t_${v}_vg > results/${v}_valgrind.log 2>&1; echo "$v valgrind exit=$?"
done
# --- host timing (x86-64, -O2)
for v in v2_fixed v3_optimized; do build $v t_${v}_bench -O2 2>/dev/null; ./build/t_${v}_bench bench >/dev/null 2> results/host_bench_$v.txt; cat results/host_bench_$v.txt; done
# --- application traces (for charts)
for v in v1_buggy v2_fixed v3_optimized; do build $v t_${v}_csv -O1 2>/dev/null; ./build/t_${v}_csv csv > results/trace_$v.csv 2>/dev/null; done
