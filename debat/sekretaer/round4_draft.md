# MOTOR v5 — CONSENSUS BLUEPRINT (ratification draft)

Assembled by the secretary strictly from Round 3 final positions. Vetoes honored are noted inline.

## 0. Philosophy (unchanged, now enforced mechanically)
Radical simplicity (solo-maintainable, stdlib+numpy, free data). Radical honesty: only walk-forward-validated claims get numbers; complexity must buy demonstrated skill or be rejected; every tested-and-failed idea is published, not deleted.

## 1. Label
- Target: NBER/USREC. Y_t = 1 if an NBER recession month occurs within the next 12 months (quarterly formulation: within the next 4 quarters). 2001 enters calibration.
- Training embargo: the most recent 6 quarters are excluded from every refit, extended while any month in the window remains undeclarable by NBER. (Honors Sol/Kimi/Gemini/Grok/GPT-OSS vetoes of the technical label.)
- Real-time need (Nemotron's binding condition): the live output prints an "advance-estimate diagnostic" line — two consecutive negative advance GDP prints — clearly labeled unvalidated, outside the model.
- Optional benchmark row: the v4-heritage technical-label model may be kept as a separately scored benchmark, never as target.

## 2. Frequency and horizon (staged, empirical gate)
- Kill confirmed (T2): the p9 product and all per-horizon weight vectors. One direct model.
- Step 1 (v5.0): quarterly direct-4q NBER baseline — label is the only change from v4, preserving attribution (S2; honors Nemotron's veto: a clean quarterly baseline must exist).
- Step 2 (same calibration cycle, preregistered): monthly direct-12m ablation with identical features, selection rules and scoring.
- Gate: monthly becomes the primary published model iff its episode-blocked skill is non-inferior to the quarterly baseline, with quarterly-thinned scores published beside monthly scores (honors Gemma's overlap-inflation objection: the proof is episode-blocked and thinned). If non-inferiority fails, quarterly stays primary and the monthly result is published as failed.
- Either way, both scores appear in the calibration report.

## 3. Engine
L2 logistic regression; penalty selected nested inside each training window; standardization from training data only. Bayesian logit (N(0,1) MAP ≈ L2) is allowed later only as a labeled, preregistered v5.1 experiment. Uncertainty comes from the episode bootstrap, not a posterior.

## 4. Features — re-arbitration and admission protocol
- No grandfather immunity: all five incumbents (curve, realrate, dd, d_infl, cape_pct) are re-arbitrated under nested selection (feature and penalty choices inside training windows; equivalently pre-1990 selection with post-1990 one-shot evaluation).
- Hard cap: 6 features total.
- Locked challenger list (one preregistered shot each): real-time Sahm/unemployment transform, initial claims momentum, building permits y/y. HY OAS is ineligible as a feature (history from ~1997, ~3 episodes) and remains a monitor.
- Admission requires ALL of: ≥2% relative walk-forward log-loss improvement; ≥2pp Brier-skill improvement; expected coefficient sign in ≥80% of leave-one-episode-out fits; no dependence on a single rescuing episode. (Merges Kimi/Sol/Gemini/Grok/Nemotron/Gemma/GPT-OSS thresholds; honors Nemotron's veto of log-loss-only gates and Kimi's veto of unpreregistered admission.)
- Every attempted candidate is published with its result — "admitted" or "tested, not passed."
- The retired headline: +22.9% is acknowledged as max-over-search and is re-derived under the nested protocol before any number is published again (honors Sol's veto).

## 5. ACM term-premium curve — one boxed test
Exactly one preregistered substitution test: raw 10y−3m → (10y − ACM term premium − 3m). Judged on full-path walk-forward skill and LOEO stability; explicitly NOT judged on repairing 2023. Pre-1961 truncation is penalized mathematically: missing years score at base rate in the comparison (Gemini's condition). Ambiguous or failed → raw curve stays, result published as failed.

## 6. Validation and uncertainty
- Episode-blocked walk-forward (leave-one-episode-out with the episode's full label window held out) is the primary published metric; expanding-window walk-forward is reported alongside.
- Episode-block bootstrap (~1000 resamples of the ~12 episodes) produces a 10–90% band printed on every live probability, named an "estimation-sensitivity range" — explicitly not a frequentist predictive interval (Sol's renaming).
- Language rule, quantitative: if the band contains the base rate, the verdict may not use "low"/"high"; it must say "not distinguishable from base rate."
- 2023 stays in the warning block permanently; no QE dummies, no balance-sheet features, no regime interactions (T8).

## 7. Kill list (confirmed)
p9 product; per-horizon weight vectors; LAG 2's bucket-percentage table (a qualitative "inversion ended X months ago, depth Y" line may remain, labeled unvalidated); aggregate flag counts; any flag influence on probability or verdict; action verbs ("Handl"); hardcoded verdict prose.

## 8. Output specification (monthly run)
1. P(recession within horizon) + 10–90% estimation-sensitivity band + base rate + ratio.
2. z-scored model inputs.
3. Benchmark table, printed even when unflattering: intercept, curve-only probit (the NY-Fed-style benchmark, already computable from calibration), real-time Sahm; Chauvet–Piger displayed separately as a coincident nowcast, different discipline; optional v4-heritage row. v5 must beat intercept and curve-only walk-forward; it does not need to dominate the rest.
4. Monitors, individually displayed, no aggregate counts, no traffic-light synthesis, no verdict influence:
   - Recession-relevant monitors (Sahm, claims, HY OAS, drawdown, advance-estimate diagnostic, inversion note) — each labeled "admitted as feature," "tested, not passed," or "ineligible (history)."
   - "Market conditions — not recession evidence" section: CAPE percentile, equity risk premium, margin debt, real cash yield (valuation/debasement items; qualitative only).
5. Verdict: template-generated from the numbers (no hardcoded prose), never exceeding them.

## 9. Data and operations
- fetch.py: FRED CSV endpoints via stdlib urllib; writes dated snapshots to data/raw/ (git-committed); prints the input values with a diff against last month for a human eyeball before commit. CAPE (Shiller) and margin debt (FINRA) stay manual entries in an override dict.
- calibrate.py: all calibration; writes weights.json (weights + data hash + date + protocol version). Includes the vintage audit (below) and all preregistered tests. inv.py's exec() is replaced by imports (S3).
- MOTOR.py: reads weights.json and the latest snapshot; refuses hand-copied constants; warns and requires an explicit --allow-stale flag if the snapshot is older than 40 days (S1 as amended by Sol).
- ALFRED: a one-time vintage audit in calibrate.py for revision-prone series (CPI, unemployment, claims, permits, and the GDP diagnostic). A permanent calibration-only vintage layer is kept iff the audit shows ≥2pp log-loss materiality OR flips any admission decision OR materially shifts historical live probabilities (Sol's triple condition; Kimi's audit-first honored; live tool never touches ALFRED).

## 10. Build order (one attributable change per step, S2)
1. Reproducibility refactor (fetch.py / calibrate.py / weights.json / imports). Acceptance: re-derives v4's published numbers from fresh data within tolerance; two runs produce identical weights.json.
2. Label ablation: technical → NBER on quarterly. Published as its own result.
3. Frequency ablation: monthly vs quarterly under the Section 2 gate.
4. Feature re-arbitration + locked challengers + ACM boxed test.
5. Vintage audit; apply the Section 9 rule.
6. Output/verdict rebuild per Section 8.
All six steps' results are published in the repo, including failures.

## 11. Dissent record
Filled after the ratification vote. Reservations noted for the record do not block.
