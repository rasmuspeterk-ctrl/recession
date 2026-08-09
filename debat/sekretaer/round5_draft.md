# MOTOR v5 — CONSENSUS BLUEPRINT, REVISION 2 (final ratification)

The Round-4 vote was 6 APPROVE / 1 REJECT (GPT-5.6 Sol). Sol's two amendments are incorporated in full, plus the non-conflicting reservations of the six approvers. Changelog:

- A1 (Sol): Section 6 rebuilt — primary metric is expanding-origin walk-forward with overlap purging; LOEO and episode bootstrap are demoted to sensitivity/stability analyses, never labeled walk-forward skill.
- A2 (Sol, reinforced by Kimi): onset-based NBER label; real-time label availability governed by a committed table of NBER announcement dates; fixed embargo becomes a demonstrated-conservative floor with mechanical extension.
- A3 (Sol reservation + Grok + Kimi): the monthly gate gets a preregistered numeric margin (−1pp) and the calibration report must print the minimum detectable effect next to the gate result; a monthly switch is framed as a timeliness decision under the stated noise floor, not demonstrated equivalence.
- A4 (Nemotron + Kimi): admission gate requires both metrics to hold in ≥80% of LOEO sensitivity folds; bootstrap-persistence printed for every challenger, <60% flagged.
- A5 (Gemini): ACM near-miss triggers a published truncated-sample secondary diagnostic.
- A6 (Sol + Nemotron + Gemma): ratio-to-base-rate suppressed when the band contains the base rate; band carries the footnote "Not a predictive interval; reflects weight sensitivity to episode composition."
- A7 (GPT-OSS + Gemma): documented update protocol for manual inputs; annual embargo/declaration-lag audit; advance-estimate diagnostic placed inside the monitors block, visually separated from the probability display.

## 0. Philosophy (unchanged)
Radical simplicity (solo-maintainable, stdlib+numpy, free data). Radical honesty: only validated claims get numbers; complexity must buy demonstrated skill; every tested-and-failed idea is published.

## 1. Label [AMENDED A2]
- Target: NBER recession ONSET. Y_t = 1 iff an NBER-dated recession begins in months t+1…t+12 (quarterly formulation: onset within the next 4 quarters). Months inside an already-running recession are excluded from the estimation sample for the onset target's purposes only — the model forecasts entry, not continuation. 2001 enters calibration.
- Real-time label availability: the repo commits a small table of NBER peak/trough announcement dates. At each historical refit date R, a training label is included only if (a) its complete 12-month horizon has elapsed by R, and (b) the NBER status resolving that window had been publicly announced by R. The 6-quarter embargo survives as an operational floor, demonstrated in calibration to cover the historical maximum declaration lag, and extends mechanically while any window month remains undeclared.
- The live output states that P is conditional on NBER dating as of the snapshot date.
- Nemotron's binding condition stands: the advance-estimate diagnostic (two consecutive negative advance GDP prints) is printed in the monitors block — visually separated from the probability display (Gemma), labeled unvalidated, never feeding the probability.
- Optional benchmark row: v4-heritage technical-label model, separately scored, never a target.

## 2. Frequency and horizon [AMENDED A3]
- Kill confirmed: p9 product and per-horizon weight vectors. One direct onset model.
- Step 1 (v5.0): quarterly direct NBER-onset baseline — label is the only change from v4 (S2 attribution; Nemotron's clean baseline).
- Step 2 (same calibration cycle, preregistered): monthly direct-12m ablation, identical features, selection and scoring.
- Gate (preregistered, numeric): monthly becomes the primary published model iff its purged expanding-origin walk-forward log-loss skill is no worse than the quarterly baseline minus 1pp, with quarterly-thinned scores published beside monthly scores. The calibration report prints the minimum detectable skill difference at n≈12 episodes next to the gate result, and any adoption of monthly is framed as a timeliness decision consistent with non-inferiority under that noise floor — not as demonstrated equivalence. If the gate fails, quarterly stays primary and the monthly result is published as failed.

## 3. Engine (unchanged)
L2 logistic regression; penalty selected inside each training window; standardization from training data only. Bayesian variant only as a labeled, preregistered v5.1 experiment.

## 4. Features — re-arbitration and admission [AMENDED A4]
- No grandfather immunity, explicitly including the curve; the full nested selection path is published so the retired +22.9% cannot reappear (Grok).
- Hard cap: 6 features. Locked challengers, one preregistered shot each: real-time Sahm/unemployment transform, initial claims momentum, building permits y/y. HY OAS ineligible (history), remains a monitor.
- Admission requires ALL of: ≥2% relative walk-forward log-loss improvement AND ≥2pp Brier-skill improvement, with BOTH improvements holding in ≥80% of LOEO sensitivity folds (Nemotron); expected coefficient sign in ≥80% of LOEO fits; no single rescuing episode.
- Bootstrap persistence (Kimi): for every challenger, admitted or not, the calibration report prints the sign-frequency of its improvement across the ~1000 episode-bootstrap resamples; any admitted challenger with <60% persistence carries that flag permanently next to its output line.
- Every attempt is published: "admitted" or "tested, not passed."
- The +22.9% headline is retired until re-derived under the nested protocol.

## 5. ACM term-premium curve [AMENDED A5]
Exactly one preregistered substitution test: raw 10y−3m → (10y − ACM TP − 3m), judged on the full purged walk-forward path and LOEO stability, explicitly not on repairing 2023; pre-1961 missing years score at base rate. If it fails by less than 0.5% log-loss, a secondary truncated-sample (1961–2024) comparison is also published to isolate whether the penalty or the signal caused the failure — the adoption decision still follows the penalized full-path test. Ambiguous or failed → raw curve stays, result published.

## 6. Validation and uncertainty [REBUILT — A1, A6]
- PRIMARY metric: expanding-origin walk-forward. At each origin, training uses only data available then, minus (a) labels not yet declarable under Section 1's information-date rule, and (b) all observations whose target windows overlap the evaluation period (purging). Feature and penalty selection occur entirely inside each training window. This is the only thing ever called walk-forward skill.
- SENSITIVITY analyses, reported as such and never labeled walk-forward: leave-one-episode-out (full label-window holdout) and the episode-block bootstrap (~1000 resamples).
- The live probability prints the 10–90% episode-bootstrap band, named "estimation-sensitivity range," with the footnote: "Not a predictive interval; reflects weight sensitivity to episode composition."
- Language rules, mechanical: if the band contains the base rate, the verdict may not say "low"/"high" — it must say "not distinguishable from base rate" — and the ratio-to-base-rate line is suppressed (Sol).
- 2023 stays permanently in the warning block; no QE dummies, balance-sheet features, or regime interactions.

## 7. Kill list (unchanged)
p9 product; per-horizon vectors; LAG 2 bucket table (qualitative inversion line allowed, labeled); aggregate flag counts; flag influence on probability or verdict; action verbs; hardcoded verdict prose.

## 8. Output specification [AMENDED A6, A7]
1. P(onset within horizon) + estimation-sensitivity band + base rate (+ ratio only when the band excludes the base rate).
2. z-scored model inputs.
3. Benchmark table, printed even when unflattering: intercept, curve-only probit (NY-Fed-style), real-time Sahm; Chauvet–Piger separately as a coincident nowcast; optional v4-heritage row. v5 must beat intercept and curve-only; it need not dominate the rest.
4. Monitors block (individually displayed, no aggregate counts, no verdict influence), containing: Sahm, claims, HY OAS, drawdown, the advance-estimate diagnostic, and the inversion note — each labeled "admitted as feature," "tested, not passed," "ineligible (history)," or "unvalidated diagnostic."
5. "Market conditions — not recession evidence" section: CAPE percentile, equity risk premium, margin debt, real cash yield; qualitative only.
6. Verdict: template-generated, never exceeding the numbers; states that P is conditional on NBER dating as of the snapshot date.

## 9. Data and operations [AMENDED A7]
- fetch.py: FRED CSV endpoints via stdlib; dated snapshots in data/raw/, git-committed; prints values with month-over-month diff for a human eyeball. Manual entries (Shiller CAPE, FINRA margin debt) follow a documented, versioned update protocol: value, source, retrieval date logged in the snapshot; MOTOR flags them when older than the snapshot month.
- calibrate.py: all calibration and preregistered tests; writes weights.json (weights + data hash + date + protocol version); commits the NBER announcement-date table; runs an annual audit confirming the embargo floor still covers observed declaration lags (GPT-OSS).
- MOTOR.py: reads weights.json; refuses hand-copied constants; requires --allow-stale for snapshots older than 40 days.
- ALFRED: one-time vintage audit (CPI, unemployment, claims, permits, GDP diagnostic); permanent calibration-only vintage layer iff the audit shows ≥2pp log-loss materiality OR flips any admission decision OR materially shifts historical live probabilities. The live tool never touches ALFRED.

## 10. Build order (unchanged in structure; step 2 now uses the onset label + announcement-date table)
1. Reproducibility refactor — acceptance: re-derives v4's numbers from fresh data; identical weights.json on repeated runs.
2. Label ablation: technical → NBER onset, quarterly held constant.
3. Frequency ablation under the Section 2 numeric gate.
4. Feature re-arbitration + locked challengers + ACM boxed test.
5. Vintage audit; apply Section 9 rule.
6. Output/verdict rebuild per Section 8.
All results published, including failures.

## 11. Dissent and reservations record
All Round-4 reservations are appended verbatim to the blueprint. Reservations do not block; they are part of the published record.
