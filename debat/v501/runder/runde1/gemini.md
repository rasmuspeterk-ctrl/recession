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