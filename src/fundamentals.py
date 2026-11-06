"""
fundamentals.py -- "a bubble relative to WHAT?"

Every bubble test is a joint test of (i) a bubble and (ii) a model of
fundamentals (Fama's joint-hypothesis problem). Testing raw log price, as v1/v2
did, silently assumes fundamentals are CONSTANT -- the worst available model.
Explosive earnings then read as an explosive bubble.

This module (a) demonstrates the confound by simulation and (b) provides the
look-ahead-free valuation-ratio transform needed to test the right object.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

from fast_psy import bsadf_fast, _min_obs_from_r0
from psy_v3 import wild_paths


# ---------------------------------------------------------------------------
# (a) Boom vs bubble simulation
# ---------------------------------------------------------------------------
def simulate_world(kind: str, T: int = 400, start: int = 240, end: int = 320,
                   rho: float = 1.004, rng=None):
    """Return (log_price, log_fundamental).

    'null'   : fundamentals a random walk; valuation (log P/F) stationary.
    'boom'   : FUNDAMENTALS are mildly explosive in [start, end); valuation stationary.
               Prices explode because earnings explode. Not a bubble.
    'bubble' : fundamentals a random walk; VALUATION is mildly explosive in
               [start, end), then collapses. Prices explode on multiple expansion.
    Both non-null worlds generate equally explosive price paths by construction.
    """
    rng = rng or np.random.default_rng()
    f = np.empty(T); v = np.empty(T)
    f[0], v[0] = 3.0, 3.0                      # log fundamentals, log multiple (~20x)
    for t in range(1, T):
        epi = start <= t < end
        f[t] = (rho * f[t-1] if (kind == "boom" and epi) else f[t-1]) + rng.normal(0, .03)
        if kind == "bubble" and epi:
            v[t] = rho * v[t-1] + rng.normal(0, .01)
        elif kind == "bubble" and t == end:
            v[t] = 3.0 + rng.normal(0, .01)    # collapse back to the long-run multiple
        else:
            v[t] = 3.0 + 0.95 * (v[t-1] - 3.0) + rng.normal(0, .01)
    return f + v, f


def boom_vs_bubble_study(M: int = 300, T: int = 400, seed: int = 0, alpha: float = .05):
    """Warp-speed wild-bootstrap rejection rates of GSADF on PRICE vs on VALUATION."""
    rng = np.random.default_rng(seed); mo = _min_obs_from_r0(T)
    out = {}
    for kind in ("null", "boom", "bubble"):
        stats = {"price": [], "ratio": []}; boots = {"price": [], "ratio": []}
        for _ in range(M):
            lp, lf = simulate_world(kind, T, rng=rng)
            for name, s in (("price", lp), ("ratio", lp - lf)):
                stats[name].append(np.nanmax(bsadf_fast(s, mo)))
                b = wild_paths(s, 1, seed=int(rng.integers(1 << 31)))[0]
                boots[name].append(np.nanmax(bsadf_fast(b, mo)))
        out[kind] = {n: float(np.mean(np.array(stats[n]) >
                                      np.quantile(boots[n], 1 - alpha)))
                     for n in ("price", "ratio")}
    return out


# ---------------------------------------------------------------------------
# (b) Look-ahead-free valuation ratio for real data
# ---------------------------------------------------------------------------
def ttm_available(fund: pd.DataFrame) -> pd.Series:
    """Trailing-twelve-month fundamental, indexed by the date it became PUBLIC.

    fund: columns ['period_end', 'filed', 'value'] with one row per fiscal quarter
    (three-month values). A TTM value is only usable from its filing date, which
    removes look-ahead bias: the market could not price revenue it had not seen.
    """
    f = fund.sort_values("period_end").reset_index(drop=True)
    f["ttm"] = f["value"].rolling(4).sum()
    # All four quarters must be public: availability = latest filing in the window.
    # Deliberately NOT done via an int64 round-trip: pandas may store datetimes in
    # us or ns depending on version, and a unit mix-up silently moves every filing
    # to 1970 -- i.e. total look-ahead. tests/test_v3.py guards this.
    filed = pd.to_datetime(f["filed"])
    f["avail"] = [filed.iloc[max(0, i - 3): i + 1].max() for i in range(len(f))]
    f = f.dropna(subset=["ttm"])
    s = pd.Series(f["ttm"].values, index=pd.to_datetime(f["avail"])).sort_index()
    return s.groupby(level=0).last()        # same-day filings: keep the latest


def log_valuation(px: pd.Series, fund: pd.DataFrame, shares: pd.Series | None = None):
    """log(price / TTM fundamental per share), aligned to px's index as-of each date.

    If `shares` (split-adjusted, indexed by availability date) is omitted, the ratio
    is price / TTM fundamental -- a per-share proxy that is exact only if the share
    count is constant. Report that caveat whenever shares are omitted.
    """
    ttm = ttm_available(fund)
    num = np.log(px)
    den = np.log(ttm.reindex(px.index, method="ffill"))
    if shares is not None:
        den = den - np.log(shares.reindex(px.index, method="ffill"))
    return (num - den).dropna()
