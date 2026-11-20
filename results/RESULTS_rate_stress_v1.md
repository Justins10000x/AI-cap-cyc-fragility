# Rate stress (a feature on the core thesis) — 20 November 2026

**Framing.** Rate rises are not the thesis. The thesis is that the AI build-out is fragile
where earnings and credit run out. Rates matter only to the extent that they tighten that
squeeze: where operating profit barely covers interest, and where a borrower still needs new
credit. This measures exactly that. Context: a December hike is close to fully priced, the
10-year Treasury is near 5%, and commentators' base case is three quarter-point hikes by mid-2027.

**Method.** `src/rate_stress.py`, from SEC company facts. Interest coverage = operating income
over the last four quarters ÷ the latest quarter's interest expense × 4. The shock is applied to
debt due within a year plus the new borrowing needed to fill a year of the funding gap (lower
bound), and to all debt as if it were floating (upper bound).

| | operating income, last 4 quarters | interest, annual run-rate | times covered | +75bp, share of operating income (all debt) | +100bp (all debt) | covered after +75bp |
|---|---|---|---|---|---|---|
| Microsoft | $163.2B | $3.5B | 47× | 0.2% | 0.2% | 44× |
| Alphabet | $157.0B | $3.9B | 41× | 0.6% | 0.8% | 33× |
| Amazon | $104.4B | $6.8B | 15× | 1.3% | 1.7% | 13× |
| Meta | $79.4B | $3.5B | 22× | 0.8% | 1.0% | 19× |
| Oracle | $23.1B | $5.7B | 4× | 3.8% | 5.1% | 3× |
| CoreWeave | −$0.2B | $2.2B | **not covered** | n/a | n/a | not covered |

## What it shows

- **For four of the five hyperscalers, rates are a rounding error.** Even if every dollar of
  their debt repriced 100 basis points higher, it would cost under 2% of operating profit.
  Rate hikes will not break them; what matters for them is whether earnings keep pace with
  capex, which is the cash-flow question in `RESULTS_hyperscalers_v1.md`.
- **Oracle is where it starts to bite**: interest is covered only about four times, and a full
  +100bp would cost about 5% of operating profit.
- **CoreWeave already earns nothing to cover its interest.** Operating income over the last
  four quarters was slightly negative, against $2.2B a year of interest, and interest takes
  22% of revenue, about 24% after +75bp on all its debt. Higher rates deepen a hole that
  already exists; they don't create it.

**Conclusion: rates are an accelerant, not a cause.** They matter only where earnings and credit
are already thin, which here means the neoclouds and, to a lesser degree, Oracle. That supports
keeping the project centred on earnings and credit, with rates as a stress setting.

## Limits

- The floating-rate share of each company's debt is not in the data. CoreWeave's term loans are
  largely floating, so its upper bound is the more relevant one.
- New borrowing assumes the funding gap is filled with debt, not existing cash, so it overstates
  for companies with large cash piles.
- Debt definitions differ by company; Oracle's quarters end a month earlier.
- Nothing here is investment advice.

## Sources for the rate context

- [October CPI comes in hot, raising odds of a bigger-than-expected rate hike — InvestmentNews](https://www.investmentnews.com/equities/october-cpi-comes-in-hot-raising-odds-of-a-bigger-than-expected-rate-hike/268961)
- [10-year Treasury yield races back to 5% — CNBC](https://www.cnbc.com/2026/11/10/us-bonds-treasurys-yields.html)
- [Fed Minutes Signal December Rate Hike as AI Inflation Fears Mount — Paterson Capital](https://patersoncapital.com/fed-minutes-signal-december-rate-hike-as-ai-inflation-fears-mount/) (commentary)
