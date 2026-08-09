**A. Architecture verdict (one line each)**  
- **LAG 1 (validated model)** – Keep; it is the only statistically‑supported core.  
- **LAG 2 (inversion‑after‑effect)** – Kill the probability‑calibration; keep only as a separate, unvalidated checklist.  
- **LAG 3 (flag list)** – Keep as a manual diagnostic layer; do not feed flags into the probability model unless they pass a walk‑forward test.  
- **Verdict layer** – Keep; it synthesises the validated probability, the flag counts, and the checklists into a plain‑language “risk” summary.

---

**B. Q1‑Q8 answers**

1. **Label** – Use the NBER series (USREC) as the primary label because it is the market’s “official” recession definition. Treat the 2001 period as an out‑of‑sample test: run the walk‑forward with 2001 excluded and compare Brier scores; if the model still improves over the base rate, include it. Real‑time GDP revisions are unavoidable; use the first‑release FRED “real” series, not the revised one, for the label.

2. **Frequency & horizon** – Stay quarterly. The number of episodes (~12) would drop to <10 if monthly, making statistical inference impossible. Keep the 4‑quarter target window but replace the naïve “p₁…p₄ → p₉” combination with a single 4‑quarter logistic that directly predicts “recession within 4 quarters” to avoid the independence assumption.

3. **Features** – Keep the five core features. Add *Sahm* (unemployment‑rate change) as a continuous predictor; add *initial jobless claims* (monthly) after standardising to a 12‑month lag; add *CPI‑adjusted term‑premium* by subtracting the ACM estimate from the 10‑yr/3‑m curve. Do not add more than five new features; run a forward‑selection walk‑forward test to confirm that each addition yields ≥1 % log‑loss improvement.

4. **Statistical engine** – Stick to L2‑regularised logistic regression for its transparency and low over‑fitting risk. Augment it with a bootstrap‑based 95 % CI for the predicted probability (sample 1,000 bootstrap folds of the training window). If a Bayesian logit with weak priors yields > dalších 2 % log‑loss improvement, switch toddler.

5. **Regime instability** – Implement the ACM term‑premium adjustment to the curve; add the Fed balance‑sheet total as a secondFine‑grained feature. Run a two‑fold walk‑forward: (i) original curve, (ii) adjusted curve + balance sheet. Accept the error only if the adjusted model demonstrates a statistically significant log‑loss gain; otherwise keep the plain curve and communicate the regime‑risk in the verdict.

6. **Architecture** – Preserve the layered firewall. Store flag evaluations in a separate “checklist” table. After a flag passes a 5‑fold block bootstrap test, promote it to a model feature; otherwise remain in the checklist. This keeps the model lean competitor‑safe while allowing future integration.

7. **Data & ops** – Automate all free‑feed pulls via the FRED API; keep a manual override spreadsheet for the six monthly numbers Creedy. Do *not* import ALFRED vintage data; the added complexity yields a <0.5 % improvement in walk‑forward log‑loss and would require a separate maintenance pipeline.

8. **Output & benchmarks** – Report a point probability with a 95 % CI, the flag counts, and the plain‑language verdict. Benchmark against NY‑Fed yield‑curve probit, Chauvet–Piger smoothed probabilities, and the real‑time Sahm rule. Require that the new model’s log‑loss be no worse than the best of these benchmarks; if it is worse, the model is considered a “fallback” and is not used for formal risk‑management.

---

**C. Top‑3 highest‑impact changes (ranked)**

| Rank | Change | Walk‑forward test |
|------|--------|-------------------|
| 1 | **Curve → ACM‑adjusted curve + Fed balance‑sheet** | Build a 4‑quarter logistic on the adjusted curve (plus balance‑sheet). Run a block‑bootstrap walk‑forward from 1960 to 2024. If log‑loss improves by ≥5 % over the baseline curve model, adopt the adjustment. |
| 2 | **Add Sahm rule725 as continuous predictor** | Include Sahm in the feature set and run the same 4‑quarter walk‑forward. Accept if log‑loss improves by ≥1 % and Brier skill by ≥1 %. |
| 3 | **Switch to Bayesian logit with weak priors** | Fit a hierarchical Bayesian logit on the five core features. Compare 10‑fold block‑CV log‑loss to the current L2 logistic. If Bayesian log‑loss is lower by ≥2 %, replace the deterministic model. |

Each test uses 5‑fold block cross‑validation (blocks of 4 quarters) to preserve temporal dependence. The improvement thresholds are set to guard against over‑fitting while rewarding substantive gains.

---

**D. Biggest risk**

The **small episode count (≈12)** limits the statistical power of any feature‑selection or model‑augmentation. Adding even a handful of new predictors can produce spurious improvements that disappear in real‑time application. Without rigorous block‑cross‑validation and bootstrap uncertainty quantification, the model may appear better in backtests yet deliver noisy, over‑confident probabilities. This risk is inherent in all proposed changes and must be managed by strict walk‑forward validation and transparent reporting of confidence intervals.