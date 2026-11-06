"""
demo_simulated_bubble.py
------------------------
Self-verifying demo: we PLANT an explosive bubble (with a known start/end) in
an otherwise random-walk series, then check the PSY/BSADF detector recovers it.
This is the validation step -- before trusting it on real data, confirm it can
find a bubble whose location we already know.

To use on REAL data instead, replace `make_series()` with a one-liner:
    prices = pd.read_csv("nvda.csv", parse_dates=["date"], index_col="date")["close"]
    df, summary = detect_bubbles(prices)
(any clean price Series with a datetime or integer index works).
"""

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from psy_bubble_detector import detect_bubbles, episodes

# Write the validation plot to examples/ (next to the committed copy),
# regardless of the directory the demo is run from.
OUT_PATH = Path(__file__).resolve().parent.parent / "examples" / "bubble_detection_demo.png"


def make_series(T=200, b_start=100, b_end=140, rho=1.06, seed=7):
    """Random walk, then a mildly explosive (rho>1) bubble, then a collapse,
    then random walk again. The bubble lives in [b_start, b_end]."""
    rng = np.random.default_rng(seed)
    y = np.zeros(T)
    for t in range(1, T):
        if b_start <= t < b_end:
            y[t] = rho * y[t - 1] + rng.normal(0, 0.5)      # explosive
        elif t == b_end:
            y[t] = y[t - 1] * 0.4 + rng.normal(0, 0.5)       # collapse
        else:
            y[t] = y[t - 1] + rng.normal(0, 0.5)             # unit root
    level = 100 + y                                          # shift to positive
    idx = pd.RangeIndex(T, name="t")
    return pd.Series(level, index=idx, name="price")


def main():
    prices = make_series()
    true_window = (100, 140)

    # log=False here because the simulated series is already in "log-like" space
    df, summary = detect_bubbles(prices, lags=0, n_sims=99, alpha=0.95,
                                 log=False, seed=0)

    print("=== GSADF whole-sample test ===")
    print(f"  GSADF stat        : {summary['gsadf_stat']:.3f}")
    print(f"  95% critical value: {summary['gsadf_cv']:.3f}")
    print(f"  Reject no-bubble  : {summary['reject_no_bubble_null']}")
    print(f"  n_obs             : {summary['n_obs']}")

    eps = episodes(df, min_len=3)
    print("\n=== Date-stamped explosive episodes (BSADF > 95% cv) ===")
    print(f"  TRUE planted bubble: t in [{true_window[0]}, {true_window[1]}]")
    for a, b in eps:
        print(f"  detected           : t in [{a}, {b}]")

    # ---- plot ----
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6), sharex=True,
                                   gridspec_kw={"height_ratios": [2, 1]})
    ax1.plot(df.index, df["value"], color="#1b3a5b", lw=1.4)
    ax1.axvspan(*true_window, color="#cde", alpha=0.5, label="true bubble (planted)")
    for a, b in eps:
        ax1.axvspan(a, b, color="#e23", alpha=0.18)
    ax1.set_title("PSY / GSADF bubble detector — validation on a planted bubble",
                  fontsize=12, fontweight="bold")
    ax1.set_ylabel("price")
    ax1.legend(loc="upper left", fontsize=9)

    ax2.plot(df.index, df["bsadf"], color="#1b3a5b", lw=1.2, label="BSADF statistic")
    ax2.plot(df.index, df["cv"], color="#e23", lw=1.0, ls="--", label="95% critical value")
    ax2.fill_between(df.index, df["bsadf"], df["cv"],
                     where=df["bubble"], color="#e23", alpha=0.18)
    ax2.set_ylabel("BSADF")
    ax2.set_xlabel("t")
    ax2.legend(loc="upper left", fontsize=9)

    fig.tight_layout()
    fig.savefig(OUT_PATH, dpi=140)
    print(f"\nSaved plot -> {OUT_PATH}")


if __name__ == "__main__":
    main()
