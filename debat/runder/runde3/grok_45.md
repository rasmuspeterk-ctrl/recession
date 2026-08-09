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