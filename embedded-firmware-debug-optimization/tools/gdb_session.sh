#!/usr/bin/env bash
# GDB-on-QEMU session that catches the ring-buffer corruption (Bug 1) on the emulated Cortex-M3.
cd "$(dirname "$0")/.."
make arm V=v1_buggy OPT=-O0 >/dev/null
(timeout 60 qemu-system-arm -M lm3s6965evb -nographic -semihosting -S -gdb tcp::1234 -kernel build/v1_buggy-O0.elf >/dev/null 2>&1 &)
sleep 1
timeout 40 gdb-multiarch -q -batch -x tools/gdb_ringbuf.gdb build/v1_buggy-O0.elf 2>&1 | grep -v '^warning' | tee results/v1_gdb_session.log
pkill qemu-system-arm || true
