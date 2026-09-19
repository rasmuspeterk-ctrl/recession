# CONSENSUS TEXT — MOTOR v5.0.1 (draft for ratification)

*Assembled by Claude from Rounds 1–3. Every amendment requested in Round 3 by Astra, Gemini and Kimi is incorporated and marked [A], [G], [K]. Claude's own positions are marked [C] where they were contested.*

## 0. Nature of the release

v5.0.1 is a **data-and-estimation repair**. Unchanged: model class (L2-logit), features, label (NBER onset within 4 quarters, announcement-embargoed, in-recession origins censored), gate metric (pooled walk-forward log-loss vs expanding intercept), Section 6 language rules, the precommitted fallback, every published failure. The feature search stays closed. Nothing enters P. The release is described everywhere as a repair, never as an upgrade or deterioration in predictive skill.

## 1. Spine

1.1 **Stitch, no rebuild.** Yale's `ie_data.xls`-derived file is kept in-repo, immutable, under its own name (`shiller_yale_2023-09.csv`). A separately named composite (`spine.csv`) carries Shiller rows through 2023-07 byte-identical, then FRED `SP500` daily → monthly mean, FRED `CPIAUCNS`, and multpl monthly CAPE from 2023-08 onward. Every row has a provenance column. [A][K]
1.2 **Tolerances, asserted in the test suite.** SP500 overlap: median |dev| ≤ 0.1 %, ≥ 99 % of months within 1 %. CAPE overlap 1990-01..2023-07: median |dev| ≤ 0.1 %, max 1 %. CPI: agreement within rounding, not exact equality. Every exception documented, including Shiller's preliminary 2023-08/09. [A][G][K]
1.3 **multpl parser.** Hard assertions: row count ≥ 1860, first date 1871-02, closed calendar months only. Page bytes hashed into meta.json; revisions diff-marked like FRED; a parse failure produces an `.ukomplet` snapshot, never a partial spine.
1.4 **Two spine tests.** (a) *Legacy replay* — the frozen Yale inputs through the chain must reproduce `w = [−2.1755, −1.6907]`, `n_obs = 264` exactly. (b) *Correction bridge* — the corrected spine truncated at 2023-09 is run and any difference to (a) is measured and reported, not required to be zero. Both are mandatory CI assertions. [A][G][K]
1.5 **Outlier guard.** CAPE outside [5, 60] or |m/m change| ≥ 15 % fails the snapshot unless the run is repeated with `--accept-outlier`. The override records the affected observations, the independent verification performed and the reason — in meta.json and in the ledger note column of the affected reading. It bypasses only the outlier check, never provenance, parsing or eligibility checks. [A][K]
1.6 **Staleness guard.** Hard fail when any input's last observation is older than its source-specific expected maximum age: daily ≤ 7 d, weekly ≤ 14 d, monthly ≤ 45 d, quarterly ≤ 130 d. This is the test that would have caught the frozen spine in October 2023; it is implemented first. [A][K]

## 2. Row universe

The row universe's **start is a protocol constant, 1947Q2** (so the legacy replay holds). Each model's **estimation end** is set by its own features and the label; the operational curve-only model never depends on CAPE availability. [A] A gate comparison is printed **only when origin identities match** — not counts — at every walk-forward training/evaluation split; otherwise it is a hard error, the line prints "comparison unavailable", and curve-only production continues. No pairwise intersection samples, no dual estimates. [A][G][K] The calibration manifest records per-model estimation end and n_obs. [K]

## 3. Calibration cadence and versioning

3.1 **Frozen between events.** Weights, standardisation parameters and the fitted base rate are frozen between re-anchor events. Monthly re-anchoring is abolished; the monthly ritual becomes fetch → manual inputs → motor.
3.2 **Events.** (a) Annually, at the September publication. (b) A hash change of the committed `nber_announcements.csv` that adds a new peak or trough, executed at the **next monthly publication run** under this deterministic rule — never at a discretionary time, never in response to the resulting probability; formatting changes do not trigger; a triggered refit does not reset the September schedule. [A][K]
3.3 **Manifest.** Each event bumps the version (v5.0.x) and commits a calibration manifest: code commit, snapshot hash, announcement-table hash, train-end, n_obs, w, mu/sd, base rate, per-model estimation end and n_obs. Its 8-character hash is written in a new ledger column `kalibrering`. The two existing rows receive the v5.0 manifest hash as a one-time, documented schema migration — metadata only; the readings are untouched.
3.4 **Bridge row.** At each splice the ledger's first row under the new manifest prints P under both the old and the new weights at identical inputs.
3.5 **Refit-time assertions.** An eligibility audit lists the exact dated new origins before fitting; n_obs must grow by exactly that number, else fail. Origins inside the 18-month floor are NaN, never 0 (test). A synthetic new eligible observation must demonstrably reach estimation (test). [A][K]
3.6 **Base rate.** Expanding intercept inside the walk-forward; frozen calibration parameter in the verdict, recorded in the manifest. [G][K]

## 4. Diagnostics printed with the reading (no gate changes)

4.1 **Episode table.** 12 onset rows plus one row containing all negative origins. Per row: n, summed model and baseline log-loss, mean Brier, and the additive contribution 100·Σ(L0−Lm)/ΣL0, which sums exactly to the pooled improvement. Negative-origin losses are additionally shown by the existing chronological bootstrap blocks, whose boundaries are published and never re-optimised. [A][K]
4.2 **LOEO.** Refit excluding each episode's block (no future training data), score the block; all 12, median and minimum printed as sensitivity — never co-primary.
4.3 **Paired rule (supplement).** Δ_b = P_b(x_now) − base_b over the existing episode-block bootstrap draws, paired by draw; the 10–90 % band (80 % coverage, stated as such) excluding zero is the supplementary criterion, printed beside Section 6, whose verdict and ratio suppression are unchanged. Both rules are backtested now over the full walk-forward, same origins, same draws; the disagreement count and the disagreeing origins are published. Any change to the verdict rule is a **separate, later council decision against preregistered criteria**; elapsed time alone is never sufficient. The README states in one sentence that no automatic migration exists. [A][G][K]
4.4 **Historical paired-loss bootstrap** (Gemini's construction) is a skill diagnostic and is printed next to the MDE in the skill section, not in the verdict.
4.5 **Oracle-free supplement.** Label unchanged: new onset within 4 quarters. Eligibility reconstructed from the announcement table as of each origin; mature labels only; the baseline scored on identical coverage; unreconstructable origins reported, never dropped silently. Printed **twice**: over all live-publishable origins, and excluding the *additional live-publishable origins* (in recession but unannounced at the time), whose count and loss contribution are disclosed. That is the terminology; they are not called "correct but late". Scoring any other target, and zero-filling immature labels, are excluded. [A][G][K]

## 5. Claims erratum

`monthly_mean` is fixed; the claims_mom test is re-run exactly as preregistered, no tuning. −61.9pp is published as "superseded implementation result" beside the corrected number. Whatever the result, no promotion; the search stays closed. A pipeline-wide audit of the aggregation bug class covers all 20 fetched series and the 3 manual inputs, with a weekly→monthly aggregation test. [A][G][K]

## 6. Gate on the extended panel

The curve-only-vs-full comparison is re-run and republished (it is part of finalize6). Its outcome **cannot** change the operational model in v5.0.1: if the full model beats curve-only by more than the MDE, that triggers a council decision for a v5.1 protocol — never an automatic switch. The six other rejected candidates keep their published numbers with the footnote "computed on the panel ending 2023Q2". [C, unopposed]

## 7. Reporting

7.1 The README states, **before the run and attributed to Kimi**, the falsifiable prediction: a smaller absolute negative curve coefficient; extended-panel skill below the truncated panel's +34.3 %; a lower P at fixed inputs. It is a prediction, not an acceptance test; the outcome is published whether it succeeds or fails, with Astra's caveat printed verbatim: the fixed-input probability and the historical skill are different objects, and none of the three directions is guaranteed once the intercept, standardisation and sample change together. [A][K]
7.2 Staged bridge at one fixed current input vector: (i) legacy pipeline; (ii) corrected sources on the original origins; (iii) extended panel. Each stage shows P, base rate, band, coefficients, n_obs; the attribution is stated to be order-dependent. [A]
7.3 The walk-forward is published twice, truncated vs extended; common-origin and added-origin skill are reported separately. [A][K]
7.4 Mandatory sentence under the bridge: *"A lower or higher recalibrated probability is changed estimation, not changed economic risk."* Motor prints the version in its header; dashboard.json carries a version field.

## 8. Order of execution

1. Staleness guard, spine tests, eligibility audit and refit assertions are written first and must fail on the current state. 2. The prediction (7.1) is committed to the README. 3. The spine is built; legacy replay passes; correction bridge reported. 4. Refit; manifest; bridge row. 5. Diagnostics (§4). 6. Erratum and audit (§5). 7. Publication (§7). Nothing in §4–§7 is looked at before §1–§3 are committed.

---
**VOTE requested.** First line 'VOTE: APPROVE' or 'VOTE: REJECT'.
