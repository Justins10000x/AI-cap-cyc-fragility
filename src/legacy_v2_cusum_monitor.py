"""
SUPERSEDED -- retained for provenance only. Do not use for inference.

This is the v2 CUSUM-on-BSADF monitor. docs/REFEREE_REPORT_v2.md documents why it
was withdrawn: its log-likelihood ratio treats a strongly dependent statistic as
i.i.d. (so the claimed Lorden/Pollak optimality does not hold), it was calibrated at
T=300 and applied at T=865-1126, and its Gaussian null over-rejects 3-4x under
realistic volatility. Replaced by src/psy_v3.py.
"""
"""
fragility_monitor.py
--------------------
Sequential change-point detection layered on the PSY/GSADF explosive-root test.

WHY THIS EXISTS
---------------
A GSADF date-stamp is a *binary flag*: explosive or not, at each date. That is a
score, not a decision rule, and it carries no statement about how often it lies.
This module converts the flag stream into three sequential detectors whose error
behaviour is characterised by simulation:

  * Shiryaev posterior      -- Bayesian P(regime change has occurred | data so far)
  * Page CUSUM              -- asymptotically optimal under Lorden's criterion
  * Shiryaev-Roberts        -- asymptotically optimal under Pollak's criterion

Each is a threshold rule. The threshold is chosen from a simulated operating
curve so we can state: "at this threshold, expect one false alarm per X years,
and expect to detect a true change in Y periods."

THE SERIAL-DEPENDENCE PROBLEM (important)
-----------------------------------------
Textbook CUSUM/SR average-run-length formulas assume i.i.d. observations. The
BSADF sequence is emphatically NOT i.i.d. -- consecutive values share almost all
of their estimation window, so the stream is strongly autocorrelated even under
the null. Any ARL taken from a textbook formula would be badly wrong.

We therefore never use a closed-form ARL. Every operating characteristic here is
obtained by Monte Carlo on the *actual* null process: simulate a driftless random
walk, run it through the identical BSADF pipeline, run the detector, record the
time to first alarm. The dependence is inherited automatically and no
independence assumption is made anywhere.

STANDARDISATION
---------------
BSADF has a nonstandard, time-varying null distribution. We standardise
pointwise against simulated null moments:  z_t = (bsadf_t - m_t) / s_t, so that
under the null z_t is approximately N(0,1) marginally (though still dependent
across t). The post-change model is N(delta, 1): `delta` is the minimum shift in
explosiveness we care to detect, chosen in advance, not fitted.

Log-likelihood ratio for N(delta,1) vs N(0,1) at z:   delta*z - delta^2/2
"""

from __future__ import annotations
import numpy as np
import pandas as pd

from fast_psy import bsadf_fast, _min_obs_from_r0


# ---------------------------------------------------------------------------
# Null simulation: pointwise moments of the BSADF stream + stored paths
# ---------------------------------------------------------------------------
def simulate_null_bsadf(T: int, n_sims: int = 500, r0: float | None = None,
                        seed: int = 0) -> np.ndarray:
    """Return (n_sims, T) array of BSADF sequences under a driftless random walk."""
    rng = np.random.default_rng(seed)
    min_obs = _min_obs_from_r0(T, r0)
    out = np.full((n_sims, T), np.nan)
    for s in range(n_sims):
        w = np.cumsum(rng.standard_normal(T))
        out[s] = bsadf_fast(w, min_obs)
    return out


def null_moments(null_paths: np.ndarray):
    """Pointwise mean and sd of the BSADF statistic under the null."""
    m = np.nanmean(null_paths, axis=0)
    s = np.nanstd(null_paths, axis=0)
    s = np.where((s > 1e-8) & np.isfinite(s), s, np.nan)
    return m, s


def standardize(bsadf: np.ndarray, m: np.ndarray, s: np.ndarray) -> np.ndarray:
    """z_t = (bsadf_t - m_t)/s_t ; NaN where undefined."""
    with np.errstate(invalid="ignore", divide="ignore"):
        z = (bsadf - m) / s
    return np.where(np.isfinite(z), z, np.nan)


# ---------------------------------------------------------------------------
# The three detectors. Each consumes a standardized stream z and returns a
# statistic aligned to it.
# ---------------------------------------------------------------------------
def shiryaev_posterior(z: np.ndarray, delta: float = 1.0,
                       rho: float = 1 / 250.0) -> np.ndarray:
    """Bayesian posterior P(change occurred by t | z_1..z_t).

    Geometric prior on the change time with per-period hazard `rho`
    (default 1/250 ~ one regime change per 250 periods a priori).

    Recursion, with Lambda_t the likelihood ratio:
        pi_t~ = p_{t-1} + (1 - p_{t-1}) * rho          (prior-predictive)
        p_t   = pi_t~ L_t / (pi_t~ L_t + (1 - pi_t~))
    """
    p = np.full(len(z), np.nan)
    cur = 0.0
    for t, zt in enumerate(z):
        if not np.isfinite(zt):
            continue
        pre = cur + (1.0 - cur) * rho
        # L = exp(delta*z - delta^2/2); work in a numerically safe form
        loglr = delta * zt - 0.5 * delta * delta
        # p = pre*L / (pre*L + (1-pre))  ==  1/(1 + (1-pre)/(pre*L))
        with np.errstate(over="ignore"):
            odds = (pre / max(1.0 - pre, 1e-300)) * np.exp(np.clip(loglr, -700, 700))
        cur = odds / (1.0 + odds)
        cur = min(max(cur, 0.0), 1.0 - 1e-12)
        p[t] = cur
    return p


def cusum(z: np.ndarray, delta: float = 1.0) -> np.ndarray:
    """Page's CUSUM on the log-likelihood ratio: S_t = max(0, S_{t-1} + llr_t)."""
    S = np.full(len(z), np.nan)
    cur = 0.0
    for t, zt in enumerate(z):
        if not np.isfinite(zt):
            continue
        cur = max(0.0, cur + delta * zt - 0.5 * delta * delta)
        S[t] = cur
    return S


def shiryaev_roberts(z: np.ndarray, delta: float = 1.0) -> np.ndarray:
    """Shiryaev-Roberts statistic R_t = (1 + R_{t-1}) * Lambda_t, returned as
    log(1+R) to stay numerically stable over long samples."""
    out = np.full(len(z), np.nan)
    logR = -np.inf                       # R = 0
    for t, zt in enumerate(z):
        if not np.isfinite(zt):
            continue
        loglr = delta * zt - 0.5 * delta * delta
        # log(1+R) then + loglr
        log1pR = np.logaddexp(0.0, logR)
        logR = log1pR + loglr
        logR = min(logR, 700.0)
        out[t] = log1pR + loglr
    return out


# ---------------------------------------------------------------------------
# Operating characteristics by Monte Carlo (no i.i.d. assumption)
# ---------------------------------------------------------------------------
def _first_alarm(stat: np.ndarray, h: float) -> int | None:
    idx = np.where(np.isfinite(stat) & (stat > h))[0]
    return int(idx[0]) if idx.size else None


def arl0_curve(null_paths: np.ndarray, m, s, thresholds, detector="cusum",
               delta: float = 1.0, rho: float = 1 / 250.0):
    """Average run length to FALSE alarm, per threshold, under the null.

    Runs of length T that never alarm are right-censored; we report both the
    mean over alarming paths and the fraction of paths that ever alarm, which
    together are more honest than a single censored mean.
    """
    T = null_paths.shape[1]
    res = {}
    stats = []
    for path in null_paths:
        z = standardize(path, m, s)
        if detector == "cusum":
            st = cusum(z, delta)
        elif detector == "sr":
            st = shiryaev_roberts(z, delta)
        else:
            st = shiryaev_posterior(z, delta, rho)
        stats.append(st)
    for h in thresholds:
        times = [_first_alarm(st, h) for st in stats]
        hit = [t for t in times if t is not None]
        res[h] = {
            "frac_alarmed": len(hit) / len(times),
            "mean_time_to_alarm": float(np.mean(hit)) if hit else float("nan"),
            "arl0_lower_bound": float(np.mean([t if t is not None else T
                                               for t in times])),
        }
    return res


def detection_delay(thresholds, T: int, change_at: int, rho_explosive: float = 1.03,
                    n_sims: int = 200, detector="cusum", delta: float = 1.0,
                    prior_rho: float = 1 / 250.0, r0=None, m=None, s=None,
                    seed: int = 99):
    """Expected delay between a true regime change at `change_at` and the alarm."""
    rng = np.random.default_rng(seed)
    min_obs = _min_obs_from_r0(T, r0)
    delays = {h: [] for h in thresholds}
    missed = {h: 0 for h in thresholds}
    for _ in range(n_sims):
        y = np.zeros(T)
        for t in range(1, T):
            if t >= change_at:
                y[t] = rho_explosive * y[t - 1] + rng.normal(0, 1.0)
            else:
                y[t] = y[t - 1] + rng.normal(0, 1.0)
        bs = bsadf_fast(y, min_obs)
        z = standardize(bs, m, s)
        if detector == "cusum":
            st = cusum(z, delta)
        elif detector == "sr":
            st = shiryaev_roberts(z, delta)
        else:
            st = shiryaev_posterior(z, delta, prior_rho)
        for h in thresholds:
            a = _first_alarm(st, h)
            if a is None or a < change_at:
                # no alarm, or alarm before the change (that is a false alarm)
                missed[h] += 1
            else:
                delays[h].append(a - change_at)
    return {h: {"median_delay": float(np.median(delays[h])) if delays[h] else float("nan"),
                "mean_delay": float(np.mean(delays[h])) if delays[h] else float("nan"),
                "frac_detected": len(delays[h]) / n_sims}
            for h in thresholds}


# ---------------------------------------------------------------------------
# Exact Monte Carlo p-values + Benjamini-Hochberg FDR
# ---------------------------------------------------------------------------
def mc_pvalue(observed: float, null_draws: np.ndarray) -> float:
    """Right-tailed MC p-value with the standard +1 correction (never 0)."""
    nd = null_draws[np.isfinite(null_draws)]
    return float((1.0 + np.sum(nd >= observed)) / (1.0 + len(nd)))


def benjamini_hochberg(pvals: dict, alpha: float = 0.05):
    """Return {key: (p, q, reject)} under BH step-up FDR control."""
    keys = list(pvals)
    p = np.array([pvals[k] for k in keys], float)
    order = np.argsort(p)
    n = len(p)
    q = np.empty(n)
    prev = 1.0
    for rank in range(n - 1, -1, -1):
        i = order[rank]
        val = p[i] * n / (rank + 1)
        prev = min(prev, val)
        q[i] = min(prev, 1.0)
    return {k: (float(p[j]), float(q[j]), bool(q[j] <= alpha))
            for j, k in enumerate(keys)}
