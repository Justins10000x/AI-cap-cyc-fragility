# Watch list: the warning lights (thresholds pre-registered 21 November 2026)

**Purpose.** Nobody can date the top. What the project can do is say how many of the conditions
that preceded past capex busts are present. Dot-com broke when the money behind the spending ran
out, and spending fell before suppliers' revenue did. These signals are chosen because they
tend to move before that happens.

**Rules.** Thresholds below were written on 21 November 2026, before the next reading of any of
them. They are not to be edited to fit later data; a revised version gets a new date and keeps
this one. Evaluated by `src/watchlist.py`; readings and guidance live in `reported/` with sources.
Every status is a description of conditions, not a trading signal.

## The lights

| code | signal | trips when | baseline (Nov 2026) | next reading |
|---|---|---|---|---|
| T1a | Capex guided down year on year | any of the five guides next year's capex below this year's | no 2027 figures yet; Alphabet and Amazon say 2027 will be "significantly" higher, Meta "aggressive" | late Jan to early Feb calls |
| T1b | Standing capex guidance cut | a guidance midpoint cut by 10% or more | worst: Microsoft −2.9% (~$175B → ~$170B, Oct 28, attributed to supply delays) | Oracle mid-Dec; the rest Jan/Feb |
| T1c | Several cut at once | two or more companies cut in the same earnings round | one (Microsoft) | as above |
| T2 | TSMC monthly revenue | growth below +20% year on year for two consecutive months | +59.7% (October) | ~10 Dec |
| T3 | GPU rental prices | H100 or B200 typical on-demand rate 15% or more below three months earlier | H100 $3.52/hr, B200 $8.38/hr (Nov to date), up 7–8% on October | monthly |
| T4 | Memory contract prices | a forecast or actual quarterly DRAM contract price decline | Q4 2026 +10–15%, Q1 2027 +5–10%, Q2 +3–8%, H2 2027 0–5% (TrendForce) | monthly / quarterly |
| C1 | **Early warning**: GPU rents and memory both falling | T3 and T4 trip together | — | — |
| T5 | Cloud backlog (remaining performance obligations) | any of Microsoft, Alphabet, Oracle, CoreWeave down 3% in a quarter, or down two quarters running | Microsoft flat (−0.1%, Jun → Sep), Alphabet +9.3%, Oracle +4.1%, CoreWeave +5.0% | quarterly filings |
| T6 | Credit | CoreWeave 5-year CDS above 1,500bp, or US high-yield spread above 5.0% | CoreWeave 1,268bp (record, 5 Nov); high-yield 3.32% | daily (reported) |
| T7 | Nvidia days to collect payment | above 75 days | 64 (Oct quarter; 45 in April) | Nvidia 10-Q |
| T8 | OpenAI funding | a round below $852B post-money, a failed or withdrawn raise, or 2026 revenue reported below $30B | last round $852B (Mar 2026) | news |
| T9 | CoreWeave interest / revenue | above 30% in a quarter | 22% (Jun quarter) | CoreWeave 10-Q |

**Not thresholded:** power and data-center deals (utility contracts, grid hookups, construction
starts, cancellations). They matter, but they arrive as scattered announcements with no common
unit, so they are logged as notes rather than given a number that would look more precise than it
is.

## Status at registration: 0 tripped, 10 clear, 2 waiting for data

Lights closest to their thresholds, and worth watching:
- **Microsoft**: a small guidance trim and its first flat quarter of backlog, both explained as
  supply timing, not demand. One more backlog decline would trip T5.
- **CoreWeave's credit**: CDS at 85% of the threshold.
- **Nvidia's collection time**: rising for two quarters (45 → 60 → 64 days).
- **Memory**: price increases are narrowing through 2027, though still increases.

Leading in the healthy direction: TSMC revenue up 60% a year, GPU rental prices rising, Alphabet's
and Oracle's backlogs still growing.

## v1.1: earnings running out of steam (added 21 November 2026)

Added after the depreciation result ([`results/RESULTS_depreciation_v1.md`](results/RESULTS_depreciation_v1.md)),
before any company has filed for the October–December 2026 quarter. The v1 lights above are
unchanged. Computed from SEC filings by `src/watchlist.py` (no reported data needed).

| code | signal | trips when | baseline (Jul–Sep 2026 quarter) | next reading |
|---|---|---|---|---|
| E1a | **Earnings squeeze, all five**: Microsoft, Alphabet, Amazon, Meta, Oracle | their combined operating income is below the same calendar quarter a year earlier while their combined depreciation is above it (quarters in which all five have reported) | operating income $134.3B, +20.5%; depreciation +49.9% | Oct–Dec quarter complete early Feb; trips if combined operating income < $128.7B |
| E1b | **Breadth**: the same squeeze company by company | two or more of the five in the same calendar quarter | one: Meta (operating income $13.0B vs $20.5B; depreciation $6.81B vs $4.76B) | Oracle mid-Dec, the rest late Jan to early Feb |

**Why these.** The thesis is that the build-out breaks when earnings and credit run out of steam.
Depreciation from capex already spent rises on a fixed schedule (about $82B over the next four
quarters at flat capex), so profit falling while depreciation rises is that mechanism showing up
in the reported numbers.

**Rules.**
- Operating income is GAAP as filed, with no adjustment for one-off charges, so there is no room
  for judgement after the fact.
- Oracle's fiscal quarter ending 30 November counts as calendar Q4.
- E1a uses only quarters for which all five have filed.

**Already worth noting.** Combined operating income has been almost flat for three quarters
($130.3B, $133.7B, $134.3B) while quarterly depreciation rose from $36.1B to $44.6B. For the
Oct–Dec quarter, E1a trips if combined operating income falls more than 4.2% below the July–
September level.

**Stated probabilities, for scoring (written 21 Nov 2026, before the data).** These are the
assistant's judgement, not a model output.
- **E1a trips on the Oct–Dec 2026 quarter: 10%.** The October–December quarter is usually the
  strongest of the year for advertising and retail, and the other four grew in July–September.
- **E1b trips on that quarter: 15%.** Meta is likely to stay squeezed against a strong prior-year
  quarter ($24.7B), but a second company would have to see operating income fall year on year,
  and none was close in July–September.

## Status with v1.1: 0 tripped, 12 clear, 2 waiting for data

## v1.2: return on new capital (added 24 November 2026)

Added after returns v1 ([`results/RESULTS_returns_v1.md`](results/RESULTS_returns_v1.md)), before
any company has filed for the October–December 2026 quarter. v1 and v1.1 are unchanged.

| code | signal | trips when | baseline (Jul–Sep 2026) | next reading |
|---|---|---|---|---|
| E2 | **Return on new capital, all five**: pre-tax return on the capital added over the last year | the change in the five's combined 4-quarter operating income ÷ the change in their combined net property and equipment (incl. finance leases) over 4 quarters falls below **12%**, the top of the assumed 10–12% pre-tax hurdle | **14.6%**, down for eight quarters in a row (97% in mid-2024) | Oct–Dec quarter complete early Feb |

**Rules.** Computed by `src/returns.py` from SEC filings: GAAP operating income as filed,
capital as reported, and only quarters in which all five have filed. It is an upper bound on the
return the AI capital earns, because all profit growth is credited to the new capital. So a trip
is a strong signal, and staying clear is a weak one.

**What the next quarter needs.** If capital grows in Oct–Dec as much as it did in Jul–Sep, E2 trips
if the five's 4-quarter operating income is below **$538B** (now $527B). That means
Oct–Dec operating income must grow about 9% on the year before, against 20.5% growth in
Jul–Sep. A faster rise in capital raises the bar.

**Stated probabilities, for scoring (written 24 Nov 2026, before the data).** These are the
assistant's judgement, not a model output.
- **E2 trips on the Oct–Dec 2026 quarter: 20%.** Profit growth has been running well above the
  ~9% needed, but capital is rising faster each quarter.
- **E2 trips on any quarter up to and including Jul–Sep 2027: 55%.** The measure has fallen about
  one to two points a quarter recently (18.3%, 18.0%, 15.9%, 14.6%), and Alphabet, Amazon and Meta
  have said 2027 capex will be higher than 2026's (see T1a baseline).

## Status with v1.2: 0 tripped, 13 clear, 2 waiting for data

## Sources for the baselines

- Capex guidance: [Meta Q3 2026 release (SEC 8-K)](https://www.sec.gov/Archives/edgar/data/0001326801/000162828026066700/meta-09302026xexhibit991.htm);
  [valueaddvc.com capex tracker](https://valueaddvc.com/blog/big-tech-ai-capex-in-2025-microsoft-google-meta-amazon-and-the-spending-race);
  [Oracle Q1 FY27 call (Yahoo Finance/Zacks)](https://finance.yahoo.com/technology/ai/articles/oracle-q1-earnings-call-centers-140000080.html);
  [Oracle Q1 FY27 release (SEC 8-K)](https://www.sec.gov/Archives/edgar/data/0001341439/000119312526387905/orcl-ex99_1.htm);
  [Big Tech Q3 capex deep dive](https://456xresearch.substack.com/p/big-tech-q3-capex-deep-dive-2027)
- [TSMC October 2026 revenue (SEC 6-K)](https://www.sec.gov/Archives/edgar/data/0001046179/000104617926000796/tsm-revenue20261110.htm)
- [GPU Rental Price Index, November 2026](https://gpurentalprices.com/gpu-price-index/2026-11)
- [TrendForce sees DRAM price growth slowing after Q4 2026 (EconoTimes)](https://econotimes.com/TrendForce-Sees-DRAM-Price-Growth-Slowing-After-2026-Fourth-Quarter-1778815)
- CoreWeave CDS: S&P Global Market Intelligence via [Reuters (AOL)](https://www.aol.com/articles/ai-data-center-stocks-slip-112314000.html)
- Backlog, high-yield spread, CoreWeave interest, E1 (operating income, depreciation) and E2 (operating income, capital): SEC company facts and FRED, refreshed by the script
