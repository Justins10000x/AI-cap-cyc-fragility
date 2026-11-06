"""
Size study: how often does each procedure cry "bubble" on data that has NO bubble?

Three no-bubble DGPs, all unit roots, length T = 922 (NVDA's weekly sample):
  A  homoskedastic Gaussian random walk        (v2's own assumption)
  B  GARCH(1,1) random walk calibrated to NVDA weekly returns
  C  random walk carrying NVDA's ACTUAL volatility path (13-wk rolling sd)

Bootstrap rejection rates use warp-speed Monte Carlo (Giacomini, Politis &
White 2013, Econometric Theory): one bootstrap draw per replication, pooled
across replications to form the critical value.
"""
import os, sys, time, pickle
import numpy as np, pandas as pd
from arch import arch_model
from fast_psy import bsadf_fast, _min_obs_from_r0
from psy_v3 import (gaussian_null_bsadf, wild_paths, pointwise_cv,
                    familywise_cv, date_episodes, min_duration)

M = int(sys.argv[1]) if len(sys.argv) > 1 else 400
px = (pd.read_csv(os.path.join(os.environ.get("DATA_DIR", "data"), "nvda_us_d.csv"), parse_dates=["Date"])
        .set_index("Date").sort_index()["Close"].resample("W-FRI").last().dropna())
y_nvda = np.log(px.values); T = len(y_nvda); r = np.diff(y_nvda)
mo = _min_obs_from_r0(T)

# --- DGP B calibration
g = arch_model(r * 100, mean="Constant", vol="GARCH", p=1, q=1, dist="t").fit(disp="off")
om, a1, b1, nu = (g.params[k] for k in ("omega", "alpha[1]", "beta[1]", "nu"))
print(f"GARCH(1,1)-t on NVDA weekly: omega={om:.3f} alpha={a1:.3f} beta={b1:.3f} "
      f"nu={nu:.1f}  persistence={a1+b1:.3f}")

# --- DGP C volatility path
sig = pd.Series(r).rolling(13, min_periods=4).std().bfill().to_numpy()

def dgp(kind, rng):
    if kind == "A":
        e = rng.standard_normal(T - 1)
    elif kind == "B":
        z = rng.standard_t(nu, T - 1) * np.sqrt((nu - 2) / nu)
        h = np.empty(T - 1); h[0] = om / (1 - a1 - b1); e = np.empty(T - 1)
        for t in range(T - 1):
            if t: h[t] = om + a1 * e[t - 1] ** 2 + b1 * h[t - 1]
            e[t] = np.sqrt(h[t]) * z[t]
    else:
        e = sig * rng.standard_normal(T - 1)
    return np.concatenate([[0.0], np.cumsum(e)])

# --- v2's machinery: Gaussian-null critical values at the SAME T (fairer than v2 did)
t0 = time.time()
gnull = gaussian_null_bsadf(T, 500, seed=3)
cv_gsadf_v2 = np.quantile(np.nanmax(gnull, axis=1), 0.95)
cv_point_v2 = pointwise_cv(gnull)
print(f"Gaussian null built ({time.time()-t0:.0f}s); GSADF 95% cv = {cv_gsadf_v2:.3f}")

res = {}
for kind in ("A", "B", "C"):
    t0 = time.time(); rng = np.random.default_rng({"A": 11, "B": 22, "C": 33}[kind])
    obs, boot = [], []
    for _ in range(M):
        y = dgp(kind, rng)
        obs.append(bsadf_fast(y, mo))
        boot.append(bsadf_fast(wild_paths(y, 1, seed=int(rng.integers(1e9)))[0], mo))
    obs, boot = np.array(obs), np.array(boot)
    g_obs = np.nanmax(obs, axis=1)
    cv_gsadf_v3 = np.quantile(np.nanmax(boot, axis=1), 0.95)
    cv_fw_v3 = familywise_cv(boot, 52)

    def any_episode(cv, min_len):
        return np.mean([len(date_episodes(o, cv, min_len)[0]) > 0 for o in obs])

    res[kind] = dict(
        gsadf_v2=np.mean(g_obs > cv_gsadf_v2),
        gsadf_v3=np.mean(g_obs > cv_gsadf_v3),
        stamp_v2=any_episode(cv_point_v2, 4),
        stamp_v2_pointwise_wild=any_episode(pointwise_cv(boot), min_duration(T)),
        stamp_v3=any_episode(cv_fw_v3, min_duration(T)),
    )
    print(f"DGP {kind}: done in {time.time()-t0:.0f}s  {res[kind]}")

pickle.dump(res, open("results/size_results.pkl", "wb"))
print("\nFalse-positive rates on NO-BUBBLE data (nominal 5%):")
print(f"{'DGP':<32}{'GSADF v2':>10}{'GSADF v3':>10}{'stamp v2':>10}{'stamp v3':>10}")
names = {"A": "A  Gaussian RW (v2's assumption)",
         "B": "B  GARCH-t RW (NVDA-calibrated)",
         "C": "C  NVDA's actual vol path"}
for k, v in res.items():
    print(f"{names[k]:<32}{v['gsadf_v2']:>10.1%}{v['gsadf_v3']:>10.1%}"
          f"{v['stamp_v2']:>10.1%}{v['stamp_v3']:>10.1%}")

pd.DataFrame([dict(dgp=names[k], **{kk: float(vv) for kk, vv in v.items()}) for k, v in res.items()]
             ).to_csv("results/size_study.csv", index=False)
