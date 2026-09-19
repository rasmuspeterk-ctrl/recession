# COUNCIL BRIEF — MOTOR v5.0.1: the first recalibration

## Who you are

You are one of four members of an advisory council convened by Rasmus, a Danish solo developer, on 2026-09-19. The council: **GPT-6 Astra** (OpenAI), **Gemini 3.8 Flash** (Google), **Kimi K3** (Moonshot AI), and **Claude** (Anthropic — the model that co-built v5 with Rasmus and wrote the draft plan under debate; treat Claude as an interested party and attack its plan as hard as anyone else's). You act as senior macro-econometricians. You advise; Rasmus decides. The debate ends when all four vote APPROVE on a consensus text.

## What exists today (MOTOR v5.0, built 2026-08-09 to 2026-08-12)

Built to a blueprint ratified 7/7 by an earlier seven-model council. Key properties:

- **Label:** NBER-onset within the next 4 quarters, quarterly origins. Real-time rule: an origin's label is only known once the NBER announcement table (committed file `nber_announcements.csv`) says it is, with an 18-month floor. Origins inside a recession are censored (not fitted, not scored).
- **Model:** L2-logit (lambda 1, Newton, early stop), features standardised on the training window only.
- **Validation:** purged expanding-origin walk-forward; the only skill metric is log-loss improvement over the unconditional base rate (plus Brier). Episode-block bootstrap (1000 draws, seed 42, 13 blocks) gives an "estimation-sensitivity band" (explicitly not a predictive interval).
- **Gate outcome (step 6):** curve-only logit (10y−3m) scored **+34.3 %** walk-forward log-loss improvement; the full 5-feature model (curve, realrate, dd, d_infl, cape_pct) scored **+33.2 %**. The precommitted fallback fired mechanically: **operational model = curve-only**. The full model is printed every month as "tested, did not pass". Difference 1.1pp is below the noise floor (~4.4pp MDE).
- **Seven candidates tested and rejected**, all published: Sahm (−1.7pp), claims momentum (−61.9pp), permits y/y (−14.5pp), ACM term-premium-adjusted curve (−77.9pp), curve+cape (v5.1, failed anti-contamination era split), AWHMAN hours (v5.2, −0.44pp), and the full model itself. **The feature search is CLOSED**: no new tests without new economic rationale + council mandate + preregistration.
- **Language rules (Section 6):** if the band contains the base rate, the verdict is "NOT DISTINGUISHABLE FROM THE BASE RATE" and the ratio to base rate is suppressed. The verdict text is template-generated and never sharper than the numbers.
- **Prospective ledger (LOG.md):** one row per month, written before the outcome is known, never edited.
  - 2026-08-12: P 20.1 % [14.4–29.2], base 18.2 %, curve +0.87, not distinguishable, ignition: none
  - 2026-09-09: P 18.0 % [12.7–26.3], base 18.2 %, curve +0.96, not distinguishable, ignition: none
- **Worst false alarm in walk-forward:** 93.8 % at origin 2023Q2, no onset followed. Printed permanently.
- **Grand review (18 models, August):** no fatal flaws. Unanimous warning: the biggest error risk is P being too LOW — the model reads the curve's level, not its path after a deep inversion; balance-sheet recessions without a fresh inversion are invisible to it. Kimi's live-risk note: "the 2022–24 inversion without recession will dilute the coefficient at every refit."
- **Three items the review deferred to "the next recalibration":**
  1. *Pooled-origin inflation:* +34.3 % pools 4–8 correlated origins per episode; an episode-decomposed skill table should be published, and leave-one-episode-out (LOEO) considered as co-primary metric.
  2. *Oracle scoring:* scoring conditions on final chronology; a supplementary score without that exclusion (all live-publishable origins) should be printed beside it.
  3. *Language-rule refinement:* "distinguishable from the base rate" should eventually be decided by the paired-difference uncertainty against the base-rate forecast, not by whether the point band crosses 18.2 %.
- Monthly ritual as documented: fetch (20 FRED series, keyless, byte-hashed snapshot) → update 3 manual inputs (CAPE, margin debt y/y, S&P vs 12m high) → **re-anchor weights** (ablation2 --promote + finalize6) → motor --log --json. 47 tests. Public repo.

## The finding that convenes this council (verified 2026-09-19)

The calibration panel's monthly **spine** is `manual/shiller.csv`, a copy of Yale's `ie_data.xls`. That file is frozen: `Last-Modified: 17 Oct 2023`, last row 2023.09 — confirmed by direct download today. `calibrate.build_monthly(shiller, gs10, tb3ms)` uses Shiller's months as the row index; `to_quarterly` then builds ten base features (BASE10 = curve, curve_min12, realrate, d_rate, dd, mom12, infl, d_infl, cape_pct, g), and the row universe is defined as

```python
mask = ~np.isnan(Y_tek)                 # same row universe as step 1
for f in C.BASE10:
    mask &= ~np.isnan(cols[f])
```

so **every feature — including the curve, which FRED supplies through 2026-08 — ends at 2023Q3 in the panel, and the row universe ends 2023Q2.** Consequences:

- Every monthly "re-anchor" since step 6 has produced **identical weights**: `w = [−2.1755, −1.6907]`, `n_obs = 264`, in all nine recalibrations across five snapshots (git history checked). The ritual step exists in the README but has never changed anything.
- 2–3 labeled origins (2023Q3–2024Q1: deep inversion, no onset — precisely the false-alarm quarters) are outside the fit. Kimi's predicted dilution is not happening, by accident rather than design.
- Shiller's own last two rows are preliminary: S&P for 2023-09 is 4515.77 in the file versus a true monthly mean of 4409.1; CAPE 30.81 versus 29.80 from an independent source.

### Verified replacement sources (all free, keyless)

- **S&P 500 monthly:** FRED series `SP500` (daily) → monthly mean. Overlap with Shiller's column 2016-09..2023-09 (85 months): mean deviation **−0.028 %**, identical to 0.1 index points in normal months; the only large deviation is Shiller's preliminary 2023-09. FRED covers 2016-09..2026-09, i.e. all 36 months after Shiller stops.
- **CAPE monthly:** multpl.com table, 1871-02..2026-09, attributed to Shiller. Overlap with Shiller 1990-01..2023-09 (405 months): median deviation **+0.002 %**, only two months deviate more than 1 % — Shiller's own preliminary Aug/Sep 2023 (−1.25 %, −3.28 %).
- **CPI:** FRED `CPIAUCNS` (the same BLS CPI-U NSA series Shiller uses). **Long rate:** Shiller's LTR column is only used as a fill before GS10 begins (1953); irrelevant after.

### Other open items on the table

- `ablation4_features.monthly_mean` is a no-op (the FRED reader had already collapsed weekly claims to the month's last observation), so step 4's `claims_mom` was tested on last-week-of-month values, not the monthly mean the header specifies. The rejection was −61.9pp.
- **Recalibration cadence:** monthly re-anchoring (once the spine is fixed) means weights can change every month, so ledger rows would be produced by different weight vectors. Nobody has decided whether that is acceptable.
- Reporting: when the new origins enter, P and the +34.3 % will move. How that is reported determines whether readers misread it as "the model improved/deteriorated".

## Claude's draft plan under debate (v5.0.1)

1. `fetch.py` builds `shiller.csv` itself: Shiller's history through 2023-07, then FRED SP500 monthly mean + CPIAUCNS + multpl CAPE. The overlap check becomes an automated test.
2. The panel extends to 2026 → 2–3 new labeled origins enter. Expect P to fall somewhat and the skill number to move. Publish whatever comes out.
3. Episode-decomposed skill table printed beside the pooled number (LOEO exists as a gate mechanism in the code already).
4. The paired-difference language rule and an oracle-free supplementary score as ADDITIONAL printed lines, not replacing the verdict.
5. Version bump to v5.0.1 with a README section and a note in the ledger's note column of the first row produced under the new weights.

## Hard constraints (not up for debate)

- The feature search stays closed. Nothing new enters P. A new feature is admissible only as a preregistration for a separate v5.x test with an economic rationale.
- Section 6 language rules, precommitted fallbacks and published failures stay.
- Free, keyless data only; byte-hashed snapshots; reproducible from the repo.
- Historical ledger rows are never edited (only the note column may be filled later).
- One Python file per stage, numpy only. No new dependencies.

## The questions

- **Q1 Spine.** Stitch Shiller (to 2023-07) onto FRED/multpl, or rebuild the entire 1871–2026 spine from multpl + FRED for a single source? What overlap tolerance is acceptable, and which seam tests must exist before the new spine is trusted?
- **Q2 Row universe.** Keep requiring all BASE10 features non-NaN (identical origins for every model in the gate comparison), or require only the fitted model's own features (more origins for curve-only, but the gate compares on different samples)?
- **Q3 Cadence and versioning.** Monthly re-anchoring versus frozen weights re-anchored on a schedule (e.g. annually, or when the NBER announcement table changes)? How is a weight change recorded so ledger rows remain comparable?
- **Q4 The three deferred items.** Exact specifications: what does the episode-decomposed table contain and how is it computed with 12 onsets? How is the paired-difference rule computed, and does it replace or accompany the band rule? What precisely is the oracle-free supplementary score?
- **Q5 monthly_mean.** Fix and re-run step 4 for claims_mom (changing a published number), or document only?
- **Q6 Reporting the change.** When P and skill move because origins were added, how must it be reported (versioning, ledger note, README) so it is not read as a model improvement or deterioration?
- **Q7 What is missing** from the plan that is in scope — data integrity, validation, reporting — but NOT features?
- **Q8 Vetoes.** What in the draft would you block consensus over, and what evidence would change your mind?

## Current reading for reference (snapshot 2026-09-10)

P(NBER-onset within 4 quarters) 18.0 %, band 12.7–26.3 %, base rate 18.2 %. Inputs: curve +0.96 (z −0.39, operational), realrate 1.32, S&P vs 12m high −0.01, d_infl 0.66, CAPE percentile 0.92. Full model would say 9.0 %. Monitors all inactive; Sahm −0.07; HY OAS 271bp; CP spread 3bp; 10Y 4.68 = term premium 0.89 + expected 3.79; Fed funds 3.63, real −0.07; PCE 3m/6m/12m annualised 2.2/4.1/3.7 %. Verdict: not distinguishable from the base rate.
