## A) Architecture verdict

- **LAG 1 — CHANGE:** Keep penalized logistic regression, but rebuild around a monthly NBER target, one direct 12-month probability, real-time vintages, and genuinely nested walk-forward selection.
- **LAG 2 — KILL:** It failed the predictive test; the bucket percentages invite users to override the validated model with statistically weak analogies.
- **LAG 3 — CHANGE:** Stop counting flags. Validate recession indicators as candidate features; retain valuation/debasement items only in a separately titled, explicitly non-recession “market conditions” checklist.
- **Verdict layer — CHANGE:** Remove “Handl,” “high risk,” and any synthesis that lets unvalidated flags overrule the model. Report facts, probability, uncertainty, and model limitations.

## B) Q1–Q8

**1. Label.** Use **NBER recession months**, with the target equal to any NBER recession month occurring during the next 12 months; 2001 must be included. NBER status is not knowable contemporaneously, but it is the stable economic outcome being forecast—not an input—and 2022 H1 is therefore correctly not labeled a recession. Show the advance-estimate two-negative-quarter rule only as a separate real-time diagnostic; never revise that diagnostic retrospectively.

**2. Frequency and horizon.** Move to monthly observations and a **single direct 12-month model**. Kill the four horizon logits and `1−Π(1−p_h)`: their events are strongly dependent and the combination is not a valid probability. Monthly data do not create more independent recessions, so inference and uncertainty must remain episode-based.

**3. Features.** Freeze the current five as the incumbent, but do not presume all survive: CAPE is especially questionable as a recession predictor. Pre-register only three challengers—building permits, initial claims, and a real-time unemployment/Sahm measure—tested individually and then as one locked three-variable package. Reject HY OAS because its history is too short; reject foreign curves, money aggregates, Fed balance sheet, and term-premium adjustments unless proposed later as a new preregistered experiment.

**4. Statistics.** Keep L2 logistic regression; Bayesian logit with Gaussian priors is substantially the same estimator, while boosting and Markov switching are indefensible with roughly 12 episodes. Select penalty and features inside expanding-window training only. Report walk-forward log loss and Brier skill with recession-episode block-bootstrap intervals, plus leave-one-recession-out sensitivity.

**5. Regime instability.** Do not engineer a QE interaction in response to one conspicuous false positive—that is textbook post-selection overfitting. Retain the 2023 miss prominently and test term-premium-adjusted curves only as a preregistered challenger against the ordinary curve. If it cannot improve pseudo-real-time walk-forward scores across several episodes, reject it.

**6. Architecture.** The validated/unvalidated firewall is sound, but v4 breaches it when flag counts drive the verdict. Failed predictive devices such as LAG 2 should disappear, not survive as numerical “checks.” Non-recession valuation observations may remain, but without counts, implied probabilities, or action language.

**7. Data and operations.** Automate downloads using the standard library plus local CSV caching and retain manual overrides; runtime can remain dependency-light. ALFRED vintages are worth the added complexity for claims, unemployment, CPI, and permits because vintage construction affects the credibility of the entire backtest. Keep vintage preparation in a separate calibration script, not the monthly user-facing file.

**8. Output and benchmarks.** Report the 12-month point probability, base rate, episode-bootstrap 10–90% model-uncertainty range, calibration/validation period, and current inputs. Benchmark against an intercept, a curve-only model, a replicated NY Fed curve specification, and real-time Sahm; Chauvet–Piger is a coincident nowcast and should be displayed separately, not treated as a like-for-like forecast. The expanded model must beat the intercept and curve-only benchmark out of sample; it need not beat every benchmark in every episode.

## C) Top three changes

1. **Replace the technical quarterly label and horizon combination.**  
   Test monthly NBER direct-12-month logit versus frozen v4 and curve-only models over the common sample. Accept only if log loss and Brier skill improve and calibration does not materially deteriorate.

2. **Rebuild calibration as pseudo-real-time nested walk-forward.**  
   At each month, use only then-available vintages and choose regularization using earlier training data. Compare final-data versus vintage-data scores and probabilities; reject any claimed v5 improvement that disappears under vintages.

3. **Run the locked three-feature challenge.**  
   Test permits, claims, and real-time Sahm individually, then jointly, with no additional feature search. Promote a challenger only if it improves both log loss and Brier score, survives leave-one-episode-out analysis, and has positive median block-bootstrap skill improvement.

## D) Biggest risk

Changing the label, frequency, vintage system, and feature protocol simultaneously may make v5 more honest but prevent clean attribution of performance differences; therefore every change must also be evaluated as an incremental, frozen ablation.