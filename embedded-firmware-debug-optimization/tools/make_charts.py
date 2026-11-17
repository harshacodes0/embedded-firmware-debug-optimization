#!/usr/bin/env python3
"""Build every figure in the report from the real logs/CSVs in results/. Also writes results/metrics.json."""
import csv, json, math, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R, C = os.path.join(ROOT, "results"), os.path.join(ROOT, "charts")
os.makedirs(C, exist_ok=True)
plt.rcParams.update({"font.size": 9, "axes.grid": True, "grid.alpha": 0.3, "figure.dpi": 150})
BLUE, RED, GREEN, ORANGE, GREY = "#1f5fa8", "#c0392b", "#2e8b57", "#e08a1e", "#666666"
M = {}

def rd(name): return list(csv.DictReader(open(os.path.join(R, name))))
truth = rd("trace_truth.csv")
tr = {v: rd("trace_%s.csv" % v) for v in ("v1_buggy", "v2_fixed", "v3_optimized")}
bench = rd("bench.csv")

# ------------------------------------------------------------------ golden model (double precision)
def golden():
    out, win, last, filled, s = [], [0]*32, 2048, 0, 0
    pos = 0; ssum = 0
    for i, row in enumerate(truth):
        raw = int(row["adc"]); fault = raw <= 10 or raw >= 4085
        x = last if fault else raw
        if not fault: last = raw
        if filled < 32:
            win[pos] = x; ssum += x; filled += 1; avg = ssum // filled
        else:
            ssum += x - win[pos]; win[pos] = x; avg = ssum // 32
        pos = (pos + 1) % 32
        r = 10000.0 * avg / (4095.0 - avg)
        t = (1.0 / (1.0 / 298.15 + math.log(r / 10000.0) / 3950.0) - 273.15) * 10.0
        out.append(t)
    return out
G = golden()
def err_stats(v):
    e = [int(tr[v][i]["t_x10"]) - G[i] for i in range(512)]
    ae = [abs(x) for x in e]
    return {"max_abs_x10": max(ae), "mean_abs_x10": sum(ae) / len(ae), "within_0_1C_pct": 100.0 * sum(1 for x in ae if x <= 1.0) / len(ae),
            "within_0_15C_pct": 100.0 * sum(1 for x in ae if x <= 1.5) / len(ae)}
for v in tr: M["trace_err_" + v] = err_stats(v)
for v in tr:
    al = [i for i, r in enumerate(tr[v]) if r["alarm"] == "1"]
    M["alarm_" + v] = {"alarm_samples": len(al), "first_alarm": al[0] if al else None, "false_alarms_first_100": sum(1 for i in al if i < 100)}
M["state_mismatch_v2_v3"] = sum(1 for a, b in zip(tr["v2_fixed"], tr["v3_optimized"]) if a["alarm"] != b["alarm"])

# ------------------------------------------------------------------ benchmark numbers
OVH = 6150  # measured timer-read overhead per stage for 512 samples (results/qemu_calibration.log)
def row(v, o): return next(r for r in bench if r["version"] == v and r["opt"] == o)
stages = ["acq", "filt", "conv", "alarm", "log"]
def net(v, o): return {s: max(0, int(row(v, o)[s]) - OVH) / 512.0 for s in stages}
for v in ("v2_fixed", "v3_optimized"):
    for o in ("-O0", "-O2", "-Os"):
        n = net(v, o); n["total"] = sum(n.values()); n["flash"] = int(row(v, o)["flash_bytes"]); n["ram"] = int(row(v, o)["ram_bytes"])
        M["%s%s" % (v, o)] = n
M["speedup_total_O2"] = M["v2_fixed-O2"]["total"] / M["v3_optimized-O2"]["total"]
M["speedup_conv_O2"] = M["v2_fixed-O2"]["conv"] / M["v3_optimized-O2"]["conv"]
M["speedup_filt_O2"] = M["v2_fixed-O2"]["filt"] / M["v3_optimized-O2"]["filt"]
M["flash_reduction_O2_pct"] = 100.0 * (1 - M["v3_optimized-O2"]["flash"] / M["v2_fixed-O2"]["flash"])
M["cpu_load_1kHz_pct"] = {k: M[k]["total"] / 12000.0 * 100.0 for k in ("v2_fixed-O0", "v2_fixed-O2", "v2_fixed-Os", "v3_optimized-O0", "v3_optimized-O2", "v3_optimized-Os")}

# ------------------------------------------------------------------ Fig 1: architecture
fig, ax = plt.subplots(figsize=(7.2, 2.6)); ax.axis("off"); ax.set_xlim(0, 100); ax.set_ylim(0, 36)
def box(x, y, w, h, t, fc="#e8f0fb", ec=BLUE):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.3,rounding_size=1.2", fc=fc, ec=ec, lw=1.2))
    ax.text(x + w / 2, y + h / 2, t, ha="center", va="center", fontsize=7.5)
def arrow(x1, y1, x2, y2): ax.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle="->", color=GREY, lw=1.2))
box(1, 14, 13, 9, "NTC + 10k\ndivider\n(12-bit ADC)", "#fff4e0", ORANGE)
box(18, 14, 12, 9, "hal_adc_read()\n(trace replay)")
box(34, 14, 11, 9, "Ring buffer\nrb_push/pop\n(64 x u16)")
box(49, 14, 12, 9, "Moving avg\nma_update()\n(32 samples)")
box(65, 14, 12, 9, "ADC -> temp\nthermo_adc_\nto_x10()")
box(81, 14, 12, 9, "Alarm +\nhysteresis\nalarm_update()")
box(65, 1, 12, 8, "Command parser\nSET / GET", "#eaf6ee", GREEN)
box(81, 1, 17, 8, "UART log\n(1 line / 16 samples)", "#eaf6ee", GREEN)
box(18, 27, 38, 7, "SysTick ISR (1 kHz)  ->  sample_due flag  ->  main loop", "#fdecea", RED)
for a, b in [(14, 18), (30, 34), (45, 49), (61, 65), (77, 81)]: arrow(a, 18.5, b, 18.5)
arrow(87, 14, 87, 9.3); arrow(71, 9.3, 71, 14); arrow(43, 27, 43, 23.3)
ax.text(0, 33, "Firmware data path (same code on QEMU Cortex-M3, host x86-64 and STM32F103)", fontsize=8, weight="bold")
fig.savefig(os.path.join(C, "fig_architecture.png"), bbox_inches="tight"); plt.close(fig)

# ------------------------------------------------------------------ Fig 2: debugging workflow
fig, ax = plt.subplots(figsize=(7.2, 2.5)); ax.axis("off"); ax.set_xlim(0, 100); ax.set_ylim(0, 33)
steps = ["1. Reproduce\nrun v1 in QEMU,\nread UART log", "2. Static\nanalysis\ngcc -Wextra,\ncppcheck", "3. Unit tests\n14 tests, one\nprocess each",
         "4. Dynamic\nanalysis\nASan, UBSan,\nvalgrind", "5. Target\ndebugger\nGDB + QEMU\nwatch memory", "6. Fix\n(v2) and\nre-run all", "7. Profile +\noptimise (v3)\nre-measure"]
w = 12.3
for k, t in enumerate(steps):
    x = 1 + k * 14.1
    fc = "#e8f0fb" if k < 5 else ("#eaf6ee" if k == 5 else "#fff4e0")
    ax.add_patch(FancyBboxPatch((x, 12), w, 17, boxstyle="round,pad=0.3,rounding_size=1.2", fc=fc, ec=BLUE, lw=1.1))
    ax.text(x + w / 2, 20.5, t, ha="center", va="center", fontsize=6.8)
    if k < 6: arrow(x + w + 0.4, 20.5, x + 14.1 - 0.4, 20.5)
ax.plot([92, 92, 7, 7], [11.5, 6.5, 6.5, 11.3], color=RED, lw=1.2)
ax.annotate("", xy=(7, 12.0), xytext=(7, 9.0), arrowprops=dict(arrowstyle="->", color=RED, lw=1.2))
ax.text(50, 2.2, "regression loop: every fix is re-checked by the same tests + sanitizers", ha="center", color=RED, fontsize=7.5)
fig.savefig(os.path.join(C, "fig_workflow.png"), bbox_inches="tight"); plt.close(fig)

# ------------------------------------------------------------------ Fig 3: ring-buffer memory layout
fig, ax = plt.subplots(figsize=(7.2, 1.9)); ax.axis("off"); ax.set_xlim(0, 100); ax.set_ylim(0, 22)
ax.add_patch(Rectangle((2, 9), 52, 7, fc="#e8f0fb", ec=BLUE)); ax.text(28, 12.5, "buf[0] ... buf[63]   (64 x uint16_t = 128 bytes)", ha="center", fontsize=8)
for x, t, fc in [(54, "head", "#fdecea"), (60, "tail", "#fdecea"), (66, "count", "#f4f4f4")]:
    ax.add_patch(Rectangle((x, 9), 6, 7, fc=fc, ec=RED if fc != "#f4f4f4" else GREY)); ax.text(x + 3, 12.5, t, ha="center", fontsize=8)
ax.add_patch(Rectangle((54, 2.5), 12, 4.5, fc="#fff4e0", ec=ORANGE)); ax.text(60, 4.75, "buf[64]  (does not exist!)", ha="center", fontsize=7.5)
ax.annotate("", xy=(57, 8.8), xytext=(57, 7.2), arrowprops=dict(arrowstyle="->", color=ORANGE))
ax.text(75, 13.8, "v1 writes buf[64] when head == 64", fontsize=7.8, color=RED, weight="bold")
ax.text(75, 10.2, "sample 3212 = 0x0C8C\n-> head = 0x8C = 140\n-> tail = 0x0C = 12", fontsize=7.5, va="center")
ax.text(2, 19, "Bug 1 - off-by-one: `if (head > RB_SIZE)` lets head reach 64; the 65th store lands on head/tail", fontsize=8, weight="bold")
fig.savefig(os.path.join(C, "fig_ringbuf_layout.png"), bbox_inches="tight"); plt.close(fig)

# ------------------------------------------------------------------ Fig 4: temperature traces
x = list(range(512)); tru = [float(r["true_c"]) for r in truth]
fig, axs = plt.subplots(2, 1, figsize=(7.2, 4.1), sharex=True)
for ax, v, col, ttl in ((axs[0], "v1_buggy", RED, "v1 (buggy) as found"), (axs[1], "v3_optimized", GREEN, "v3 (fixed + optimised)")):
    ax.plot(x, tru, color=GREY, lw=1.0, ls="--", label="true temperature (simulated)")
    ax.plot(x, [int(r["t_x10"]) / 10.0 for r in tr[v]], color=col, lw=1.0, label="firmware output")
    ax.axhline(40, color=ORANGE, lw=0.8, ls=":")
    al = [i for i, r in enumerate(tr[v]) if r["alarm"] == "1"]
    ax.fill_between(x, -22, 105, where=[r["alarm"] == "1" for r in tr[v]], color=RED, alpha=0.12, step="mid", label="alarm active")
    ax.set_ylim(-22, 105); ax.set_ylabel("deg C"); ax.set_title(ttl, fontsize=9); ax.legend(loc="upper left", fontsize=6.5, ncol=3)
axs[0].annotate("SET abc -> threshold 0.0 C\n(no validation)", xy=(205, 62), xytext=(250, 88), fontsize=7, arrowprops=dict(arrowstyle="->"))
axs[0].annotate("cold start: false ALARM\n(signed/unsigned)", xy=(10, -8), xytext=(35, -18), fontsize=7, arrowprops=dict(arrowstyle="->"))
for ax in axs: ax.axvline(150, color="k", lw=0.6, ls=":"); ax.axvline(330, color="k", lw=0.6, ls=":")
axs[1].text(152, -19, "open circuit", fontsize=6.5); axs[1].text(332, -19, "short circuit", fontsize=6.5)
axs[1].set_xlabel("sample index (1 kHz)")
fig.tight_layout(); fig.savefig(os.path.join(C, "fig_trace_compare.png")); plt.close(fig)

# ------------------------------------------------------------------ Fig 5: per-stage timing
fig, ax = plt.subplots(figsize=(7.2, 3.1)); w = 0.38
a, b = M["v2_fixed-O2"], M["v3_optimized-O2"]
xs = range(len(stages))
r1 = ax.bar([i - w / 2 for i in xs], [a[s] for s in stages], w, color=BLUE, label="v2 fixed (-O2)")
r2 = ax.bar([i + w / 2 for i in xs], [b[s] for s in stages], w, color=GREEN, label="v3 optimised (-O2)")
ax.set_yscale("log"); ax.set_xticks(list(xs)); ax.set_xticklabels(["acquire\n(ring buf)", "moving\naverage", "ADC->temp", "alarm", "UART log"])
ax.set_ylabel("ticks per sample (log scale)"); ax.set_title("Per-stage cost, QEMU Cortex-M3, 1 tick = 1/12 MHz")
for rects in (r1, r2):
    for r_ in rects: ax.text(r_.get_x() + r_.get_width() / 2, r_.get_height() * 1.08, "%.0f" % r_.get_height(), ha="center", fontsize=7)
ax.legend(); fig.tight_layout(); fig.savefig(os.path.join(C, "fig_stage_timing.png")); plt.close(fig)

# ------------------------------------------------------------------ Fig 6: build matrix + footprint
fig, axs = plt.subplots(1, 2, figsize=(7.2, 3.0))
labels = ["v2\n-O0", "v2\n-O2", "v2\n-Os", "v3\n-O0", "v3\n-O2", "v3\n-Os"]; keys = ["v2_fixed-O0", "v2_fixed-O2", "v2_fixed-Os", "v3_optimized-O0", "v3_optimized-O2", "v3_optimized-Os"]
cols = [BLUE] * 3 + [GREEN] * 3
tot = [M[k]["total"] for k in keys]
axs[0].bar(labels, tot, color=cols); axs[0].set_ylabel("ticks per sample"); axs[0].set_title("Execution cost per sample", fontsize=9)
for i, t in enumerate(tot): axs[0].text(i, t + 30, "%.0f" % t, ha="center", fontsize=7)
fl = [M[k]["flash"] / 1024.0 for k in keys]
axs[1].bar(labels, fl, color=cols); axs[1].set_ylabel("flash (KiB)"); axs[1].set_title("Code + constants in flash", fontsize=9)
for i, t in enumerate(fl): axs[1].text(i, t + 0.15, "%.1f" % t, ha="center", fontsize=7)
fig.tight_layout(); fig.savefig(os.path.join(C, "fig_build_matrix.png")); plt.close(fig)

# ------------------------------------------------------------------ Fig 7: LUT error
def tx10(adc):
    r = 10000.0 * adc / (4095.0 - adc)
    return (1.0 / (1.0 / 298.15 + math.log(r / 10000.0) / 3950.0) - 273.15) * 10.0
def tx10c(adc): return tx10(min(max(adc, 1), 4094))
tab = [int(round(tx10c(k * 16))) for k in range(257)]
def lut(adc):
    i, f = adc >> 4, adc & 15; a_, b_ = tab[i], tab[i + 1]
    return a_ + (((b_ - a_) * f + 8) >> 4)
codes = list(range(142, 3996)); errs = [lut(c) - tx10(c) for c in codes]
temps = [tx10(c) / 10.0 for c in codes]
M["lut_max_err_C"] = max(abs(e) for e in errs) / 10.0
M["lut_mean_err_C"] = sum(abs(e) for e in errs) / len(errs) / 10.0
M["lut_bytes"] = 2 * len(tab)
fig, ax = plt.subplots(figsize=(7.2, 2.6))
ax.plot(temps, [e / 10.0 for e in errs], color=GREEN, lw=0.8); ax.set_xlabel("temperature (deg C)"); ax.set_ylabel("LUT error (deg C)")
ax.set_title("v3 lookup-table error vs double-precision formula, all 3854 ADC codes from -40 to 125 deg C", fontsize=8.5)
ax.axhline(0.15, color=RED, lw=0.7, ls=":"); ax.axhline(-0.15, color=RED, lw=0.7, ls=":")
fig.tight_layout(); fig.savefig(os.path.join(C, "fig_lut_error.png")); plt.close(fig)

# ------------------------------------------------------------------ Fig 8: test matrix
names, res = [], {}
for v in ("v1_buggy", "v2_fixed", "v3_optimized"):
    cur = None
    for line in open(os.path.join(R, "test_summary.txt")):
        line = line.strip()
        if line.startswith("== "): cur = line[3:]; continue
        if cur == v and line:
            st, nm = line.split(" ", 1); res.setdefault(v, {})[nm] = st
            if nm not in names: names.append(nm)
fig, ax = plt.subplots(figsize=(7.2, 3.3))
colmap = {"PASS": "#cfe8d5", "FAIL": "#f5c6c2", "CRASH": "#e89a93"}
for j, v in enumerate(("v1_buggy", "v2_fixed", "v3_optimized")):
    for i, nm in enumerate(names):
        st = res[v][nm]; ax.add_patch(Rectangle((j, len(names) - 1 - i), 1, 1, fc=colmap[st], ec="white"))
        ax.text(j + 0.5, len(names) - 1 - i + 0.5, st, ha="center", va="center", fontsize=6.5)
ax.set_xlim(0, 3); ax.set_ylim(0, len(names)); ax.set_xticks([0.5, 1.5, 2.5]); ax.set_xticklabels(["v1 buggy", "v2 fixed", "v3 optimised"])
ax.set_yticks([len(names) - 1 - i + 0.5 for i in range(len(names))]); ax.set_yticklabels(names, fontsize=6.5); ax.grid(False)
ax.set_title("Unit-test results (host build, one process per test)", fontsize=9)
M["tests_pass"] = {v: sum(1 for s in res[v].values() if s == "PASS") for v in res}; M["tests_total"] = len(names)
fig.tight_layout(); fig.savefig(os.path.join(C, "fig_test_matrix.png")); plt.close(fig)

json.dump(M, open(os.path.join(R, "metrics.json"), "w"), indent=1)
print(json.dumps(M, indent=1))
