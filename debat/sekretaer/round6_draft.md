# MOTOR v5 — CONSENSUS BLUEPRINT, REVISION 3 (final ratification)

Round-5 vote: 6 APPROVE / 1 REJECT (GPT-5.6 Sol). Sol identified that Revision 2's label-availability rule could not assign NEGATIVE labels mechanically (NBER announces recessions, never "no recession"), and stated that one operational amendment flips him to APPROVE. This revision contains exactly that amendment and nothing else:

- A8 (Sol, Round 5): Section 1's label-availability rule replaced by the fully mechanical real-time rule below. It subsumes Kimi's Round-4 "automatic floor with mechanical extension" reservation and formalizes the annual embargo audit (GPT-OSS/Gemma) as the L_R update. No other section changed from Revision 2.

## 0. Philosophy (unchanged)
Radical simplicity (solo-maintainable, stdlib+numpy, free data). Radical honesty: only validated claims get numbers; complexity must buy demonstrated skill; every tested-and-failed idea is published.

## 1. Label [AMENDED A8 — the only change in Revision 3]
- Target: NBER recession ONSET. Y_t = 1 iff an NBER-dated recession begins in months t+1…t+12 (quarterly formulation: onset within the next 4 quarters). The model forecasts entry, not continuation. 2001 enters calibration.
- Label availability — mechanical real-time rule (Sol):
  - For target window W_t = (t, t+12], the observation becomes training-eligible only when its horizon has ended and at least 18 additional months have elapsed.
  - At each refit date R, reconstruct the NBER chronology publicly available at R using the committed announcement-date table.
  - Assign Y_t(R) = 1 only if, by R, NBER had announced a peak/onset falling inside W_t; otherwise assign Y_t(R) = 0.
  - Exclude observations inside a running recession only when that recession's onset had been announced by R. Never use subsequently published dates to alter what a historical fit knew.
  - Report any historical case where a provisional zero later changed to one.
  - At each annual audit, set the prospective embargo to L_R = max(18 months, largest announcement lag observed by R). Changes apply prospectively and increment the protocol version; they never rewrite earlier information sets.
- The live output states that P is conditional on NBER dating as of the snapshot date.
- Nemotron's binding condition stands: the advance-estimate diagnostic (two consecutive negative advance GDP prints) is printed in the monitors block — visually separated from the probability display (Gemma), labeled unvalidated, never feeding the probability.
- Optional benchmark row: v4-heritage technical-label model, separately scored, never a target.

## 2. Frequency and horizon (unchanged from Revision 2)
- Kill confirmed: p9 product and per-horizon weight vectors. One direct onset model.
- Step 1 (v5.0): quarterly direct NBER-onset baseline — label is the only change from v4 (S2 attribution; Nemotron's clean baseline).
- Step 2 (same calibration cycle, preregistered): monthly direct-12m ablation, identical features, selection and scoring.
- Gate (preregistered, numeric): monthly becomes primary iff its purged expanding-origin walk-forward log-loss skill is no worse than the quarterly baseline minus 1pp, with quarterly-thinned scores published beside monthly scores. The calibration report prints the minimum detectable skill difference at n≈12 episodes next to the gate result; adoption of monthly is framed as a timeliness decision consistent with non-inferiority under that noise floor, not demonstrated equivalence. Gate fails → quarterly stays primary, monthly published as failed.

## 3. Engine (unchanged)
L2 logistic regression; penalty selected inside each training window; standardization from training data only. Bayesian variant only as a labeled, preregistered v5.1 experiment.

## 4. Features — re-arbitration and admission (unchanged from Revision 2)
- No grandfather immunity, explicitly including the curve; the full nested selection path is published so the retired +22.9% cannot reappear.
- Hard cap: 6 features. Locked challengers, one preregistered shot each: real-time Sahm/unemployment transform, initial claims momentum, building permits y/y. HY OAS ineligible (history), remains a monitor.
- Admission requires ALL of: ≥2% relative walk-forward log-loss improvement AND ≥2pp Brier-skill improvement, with BOTH improvements holding in ≥80% of LOEO sensitivity folds; expected coefficient sign in ≥80% of LOEO fits; no single rescuing episode.
- Bootstrap persistence: for every challenger, admitted or not, the calibration report prints the sign-frequency of its improvement across the ~1000 episode-bootstrap resamples; any admitted challenger with <60% persistence carries that flag permanently next to its output line.
- Every attempt is published: "admitted" or "tested, not passed."
- The +22.9% headline is retired until re-derived under the nested protocol.

## 5. ACM term-premium curve (unchanged from Revision 2)
Exactly one preregistered substitution test: raw 10y−3m → (10y − ACM TP − 3m), judged on the full purged walk-forward path and LOEO stability, explicitly not on repairing 2023; pre-1961 missing years score at base rate. If it fails by less than 0.5% log-loss, a secondary truncated-sample (1961–2024) comparison is also published; the adoption decision still follows the penalized full-path test. Ambiguous or failed → raw curve stays, result published.

## 6. Validation and uncertainty (unchanged from Revision 2)
- PRIMARY metric: expanding-origin walk-forward. At each origin, training uses only data available then, minus (a) labels not yet eligible under Section 1's mechanical rule, and (b) all observations whose target windows overlap the evaluation period (purging). Feature and penalty selection occur entirely inside each training window. This is the only thing ever called walk-forward skill.
- SENSITIVITY analyses, reported as such, never labeled walk-forward: leave-one-episode-out (full label-window holdout) and the episode-block bootstrap (~1000 resamples).
- The live probability prints the 10–90% episode-bootstrap band, named "estimation-sensitivity range," with the footnote: "Not a predictive interval; reflects weight sensitivity to episode composition."
- Language rules, mechanical: if the band contains the base rate, the verdict may not say "low"/"high" — it must say "not distinguishable from base rate" — and the ratio-to-base-rate line is suppressed.
- 2023 stays permanently in the warning block; no QE dummies, balance-sheet features, or regime interactions.

## 7. Kill list (unchanged)
p9 product; per-horizon vectors; LAG 2 bucket table (qualitative inversion line allowed, labeled); aggregate flag counts; flag influence on probability or verdict; action verbs; hardcoded verdict prose.

## 8. Output specification (unchanged from Revision 2)
1. P(onset within horizon) + estimation-sensitivity band + base rate (+ ratio only when the band excludes the base rate).
2. z-scored model inputs.
3. Benchmark table, printed even when unflattering: intercept, curve-only probit (NY-Fed-style), real-time Sahm; Chauvet–Piger separately as a coincident nowcast; optional v4-heritage row. v5 must beat intercept and curve-only; it need not dominate the rest.
4. Monitors block (individually displayed, no aggregate counts, no verdict influence): Sahm, claims, HY OAS, drawdown, the advance-estimate diagnostic, the inversion note — each labeled "admitted as feature," "tested, not passed," "ineligible (history)," or "unvalidated diagnostic."
5. "Market conditions — not recession evidence" section: CAPE percentile, equity risk premium, margin debt, real cash yield; qualitative only.
6. Verdict: template-generated, never exceeding the numbers; states that P is conditional on NBER dating as of the snapshot date.

## 9. Data and operations (unchanged from Revision 2)
- fetch.py: FRED CSV endpoints via stdlib; dated snapshots in data/raw/, git-committed; month-over-month diff printed for a human eyeball. Manual entries (Shiller CAPE, FINRA margin debt) follow a documented, versioned update protocol; MOTOR flags them when older than the snapshot month.
- calibrate.py: all calibration and preregistered tests; writes weights.json (weights + data hash + date + protocol version); commits the NBER announcement-date table; runs the annual L_R audit (Section 1).
- MOTOR.py: reads weights.json; refuses hand-copied constants; requires --allow-stale for snapshots older than 40 days.
- ALFRED: one-time vintage audit (CPI, unemployment, claims, permits, GDP diagnostic); permanent calibration-only vintage layer iff the audit shows ≥2pp log-loss materiality OR flips any admission decision OR materially shifts historical live probabilities. The live tool never touches ALFRED.

## 10. Build order (unchanged from Revision 2)
1. Reproducibility refactor — acceptance: re-derives v4's numbers from fresh data; identical weights.json on repeated runs.
2. Label ablation: technical → NBER onset (Section 1 mechanical rule), quarterly held constant.
3. Frequency ablation under the Section 2 numeric gate.
4. Feature re-arbitration + locked challengers + ACM boxed test.
5. Vintage audit; apply Section 9 rule.
6. Output/verdict rebuild per Section 8.
All results published, including failures.

## 11. Dissent and reservations record
All Round-4 and Round-5 reservations are appended verbatim to the blueprint. Reservations do not block; they are part of the published record.
