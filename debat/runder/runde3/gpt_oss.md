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