# Pre-registered predictions: Nvidia, quarter ended 25 October 2026 (Q3 FY2027)

**Written 17 November 2026, 05:20 UTC, before Nvidia's results (due after the US close on
17 November) and before its 10-Q is filed.** The git commit and GitHub push of this file are the
timestamp. Nothing below may be edited after the results; the scorecard goes in a separate file.

These predict the circular-funding measures, not the share price or revenue. Each is a yes/no
statement with a stated probability, scored from the 10-Q via `src/circular_funding.py` and
`src/filing_notes.py`. Probabilities are scored with a Brier score (lower is better; always
answering 50% scores 0.25), so overconfidence is penalised, not just wrong calls.

## Baseline (10-Q for the quarter ended 26 July 2026)

Equity investments $99B; further equity commitments $25B ($18B due by fiscal year-end, Jan 2027);
AI cloud agreement commitments $36B; guarantee maximum exposure $108.5B ($105B for an OpenAI
affiliate, $3.5B for AI cloud partners); new money into private stakes $13.1B in the quarter;
gains on investments 11% of pre-tax profit; largest direct customer 16% of revenue.

## Predictions

| # | Statement (true or false when the 10-Q is read) | Probability true |
|---|---|---|
| P1 | Guarantee maximum exposure is at least $108.5B | 80% |
| P2 | Total equity investments stated in the filing exceed $99B | 70% |
| P3 | Net additions to non-marketable (private) equity securities in the quarter are at least $5B | 70% |
| P4 | Gains on investments are a smaller share of pre-tax profit than in the July quarter (below 10.9%) | 65% |
| P5 | AI cloud agreement commitments are at least $36B | 70% |
| P6 | The largest direct customer is between 12% and 20% of the quarter's revenue | 75% |

## Reasoning, briefly

- **P1:** the OpenAI-affiliate guarantees were signed in August as a cap; nothing in their terms
  reduces the cap before leases start (fiscal 2029).
- **P2, P3:** $18B of equity commitments fall due by January 2027, roughly half of that window
  falls inside this quarter, and Nvidia said it expects to keep investing in its ecosystem.
  Markdowns could offset P2.
- **P4:** listed holdings fell over the quarter (CoreWeave −25% from 24 Jul to 23 Oct; the
  semiconductor index −6%), and private stakes are marked up only on observable new rounds.
- **P5:** the AI cloud programme began in the July quarter and was described as a growth tool.
- **P6:** direct concentration has been in a 13–23% band for the past year.

## What the outcome would mean

If P1, P2, P3 and P5 come true, Nvidia kept expanding the loop up to the start of the
November sell-off. If equity investments or AI cloud commitments fall, it was already pulling
back before the market did. Either result is informative; neither is a trading signal.
