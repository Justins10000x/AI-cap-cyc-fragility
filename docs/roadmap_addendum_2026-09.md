# Roadmap Addendum — September 2026

**Purpose.** Developments between the drafting of `roadmap.md` (v2) and September 2026
materially change three parts of the research design. This addendum records what changed,
why it matters methodologically, and what to patch. It does not supersede v2; it amends it.

**Status of evidence.** Figures below are drawn from public reporting and company
disclosures current to mid-September 2026. Verify each against primary filings before
using any of it in a published result — several headline numbers in this sector have been
revised substantially between announcement and contract (see §4).

---

## 1. New shock channel: endogenous governance / safety shock

**What happened.** On 13–14 September 2026, a chip selloff sent a semiconductor gauge down
~5.9% — triggered not by a demand miss or a credit event, but by *the producers themselves*
proposing to slow frontier development. Microsoft joined OpenAI, Anthropic and others in
endorsing a more prudent development posture; investors read it as a threat to compute spend.

**Why it matters.** Every transmission channel in v2 assumes the loop breaks from *below*:
revenue shortfall (§7), refinancing failure (§3.1), collateral erosion (§3.1). This is a break
from *above* — a voluntary, coordinated supply-side deceleration driven by governance rather
than economics. **No historical analogue in the donor pool has this channel.** Railways,
telecom, and housing had no mechanism by which the principal producers jointly proposed to
build less.

**Patch.**
- Add a fourth shock channel to the Phase-5 stress test: *coordinated capex deceleration*,
  parameterised independently of demand.
- Flag it explicitly in the small-sample discussion (v2 §0.2): it is a concrete instance of
  regime novelty, and it *weakens* the historical-analogue layer's claim to transportability.
  This strengthens the paper rather than weakening it — name it.

---

## 2. Vendor backstops are a signal-suppressor — the key measurement patch

**What happened.** On 1 July 2026 Nvidia introduced a backstop model under which it agrees to
rent back unused GPU capacity from neocloud partners at a fixed rate, underwriting a
utilisation floor. Related: reported CoreWeave arrangements obliging Nvidia to purchase
residual unsold capacity; Meta-backstopped term loans pricing ~400bp inside CoreWeave's own
unsecured curve (≈5.9% vs ≈10%).

**Why it matters — and this is the single most important update in this document.** The
**circular-funding ratio** (v2 §9) is defined as externally-sourced revenue ÷ total cash
cycled through the loop. Backstopped revenue *presents as customer revenue in the filings*
while being, economically, the most internal money in the system — the chip vendor paying the
chip buyer to hold the chips. A naïve parse of the income statement will therefore book
vendor-backstopped and take-or-pay revenue as **external**, biasing the ratio upward exactly
when the underlying demand is weakest. The instrument is, by construction, blind at the moment
it matters most.

Note further that backstop pricing means neocloud debt spreads now track *the backstopper's*
credit, not the borrower's — so spread-based fragility indicators (v2 §2 feature battery) are
similarly suppressed.

**Patch.**
- Redefine the numerator: external revenue must **net out** (a) vendor-backstopped revenue,
  (b) take-or-pay and residual-capacity purchase obligations, (c) revenue from counterparties
  in which the seller holds an equity stake, pro-rated by stake.
- Publish **both** a naïve and an adjusted ratio. The *spread between them* is itself a
  fragility indicator — it measures how much of reported demand is vendor-manufactured.
- Add a spread-adjustment note: treat backstopped-tranche spreads as uninformative about
  borrower credit; use unsecured curves where they exist.

---

## 3. Off-balance-sheet commitments break a filings-only extractor

**What happened.** Moody's has flagged roughly **$662B of signed-but-not-commenced
data-center leases** sitting off balance sheet. Separately, PIMCO estimates hyperscaler capex
will consume ~94% of operating cash flow by 2026–27, and Mag-7 free cash flow has fallen to
its lowest share of sales since early 2024.

**Why it matters.** The Phase-1 extractor was scoped to capex, revenue, RPO, depreciation and
debt from the face of the financials. Commitments of this size that are *not yet* on balance
sheet will not appear there, yet they are precisely the forward obligation that determines
whether the loop can keep self-funding.

**Patch.**
- Add a **commitments-and-contingencies footnote layer** to the extractor: operating-lease
  commitments not yet commenced, purchase obligations, take-or-pay contracts, residual-value
  guarantees.
- Add **capex ÷ operating cash flow** as a first-class fragility feature. It is simple,
  filing-derived, and currently near a structural ceiling — a natural rate limit on the
  build-out that requires no valuation assumptions.

---

## 4. Discipline note: headline vs. contract

Reported AI financing figures have diverged from executed contracts by very large margins
(e.g. a widely-reported ~$600B Nvidia–OpenAI financing figure in July 2026 corresponding to a
signed guarantee reported at ~$105B in August). **Rule for this project: no announced figure
enters the dataset until traced to a filing, contract, or company disclosure.** Maintain an
`announced` vs. `executed` flag on every deal record; the gap between them is worth plotting
in its own right as a sentiment indicator.

---

## 5. Concentration and threshold indicators worth tracking

Recent commentary proposes thresholds that are usefully falsifiable and cheap to monitor.
Recorded here as *candidate* indicators to pre-register (v2 §8), not as endorsed thresholds:

- **Nvidia revenue concentration.** Reported at four customers ≈61% of a recent quarter's
  revenue; a proposed bursting-signal threshold is >70% (the loop tightening rather than
  expanding).
- **Hyperscaler capex deceleration** of >20% YoY as a regime-break signal.
- **Enterprise AI production-deployment rates** stalling below ~15%.
- On the other side: healthcare/manufacturing AI spend, enterprise deal-conversion rates, and
  documented Fortune-2000 productivity gains as floor-confirming indicators.
- **Revenue-adequacy gap.** Bain's estimate that the ecosystem requires ~$2T annual revenue by
  2030 to justify current infrastructure spend, with the trajectory falling roughly $800B
  short, is the cleanest published statement of the loop's terminal condition. Treat as a
  scenario input to Phase 5, not as a forecast.

Pre-register these *before* evaluating them, and apply FDR control across the set (v2 §8).

---

## 6. Competitive landscape

At least one public project now maps AI circular financing deal-by-deal and publishes a scored
"Bubble Index" (reported at 73/100 against past bubbles). This is adjacent work and worth
monitoring.

**Positioning.** That project is a *scored dashboard*: sourced, useful, but scoring is not
inference. This project's differentiation is unchanged and should be stated explicitly in the
README — formal, testable definitions of a bubble (v2 §1), detection with a *characterised
false-alarm rate* rather than an unvalidated score (v2 §2), and an explicit power analysis of
what the data cannot support (v2 §0). Where a dashboard says "73," this project should say
"here is the probability, here is the credible interval, and here is what we cannot conclude."

---

## 7. Revised near-term priority

1. **Run the detector on real prices** (NVDA, SMH, the Mag-7 basket) and date-stamp episodes —
   the repo's headline result is still simulated.
2. **Implement the adjusted circular-funding ratio** per §2, with the naïve-vs-adjusted spread
   as a published series. This is now the project's highest-value original contribution.
3. Add the commitments footnote layer (§3) and the capex/OCF feature.
4. Add the coordinated-deceleration channel to the stress test (§1).

Items 2 and 4 are the pieces no one else is doing.
