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