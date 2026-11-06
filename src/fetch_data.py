"""
fetch_data.py -- download everything the project needs into ./data, in one go.

Run from the repo root, on your own machine:
    python src/fetch_data.py --sec-contact "Your Name you@example.com"

Writes (overwriting older copies):
    data/{nvda,smh,spy,crwv,rsp}_us_d.csv   daily prices, Stooq-style columns
                                            (Date,Open,High,Low,Close,Volume), split-
                                            and dividend-adjusted, so src/ code reads
                                            them unchanged
    data/nvda_revenue*.json                 Nvidia revenue, SEC XBRL API (two tags)
    data/fedfunds.csv, data/hy_spread.csv   Fed funds rate and high-yield credit
                                            spread, from FRED

The SEC asks every automated client to identify itself with a name and email
(https://www.sec.gov/os/accessing-edgar-data). Pass yours with --sec-contact;
without it the SEC download is skipped and everything else still runs.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request

TICKERS = ["NVDA", "SMH", "SPY", "CRWV", "RSP"]
_SEC = "https://data.sec.gov/api/xbrl/companyconcept/CIK0001045810/us-gaap/"
# NVDA reported revenue under the ASC 606 tag for FY2019-FY2021 annual totals,
# so both tags are needed for a continuous, correctly dated series.
SEC_FILES = {"nvda_revenue.json": _SEC + "Revenues.json",
             "nvda_revenue_asc606.json":
                 _SEC + "RevenueFromContractWithCustomerExcludingAssessedTax.json"}
FRED = {"fedfunds.csv": "FEDFUNDS", "hy_spread.csv": "BAMLH0A0HYM2"}


def to_stooq_format(hist):
    """yfinance history -> Stooq-style frame: naive dates, the five columns we use."""
    import pandas as pd
    df = hist[["Open", "High", "Low", "Close", "Volume"]].copy()
    idx = pd.DatetimeIndex(df.index)
    if idx.tz is not None:
        idx = idx.tz_localize(None)
    df.index = idx.normalize()
    df.index.name = "Date"
    df = df[~df.index.duplicated(keep="last")].dropna(subset=["Close"]).sort_index()
    return df


def fetch_prices(outdir: str) -> bool:
    try:
        import yfinance as yf
    except ImportError:
        print("  yfinance is not installed:  pip install yfinance pandas")
        return False
    ok = True
    for t in TICKERS:
        try:
            hist = yf.Ticker(t).history(period="max", auto_adjust=True)
            if hist is None or hist.empty:
                raise RuntimeError("no rows returned")
            df = to_stooq_format(hist)
            path = os.path.join(outdir, f"{t.lower()}_us_d.csv")
            df.to_csv(path, date_format="%Y-%m-%d")
            print(f"  {t:5} {len(df):>6} rows  {df.index[0].date()} -> "
                  f"{df.index[-1].date()}  -> {path}")
        except Exception as e:                       # keep going on one bad ticker
            ok = False
            print(f"  {t:5} FAILED: {e}")
    return ok


def _get(url: str, headers: dict) -> bytes:
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def fetch_sec(outdir: str, contact: str | None) -> bool:
    if not contact:
        print("  skipped: pass --sec-contact \"Your Name you@example.com\"")
        return False
    ok = True
    for fname, url in SEC_FILES.items():
        try:
            raw = _get(url, {"User-Agent": contact, "Accept-Encoding": "identity"})
            n = len(json.loads(raw).get("units", {}).get("USD", []))
            path = os.path.join(outdir, fname)
            with open(path, "wb") as f:
                f.write(raw)
            print(f"  {fname:26} {n:>4} facts -> {path}")
        except Exception as e:
            ok = False
            print(f"  {fname:26} FAILED: {e}")
    return ok


def fetch_fred(outdir: str) -> bool:
    ok = True
    for fname, sid in FRED.items():
        url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}"
        try:
            raw = _get(url, {"User-Agent": "ai-cap-cyc-fragility/1.0"})
            path = os.path.join(outdir, fname)
            with open(path, "wb") as f:
                f.write(raw)
            rows = raw.count(b"\n") - 1          # no backslash inside f-string: py<3.12
            print(f"  {sid:13} {rows:>6} rows -> {path}")
        except Exception as e:
            ok = False
            print(f"  {sid:13} FAILED: {e}")
    return ok


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--sec-contact", default=os.environ.get("SEC_USER_AGENT"),
                    help='name and email for the SEC, e.g. "Jane Doe jane@example.com"')
    ap.add_argument("--outdir", default="data")
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)

    print("Prices (Yahoo Finance via yfinance):")
    p = fetch_prices(a.outdir)
    print("Fundamentals (SEC EDGAR):")
    s = fetch_sec(a.outdir, a.sec_contact)
    print("Macro (FRED):")
    m = fetch_fred(a.outdir)

    print("\nDone." if (p and s and m) else "\nFinished with some failures (see above).")
    return 0 if p else 1


if __name__ == "__main__":
    sys.exit(main())
