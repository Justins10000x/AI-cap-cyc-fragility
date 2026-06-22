# Quantifying AI Capital-Cycle Fragility — Methodological Core (v2)

**Thesis.** The "top" of a bubble is not a point to be *predicted*; it is a regime change to be *detected* under a controlled false-alarm rate, in a system whose fragility can be characterized structurally even when its timing cannot. This document specifies a research program built to that standard.

---

## 0. The epistemic contract (this is the part that earns the room)

Everything below is engineered around four constraints that a serious reviewer will raise in the first five minutes. State them first; design to them.

1. **Tiny effective sample.** The number of comparable tech-infrastructure / credit-fuelled episodes is *N ≈ 6–10* (dot-com, telecom over-build, Japan, US housing/credit, railway mania, several crypto cycles). No amount of high-frequency market data changes the fact that the *events you care about* are this rare. Any claim of "statistical significance about timing" is therefore a claim about an extrapolation, and must be reported as such.
2. **Non-stationarity / regime novelty.** The data-generating process is not fixed; the AI cycle has structural features (depreciation dynamics of compute, vendor-financing topology) with no exact historical precedent. Pure ML on this is extrapolation dressed as interpolation.
3. **Identification, not fit.** Predictive accuracy is cheap and misleading here. The defensible questions are *causal/structural*: how much of the cash circulating the loop is externally sourced, and what thresholds break self-funding? Those require an identification strategy, not an R².
4. **Pre-registration & multiplicity.** We will test many indicators; without pre-registration and false-discovery control, "we found a signal" is meaningless. Hypotheses, indicator set, and decision thresholds are frozen *before* the live evaluation window (timestamp them on OSF).

**Power-honesty deliverable (mandatory, Phase 0).** Before modeling, compute and publish the *detectable effect size* given N and the chosen test. If the honest answer is "we cannot distinguish hypothesis A from B at conventional confidence," that is a finding, not a failure, and stating it is what separates this from amateur work.

---

## 1. What *is* a bubble? Three formal definitions, used together

Amateurs argue about valuations. We commit to definitions with testable consequences and triangulate across all three.

### 1.1 Econometric: explosive autoregressive root (the working horse)
A bubble is a period in which log-price departs from a unit-root random walk toward a **mildly explosive root** ($\rho > 1$). Detect and *date-stamp* it with the **Phillips–Shi–Yu generalized sup-ADF (GSADF)** test (Phillips, Shi & Yu, *Int. Econ. Review*, 2015):

$$\text{GSADF} = \sup_{r_2 \in [r_0,1],\; r_1 \in [0, r_2-r_0]} \text{ADF}_{r_1}^{r_2}$$

with the backward sup-ADF (BSADF) sequence giving real-time origination/termination dates. This is the closest thing the literature has to a defensible "is this explosive *right now*" test. Tooling: `exuber` / `psymonitor`. **LPPL/Sornette is demoted to a single corroborating signal with its poor real-time record disclosed in-line — never the headline.**

### 1.2 Mathematical-finance: strict local martingale (what a bubble *is*)
Under a risk-neutral measure $\mathbb{Q}$, the fundamental value is the expected discounted cash-flow stream; a bubble is the excess $\beta_t = S_t - \text{(fundamental)}$. Jarrow–Protter–Shimbo: **a bubble exists iff the discounted price process is a strict local martingale** (a local martingale that is not a true martingale) under $\mathbb{Q}$. Because strict local martingales are strict supermartingales, this formalizes "price above fundamental, expected to fall." It is *testable*: per Jarrow–Kchia–Protter (*SIAM J. Financial Math*, 2011), estimate the local-volatility function $\sigma(\cdot)$ and check its tail — if

$$\int^{\infty} \frac{x}{\sigma^2(x)}\,dx < \infty,$$

the process is a strict local martingale (a bubble). Operationally: nonparametrically estimate $\sigma(x)$ from the relevant equities/options surface and test the integral's convergence, cross-checked against put–call-parity deviations. Invoking this correctly signals you know what a bubble is, measure-theoretically.

### 1.3 Economic: rational-bubble cross-equation restriction
Blanchard–Watson stochastic bubbles require the bubble component satisfy $\mathbb{E}_t[B_{t+1}] = (1+r)B_t$; a bursting bubble crashes to zero with probability $\pi$ each period and grows at rate $(1+r)/(1-\pi)$ otherwise. Tirole's OLG condition ($r \le g$) tells you *when rational bubbles can even exist*. These impose **cross-equation restrictions** you can test against the data, distinguishing "rational bubble" from "mispricing" from "justified repricing."

A period flagged by all three lenses is a far stronger claim than any single test.

---

## 2. The spine: detection, not prediction (quickest-change-detection)

Reframe "when does the music stop" as **sequential change-point detection**: observe the stream, declare a regime change as *quickly as possible* subject to a *bound on false alarms*. This is a solved problem class with optimality theory — which is exactly why it impresses.

- **Bayesian (Shiryaev) formulation:** with a prior on an unknown change-time, the rule minimizing expected delay subject to a false-alarm constraint is a threshold on the posterior probability of "change has occurred." This yields an honest, continuously-updated *fragility probability*.
- **Minimax formulations:** **CUSUM** (Page) is asymptotically optimal under Lorden's criterion; the **Shiryaev–Roberts** procedure under Pollak's. Run both as the production detector.
- **Output:** not a date, but a monitored statistic with a *characterized* ARL (average run length to false alarm) vs. detection-delay tradeoff. You can state: "at this threshold, expected false alarm once per X years; expected detection delay Y weeks." That is a defensible claim.

The change being detected is multivariate — a shift in the joint distribution of the feature battery in §3–4 — so use multivariate/nonparametric CUSUM or a detector on the posterior of the regime model in §5.

---

## 3. The object of study: the loop as a structural, causal system

Stop treating the financing loop as a correlation graph. Model it as a system with *direction* and *mechanism*.

### 3.1 The right theory for "GPUs pledged to buy more GPUs"
This is a **collateral / leverage cycle**, and there is precise theory for it:
- **Geanakoplos leverage cycle:** equilibrium leverage and collateral values co-move and amplify; a small drop in collateral value (GPU resale/depreciation) forces deleveraging → fire sales → further collateral decline.
- **Brunnermeier–Pedersen** margin/liquidity spirals: funding-liquidity and market-liquidity reinforce, producing the discontinuous "music stops" dynamic. Calibrate these to the neocloud (e.g., CoreWeave-type) balance sheets and GPU depreciation schedules pulled from filings.

### 3.2 Measuring how *wired* the loop is, and in which direction
- **Diebold–Yilmaz connectedness:** generalized forecast-error-variance decomposition of a VAR over {Nvidia, hyperscalers, labs' proxies, neocloud credit, semis} → a rolling *total* and *directional* spillover index. Rising connectedness = rising systemic fragility.
- **Transfer entropy** (Schreiber): model-free directed information flow,
$$T_{Y\to X} = \sum p(x_{t+1},x_t,y_t)\,\log\frac{p(x_{t+1}\mid x_t,y_t)}{p(x_{t+1}\mid x_t)},$$
with *effective* transfer entropy (shuffle-corrected) to kill finite-sample bias. Resolves the genuinely interesting question: does Nvidia capex *drive* lab valuations, or vice versa?
- **Structural identification:** a structural VAR with sign/financial-friction restrictions (financial-accelerator lineage) to move from "connected" to "this shock propagates *this* way."

### 3.3 Contagion mechanics
Represent the financing graph and apply **Eisenberg–Noe** clearing and **DebtRank** (Battiston et al.). Note the Acemoglu–Ozdaglar–Tahbaz-Salehi result: dense networks are *robust-yet-fragile* — resilient to small shocks, catastrophic past a threshold. Locate where this loop sits on that phase transition.

---

## 4. Early-warning battery (theory-grounded, not heuristic)

- **Critical slowing down** (Scheffer et al., *Nature* 2009): approaching a bifurcation, the system's recovery from perturbations slows — the dominant eigenvalue → 0 — producing rising **lag-1 autocorrelation**, rising **variance**, and changing **skewness/flickering**. Compute these generic early-warning indicators on the loop's state variables. Almost nobody does this in finance; it is rigorous and visually compelling.
- **Topological data analysis** (Gidea–Katz, 2018): build sliding-window point clouds from the multivariate price/fundamentals stream, compute persistence diagrams, track $L^p$ norms of **persistence landscapes** — these spiked before the 2000 and 2008 crashes. Genuine novelty, defensible provenance.
- **Extreme-value theory** for the crash *magnitude* tail: peaks-over-threshold / generalized Pareto, Hill estimator — because Gaussian tails will badly understate the downside and any reviewer will check.

---

## 5. The inference engine (built for tiny N)

- **Bayesian hierarchical partial pooling across episodes.** This is the honest way to use N≈8: model each historical bubble as a draw from a population with shared and idiosyncratic parameters; the AI cycle is a new draw. Partial pooling *borrows strength* across episodes while explicitly modeling heterogeneity — and the posterior predictive intervals will *correctly* be wide. Implement in PyMC / NumPyro.
- **Regime detection without fixing the number of regimes:** the **sticky HDP-HMM** (Fox et al.) — Bayesian nonparametric — lets the data decide how many regimes exist (build-out / euphoria / distribution / unwind) rather than assuming two.
- **Gaussian-process** components for nonparametric, uncertainty-bearing trend/fragility surfaces.
- All fragility outputs are *distributions with credible intervals*, never point estimates.

---

## 6. Historical-analogue layer

- **Synthetic control** (Abadie): construct a weighted counterfactual "no-bubble" path for the AI cycle from donor episodes/sectors; the divergence is your estimand.
- **Dynamic time warping** to align trajectories of different durations before computing **Mahalanobis distance** of the current feature vector to each episode's pre-peak path.
- **Free, serious data:** the **Jordà–Schularick–Taylor Macrohistory Database** (credit, asset prices, crises across countries since 1870 — built for exactly this) and **Shiller's** long-run valuation series.

---

## 7. Stress-testing the loop ("what makes the music stop")

- **Threshold-surface search via Monte Carlo:** simulate the calibrated structural loop (§3.1) forward under joint distributions of {external AI revenue growth, GPU depreciation rate, refinancing spread, rates}. Locate the surfaces in parameter space where externally-sourced revenue can no longer service recycled capital — the self-funding boundary.
- **Cascade simulation:** shock a node (a major lab misses revenue; a neocloud can't roll its GPU-backed debt; resale GPU prices fall X%) and propagate via §3.3.
- **Output:** a scenario tree {self-sustains, soft deflation, cascade}, each with posterior probability and explicit trigger thresholds — the project's signature deliverable.

---

## 8. Validation & anti-overfitting protocol (the credibility firewall)

Financial ML fails in predictable, embarrassing ways. Preempt each:
- **Pre-registration** of hypotheses, indicator set, and thresholds on OSF, timestamped before the live window.
- **Purged & embargoed cross-validation** (López de Prado) to eliminate the leakage that standard k-fold introduces in serially-correlated financial data.
- **Multiple-testing control:** Benjamini–Hochberg FDR across the indicator battery; report the **Probability of Backtest Overfitting** (Bailey–López de Prado) and **deflated** performance metrics.
- **Walk-forward, strictly out-of-sample** evaluation on held-out historical episodes; report detector ARL/delay, not just hit-rate.
- **Negative controls:** does the system "predict" crashes in periods that looked scary but resolved benignly? If it can't avoid those false positives, say so.
- **Power analysis up front** (per §0): publish the minimum detectable effect given N.

---

## 9. Data architecture (sharpened)

| Layer | Critical fields | Source |
|---|---|---|
| Public financials | capex, revenue, **RPO / deferred revenue**, **GPU depreciation schedules & useful-life assumptions**, debt & collateral terms | SEC EDGAR API (10-K/Q, 8-K): NVDA, MSFT, GOOGL, AMZN, META, ORCL, CRWV, … |
| Market / options | prices, multiples, index concentration, **implied-vol surfaces** (for §1.2), credit spreads | market-data + options API; FRED for spreads |
| Macro / liquidity | rates, curve, M2, financial-conditions indices | FRED |
| Physical economy | GPU shipments, datacenter leases, power/interconnection-queue data, utilization | EIA, semiconductor reports, datacenter trackers |
| Private flows | funding rounds, vendor-financing & GPU-collateral deals, equity stakes | filings + curated; Crunchbase/PitchBook (paid) |
| Historical bubbles | credit, asset prices, crisis dates | **JST Macrohistory DB** (free), **Shiller** (free), BIS credit gap |

The **circular-funding ratio** — externally-sourced revenue ÷ total cash cycled through the loop — is computed here and is the single most important series in the project.

---

## 10. Stack
Python; pandas/numpy; **statsmodels** & `arch` (VAR, GARCH, regime); **`exuber`/`psymonitor`** (GSADF); **PyMC / NumPyro** (hierarchical Bayes, sticky HDP-HMM); **ruptures** (change-point) + custom CUSUM/Shiryaev–Roberts; **giotto-tda** / `ripser` (TDA); **networkx** + DebtRank/Eisenberg–Noe; `dtaidistance` (DTW); EVT via `scipy`/`pyextremes`. Reproducible, config-driven, versioned data.

---

## 11. Sequencing & MVP
The defensible minimum that still impresses:
1. **GSADF date-stamping** of the relevant equities (§1.1) + **strict-local-martingale test** on one bellwether (§1.2) — establishes "is this even a bubble" rigorously.
2. **Circular-funding ratio** time series from filings (§9) — the structural heart.
3. **Quickest-detection monitor** (§2) over a Bayesian hierarchical fragility index (§5).
4. **Loop stress test** with threshold surfaces (§7).
Everything else (TDA, critical-slowing-down, Diebold–Yilmaz, synthetic control) is enrichment that deepens the story.

---

## What makes this defensible in front of that audience
Not the method count. It's that the project (a) commits to *formal definitions* of its object, (b) reframes the impossible question (timing) into a solvable one (detection with controlled error), (c) treats the loop *causally and structurally* rather than as correlation, and (d) is brutally explicit about its own statistical power and overfitting risk. A sharp reviewer's hardest questions are answered *in the design*, not in the defense.
