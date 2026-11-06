"""v3 on real data: wild-bootstrap null, FDR, family-wise date-stamping, per-episode evaluation."""
import os, time, pickle
import numpy as np, pandas as pd
from fast_psy import bsadf_fast, _min_obs_from_r0
from psy_v3 import (gaussian_null_bsadf, wild_null_bsadf, gsadf_pvalue, familywise_cv,
                    date_episodes, min_duration, episode_table,
                    benjamini_hochberg)

FILES = {"NVDA": "nvda_us_d.csv", "SMH": "smh_us_d.csv",
         "CRWV": "crwv_us_d.csv", "SPY": "spy_us_d.csv"}
B = 499
DATA = os.environ.get("DATA_DIR", "data")
out, p_v2, p_v3 = {}, {}, {}
for k, f in FILES.items():
    t0 = time.time()
    px = (pd.read_csv(os.path.join(DATA, f), parse_dates=["Date"]).set_index("Date")
            .sort_index()["Close"].resample("W-FRI").last().dropna())
    y = np.log(px.values); T = len(y)
    bs = bsadf_fast(y, _min_obs_from_r0(T))
    wnull = wild_null_bsadf(y, B, seed=101)
    gnull = gaussian_null_bsadf(T, B, seed=202)
    p_v2[k], p_v3[k] = gsadf_pvalue(bs, gnull), gsadf_pvalue(bs, wnull)
    cv = familywise_cv(wnull, 52)
    eps, flag = date_episodes(bs, cv, min_duration(T))
    out[k] = dict(px=px, bsadf=bs, cv=cv, flag=flag, eps=eps, T=T,
                  table=episode_table(px, eps))
    print(f"{k}: T={T} GSADF={np.nanmax(bs):.3f}  p(Gaussian, v2)={p_v2[k]:.3f}  "
          f"p(wild, v3)={p_v3[k]:.3f}  episodes={len(eps)}  ({time.time()-t0:.0f}s)")

bh2, bh3 = benjamini_hochberg(p_v2), benjamini_hochberg(p_v3)
print("\nWhole-sample GSADF, BH-FDR at 5%:")
print(f"{'':6}{'v2 p':>8}{'v2 q':>8}{'v2 sig':>8} | {'v3 p':>8}{'v3 q':>8}{'v3 sig':>8}")
for k in FILES:
    print(f"{k:6}{bh2[k][0]:>8.3f}{bh2[k][1]:>8.3f}{str(bh2[k][2]):>8} | "
          f"{bh3[k][0]:>8.3f}{bh3[k][1]:>8.3f}{str(bh3[k][2]):>8}")

pd.set_option("display.width", 200); pd.set_option("display.max_columns", 20)
for k in FILES:
    t = out[k]["table"]
    print(f"\n=== {k}: family-wise dated episodes (min {min_duration(out[k]['T'])} wks) ===")
    if t.empty:
        print("  none"); continue
    fmt = t.copy()
    for c in ("gain_detect_to_peak", "dd_peak_to_termination", "fwd_after_termination",
              "maxdd_after_termination"):
        fmt[c] = fmt[c].map(lambda x: "" if x is None or pd.isna(x) else f"{x:+.0%}")
    print(fmt.to_string(index=False))

pickle.dump(dict(out=out, p_v2=p_v2, p_v3=p_v3, bh2=bh2, bh3=bh3), open("results/v3_results.pkl", "wb"))
pd.DataFrame([dict(series=k, T=out[k]["T"], gsadf=float(np.nanmax(out[k]["bsadf"])),
                   p_gaussian_v2=bh2[k][0], q_gaussian_v2=bh2[k][1],
                   p_wild_v3=bh3[k][0], q_wild_v3=bh3[k][1], significant_v3=bh3[k][2],
                   n_episodes_v3=len(out[k]["eps"])) for k in FILES]
             ).to_csv("results/gsadf_tests_v3.csv", index=False)
pd.concat([out[k]["table"].assign(series=k) for k in FILES if not out[k]["table"].empty]
          ).to_csv("results/episodes_v3.csv", index=False)
