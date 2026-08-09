# ROUND4 — samlet


---

## GPT-5.6 Sol (OpenAI)

VOTE: REJECT

Two concrete amendments would flip me to APPROVE:

1. **Fix the validation contradiction.** Leave-one-episode-out is not walk-forward because a held-out historical episode is predicted using later episodes. It violates the no-look-ahead constraint and cannot be the primary metric. Replace Section 6 with:
   - Primary: **expanding-origin walk-forward**, with all observations whose 12-month target windows overlap the test episode purged from training.
   - Episode bootstrap or LOEO may be reported only as sensitivity/stability analyses, never as walk-forward skill.
   - Hyperparameter and feature selection must occur entirely inside each historical training window.

2. **Define the NBER target and label availability precisely.**
   - Use **recession onset**, not “any recession month,” otherwise long recessions create positive targets after onset and the model partly predicts continuation rather than entry.
   - Define \(Y_t=1\) when an NBER recession onset falls in months \(t+1,\ldots,t+12\).
   - At each historical refit date, include a training label only if its complete 12-month horizon has elapsed **and** the relevant NBER peak/trough status was publicly declared by that date. Use a small committed table of NBER announcement dates; current USREC values alone are not real-time labels.
   - Replace the arbitrary six-quarter embargo with this information-date rule. A conservative fixed embargo may be an operational fallback, but it must be demonstrated to cover the historical maximum declaration lag.

Reservations otherwise: preregister the numerical monthly non-inferiority margin, and do not print a probability ratio when the base-rate sensitivity band is broad enough to make that ratio misleading.

---

## Kimi K3 (Moonshot AI)

VOTE: APPROVE

Reservation 1 — the frequency gate is underpowered; print that number. With ~12 episodes, the monthly-vs-quarterly non-inferiority comparison has a minimum detectable skill difference on the order of ±5–8pp relative log-loss. "Non-inferior" is the near-certain verdict under that noise floor. The calibration report must state the detectable-effect size next to the gate result, and any switch to monthly must be framed as a timeliness decision, not demonstrated equivalence. Otherwise the gate is theater.

Reservation 2 — admission needs bootstrap persistence, at minimum reported. A ≥2% mean log-loss gain across 12 episodes can be manufactured by two or three quarters inside a single episode. The LOEO sign-stability and no-single-rescuing-episode conditions catch most of this, but for every challenger — admitted or not — print the sign frequency of its improvement across the ~1000 episode-bootstrap resamples. A challenger passing the gate with <60% bootstrap persistence carries that fact next to its number in the output.

Reservation 3 — the NBER target is partially unknowable exactly when it matters most. Median peak-declaration lag is ~8 months (2020: 4 months; 2001 trough: 20 months). Two consequences. First, the 6-quarter embargo must be an automatic floor with mechanical extension while any window month is undeclarable — not a judgment call at refit time. Second, the live output must state explicitly that P is conditional on NBER dating as of the snapshot date. The advance-estimate diagnostic is the only real-time bridge across that gap: keep it visible, keep it labeled unvalidated, and never let it feed the probability.

None of this blocks. The draft honors the philosophy mechanically — preregistration, published failures, the language rule tying verdict words to the band — which is the part that actually matters.

---

## Gemini Pro (latest) (Google)

VOTE: APPROVE

Reservations for the record:

1. **Bootstrap volatility on n≈12:** Bootstrapping a sample of roughly 12 episodes to construct a 10–90% estimation-sensitivity band will yield highly unstable bounds. Small-sample bootstraps systematically underestimate true tail risk. The resulting band will correctly demonstrate uncertainty, but will likely remain overconfident at the extremes.

2. **Monthly non-inferiority gate:** Requiring strict non-inferiority in episode-blocked skill for the monthly model may falsely reject it. Monthly data inherently carries a higher noise-to-signal ratio, which degrades log-loss, but the 60-to-90-day operational lead time gained over quarterly macroeconomic prints has real-world utility that the strict scoring rule ignores. 

3. **ACM pre-1961 penalty:** Forcing the ACM term-premium model to score at the unconditional base rate before 1961 is a necessary stricture to prevent look-ahead bias, but it biases the test against ACM if the 1934–1960 period had a localized base rate significantly different from the full-sample average. If the ACM test fails by <0.5% log-loss, a secondary truncated-sample comparison (1961–2024) should be published alongside it to isolate whether the failure is due to the missing data penalty or actual signal degradation.

---

## Grok 4.5 (xAI)

VOTE: APPROVE

Reservations (non-blocking):
1. Monthly non-inferiority gate needs a pre-specified numeric rule (e.g., episode-blocked log-loss skill no worse than −1 pp vs quarterly baseline, plus thinned scores); “non-inferior” alone is too elastic.
2. Episode bootstrap (n≈12) will yield wide 10–90% bands that frequently contain the base rate; enforce the language rule rigidly so the point estimate is never narrated as “low/high” when overlapping.
3. Re-arbitration must be allowed to drop any incumbent (including curve) with zero grandfathering; publish the nested selection path so the retired +22.9% cannot reappear.

---

## Nemotron 3 Ultra 550B (NVIDIA (free))

VOTE: APPROVE

Reservations for the record:
1. The 6-quarter NBER embargo may still leave real-time ambiguity at turning points; consider a formal "nowcast vs forecast" split in the live output.
2. The dual admission gate (≥2% log-loss + ≥2pp Brier) could admit a feature that passes by chance on one metric; require both improvements to hold in ≥80% of LOEO folds.
3. "Estimation-sensitivity range" is well-named but users may misinterpret; add a one-line output footnote: "Not a predictive interval; reflects weight sensitivity to episode composition."

---

## Gemma 4 31B (Google (free))

VOTE: APPROVE

**Reservations for the record:**

1. **The "Advance-Estimate Diagnostic" Risk:** While I support the "honesty firewall," providing a real-time GDP diagnostic (two negative advance estimates) in the output—even if labeled unvalidated—creates a psychological "backdoor" for the user. There is a high risk that a user will treat this diagnostic as a proxy for the model's probability, effectively re-introducing the "vibes" the architecture seeks to kill. I recommend this be moved to a strictly separate "Data Quality/Volatility" section to prevent cognitive leakage into the probability assessment.

2. **The "Estimation-Sensitivity Range" Naming:** While I accept the name change from "predictive interval" to "estimation-sensitivity range" to satisfy Sol, we must be extremely careful with the documentation. If the user interprets this as a measure of *market volatility* or *error variance* rather than *parameter uncertainty* (due to the small $n$ of episodes), the model's utility for risk management collapses. The distinction between "the model is uncertain" and "the economy is volatile" must be mathematically and linguistically airtight.

3. **The ACM Term-Premium Substitution:** I accept the "one boxed test" approach, but I hold a reservation regarding the "pre-1961 truncation" penalty. If the term-premium series is significantly more stable or has a different distribution than the raw curve in the 1940s-50s, the penalty might be mathematically unfair. However, given the "radical simplicity" and "no complexity without proof" constraints, I concede this to maintain the build order.

---

## GPT-OSS-20B (OpenAI (free))

VOTE: APPROVE

**Reservations for the record**

1. **Manual CAPE/margin debt updates** – The model still relies on a human‑edited override for Shiller CAPE and FINRA margin debt. A clear, versioned update protocol (e.g., a scheduled GitHub action that pulls the latest spreadsheet and flags any changes) should be documented to avoid stale inputs.

2. **Bootstrapped sensitivity band** – The 10–90 % band printed with each probability is an estimation‑sensitivity range, not a frequentist predictive interval. The documentation should explicitly state this distinction and advise users that the band reflects model‑parameter uncertainty, not future‑outcome uncertainty.

3. **6‑month training embargo** – Excluding the most recent six quarters from each refit protects against look‑ahead bias, but the rule may need adjustment if data revision lags shrink or if the GDP series becomes more stable. A periodic audit (e.g., annually) to confirm that the embargo still yields unbiased training windows is recommended.