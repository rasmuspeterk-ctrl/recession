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