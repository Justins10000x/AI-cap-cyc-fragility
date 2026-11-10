# Circular-funding ratio v2, part 2: cash runway — 11 November 2026

**Question.** Four of the five hyperscalers now spend more on capex than they earn in
cash. Is that an immediate constraint? How long could each keep it up from cash on hand?

**Method.** `src/runway.py`. Liquid funds = cash + short-term investments. Gap = capex +
buybacks + dividends − operating cash flow, averaged over the latest two quarters. Runway =
liquid ÷ gap. A what-if at recent levels, not a forecast.

| | liquid funds, 2025 Q3 ($B) | 2026 Q3 ($B) | gap per quarter, a year ago ($B) | now ($B) | buybacks, latest two quarters ($B) | same two quarters a year ago ($B) | runway |
|---|---|---|---|---|---|---|---|
| Amazon | 94 | 114 | −0.4 | **21.8** | n/t | n/t | **about 5 quarters** |
| Oracle | 11 | 37 | 3.2 | 5.2 | 0.0* | 0.2 | about 7 quarters |
| Alphabet | 98 | 265 | 0.2 | 10.3 | **0.0** | 25.1 | about 26 quarters |
| Meta | 44 | 82 | −2.0 | 1.1 | **0.0** | 13.5 | very long |
| Microsoft | 102 | 65 | −14.3 | −7.9 | 9.0 | 10.2 | no gap |

A negative gap means the company still generates spare cash after capex and payouts.
\* Oracle's latest quarter has no buyback figure tagged; counted as zero.

## What it shows

1. **Cash is not the immediate constraint.** The five hold about **$563B** of liquid funds
   against a combined gap of about **$30B a quarter**. A year ago they had a combined
   surplus of $13B a quarter.
2. **They borrowed ahead of need.** Cash piles *rose* over the year (about $350B to $563B)
   while long-term debt rose by roughly $309B. Alphabet's liquid funds went from $98B to $265B.
   The money for the next stretch of build-out is largely already raised.
3. **Buybacks were switched off to make room.** Alphabet and Meta each report **zero share
   repurchases in all three quarters of 2026**, after $25.1B and $13.5B in the same two
   quarters of 2025. Meta's gap is small only because of this.
4. **Amazon is the tightest**: a $22B-a-quarter gap against $114B of liquid funds, about five
   quarters at the current pace, with no buybacks to cut. **Oracle** has about seven.
5. **Microsoft still funds everything from operations**, with $8B a quarter to spare, though
   that surplus has halved.

## What it means for the loop

The squeeze is not imminent: the hyperscalers have pre-funded several quarters. What has
changed is where the cushion comes from. A year ago it was surplus cash flow; now it is
borrowed money and cancelled buybacks. The build-out can continue at this pace for a while,
but continuing *beyond* that depends on debt markets staying open, most pressingly for Amazon
and Oracle. For Nvidia's revenue, the risk is less a sudden stop than a slowdown when the
pre-funded cash runs down and the next round of borrowing is priced.

## Limits

- Holds capex, payouts and cash flow at recent levels; all three will change.
- Liquid funds exclude long-term investments and undrawn credit lines, and not all cash is
  freely usable.
- Lease commitments are excluded, so the true gap is larger.
- Two-quarter averages still carry some seasonality.
- Nothing here is investment advice.

## Reproduce

```bash
python src/runway.py     # -> results/runway.csv, results/runway_quarterly.csv
```
