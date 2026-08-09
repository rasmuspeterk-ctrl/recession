# ROUND3 — samlet


---

## GPT-5.6 Sol (OpenAI)

### D1 — Label
**Final:** Use monthly NBER/USREC: \(Y_t=1\) if a recession begins or occurs during \(t+1,\ldots,t+12\). Embargo the latest six months—or longer if NBER classification remains unresolved—and show advance-estimate “two negative quarters” only as a non-probabilistic diagnostic.  
**Compromise:** Preserve the vintage technical-GDP model as a separately scored benchmark, not a hybrid target.  
**VETO:** Technical GDP as the primary label, or mixing NBER and technical rules in one label. I would change only if Rasmus explicitly defines the product’s estimand as “two negative GDP prints,” rather than economic recession.

### D2 — Frequency and horizon
**Final:** Monthly direct-12-month model, with episode-blocked metrics and a quarterly-thinned score beside the monthly score. Monthly frequency improves forecast timing without pretending to add episodes.  
**Compromise:** Ship quarterly direct-4-quarter v5.0 first, then conduct a preregistered monthly v5.1 ablation using identical labels, features, and selection rules. No veto.

### D3 — Features
**Final:** No incumbent immunity; cap the final model at six features. Use the frozen candidate set and require at least 2% relative log-loss improvement, positive Brier improvement, economically coherent coefficient sign, and no dependence on one recession episode.  
**Compromise:** “Sign stability” means the expected sign in at least 75% of leave-one-episode-out fits, not every fold. Publish all attempted candidates.  
**VETO:** Reprinting +22.9% as post-selection skill or retaining all five incumbents without nested re-arbitration. I would withdraw this veto if an untouched holdout reproduced the claim.

### D4 — ACM curve
**Final:** Permit exactly one raw-versus-ACM substitution test, accounting explicitly for its shorter history and vintage/revision properties. It must not be selected because it repairs 2023.  
**Compromise:** If skill is close or episode sensitivity worsens, raw 10y–3m wins by simplicity. No veto.

### D5 — ALFRED
**Final:** Run the vintage audit first. Maintain a permanent calibration-only vintage layer if vintages change relative log loss by at least 2 percentage points, alter feature selection, or materially change historical live probabilities.  
**Compromise:** Otherwise freeze the audit, publish its result, and avoid maintaining an ALFRED pipeline. No live-tool ALFRED dependency.

### D6 — Market conditions
**Final:** Valuation, leverage, and debasement belong in a separate “market conditions—not recession evidence” section. Failed recession candidates should not become an influential second model.  
**Compromise:** Display Sahm, claims, HY OAS, and drawdown as raw monitors labeled “unvalidated/tested-not-passed,” without counts, traffic lights, synthesis, or verdict effects.  
**VETO:** Any checklist override, ensemble, or action instruction. Only successful preregistered validation would change this.

### D7 — Engine
**Final:** L2 logistic regression; episode bootstrap supplies estimation sensitivity. Bayesian logit adds no necessary capability to v5.  
**Compromise:** Allow a preregistered v5.1 Bayesian experiment, reported separately. No veto.

### Secretariat notes
- **S1 amend:** Ratify `weights.json`, hash, and date; stale data require an explicit `--allow-stale` or manual override rather than making offline operation impossible.
- **S2 ratify:** One attributable change per ablation.
- **S3 ratify:** Proper modules; stdlib plus numpy only.

---

## Kimi K3 (Moonshot AI)

# KIMI K3 — ROUND 3: FINAL POSITIONS

**D1 — Label.** Final: NBER/USREC, 2001 in, embargo the most recent ~6 quarters where declaration is pending. The target of a 12-month forecast need not be contemporaneously knowable; training labels must be final — the technical rule fails this (2022 H1 was revised away). Compromise: a "two consecutive negative advance prints" line in the real-time checklist, labeled unvalidated — covers Nemotron/Gemma's evaluability concern without contaminating the label. **VETO** on the technical rule as primary label. Change my mind: evidence the embargo traps a live episode undeclarable for >24 months; then I accept a hybrid.

**D2 — Frequency.** Final: monthly direct-12m. Episode count is unchanged (~12); T3's episode-blocked scoring neutralizes the overlap-inflation objection. Compromise: Sol's package — monthly model, all published metrics episode-blocked, quarterly-thinned robustness score printed beside them. If the minority holds out, I can live with the secretariat fallback (quarterly v5.0, monthly as preregistered v5.1), but it is second-best. No veto.

**D3 — Feature budget.** Final: no immunity; all five incumbents re-arbitrated under pre-1990-select / post-1990-one-shot (T7); hard cap 6; locked challengers {Sahm transform, claims, permits} plus the D4 substitution; admission requires log-loss AND Brier improvement, ≥2% relative log-loss, sign stability in ≥80% of LOEO folds, no single-episode rescue; all failures published. Compromise: threshold band 2–3%, exact number fixed once and preregistered after the re-derivation shows the noise floor — I'll accept 3%. **VETO** on any admission path without preregistered thresholds (GPT-OSS's 1% forward selection is a garden of forking paths with a gate sign). Change my mind: a block-bootstrap simulation of selection noise at n=12 justifying a different floor.

**D4 — ACM curve.** Final: exactly one locked substitution test, judged on full-path walk-forward plus episode stability, explicitly not on 2023 repair; pre-1961 truncation cost reported in the result. Compromise: if ambiguous, raw curve stays and the test is published as failed. Gemini's refusal is noted, but a single boxed test is not fishing. No veto. Change my mind: evidence that ACM estimates are themselves materially revised in real time.

**D5 — ALFRED.** Final: I concede to the conditional pipeline. The one-time audit is step one; any series showing >2pp log-loss materiality gets a permanent vintage layer in the calibration script only. The live tool never touches ALFRED. This is my position with a binding trigger — no veto.

**D6 — LAG 3.** Final: accept the on-the-table structure — recession-relevant flags (Sahm, claims, HY OAS, drawdown) become protocol candidates, admitted or published as "tested, not passed"; valuation/debasement flags move to a separated "market conditions — not recession evidence" section; counts never produce probability or action language. **VETO** on Nemotron's BMA sub-model — three weight-estimation problems on 12 events is the vibes-backdoor with machinery. Change my mind: a preregistered identifiability simulation showing BMA weights are recoverable at n≈12. I don't believe one exists.

**D7 — Engine.** Final: L2 logit. L2 with Gaussian penalty *is* the Bayesian MAP; the only real difference is the band, and the episode bootstrap (T3) respects dependence that a posterior over i.i.d. quarters would miss. Compromise: Bayesian variant as a labeled, preregistered v5.1 experiment. No veto.

**Secretariat notes.** S1 ratify — weights.json + data hash + 40-day staleness refusal kills hand-copied constants. S2 ratify — order: label → frequency → features → vintage, one ablation each. S3 ratify — calibrate.py / fetch.py / MOTOR.py, stdlib+numpy.

**Vetoes, summary:** (1) technical-rule primary label; (2) BMA/flag sub-model; (3) unpreregistered feature admission. Everything else negotiable within the stated bands.

---

## Gemini Pro (latest) (Google)

### D1 — Label
**Position:** NBER (USREC) is the only valid target; the technical rule misses 2001 and models BEA accounting quirks rather than economic reality.
**Compromise:** NBER label with a 6-month training embargo (to avoid fitting on undeclared recent months), plus a separate unvalidated "advance-estimate technical recession" diagnostic line.
**VETO:** I VETO keeping the technical 2-quarter rule as the model target. *Evidence to change my mind:* Walk-forward proof that the technical rule has a statistically significantly higher out-of-sample correlation with S&P 500 drawdowns than NBER dates.

### D2 — Frequency and horizon
**Position:** Monthly direct-12m. Economic data and NBER dates are monthly; aggregating to quarterly destroys timing precision without changing the underlying episode count (~12).
**Compromise:** Sol's proposal: Monthly model, but all published skill metrics must be computed episode-blocked, alongside a quarterly-thinned robustness score to prove we aren't inflating skill via overlap.

### D3 — Feature budget, incumbency and admission thresholds
**Position:** Hard cap of 4 features, zero grandfather immunity. The v4 +22.9% was a max-over-search; all features must be re-arbitrated via pre-1990 selection / post-1990 holdout.
**Compromise:** Hard cap of 5. Locked challenger list (Sahm, claims, permits). Admission requires walk-forward log-loss > +2pp, Brier > +2pp, and sign stability across LOEO folds. Failures are published.

### D4 — ACM term-premium-adjusted curve
**Position:** Reject ACM. It is an unobservable, model-laden estimate that truncates pre-1961 data, destroying 30% of our already tiny episode count.
**Compromise:** One preregistered substitution test (raw vs. ACM), but the pre-1961 truncation penalty must be mathematically enforced in the log-loss comparison (e.g., assigning base-rate to the missing years). If it fails to beat the raw curve under this penalty, it dies permanently.

### D5 — ALFRED vintage depth
**Position:** ALFRED vintages are mandatory in the offline calibration script for all revised series (CPI, unemployment) to prevent look-ahead bias in the reported skill.
**Compromise:** Accept Kimi's one-time vintage audit *if and only if* the audit proves the vintage-vs-revised delta alters log-loss by < 1pp. If the error is > 1pp, the ALFRED calibration pipeline becomes permanent.

### D6 — LAG 3 and the market-conditions section
**Position:** Delete recession flags entirely to prevent pseudo-validation. Move valuation/debasement to a strictly separate "Market Conditions" section.
**Compromise:** Recession candidates (Sahm, HY OAS) that fail validation become explicitly labeled "Tested, not passed" lines. Valuation/debasement stay in a separate section. Absolutely no Bayesian Model Averaging (BMA) sub-models.

### D7 — Engine variant
**Position:** L2 regularized logit. Bayesian logit adds unnecessary machinery when the episode-blocked bootstrap already provides the required uncertainty bands.
**Compromise:** L2 logit for v5.0. Bayesian variant can be a preregistered v5.1 experiment, provided it is evaluated strictly on out-of-sample log-loss against the L2 baseline.

---

## Grok 4.5 (xAI)

# GROK 4.5 — ROUND 3 FINAL

## OPEN DISPUTES

**D1 — Label**  
Final: NBER/USREC. Technical rule misses 2001, is revision-contaminated (2022 H1 advance prints), and is not the object the literature or users mean. Training labels must be final; real-time knowability is a property of predictors, not of the 12m target.  
Live with: NBER primary + ~6q training embargo on undeclared dates + separate unvalidated “advance two-negative GDP prints” diagnostic line.  
**VETO** technical-as-primary. Evidence to flip: published LOEO showing NBER destroys skill vs vintage-technical by >5pp log-loss *and* users explicitly want BEA accounting, not contractions.

**D2 — Frequency/horizon**  
Final: Monthly, one direct 12m logit. Episode count unchanged (~12); monthly preserves timing of curve/dd/Sahm without inventing episodes.  
Live with: Sol’s package — monthly model, all headline skill episode-blocked, plus quarterly-thinned robustness score printed beside it. Quarterly-only v5.0 with preregistered monthly v5.1 is acceptable if build order forces it (S2).

**D3 — Features**  
Final: No grandfather immunity (T7 already kills it). Re-arbitrate the five under nested/pre-1990 selection. Hard cap 6. Challengers locked: real-time unemployment/Sahm transform, initial claims, building permits; plus ACM swap (D4).  
Live with: admission = both log-loss and Brier improve on honest WF, ≥2% relative log-loss floor, sign-stable across LOEO, no single-episode rescue; all failures published. My prior ≥3pp/≥2pp absolute was too tight given post-selection honesty; 2% relative is livable. Cap 3 is a VETO — discards already-demonstrated skill without nested evidence.

**D4 — ACM curve**  
Final: Exactly one preregistered raw→(10y−ACM−3m) substitution. Judge full-path WF + LOEO stability; ignore 2023 repair. Account pre-1961 truncation. Fail → raw stays, test published failed.  
Live with the table as written. No veto.

**D5 — ALFRED**  
Final: Calibration-only vintage layer for revision-prone inputs (CPI, unemployment, claims, permits; market prices unrevised). Live tool never touches ALFRED.  
Live with: audit first; keep permanent layer only if audit shows ≥2pp log-loss materiality; else freeze revised series and publish the null. Complexity stops when materiality is null.

**D6 — LAG 3 / market section**  
Final: Firewall holds. Recession-relevant items (Sahm, claims, HY OAS, drawdown) are protocol candidates — features if they pass D3, else “tested, not passed” checklist lines. Valuation/debasement move to a separated “market conditions — not recession evidence” block. No counts in probability/action language; no BMA sub-model.  
Live with the table. **VETO** Nemotron BMA/ensemble-on-flags (extra models on n≈12 = vibes). Evidence to flip: nested WF showing BMA beats L2 by ≥3pp log-loss with LOEO stability.

**D7 — Engine**  
Final: L2 logit; penalty nested inside training windows. Uncertainty = episode-block bootstrap (T3), not posterior.  
Live with: Bayesian N(0,1) MAP/posterior as labeled preregistered v5.1 only. No veto.

## SECRETARIAT
- S1: Ratify.  
- S2: Ratify (label → frequency → features/vintage, one ablation each).  
- S3: Ratify.

## Non-negotiable for my signature
NBER (or the D1 compromise), episode-blocked honest post-selection skill, no flag-derived probabilities/action verbs, no BMA-on-flags, hard cap ≤6 with published failures. Everything else above is already compromise.

---

## Nemotron 3 Ultra 550B (NVIDIA (free))

**D1 — Label**  
*Position:* Technical two-quarter rule with ALFRED-vintage GDP is the only label knowable in real time; NBER’s 6–18 month lag makes live validation impossible for a monthly tool.  
*Compromise I accept:* NBER label **only if** the live tool prints a real-time “advance-estimate recession” flag (two negative advance GDP prints) as a separate, unvalidated diagnostic — satisfying the developer’s need for a contemporaneous signal.  
*Veto:* NBER label without the real-time diagnostic; that ships a model the user cannot evaluate until years later.

**D2 — Frequency/Horizon**  
*Position:* Quarterly direct-4q. Monthly adds zero episodes, inflates apparent skill via 12× label overlap, and forces interpolation of quarterly GDP.  
*Compromise I accept:* Quarterly v5.0; monthly as a **preregistered v5.1 experiment** with separate ablation attribution (label + frequency changed together).  
*Veto:* Monthly as the primary v5 output without a clean quarterly baseline — attribution becomes impossible.

**D3 — Feature Budget**  
*Position:* Hard cap **4 validated features** (curve, dd, d_infl, plus one of {cape_pct, realrate, ACM-curve}). No grandfather immunity; all re-arbitrated via leave-one-episode-out CV.  
*Compromise I accept:* Cap 6 **if** admission requires **both** log-loss ≥2% relative improvement **and** Brier ≥2pp **and** sign stability in ≥9/11 LOEO folds.  
*Veto:* Cap 6 with only a log-loss threshold — Brier and stability are non-negotiable guards against curve-fitting on 11 episodes.

**D4 — ACM Curve**  
*Position:* One preregistered substitution test (raw → 10y−ACM−3m), judged on full-path episode-blocked walk-forward. Pre-1961 truncation cost must be reported.  
*Compromise I accept:* Exactly the table compromise.  
*Veto:* Adopting ACM because it “fixes 2023” — that is post-hoc reasoning banned by the philosophy.

**D5 — ALFRED Vintage**  
*Position:* Mandatory in calibration script for CPI, unemployment, claims, permits, GDP. Live tool stays manual.  
*Compromise I accept:* One-time audit published; pipeline kept **only if** audit shows >2pp log-loss delta on any feature.  
*Veto:* No vintage audit at all — published skill would remain contaminated by look-ahead.

**D6 — LAG 3 / Market Conditions**  
*Position:* Recession-relevant flags (curve, Sahm, HY OAS, drawdown) enter the **feature protocol** (D3); if they pass, they become validated features. If they fail, they appear as “tested, not passed” lines. Valuation/debasement flags move to a separate “Market Conditions — Not Recession Evidence” section.  
*Compromise I accept:* Table compromise (protocol candidates + separated section).  
*Veto:* Keeping recession flags as influential checklists without a validation pathway — that is the backdoor for vibes the firewall was built to prevent.

**D7 — Engine**  
*Position:* Bayesian logit (β ~ N(0,1)) for coherent posterior intervals; episode-blocked bootstrap for skill uncertainty.  
*Compromise I accept:* L2 logit **if** the episode-blocked bootstrap band is printed on every live probability (satisfies T3). Bayesian variant as preregistered v5.1.  
*Veto:* L2 without the bootstrap band — uncertainty quantification is mandatory per settled point T3.

---

## Gemma 4 31B (Google (free))

As a senior macro-econometrician, I have reviewed the Round 2 positions. The council has reached a high degree of convergence on the engine and architecture; the remaining disputes are primarily about the precision of the target and the breadth of the feature set.

### **D1 — Label**
**Final Position:** Use NBER (USREC) as the training label to ensure the model targets actual economic contractions and includes the 2001 episode.
**Compromise:** The live tool will report the NBER-based probability but include a "Technical Recession Diagnostic" (using ALFRED-vintage GDP) in the unvalidated checklist to capture real-time volatility without contaminating the core model.

### **D2 — Frequency and Horizon**
**Final Position:** Maintain **Quarterly** frequency to preserve the integrity of the $\approx 12$ recession episodes and prevent overfitting.
**Compromise:** The model will predict a single 12-month-ahead probability ($P(\text{recession within next 4 quarters})$), eliminating the mathematically flawed $p_9$ product rule.

### **D3 — Feature Budget, Incumbency, and Admission**
**Final Position:** The 5 core features are the baseline, but they have no immunity; any addition or subtraction must be decided by a single, pre-registered, episode-blocked walk-forward test.
**Compromise:** A "Candidate Package" (Sahm, Initial Claims, Building Permits, ACM-adjusted curve) will be tested as a single block. Admission requires a $\ge 2\%$ relative log-loss improvement and $\ge 2\text{pp}$ Brier skill improvement, with stability across leave-one-episode-out (LOEO) folds.

### **D4 — ACM Term-Premium-Adjusted Curve**
**Final Position:** The ACM-adjusted curve is a candidate, not a replacement.
**Compromise:** It will be tested via a single, pre-registered substitution test (Raw Curve $\to$ ACM-Adjusted Curve) during the next calibration cycle. If it fails to show significant skill improvement in the block-bootstrap, the raw curve remains the incumbent.

### **D6 — LAG 3 and the Market-Conditions Section**
**Final Position:** The "Honesty Firewall" is absolute; recession-relevant flags (Sahm, HY OAS, Drawdown) are only admitted to the model if they pass the admission threshold.
**Compromise:** All other flags (Valuation/Debasement) are relegated to a "Market Conditions" checklist. They are strictly qualitative/diagnostic and must never be used to adjust the point probability or the verdict.

***

**VETO:** I VETO any attempt to move to a **Monthly** frequency (D2) or to use **Bayesian Model Averaging** for flags (D6).
**Evidence to change my mind:** 
1. **For Frequency:** If a monthly model demonstrates a $\ge 15\%$ relative log-loss improvement over the quarterly model *after* episode-blocked validation and accounting for the increased number of overlapping observations.
2. **For BMA:** If a BMA ensemble demonstrates superior Brier skill over a simple L2 logit on a holdout sample of at least 3 full recession episodes.

---

## GPT-OSS-20B (OpenAI (free))

**D1 – Label**  
We will use the NBER USREC monthly dates as the primary target, with a separate real‑time “advance‑estimate two‑negative‑print” diagnostic flag in the checklist.  
*Compromise*: the technical two‑quarter rule can be retained as a secondary diagnostic (not used for training).  
*VETO*: we reject using the technical rule as the main label because it excludes 2001 and introduces revision bias.  Evidence that would change this is a demonstrable out‑of‑sample improvement in predictive accuracy when the technical rule is used.

**D2 – Frequency & Horizon**  
The model will be a single direct‑12‑month logit estimated on monthly data.  
*Compromise*: a quarterly 4‑quarter model can be kept as a secondary check, but will not influence the main probability.  
*VETO*: we reject a quarterly primary model.  Evidence that would change this is a statistically significant drop in performance for the monthly model relative to a quarterly one.

**D3 – Feature Budget & Selection**  
Keep the five incumbent features; allow up to six total.  New candidates (e.g., Sahm, initial claims, permits, ACM‑adjusted curve) are admitted only if nested walk‑forward shows ≥2 % log‑loss improvement, ≥1 % Brier improvement, and stability across leave‑one‑episode‑out folds.  
*Compromise*: a single candidate may be added if it meets the thresholds.  
*VETO*: we veto adding more than six features.  Evidence that would change this is a consistent performance gain above the thresholds.

**D4 – ACM‑Adjusted Curve**  
Test raw curve versus ACM‑adjusted curve as a single substitution, evaluated on the full walk‑forward path and episode stability.  
*Compromise*: if ACM improves log‑loss, adopt it; otherwise keep raw curve.  
*VETO*: we veto permanently replacing the raw curve.  Evidence that would change this is a statistically significant improvement in log‑loss with the ACM adjustment.

**D5 – ALFRED Vintage Depth**  
ALFRED vintage data will be used only in the offline calibration script; the live tool will use revised FRED series with a manual override.  If a one‑time vintage audit shows >2 pp log‑loss improvement, we freeze the vintage pipeline for live use.  
*Compromise*: the audit result will decide whether to adopt vintage data in production.  
*VETO*: we veto a permanent live vintage pipeline.  Evidence that would change this is a >2 pp improvement in log‑loss from the audit.

**D6 – LAG 3 & Market‑Conditions Section**  
Keep all LAG 3 flags as an unvalidated checklist; they may be displayed but never influence the probability or the verdict.  Valuation/debasement flags are kept in a separate “market‑conditions” section.  
*Compromise*: flags can be used for qualitative risk assessment but not for probability.  
*VETO*: we veto using any flag as part of the probability model.  Evidence that would change this is a statistically significant predictive contribution of a flag in a nested walk‑forward test.

**D7 – Engine Variant**  
Use L2‑regularised logistic regression with the L2 penalty chosen within each training window.  Bayesian logit is kept as a labelled experimental variant.  
*Compromise*: Bayesian can be run in parallel as a side‑experiment.  
*VETO*: we veto Bayesian as the primary engine.  Evidence that would change this is a ≥2 pp log‑loss advantage over L2.

**D8 – Output & Benchmarks**  
The tool will output: point probability, 90 % episode‑bootstrap band, base‑rate, z‑scores of the five features, flag counts, and a plain‑language verdict that never exceeds the model’s numbers.  Benchmarks (NY‑Fed yield‑curve probit, real‑time Sahm, Chauvet–Piger) are displayed side‑by‑side.  
*Compromise*: the benchmark table can include additional non‑validated models as informational.  
*VETO*: we veto using any non‑validated benchmark as a primary reference.  Evidence that would change this is a demonstrable superiority of a non‑validated benchmark across all walk‑forward metrics.