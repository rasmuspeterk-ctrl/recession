# ROUND6 — samlet


---

## GPT-5.6 Sol (OpenAI)

VOTE: APPROVE

A8 resolves the blocking defect: both positive and negative labels are now assigned mechanically from the chronology actually available at each historical refit date, without retroactive rewriting.

Reservations for the record:

1. **Benchmark failure needs an explicit consequence.** Section 8 says v5 “must beat intercept and curve-only.” If it fails either benchmark, the multi-feature probability should not be presented as validated. The operational output should fall back to the best qualifying benchmark, while the candidate v5 model is published as “tested, not passed.”

2. **The estimation-sensitivity band may understate total uncertainty.** Episode-bootstrap weight dispersion excludes label-definition uncertainty, structural breaks, and irreducible forecast error. The specified name and footnote are adequate, but no coverage interpretation—especially “80% confidence interval”—should appear anywhere.

3. **Feature re-arbitration must use a fully deterministic path.** Before running it, commit the order in which incumbent features are removed or restored, tie-breaking rules, penalty grid, bootstrap seed policy, missing-data treatment, and definition of “no single rescuing episode.” Otherwise the nested protocol still leaves material researcher degrees of freedom despite publishing the final path.

---

## Kimi K3 (Moonshot AI)

VOTE: APPROVE

A8 resolves the negative-label problem mechanically, and the 18-month floor is correctly sized: historical peak-announcement lags (Dec 2007 peak announced Dec 2008, 12 months; Mar 2001 announced Nov 2001, 8 months; COVID 4 months) sit well inside it, and L_R = max(18, max observed lag) is exactly the floor-plus-mechanical-extension rule I reserved on in Round 4. Three reservations for the record; none block.

1. **Embargo cost must be a published number.** Eligibility requires window end + 18 months, so every training set permanently lacks the most recent ~30 months of observations. With ~13 onsets, any origin within ~2.5 years after an episode trains without it — precisely when that episode is most informative (post-2010 origins without 2008; post-2021 origins without COVID). Require the calibration report to print effective episode count per walk-forward origin and skill with vs. without the newest eligible episode. The honesty discount should be quantified, not absorbed silently.

2. **Provisional-zero asymmetry.** Y=0-when-unannounced is the correct assignment, but every provisional zero that later flips biased its historical fit toward zero. The annual audit should print cumulative flipped zeros and refit sensitivity at L = 12/18/24 months. If headline skill moves >2pp across that range, the embargo length is itself a material fork and must be labeled as such, not presented as a fixed constant.

3. **Off-by-one in onset semantics.** The NBER peak is the last expansion month; the recession begins the following month. With monthly dates binned quarterly, W_t membership must be defined as recession start (peak + 1) in t+1…t+12, i.e. peak in t…t+11. Get this wrong and 2001's onset quarter shifts. Commit the exact mapping in the announcement-date table, with worked examples for 2001 and 2020.

A8 is operational as written. Ratified.

---

## Gemini Pro (latest) (Google)

VOTE: APPROVE

**Reservation 1: The 18-month embargo floor (Section 1)**
The 18-month minimum embargo is excessively conservative. While NBER announcement lags vary (e.g., 2008 was 12 months, 2020 was 3.5 months), forcing a minimum 18-month blind spot starves the walk-forward training set of recent data. A 12-month floor captures the vast majority of historical NBER lags while allowing the model to adapt to regime shifts half a year faster. The annual audit ($L_R$) already protects against longer anomalies.

**Reservation 2: ACM term-premium look-ahead bias (Section 5)**
The ACM term-premium test introduces hidden look-ahead bias and operational fragility. ACM is a derived model, not a raw observable. The NY Fed frequently revises historical ACM estimates based on full-sample smoothing. Using current-vintage ACM data to test historical walk-forward skill violates the strict real-time information constraint unless you source true vintage ACM series (which are not cleanly available via standard FRED APIs). If the ACM test passes, it likely does so on the back of this look-ahead leakage.

**Reservation 3: Bootstrap persistence threshold (Section 4)**
The bootstrap persistence threshold of 60% is too low given the hard cap of 6 features and $n \approx 12$ episodes. A 60% sign-agreement across resamples allows features that fail in 4 out of 10 alternate histories to maintain "admitted" status without a warning flag. A 75% persistence threshold would better guard against overfitting to the specific sequence of late-20th-century recessions.

---

## Grok 4.5 (xAI)

VOTE: APPROVE

Reservations (non-blocking):

1. Dual attrition (Section-1 eligibility lag of horizon+≥18m plus purge of overlapping windows) will leave many origins with very few usable episodes. Calibration must tabulate, by origin, training episodes and positive labels remaining; if median positives <8, the report must flag the design as underpowered and freeze feature admission.

2. Admission gate (≥2% LL and ≥2pp Brier in ≥80% of ~11 LOEO folds) is appropriately strict but low-powered. Publish the exact LOEO count and a simple power note; never relax thresholds after seeing results. Failed challengers stay failed.

3. Live band will frequently contain the base rate, forcing “not distinguishable” language. That is correct; do not soften the mechanical rule or re-introduce ratio-to-base when the band overlaps.

---

## Nemotron 3 Ultra 550B (NVIDIA (free))

VOTE: APPROVE

Reservations for the record:
1. The 18-month embargo floor in Section 1 is arbitrary; the annual L_R audit may ratchet it up but never down, creating asymmetric rigidity. A symmetric rule (e.g., L_R = median observed lag + 6 months, floored at 12) would adapt both ways without discretion.
2. The 6-feature hard cap (Section 4) is a blunt instrument; with n≈12 episodes, even 4 features risks overfitting. A data-driven cap (e.g., max features = floor(episodes/3)) would be more principled and self-adjusting as episodes accumulate.
3. The monthly non-inferiority gate (Section 2) uses a 1pp log-loss margin that exceeds the minimum detectable difference at n≈12. This effectively guarantees quarterly stays primary regardless of monthly's true performance. The margin should be derived from the bootstrap noise floor, not fixed.

---

## Gemma 4 31B (Google (free))

VOTE: APPROVE

**Reservations for the record:**

1. **The "NBER Lag" Paradox:** While Section 1's mechanical rule (Section 1, A8) solves the look-ahead bias, it introduces a structural "blind spot" where the model is intentionally trained on data that is, by definition, lagging the actual economic reality. We are trading real-time accuracy for historical rigor. This is the correct econometric choice, but it must be explicitly communicated to the user: the model is a "recession-onset predictor" based on historical NBER patterns, not a real-time economic indicator.

2. **The "Gate" Complexity:** The Section 2 "Gate" (monthly vs. quarterly) introduces significant operational overhead for a "radical simplicity" project. The requirement to run a full purged expanding-origin walk-forward comparison just to decide on frequency is a high bar. If the monthly model is only marginally better (e.g., 0.5% log-loss improvement), the maintenance burden of monthly data entry and the risk of overfitting to monthly noise may violate the core philosophy of solo-maintainability.

3. **The "ACM Term-Premium" Substitution:** The substitution test in Section 5 is necessary due to the 2023 error, but the decision to keep the raw curve if the ACM test fails is a pragmatic concession. We are essentially admitting that we cannot distinguish between a "broken" signal and a "regime-shifted" signal. The model will remain vulnerable to the same "false alarm" logic if the term premium is indeed the driver of the 2023 distortion.

**Conclusion:** The blueprint is robust. The transition from "technical recession" to "NBER onset" via a mechanical, vintage-aware protocol is the single most important improvement for scientific integrity. Proceed to Build Order.

---

## GPT-OSS-20B (OpenAI (free))

VOTE: APPROVE

Reservations:
1. The mechanical label rule depends on a pre‑compiled NBER announcement table; if this table is not available at the exact snapshot date, the model cannot determine Y_t(R) and would need a fallback, potentially re‑introducing look‑ahead.
2. The fixed 18‑month lag may be insufficient for recessions with unusually long announcement delays; the rule’s L_R adjustment mitigates this but still requires periodic audit and version bump, adding operational overhead.
3. Switching to NBER‑onset labels while retaining the same feature set may alter the predictive relationships; a formal feature‑relevance audit under the new label regime would strengthen confidence that the existing features remain appropriate.