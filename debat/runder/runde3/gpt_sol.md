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