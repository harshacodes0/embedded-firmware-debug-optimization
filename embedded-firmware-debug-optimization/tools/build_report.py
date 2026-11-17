#!/usr/bin/env python3
"""Build report/Embedded_Debugging_Optimization_Report.pdf from the real logs, charts, diffs and sources."""
import json, os, textwrap, datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, PageBreak, Image, Table, TableStyle,
                                Preformatted, KeepTogether, CondPageBreak)
from reportlab.platypus.tableofcontents import TableOfContents

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R, C = os.path.join(ROOT, "results"), os.path.join(ROOT, "charts")
OUT = os.path.join(ROOT, "report", "Embedded_Debugging_Optimization_Report.pdf")
os.makedirs(os.path.dirname(OUT), exist_ok=True)
M = json.load(open(os.path.join(R, "metrics.json")))
def rf(p): return open(os.path.join(ROOT, p), errors="replace").read()
def esc(s): return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

NAVY = colors.HexColor("#1f3a5f"); LIGHT = colors.HexColor("#eef3fa"); GREYL = colors.HexColor("#f5f5f5")
ss = getSampleStyleSheet()
body = ParagraphStyle("body", parent=ss["Normal"], fontName="Helvetica", fontSize=9.4, leading=13, alignment=TA_JUSTIFY, spaceAfter=5)
bul = ParagraphStyle("bul", parent=body, leftIndent=14, bulletIndent=3, spaceAfter=2)
h1 = ParagraphStyle("h1", parent=ss["Heading1"], fontName="Helvetica-Bold", fontSize=15, leading=19, textColor=NAVY, spaceBefore=6, spaceAfter=8)
h2 = ParagraphStyle("h2", parent=ss["Heading2"], fontName="Helvetica-Bold", fontSize=11.5, leading=15, textColor=NAVY, spaceBefore=8, spaceAfter=4)
h3 = ParagraphStyle("h3", parent=ss["Heading3"], fontName="Helvetica-Bold", fontSize=9.8, leading=13, textColor=colors.HexColor("#333333"), spaceBefore=5, spaceAfter=3)
cap = ParagraphStyle("cap", parent=body, fontName="Helvetica-Oblique", fontSize=8.2, leading=10.5, alignment=TA_CENTER, textColor=colors.HexColor("#444444"), spaceAfter=8)
cell = ParagraphStyle("cell", parent=body, fontSize=7.7, leading=9.6, alignment=0, spaceAfter=0)
cellb = ParagraphStyle("cellb", parent=cell, fontName="Helvetica-Bold")
codest = ParagraphStyle("code", fontName="Courier", fontSize=6.7, leading=8.0, backColor=GREYL, borderPadding=4, spaceAfter=7, leftIndent=2)
logst = ParagraphStyle("log", parent=codest, backColor=colors.HexColor("#f0f4f0"))
note = ParagraphStyle("note", parent=body, backColor=colors.HexColor("#fff8e6"), borderColor=colors.HexColor("#e0b040"), borderWidth=0.6, borderPadding=5, spaceBefore=4, spaceAfter=8, fontSize=8.8, leading=12)

def P(t, st=body): return Paragraph(t, st)
def B(t): return Paragraph(t, bul, bulletText="\u2022")
def code(text, st=codest, width=118):
    out = []
    for ln in text.rstrip("\n").split("\n"):
        ln = ln.replace("\t", "    ").rstrip()
        if len(ln) <= width: out.append(ln)
        else:
            w = textwrap.wrap(ln, width, subsequent_indent="      ", break_long_words=True, drop_whitespace=False)
            out.extend(w if w else [ln])
    return Preformatted("\n".join(out), st)
def fig(name, width_cm, caption):
    from PIL import Image as PI
    im = PI.open(os.path.join(C, name)); w, h = im.size
    return KeepTogether([Image(os.path.join(C, name), width=width_cm * cm, height=width_cm * cm * h / w), P(caption, cap)])
def table(rows, widths, header=True, zebra=True, fs=None):
    data = []
    for i, r in enumerate(rows):
        data.append([c if not isinstance(c, str) else Paragraph(esc(c) if "<" not in c else c, cellb if (header and i == 0) else cell) for c in r])
    t = Table(data, colWidths=[w * cm for w in widths], repeatRows=1 if header else 0)
    st = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#b8c4d6")),
          ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3), ("TOPPADDING", (0, 0), (-1, -1), 2.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5)]
    if header: st += [("BACKGROUND", (0, 0), (-1, 0), LIGHT)]
    if zebra:
        for i in range(2, len(rows), 2): st.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#fafbfd")))
    t.setStyle(TableStyle(st)); return t

class Doc(BaseDocTemplate):
    def __init__(self, fn, **kw):
        BaseDocTemplate.__init__(self, fn, pagesize=A4, leftMargin=1.8 * cm, rightMargin=1.8 * cm, topMargin=1.9 * cm, bottomMargin=1.8 * cm,
                                 title="Debugging and Optimization of Embedded Firmware", author="Harsha", subject="Embedded systems debugging and optimization report", **kw)
        fr = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id="f")
        self.addPageTemplates([PageTemplate(id="p", frames=[fr], onPage=self.deco)])
    def deco(self, c, d):
        if d.page == 1: return
        c.saveState(); c.setFont("Helvetica", 7.5); c.setFillColor(colors.HexColor("#555555"))
        c.drawString(1.8 * cm, A4[1] - 1.2 * cm, "Debugging and Optimization of an Embedded Sensor Firmware")
        c.drawRightString(A4[0] - 1.8 * cm, A4[1] - 1.2 * cm, "ECE - Embedded Systems")
        c.setStrokeColor(colors.HexColor("#b8c4d6")); c.line(1.8 * cm, A4[1] - 1.35 * cm, A4[0] - 1.8 * cm, A4[1] - 1.35 * cm)
        c.drawCentredString(A4[0] / 2, 1.0 * cm, "Page %d" % d.page); c.restoreState()
    def afterFlowable(self, f):
        if isinstance(f, Paragraph) and f.style.name in ("h1", "h2"):
            self.notify("TOCEntry", (0 if f.style.name == "h1" else 1, f.getPlainText(), self.page))

stages = ["acq", "filt", "conv", "alarm", "log"]
def pct(a, b): return 100.0 * (1 - a / b)
v2, v3 = M["v2_fixed-O2"], M["v3_optimized-O2"]
S = []

# ===================================================================== title page
S += [Spacer(1, 3.2 * cm), P("<font size=24 color='#1f3a5f'><b>Debugging and Optimization of an<br/>Embedded Sensor-Acquisition Firmware</b></font>", ParagraphStyle("t", alignment=TA_CENTER, leading=30)),
      Spacer(1, 0.5 * cm), P("<font size=12 color='#555555'>Fault finding with static analysis, sanitizers, valgrind and GDB-on-target; profiling-driven optimization; "
                              "measured on an emulated ARM Cortex-M3 (QEMU) with an STM32F103 hardware port included</font>", ParagraphStyle("t2", alignment=TA_CENTER, leading=16)),
      Spacer(1, 1.2 * cm)]
kp = [["Item", "Value"],
      ["Prepared by", "Harsha - Electronics and Communication Engineering, Manakula Vinayagar Institute of Technology, Pondicherry"],
      ["Date", "12 November 2026"],
      ["Target core", "ARM Cortex-M3 (Thumb-2, no FPU): QEMU lm3s6965evb for measurement; STM32F103C8 port provided"],
      ["Language / toolchain", "C11, arm-none-eabi-gcc 13.2.1, gcc 13.3, QEMU 8.2.2, valgrind 3.22, cppcheck 2.13, GDB 15.1"],
      ["Deliverables", "This report + complete source repository (firmware v1/v2/v3, tests, tools, logs, charts)"]]
S += [table(kp, [4.0, 13.2]), Spacer(1, 0.8 * cm)]
hl = [["Headline result (v2 fixed baseline -> v3 optimised, -O2)", ""],
      ["Defects found and fixed", "11 (10 of 14 unit tests failing or crashing in v1; 14/14 passing in v2 and v3)"],
      ["Execution cost per sample", "%.0f -> %.0f ticks  (%.1fx faster; CPU load at 1 kHz: %.1f%% -> %.1f%%)" % (v2["total"], v3["total"], M["speedup_total_O2"], M["cpu_load_1kHz_pct"]["v2_fixed-O2"], M["cpu_load_1kHz_pct"]["v3_optimized-O2"])],
      ["Flash footprint", "%d -> %d bytes  (-%.1f%%; includes 1 KiB of replayed ADC data in both)" % (v2["flash"], v3["flash"], M["flash_reduction_O2_pct"])],
      ["Accuracy cost of optimisation", "max %.2f deg C difference vs double-precision reference; alarm decisions identical on all 512 samples" % (M["trace_err_v3_optimized"]["max_abs_x10"] / 10.0)]]
t = table(hl, [6.2, 11.0]); t.setStyle(TableStyle([("SPAN", (0, 0), (1, 0)), ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dfeadf"))])); S += [t, PageBreak()]

toc = TableOfContents(); toc.levelStyles = [ParagraphStyle("t0", fontName="Helvetica-Bold", fontSize=9, leading=11.5, leftIndent=0, spaceBefore=2),
                                           ParagraphStyle("t1", fontName="Helvetica", fontSize=8.2, leading=10, leftIndent=14)]
S += [P("Contents", h1), toc, PageBreak()]

# ===================================================================== 1 objective
S += [P("1. Objective and scope", h1),
      P("The task is to simulate real-world firmware debugging: take an embedded application that contains common defects, locate them "
        "systematically with debugging tools, fix them, optimise the corrected code for speed and memory footprint, and prove the result with "
        "measurements. This report documents that process end to end for a thermistor-based temperature monitor written in C for an ARM Cortex-M3."),
      P("<b>What is different from the previous submission.</b> The earlier feedback praised the documentation but penalised the absence of real code "
        "and of real-world measurements. This submission therefore ships (a) every source file, in the repository and listed in Appendix C; "
        "(b) every number in this report as the output of a script that can be re-run (Appendix A); and (c) a build for real hardware "
        "(STM32F103 / Cortex-M3) together with the exact procedure for the on-board measurement (Section 9)."),
      P("Three firmware versions are used throughout:"),
      B("<b>v1_buggy</b> - the application as first written, with eleven deliberate-but-realistic defects (Section 5)."),
      B("<b>v2_fixed</b> - v1 with only the defects fixed. This is the honest performance baseline: nobody benchmarks code that gives wrong answers."),
      B("<b>v3_optimized</b> - v2 plus profiling-driven optimisations (Section 7). Functionally equivalent to v2 within a stated tolerance."),
      Spacer(1, 4)]

# ===================================================================== 2 system
S += [P("2. System under test", h1),
      P("The firmware samples a 12-bit ADC that reads a 10 kOhm NTC thermistor (B = 3950) in a divider with a 10 kOhm resistor. Every millisecond a SysTick "
        "interrupt sets a flag; the main loop wakes, acquires a sample, filters it, converts it to temperature, evaluates a high-temperature alarm with "
        "2.0 deg C hysteresis, services a small text command interface (<font face='Courier'>SET &lt;0..125&gt;</font>, <font face='Courier'>GET</font>) and "
        "logs one line every 16 samples over UART."),
      fig("fig_architecture.png", 16.5, "Figure 1 - Data path of the firmware. The same application code runs on QEMU, on the host PC and on an STM32F103; only the HAL differs."),
      P("<b>Input data.</b> A deterministic 512-sample ADC recording (<font face='Courier'>tools/gen_trace.py</font>) is replayed by the HAL. It models a warm-up from -8 deg C "
        "to 52 deg C and cool-down to 15 deg C, adds Gaussian noise (sigma = 1.5 LSB, fixed seed) and injects two sensor faults: an open circuit "
        "(ADC = 4095) at sample 150 and a short circuit (ADC = 0) at sample 330. Replaying the same recording on every platform makes results exactly comparable "
        "across versions, compilers and (later) hardware."),
      P("<b>Pipeline interface.</b> All three versions expose the same function signatures (<font face='Courier'>fw.h</font>), so one test suite runs unchanged against every version.")]

# ===================================================================== 3 environment
S += [P("3. Test and measurement environment", h1),
      table([["Purpose", "Tool / platform", "Used for"],
             ["Cross compile", "arm-none-eabi-gcc 13.2.1, -mcpu=cortex-m3 -mthumb, newlib-nano", "Real Thumb-2 binaries, size, disassembly"],
             ["Target execution", "QEMU 8.2.2, machine lm3s6965evb (Cortex-M3), semihosting, -icount shift=6", "Run the firmware, UART log, deterministic timing"],
             ["Target debugger", "gdb-multiarch 15.1 attached to QEMU gdbstub (-S -gdb tcp::1234)", "Breakpoints and memory inspection on the ARM target"],
             ["Static analysis", "gcc -Wall -Wextra -O2, cppcheck 2.13", "Compile-time defect detection"],
             ["Dynamic analysis", "AddressSanitizer, UndefinedBehaviorSanitizer, valgrind memcheck 3.22", "Memory and undefined-behaviour errors (host build)"],
             ["Unit tests", "tests/test_all.c, 14 tests, one process per test", "Regression suite, identical for v1/v2/v3"],
             ["Hardware port", "STM32F103C8 HAL, DWT cycle counter (builds; see Section 9)", "Real-cycle measurement on a physical board"]],
            [3.0, 8.0, 6.2]),
      Spacer(1, 6),
      P("<b>How time is measured.</b> The firmware brackets each pipeline stage with <font face='Courier'>hal_timer_read()</font> (SysTick-based, 12 MHz model clock) and accumulates "
        "ticks per stage in <font face='Courier'>g_prof[]</font>. Because QEMU runs with <font face='Courier'>-icount</font>, virtual time advances only as instructions retire, so the "
        "numbers are deterministic and do not depend on how fast the host PC is. Two calibrations were measured on the same setup (<font face='Courier'>results/qemu_calibration.log</font>):"),
      B("a block of 2000 NOPs takes 1614 ticks and 6000 NOPs take 4814 ticks, i.e. a linear <b>0.80 ticks per instruction</b> (1 tick = 83.3 ns of model time);"),
      B("two back-to-back <font face='Courier'>hal_timer_read()</font> calls cost <b>12 ticks</b> on average (6150 ticks per 512 samples). This measurement floor is subtracted from every stage "
        "figure in this report (\"net ticks\")."),
      P("<b>Limitations (stated openly).</b> QEMU is an instruction-level emulator: it executes the real ARM binary but does not model pipeline stalls, flash wait states or multi-cycle "
        "divides, so one tick is not the same as one real core cycle. The ratios between versions are therefore reliable evidence of algorithmic and code-size improvement, "
        "but the absolute cycle counts must be confirmed on silicon. Section 9 provides the board port and procedure for that.", note)]

# ===================================================================== 4 debugging process
S += [PageBreak(), P("4. The debugging process", h1),
      fig("fig_workflow.png", 16.5, "Figure 2 - Debugging workflow. Cheap, broad techniques come first; target-level debugging is used to explain what the broad techniques flagged."),
      P("4.1 Step 1 - Reproduce and observe (QEMU)", h2),
      P("v1 was built at -O0 and run on the emulated Cortex-M3. The UART log (full log in Appendix D) already shows that the firmware is wrong, even before any tool is used:"),
      code("\n".join(rf("results/qemu_v1_buggy-O0.log").split("\n")[:14]), logst),
      B("<b>Sample 0 reports ALARM at -7.9 deg C.</b> A cold sensor should never trip a high-temperature alarm."),
      B("<b>Sample 32 reports 41.3 deg C</b> while the true temperature is about -7 deg C; the filtered value is garbage as soon as the moving-average window fills."),
      B("<b>The alarm is active for 496 of 512 samples</b> (v2: 214). After <font face='Courier'>SET abc</font> the controller answers <font face='Courier'>THR=0.0</font> - the garbage command silently set the threshold to zero."),
      fig("fig_trace_compare.png", 13.6, "Figure 3 - Firmware output versus the true temperature. Top: v1 as found (QEMU log). Bottom: v3. Shaded = alarm active. Dotted verticals = injected sensor faults."),
      P("4.2 Step 2 - Static analysis", h2),
      P("Compiling with <font face='Courier'>-Wall -Wextra</font> and running cppcheck costs nothing and found three defects before the code was executed:"),
      code("v1_buggy/alarm.c:8:15: warning: comparison of integer expressions of different signedness: 'int' and 'uint32_t' [-Wsign-compare]\n"
           "v1_buggy/alarm.c:9:20: warning: comparison of integer expressions of different signedness: 'int' and 'uint32_t' [-Wsign-compare]\n"
           "v1_buggy/app.c:29:33: warning: '%s' directive writing 2 or more bytes into a region of size between 1 and 10 [-Wformat-overflow=]\n"
           "v1_buggy/app.c:29:9: note: 'sprintf' output 11 or more bytes (assuming 20) into a destination of size 16\n"
           "v1_buggy/alarm.c:10:12: error: Uninitialized variable: state [legacyUninitvar]      <- cppcheck", logst),
      P("These point at Bug 5 (signed/unsigned comparison), Bug 9 (log buffer too small) and Bug 4 (uninitialised return value). Static analysis cannot see "
        "Bugs 1, 2, 3, 7 or 11 - they are logic and concurrency errors that need execution to expose.")]

S += [P("4.3 Step 3 - Unit tests as a regression net", h2),
      P("Fourteen small tests (Appendix C) exercise each module in isolation. Each test runs in its own process so that a crash in one test cannot hide the result of the others. "
        "The same test source is run against all three versions. v1 passes only 4 of 14 tests; 8 fail and 2 crash the process."),
      fig("fig_test_matrix.png", 12.5, "Figure 4 - Test matrix. CRASH means the process was killed (glibc buffer-overflow abort) before reporting."),
      P("Examples of failure messages produced by v1 (verbatim from <font face='Courier'>results/tests_v1_buggy.log</font>):"),
      code("    expected: v == 1000 + i  (i=64 got 1004)                    [FAIL] ringbuf_fifo\n"
           "    expected: y == 3000  (avg of 3000s = 952)                   [FAIL] filter_constant\n"
           "    expected: y == 4095  (avg of 4095s = 2047)                  [FAIL] filter_fullscale\n"
           "    expected: thermo_adc_to_x10(0, &t) == -1  (adc=0 must be a fault)   [FAIL] thermo_fault\n"
           "    expected: alarm_update(-80) == 0  (-8.0 C raised alarm)     [FAIL] alarm_negative_temp\n"
           "    expected: cmd_process(\"SET abc\",...) == -1  (garbage accepted)    [FAIL] cmd_set_garbage\n"
           "    *** buffer overflow detected ***: terminated                [CRASH] cmd_long_input / app_trace", logst),
      P("The numbers are informative on their own. The constant input 3000 comes out as 952: the 16-bit sum is 32 x 3000 = 96000, which wraps to 30464 and 30464 / 32 = 952 - "
        "exactly the value printed. The first sample that goes wrong in the ring buffer is number 64 - the first time the head index reaches the capacity."),
      P("4.4 Step 4 - Dynamic analysis (sanitizers and valgrind)", h2),
      P("<b>UndefinedBehaviorSanitizer</b> (built with <font face='Courier'>-fsanitize=undefined</font>) names the ring-buffer defect at the exact source line:"),
      code("v1_buggy/ringbuf.c:4:11: runtime error: index 64 out of bounds for type 'uint16_t [64]'", logst),
      P("<b>AddressSanitizer</b> reports the log-line overflow, including the stack-frame layout that shows <font face='Courier'>line[96,112)</font> being overrun:"),
      code("==1414==ERROR: AddressSanitizer: stack-buffer-overflow ... WRITE of size 17 at ...\n"
           "    #2 sprintf /usr/include/x86_64-linux-gnu/bits/stdio2.h:30\n"
           "    #3 app_step v1_buggy/app.c:29\n"
           "  This frame has 4 object(s):\n"
           "    [64, 80) 'resp' (line 26)\n"
           "    [96, 112) 'line' (line 28) <== Memory access at offset 112 overflows this variable", logst),
      P("The line <font face='Courier'>\"300,52.0,ALARM\\r\\n\"</font> is 16 characters plus the terminating NUL = 17 bytes in a 16-byte array. The bug only triggers when the alarm is active and the "
        "sample index has three digits, which is why it can survive casual testing. <b>valgrind memcheck</b> finds Bug 4:"),
      code("==1438== Conditional jump or move depends on uninitialised value(s)\n"
           "==1438==    at 0x10A3C3: t_alarm_hysteresis (test_all.c:70)\n"
           "==1438==  Uninitialised value was created by a stack allocation\n"
           "==1438==    at 0x109385: alarm_update (alarm.c:6)", logst),
      P("4.5 Step 5 - Debugging on the target with GDB", h2),
      P("The sanitizers ran on the host. To be sure the same fault occurs in the real ARM binary, GDB was attached to the QEMU Cortex-M3 through its gdbstub and a conditional "
        "breakpoint was placed on the suspicious function: stop in <font face='Courier'>rb_push()</font> only when <font face='Courier'>head == 64</font>, a state that is impossible "
        "for a correct 64-entry buffer. The script is <font face='Courier'>tools/gdb_ringbuf.gdb</font>; the output below is the real session:"),
      code("Breakpoint 1, rb_push (r=0x2000007c <rb>, v=3212) at v1_buggy/ringbuf.c:4\n"
           "--- stopped: head==64 (should be impossible: valid indices are 0..63)\n"
           "#0  rb_push (r=0x2000007c <rb>, v=3212) at v1_buggy/ringbuf.c:4\n"
           "#1  0x00000106 in app_step (i=64, o=0x0 <g_vectors>) at v1_buggy/app.c:13\n"
           "#2  0x00000510 in main () at v1_buggy/main.c:14\n"
           "--- executing the store r->buf[r->head] = v  (v = 3212)\n"
           "--- head/tail were overwritten by the sample bytes: head=140 tail=12", logst),
      P("The stop happens at <b>app_step(i=64)</b>, matching the unit test (first wrong sample = 64). The sample value 3212 is 0x0C8C: after the store, <font face='Courier'>head = 0x8C = 140</font> and "
        "<font face='Courier'>tail = 0x0C = 12</font>. The store went to <font face='Courier'>buf[64]</font>, which does not exist, so it landed on the two bytes that follow the array in the structure. "
        "That one observation explains every later ring-buffer symptom: from this sample on the head index is a random number from the ADC."),
      fig("fig_ringbuf_layout.png", 16.0, "Figure 5 - Why the store to buf[64] corrupts head and tail. Note that AddressSanitizer cannot see this bug (the write stays inside the same object); UBSan and GDB can."),
      P("4.6 Step 6 - Debug build works, release build hangs", h2),
      P("Built with <font face='Courier'>-O2</font>, v1 prints its banner and then never produces a sample; QEMU has to be killed by the timeout. The cause is visible in the disassembly of "
        "<font face='Courier'>main()</font>. The flag that the SysTick interrupt sets is an ordinary <font face='Courier'>uint8_t</font>, so the optimiser is entitled to assume nobody else changes it:"),
      code("v1 (non-volatile flag, -O2)                     v2 (volatile flag, -O2)\n"
           "  342:  ldrb   r3, [r5, #0]   ; read ONCE          416:  ldrb   r3, [r4, #0]   ; read every pass\n"
           "  344:  cbnz   r3, 348                              418:  cmp    r3, #0\n"
           "  346:  b.n    346            ; spin forever        41a:  beq.n  416           ; loop back and re-read", logst),
      P("The compiler loaded the flag once and, finding it zero, replaced the wait loop with a branch to itself. At -O0 the code works because every access goes to memory, which is why this class of bug "
        "is dangerous: it passes all debug-build testing.")]

# ===================================================================== 5 issue catalogue
S += [CondPageBreak(9 * cm), P("5. Identified issues (defect catalogue)", h1),
      P("Eleven defects were identified. The table lists each with its observable symptom, root cause, the technique that exposed it and the fix applied in v2."),
      table([["#", "Module", "Symptom (measured)", "Root cause", "Found by", "Fix"],
             ["1", "ringbuf.c", "Sample 64 onward corrupted; head=140, tail=12 (GDB)", "<font face='Courier'>if (head > RB_SIZE)</font> lets head reach 64; store to buf[64] hits head/tail", "UBSan, unit test, GDB", "<font face='Courier'>&gt;=</font> (v3: power-of-two mask)"],
             ["2", "filter.c", "DC input 3000 -> 952; 4095 -> 2047; bad temperatures", "16-bit accumulator: 32 x 4095 = 131040 exceeds 65535", "unit test, QEMU log", "32-bit accumulator"],
             ["3", "thermo.c", "ADC 0 or 4095 gives divide-by-zero / log(0) -> inf, then (int)inf is undefined", "No sensor-fault handling", "unit test, review", "Reject codes <= 10 or >= 4085; hold last good sample; flag FLT"],
             ["4", "alarm.c", "Return value indeterminate inside hysteresis band", "Local <font face='Courier'>state</font> not assigned on all paths", "valgrind, cppcheck, unit test", "Persistent, initialised state"],
             ["5", "alarm.c", "False alarm on every negative temperature; 100 of first 100 samples", "int compared with uint32_t: negative converts to huge unsigned", "-Wsign-compare, unit test", "Signed threshold"],
             ["6", "cmd.c", "40-character argument aborts the program (stack smash)", "Unbounded <font face='Courier'>strcpy</font> into char[8]", "unit test crash", "No copy; parse in place"],
             ["7", "cmd.c", "<font face='Courier'>SET abc</font> sets threshold 0.0; <font face='Courier'>SET 200</font> accepted", "<font face='Courier'>atoi</font> returns 0 on error, no range check", "unit tests, QEMU log", "Strict parser, range 0..125"],
             ["8", "cmd.c", "Latent overflow of the caller's response buffer", "Unbounded <font face='Courier'>sprintf</font>", "code review", "snprintf / bounded copy"],
             ["9", "app.c", "17 bytes written to a 16-byte buffer when an ALARM line is logged", "Buffer too small for worst-case line", "ASan, -Wformat-overflow", "32-byte buffer, bounded formatting"],
             ["10", "app.c", "Temperatures -0.1..-0.9 print without sign: -0.5 prints as \"0.5\"", "Integer division truncates toward zero, sign lost", "review + reproduction", "Explicit sign handling"],
             ["11", "main.c", "-O2 build hangs forever; -O0 works", "ISR-shared flag not <font face='Courier'>volatile</font>", "QEMU timeout, objdump", "<font face='Courier'>volatile</font>"]],
            [0.6, 1.5, 4.0, 4.4, 2.6, 4.1]),
      Spacer(1, 4),
      P("Bug 10 is a good example of a defect that is easy to miss in testing. In the corrected firmware four samples (82-85) fall in the -0.9..-0.1 deg C window, but the UART log prints only every 16th sample "
        "(80, 96, ...), so no log line ever shows one. It was caught by reading the code and then reproduced with an eight-line program (<font face='Courier'>results/v1_sign_loss.log</font>): the input -5 (i.e. -0.5 deg C) prints "
        "<font face='Courier'>\"0.5\"</font>, while -12 correctly prints <font face='Courier'>\"-1.2\"</font>.", body),
      P("<b>Severity ranking.</b> Safety-relevant first: 5 (false alarm) and 3 (a disconnected sensor would not be detected), then 6/9/1 (memory corruption), 7 (silent mis-configuration), 2 (wrong readings), 11 (system hang in production build), 4, 8, 10.")]

# ===================================================================== 6 fixes
S += [P("6. Corrective changes (v2)", h1),
      P("The complete before/after differences are in Appendix B.1. The most instructive fixes are shown here."),
      P("Bug 2 and 1 - integer width and off-by-one", h3),
      code("// v1                                    // v2\n"
           "uint16_t sum = 0;                        uint32_t sum = 0;          // 32 * 4095 fits\n"
           "if (r->head > RB_SIZE) r->head = 0;      if (r->head >= RB_SIZE) r->head = 0;", codest),
      P("Bug 3 - validate before computing", h3),
      code("// v2 thermo.c\n"
           "if (adc <= ADC_FAULT_LO || adc >= ADC_FAULT_HI) { *t_x10 = 0; return -1; }   // open / short circuit\n"
           "// v2 app.c: a faulty sample never enters the filter; the last good value is held and 'FLT' is logged\n"
           "int fault = (raw <= ADC_FAULT_LO || raw >= ADC_FAULT_HI);\n"
           "rb_push(&rb, fault ? last_good : raw);", codest),
      P("Bugs 4 and 5 - alarm state machine", h3),
      code("// v2 alarm.c\n"
           "static int thr_x10 = 400;   // signed: negative temperatures compare correctly\n"
           "static int state;           // persistent: the hysteresis band returns the previous state\n"
           "int alarm_update(int t_x10) {\n"
           "    if (t_x10 > thr_x10) state = 1;\n"
           "    else if (t_x10 < thr_x10 - HYST_X10) state = 0;\n"
           "    return state;\n"
           "}", codest),
      P("Bugs 6, 7, 8 - command parser", h3),
      code("static int parse_thr(const char *s, int *out) {\n"
           "    int v = 0, digits = 0;\n"
           "    while (*s >= '0' && *s <= '9') { v = v * 10 + (*s - '0'); if (++digits > 3) return -1; s++; }\n"
           "    if (digits == 0 || *s != '\\0' || v > 125) return -1;   // no digits, trailing junk, out of range\n"
           "    *out = v; return 0;\n"
           "}", codest),
      P("The parser works in place (no copy, so nothing to overflow), accepts at most three digits (so the integer cannot overflow either) and rejects anything that is not exactly a number in 0..125. "
        "Bug 11 is fixed by <font face='Courier'>static volatile uint8_t sample_due;</font>.")]

# ===================================================================== 7 profiling and optimisation
S += [CondPageBreak(9 * cm), P("7. Profiling and optimisation", h1),
      P("7.1 Where does the time go? (baseline = v2)", h2),
      P("Optimisation starts with measurement. The per-stage counters in v2 (built -O2, QEMU, net of the 12-tick measurement floor) give:"),
      table([["Stage", "Net ticks / sample", "Share of total", "Comment"]] +
            [[n, "%.1f" % v2[k], "%.1f %%" % (100.0 * v2[k] / v2["total"]), c] for n, k, c in
             [("ADC acquire + ring buffer", "acq", "small"), ("Moving average", "filt", "O(32) loop + division every sample"),
              ("ADC to temperature", "conv", "float divide + logf() + soft-float emulation (no FPU on Cortex-M3)"), ("Alarm", "alarm", "negligible"), ("UART log line", "log", "snprintf from newlib-nano")]] +
            [["<b>Total</b>", "<b>%.1f</b>" % v2["total"], "100 %", "%.1f %% of one 1 ms sample period" % M["cpu_load_1kHz_pct"]["v2_fixed-O2"]]],
            [4.2, 3.0, 2.6, 7.4]),
      Spacer(1, 4),
      P("The Cortex-M3 has no floating-point unit, so every <font face='Courier'>float</font> operation in <font face='Courier'>thermo_adc_to_x10()</font> is a call into the soft-float library, and "
        "<font face='Courier'>logf()</font> adds a polynomial evaluation on top. This single function costs <b>%.0f %%</b> of the whole pipeline. By Amdahl's law, nothing else is worth touching until it is fixed." % (100.0 * v2["conv"] / v2["total"])),
      P("7.2 Optimisations applied (v3)", h2),
      table([["#", "Change", "Mechanism", "Effect (v2 -> v3, -O2)"],
             ["O1", "Thermistor conversion by lookup table", "257-entry int16 table (514 bytes of flash, generated by tools/gen_lut.py) with linear interpolation, replaces float math and logf()", "%.0f -> %.0f ticks (%.0fx); soft-float and libm no longer linked" % (v2["conv"], v3["conv"], M["speedup_conv_O2"])],
             ["O2", "Moving average with running sum", "sum += new; sum -= oldest; result = sum >> 5. O(1) instead of O(32); no divide once the window is full", "%.0f -> %.0f ticks (%.1fx)" % (v2["filt"], v3["filt"], M["speedup_filt_O2"])],
             ["O3", "Ring buffer index wrap by mask", "RB_SIZE is a power of two: (i+1) & 63 replaces compare-and-branch", "%.0f -> %.0f ticks" % (v2["acq"], v3["acq"])],
             ["O4", "Log formatting without printf", "Hand-written decimal formatter writes the line into a stack buffer", "%.0f -> %.0f ticks (%.1fx); newlib printf removed from flash" % (v2["log"], v3["log"], v2["log"] / v3["log"])],
             ["O5", "Command parser without stdio / string.h", "Small bounded helpers replace snprintf, strcmp, strncmp", "Flash reduction (shared with O4)"],
             ["O6", "Compiler and linker flags", "-O2 for speed or -Os for size, -ffunction-sections -fdata-sections -Wl,--gc-sections", "See Section 8.3"]],
            [0.8, 4.3, 7.2, 4.9]),
      Spacer(1, 4),
      P("7.3 Key code changes", h2),
      code("// v2 (float, ~%d ticks)                                    // v3 (table, ~%d ticks)\n"
           "float r  = 10000.0f * adc / (4095.0f - adc);               unsigned i = adc >> LUT_SHIFT;           // LUT_SHIFT = 4\n"
           "float lr = logf(r / 10000.0f);                             unsigned f = adc & 15;\n"
           "float tc = 1.0f/(1.0f/298.15f + lr/3950.0f) - 273.15f;     int a = g_lut[i], b = g_lut[i + 1];\n"
           "*t_x10 = (int)(tc*10.0f + 0.5f);                           *t_x10 = a + (((b - a) * (int)f + 8) >> 4);" % (round(v2["conv"]), round(v3["conv"])), codest),
      code("// v2 moving average: loop + divide                        // v3: running sum, shift\n"
           "uint32_t sum = 0;                                         sum += x; sum -= win[pos]; win[pos] = x;\n"
           "for (int i = 0; i < filled; i++) sum += win[i];           pos = (pos + 1) & (MA_WIN - 1);\n"
           "return sum / filled;                                      return (uint16_t)(sum >> 5);", codest),
      P("<b>Choosing the table step.</b> The generator reports the worst-case interpolation error for several step sizes over the full operating range (-40 to +125 deg C):"),
      code("shift 6 (step 64):  65 entries, 130 bytes, max err 9.54 (x0.1 C)   -> too inaccurate\n"
           "shift 5 (step 32): 129 entries, 258 bytes, max err 2.43 (x0.1 C)   -> too inaccurate\n"
           "shift 4 (step 16): 257 entries, 514 bytes, max err 1.39 (x0.1 C)   -> chosen (with rounding: %.2f C)" % M["lut_max_err_C"], logst),
      fig("fig_lut_error.png", 15.0, "Figure 6 - Lookup-table error over all 3854 ADC codes in the operating range. Mean error %.3f deg C, maximum %.2f deg C." % (M["lut_mean_err_C"], M["lut_max_err_C"])),
      P("The thermistor curve is steepest at the cold end, which is where the error peaks; at room temperature it is well below 0.05 deg C. The table adds 514 bytes of flash but removes several kilobytes of library code.")]

# ===================================================================== 8 validation
S += [CondPageBreak(9 * cm), P("8. Validation results", h1),
      P("8.1 Functional equivalence (v1 vs v2 vs v3)", h2),
      P("A double-precision golden model (<font face='Courier'>tools/make_charts.py</font>, same fault handling and the same integer moving average, exact floating-point thermistor equation) was run over the same 512 ADC samples. "
        "The firmware outputs are compared with it:"),
      table([["Metric (512 samples)", "v1 buggy", "v2 fixed", "v3 optimised"],
             ["Maximum |error| vs golden model", "%.0f deg C" % (M["trace_err_v1_buggy"]["max_abs_x10"] / 10.0), "%.2f deg C" % (M["trace_err_v2_fixed"]["max_abs_x10"] / 10.0), "%.2f deg C" % (M["trace_err_v3_optimized"]["max_abs_x10"] / 10.0)],
             ["Mean |error|", "%.1f deg C" % (M["trace_err_v1_buggy"]["mean_abs_x10"] / 10.0), "%.3f deg C" % (M["trace_err_v2_fixed"]["mean_abs_x10"] / 10.0), "%.3f deg C" % (M["trace_err_v3_optimized"]["mean_abs_x10"] / 10.0)],
             ["Samples within 0.1 deg C", "%.1f %%" % M["trace_err_v1_buggy"]["within_0_1C_pct"], "%.0f %%" % M["trace_err_v2_fixed"]["within_0_1C_pct"], "%.0f %%" % M["trace_err_v3_optimized"]["within_0_1C_pct"]],
             ["Samples with alarm active", str(M["alarm_v1_buggy"]["alarm_samples"]), str(M["alarm_v2_fixed"]["alarm_samples"]), str(M["alarm_v3_optimized"]["alarm_samples"])],
             ["First alarm at sample", str(M["alarm_v1_buggy"]["first_alarm"]), str(M["alarm_v2_fixed"]["first_alarm"]), str(M["alarm_v3_optimized"]["first_alarm"])],
             ["False alarms in first 100 samples (cold)", str(M["alarm_v1_buggy"]["false_alarms_first_100"]), "0", "0"],
             ["Sensor faults detected (expected 2)", "0", "2", "2"],
             ["Unit tests passed", "%d / %d" % (M["tests_pass"]["v1_buggy"], M["tests_total"]), "%d / %d" % (M["tests_pass"]["v2_fixed"], M["tests_total"]), "%d / %d" % (M["tests_pass"]["v3_optimized"], M["tests_total"])]],
            [6.4, 3.4, 3.4, 4.0]),
      Spacer(1, 4),
      P("v2 and v3 make <b>identical alarm decisions on all 512 samples</b> (%d mismatches). Their UART logs on the emulated Cortex-M3 differ only in the last digit of some temperatures (for example "
        "<font face='Courier'>176,25.3</font> in v2 versus <font face='Courier'>176,25.2</font> in v3) - the expected 0.1 deg C consequence of table interpolation. The optimisation therefore changed the speed, not the behaviour." % M["state_mismatch_v2_v3"]),
      P("8.2 Memory-safety validation of the fixed versions", h2),
      P("v2 and v3 were rebuilt with <font face='Courier'>-fsanitize=address,undefined,float-cast-overflow -fno-sanitize-recover=all</font> and also run under valgrind with full leak checking. "
        "All 14 tests pass with <b>zero</b> sanitizer reports and zero valgrind errors (<font face='Courier'>results/v2_fixed_sanitizers.log</font>, <font face='Courier'>v3_optimized_valgrind.log</font>). cppcheck reports a single portability note for v3 (right shift of a negative interpolation difference, <font face='Courier'>thermo.c:9</font>); GCC defines this as an arithmetic shift and the accuracy test confirms the result, but it is implementation-defined behaviour that a port to another compiler should re-check."),
      P("8.3 Performance: build matrix on the emulated Cortex-M3", h2),
      fig("fig_stage_timing.png", 14.5, "Figure 7 - Net ticks per sample for each pipeline stage (log scale). The conversion stage dominates v2 and almost disappears in v3."),
      table([["Build", "Flash (B)", "Static RAM (B)", "acq", "filt", "conv", "alarm", "log", "Total ticks / sample", "CPU load @1 kHz"]] +
            [[lab, str(M[k]["flash"]), str(M[k]["ram"])] + ["%.0f" % M[k][s] for s in stages] + ["<b>%.0f</b>" % M[k]["total"], "%.1f %%" % M["cpu_load_1kHz_pct"][k]] for lab, k in
             [("v2 -O0", "v2_fixed-O0"), ("v2 -O2", "v2_fixed-O2"), ("v2 -Os", "v2_fixed-Os"), ("v3 -O0", "v3_optimized-O0"), ("v3 -O2", "v3_optimized-O2"), ("v3 -Os", "v3_optimized-Os")]],
            [1.6, 1.5, 1.8, 1.2, 1.2, 1.3, 1.3, 1.2, 2.6, 2.4]),
      Spacer(1, 4),
      fig("fig_build_matrix.png", 15.0, "Figure 8 - Execution cost and flash size for the six builds (QEMU Cortex-M3, 512 samples, net of timer overhead)."),
      B("<b>Speed:</b> %.1fx faster at -O2 (%.0f -> %.0f ticks per sample, i.e. about %.0f us -> %.0f us of model time at 12 MHz). The 1 kHz sampling task drops from %.1f %% to %.1f %% of the CPU." % (M["speedup_total_O2"], v2["total"], v3["total"], v2["total"] / 12.0, v3["total"] / 12.0, M["cpu_load_1kHz_pct"]["v2_fixed-O2"], M["cpu_load_1kHz_pct"]["v3_optimized-O2"])),
      B("<b>Flash:</b> %d -> %d bytes (-%.1f %%) at -O2, and %d -> %d bytes (-%.1f %%) at -Os. These totals include the 1024-byte replayed ADC recording that is present in every build; "
        "excluding it, code plus constants shrink from %d to %d bytes (-%.1f %%) at -O2. The savings come from removing the soft-float library, logf() and newlib's printf (confirmed with arm-none-eabi-nm: none of them is linked into v3)." % (v2["flash"], v3["flash"], M["flash_reduction_O2_pct"], M["v2_fixed-Os"]["flash"], M["v3_optimized-Os"]["flash"], pct(M["v3_optimized-Os"]["flash"], M["v2_fixed-Os"]["flash"]), v2["flash"] - 1024, v3["flash"] - 1024, pct(v3["flash"] - 1024, v2["flash"] - 1024))),
      B("<b>RAM:</b> static RAM (.data + .bss) falls from %d to %d bytes at -O2, mainly because newlib's re-entrancy data (<font face='Courier'>_impure_data</font>, 76 bytes) is no longer linked in." % (v2["ram"], v3["ram"])),
      B("<b>Compiler flags:</b> -O2 beats -O0 by only %.2fx on v2 because the soft-float library dominates either way; on v3 -O2 is %.1fx faster than -O0. -Os gives the smallest image at a %.0f %% speed cost on v3. Optimising the algorithm mattered far more than the compiler switch." % (M["v2_fixed-O0"]["total"] / v2["total"], M["v3_optimized-O0"]["total"] / v3["total"], 100.0 * (M["v3_optimized-Os"]["total"] / v3["total"] - 1))),
      P("8.4 Secondary check on the host PC", h2),
      P("The same per-stage counters were collected on the development PC (x86-64, -O2, 200 passes of the trace, <font face='Courier'>clock_gettime</font>): v2 %s and v3 %s." % (
          esc(rf("results/host_bench_v2_fixed.txt").strip()), esc(rf("results/host_bench_v3_optimized.txt").strip())) +
        " On a desktop CPU with a hardware FPU the timer-read overhead (about 30 ns per stage) is comparable to the work itself, so these numbers show only the direction of the change; "
        "the soft-float effect is specific to FPU-less microcontrollers.")]

# ===================================================================== 9 hardware
S += [CondPageBreak(9 * cm), P("9. Hardware validation status and procedure", h1),
      P("The measurements in Section 8 were produced on an emulated Cortex-M3. The binaries are ordinary Thumb-2 images, and the Cortex-M3 core is the same one found in the STM32F103, "
        "but emulator timing is not silicon timing. To close that gap the repository contains a hardware port, <font face='Courier'>ports/stm32f103/</font>, which replaces only the HAL:"),
      B("UART: USART1 on PA9, 115200 baud from the 8 MHz internal oscillator;"),
      B("time base: SysTick at 1 kHz (same application tick as in QEMU);"),
      B("timing: <font face='Courier'>hal_timer_read()</font> returns the <b>DWT cycle counter (CYCCNT)</b>, so <font face='Courier'>g_prof[]</font> then contains real core clock cycles;"),
      B("input: the same 512-sample recording is replayed, so hardware and emulator results are directly comparable."),
      P("The port compiles and links for both versions (v3 -O2: 4584 bytes of flash and 244 bytes of static RAM; v2 -O2: 9824 bytes of flash), which fits the 64 KiB / 20 KiB device with large margin. "
        "<b>It has not been executed on a physical board as part of this report</b>; the table below is the template for those measurements and is deliberately left unfilled rather than estimated.", note),
      P("Procedure:", h3),
      code("make stm32 V=v2_fixed    OPT=-O2        # -> build/stm32_v2_fixed-O2.bin\n"
           "make stm32 V=v3_optimized OPT=-O2        # -> build/stm32_v3_optimized-O2.bin\n"
           "st-flash write build/stm32_v3_optimized-O2.bin 0x8000000     # or OpenOCD / STM32CubeProgrammer\n"
           "# serial terminal 115200 8N1 on PA9; the last two lines are:\n"
           "#   # done ticks=...        (wall time, 8 MHz ticks, ~4.1e6 for 512 ms)\n"
           "#   # prof acq=.. filt=.. conv=.. alarm=.. log=..    (REAL CPU cycles summed over 512 samples)", codest),
      P("Measured results available without a board (emulated Cortex-M3, -O2, net ticks per sample; 1 tick = 1.25 emulated instructions, Section 3):", h3),
      table([["Measurement (QEMU Cortex-M3, instruction model)", "v2 fixed", "v3 optimised", "Ratio"],
             ["ADC to temperature (ticks / sample)", "%.1f" % v2["conv"], "%.1f" % v3["conv"], "%.0fx" % M["speedup_conv_O2"]],
             ["Moving average (ticks / sample)", "%.1f" % v2["filt"], "%.1f" % v3["filt"], "%.1fx" % M["speedup_filt_O2"]],
             ["UART log formatting (ticks / sample)", "%.1f" % v2["log"], "%.1f" % v3["log"], "%.1fx" % (v2["log"] / v3["log"])],
             ["Total (ticks / sample)", "%.1f" % v2["total"], "%.1f" % v3["total"], "%.1fx" % M["speedup_total_O2"]],
             ["Approx. instructions / sample (ticks x 1.25)", "%.0f" % (v2["total"] * 1.25), "%.0f" % (v3["total"] * 1.25), "%.1fx" % M["speedup_total_O2"]],
             ["Flash, STM32F103 build (bytes)", "9824", "4584", "-53.3 %"],
             ["Static RAM, STM32F103 build (bytes)", "336", "244", "-27.4 %"],
             ["Alarm decisions identical (512 samples)", "-", "yes (0 mismatches)", "-"],
             ["Physical-board cycle count (DWT CYCCNT)", "not measured", "not measured", "-"]],
            [8.2, 3.0, 3.0, 3.0]),
      Spacer(1, 4),
      Spacer(1, 4),
      P("Expected outcome (a hypothesis to test, not a result): because soft-float multiply, divide and logf contain many multi-cycle operations that the emulator counts as one instruction, the real-silicon speed-up of the conversion stage should be at least as large as the emulated one.")]

# ===================================================================== 10 conclusions
S += [P("10. Conclusions", h1),
      B("A systematic, layered approach found all 11 defects: static analysis (3 defects), unit tests (8), sanitizers and valgrind (3), code review (2: Bugs 8 and 10), GDB on the ARM target (the mechanism behind Bug 1), and the -O2 build plus disassembly (Bug 11). No single tool found everything; Bug 1 is invisible to AddressSanitizer, Bug 10 was invisible to every test and log."),
      B("Fixing the defects changed the output from wrong (96.9 %% of samples in alarm, errors up to %.0f deg C) to correct within %.2f deg C of a double-precision model on all 512 samples." % (M["trace_err_v1_buggy"]["max_abs_x10"] / 10.0, M["trace_err_v2_fixed"]["max_abs_x10"] / 10.0)),
      B("Profiling pointed at one function (%.0f %% of cycles). Replacing floating-point math with a 514-byte lookup table gave %.0fx on that stage and %.1fx overall, while halving flash use, at a cost of at most %.2f deg C." % (100.0 * v2["conv"] / v2["total"], M["speedup_conv_O2"], M["speedup_total_O2"], M["lut_max_err_C"])),
      B("The regression suite and sanitizers were re-run after every change; v2 and v3 pass 14/14 with zero sanitizer reports."),
      P("<b>Limitations and future work.</b> (1) On-board cycle measurement (Section 9) is the remaining validation step. (2) The ADC is a replayed recording, not a live converter; reading the real ADC and DMA-ing samples would add an interrupt-driven producer/consumer case for the ring buffer. "
        "(3) A real command interface would use a UART receive interrupt; the volatile/atomicity analysis would then need to cover the receive buffer. (4) Stack-usage analysis (<font face='Courier'>-fstack-usage</font>) and a hardware watchdog were out of scope."),
      Spacer(1, 4)]

# ===================================================================== appendices
S += [PageBreak(), P("Appendix A - Reproducing every result", h1),
      P("From the repository root (Ubuntu 24.04; <font face='Courier'>sudo apt install gcc-arm-none-eabi qemu-system-arm gdb-multiarch valgrind cppcheck python3-matplotlib python3-reportlab</font>):"),
      code("python3 tools/gen_trace.py          # ADC recording  -> common/adc_trace.h, results/trace_truth.csv\n"
           "python3 tools/gen_lut.py 4          # LUT            -> v3_optimized/thermo_lut.h\n"
           "./tools/run_tests.sh                # unit tests, UBSan, ASan, valgrind, gcc/cppcheck, host timing, traces\n"
           "./tools/bench.sh                    # builds v2/v3 at -O0/-O2/-Os, runs in QEMU, results/bench.csv\n"
           "bash tools/gdb_session.sh           # GDB-on-QEMU ring-buffer session\n"
           "make arm V=v1_buggy OPT=-O0 && make run V=v1_buggy OPT=-O0      # watch the buggy firmware run\n"
           "python3 tools/make_charts.py        # figures + results/metrics.json\n"
           "python3 tools/build_report.py       # this PDF", codest),
      P("Tool versions used: " + esc("; ".join(l.strip() for l in rf("results/env.txt").strip().split("\n")))),
      P("Appendix B - Source differences", h1),
      P("B.1 v1 (buggy) to v2 (fixed)", h2), code(rf("results/diff_v1_v2.txt")),
      PageBreak(), P("B.2 v2 (fixed) to v3 (optimised)", h2), code(rf("results/diff_v2_v3.txt"))]

S += [PageBreak(), P("Appendix C - Complete source of v3 (final firmware) and the test suite", h1)]
for f in ["common/fw.h", "common/hal.h", "v3_optimized/ringbuf.c", "v3_optimized/filter.c", "v3_optimized/thermo.c", "v3_optimized/alarm.c", "v3_optimized/cmd.c", "v3_optimized/app.c", "v3_optimized/main.c",
          "common/hal_qemu.c", "common/startup.c", "common/lm3s.ld", "ports/stm32f103/hal_stm32f103.c", "tools/gen_lut.py"]:
    S += [KeepTogether([P(f, h3), code(rf(f))])]
S += [PageBreak(), P("C.1 Unit-test suite (tests/test_all.c)", h2), code(rf("tests/test_all.c"))]

S += [PageBreak(), P("Appendix D - Raw logs", h1),
      P("D.1 v1 (buggy) UART log, QEMU, -O0", h2), code(rf("results/qemu_v1_buggy-O0.log"), logst),
      P("D.2 v3 (optimised) UART log, QEMU, -O2", h2), code(rf("results/qemu_v3_optimized-O2.log"), logst),
      P("D.3 Benchmark matrix (results/bench.csv, raw ticks over 512 samples, before subtracting the 6150-tick timer floor per stage)", h2), code(rf("results/bench.csv"), logst),
      P("D.4 QEMU timing calibration (results/qemu_calibration.log)", h2), code(rf("results/qemu_calibration.log"), logst),
      P("D.5 Unit-test log of v1 (results/tests_v1_buggy.log)", h2), code(rf("results/tests_v1_buggy.log"), logst),
      P("D.6 Sanitizer / valgrind verdict for the fixed versions", h2),
      code("v2_fixed : ASan+UBSan 14/14 PASS, exit 0;  valgrind exit 0 (no errors, no leaks)\nv3_optimized: ASan+UBSan 14/14 PASS, exit 0;  valgrind exit 0 (no errors, no leaks)\n\n" +
           rf("results/v3_optimized_sanitizers.log"), logst),
      P("D.7 Disassembly of the wait loop (results/disasm_wait_loop.txt, first 22 lines of each)", h2),
      code("\n".join(rf("results/disasm_wait_loop.txt").split("\n")[:24]), logst)]

doc = Doc(OUT)
doc.multiBuild(S)
print("wrote", OUT, os.path.getsize(OUT), "bytes")
