"""Figure for the 6 Nov 2026 update. Run from repo root after nvda_valuation.py and
oos_realtime.py (both samples). Encoding: BLUE = v3 / the object we trust,
ORANGE = the alternative it is compared against, GRAY = price."""
import pickle
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

SURF, INK, INK2, MUT = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8984"
BLUE, ORANGE = "#2a78d6", "#eb6834"

val = pickle.load(open("results/nvda_valuation.pkl", "rb"))
same = pickle.load(open("results/nvda_price_samewindow.pkl", "rb"))
lv = val["lv"]
px = (pd.read_csv("data/nvda_us_d.csv", parse_dates=["Date"]).set_index("Date").sort_index()
        ["Close"].resample("W-FRI").last().dropna())
px = px.reindex(lv.index)
rev = np.exp(np.log(px) - lv)                       # TTM revenue implied, same units
idx = lambda s: 100 * s / s.iloc[0]
rt3 = pd.read_csv("results/oos_realtime.csv", parse_dates=["as_of"])
rtF = pd.read_csv("results/oos_realtime_fullhistory.csv", parse_dates=["as_of"])


def style(ax, ygrid=True):
    ax.set_facecolor(SURF)
    for sp in ("top", "right"): ax.spines[sp].set_visible(False)
    for sp in ("left", "bottom"): ax.spines[sp].set_color(MUT)
    ax.tick_params(colors=INK2, labelsize=9)
    ax.grid(axis="y" if ygrid else "both", alpha=.18, lw=.6, color=MUT); ax.set_axisbelow(True)


fig = plt.figure(figsize=(12.5, 12.2), facecolor=SURF)
gs = fig.add_gridspec(3, 1, height_ratios=[1.25, .95, .95], hspace=.48)

# ---- A: price vs revenue, common base
ax = fig.add_subplot(gs[0]); style(ax)
ax.plot(lv.index, idx(px), color=INK2, lw=1.6, zorder=3)
ax.plot(lv.index, idx(rev), color=BLUE, lw=2.2, zorder=4)
ax.set_yscale("log")
for a, b in same["eps"]:
    ax.axvspan(a, b, color=ORANGE, alpha=.14, lw=0, zorder=1)
ax.annotate(f"price ×{px.iloc[-1]/px.iloc[0]:.0f}", (lv.index[-1], idx(px).iloc[-1]),
            xytext=(6, 0), textcoords="offset points", va="center", fontsize=9.5,
            color=INK2, weight="bold")
ax.annotate(f"revenue ×{rev.iloc[-1]/rev.iloc[0]:.0f}", (lv.index[-1], idx(rev).iloc[-1]),
            xytext=(6, 0), textcoords="offset points", va="center", fontsize=9.5,
            color=BLUE, weight="bold")
ax.set_xlim(lv.index[0], lv.index[-1] + pd.Timedelta(days=330))
ax.set_ylabel("index, Mar 2012 = 100 (log)", fontsize=9.5, color=INK2)
ax.set_title("A. NVDA price vs trailing-12-month revenue (as filed with the SEC)",
             fontsize=11, weight="bold", color=INK, loc="left", pad=8)
ax.legend(handles=[Line2D([0], [0], color=INK2, lw=1.6, label="price"),
                   Line2D([0], [0], color=BLUE, lw=2.2, label="revenue, dated by filing"),
                   Patch(fc=ORANGE, alpha=.14, label="explosive episode: test on PRICE")],
          loc="upper left", fontsize=8.6, frameon=False, labelcolor=INK)

# ---- B: the multiple
ax = fig.add_subplot(gs[1], sharex=ax); style(ax)
ps = np.exp(lv); ps = ps / ps.median()
ax.plot(ps.index, ps, color=BLUE, lw=1.8, zorder=3)
ax.axhline(1, color=INK2, lw=1, ls="--", zorder=2)
ax.text(ps.index[2], 1.04, "2012–26 median", fontsize=8.3, color=INK2, va="bottom")
oct_peak = ps["2026-10"].idxmax()
for t, lab in ((oct_peak, "Oct 2026 peak"), (ps.index[-1], "5 Nov 2026")):
    pct = (ps < ps.loc[t]).mean()
    ax.plot([t], [ps.loc[t]], "o", ms=8, color=BLUE, mec=SURF, mew=2, zorder=5)
    ax.annotate(f"{lab}: {pct:.0%} pctile", (t, ps.loc[t]), xytext=(8, 10 if "Oct" in lab else -16),
                textcoords="offset points", fontsize=8.8, color=INK, weight="bold")
ax.set_ylabel("price / revenue, × median", fontsize=9.5, color=INK2)
ax.set_title(f"B. The same test on price ÷ revenue: no explosive episode at all "
             f"(whole-sample p = {val['p']:.2f})", fontsize=11, weight="bold", color=INK,
             loc="left", pad=8)

# ---- C: real-time replay, margin over the critical value
ax = fig.add_subplot(gs[2]); style(ax)
for df, col, lab, mk in ((rt3, BLUE, "v3's sample (from 2009): the pre-registered test", "o"),
                         (rtF, ORANGE, "full history (from 1999 IPO)", "s")):
    d = df[df.series == "NVDA"].sort_values("as_of")
    m = d.bsadf_last - d.cv_last
    ax.plot(d.as_of, m, color=col, lw=2, marker=mk, ms=8, mec=SURF, mew=1.5, label=lab, zorder=3)
ax.axhline(0, color=INK, lw=1.2, zorder=2)
ax.text(rt3.as_of.min(), .03, "above 0 = flagged explosive", fontsize=8.3, color=INK2, va="bottom")
ax.set_ylabel("test statistic − critical value", fontsize=9.5, color=INK2)
ax.set_title("C. Real-time replay, week by week, NVDA price: the verdict depends on where "
             "the sample starts", fontsize=11, weight="bold", color=INK, loc="left", pad=8)
ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter("%d %b"))
ax.legend(loc="lower left", fontsize=8.6, frameon=False, labelcolor=INK)

fig.suptitle("NVDA after the 5 Nov sell-off: no valuation bubble on the evidence; "
             "price verdict not robust", fontsize=13.5, weight="bold", color=INK,
             x=.07, ha="left", y=.975)
fig.text(.07, .945, "Weekly closes to 5 Nov 2026 (Yahoo Finance). Revenue: SEC XBRL, each "
         "quarter dated by first filing. Wild-bootstrap GSADF (B = 499), 52-week family-wise "
         "critical values. Code frozen at v3.", fontsize=8.6, color=INK2)
fig.savefig("results/v31_nov2026.png", dpi=145, facecolor=SURF, bbox_inches="tight")
print("saved results/v31_nov2026.png")
