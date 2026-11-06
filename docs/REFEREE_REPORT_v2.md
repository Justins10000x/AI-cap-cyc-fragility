# Referee report on v2 (the CUSUM fragility monitor)

**Reviewer's recommendation: reject v2's empirical claims; accept its framing with major revisions.**

v2 was written and then reviewed by the same system. The review below was produced by
trying to break each claim with a test that could fail, not by rereading the argument.
Every number quoted is reproducible from `src/` and most are enforced by `tests/test_v3.py`.

| # | v2 claim or practice | Verdict | Fixed in v3 by |
|---|---|---|---|
| R1 | Explosive *price* = bubble | **Wrong object** | `fundamentals.py` (valuation-ratio mode) |
| R2 | Gaussian homoskedastic null | **Size 17–19%, not 5%** | wild bootstrap (`psy_v3.py`) |
| R3 | Threshold calibrated at T=300, ARL of "72 years" | **Invalid calibration** | per-series bootstrap at own T |
| R4 | CUSUM "optimal under Lorden / Pollak" | **Overclaim** | retracted; monitor retired |
| R5 | "Alarm at $1.55, now $219: 142×" | **Confounded headline** | per-episode evaluation |
| R6 | Pointwise date-stamping | **Fake episode in 83–91% of bubble-free samples** | family-wise critical values |
| R7 | "SPY is a contaminated control" | **Built on a false positive** | retracted |
| R8 | "NVDA explosive since Nov 2023, still flagged" | **Does not survive** | retracted |
| R9 | Conditional forward returns on z > 1.645 | **Inconsistent flag; eff. N 1–8** | withdrawn |
| R10 | δ, h, minimum lengths chosen ad hoc | **Researcher degrees of freedom** | literature defaults + sensitivity |

---

### R1 — The object under test was wrong (the deepest problem)

Every bubble test is a joint test of a bubble *and* a model of fundamentals (Fama's
joint-hypothesis problem). Testing raw log price implicitly assumes fundamentals are
constant, the worst model available. When earnings grow explosively, price does too, and
the test reports a "bubble". Phillips, Shi & Yu test the S&P 500 *price–dividend ratio* for
exactly this reason; v1 and v2 dropped the denominator.

**Evidence** (`src/boom_vs_bubble.py`, 300 simulated worlds per row, identical 3.1× price run-ups):

| world | test on price | test on price ÷ fundamentals |
|---|---|---|
| neither | 4.0% | 0.7% |
| earnings boom, no bubble | **69.7%** | 0.7% |
| valuation bubble | **38.7%** | **100.0%** |

In this design the price test flags the *non*-bubble more often than the bubble. The ordering
depends on the noise settings; the confound does not. A price-only explosive-root test is a
momentum detector.

### R2 — The null model assumed away volatility clustering

NVDA's weekly returns cluster (autocorrelation of |r| is 0.18 at lag 1; GARCH(1,1)-t
persistence 0.981). Right-tailed unit-root tests over-reject under time-varying volatility
(Harvey, Leybourne, Sollis & Taylor 2016).

**Evidence** (`src/size_study.py`; 400 bubble-free samples of NVDA's length per row):

| bubble-free DGP | v2 GSADF false-positive | v3 (wild bootstrap) |
|---|---|---|
| Gaussian random walk (v2's own assumption) | 3.8% | 4.8% |
| GARCH-t random walk fitted to NVDA | **16.8%** | 6.0% |
| random walk carrying NVDA's actual volatility path | **19.2%** | 6.2% |
| late 5× volatility increase (T=250, test suite) | **~60%** | ~5% |

On data like NVDA's, v2 cried "bubble" about four times as often as it claimed.

### R3 — Calibration did not match the data it was applied to

The operating curve behind "one false alarm per 72 years" was simulated at T=300 and applied
to series with T=865–1,126. The BSADF null distribution depends on T through the minimum
window. The ARL was then extrapolated from a within-sample alarm probability by assuming an
exponential first-passage time, which requires a stationary statistic. The BSADF null is
not stationary in t: its mean drifts from −1.5 to −0.6 as the recursion widens.

### R4 — The optimality claim did not hold

Page's CUSUM is minimax-optimal (Lorden) and Shiryaev–Roberts is optimal (Pollak) when the
increment is the *log-likelihood ratio of the observed process*. v2 accumulated
δz − δ²/2 with z_t the standardised BSADF, a statistic whose consecutive values share almost
their whole estimation window. That is not the LLR of anything, so no optimality result
transfers. The first sanity check showed it: the Shiryaev posterior reached 1.000 on a pure
random walk. v2 noticed the symptom and fixed calibration by simulation, which was right, but
kept the optimality language, which was not. **Retracted.** The monitor is kept at
`src/legacy_v2_cusum_monitor.py` for provenance only.

### R5 — The headline number measured the wrong interval

"Alarm on 2016-09-16 at $1.55; $219.34 today; 142×" spans three distinct regimes and two
crashes that the sentence hides: −54% (trough Dec 2018) and −66% (trough Oct 2022). CUSUM
never resets, so "first alarm to today" is not an episode. The conclusion it was used for
(onset detection doesn't time tops) survives, but it should be shown per episode, and v3 now does.

### R6 — Date-stamping had no multiplicity control over time

Comparing BSADF with a *pointwise* 95% critical value every week for 900 weeks generates
false flags as a matter of course, and they cluster because BSADF is autocorrelated. Under
v2's own Gaussian null, v2's rule dated at least one fake episode in **83%** of bubble-free
samples, and in 89–91% under realistic volatility. v3 uses the Phillips & Shi (2020) logic:
the critical value is the bootstrap quantile of the null's *maximum* BSADF over a trailing
window (52 weeks). A false episode anywhere in a given year then has probability ≈5%,
validated on held-out null paths in the test suite. Over a 17-year sample, that leaves a
14–18% chance of at least one spurious episode, about 1% per year, and it is reported as such.

### R7, R8 — Two real-data claims were artifacts

Under the wild bootstrap, SPY's whole-sample p-value moves from 0.016 to **0.432**. The v2
narrative that SPY was a "contaminated control" was an explanation for a false positive.
NVDA's "explosive regime since Nov 2023, still flagged" was a pointwise-dating artifact (R6).
Under family-wise dating, no episode is live on 18 Sep 2026 at any window from 26 to 156 weeks.

### R9 — Conditional forward returns

The flag used z > 1.645 on the standardised statistic, which is not the date-stamping rule.
With overlapping windows the effective sample was 1–8. Withdrawn, not replaced. Per-episode
evaluation (R5) answers the same question honestly.

### R10 — Researcher degrees of freedom

δ = 2 and h = 100 were chosen after looking at simulations; minimum episode lengths were 4
in one script and 15 in another. v3 takes its parameters from the literature: 5% level,
PSY's ⌈log T⌉ minimum duration, Phillips–Shi family-wise critical values. The one free
choice, the 52-week window, is disclosed, and results are reported across 26/52/104/156 weeks.

---

### What v2 got right, and v3 keeps

- The reframing from *predicting the top* to *detecting a regime with a stated error rate*.
- Calibrating by simulation on the actual statistic rather than by textbook formula.
- The instinct that detection of onset is not a timing signal (now shown per episode).
- The prefix-sum BSADF, validated against the reference implementation to 1e-14.

### A note on process

The fixes above did not come from being cleverer than v2. They came from running tests that
could embarrass the claims, most of which v2 could have run and didn't. The durable lesson for
this repo: **a quantitative claim goes in the README only if a test in `tests/` would fail were
it false**, or, where market data are needed, if the script that produces it is in `src/`
with a fixed seed.
