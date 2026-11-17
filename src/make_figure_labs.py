"""Figure for labs.py. Run from repo root after labs.py."""
import os
import pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

SURF, INK, INK2, MUT = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8984"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
s = pd.read_csv("results/labs_openai_scenarios.csv")
COL = {"fixed": ORANGE, "other_flex": BLUE, "half_flex": AQUA}
LAB = {"fixed": "all planned costs fixed", "other_flex": "compute fixed, other costs flex",
       "half_flex": "half of compute flexes too"}


def style(ax):
    ax.set_facecolor(SURF)
    for sp in ("top", "right"): ax.spines[sp].set_visible(False)
    for sp in ("left", "bottom"): ax.spines[sp].set_color(MUT)
    ax.tick_params(colors=INK2, labelsize=9)
    ax.grid(alpha=.18, lw=.6, color=MUT); ax.set_axisbelow(True)


fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 5.6), facecolor=SURF, gridspec_kw={"wspace": .25})
x = s.growth * 100
for c in ("fixed", "other_flex", "half_flex"):
    a1.plot(x, s[f"to_raise_{c}"], color=COL[c], lw=2, marker="o", ms=7, mec=SURF, mew=1.5, label=LAB[c])
plan = s[s.is_plan].iloc[0]
a1.annotate(f"the plan: ${plan.to_raise_fixed:.0f}B more\non top of the $122B raised",
            (plan.growth * 100, plan.to_raise_fixed), xytext=(-235, -48), textcoords="offset points",
            fontsize=9, color=INK, arrowprops=dict(arrowstyle="-", color=MUT, lw=.8))
a1.set_xlabel("average annual revenue growth, 2027–2030 (%)", fontsize=9.5, color=INK2)
a1.set_ylabel("money still to raise by 2030 ($B)", fontsize=9.5, color=INK2)
a1.set_ylim(0, s.to_raise_fixed.max() * 1.12)
a1.set_title("A. OpenAI's funding need by revenue growth", fontsize=11, weight="bold", color=INK, loc="left")
a1.legend(fontsize=8.6, frameon=False, labelcolor=INK, loc="upper right"); style(a1)

a2.bar(x, s.compute_cut_half_flex.clip(lower=0), width=6, color=AQUA, edgecolor=SURF, lw=2, zorder=3)
for xi, v in zip(x, s.compute_cut_half_flex.clip(lower=0)):
    if v > 1: a2.text(xi, v + 5, f"${v:.0f}B", ha="center", fontsize=8.6, color=INK)
a2.set_xlabel("average annual revenue growth, 2027–2030 (%)", fontsize=9.5, color=INK2)
a2.set_ylabel("compute not bought vs the \\$856B plan (\\$B)", fontsize=9.5, color=INK2)
a2.set_title("B. If OpenAI cuts compute instead: lost revenue for\n     its suppliers (half of compute flexes)",
             fontsize=11, weight="bold", color=INK, loc="left"); style(a2)

fig.suptitle("The demand end: OpenAI must raise far more, or its suppliers sell far less",
             fontsize=13.5, weight="bold", color=INK, x=.07, ha="left", y=1.02)
fig.text(.07, .955, "Scenario model on REPORTED projections (FT, Sept 2026: \\$840B revenue, \\$856B compute, \\$262B other "
         "costs, 2026–30). Not filed data. Revenue starts at \\$36B in 2026.", fontsize=8.5, color=INK2)
fig.savefig("results/labs_openai_v1.png", dpi=145, facecolor=SURF, bbox_inches="tight")
print("saved")
