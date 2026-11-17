# Embedded firmware: debugging and optimisation (ARM Cortex-M3)

A thermistor temperature monitor written in C, used to practise a complete **debug -> fix -> profile -> optimise -> validate** cycle.
Three versions of the same firmware are kept side by side:

| Folder | What it is |
|---|---|
| `v1_buggy/` | First version with 11 realistic defects (off-by-one, integer overflow, uninitialised variable, signed/unsigned compare, buffer overflows, missing `volatile`, ...) |
| `v2_fixed/` | v1 with only the defects fixed - the performance baseline |
| `v3_optimized/` | v2 + profiling-driven optimisations (lookup table instead of `logf`, O(1) moving average, no `printf`) |

The full write-up (debugging process, defect catalogue, measurements, source listings) is in
[`report/Embedded_Debugging_Optimization_Report.pdf`](report/Embedded_Debugging_Optimization_Report.pdf).

## Results (QEMU Cortex-M3, `-O2`, 512 samples, net of timer overhead)

| | v2 fixed | v3 optimised | change |
|---|---:|---:|---:|
| ticks per sample | 2142 | 132 | **16.2x faster** |
| ADC-to-temperature stage | 1799 | 23 | 77x |
| flash (incl. 1 KiB replay data) | 9784 B | 4544 B | -53.6 % |
| CPU load at 1 kHz sampling | 17.8 % | 1.1 % | |
| unit tests passed | 14 / 14 | 14 / 14 | (v1: 4 / 14) |
| max error vs double-precision model | 0.05 C | 0.10 C | alarm decisions identical |

> **Honesty note:** timings come from QEMU's instruction-level model (deterministic `-icount`), not from silicon. Ratios are meaningful;
> absolute cycle counts need confirming on a board. A ready STM32F103 port (`ports/stm32f103/`, uses the DWT cycle counter) is included and
> **builds**, but has **not been run on hardware yet**.

## Quick start (Ubuntu 24.04)

```bash
sudo apt install gcc-arm-none-eabi qemu-system-arm gdb-multiarch valgrind cppcheck python3-matplotlib python3-reportlab

make arm V=v1_buggy OPT=-O0 && make run V=v1_buggy OPT=-O0     # watch the buggy firmware misbehave (UART log in terminal)
make arm V=v3_optimized OPT=-O2 && make run V=v3_optimized OPT=-O2

./tools/run_tests.sh      # 14 unit tests x 3 versions, UBSan, ASan, valgrind, gcc/cppcheck, host timing -> results/
./tools/bench.sh          # build v2/v3 at -O0/-O2/-Os, run in QEMU, collect size + per-stage ticks -> results/bench.csv
./tools/calib.sh          # QEMU timing calibration
./tools/gdb_session.sh    # GDB attached to QEMU: catches the ring-buffer corruption (Bug 1)
python3 tools/make_charts.py && python3 tools/build_report.py   # regenerate figures + PDF
```

## Layout

```
common/      fw.h (module API), HAL for QEMU and host, Cortex-M3 start-up, linker script, generated ADC trace
v1_buggy/ v2_fixed/ v3_optimized/   ringbuf, filter, thermo, alarm, cmd, app, main
tests/       test_all.c - same 14 tests run against every version
tools/       trace/LUT generators, test + benchmark + GDB scripts, chart and report builders
ports/stm32f103/   HAL + linker script for a real STM32F103C8 ("Blue Pill") board
results/     every log, CSV and metric quoted in the report (generated, committed as evidence)
charts/      figures used in the report
report/      the PDF
```

## Running on real hardware (STM32F103C8)

```bash
make stm32 V=v3_optimized OPT=-O2        # -> build/stm32_v3_optimized-O2.bin
st-flash write build/stm32_v3_optimized-O2.bin 0x8000000
# serial terminal 115200 8N1 on PA9: the last line "# prof acq=.. filt=.. conv=.. alarm=.. log=.." is in real CPU cycles
```

## Known notes
* cppcheck reports one portability note on v3 (`thermo.c`: right shift of a negative value). GCC defines it as an arithmetic shift; the accuracy test passes.
* Bug 10 (sign lost for -0.9..-0.1 deg C) is demonstrated by `results/v1_sign_loss.log`; it never appears in the 1-in-16 UART log.

License: MIT (see `LICENSE`).
