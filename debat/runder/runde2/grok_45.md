**ATTACK**

**Gemini Pro**: “Kill LAG 2 & 3… Flatten… validated model only.” Wrong. Flags/checklists that failed as features still supply real-time context (Sahm, HY, margin) under an explicit “unvalidated” label. Deleting them removes operational value without buying walk-forward skill and violates the honesty firewall’s purpose.

**Nemotron**: “Shrink to 2–3 features… Bayesian logit… flags as ensemble member.” Wrong. The locked 5 already delivered +22.9% log-loss / +19.4% Brier on 11 episodes. Arbitrary shrinkage discards validated skill. Bayesian ≈ L2 with extra machinery; ensemble weights on ~12 episodes are vibes, not validation. ACM-primary also truncates pre-1961 episodes.

**GPT-OSS-20B**: Multi-add (Sahm + claims + ACM + BS) + stay quarterly + first-release GDP label. Wrong. n≈12 cannot support that search; quarterly discards monthly timing; first-release GDP for a technical/NBER hybrid re-introduces revision mess the NBER switch avoids.

**Gemma**: Keep technical label + p9 + quarterly. Wrong. Technical misses 2001, is revision-contaminated (2022 H1), and is not the object users/literature mean. p9 assumes false independence across nested horizons.

**Kimi (partial)**: Stripped LAG-2 buckets still printed as historical frequencies invite override of the validated model; that is pseudo-validation.

**STEELMAN**  
Sol’s nested expanding-window selection + locked three-challenger package (permits/claims/Sahm) tested only inside training folds, plus mandatory curve-only and intercept benchmarks. My R1 protocol was looser; this better blocks the garden of forking paths.

**REVISED Q1–Q8**

**Q1 Label**: NBER (USREC) monthly, Y = any recession month in t+1…t+12. Include 2001. Score on final NBER; live note “trained on NBER; latest GDP print subject to revision.” No hybrid.

**Q2 Freq/horizon**: Monthly. Single direct 12m logit. Kill per-horizon models and p9.

**Q3 Features**: Incumbent 5 locked. Hard cap 6. Pre-registered one-at-a-time (then Sol-style locked package of Sahm/claims/permits). Admit only if WF log-loss ≥+3 pp, Brier ≥+2 pp, episode-blocked stable, pre/post-1990 stable. HY OAS post-1997 robustness only. No foreign curves/money/BS.

**Q4 Stats**: L2 logit. Episode-blocked CV + 500–1000 block-bootstrap 10–90% bands on p and on skill. Leave-one-episode-out sensitivity. No GBM/MS/ensembles.

**Q5 Regime**: Accept/communicate 2023 permanently. Test ACM-adjusted curve as single pre-registered swap only; accept solely on full-path WF + episode stability. Else raw curve.

**Q6 Architecture**: Keep strict firewall. LAG2: kill numerical buckets (failed feature + pseudo-%). Keep qualitative “months since/depth” note if desired, labeled unvalidated. LAG3: keep counted flags, never in probability or action language. Verdict cannot let flags overrule p.

**Q7 Data/ops**: Automate FRED (urllib/csv) + manual override. ALFRED vintages mandatory in calibration script for CPI/unemp/claims/permits/GDP diagnostics; live MOTOR stays simple. Complexity pays when it removes look-ahead in published skill.

**Q8 Output/benchmarks**: p12 + bootstrap band, base rate, skill, z-features, flag counts (labeled), short verdict that never exceeds numbers. Side-by-side: intercept, curve-only, NY Fed probit, real-time Sahm; Chauvet–Piger as coincident only. Must beat intercept + curve-only on WF; no requirement to dominate others.

**Top-3 build**: (1) NBER monthly direct-12m rebuild of locked-5, accept if skill ≥+18% log-loss / ≥+15% Brier and 2001 captured. (2) Episode-block + bootstrap bands in every output. (3) Locked challenger package under nested WF; promote only on clear thresholds.

**AGREE**  
- L2 logit core; reject boosting/MS/ensembles on n≈12  
- Kill p9 product (false independence)  
- Episode-blocked validation + uncertainty bands on output  
- Communicate 2023; no knee-jerk regime dummy  
- Automate free FRED pulls; honesty firewall for unvalidated pieces  
- Benchmarks reported alongside (curve-only mandatory)

**DISAGREE**  
- Label: NBER monthly (Sol/Kimi/Grok/Gemini) vs technical quarterly (Nemotron/Gemma)  
- LAG2/3: kill or strip hard (Sol/Gemini) vs keep labeled checklists (Grok/Kimi/Gemma/OSS) vs integrate (Nemotron)  
- Feature count: keep-5 + strict ladder (Grok/Sol/Kimi) vs shrink-to-2–3 (Nemotron) vs multi-add (OSS)  
- ALFRED: mandatory for cal credibility (Sol/Gemini/Grok) vs skip (Kimi/OSS)

**CHANGED-MY-MIND**  
- LAG2 numerical buckets: from “keep checklist” to kill the % tables (Sol/Kimi/Gemini right—they are pseudo-validation that failed as features).  
- Feature protocol: adopt Sol’s locked-package + nested selection over my looser one-at-a-time.  
- ALFRED: upgrade from “worth for cal” to mandatory in the calibration script; published skill without vintages is overstated.