**A) Architecture verdict**  
LAG 1: **keep core, shrink to 2–3 features, switch to Bayesian logit** — current 5 features overfit 11 episodes.  
LAG 2: **kill as separate layer** — inv_score failed walk-forward; if it works, it belongs inside the validated model.  
LAG 3: **split and validate** — recession flags (curve, Sahm, HY OAS, drawdown) are distinct from valuation flags (CAPE, ERP, margin) and debasement; each category gets its own walk-forward test.  
Verdict layer: **keep but formalize** — output must show calibrated probability ± interval, validated flag counts, and explicit “unvalidated” tags.

**B) Q1–Q8**  
1. **Label**: Stay with technical 2-quarter rule for *both* history and real-time. NBER is unknowable in real-time (6–18 month lag). 2001 stays out; 2022 H1 false positive is a documented revision-risk case. Add a “advance-estimate recession” flag (2 consecutive negative advance GDP prints) as a real-time checklist item.  
2. **Frequency/horizon**: Stay quarterly. Monthly adds no new episodes, worsens label overlap. Drop per-horizon models and p9 combination (independence assumption false). Single target: “recession within 4 quarters.”  
3. **Features**: Max 3 validated features for ~12 episodes. Pre-specify 8 candidates (curve, ACM-adjusted curve, Sahm, realrate, dd, d_infl, cape_pct, HY OAS). Protocol: leave-one-episode-out CV; feature enters only if it improves median log-loss in ≥80% of folds. No post-hoc selection.  
4. **Statistics**: Bayesian logit with weakly informative priors (β ~ N(0, 1) on standardized features) — regularizes naturally, yields posterior predictive intervals. Validation: episode-blocked bootstrap (resample episodes, not quarters) for uncertainty bands. HAC corrections irrelevant once blocks are episodes.  
5. **Regime instability**: Replace raw curve with **ACM 10y term premium subtracted** (expected future short rates). Free, monthly, 1961–present. Walk-forward test: does ACM-adjusted curve beat raw curve on log-loss? If not, keep raw curve and add “QE regime” binary (Fed BS/GDP > 25%) as interaction — but only if it passes episode-blocked CV.  
6. **Architecture**: Firewall is a backdoor. Validate each flag category as a sub-model. Recession flags → second ensemble member (Bayesian model averaging weight). Valuation flags → separate “repricing risk” probability. Debasement → separate “fiscal dominance” probability. Unvalidated = not in probability.  
7. **Data/ops**: Automate 6 core numbers via FRED API (requests + pandas, ~50 lines). Manual override retained. Add ALFRED vintage pulls for GDP (label) and curve (feature) — enables true real-time backtest. Complexity cost: ~200 lines, one-time. Worth it: current backtest uses revised labels.  
8. **Output/benchmarks**: Report: (a) P(recession|4q) ± 90% posterior interval, (b) validated flag counts by category, (c) unvalidated monitor readings. Benchmark table: NY Fed probit, Chauvet-Piger, real-time Sahm, unconditional base rate — same vintage, same horizon. v5 need not beat them; must not lose by >5% log-loss.

**C) Top-3 changes with validation tests**  
1. **ACM-adjusted curve replaces raw curve** — Walk-forward: episode-blocked CV comparing log-loss of (curve) vs (y10 − ACM_term_premium) as sole feature. Accept if median improvement ≥ 5%.  
2. **Bayesian logit + episode-blocked bootstrap intervals** — Test: 90% posterior predictive interval covers realized recession frequency in 80%+ of holdout episodes (calibration). Reject if under/over-confident.  
3. **FRED/ALFRED automation + vintage backtest** — Test: real-time vintage backtest log-loss vs revised-data backtest. If degradation > 10% log-loss, model is revision-fragile — document and widen intervals.

**D) Biggest risk in my proposal**  
ACM term premium starts 1961 → drops 1934–1960 data (4 recession episodes). Remaining 7 episodes (1969, 1973, 1980, 1981, 1990, 2001, 2007, 2020) may be too few for even 2-feature Bayesian logit. Mitigation: use raw curve pre-1961, ACM-adjusted post-1961 with a structural break dummy — but that adds complexity the philosophy forbids unless it pays in walk-forward skill.