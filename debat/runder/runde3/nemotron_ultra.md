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