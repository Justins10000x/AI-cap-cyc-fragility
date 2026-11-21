"""Figure for depreciation v1. Run from repo root after depreciation.py."""
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

SURF, INK, INK2, MUT = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8984"
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]   # fixed categorical order
NEUTRAL = "#c9c8c2"
F = pd.read_csv("results/depreciation_fits.csv")
Q = pd.read_csv("results/depreciation_quarterly.csv", index_col=0, parse_dates=True)
C = F[F.central].set_index("company")
G = F[F.fits]
ORDER = ["Microsoft", "Alphabet", "Amazon", "Meta", "Oracle", "CoreWeave"]
B = 1e9


def style(ax, grid="y"):
    ax.set_facecolor(SURF)
    for sp in ("top", "right"): ax.spines[sp].set_visible(False)
    for sp in ("left", "bottom"): ax.spines[sp].set_color(MUT)
    ax.tick_params(colors=INK2, labelsize=8.8)
    ax.grid(axis=grid, alpha=.18, lw=.6, color=MUT); ax.set_axisbelow(True)


fig = plt.figure(figsize=(13, 11), facecolor=SURF)
gs = fig.add_gridspec(2, 2, hspace=.42, wspace=.28, height_ratios=[1.05, 1])

# ---- A: depreciation already coming
ax = fig.add_subplot(gs[0, :]); style(ax)
x = np.arange(len(ORDER)); w = .26
cols = [("dep_4q", NEUTRAL, "last 4 quarters (reported)"),
        ("dep_next4q_stop", SERIES[0], "next 4 quarters if capex stopped today (model)"),
        ("dep_next4q_flat", SERIES[1], "next 4 quarters if capex stays at the latest quarter's level (model)")]
for k, (col, colr, lab) in enumerate(cols):
    v = C.loc[ORDER, col].values / B
    ax.bar(x + (k - 1) * w, v, w - .02, color=colr, edgecolor=SURF, lw=2, label=lab, zorder=3)
    if k:
        g = C.loc[ORDER, "dep_growth_stop" if k == 1 else "dep_growth_flat"].values
        for i, (vi, gi) in enumerate(zip(v, g)):
            ax.text(i + (k - 1) * w, vi + 1.2, f"+{gi:.0%}", ha="center", va="bottom", fontsize=8.2, color=INK)
ax.set_xticks(x, [f"{c}\n(to {pd.Timestamp(C.loc[c, 'as_of']):%b %Y})" for c in ORDER], fontsize=9, color=INK2)
ax.set_ylabel("depreciation, $ billions", fontsize=9.5, color=INK2)
ax.set_ylim(0, C.dep_next4q_flat.max() / B * 1.22)
ax.legend(loc="upper left", fontsize=8.6, frameon=False, labelcolor=INK)
ax.set_title("A. Depreciation already set in motion by capex that has been spent",
             fontsize=11, weight="bold", color=INK, loc="left", pad=8)

# ---- B: shorter server lives
ax = fig.add_subplot(gs[1, 0]); style(ax, grid="x")
hs = ORDER[:5][::-1]
y = np.arange(len(hs)); h = .36
for k, (L, colr) in enumerate(((4, SERIES[0]), (3, SERIES[1]))):
    v = C.loc[hs, f"extra_dep_{L}y_pct_oi"].values
    ax.barh(y + (0.5 - k) * h, v, h - .03, color=colr, edgecolor=SURF, lw=2, zorder=3,
            label=f"servers last {L} years")
    for i, c in enumerate(hs):
        r = G[G.company == c][f"extra_dep_{L}y_pct_oi"]
        lab = f"{r.min():.0%}" if round(r.min(), 2) == round(r.max(), 2) else f"{r.min():.0%}–{r.max():.0%}"
        ax.text(v[i] + .006, y[i] + (0.5 - k) * h, lab, va="center", fontsize=8.2, color=INK)
ax.set_yticks(y, hs, fontsize=9, color=INK2)
ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
ax.set_xlim(0, C.loc[hs, "extra_dep_3y_pct_oi"].max() * 1.3)
ax.set_xlabel("extra depreciation per year, % of last-4-quarter operating income", fontsize=8.8, color=INK2)
ax.legend(loc="upper right", fontsize=8.4, frameon=False, labelcolor=INK)
cw = C.loc["CoreWeave"]
M = lambda v: f"{'−' if v < 0 else ''}\\${abs(v)/B:.1f}B"   # escaped: matplotlib reads $..$ as math
ax.text(0, -.19, f"CoreWeave (not shown: no operating profit): operating income over the last 4 quarters "
        f"{M(cw.op_income_4q)}\nwould be {M(cw.op_income_4q_at_4y)} at 4 years and "
        f"{M(cw.op_income_4q_at_3y)} at 3 years (stated life: 6).",
        transform=ax.transAxes, fontsize=8.2, color=INK2, va="top")
ax.set_title("B. If servers wore out faster than the\n     stated 5.5–6 years",
             fontsize=11, weight="bold", color=INK, loc="left", pad=8)

# ---- C: depreciation share of operating profit before depreciation
ax = fig.add_subplot(gs[1, 1]); style(ax)
d = Q[Q.index >= "2024-01-01"]
ends = []
for c, colr in zip(ORDER[:5], SERIES):
    s = d[d.company == c].dep_share_pre_dep_profit
    ax.plot(s.index, s.values, color=colr, lw=2, marker="o", ms=4.5, mec=SURF, mew=1.2, zorder=3)
    ends.append([s.values[-1], c, s.index[-1]])
ends.sort()                                   # dodge end labels so they never overlap
for i in range(1, len(ends)):
    ends[i][0] = max(ends[i][0], ends[i - 1][0] + .022)
for yy, c, t in ends:
    v = d[d.company == c].dep_share_pre_dep_profit.values[-1]
    ax.text(d.index.max() + pd.Timedelta(days=16), yy, f"{c} {v:.0%}", va="center", fontsize=8.4, color=INK)
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
ax.set_xlim(d.index.min() - pd.Timedelta(days=20), d.index.max() + pd.Timedelta(days=150))
ticks = pd.date_range("2024-03-31", d.index.max(), freq="2QE")
ax.set_xticks(ticks, [f"Q{t.quarter} {t.year}" for t in ticks])
ax.set_ylim(0, d[d.company.isin(ORDER[:5])].dep_share_pre_dep_profit.max() * 1.15)
ax.set_title("C. Depreciation as a share of operating profit\n     before depreciation, by quarter",
             fontsize=11, weight="bold", color=INK, loc="left", pad=8)
ax.tick_params(axis="x", labelsize=8.2)

fig.suptitle("Depreciation v1: how much of today's profit the build-out will absorb",
             fontsize=13.5, weight="bold", color=INK, x=.07, ha="left", y=.985)
fig.text(.07, .952, "Source: SEC XBRL company facts (quarters reconciled to 10-K totals); stated server lives from "
         "10-Ks (reported/useful_lives.csv). Panels A and B use a straight-line vintage model fitted to each "
         "company's reported depreciation.", fontsize=8.5, color=INK2)
fig.savefig("results/depreciation_v1.png", dpi=145, facecolor=SURF, bbox_inches="tight")
print("saved results/depreciation_v1.png")
