# Circular-funding ratio v2, part 3: what the filing notes say — 13 November 2026

**Source.** The written notes of Nvidia's 10-Q for the quarter ended 26 July 2026 (filed
26 Aug 2026) and CoreWeave's 10-Q for the quarter ended 30 June 2026. Figures are pulled by
`src/filing_notes.py`, which fails if the filing's wording no longer matches, and saved in
`results/filing_notes.csv`. This layer answers what the company-facts data could not: who
the exposure is with.

## 1. Two corrections to version 1

**The $108.5B of guarantees was not in force at July 2026.** $105B of it is a set of
guarantees signed in **August 2026**, after the quarter ended, on behalf of **an affiliate of
OpenAI**: credit support for leases on a 4.25-gigawatt data-center campus in Ohio built by SB
Energy. Each guarantee starts only when its lease starts, with the first phase expected in
Nvidia's fiscal 2029; Nvidia pays only if the tenant defaults; the cap falls as rent is paid;
and the guarantees end if OpenAI obtains a satisfactory credit rating. Only **$3.5B** of
guarantees (for AI cloud partners' leases) was live at July 2026. So "66% of a year's revenue"
in version 1 mixed money already at work with a ceiling on a future, contingent obligation.
On money actually deployed, the figure is about **33%** ($99B of equity investments against
$303B of trailing revenue).

**New money into private stakes in the July quarter was $13.1B, not $0.7B.** Version 1
inferred $0.7B from the change in the balance and noted it could not separate purchases from
transfers. The notes give it directly: $13.1B of net additions in the quarter and **$31.0B in
the half-year**, with $12.3B moved out to the listed category because investees went public.

## 2. What Nvidia has put in, and promised (at 26 July 2026 unless stated)

| item | $ billions | nature |
|---|---|---|
| Equity investments held | 99 | deployed |
| Further equity investments committed | 25 | promised, $18B of it due within the fiscal year |
| AI cloud agreements | 36 | promised: see below |
| Cloud capacity for Nvidia's own R&D | 29 | promised purchases |
| Data-center leases signed to hand on to third parties | 20 | promised, about 15-year terms |
| Guarantees for AI cloud partners' leases | 3.5 | contingent, live |
| Guarantees for an OpenAI affiliate (Aug 2026) | 105 | contingent, from fiscal 2029, capped |

**The AI cloud agreements are the loop in its plainest form.** Introduced in the July 2026
quarter: an AI cloud buys Nvidia's data-center products, and Nvidia commits to buy cloud
capacity from it, typically over six years, $36B in total. The commitment shrinks as the cloud
sells that capacity to others, and Nvidia may share in that revenue. In Nvidia's words, the
partners "are constrained by the large-scale infrastructure that is required". This is a
seller underwriting demand for its own product. It is disclosed, and it is new.

Also disclosed: memorandums of understanding with capital providers to mobilise more than
$500B of third-party financing for customers' AI infrastructure, with optional
"residual-value support" from Nvidia. These are not definitive agreements.

## 3. Customer concentration

- **Nvidia, direct customers:** in the July 2026 quarter one customer was 16% of revenue; over
  the half-year three were 16%, 15% and 13% (44% together). A year earlier two customers were
  23% and 16% in the quarter. Direct concentration has not risen.
- **Nvidia, indirect:** the filing says "one AI research and deployment company contributed a
  meaningful amount of our revenue by purchasing cloud services from our customers". It is not
  named and no percentage is given.
- **CoreWeave:** its largest customer was 36% of revenue in the June 2026 quarter, down from
  71% a year earlier; the second was 26%. Customers are not named. In January 2026 CoreWeave
  sold $2.0B of new shares to Nvidia.

## 4. What this does to the thesis

It sharpens it and removes some alarm.

- **Less alarming than version 1 suggested:** the single largest number was a capped,
  conditional guarantee that does not begin for years. Direct customer concentration is flat.
- **More specific than version 1 could be:** Nvidia put $31B of new money into private
  companies in six months, has promised $25B more, and has started committing to buy back the
  capacity its own products create ($36B). One unnamed AI company's spending reaches Nvidia
  through several of its customers at once.
- **The dependency has a name.** The largest contingent exposure is to OpenAI's ability to pay
  rent on leases that run twenty years. Nvidia's own risk section says so.

The loop is real, disclosed, and growing quickly from a small base. On deployed money it is
about a third of a year's revenue, not two-thirds.

## 5. Limits

- Equity investees are not listed by name or amount, so stakes still cannot be split between
  customers and non-customers.
- $99B "equity investments" is Nvidia's own total; the tagged private and listed stakes sum to
  $90.7B. The filing does not reconcile the two, and the difference may be warrants and other
  instruments.
- The commitments are gross: several shrink or lapse if conditions are not met.
- One quarter's filing. Nvidia's next 10-Q (quarter to late October 2026) follows its
  17 November results.
- Nothing here is investment advice.
