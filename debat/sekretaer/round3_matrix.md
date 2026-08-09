# SECRETARY'S DISAGREEMENT MATRIX — after Round 2

## SETTLED (unanimous or conceded — do NOT reopen)

- T1. Engine: penalized logistic regression. Boosting, Markov-switching and model ensembles rejected at n≈12.
- T2. Kill the p9 = 1−Π(1−p_h) product and the four per-horizon weight vectors. One direct model. (Gemma conceded in R2.)
- T3. Episode-blocked validation (leave-one-episode-out / episode blocks) plus episode-block bootstrap uncertainty band printed on the live probability. Overlap-aware scoring is mandatory.
- T4. LAG 2's bucket-percentage table dies. At most a qualitative "inversion ended X months ago, depth Y" line, labeled unvalidated.
- T5. Flags may never produce probability language or action language ("Handl"), and may never override the model. v4's verdict text breached this; v5 fixes it.
- T6. Automate data pulls (FRED CSV, stdlib urllib + manual override dict). Margin debt stays manual.
- T7. Selection integrity: v4's +22.9% is a max-over-search (feature sets chosen on the same walk-forward that produced the headline). v5 re-derives skill with feature AND penalty selection nested inside training windows (or pre-1990 selection / post-1990 one-shot evaluation). Published numbers are post-selection honest.
- T8. 2023 false alarm: accept and permanently communicate; no QE dummies, no Fed-balance-sheet feature, no regime interactions.
- T9. Benchmarks in every output: intercept, curve-only (this IS the NY-Fed-style probit), real-time Sahm; Chauvet–Piger shown separately as a coincident nowcast. v5 must beat intercept and curve-only walk-forward; it does not have to dominate the rest, but the table is printed even when unflattering.
- T10. Output: point probability + episode-bootstrap band + base rate + z-scored inputs + benchmark table + plain verdict that never exceeds the numbers.

## OPEN DISPUTES — give your final position and a livable compromise on each

### D1 — Label
NBER/USREC (Sol, Kimi, Gemini, Grok, GPT-OSS) vs technical two-quarter rule with ALFRED-vintage GDP label (Nemotron, Gemma-hybrid).
Nemotron's real-time-evaluability objection stands against Sol/Kimi's "the target need not be contemporaneously knowable; training labels must be final — NBER dates are final, technical labels are not (2022 H1)."
On the table: NBER label; training embargo on the most recent ~6 quarters (labels not yet declarable); a separate real-time "advance-estimate two-negative-prints" diagnostic line in the checklist (satisfies the real-time need without contaminating the label).

### D2 — Frequency and horizon
Monthly direct-12m (Sol, Kimi, Gemini, Grok) vs quarterly direct-4q (Nemotron, Gemma, GPT-OSS).
Overlap-inflation concern vs timing loss. On the table (Sol's compromise): monthly model, but ALL published skill metrics computed episode-blocked AND a quarterly-thinned robustness score published next to them. Secondary option (secretariat): quarterly v5.0, monthly as preregistered v5.1 experiment — never change label and frequency without separate ablation attribution.

### D3 — Feature budget, incumbency and admission thresholds
Positions: keep 5 locked incumbents (Grok, Sol, GPT-OSS, Gemma) vs no grandfather immunity — re-arbitrate all five (Kimi, Gemini) vs hard cap 3 (Nemotron).
Thresholds proposed: ≥1% (GPT-OSS), ≥2% relative log-loss (Kimi), ≥3pp log-loss + 2pp Brier (Grok), ≥80% of LOEO folds improved (Nemotron).
On the table: no immunity (T7 forces re-arbitration anyway); hard cap 6 total; locked challenger list = {Sahm/real-time unemployment transform, initial claims, building permits} + ACM-curve substitution (D4); admission = walk-forward log-loss AND Brier both improve, ≥2% relative log-loss floor, sign stability across LOEO folds, no single-episode rescue; all failures published in the repo ("tested, not passed").

### D4 — ACM term-premium-adjusted curve
One preregistered substitution test (Kimi, Grok, Sol, GPT-OSS, Nemotron-as-candidate) vs refuse to test (Gemini: estimated unobservable, model-laden, revised).
On the table: exactly one locked substitution test (raw curve → 10y−ACM−3m), judged on full-path walk-forward + episode stability, explicitly NOT judged on whether it repairs 2023; pre-1961 truncation cost must be accounted; if it fails or is ambiguous, raw curve stays and the test is published as failed.

### D5 — ALFRED vintage depth
Permanent vintage layer in the calibration script for revision-prone series (Grok, Gemini, Sol, Nemotron, Gemma) vs one-time vintage audit, pipeline only if the audit shows >2pp log-loss materiality (Kimi).
On the table: calibration-only either way (live tool never touches ALFRED); the audit IS step one; keep-or-freeze decided by its published result.

### D6 — LAG 3 and the market-conditions section
Keep-labeled checklist (Grok, Kimi, Gemma, GPT-OSS) vs delete flags / move valuation items to a separate non-recession section (Sol, Gemini) vs recession-flags as a validated Bayesian-model-averaging sub-model (Nemotron — attacked by Kimi and Grok as the backdoor with extra machinery).
On the table: recession-relevant flags (Sahm, claims, HY OAS, drawdown) become protocol candidates — admitted features if they pass, "tested, not passed" checklist lines if they fail; valuation/debasement flags move to a clearly separated "market conditions — not recession evidence" section; no BMA sub-model.

### D7 — Engine variant
L2 logit (majority) vs Bayesian logit with N(0,1) priors for posterior bands (Nemotron).
On the table: L2 as the v5 engine (Sol/Kimi: mathematically near-identical to the Bayesian MAP); uncertainty bands come from the episode bootstrap (T3), which delivers what the posterior was wanted for; Bayesian variant allowed later as a labeled, preregistered v5.1 experiment.

## Secretariat notes (ratify or amend in one line each)
- S1. Reproducibility: calibration writes weights.json (weights + data hash + date); MOTOR.py refuses hand-copied constants and refuses data snapshots older than 40 days.
- S2. Build discipline: one change per ablation — label switch, frequency switch, feature changes and vintage corrections are separate, attributable steps, in that order.
- S3. inv.py's `exec(open('curve.py'))` becomes a proper import; calibration/live-tool split into calibrate.py / fetch.py / MOTOR.py, all stdlib+numpy.
