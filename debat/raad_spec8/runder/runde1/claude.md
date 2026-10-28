**Claude Opus 5.5 — Round 1 (interested party: I proposed this item).**

**A) The agenda**

**Q1 — yes, but only as a logged shadow, and I want the council to test whether even that is worth it.** The
context lines already tell the reader the inversion history. What they cannot do is accumulate evidence: a
shadow P written every month, before outcomes are known, is the only way the memory question can ever be settled,
and it costs nothing in P. The case against: with ≥ 2 post-sealing onsets needed, the record may take decades to
mean anything — but that is also true of the ledger itself, and the record is cheap.

**Q2 — `curve_min12` (rolling 12-month minimum of the monthly curve, ≥ 6 observations), as defined in
`calibrate.build_monthly` since v4.** Three reasons. (1) Least forking: its definition predates E1, E2 and this
debate; every other horizon would be chosen knowing what it shows today. (2) It agrees with E1: every historical
onset came during an inversion or within 9 months of its end, so a 12-month memory covers the documented window.
(3) Its consequence is uncomfortable and therefore honest: today it holds no inversion (+0.24), so the shadow will
read close to P. If the council prefers a longer horizon, it must say why on grounds that do not depend on E2 — and
it should know that 24 or 36 months would light the shadow up precisely in the one cycle (2022–24) that has
produced no recession so far. (b)–(d) all need extra choices (cap, threshold, area) made after E1/E2.

**Q3 — curve + curve_min12, both standardised, λ = 1;** the operational universe (1947Q2), labels, 18-month floor
and eligibility; fitted on the operational calibration's snapshot and R (2026-09-19, R = 2026-09) and refitted
with it every September. Not memory replacing curve: the question is whether memory adds to the level. Fitting on
pre-2027 data is allowed and the spec discloses the contamination: E1–E4, the grand review's diagnosis, yesterday's
backtest, and that v4 once fitted curve_min12 alone with an unrecorded result.

**Q4 — `hovedbog.jsonl` only (`p_hukommelse`, 6 decimals, plus the memory value), from the first row; not in
LOG.md before the 2027 refit (a column change mid-ledger needs its own decision); not on the dashboard.** The
distribution argument from yesterday applies with more force: a model designed in response to a backtest is
exactly the "real P" a screenshot would circulate. The September diagnostics print the tracking record.

**Q5 — unscored tracking; a scored comparison only after ≥ 2 onsets after sealing,** on identical rows against the
logged P, Δ log-loss with an episode-block SD; |Δ| > 1.96·SD_block either way is an agenda item, never a switch.

**Q6 — from the November 2026 row.** Starting before anyone knows how this cycle ends is the whole point.

**B) Verdict on my own draft** — I keep all of it. The weakest part is Q2's "pre-existing definition" tie-breaker:
it is procedural, not economic. If the council has an economic argument for a horizon that does not lean on E2, I
will move.

**C) The biggest risk** — that curve_min12 is a memory with no memory exactly when it matters: if the 2022–24 cycle
ends in a recession in 2027, a 12-month horizon will have been blind to it, and the record will say the shadow
"added nothing" for a reason we chose. The alternative risk is the mirror image, and E2 makes it visible: a
24-month horizon chosen today would read high now and be scored on the cycle that motivated it.
