"""
psy_v3.py -- explosive-root testing that survives a hostile referee.

Changes from v2, each answering a specific defect (see REFEREE_REPORT_v2.md):

  R2  NULL MODEL.  v2 simulated critical values under a homoskedastic Gaussian
      random walk. Real returns cluster in volatility, and right-tailed unit-root
      tests are known to over-reject under time-varying volatility
      (Harvey, Leybourne, Sollis & Taylor 2016, J. Empirical Finance).
      v3 uses an order-preserving Rademacher WILD BOOTSTRAP of the series' own
      first differences: y*_t = sum_{s<=t} w_s * e_s,  w_s = +/-1.
      This keeps the sample's actual volatility path (the calm years stay calm,
      the violent years stay violent) while imposing the unit-root null.

  R9  MULTIPLICITY IN TIME.  v2 compared BSADF to a *pointwise* 95% critical
      value every week. Over ~900 weeks that guarantees a steady drip of false
      flags. v3 follows the logic of Phillips & Shi (2020): the critical value
      at date t is the bootstrap 95% quantile of the null's MAXIMUM BSADF over
      the trailing window (default 52 weeks), so a false flag *anywhere* in a
      given year has probability ~5%. Validated empirically in tests/.

  MIN DURATION.  v2 used ad-hoc minimum episode lengths (4, 15). v3 uses the
      PSY rule: an episode must last at least ceil(log T) observations.

  R5  EVALUATION.  v2 measured "price at first alarm vs price today", a window
      containing -54% and -66% crashes. v3 evaluates each dated episode on its
      own: gain from detection to peak, drawdown from peak to the date the test
      declares the episode over, and what happens after.
"""

from __future__ import annotations
import math
import numpy as np
import pandas as pd

from fast_psy import bsadf_fast, _min_obs_from_r0


# ---------------------------------------------------------------------------
# Nulls
# ---------------------------------------------------------------------------
def gaussian_null_bsadf(T: int, B: int, seed: int = 0, r0=None) -> np.ndarray:
    """v2's null: homoskedastic Gaussian random walk. Kept for comparison."""
    rng = np.random.default_rng(seed)
    mo = _min_obs_from_r0(T, r0)
    return np.vstack([bsadf_fast(np.cumsum(rng.standard_normal(T)), mo)
                      for _ in range(B)])


def wild_paths(y: np.ndarray, B: int, seed: int = 0) -> np.ndarray:
    """(B, T) wild-bootstrap level paths under the unit-root null, preserving the
    time ordering -- and therefore the volatility path -- of the increments."""
    y = np.asarray(y, float)
    e = np.diff(y)
    e = e - e.mean()                       # the ADF regression carries an intercept
    rng = np.random.default_rng(seed)
    w = rng.choice(np.array([-1.0, 1.0]), size=(B, e.size))
    return np.hstack([np.zeros((B, 1)), np.cumsum(w * e, axis=1)])


def wild_null_bsadf(y: np.ndarray, B: int, seed: int = 0, r0=None) -> np.ndarray:
    T = len(y)
    mo = _min_obs_from_r0(T, r0)
    return np.vstack([bsadf_fast(p, mo) for p in wild_paths(y, B, seed)])


# ---------------------------------------------------------------------------
# Critical values
# ---------------------------------------------------------------------------
def gsadf_pvalue(obs_bsadf: np.ndarray, null_bsadf: np.ndarray) -> float:
    """Right-tailed bootstrap p-value of the whole-sample GSADF statistic."""
    stat = np.nanmax(obs_bsadf)
    nulls = np.nanmax(null_bsadf, axis=1)
    return float((1 + np.sum(nulls >= stat)) / (1 + nulls.size))


def pointwise_cv(null_bsadf: np.ndarray, alpha: float = 0.05) -> np.ndarray:
    """v2-style date-stamping benchmark (no multiplicity control)."""
    return np.nanquantile(null_bsadf, 1 - alpha, axis=0)


def familywise_cv(null_bsadf: np.ndarray, window: int = 52,
                  alpha: float = 0.05) -> np.ndarray:
    """Time-varying critical value controlling the probability of ANY false flag
    within the trailing `window` observations at ~alpha."""
    df = pd.DataFrame(null_bsadf.T)                      # T x B
    roll = df.rolling(window, min_periods=1).max().to_numpy().T
    return np.nanquantile(roll, 1 - alpha, axis=0)


# ---------------------------------------------------------------------------
# Date-stamping
# ---------------------------------------------------------------------------
def min_duration(T: int) -> int:
    """PSY minimum-duration rule: an episode must last >= log(T) observations."""
    return int(math.ceil(math.log(T)))


def date_episodes(bsadf: np.ndarray, cv: np.ndarray, min_len: int):
    """Return [(origination_i, last_flag_i, termination_i)]; termination is the
    first unflagged observation after the run (None if still running)."""
    flag = np.isfinite(bsadf) & np.isfinite(cv) & (bsadf > cv)
    eps, start = [], None
    for i, f in enumerate(flag):
        if f and start is None:
            start = i
        elif not f and start is not None:
            if i - start >= min_len:
                eps.append((start, i - 1, i))
            start = None
    if start is not None and len(flag) - start >= min_len:
        eps.append((start, len(flag) - 1, None))
    return eps, flag


# ---------------------------------------------------------------------------
# Per-episode evaluation (what a user of the detector would actually live through)
# ---------------------------------------------------------------------------
def episode_table(px: pd.Series, eps, horizon: int = 52) -> pd.DataFrame:
    rows = []
    v = px.values
    for o, last, term in eps:
        end = last if term is None else term
        pk = o + int(np.argmax(v[o:end + 1]))
        row = dict(
            origination=px.index[o].date(),
            peak=px.index[pk].date(),
            termination=None if term is None else px.index[term].date(),
            weeks=end - o + 1,
            gain_detect_to_peak=v[pk] / v[o] - 1,
        )
        if term is None:
            row.update(dd_peak_to_termination=v[-1] / v[pk] - 1, exit_lag_weeks=None,
                       fwd_after_termination=None, maxdd_after_termination=None,
                       still_running=True)
        else:
            fut = v[term:min(term + horizon, len(v))]
            row.update(
                dd_peak_to_termination=v[term] / v[pk] - 1,
                exit_lag_weeks=term - pk,
                fwd_after_termination=(fut[-1] / v[term] - 1) if fut.size > 1 else None,
                maxdd_after_termination=(fut.min() / v[term] - 1) if fut.size > 1 else None,
                still_running=False,
            )
        rows.append(row)
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Multiple testing across a battery of series
# ---------------------------------------------------------------------------
def benjamini_hochberg(pvals: dict, alpha: float = 0.05):
    """{key: (p, q, reject)} under Benjamini-Hochberg step-up FDR control."""
    keys = list(pvals)
    p = np.array([pvals[k] for k in keys], float)
    n = len(p); order = np.argsort(p); q = np.empty(n); prev = 1.0
    for rank in range(n - 1, -1, -1):
        i = order[rank]
        prev = min(prev, p[i] * n / (rank + 1))
        q[i] = min(prev, 1.0)
    return {k: (float(p[j]), float(q[j]), bool(q[j] <= alpha)) for j, k in enumerate(keys)}
