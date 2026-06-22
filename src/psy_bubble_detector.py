"""
psy_bubble_detector.py
----------------------
Real-time bubble detection via the Phillips-Shi-Yu (2015) GSADF / BSADF test.

A bubble is operationalised as a period in which the log-price departs from a
unit root toward a *mildly explosive* autoregressive root (rho > 1). The test
recursively runs right-tailed ADF regressions over expanding/rolling windows,
takes the supremum (GSADF), and date-stamps episodes by comparing the backward
sup-ADF (BSADF) sequence against simulated critical values.

Implemented from scratch on numpy/statsmodels so there is no black-box
dependency and every step is auditable.

Reference: Phillips, Shi & Yu, "Testing for Multiple Bubbles," International
Economic Review 56(4), 2015.
"""

from __future__ import annotations
import numpy as np
import pandas as pd
import statsmodels.api as sm


# --------------------------------------------------------------------------
# Core ADF regression (right-tailed: we care about the t-stat on the lag level)
# --------------------------------------------------------------------------
def _adf_tstat(y: np.ndarray, lags: int = 0) -> float:
    """t-statistic on the lagged-level coefficient in an ADF regression with
    intercept:  dy_t = a + b*y_{t-1} + sum_i g_i*dy_{t-i} + e_t.
    Explosive alternative => b > 0 => large positive t-stat.

    Fast closed-form path for lags == 0 (a simple bivariate regression, which
    is the dominant case inside the Monte Carlo); general statsmodels path for
    lags > 0."""
    y = np.asarray(y, dtype=float)
    dy = np.diff(y)
    n = len(dy)
    if n <= lags + 2:
        return np.nan

    if lags == 0:
        # Regress dy on [1, x] with x = y_{t-1}; closed-form t-stat on slope.
        x = y[:-1]
        nx = len(x)
        xbar = x.mean()
        xc = x - xbar
        Sxx = xc @ xc
        if Sxx <= 0:
            return np.nan
        b = (xc @ (dy - dy.mean())) / Sxx
        a = dy.mean() - b * xbar
        resid = dy - (a + b * x)
        dof = nx - 2
        if dof <= 0:
            return np.nan
        s2 = (resid @ resid) / dof
        se_b = np.sqrt(s2 / Sxx)
        if se_b == 0 or not np.isfinite(se_b):
            return np.nan
        return float(b / se_b)

    # General case with lagged differences
    y_lag = y[lags:-1]
    rows = n - lags
    X = [np.ones(rows), y_lag]
    for i in range(1, lags + 1):
        X.append(dy[lags - i: -i])
    X = np.column_stack(X)
    Y = dy[lags:]
    try:
        res = sm.OLS(Y, X).fit()
        return float(res.tvalues[1])
    except Exception:
        return np.nan


# --------------------------------------------------------------------------
# SADF / GSADF / BSADF
# --------------------------------------------------------------------------
def bsadf_sequence(y: np.ndarray, r0: float | None = None, lags: int = 0) -> np.ndarray:
    """Backward sup-ADF sequence. For each end point r2, take the sup over all
    start points r1 in [0, r2 - r0]. Returns an array aligned to y (NaN before
    the minimum window is available)."""
    y = np.asarray(y, dtype=float)
    T = len(y)
    if r0 is None:
        r0 = 0.01 + 1.8 / np.sqrt(T)        # PSY rule-of-thumb minimum window
    min_w = int(np.floor(r0 * T))
    out = np.full(T, np.nan)
    for r2 in range(min_w, T + 1):
        best = -np.inf
        for r1 in range(0, r2 - min_w + 1):
            stat = _adf_tstat(y[r1:r2], lags=lags)
            if np.isfinite(stat) and stat > best:
                best = stat
        out[r2 - 1] = best
    return out


def gsadf_stat(y: np.ndarray, r0: float | None = None, lags: int = 0) -> float:
    """The GSADF statistic = sup of the BSADF sequence."""
    seq = bsadf_sequence(y, r0=r0, lags=lags)
    return float(np.nanmax(seq))


# --------------------------------------------------------------------------
# Monte Carlo critical values under the unit-root null
# --------------------------------------------------------------------------
def simulate_critical_values(T: int, r0: float | None = None, lags: int = 0,
                             n_sims: int = 299, quantiles=(0.90, 0.95, 0.99),
                             seed: int = 0):
    """Simulate the GSADF null distribution (random walk) and return the
    requested quantiles for both the scalar GSADF stat and the BSADF sequence
    (the latter used for date-stamping)."""
    rng = np.random.default_rng(seed)
    if r0 is None:
        r0 = 0.01 + 1.8 / np.sqrt(T)
    gsadf_draws = np.empty(n_sims)
    bsadf_draws = np.full((n_sims, T), np.nan)
    for s in range(n_sims):
        e = rng.standard_normal(T)
        y = np.cumsum(e)                    # driftless random walk = the null
        seq = bsadf_sequence(y, r0=r0, lags=lags)
        bsadf_draws[s] = seq
        gsadf_draws[s] = np.nanmax(seq)
    gsadf_cv = {q: float(np.quantile(gsadf_draws, q)) for q in quantiles}
    # Pointwise BSADF critical-value sequence (the date-stamping benchmark)
    bsadf_cv = {q: np.nanquantile(bsadf_draws, q, axis=0) for q in quantiles}
    return gsadf_cv, bsadf_cv


# --------------------------------------------------------------------------
# Top-level convenience wrapper
# --------------------------------------------------------------------------
def detect_bubbles(prices: pd.Series, lags: int = 0, n_sims: int = 299,
                   alpha: float = 0.95, log: bool = True, seed: int = 0):
    """Run the full PSY procedure on a price series.

    Returns a DataFrame indexed like `prices` with the BSADF stat, the
    date-stamping critical value, and a boolean `bubble` flag, plus a summary
    dict (GSADF stat, its critical value, and whether the whole-sample test
    rejects the no-bubble null)."""
    s = prices.dropna()
    y = np.log(s.values) if log else s.values.astype(float)
    T = len(y)

    bsadf = bsadf_sequence(y, lags=lags)
    gsadf = float(np.nanmax(bsadf))
    gsadf_cv, bsadf_cv = simulate_critical_values(T, lags=lags, n_sims=n_sims,
                                                  quantiles=(alpha,), seed=seed)

    cv_seq = bsadf_cv[alpha]
    df = pd.DataFrame({
        "value": s.values,
        "bsadf": bsadf,
        "cv": cv_seq,
    }, index=s.index)
    df["bubble"] = df["bsadf"] > df["cv"]

    summary = {
        "gsadf_stat": gsadf,
        "gsadf_cv": gsadf_cv[alpha],
        "alpha": alpha,
        "reject_no_bubble_null": bool(gsadf > gsadf_cv[alpha]),
        "n_obs": T,
    }
    return df, summary


# --------------------------------------------------------------------------
# Date-stamping helper: contiguous bubble episodes (with a min duration filter)
# --------------------------------------------------------------------------
def episodes(df: pd.DataFrame, min_len: int = 3):
    """Extract contiguous (start, end) bubble episodes lasting >= min_len."""
    flags = df["bubble"].values
    idx = df.index
    out, start = [], None
    for i, f in enumerate(flags):
        if f and start is None:
            start = i
        elif not f and start is not None:
            if i - start >= min_len:
                out.append((idx[start], idx[i - 1]))
            start = None
    if start is not None and len(flags) - start >= min_len:
        out.append((idx[start], idx[-1]))
    return out
