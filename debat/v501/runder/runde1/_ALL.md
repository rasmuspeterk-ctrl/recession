# ROUND1 — samlet


---

## GPT-6 Astra (OpenAI)

## A) Q1–Q8

**1. Spine.** Stitch through 2023-07; FRED cannot reconstruct an internally consistent 1871–2026 replacement, and changing validated history adds unnecessary revision risk. Preserve the original file and construct a separately named composite with source provenance per column/month, excluding incomplete months and data unavailable at the forecast timestamp. On the non-preliminary overlap, require median absolute relative deviation ≤0.1% and at least 99% of observations within 1%; individually document every exception, including August–September 2023. Test unique consecutive months, units, positivity, historical immutability, daily-to-monthly aggregation, and independent recomputation of every seam-crossing rolling feature; do not smooth genuine market movements.

**2. Row universe.** Reject both blanket BASE10 completeness and comparisons on different samples: estimation requires the model’s own features; comparisons require a common evaluation sample. For models \(A,B\), use \(E_{AB}=E_A\cap E_B\), with identical label-maturity, censoring and purge rules; report each model’s training and evaluation counts. Operational curve-only estimation should not depend on CAPE availability, but its expanded-sample score must be distinguished from its common-sample comparison score. This repair does not reopen promotion: curve-only remains operational and every published rejection remains visible.

**3. Cadence and versioning.** Freeze weights, standardisation parameters and the fitted base rate between annual recalibrations, scheduled for the first September publication; v5.0.1 is an explicitly exceptional repair. Each month still updates predictors, while NBER-table changes update eligibility and scoring without triggering an unscheduled refit. Every ledger row must identify code version, calibration ID, data-snapshot hash, announcement-table hash, training cutoff, sample count, coefficients, standardisation and base rate through an immutable linked manifest. Comparing probabilities from different calibrations is legitimate only when the calibration change is disclosed.

**4. Deferred diagnostics.** For each of the 12 onsets, assign eligible positive origins whose four-quarter horizon first contains that onset; put all remaining negative origins in a thirteenth, explicitly non-episode row. Print counts, summed model/base losses, mean Brier scores and contribution \(100\sum_{i\in e}(L_{0i}-L_{mi})/\sum_iL_{0i}\), which adds exactly to pooled percentage improvement; also print negative-origin losses by the existing 13 chronological bootstrap blocks, whose boundaries must be published. LOEO remains sensitivity analysis, not a retrospectively introduced co-primary gate; any rerun must preserve walk-forward timing and remove the held-out block from subsequent training.

For the language supplement, jointly bootstrap the fitted probability and corresponding base rate using identical existing episode-block draws: \(\Delta^{(b)}=p^{(b)}-p_0^{(b)}\); use the existing band’s nominal coverage and percentile convention, retain Section 6’s verdict and ratio suppression, and distinguish this parameter-sensitivity comparison from historical skill uncertainty. The oracle-free supplement scores **every feature-available quarterly origin where production would issue a forecast**, including retrospectively recession-dated origins, using archived or timestamp-reconstructed forecasts and \(Y_t=1\) only for a *new* onset in the next four quarters; score only after label maturity, apply identical coverage to the baseline, and report unreconstructable origins rather than silently dropping them.

**5. Claims aggregation.** Fix and rerun the exact original claims specification as a preregistered implementation correction, with no tuning. Aggregate the underlying weekly observations by arithmetic mean according to observation date, retain those raw observations, and test missing-week and release-timing handling. Publish the original −61.9pp as “superseded implementation result” beside the corrected result; even a reversal grants no automatic feature promotion.

**6. Reporting.** Publish a calibration bridge at one fixed current input vector: original pipeline, corrected sources on original origins, model-specific completeness on the historical date span, then extension through the new eligible cutoff. Show probability, base rate, band, coefficients and sample count at each stage, acknowledging that this sequential attribution is order-dependent. For skill, separate rescoring the original evaluation origins from performance on newly eligible origins; their changing composition must not masquerade as improved methodology. Bump to v5.0.1, retain old artifacts, append the first new ledger row with a calibration-change note, and describe this as a **data-and-estimation repair**, not an upgrade in predictive skill.

**7. Missing controls.** Require an origin-level eligibility audit listing missing features, censoring, horizon completion, announcement maturity and purge status; “2–3 new origins” must become an exact dated list before fitting. Separate observation dates from publication dates, and explicitly label revised-history backtests rather than calling them fully real-time. Add freshness assertions, fail-closed source-schema checks, frozen fetch timestamps, snapshot replay, and a regression test proving that an eligible synthetic new observation reaches estimation. Monthly forecast rows have overlapping horizons and must not be counted as independent quarterly validation observations.

**8. Vetoes.** I block mutable overwriting of `shiller.csv`, BASE10-driven operational eligibility, undocumented automatic promotion/refitting, and any “oracle-free” score that silently retains retrospective recession exclusions. I also block interpreting a lower recalibrated probability as reduced economic risk: that mixes changed evidence with changed estimation. Reproducible manifests, eligibility tables, common-sample scores and the fixed-input calibration bridge would remove these vetoes.

## B) Verdict on Claude’s five points

**REQUEST CHANGES. None stays as written.**

1. **Amend:** immutable composite, provenance and integrity tests.
2. **Amend:** exact eligibility audit; remove the expectation that P falls.
3. **Amend:** additive episode decomposition and negative-origin attribution.
4. **Amend:** specify paired resampling and genuinely non-oracle scoring.
5. **Amend:** add calibration manifests, cadence and attribution bridge.

Strike no objective; strike implicit automatic re-promotion and mutable source replacement.

## C) Biggest risk

Annual freezing delays incorporation of newly matured inversion false alarms by up to twelve months. That is the explicit cost of calibration stability—not evidence that stale weights are economically superior.

---

## Gemini 3.8 Flash (Google)

### A) Q1–Q8: Econometric Positions

**Q1 Spine.** Stitch Shiller to 2023-07; do not rebuild the 1871–2023 history from multpl. Scraping multpl for 150 years introduces third-party pipeline risk when Shiller’s academic spreadsheet is the accepted benchmark. Overlap check must run on the 84 months from 2016-08 to 2023-07 with strict numerical tolerances: $\max |\Delta \ln(\text{SP500})| < 0.005$, $\max |\text{CPI}_{\text{FRED}} - \text{CPI}_{\text{Shiller}}| = 0.0$ (exact integer index match), and multpl CAPE $\max |\Delta| \le 0.35$ index points. Abort build on any seam violation.

**Q2 Row universe.** Keep requiring all BASE10 features non-NaN. Comparing curve-only against 5-feature candidates on different row samples invalidates the gate: log-loss improvements are only identifiable on a common sample space $\Omega_{\text{eval}}$. If curve-only trains on 2023Q3–2026Q2 while multivariate models drop out due to missing inputs, the precommitted fallback comparison is mathematically compromised.

**Q3 Cadence and versioning.** Veto monthly re-weighting. Label arrival occurs at business-cycle frequency; refitting weights monthly across quarters with zero new label realizations injects high-frequency noise into L2-logit coefficients without information gain. Re-anchor weights **only upon an NBER chronology update** or **annually every September**. Record the change in `LOG.md` by appending an explicit 8-character `weights_hash` column so every historical output maps to an immutable parameter vector.

**Q4 Deferred items.**
*   *Episode-decomposed skill:* Report a 13-row table (12 onsets + 1 non-recession false alarm block 2022–2024). For episode $j$, define $\Delta \text{LL}_j = \sum_{t \in E_j} \left[ \ln P(Y_t \mid \bar{y}) - \ln P(Y_t \mid \hat{p}_t) \right]$, along with Brier score and episode observation count.
*   *Paired-difference rule:* Compute $d_t = \text{Loss}(\bar{y}, Y_t) - \text{Loss}(\hat{p}_t, Y_t)$. Block-bootstrap the mean paired difference $\bar{d}$ across the 13 episode blocks (10,000 draws). The model is "distinguishable" from the base rate iff the 90% empirical interval of $\bar{d}$ is strictly positive ($P(\bar{d} \le 0) < 0.05$). Print this as an accompanying $p$-value; do not replace the point band.
*   *Oracle-free score:* Evaluate all origins $t$ with $t + 4Q \le T_{\text{current}}$, imputing $Y_t = 0$ for unannounced origins. This immediately penalises the 2023 false alarm in the score without waiting for NBER's formal 18-month clearance.

**Q5 monthly_mean.** Document only; do not re-run. Claims momentum was rejected at $-61.9\text{pp}$; shifting from the 4th weekly print to the 4-week monthly mean cannot bridge a 60-percentage-point performance deficit. Modifying code to alter historical gate results retroactively violates preregistration hygiene. Record the code defect in `ERRATA.md` and leave the rejection intact.

**Q6 Reporting the change.** Frame this strictly as a **pipeline bug fix restoring missing historical origins**, not a model improvement or recalibration choice. Bump to v5.0.1. The README must publish a static reconciliation table showing the exact parameter shift:
$$\Delta w = w_{\text{v5.0.1}} - w_{\text{v5.0.0}}, \quad \Delta \text{Skill} = \text{Skill}_{\text{v5.0.1}} - 34.3\%$$
Accompany this with the mandatory explanatory text: *"Inclusion of 2023Q3–2024Q1 incorporates the recent inversion false alarm into the fitting sample, mechanically compressing the yield curve slope coefficient."*

**Q7 What is missing.** 
1. *Stale data assertions:* An automated check ensuring that FRED and multpl latest dates are within 45 days of the execution date, preventing silent panel freezing in the future.
2. *Base-rate updating specification:* The draft does not state whether the unconditional base rate $\bar{y} = 18.2\%$ is fixed at step 6 or updates as denominator $N$ expands. It must be explicitly defined as expanding: $\bar{y}_T = \frac{1}{T}\sum_{t=1}^T Y_t$.

**Q8 Vetoes.** I veto **monthly re-anchoring of weights**. Refitting coefficients on identical label sets each month merely tracks minor revisions in historical macro data while churning ledger probabilities. I will withdraw this veto only if Claude provides proof that monthly re-estimation out-predicts fixed-weight schedules over historical out-of-sample drawdowns.

---

### B) Verdict on Claude’s Draft Plan

1. **Point 1 (Spine construction): KEEP**, but require hard assertion limits on the 2016–2023 overlap seam ($\Delta \text{CAPE} \le 0.35$).
2. **Point 2 (Panel extension & refit): AMEND**. Extend the panel immediately to incorporate the 2023Q3–2024Q1 origins, but freeze the resulting weight vector. Do not allow continuous monthly refitting.
3. **Point 3 (Episode table): KEEP**. Essential to diagnose whether +34% skill is driven by 1970s/1980s cluster points.
4. **Point 4 (Paired-difference & oracle-free metrics): KEEP**. Must be printed as auxiliary diagnostic lines below the operational verdict, preserving Section 6 formatting.
5. **Point 5 (Versioning and logging): AMEND**. In addition to the note column, add a formal `param_hash` or explicit version tag inside `LOG.md` machine-readable output to prevent ambiguous historical tracking.

---

### C) Single Biggest Risk

**Mechanical coefficient dilution blinding the model to non-inversion onset.** 

Incorporating the 2022–2024 deep curve inversion as non-recession quarters ($Y=0$) into the tiny sample ($N \approx 267$) will compress the slope coefficient $\beta_{\text{curve}}$. MOTOR already reads only curve *level*, not curve *path* or post-inversion steepening. Compressing $\beta_{\text{curve}}$ directly lowers $P$ across the entire operational domain. If late-cycle credit stress or labor deceleration triggers a balance-sheet onset without re-inverting the 10y−3m curve, the diluted v5.0.1 model will severely understate recession risk, printing near the base rate until the economy is already in contraction.

---

## Kimi K3 (Moonshot AI)

## A) Q1–Q8

**Q1 — Stitch, don't rebuild.** Keep Shiller byte-identical through 2023-07 (dropping the two preliminary rows), then append FRED SP500 monthly means, CPIAUCNS, and multpl CAPE. A full rebuild swaps the primary source for an unattributed aggregator across 1,800+ months to fix a two-row problem, and it silently moves every historical fitted value behind the published +34.3 %. Tolerances: SP500 overlap 2016-09..2023-07 mean |dev| ≤ 0.1 %, max ≤ 0.5 %; CAPE overlap 1990-01..2023-07 median |dev| ≤ 0.1 %, max ≤ 1 % excluding Shiller's preliminary months; CPI ratio within 0.3 %. Seam tests: (i) stitched file byte-identical to the frozen file through 2023-07; (ii) m/m log-change at the seam inside the 1st–99th percentile of historical changes; (iii) a staleness guard — every spine input's last row within 45 days of fetch date, hard fail otherwise. That guard is the test that would have caught this bug three years ago.

**Q2 — Keep the common all-BASE10 mask.** The fallback fired on a 1.1pp gap against a 4.4pp MDE; letting curve-only and the full model score different origin sets confounds exactly that comparison. The spine fix restores timeliness, so the mask's cost is now ~zero. Add one test: origins inside the 18-month floor must be NaN in Y, never 0 — with new origins flowing in, a silent zero-fill is the next contamination waiting to happen.

**Q3 — Scheduled re-anchoring, not monthly.** Refit when the NBER announcement table changes or 12 months have elapsed, whichever first. Monthly refits add at most one labeled origin (18-month floor) to 264+; the weight jitter is pure noise and destroys ledger comparability. Every ledger row carries a weight-version tag: SHA256(weights ‖ n_obs ‖ train-end)[:8]. At a refit, the splice row prints P under both the old and new weight vectors — a bridge line, like a national-accounts revision overlap.

**Q4 — Specs.** Episode table: one row per NBER episode k (12 in sample) over the episode block (onset −8q through recession end, matching the 13 bootstrap blocks): n_pos, n_neg, skill_k = 1 − LL_model/LL_base, Brier_k. LOEO: refit excluding block k, score block k; report median LOEO skill and count positive. Expect 2020 to fail (no inversion) — print it anyway. Paired-difference rule: at the live origin, Δ_b = P_t^(b) − π̂^(b) across the 1000 estimation-bootstrap draws, paired by draw; "distinguishable" iff the 90 % CI of Δ excludes 0. It accompanies the band rule for two quarters; then the council votes with the historical disagreement rate in hand. Oracle-free score: walk-forward where censoring and labels use only the announcement table as of each scoring date, with the base rate expanding in real time; printed beside the primary.

**Q5 — Fix and re-run.** The published −61.9pp describes a test the header says used monthly means but the code ran on last-week-of-month; that is an erratum, not a new test. Publish the corrected number, keep claims_mom rejected regardless, state the search stays closed. Add an aggregation test asserting weekly→monthly mean, and audit the other 19 series and 3 manual inputs for the same bug class.

**Q6 — Label v5.0.1 a data correction.** Model class, features, gate, protocol unchanged. Publish the walk-forward twice — truncated panel vs extended panel — side by side; the difference is by construction entirely the added origins (2023Q3–2024Q1, the false-alarm quarters). State the expected direction in advance: curve coefficient, skill, and current P should all fall. The dilution I flagged in August was not happening only because the spine was frozen; it now arrives by design rather than by accident, and the README must say so before the numbers, not after.

**Q7 — Missing.** (i) The no-change alarm: nine identical recalibrations should have tripped something — test that a new snapshot changes n_obs or weights, else fail. (ii) Re-run the gate comparison (curve-only vs full) on the new panel and republish, with the seven rejections footnoted as truncated-panel numbers. (iii) An explicit rule that the fallback does NOT re-fire on a data correction: if the full model now beats curve-only by more than the MDE, that triggers a council decision for v5.1, not an automatic switch. (iv) multpl is a single unattributed source: quarterly CAPE cross-check against an independent computation, plus level (5–60) and m/m-change (< 15 %) guards. cape_pct feeds only the printed full model, not operational P — but the whole panel depends on it through the common mask.

**Q8 — Three blocks.** (1) Full spine rebuild from multpl: changes all of history to fix two rows. I relent only if two independent sources agree with Shiller to < 0.1 % on 95 % of months. (2) Automatic re-firing of the gate fallback on the new panel: precommitment cuts both ways — you don't re-run the gate until it says what you want. No evidence changes this; only a preregistered v5.1 protocol. (3) Replacing the band rule with the paired rule in the same release: one release, one kind of change. I relent if backtests show the two rules disagree on > 20 % of origins.

## B) Verdict on Claude's draft

**Point 1: keep, amended** — add byte-identity through 2023-07, the staleness guard, explicit tolerances; archive the frozen file in-repo. **Point 2: keep, amended** — "publish whatever comes out" is too casual for a project whose entire credibility is precommitment; require the side-by-side decomposition and the pre-stated expected direction, and state the fallback does not re-fire. **Point 3: keep, with my Q4 spec** — LOEO printed, not co-primary; 12 episodes give LOEO too much variance to crown. **Point 4: keep as written** — additional lines, not replacements; correct call. **Point 5: keep, amended** — weight-version tags on every row, bridge line at the splice. Strike nothing outright. The plan's real defect is what it omits: cadence (Q3) and the fallback re-fire rule.

## C) Biggest risk in my own proposal

The seam is untestable beyond the overlap window. multpl is unattributed; if its CAPE construction drifts from Shiller's, cape_pct's percentile becomes nonstationary across the seam, and the byte-hash won't catch it — content is supposed to change monthly. My guards catch level breaks, not slow drift, and the quarterly independent cross-check is specified in spirit but not yet sourced. If that cross-check can't be made keyless and reproducible, the CAPE column — and via the common mask, the entire panel — rests on one scraper's goodwill.

---

## Claude (Opus 5) (Anthropic — interested party)

**Disclosure.** I co-built v5 and wrote the draft plan. Writing this proposal made me change my own plan on two points (Q3, Q4b); I flag them below.

## A) Q1–Q8

**Q1 Spine — stitch, do not rebuild.** Shiller 1871..2023-07 is the canonical, hand-corrected history the published +34.3 % was computed on; rebuilding it from multpl would move every historical row by tiny amounts and break the reproducibility chain to the published result for zero gain. Stitch at the last non-preliminary Shiller row (2023-07), replacing Shiller's own preliminary 2023-08/09 with FRED SP500 monthly mean + CPIAUCNS + multpl CAPE. Tolerances, asserted in the test suite: SP500 |dev| ≤ 0.1 % in every overlap month except the two documented preliminary months; CAPE median |dev| ≤ 0.05 % and no month > 0.5 % outside those two. Three seam tests must exist before the spine is trusted: (i) the overlap test above; (ii) a *truncation regression test* — truncate the new spine at 2023-09, run the calibration chain, and it must reproduce `w = [−2.1755, −1.6907]`, n_obs 264 exactly, proving the stitch did not touch history; (iii) a continuity test that the derived features (dd, mom12, cape_pct) show no seam-attributable jump between 2023-07 and 2023-08. multpl is a scraped page, not an API: the parser must assert row count ≥ 1860 and first date 1871-02, and a format change must produce an `.ukomplet` snapshot, never a silent partial spine. The page bytes are hashed into meta.json like every FRED series, and revisions get the existing "REVIDERET historik" diff mark.

**Q2 Row universe — keep identical origins.** The gate compares models on the same rows by design; once the spine runs to 2026 the data loss from requiring all BASE10 is zero (the only remaining loss is CAPE's 120-month burn-in, which ends in 1881 — irrelevant). Loosening the rule buys nothing and costs the comparability the step-6 verdict rests on.

**Q3 Cadence — I change my own plan: freeze weights, re-anchor as a versioned event.** Monthly re-anchoring means each ledger row is produced by a different weight vector, so the ledger stops testing a fixed object; a reader cannot separate "new data" from "new weights". Proposal: weights are frozen per version. Re-anchoring happens (a) once a year in January, and (b) immediately when the NBER announcement table gains a row — never silently, never monthly. Each re-anchor is a version bump (v5.0.x), gets a README table row (n_obs, episodes, w, skill, band, and P on the *same* snapshot under old and new weights), and the note column of the first ledger row under the new weights records the version. The monthly ritual becomes fetch → manual inputs → motor: simpler, and it matches the simplicity principle.

**Q4a Episode table.** For each of the 12 onsets: the origins whose 4-quarter window contains that onset (the Y=1 origins), their walk-forward log-loss under the model and under the expanding-window intercept, and the resulting per-episode skill; plus one row for all Y=0 origins pooled (the false-alarm cost) and the pooled total. Alongside: LOEO — refit excluding each episode's block, score on it, report all 12, the median and the minimum. LOEO stays *diagnostic*; the pooled walk-forward log-loss remains the primary gate. Promoting LOEO to co-primary now would be a post hoc metric change, exactly what the protocol forbids.

**Q4b Paired rule — I amend my plan: it should become the rule, after a parallel year.** We already have 1000 episode-block bootstrap draws of the weights. For each draw b, compute Δ_b = P_b(x_now) − base_b, where base_b is the base rate *in that resample* — the comparison is then paired, because P and base rate come from the same resample, which the current rule (resampled P vs a fixed 18.2 %) is not. Verdict "distinguishable" iff the 10–90 % band of Δ excludes zero. Print both rules for twelve months; then the paired rule becomes the verdict rule. Risk I accept: if the paired rule happens to flip the current verdict it will look convenient; publishing both for a year is the protection.

**Q4c Oracle-free supplementary score.** The current score only rates origins that the *final* chronology says were outside a recession. A live user in 2008Q2 did not know that. Supplementary score: rate every origin that was live-publishable under the announcement rule as of that date (i.e. NBER had not yet announced an ongoing recession), against the label Y′ = 1 if a recession was ongoing at the origin *or* an onset fell within the next 4 quarters. This is what a real-time user experienced. Printed beside the primary score, never replacing it.

**Q5 monthly_mean — fix and re-run, publish both numbers.** Leaving code that contradicts its own specification is incompatible with the protocol. Re-running a preregistered test with the corrected implementation is not reopening the search; proposing a new hypothesis would be. Old (−61.9pp) and new numbers stand side by side in README.

**Q6 Reporting.** Version bump v5.0.1. README section with a before/after table where the decisive column is P on the *same* September snapshot under old and new weights — that isolates the weight effect from the data effect. The first ledger row under new weights carries the version in its note column; motor prints the version in its header; dashboard.json carries it as a field. The sentence "the model did not improve or deteriorate; its calibration sample grew by N origins" is printed verbatim.

**Q7 Missing.** (1) The truncation regression test (Q1 ii) — it is the proof, not a nicety. (2) Re-run the step-1 acceptance test against v4 constants to confirm pre-seam history is intact. (3) The bootstrap's 13 episode blocks must be re-derived from the new panel, not hardcoded — verify finalize6. (4) A version field in the dashboard contract. (5) fetch.py must treat multpl exactly like FRED: hashed, diffed, veto-capable.

**Q8 Vetoes.** I would block: (a) rebuilding the pre-2023 history from multpl — it breaks reproducibility for no gain; (b) making LOEO co-primary or otherwise changing the gate metric post hoc; (c) anything entering P. Evidence that would move me on (a): if the truncation test *fails* — i.e. the stitch cannot reproduce the old weights — then the stitch is broken and a full rebuild with a fresh acceptance test is the honest alternative.

## B) Verdict on the draft plan

Keep 1 and 5 as written. **Amend 2**: origins enter under a frozen-then-versioned cadence, not monthly. **Amend 4**: specified as Q4a–c above; the paired rule becomes the verdict rule after a parallel year. Keep 3 but LOEO explicitly diagnostic.

## C) Biggest risk in my own proposal

multpl is the only non-FRED, non-official source in the pipeline: a scraped HTML table with no API, no versioning and no revision log. The hashing and diff marks catch *that* it changed, not *why*. If multpl silently re-bases CAPE, our cape_pct history drifts under us while every test passes.
