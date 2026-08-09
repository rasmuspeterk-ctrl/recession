# ROUND5 — samlet


---

## GPT-5.6 Sol (OpenAI)

VOTE: REJECT

One operational amendment would flip me to APPROVE.

Replace Section 1’s label-availability rule. NBER never announces that an expansion month is “undeclared” or formally resolves a negative 12-month window, so the current rule cannot assign negative training labels mechanically.

Use this explicit real-time rule:

- For target window \(W_t=(t,t+12]\), the observation becomes training-eligible only when its horizon has ended and at least 18 additional months have elapsed.
- Reconstruct the NBER chronology publicly available at refit date \(R\) using the committed announcement table.
- Assign \(Y_t(R)=1\) only if, by \(R\), NBER had announced a peak/onset falling inside \(W_t\); otherwise assign \(Y_t(R)=0\).
- Exclude observations inside a running recession only when that recession’s onset had been announced by \(R\). Never use subsequently published dates to alter what the historical fit knew.
- Report any historical case where the provisional zero later changed to one.
- At each annual audit, set the prospective embargo to  
  \[
  L_R=\max(18\text{ months},\ \text{largest announcement lag observed by }R).
  \]
  Changes apply prospectively and increment the protocol version; they do not rewrite earlier information sets.

This makes negative labels observable by a committed rule, permits genuine real-time reconstruction, and prevents the announcement-date table from quietly becoming revised-label look-ahead. Everything else in Revision 2 is acceptable.

---

## Kimi K3 (Moonshot AI)

VOTE: APPROVE

Three reservations for the record; none block.

**1. Onset-label scoring loophole (Section 1).** In-recession months are excluded from *estimation*, but the blueprint is silent on walk-forward *evaluation* origins. An origin inside an ongoing NBER recession has a censored onset target — a new onset is impossible until the current recession ends (1980→1981 is the boundary case, trough to next onset exactly 12 months). Scoring those origins inflates skill with near-mechanical negatives across ≈14% of post-war quarters. One sentence fixes it: origins inside an NBER recession, as dated at the snapshot, are excluded from scoring as well as from fitting. Without this, the purged walk-forward number is biased upward by construction.

**2. Unspecified failure path (Section 8).** "Must beat intercept and curve-only probit" is a release gate, but nothing says what ships if the re-arbitrated model fails it — a live possibility, since purging plus the declaration-lag embargo will mechanically shrink the old +22.9%, which was computed with neither. Specify the fallback now, in advance: publish the best specification that passes the gate (even if that is curve-only), label the full model "tested, not passed," and print both. Pre-committing the fallback is the only protection against a motivated carve-out the first time the gate actually bites.

**3. Residual look-ahead in the shipped tool (Section 9).** MOTOR.py's `cape_percentil()` uses fixed knots fit to the full 1881–2026 distribution, while curve.py calibrates on expanding-window percentiles — train/serve skew plus a hand-copied constant. The "refuses hand-copied constants" rule should explicitly cover these knots: the live percentile must be computed from the snapshot's own expanding history, not from a table that embeds 2026 information.

The rest — purged walk-forward as the sole skill claim, the announcement-date table, the dual-metric admission gate with bootstrap persistence printed, the retired +22.9% — I stand behind. Build it.

---

## Gemini Pro (latest) (Google)

VOTE: APPROVE

Reservations for the record:

1. **ACM Evaluation Window:** Section 5 mandates the adoption decision for the ACM term premium rests on the full-path walk-forward test (1934–2024), scoring pre-1961 missing years at the base rate. This mathematically guarantees ACM will fail against the raw curve's cumulative log-loss due to the 27-year penalty box. The 1961–2024 truncated test should be the primary adoption gate, not a secondary diagnostic.

2. **Redundant Feature Cap:** Section 4 enforces a hard cap of 6 features. Given the strict new admission gates—L2 regularization, expanding-origin purging, ≥80% LOEO stability, and bootstrap persistence—overfitting is already structurally penalized. An arbitrary integer cap is unscientific and risks forcing the rejection of a validated, orthogonal signal that passes all rigorous statistical hurdles.

3. **Vintage Audit Threshold:** Section 9 requires a ≥2pp log-loss materiality to permanently adopt ALFRED vintage data. This threshold is too high. Look-ahead bias from revised data (especially GDP and initial claims) fundamentally invalidates the "walk-forward" claim. If the audit reveals *any* statistically significant inflation of historical skill due to revisions, vintage data must be adopted, regardless of the 2pp threshold. Radical honesty requires evaluating what the model actually saw in real time.

---

## Grok 4.5 (xAI)

VOTE: APPROVE

Reservations:
1. Feature gates (≥2% LL and ≥2pp Brier, 80% LOEO) must print the MDE at n≈12 beside every challenger result, exactly as the monthly frequency gate does; otherwise 2%/2pp is an unanchored round number under the same noise floor.
2. Onset-sample rule (drop months already inside a recession) needs a published sensitivity: effective positive-label count and skill if those months are instead kept with Y=0. If positives thin below ~10 distinct onsets, the exclusion is too costly.
3. ACM near-miss secondary (truncated 1961–) must also report LOEO sign/stability, not only point skill, so the diagnostic matches the primary admission standard.

---

## Nemotron 3 Ultra 550B (NVIDIA (free))

VOTE: APPROVE

Reservations for the record:

1. The 6-feature hard cap with only 11 episodes still risks overfitting; the admission gate's dual-threshold (≥2% log-loss + ≥2pp Brier) plus LOEO stability is necessary but not sufficient. I would prefer an explicit out-of-sample holdout (e.g., post-2010) as a final gate, but accept the bootstrap-persistence flag as a pragmatic compromise.

2. The ACM term-premium test's "pre-1961 missing years score at base rate" injects 27 quarters of uninformative predictions into the walk-forward path, which penalizes the substitution mechanically rather than diagnostically. The truncated-sample secondary comparison (A5) mitigates this, but the primary test's penalty should be acknowledged as a design choice, not a pure skill test.

3. The monthly gate's −1pp non-inferiority margin is arbitrary relative to the minimum detectable effect (MDE) at n≈12 episodes. Printing the MDE next to the gate result (A3) is good, but the decision rule should reference the MDE explicitly: adopt monthly only if the skill difference's confidence interval excludes −MDE, not merely a fixed −1pp.

---

## Gemma 4 31B (Google (free))

VOTE: APPROVE

**Reservations:**

1. **The "Non-Inferiority" Gate (Section 2):** While the -1pp margin for monthly adoption is mathematically sound to prevent chasing noise, it creates a "zombie quarterly" state where a monthly model might be objectively better but remains suppressed by the threshold. I accept this for the sake of the "Radical Honesty" philosophy, but it is a pragmatic compromise, not a statistical ideal.

2. **The 2023 Error Handling (Section 5/6):** I support the decision to reject QE/term-premium adjustments and regime-switching models to preserve simplicity. However, we must ensure the "estimation-sensitivity range" (Section 6) is sufficiently wide in high-volatility regimes. If the bootstrap band is too tight during structural shifts (like 2023), the "Not distinguishable from base rate" verdict becomes a false sense of security.

3. **The ALFRED Complexity (Section 9):** The "one-time vintage audit" is a high-friction requirement for a solo developer. While I agree that ALFRED should not be in the live tool, the threshold for its inclusion in calibration (≥2pp log-loss materiality) is extremely high. We risk building a model that is "honest" about its simplicity but blind to the significant look-ahead bias inherent in using final GDP revisions for calibration.

**Summary:** The blueprint successfully transforms MOTOR from a "black-box-lite" into a rigorous econometric tool. By moving from "technical recession" to "NBER onset" and implementing the "admission gate" for features, we trade the illusion of high precision for the reality of validated skill. The architecture is robust.

---

## GPT-OSS-20B (OpenAI (free))

VOTE: APPROVE

**Reservations**

1. The 1‑percentage‑point non‑inferiority margin for the monthly gate may be too generous given the small number of episodes; a tighter margin (e.g. 0.5 pp) would reduce the risk of adopting a noisier monthly model.

2. The episode‑bootstrap band (10–90 %) is a useful sensitivity diagnostic, but its computation adds non‑trivial runtime and memory overhead; a simpler 90‑10 % confidence interval on the log‑loss could be considered as an alternative.

3. The blueprint requires a maintained table of NBER announcement dates. If this table is not updated promptly, the real‑time label rule may misclassify recent horizons. A lightweight automated check against the NBER API (or a static snapshot) would mitigate this risk.