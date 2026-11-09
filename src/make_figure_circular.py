"""Figure for circular-funding ratio v1. Run from repo root after circular_funding.py."""
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

SURF, INK, INK2, MUT = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8984"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
nv = pd.read_csv("results/circular_nvda.csv", index_col=0, parse_dates=True)
cw = pd.read_csv("results/circular_crwv.csv", index_col=0, parse_dates=True)
B = 1e9


def style(ax):
    ax.set_facecolor(SURF)
    for sp in ("top", "right"): ax.spines[sp].set_visible(False)
    for sp in ("left", "bottom"): ax.spines[sp].set_color(MUT)
    ax.tick_params(colors=INK2, labelsize=8.8)
    ax.grid(axis="y", alpha=.18, lw=.6, color=MUT); ax.set_axisbelow(True)


qlab = lambda idx, fy=False: [f"{d:%b %y}" for d in idx]
fig = plt.figure(figsize=(13, 10.6), facecolor=SURF)
gs = fig.add_gridspec(2, 2, hspace=.5, wspace=.24, height_ratios=[1.15, 1])

# ---- A: Nvidia exposure, stacked
ax = fig.add_subplot(gs[0, :]); style(ax)
d = nv[nv.index >= "2024-10-01"]
x = np.arange(len(d)); w = .62
bottom = np.zeros(len(d))
for col, colr, lab in (("private_stakes", BLUE, "stakes in private companies (labs, neoclouds)"),
                       ("listed_stakes", AQUA, "stakes in listed companies"),
                       ("guarantee_max", ORANGE, "guarantees, maximum exposure")):
    v = d[col].fillna(0).values / B
    ax.bar(x, v, w, bottom=bottom, color=colr, edgecolor=SURF, lw=2, label=lab, zorder=3)
    bottom += v
for i, (t, r) in enumerate(d.iterrows()):
    star = "" if r.exposure_complete else "*"
    pct = f"{r.exposure_pct_ttm_revenue:.0%}"
    txt = (f"${bottom[i]:.0f}B\n{pct} of yearly revenue{star}" if bottom[i] >= 20
           else f"${bottom[i]:.0f}B\n{pct}{star}")
    ax.text(i, bottom[i] + 3, txt, ha="center", va="bottom",
            fontsize=8.6, color=INK, weight="bold" if r.exposure_complete else "normal")
ax.set_xticks(x, [f"{t:%b %Y}" for t in d.index], fontsize=8.8, color=INK2)
ax.set_ylim(0, bottom.max() * 1.28); ax.set_ylabel("$ billions", fontsize=9.5, color=INK2)
ax.set_title("A. Nvidia's money in the AI ecosystem, at each fiscal quarter-end",
             fontsize=11, weight="bold", color=INK, loc="left", pad=8)
ax.legend(loc="upper left", fontsize=8.6, frameon=False, labelcolor=INK)
ax.text(1, -.17, "* incomplete: at least one component is not tagged in the SEC data for that "
        "quarter, so the total is a lower bound", transform=ax.transAxes, ha="right",
        fontsize=8.2, color=MUT, style="italic")

# ---- B: investment gains share of pretax profit
ax = fig.add_subplot(gs[1, 0]); style(ax)
d = nv[nv.index >= "2024-04-01"]
v = d.gains_pct_pretax.values
bars = ax.bar(np.arange(len(d)), v, .62, color=BLUE, edgecolor=SURF, lw=2, zorder=3)
for i, val in enumerate(v):
    ax.text(i, max(val, 0) + .006, f"{val:.0%}", ha="center", va="bottom", fontsize=8.5, color=INK)
ax.axhline(0, color=MUT, lw=.8)
ax.set_xticks(np.arange(len(d)), [f"{t:%b %y}" for t in d.index], fontsize=8.3, color=INK2, rotation=0)
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y:.0%}"))
ax.set_ylim(min(0, v.min()) - .01, v.max() * 1.25)
ax.set_title("B. Nvidia: gains on investments as a share\n     of pre-tax profit, by quarter",
             fontsize=11, weight="bold", color=INK, loc="left", pad=8)

# ---- C: CoreWeave capex vs operating cash flow
ax = fig.add_subplot(gs[1, 1]); style(ax)
d = cw.dropna(subset=["capex_q"]); x = np.arange(len(d)); w = .38
ax.bar(x - w / 2, d.capex_q / B, w, color=ORANGE, edgecolor=SURF, lw=2, label="capex (cash paid)", zorder=3)
ax.bar(x + w / 2, d.ocf_q / B, w, color=AQUA, edgecolor=SURF, lw=2, label="operating cash flow", zorder=3)
ax.axhline(0, color=MUT, lw=.8)
for i, (t, r) in enumerate(d.iterrows()):
    if pd.notna(r.debt):
        ax.text(i, max(r.capex_q, r.ocf_q) / B + .2, f"debt\n${r.debt/B:.0f}B", ha="center",
                va="bottom", fontsize=7.6, color=INK2)
ax.set_xticks(x, [f"{t:%b %y}" for t in d.index], fontsize=8.3, color=INK2)
ax.set_ylabel("$ billions per quarter", fontsize=9.5, color=INK2)
ax.set_ylim(min(0, (d.ocf_q / B).min()) - .5, (d.capex_q / B).max() * 1.45)
ax.set_title("C. CoreWeave: spending vs cash it generates,\n     and the debt that fills the gap",
             fontsize=11, weight="bold", color=INK, loc="left", pad=8)
ax.legend(loc="upper left", fontsize=8.4, frameon=False, labelcolor=INK)

fig.suptitle("Circular-funding ratio v1: how much of the AI loop is Nvidia's own money",
             fontsize=13.5, weight="bold", color=INK, x=.07, ha="left", y=.985)
fig.text(.07, .953, "Source: SEC XBRL company facts (Nvidia fiscal quarters; CoreWeave calendar quarters), "
         "first-reported values. Stakes are carried values incl. revaluation gains; guarantees are "
         "maximum exposure, not expected loss.", fontsize=8.5, color=INK2)
fig.savefig("results/circular_v1.png", dpi=145, facecolor=SURF, bbox_inches="tight")
print("saved results/circular_v1.png")
