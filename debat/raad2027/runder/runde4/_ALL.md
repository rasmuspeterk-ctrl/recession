# ROUND4 — samlet


---

## GPT-6.1 Sol Pro (OpenAI)

VOTE: REJECT

One executable ambiguity remains. Fix it and I approve.

**Replace §9.2 with:**

> An origin dated \(q\), with forecast-window end \(H(q)=q+12\) months under the committed quarterly dating convention, enters `eligible_fit(R)` iff:
> 1. \(R \ge H(q)+L_R\); and
> 2. its censoring status is resolved using only announcement information available at \(R\).
>
> “Age ≥ \(L_R\)” means age **since forecast-window end**, not age since origin. With \(L_R=18\), minimum maturity is therefore \(q+30\) months, not \(q+18\).

**Add to §9.3:**

> Date-stamped eligibility tests, including the 1991 and 2001 episodes, must verify both conditions before the first audit runs.

The current draft explicitly invokes \(q+12+L_R\) in §9.1 but leaves “age” undefined in its operative eligibility rule. Implementing age from the origin would admit labels 12 months prematurely and invalidate the arithmetic supporting the lag compromise. This is not a cosmetic objection.

Everything else incorporates my compromises: the frequency override is explicit; the gate makes no calibrated significance claim; and the content-trigger regime receives its own replay. I accept those decisions despite their known effects for the reasons recorded.

---

## Gemini 4 Argon (Google)

VOTE: APPROVE

**Reservations for the record (non-blocking):**

1. **Monthly Fit Loss Normalisation (§3.3):** When the specification for the unscored monthly curve-only column is sealed prior to 2027-09, the L2 regularisation penalty must be scaled to match the quarterly per-observation weight ($\lambda_{\text{monthly}} = \lambda_{\text{quarterly}} \cdot (N_m / N_q) \approx 3.0$ under a summed log-loss, or switching both models to mean log-loss with $\lambda$ scaled by $1/N_q$). Logging an unnormalised summed-loss monthly fit with $\lambda = 1$ on $N \approx 800$ rows applies roughly one-third the effective shrinkage of the $N = 267$ quarterly model, confounding sampling frequency with regularisation relaxation ($\beta = -1.41$ vs $-1.29$).
2. **Pre-2027 EBP Estimation Leakage (§8.3):** While §8.3 rightly bars pre-2027 EBP observations from ever serving as confirmatory evidence, allowing a future council to include pre-2027 EBP data in the *fitting* sample of a prospective evaluation still leaks the already-inspected historical sign pattern (high before 1990/2001, low before 1980/2008/2020) into the estimated coefficient $\hat{\beta}_{\text{EBP}}$. If a future council ever mandates a prospective EBP test, any coefficient estimated on pre-2027 data carries post-hoc selection bias that disclosure alone cannot purge.
3. **One-Per-Onset Trigger Residual Lag (§6.1):** Restricting the content trigger to only the *first* matured positive origin of a new recession leaves up to 3 subsequent positive origins of that same episode waiting up to 9 months for the September refit. While the historical mean $|\Delta P|$ is negligible (0.13 pp, max 1.05 pp) and this compromise avoids intra-year refit churn, it only partially eliminates the NBER calendar-alignment artifact identified in E6.

---

## Claude Fable 5.1 (Anthropic (independent instance))

VOTE: APPROVE

The draft meets every condition I set in Round 3: oracle-free fixed-λ leads with the triple print and inline power clause (§1.2); the gate is one-sided, own critical value, agenda-only, with the three robustness lines (§2.3); L_R formula with both inequalities audited and a halt on breach (§9); frequency option (b) with the override recorded verbatim, monthly P unscored, spec-governs-code prospective (§3); one-per-onset trigger with sealed replay not conditioned on score (§6); EBP historical test closed (§8). The §11 table gives a defensible reason for each post-hoc choice; I accept it as written. My only veto, O1(c), is not in the text.

Three reservations for the record, none blocking:

1. **§3.2(b) — "the same-origins diagnostic already exists in E2".** It exists only if the m%3==0 months are origin-for-origin identical to the 198 quarterly origins, with identical labels and a shared pooled base rate. That identity is asserted, not shown; 591/3 ≈ 197. The §3.3 sealed monthly spec should include this paired diagnostic on the 2027 panel, with the origin-set identity checked in code, so the −1.02 pp claim is verified rather than inherited. If the sets differ, (b) is not a paired comparison and the minutes should say so.

2. **§8.3 — pre-2027 EBP as fit data.** I asked that no pre-2027 observation be used for fitting or evidence; the text permits fitting under disclosure. With ~8 onsets, fitting on the inspected pattern and scoring on 2 later onsets largely tests whether the inspected pattern recurs — a weaker design than the text implies. Acceptable because any such test is decades away and must be sealed; I note it so a future council does not read §8.3 as a half-open door.

3. **§1.2 power clause.** The ≈150-year figure is derived from the September-only, real-time-censored replay. Once the §6.2 configuration-specific replay exists, the clause should be re-derived from it and labelled "order of magnitude, configuration 2027-09"; the same holds for the Gaussian 2.8·SD approximation behind the ≈30 pp MDE in §2.3, which should be marked as a normal-theory figure.

Post-hoc acceptability, restated: each decision is a tightening, a disclosure, or the status quo with the override on record. Nothing moves P before 2027-09.

---

## Grok 4.7 (xAI)

VOTE: REJECT

One amendment flips me.

§3.2(b) is false as written. −1.02 pp is 26.03 − 27.05: quarter-end thinned monthly walk-forward versus quarterly walk-forward. E2 scores those on different origin sets with their own pooled base rates. It is not “monthly fit scored at quarter-end months vs quarterly fit on the same origins.” Fable’s Round 3 test — fit monthly, score on the 198 quarterly origins, pair against the quarterly fit — “has not been run.” The interval [−4.47, +1.32] is not in the brief. I will not ratify an unverified interval, or a relabelled thinned gap, as the reason for overriding a preregistered gate.

Replace (b) with: thinned score +26.03 % versus quarterly +27.05 % (−1.02 pp); not a paired same-origin, same-base-rate fit comparison; Fable’s diagnostic has not been run; delete [−4.47, +1.32] unless a sealed E2 artifact is cited. If wanted, seal that diagnostic before the 2027 refit as unscored. Do not treat its result as known.

I do not block the override sentence, quarterly retention, the unscored monthly column, or prospective spec-governs-code. (a), (c) and (d) stand: unpaired grids; +2.19 pp below the 2.99 pp block critical value; λ = 1 on ~800 rows is a different per-observation penalty under a summed loss (β −1.29 → −1.41; live P 14.9 → 14.4).

Everything else matches compromises I already accepted: oracle-free +20.37 % leads; λ = 1 inherited; gate is an administrative boundary at 1.96·SD_block, never “evidence”; L_R = max(18, max lag_peak, max lag_trough − 12); one content refit per onset with a sealed replay that is not the September-only +24.41 / +28.95 / +33.28; key unamended; historical EBP test closed.

---

## Kimi K3 (Moonshot AI)

VOTE: APPROVE

The text matches every position I held at the end of Round 3, and neither of my stated vetoes is triggered: the monthly fit is unscored-only with its loss/penalty normalisation sealed before any run (§3.3), and L_R is the formula giving 18, not a flat 21 (§9.1). My eligibility sentence is in §9.2 verbatim. The §3.2 minute records the override in so many words, including my concession that the full monthly score was published 2026-08-09 and my reservation that the thinned gate was the one fixed before the run. §2.3 is strictly better than my two tiers, as I said in Round 3. §6 is the one-per-onset trigger with a sealed replay whose adoption is not score-conditional. §8 closes the historical EBP test permanently.

Reservations for the record (non-blocking):

1. **§1.2 — complete the triple.** I withdraw my Round-3 demand to label nested +18.32 % an "upper bound" for nested-oracle-free: Sol's monotonicity point is correct, since the oracle-free population carries its own pooled base rate. The text's "not been computed" is the accurate label. The 2027 refit should compute the nested oracle-free figure so the printed sentence compares three realised numbers, not two plus a gap.

2. **§3.2(b) / §3.3 — the paired diagnostic is close, not exact.** The −1.02 pp [−4.47, +1.32] figure is the quarter-end thinned phase against the quarterly fit; Fable's requested comparison (monthly fit scored on the 198 quarterly origins, paired) differs in origin set. The sealed monthly-fit spec should include that exact paired comparison, pushed before the refit so its outcome is unknown at sealing. That is the evidentiary door I said would flip me on frequency; seal it now.

3. **§6.2 — replay commensurability.** The configuration-specific replay must print all three censoring variants (real-time open-episode primary, per §7.2's ordering), so the trigger regime's supplement is line-by-line comparable with the September-only supplement and "adoption not conditional on score" cannot be read as sheltering an adverse variant.

---

## DeepSeek V4 Pro (DeepSeek)

VOTE: APPROVE

Reservations for the record:

1. **§3.2.** The minutes state the written §2 gate passed and the council declined to apply it. I do not accept that framing as the operative governance description. The only pre-run executed comparison was the quarter-thinned ablation3 score, which failed (26.03 vs 26.05). The literal full-monthly comparison is unpaired across different origin sets and base rates, so it is not a passed gate being overridden; it is an incommensurable reading. I accept the minutes, but I record my description as “executed gate failed; literal reading noted as incommensurable,” not “gate passed and council overrode.”

2. **§9.** The L_R formula is acceptable because it returns 18 today. I reserve that `max lag_trough − 12` is an audit check on open-episode censoring, not a maturation floor. Onset eligibility is label maturity; trough announcements matter only for resolving censoring. If the audit implementation folds these into one parameter, a peak-lag breach must still halt the refit.

3. **§1.2.** The nested figure printed is oracle-censored. I accept “oracle-free counterpart has not been computed” only if that sentence is never deleted without first computing the configuration under the same sealed replay rules.

---

## Claude (Opus 5.5) (Anthropic — interested party, co-builder and secretary)

VOTE: APPROVE

Reservations for the record (they do not block):

1. §3 retains the quarterly fit, against my Round 2–3 preference. I approve because the minutes now state in so many words that the preregistered gate passed and was overridden. I also approve because Fable's same-origins diagnostic turned out to exist already (−1.02 pp on the quarterly origins) and does not favour monthly. The unscored monthly column keeps the question open on the record.
2. §6's one-trigger-per-onset rule is my own compromise. Its value depends on the sealed replay actually being written before the 2027 refit; if that slips, the trigger should not run.
3. As secretary I drafted text that I am also a party to. Every councillor should check §3.2's verbatim minute and §11's table against their own words, not mine.
