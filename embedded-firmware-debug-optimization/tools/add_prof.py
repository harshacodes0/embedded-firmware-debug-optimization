#!/usr/bin/env python3
"""Append a per-stage profile print-out to each version's main.c (idempotent)."""
import sys
ADD = '''    { static const char *nm[] = {"acq", "filt", "conv", "alarm", "log"};
      hal_uart_puts("# prof");
      for (int k = 0; k < N_STAGE; k++) { hal_uart_puts(" "); hal_uart_puts(nm[k]); hal_uart_puts("="); put_u(g_prof[k]); }
      hal_uart_puts("\\r\\n"); }
    return 0;'''
for p in sys.argv[1:]:
    s = open(p).read()
    if "# prof" in s:
        continue
    s = s.replace("    return 0;", ADD)
    open(p, "w").write(s)
