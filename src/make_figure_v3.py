"""Summary figure for v3. Run from repo root after run_v3.py, size_study.py, boom_vs_bubble.py.
Encoding is fixed across panels: ORANGE = what v2 did, BLUE = what v3 does."""
import os, pickle
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
from psy_v3 import gaussian_null_bsadf, pointwise_cv, date_episodes

SURF, INK, INK2, MUT = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8984"
BLUE, ORANGE = "#2a78d6", "#eb6834"          # validated palette slots 1 and 2

size = pd.read_csv("results/size_study.csv")
bvb = pd.read_csv("results/boom_vs_bubble.csv")
v3 = pickle.load(open("results/v3_results.pkl", "rb"))["out"]["NVDA"]

def style(ax):
    ax.set_facecolor(SURF)
    for sp in ("top", "right"): ax.spines[sp].set_visible(False)
    for sp in ("left", "bottom"): ax.spines[sp].set_color(MUT)
    ax.tick_params(colors=INK2, labelsize=9)
    ax.grid(axis="y", alpha=.18, lw=.6, color=MUT); ax.set_axisbelow(True)

def bars(ax, labels, a, b, la, lb, title, nominal=None, ymax=1.0):
    x = np.arange(len(labels)); w = .36
    for off, vals, col, lab in ((-w/2, a, ORANGE, la), (w/2, b, BLUE, lb)):
        rs = ax.bar(x + off, vals, w, color=col, edgecolor=SURF, lw=2, label=lab, zorder=3)
        for r, v in zip(rs, vals):
            ax.text(r.get_x() + r.get_width()/2, v + ymax*.015, f"{v:.0%}", ha="center",
                    va="bottom", fontsize=8.5, color=INK, zorder=4)
    if nominal is not None:
        ax.axhline(nominal, color=INK2, lw=1.2, ls="--", zorder=2, label="nominal 5% rate")
    ax.set_xticks(x, labels, fontsize=8.8, color=INK2)
    ax.set_ylim(0, ymax)
    top = min(ymax, 1.0); step = .05 if top < .5 else .2
    ax.set_yticks(np.arange(0, top + 1e-9, step)); ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
    ax.set_title(title, fontsize=10.5, weight="bold", color=INK, loc="left", pad=8)
    style(ax)
    ax.legend(loc="upper left", fontsize=8.3, frameon=False, labelcolor=INK)

fig = plt.figure(figsize=(13, 10.2), facecolor=SURF)
gs = fig.add_gridspec(2, 3, height_ratios=[1, 1.15], hspace=.42, wspace=.28)
dgp = ["Gaussian\n(v2's assumption)", "GARCH-t\n(NVDA-fit)", "NVDA's own\nvol path"]

bars(fig.add_subplot(gs[0, 0]), dgp, size.gsadf_v2, size.gsadf_v3,
     "v2: Gaussian null", "v3: wild bootstrap",
     "A. Whole-sample test on\n     bubble-FREE data", nominal=.05, ymax=.32)
bars(fig.add_subplot(gs[0, 1]), dgp, size.stamp_v2, size.stamp_v3,
     "v2: pointwise dating", "v3: family-wise dating",
     "B. ≥1 fake episode dated in a\n     bubble-free 17-year sample", ymax=1.32)
bars(fig.add_subplot(gs[0, 2]), ["neither", "earnings\nboom", "valuation\nbubble"],
     bvb.reject_price, bvb.reject_ratio, "test on price (v1/v2)", "test on price ÷ earnings (v3)",
     "C. Same 3× price run-up:\n     who says “bubble”?", ymax=1.32)

# ---- D: NVDA, what survived
ax = fig.add_subplot(gs[1, :]); style(ax); ax.grid(axis="x", alpha=.18, lw=.6, color=MUT)
px = v3["px"]; ax.plot(px.index, px.values, color=INK2, lw=1.3, zorder=3); ax.set_yscale("log")
lo, hi = px.min() * .55, px.max() * 3.2; ax.set_ylim(lo, hi)
gnull = gaussian_null_bsadf(v3["T"], 499, seed=202)
eps2, _ = date_episodes(v3["bsadf"], pointwise_cv(gnull), 4)
for o, last, _t in eps2:                          # v2's episodes: thin strip at the top
    ax.axvspan(px.index[o], px.index[last], ymin=.93, ymax=.975, color=ORANGE, lw=0, zorder=2)
for i, (o, last, term) in enumerate(v3["eps"], 1):
    ax.axvspan(px.index[o], px.index[last], ymin=0, ymax=.9, color=BLUE, alpha=.16, lw=0, zorder=1)
    ax.text(px.index[o], lo * (1.25 if i % 2 else 1.9), f"{i}", fontsize=8.5, color=BLUE,
            weight="bold")
tab = v3["table"]
for i, r in tab.iterrows():
    if r["maxdd_after_termination"] is not None and r["maxdd_after_termination"] < -.3:
        t = pd.Timestamp(r["termination"]); p = px.loc[t]
        ax.plot([t], [p], "o", ms=8, color=BLUE, mec=SURF, mew=2, zorder=5)
        ax.annotate(f"test says “over” here\n(already {r['dd_peak_to_termination']:.0%} off peak)\n"
                    f"then {r['maxdd_after_termination']:.0%} more within a year",
                    (t, p), xytext=(12, -52), textcoords="offset points", fontsize=8.5,
                    color=INK, arrowprops=dict(arrowstyle="-", color=MUT, lw=.8))
ax.annotate("18 Sep 2026:\nno live episode", (px.index[-1], px.iloc[-1]), xytext=(-4, -44),
            textcoords="offset points", ha="right", fontsize=9, color=INK, weight="bold")
ax.set_ylabel("price, log scale (USD, split-adj.)", fontsize=9.5, color=INK2)
ax.set_title("D. NVDA: what survives a correct null. Blue = v3 episodes (numbered); "
             "orange strip = what v2 flagged", fontsize=10.5, weight="bold", color=INK,
             loc="left", pad=8)
ax.legend(handles=[Line2D([0], [0], color=INK2, lw=1.5, label="NVDA weekly close"),
                   Patch(fc=BLUE, alpha=.16, label="v3 family-wise episode"),
                   Patch(fc=ORANGE, label="v2 pointwise episode (mostly noise; see B)")],
          loc="upper left", fontsize=8.5, frameon=False, labelcolor=INK)

fig.suptitle("v3 review: v2 found bubbles in noise and in earnings growth",
             fontsize=14, weight="bold", color=INK, x=.06, ha="left", y=.985)
fig.text(.06, .945, "A–B: 400 simulated bubble-free samples each (warp-speed bootstrap).  "
         "C: 300 simulated worlds each.  D: weekly closes, 2009–2026.  NVDA whole-sample "
         "p = 0.076 (v3) vs 0.008 (v2).", fontsize=8.8, color=INK2)
os.makedirs("results", exist_ok=True)
fig.savefig("results/v3_summary.png", dpi=145, facecolor=SURF, bbox_inches="tight")
print("saved results/v3_summary.png")
