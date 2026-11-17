#!/usr/bin/env bash
# Build every version/optimisation level for Cortex-M3, run in QEMU (deterministic icount), collect size + profile.
cd "$(dirname "$0")/.."
mkdir -p build results
echo "version,opt,text,data,bss,flash_bytes,ram_bytes,acq,filt,conv,alarm,log,total" > results/bench.csv
for v in v2_fixed v3_optimized; do for o in -O0 -O2 -Os; do
  make arm V=$v OPT=$o > build/log_$v$o.txt 2>&1 || { echo "build failed $v $o"; continue; }
  sz=$(arm-none-eabi-size build/$v$o.elf | tail -1)
  text=$(echo $sz | awk '{print $1}'); data=$(echo $sz | awk '{print $2}'); bss=$(echo $sz | awk '{print $3}')
  out=$(timeout 60 qemu-system-arm -M lm3s6965evb -nographic -semihosting -icount shift=6 -kernel build/$v$o.elf 2>/dev/null | tr -d '\r')
  echo "$out" > results/qemu_${v}${o}.log
  p=$(echo "$out" | grep '# prof')
  acq=$(echo $p | sed 's/.*acq=\([0-9]*\).*/\1/'); filt=$(echo $p | sed 's/.*filt=\([0-9]*\).*/\1/')
  conv=$(echo $p | sed 's/.*conv=\([0-9]*\).*/\1/'); alr=$(echo $p | sed 's/.*alarm=\([0-9]*\).*/\1/'); log=$(echo $p | sed 's/.*log=\([0-9]*\).*/\1/')
  tot=$((acq+filt+conv+alr+log))
  echo "$v,$o,$text,$data,$bss,$((text+data)),$((data+bss)),$acq,$filt,$conv,$alr,$log,$tot" >> results/bench.csv
done; done
cat results/bench.csv
