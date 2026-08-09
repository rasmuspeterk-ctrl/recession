**A) v4 architecture verdict**

- **LAG 1**: KEEP core (L2 logit + 5 features + walk-forward), CHANGE label/validation/uncertainty.
- **LAG 2**: KEEP as unvalidated checklist only; do not re-integrate.
- **LAG 3**: KEEP as counted flags; do not model or ensemble them.
- **Verdict layer**: CHANGE — tighten language, force explicit base-rate comparison + uncertainty, drop narrative flourish that outruns the numbers.

**B) Q1–Q8**

**Q1 — Label.** Switch to NBER peak-to-trough dates (USREC, quarterlyized or monthly). Include 2001. Technical two-quarter rule is inferior: it misses 2001, is revision-contaminated (2022H1), and is not the object most users or literature care about. Real-time knowability is imperfect for both; NBER has publication lag, final GDP has look-ahead. Calibrate and score on NBER; in live use report “model trained on NBER, latest GDP print is X (subject to revision)”. Hybrid is complexity without payoff.

**Q2 — Frequency and horizon.** Move to monthly. Most inputs and NBER are monthly; quarterly throws away timing. Keep 12-month-ahead binary target (recession starts within 12 months). Kill per-horizon models and the p9 = 1 − Π(1 − p_h) product: independence is false, four small models overfit noise with ~12 episodes, and a single 12m logit is cleaner and more honest. Report the single p12.

**Q3 — Features.** Keep the five as baseline. Hard cap at 5–6 features total given ~12 episodes. Candidate adds only if free and long history: Sahm (or 3m unemployment change), building permits y/y, HY OAS only as post-1997 robustness check not main model. Drop or demote anything that fails the protocol. Protocol (pre-registered, no forking): (1) start from the locked 5-feature set, (2) test one candidate at a time, (3) require walk-forward log-loss improvement ≥ 3 pp and Brier skill ≥ 2 pp on the full post-1960 path plus stability in pre/post-1990 splits, (4) reject if it degrades any major episode cluster. Expanding CAPE percentile stays; no foreign curves or money growth unless they clear the same bar.

**Q4 — Statistics.** Keep L2-regularized logistic regression. With n_episodes ≈ 12, Bayesian logit with weakly informative priors is acceptable only if it matches or beats L2 in WF; gradient boosting, Markov-switching, and ensembles are rejected—they will overfit. Validation must become episode-blocked: treat each recession episode + surrounding non-recession window as a block; report log-loss/Brier on blocks, not raw overlapping quarters. Add block-bootstrap percentile bands on the probability path. Output must carry a simple uncertainty band (e.g., 10th–90th from expanding-window or block bootstrap). Ignore HAC on the score itself; fix the dependence at the CV level.

**Q5 — Regime instability.** Accept the 2023 error and communicate it permanently in the warning block. Do not add Fed balance sheet or regime dummies without a clean WF win. Test one concrete fix only: replace raw curve with ACM-period term-premium-adjusted curve (or 10y–3m minus ACM TP) if the series is free and long enough. Accept only if it raises overall WF skill and reduces the 2022–23 peak without destroying earlier episodes. Otherwise leave the curve raw and state the regime risk explicitly.

**Q6 — Architecture.** Layered design is sound and must be preserved. Validated model stays strictly separated from checklists/flags. Integrating flags into an ensemble is a backdoor for vibes and fails the honesty rule. LAG 2/3 remain labeled “unvalidated checklist — not probabilities.”

**Q7 — Data and ops.** Automate via free FRED API (plus Shiller/BLS fallbacks) with a manual override dict. This removes transcription error at near-zero complexity cost. ALFRED vintage for key series (GDP, CPI, unemployment, yields) is worth doing for the calibration script only; live MOTOR stays simple. Simplicity stops paying when manual entry or revised-data look-ahead systematically biases the published skill numbers.

**Q8 — Output and benchmarks.** Report: point p12, bootstrap interval, base rate, skill vs base, the five z-scored features, LAG 2 score+bucket, LAG 3 flag counts by category, and a one-paragraph verdict that never exceeds the numbers. Mandatory side-by-side table vs NY Fed probit, Chauvet–Piger (or equivalent free real-time smoother), and real-time Sahm. v5 does not need to beat them; it must show its WF skill and calibration honestly beside them.

**C) Top-3 highest-impact changes**

1. **NBER label + monthly 12m target + single logit**  
   Concrete test: rebuild D monthly with USREC, Y = any NBER recession month in t+1…t+12. Re-run identical walk-forward L2 logit on the locked 5 features from 1960. Accept if log-loss improvement ≥ +18 % and Brier skill ≥ +15 % vs new base rate, and 2001 is now captured without destroying 1970s/2008. Reject and revert if skill collapses below +15 %.

2. **Episode-blocked validation + bootstrap probability bands**  
   Concrete test: define ~11–12 episode blocks; compute mean log-loss/Brier across left-out blocks (and expanding WF). Generate 500 block-bootstrap probability paths; report 10/90 band around live p. Accept if bands are implemented and the point-skill remains positive under blocking; use the bands in every output thereafter.

3. **One-at-a-time feature trial: Sahm (or Δu 3m) under the strict protocol**  
   Concrete test: add Sahm (lagged to be real-time known) to the 5-feature set; run full WF + episode-blocked metrics + pre/post-1990 split. Accept only if Δlog-loss improvement ≥ +3 pp and no major episode degrades; else keep as flag only.

**D) Single biggest risk in this proposal**

Changing the label and frequency re-opens the entire calibration; with only ~12 episodes the new WF numbers can look better by chance or by construction, creating false confidence that the model is more skillful than the tiny effective sample justifies.