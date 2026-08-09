**1. ATTACK**

- **GPT-5.6 / Kimi / Grok / GPT-OSS (NBER monthly label):** NBER dates are published with 6–18 month lag. A model that cannot be evaluated in real time is a research artifact, not a tool. Monthly frequency adds zero new episodes (~12 either way) but inflates apparent skill via 12× label overlap. The technical rule with ALFRED vintage GDP is knowable *now*; NBER is not.
- **Gemini (kill LAG 2/3):** The philosophy explicitly permits checklists labeled “not a probability.” LAG 2/3 provide qualitative context (repricing/debasement) that a single recession probability cannot. Deleting them discards signal the developer uses.
- **GPT-OSS (ACM + Fed BS + Sahm + claims + Bayesian):** 5+ features on 11 episodes is curve-fitting. Fed balance sheet is collinear with the curve (ρ > 0.8 post-2008); adding both guarantees multicollinearity, not information.
- **Gemma (keep p9 combination):** p9 = 1−Π(1−p_h) assumes independence across overlapping horizons. That assumption is false; the combination is mathematically incoherent.

**2. STEELMAN**

Kimi’s **episode-block bootstrap band + episode-level skill metric**. This converts the “8.8% vs 13.4% not statistically certain” caveat into a printed 10–90% band (e.g., 8.8% [4–19%]) and a diagnostic: “max predicted p in each historical episode vs outcome.” It makes honesty quantitative.

**3. REVISED Q1–Q8**

| Q | Revised Position |
|---|------------------|
| **1 Label** | Stay technical 2-quarter rule. **Add ALFRED vintage GDP for label construction** (fixes 2022 H1 look-ahead). 2001 stays out; add “advance-estimate recession” flag for real-time checklist. |
| **2 Freq/Horizon** | Stay quarterly. Single target: “recession within 4 quarters.” Kill p9 and per-horizon models. |
| **3 Features** | Hard cap **3 validated features**. Incumbent: curve, dd, d_infl. Candidates (pre-registered, one-at-a-time): ACM-adjusted curve (replaces raw curve), Sahm. Protocol: leave-one-episode-out CV; enter only if median log-loss improves in ≥80% folds. |
| **4 Statistics** | **Bayesian logit** (β ~ N(0,1) on standardized features) for natural regularization + posterior predictive intervals. Validation: **episode-blocked bootstrap** (resample 11 episodes) for probability bands. **Add episode-level skill metric** (max p per episode vs outcome). |
| **5 Regime** | Test ACM-adjusted curve (10y − ACM term premium) as **sole curve feature** via episode-blocked CV. If it fails, keep raw curve + permanent “QE regime risk” warning. No balance-sheet feature. |
| **6 Architecture** | Firewall holds. **Recession flags (curve, Sahm, HY OAS, drawdown) → validated sub-model** combined via Bayesian model averaging (weight learned in walk-forward). Valuation/debasement flags stay unvalidated checklists. |
| **7 Data/Ops** | **Automate FRED/ALFRED in calibration script only** (~200 lines, one-time). Live MOTOR.py stays 6 manual numbers + override dict. Vintage backtest mandatory for any claimed improvement. |
| **8 Output/Benchmarks** | Report: (a) P(recession|4q) ± 90% posterior interval, (b) episode-level skill table, (c) validated flag counts, (d) unvalidated monitor readings. Benchmark table: NY Fed probit, Chauvet-Piger, real-time Sahm — same vintage, same horizon. |

**4. COUNCIL STATE**

**AGREE**
- LAG 1 (penalized logit, walk-forward) is the only validated core.
- LAG 2 (inv_score) failed walk-forward; stays out of model.
- Overlapping labels require episode-blocked validation, not quarter-level CV.
- Uncertainty bands on live probability are mandatory.
- Free data, solo-maintainable, no look-ahead in fit or label.

**DISAGREE**
- **Label/Frequency:** Me + Gemma (technical quarterly + ALFRED vintage) vs GPT-5.6/Kimi/Grok/GPT-OSS (NBER monthly).
- **LAG 3 disposition:** Me (recession flags → validated ensemble member) vs Gemini (kill all) vs GPT-5.6/Kimi/Grok (keep as checklists only).
- **Feature budget:** Me (3 features max, ACM curve + Sahm candidates) vs GPT-OSS (5+ features including Fed BS, claims).

**CHANGED-MY-MIND**
- **ALFRED vintage for GDP label** (from Gemma/GPT-5.6): fixes 2022 H1 look-ahead without switching to unknowable NBER.
- **Episode-level skill metric** (from Kimi): turns statistical uncertainty into a printed diagnostic.
- **Nested walk-forward for regularization selection** (from GPT-5.6): prevents leakage when choosing prior scale/penalty.
- **Recession flags as single Bayesian ensemble member** (was: validate each category separately): simpler, respects episode budget.