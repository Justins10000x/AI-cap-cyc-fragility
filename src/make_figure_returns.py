"""Figure for returns v1. Run from repo root after depreciation.py and returns.py."""
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

SURF, INK, INK2, MUT = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8984"
SERIES = ["#2a78d6", "#eb6834", "#1baf7a"]
NEUTRAL = "#c9c8c2"
BAND = "#e4e3de"
C = pd.read_csv("results/returns_combined.csv", index_col=0)
C.index = pd.PeriodIndex(C.index, freq="Q")
P = pd.read_csv("results/returns_quarterly.csv", index_col=0, parse_dates=True)
H = pd.read_csv("results/returns_hurdle.csv")
HURDLE = (H.hurdle.min(), H.hurdle.max())
B = 1e9


def style(ax, grid="y"):
    ax.set_facecolor(SURF)
    for sp in ("top", "right"): ax.spines[sp].set_visible(False)
    for sp in ("left", "bottom"): ax.spines[sp].set_color(MUT)
    ax.tick_params(colors=INK2, labelsize=8.8)
    ax.grid(axis=grid, alpha=.18, lw=.6, color=MUT); ax.set_axisbelow(True)


pct = plt.FuncFormatter(lambda v, _: f"{v:.0%}")
fig = plt.figure(figsize=(13, 10.8), facecolor=SURF)
gs = fig.add_gridspec(2, 2, hspace=.52, wspace=.26, height_ratios=[1.1, 1])

# ---- A: combined returns over time
ax = fig.add_subplot(gs[0, :]); style(ax)
d = C[C.index >= pd.Period("2019Q1", "Q")]
x = d.index.to_timestamp(how="end")
ax.axhspan(*HURDLE, color=BAND, zorder=1)
ax.text(x[0], np.mean(HURDLE), f" pre-tax hurdle {HURDLE[0]:.0%}–{HURDLE[1]:.0%} (assumed)", va="center",
        fontsize=8.4, color=INK2, zorder=2)
lines = [("return_on_capital", SERIES[0], "all physical capital"),
         ("incremental_4q", SERIES[1], "new capital: last year's profit growth / capital added"),
         ("incremental_8q_lag4", SERIES[2], "new capital: 2-year growth / capital added a year earlier")]
for col, colr, lab in lines:
    ax.plot(x, d[col], color=colr, lw=2, marker="o", ms=4, mec=SURF, mew=1, label=lab, zorder=3)
    ax.text(x[-1] + pd.Timedelta(days=20), d[col].iloc[-1], f"{d[col].iloc[-1]:.0%}", va="center",
            fontsize=8.8, color=INK, weight="bold")
ax.axhline(0, color=MUT, lw=.8)
ax.yaxis.set_major_formatter(pct)
ax.set_xlim(x[0] - pd.Timedelta(days=30), x[-1] + pd.Timedelta(days=120))
ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), fontsize=8.6, frameon=False, labelcolor=INK, ncol=3)
ax.set_title("A. Five hyperscalers combined: pre-tax operating income per dollar of physical capital",
             fontsize=11, weight="bold", color=INK, loc="left", pad=30)

# ---- B: per company, before vs now vs new capital
ax = fig.add_subplot(gs[1, 0]); style(ax, grid="x")
names = ["Microsoft", "Alphabet", "Amazon", "Meta", "Oracle"][::-1]
rows = []
for n in names:
    q = P[P.company == n].dropna(subset=["return_on_capital"])
    pre = q[(q.index >= "2019-01-01") & (q.index <= "2021-12-31")].return_on_capital.mean()
    rows.append((pre, q.return_on_capital.iloc[-1], q.incremental_8q.iloc[-1], q.incremental_8q_lag4.iloc[-1]))
rows = np.array(rows)
y = np.arange(len(names))
ax.axvspan(*HURDLE, color=BAND, zorder=1)
for i in range(len(names)):
    ax.plot([min(rows[i]), max(rows[i, :2])], [y[i], y[i]], color=NEUTRAL, lw=1.2, zorder=2)
ax.scatter(rows[:, 0], y, s=46, color=NEUTRAL, edgecolor=SURF, lw=1.5, zorder=3, label="2019–21 average")
ax.scatter(rows[:, 1], y, s=46, color=SERIES[0], edgecolor=SURF, lw=1.5, zorder=4, label="all capital, now")
ax.scatter(rows[:, 2], y, s=46, color=SERIES[1], edgecolor=SURF, lw=1.5, zorder=4, label="new capital, 2 years")
ax.scatter(rows[:, 3], y, s=46, color=SERIES[2], edgecolor=SURF, lw=1.5, zorder=4, marker="D",
           label="new capital, lagged a year")
for i in range(len(names)):
    ax.text(rows[i, 2], y[i] - .32, f"{rows[i, 2]:.0%}", ha="center", fontsize=7.8, color=INK)
ax.set_xscale("symlog", linthresh=1)
ax.set_xlim(0, 2.6)
ax.set_xticks([0, .1, .25, .5, 1, 2], ["0%", "10%", "25%", "50%", "100%", "200%"])
ax.set_yticks(y, names, fontsize=9, color=INK2)
ax.set_ylim(-.7, len(names) - .5)
ax.legend(loc="upper left", bbox_to_anchor=(0, -.1), fontsize=8, frameon=False, labelcolor=INK, ncol=2)
ax.set_title("B. By company: return on capital before the boom,\n     now, and on the capital added since",
             fontsize=11, weight="bold", color=INK, loc="left", pad=8)

# ---- C: hurdle test
ax = fig.add_subplot(gs[1, 1]); style(ax)
labels = [f"needed at {h:.0%}\nhurdle" for h in H.hurdle] + ["last year's\nactual growth"]
vals = list(H.oi_growth_needed / B) + [H.oi_growth_last_year.iloc[0] / B]
cols = [NEUTRAL, NEUTRAL, SERIES[0]]
ax.bar(range(3), vals, .58, color=cols, edgecolor=SURF, lw=2, zorder=3)
for i, v in enumerate(vals):
    ax.text(i, v + 1.5, f"${v:.0f}B", ha="center", va="bottom", fontsize=9.5, color=INK, weight="bold")
ax.set_xticks(range(3), labels, fontsize=8.8, color=INK2)
ax.set_ylim(0, max(vals) * 1.25)
ax.set_ylabel("growth in operating income over 4 quarters, $ billions", fontsize=8.8, color=INK2)
ax.text(0.5, -.2, f"New capital over the next 4 quarters if capex stays at the latest quarter's level: "
        f"\\${H.new_capital_next4q.iloc[0]/B:.0f}B", transform=ax.transAxes, ha="center", fontsize=8.2, color=INK2)
ax.set_title("C. To earn the hurdle on next year's new capital,\n     operating income must grow by…",
             fontsize=11, weight="bold", color=INK, loc="left", pad=8)

fig.suptitle("Returns v1: does the build-out earn its keep?",
             fontsize=13.5, weight="bold", color=INK, x=.07, ha="left", y=.985)
fig.text(.07, .953, "Source: SEC XBRL company facts. Capital = net property and equipment incl. finance-lease assets. "
         "Returns on new capital are upper bounds: they credit all profit growth, including ads and software, to new capital.",
         fontsize=8.5, color=INK2)
fig.savefig("results/returns_v1.png", dpi=145, facecolor=SURF, bbox_inches="tight")
print("saved results/returns_v1.png")
