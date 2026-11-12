"""
filing_notes.py -- figures that exist only in the written notes of Nvidia's and
CoreWeave's SEC filings (not in the company-facts data): who the guarantees cover,
new money put into private stakes, cloud-capacity commitments, customer concentration.

Each figure is pulled by a pattern that must match the filing text exactly once in
meaning; if a pattern stops matching (new filing, new wording) the script fails
loudly instead of reporting a stale or guessed number. Standard library only.

Usage (repo root):  python src/filing_notes.py
Reads the newest data/filings/nvda_10-Q_*.htm and crwv_10-Q_*.htm (src/fetch_data.py).
"""
from __future__ import annotations
import csv, glob, html, os, re, sys

DATA = os.environ.get("DATA_DIR", "data")


def to_text(raw: str) -> str:
    raw = re.sub(r"(?is)<(script|style|ix:header).*?</\1>", " ", raw)
    raw = re.sub(r"(?i)</(p|div|tr|table|li|h\d)>|<br\s*/?>", "\n", raw)
    raw = re.sub(r"(?i)</t[dh]>", " | ", raw)
    t = html.unescape(re.sub(r"<[^>]+>", "", raw)).replace("\xa0", " ")
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"( \| )+", " | ", t)
    return re.sub(r"\n\s*\n+", "\n", t)


def num(s: str) -> float:
    return float(s.replace(",", "").replace("(", "-").replace(")", ""))


# name: (pattern, unit, what it is). Group 1 is the value.
NVDA = {
    "openai_guarantee_cap_bn": (r"guarantees, capped at a total of \$(\d+) billion.{0,200}?affiliate of OpenAI", "USD bn",
                                "SB Energy guarantees on behalf of an OpenAI affiliate (signed Aug 2026, effective from lease start)"),
    "ai_cloud_guarantees_bn": (r"maximum gross exposure under all agreements is \$([\d.]+) billion", "USD bn",
                               "land/power/shell guarantees for AI cloud partners"),
    "private_net_additions_q_mn": (r"Net additions \| ([\d,]+) \|", "USD mn", "new money into private stakes, latest quarter"),
    "private_net_additions_ytd_mn": (r"Net additions \| [\d,]+ \| [\d,]+ \| ([\d,]+) \|", "USD mn", "same, fiscal year to date"),
    "private_reclassified_q_mn": (r"Reclassification \(2\) \| \(([\d,]+)\)", "USD mn", "private stakes moved to listed after going public, latest quarter"),
    "equity_investments_total_bn": (r"equity investments of \$(\d+) billion and equity investment commitments", "USD bn", "all equity investments held"),
    "equity_commitments_bn": (r"equity investment commitments of \$(\d+) billion", "USD bn", "further equity investments committed"),
    "ai_cloud_agreements_bn": (r"typically six years in duration, totaled \$(\d+) billion", "USD bn",
                               "Nvidia commits to buy cloud capacity from AI clouds that buy its products"),
    "cloud_service_agreements_bn": (r"Cloud service agreements \| 3 \| 8 \| 7 \| 6 \| 4 \| 1 \| (\d+) \|", "USD bn", "cloud capacity for Nvidia's own R&D"),
    "third_party_dc_leases_bn": (r"Data center leases not commenced for third party \|.*?\| (\d+) \|\s*\n", "USD bn", "data-center leases signed to hand on to third parties"),
    "top_direct_customer_q_pct": (r"For the second quarter of fiscal year 2027, one direct customer represented (\d+)% of total revenue", "%", "largest direct customer, latest quarter"),
    "top3_direct_customers_h1_pct": (r"three direct customers represented (\d+%, \d+%, and \d+%) of total revenue", "% each", "three largest direct customers, first half"),
    "financing_platforms_mou_bn": (r"mobilize more than \$(\d+) billion of third-party capital", "USD bn", "memorandums of understanding, not definitive agreements"),
}
CRWV = {
    "crwv_customer_a_q_pct": (r"Customer A \| (\d+)% \|", "%", "CoreWeave's largest customer, share of revenue, latest quarter"),
    "crwv_customer_a_q_year_ago_pct": (r"Customer A \| \d+% \| (\d+)% \|", "%", "same, a year earlier"),
    "crwv_customer_b_q_pct": (r"Customer B \| (\d+)% \|", "%", "second largest"),
    "crwv_nvidia_placement_bn": (r"NVIDIA Corporation for a private placement.{0,200}?aggregate gross proceeds of \$([\d.]+) billion", "USD bn",
                                 "shares CoreWeave sold to Nvidia, Jan 2026"),
}


def extract(text: str, spec: dict) -> dict:
    out = {}
    for name, (pat, unit, what) in spec.items():
        m = re.search(pat, text, flags=re.S)
        if not m:
            raise SystemExit(f"pattern for '{name}' no longer matches the filing; do not reuse old values")
        v = m.group(1)
        out[name] = (v if "%" in v else num(v), unit, what)
    return out


def newest(pattern: str) -> str:
    files = sorted(glob.glob(os.path.join(DATA, "filings", pattern)))
    if not files:
        raise SystemExit(f"no file matching {pattern} in {DATA}/filings; run src/fetch_data.py")
    return files[-1]


if __name__ == "__main__":
    rows = []
    for pat, spec in (("nvda_10-Q_*.htm", NVDA), ("crwv_10-Q_*.htm", CRWV)):
        path = newest(pat)
        text = to_text(open(path, encoding="utf-8", errors="replace").read())
        for name, (v, unit, what) in extract(text, spec).items():
            rows.append((name, v, unit, what, os.path.basename(path)))
            print(f"{name:34} {str(v):>18} {unit:7} {what}")
    os.makedirs("results", exist_ok=True)
    with open("results/filing_notes.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["figure", "value", "unit", "what", "source_file"]); w.writerows(rows)
    print("\nwrote results/filing_notes.csv")
