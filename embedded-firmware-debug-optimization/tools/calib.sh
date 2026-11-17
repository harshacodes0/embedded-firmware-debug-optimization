#!/usr/bin/env bash
# Calibrates the QEMU timing model (ticks per instruction, timer-read overhead). Output: results/qemu_calibration.log
cd "$(dirname "$0")/.."; mkdir -p build results
arm-none-eabi-gcc -mcpu=cortex-m3 -mthumb -O1 -Icommon calib/main.c common/startup.c common/hal_qemu.c -T common/lm3s.ld \
  -nostartfiles --specs=nano.specs --specs=nosys.specs -o build/calib.elf || exit 1
timeout 20 qemu-system-arm -M lm3s6965evb -nographic -semihosting -icount shift=6 -kernel build/calib.elf 2>/dev/null | tr -d '\r' | tee results/qemu_calibration.log
