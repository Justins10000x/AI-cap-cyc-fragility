# Project Roadmap: Quantifying AI / Data-Center Bubble Risk

**Working title:** "When does the music stop?" — A probabilistic risk monitor for the AI capital cycle.

---

## 0. The honest framing (read this first)

The instinct is to find *the top*. Resist it. Here is the epistemic reality this project has to live inside:

- **You cannot reliably time a bubble top.** The number of comparable historical episodes (tech-infrastructure / credit-fuelled asset booms) is small — maybe 6–10 useful analogues — and the system is non-stationary. Any claim of "statistical significance" about *timing* is constrained by that tiny sample.
- **Elegant top-timing methods are seductive and unreliable.** Log-Periodic Power Law (LPPL / Johansen-Ledoit-Sornette) produces a "critical time" that looks rigorous but has a weak out-of-sample record. Include it as *one* signal with explicit caveats, never as the headline.
- **What is genuinely achievable:** a multi-dimensional, probabilistic *risk gauge* (analogous to the NY Fed recession-probability model), a quantified *distance-to-historical-bubble* measure, and a *stress test of the circular financing loop* that says "here are the thresholds at which the loop breaks and how it cascades."

**Reframed goal:** Estimate, with quantified uncertainty, the *regime* the AI capital cycle is in (build-out / euphoria / fragility) and the *conditions* under which the circular flow stops self-funding — not the date it ends.

*Not financial advice. This is a research-methodology project; nothing here should be used as a basis for trades. I'm not a licensed advisor, and no model here can or should be treated as a market-timing tool.*

---

## 1. The thing you are actually modeling

Make the "snake eating its tail" loop explicit and quantitative. The loop has measurable nodes and edges:

```
Investor / Big-Tech capital  ──►  AI labs (OpenAI, Anthropic, xAI, …)
        ▲                                   │  (cloud spend)
        │                                   ▼
   Nvidia profit / stock  ◄──  Hyperscalers (MSFT, GOOGL, AMZN, META, ORCL)
        ▲                                   │  (chip purchases)
        │                                   ▼
   Vendor financing  ◄────────  Neoclouds (CoreWeave, …) ──► GPU-collateral debt
```

The bubble question reduces to one structural test: **how much of the cash flowing around this loop originates from a real external end-customer, versus being recycled investor capital and balance-sheet credit?** Quantifying that ratio over time is arguably the single most important output of the project.

---

## 2. Phase plan

### Phase 0 — Hypotheses & success criteria (1 week, no code)
- Write 3–5 *falsifiable* hypotheses before touching data (pre-registration discipline; it's your main defense against p-hacking).
  - e.g. "Aggregate AI-segment capex grows faster than externally-sourced AI revenue for N consecutive quarters" → fragility signal.
  - e.g. "Current valuation/credit/concentration feature vector sits within X Mahalanobis distance of the 1999-2000 pre-peak vector."
- Define operationally what "fragility" and "stop" mean in measurable terms.
- Define what a *good* result looks like (a calibrated probability + scenario tree), and what would *falsify* your thesis.

### Phase 1 — Data architecture (2–4 weeks)
Build clean, versioned, reproducible ingestion. Categories and sources:

| Layer | What you need | Where |
|---|---|---|
| Public financials | Capex, revenue, **RPO / remaining performance obligations**, deferred revenue, **GPU depreciation schedules**, debt | SEC EDGAR API (10-K, 10-Q, 8-K) for NVDA, MSFT, GOOGL, AMZN, META, ORCL, CRWV, etc. |
| Market data | Prices, P/E, EV/EBITDA, P/S, Mag-7 index concentration, options-implied vol, credit spreads | Market data API / yfinance; FRED for spreads |
| Macro / liquidity | Rates, yield curve, M2, financial-conditions indices | FRED |
| Physical economy | GPU shipments, datacenter leases, power contracts, grid interconnection queues, electricity demand | EIA, semiconductor reports, datacenter trackers |
| Private flows | Funding rounds, vendor-financing deals, who-invested-in-whom | Crunchbase / PitchBook (paid), curated from filings & news |
| Historical bubbles | Credit, asset prices, crisis dates across countries & decades | **JST Macrohistory Database** (free), **Shiller's online dataset** (free), BIS credit-gap data |

Deliverable: a tidy, documented data warehouse + a data dictionary. Most of the project's credibility lives here.

### Phase 2 — Feature engineering / "bubble taxonomy" (2–3 weeks)
Translate qualitative bubble signatures into quantitative features grounded in the literature:
- **Valuation stretch:** Shiller CAPE / excess CAPE yield; sector P/S vs history.
- **Credit intensity:** Borio/BIS credit-to-GDP gap; debt growth at the neoclouds; GPU-as-collateral leverage.
- **Crisis-predictive combo:** Jordà-Schularick-Taylor finding — *credit growth + asset-price growth together* is the strongest historical crisis predictor. Build that interaction feature.
- **Concentration / fragility:** index concentration, Kritzman-Li **absorption ratio** (how much variance loads on few factors — high = fragile), **financial turbulence** (Mahalanobis distance of returns).
- **The circular-funding ratio:** external revenue ÷ total cash cycled through the loop (your signature metric).
- **Real-economy gap:** capex vs deliverable revenue; deferred-revenue/RPO trends; utilization of built capacity.

### Phase 3 — Historical-analogue modeling (2–3 weeks)
- Build comparable feature vectors for past episodes: dot-com (2000), telecom/fiber over-build (1999–2001), Japan asset bubble (late 80s), 2008 housing/credit, railway mania, crypto cycles.
- Normalize and measure how today maps onto each pre-peak trajectory: **Mahalanobis distance**, **dynamic time warping** on trajectories, and the **synthetic control method** (construct a counterfactual "expected" path and measure divergence).
- Output: "current conditions resemble {episode} at T-minus {range}, with these caveats" — explicitly probabilistic, never a date.

### Phase 4 — Statistical / ML core (3–5 weeks)
Layered, each with uncertainty quantification:
- **Regime detection:** Hamilton Markov regime-switching model + GARCH/EGARCH vol regimes → probability you're in a "euphoria/fragility" state.
- **Hazard / survival model:** Cox or discrete-time hazard for "time-to-correction" conditioned on the feature set — outputs a *hazard rate*, which is the honest form of a "how close are we" answer.
- **Bayesian risk index:** PyMC hierarchical model that fuses the features into one calibrated probability with credible intervals. This is your headline gauge.
- **LPPL (optional, caveated):** fit it, report the critical-time distribution, and *prominently document its poor real-time record.* It's a sanity check, not a verdict.

### Phase 5 — Stress-testing the loop (3–4 weeks) ← the heart of the project
This is where you directly model "the music stops":
- **Financing-network model:** represent the loop as a directed graph (networkx); apply **DebtRank** / **Eisenberg-Noe** contagion mechanics. Shock one node (a lab misses revenue, a neocloud can't refinance, GPU resale value drops) and trace the cascade.
- **System-dynamics / Monte Carlo:** simulate the loop forward under distributions of (AI revenue growth, GPU depreciation rate, interest rates, refinancing availability). Find the **threshold surfaces** where external revenue can no longer service the recycled capital.
- Output: a scenario tree — "loop self-sustains," "soft deflation," "cascade" — each with a probability and the trigger conditions.

### Phase 6 — Validation & anti-fooling-yourself (ongoing, gate before any conclusion)
- Backtest every signal on the historical episodes; insist on out-of-sample / walk-forward.
- Correct for **multiple comparisons** (you'll test many features — control the false-discovery rate).
- Stress your own results: would they have "predicted" booms that *didn't* crash? (survivorship of scary-looking-but-fine periods).
- Document the small-sample limit honestly in the final write-up.

### Phase 7 — Output (2–3 weeks)
- A living **"AI Capital-Cycle Risk" dashboard**: regime probability, distance-to-analogue, circular-funding ratio, scenario tree — all with uncertainty bands.
- A methods write-up that leads with limitations.

---

## 3. Suggested tech stack
- **Core:** Python, pandas, numpy.
- **Stats/ML:** statsmodels (regime-switching, hazard), `arch` (GARCH), scikit-learn, **PyMC** (Bayesian), **networkx** (contagion graph).
- **Bubble-specific:** the `lppls` package (with caveats), DTW libraries (`dtaidistance`).
- **Data:** SEC EDGAR API, FRED API, market-data API; JST Macrohistory & Shiller datasets (downloadable).
- **Reproducibility:** versioned data, notebooks → modular package, config-driven runs.

---

## 4. Sequencing advice
Phases 1 and 5 are where the real value is, and Phase 5 is what makes this project *different* from every "is AI a bubble?" think-piece — because you're modeling the actual money loop, not just valuations. If time is short, the minimum viable version is: **circular-funding ratio (Phase 2) + financing-network stress test (Phase 5) + Bayesian risk gauge (Phase 4)**, with everything else as enrichment.

---

## 5. Open decisions for you
1. **Public-only or include private-flow data?** (Private data is where the loop really lives, but it's expensive/estimated.)
2. **Time budget / solo or team?** (Determines whether the full plan or the MVP slice.)
3. **Audience:** rigorous internal research, a published analysis, or a decision tool? (Changes how much polish vs. how much methodology disclosure.)
