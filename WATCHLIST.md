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
- Backlog, high-yield spread, CoreWeave interest: SEC company facts and FRED, refreshed by the script
