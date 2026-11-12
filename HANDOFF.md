# Handoff: where this project stands (11 Nov 2026)

Read this first if you are picking the project up in a new session.

## What the project is

A statistically careful attempt to measure fragility in the AI / data-center capital cycle.
Governing rule: characterise a regime with a stated error rate; never claim to time a top.
Nothing here is investment advice.

## What has been established (each with a write-up in `results/`)

1. **Price tests alone are unreliable** (`docs/REFEREE_REPORT_v2.md`, `RESULTS_v3.md`). The
   v2 monitor was withdrawn: its null over-rejected and it tested price, not valuation.
2. **Nvidia shows no valuation bubble relative to revenue** (`RESULTS_v31.md`): no explosive
   episode in price / trailing revenue since 2012 (p = 0.20). A pre-registered out-of-sample
   replay through the 5 Nov 2026 sell-off passed. The price-only verdict flips with the
   sample start date and should not be trusted.
3. **So the question moved to the revenue** (`RESULTS_circular_v1.md`): Nvidia's stakes plus
   guarantees rose from ~2% to 66% of a year's revenue in twelve months; investment gains
   were 23% of pre-tax profit in the April 2026 quarter; CoreWeave funds ~3/4 of its capex
   externally.
4. **The hyperscalers now outspend their cash flow** (`RESULTS_hyperscalers_v1.md`): combined
   capex 116% of operating cash flow in 2026 Q3; four of five above 100%.
5. **But they pre-funded it** (`RESULTS_runway_v1.md`): ~$563B liquid vs a ~$30B/quarter gap;
   Alphabet and Meta stopped buybacks; Amazon (~5 quarters) and Oracle (~7) are tightest.

6. **The filing notes corrected item 3** (`RESULTS_filing_notes_v1.md`): $105B of the
   guarantees is for an OpenAI affiliate and not in force until fiscal 2029; deployed
   exposure is ~33% of revenue. Nvidia now commits to buy capacity from AI clouds that buy
   its products ($36B).

## Working rules (keep these)

- A number goes in a write-up only if a script in `src/` produces it; simulation and
  data-handling claims are enforced by `tests/` (26 tests, `pytest -q`).
- Quarterly SEC figures are derived from year-to-date filings and reconciled to the 10-K
  totals on every run (`circular_funding.reconcile`).
- "n/t" means not tagged in the SEC data, never zero.
- Detection code is frozen at v3; predictions are stated before data is examined.
- State limits next to every result.

## How data gets in

The assistant's workspace cannot reach Yahoo, the SEC or FRED. The user runs, on their Mac:

    conda activate quant
    cd ~/Desktop/AI-capital-cycle-fragility
    python src/fetch_data.py --sec-contact "Name email"

which fills `data/` (git-ignored). The assistant reads it through the connected folder.
Commits are made locally as Justins10000x; the user runs `git push`.
After a commit made through the linked shell, stale `.git/*.lock` files must be moved aside.

## Next steps, in order

1. **Nvidia's October-quarter 10-Q** (results 17 Nov 2026): re-run the fetch, then
   `circular_funding.py` and `filing_notes.py` (its patterns will need updating for the new
   quarter's wording; it fails loudly rather than reuse old values).
2. Filing notes for the hyperscalers (lease commitments).
3. Replicate Phillips-Shi-Yu (2015) on Shiller's S&P 500 data as external validation.
4. Lease commitments for the hyperscalers (not in company facts; needs filing text).

## Known loose ends

- `src/bubble_detection_demo.png` is an untracked stray copy; safe to delete.
- Hyperscaler debt tags differ by company; compare each with its own past only.
