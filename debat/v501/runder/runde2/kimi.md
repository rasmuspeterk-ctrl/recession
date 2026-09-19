# KIMI K3 — ROUND 2

## 1) Attacks

**Gemini, Q5:** *"shifting from the 4th weekly print to the 4-week monthly mean cannot bridge a 60-percentage-point performance deficit."* This is an empirical claim about a test Gemini refuses to run, and the leverage structure says otherwise. Log-loss here is concentrated: 12 onsets, roughly 50 positive origins carry the entire metric. claims_mom is a month-end momentum feature; in March 2020 weekly initial claims ran ~0.28M → 6.87M within the month. Last-week-of-month versus monthly mean is not a perturbation of the same variable at the origins that dominate the loss — it is a different variable there. Flipping the score on two high-leverage origins moves aggregate skill by tens of pp. Whether it bridges −61.9pp is unknown until run; the fix is five lines. And the hygiene argument inverts: the preregistered object was the monthly-mean test; −61.9pp is the erratum, not the preregistered result. "Document only" also leaves the no-op in the code as a latent defect for every future aggregation. Rejection stands regardless; the search stays closed.

**Gemini, oracle-free score:** *"imputing Y_t = 0 for unannounced origins."* Sign error. NBER announced the Feb-2020 peak on 8 June 2020. Under Gemini's rule, 2020Q1 origins get Y=0 imputed, and an elevated P is scored a miss for being right. The rule rewards low probabilities precisely at unannounced onsets — the exact origins the supplement exists to capture. The 18-month floor encodes label ignorance, not bureaucratic delay. Claude's Y′ (recession ongoing at origin, or onset within 4 quarters, per the announcement table as of the scoring date) is the correct real-time label.

**Astra, Q2:** *"Operational curve-only estimation should not depend on CAPE availability."* After the spine fix, it doesn't: CAPE and curve both run to 2026-09, and the all-BASE10 mask binds only through cape_pct's 120-month burn-in — pre-1881. Origins gained by Astra's pairwise E_AB scheme: **zero**. Cost: with 8 gate models, up to C(8,2)=28 pairwise intersection samples, each with its own unestimated noise floor, while the published 4.4pp MDE was estimated on the single common sample. Comparability down, complexity up, benefit nil.

## 2) Steelman

Claude's **truncation regression test**: truncate the stitched spine at 2023-09, run the full chain, require w = [−2.1755, −1.6907], n_obs = 264 exactly. My byte-identity check proves the inputs are unchanged; Claude's proves the whole chain — row indexing, to_quarterly, mask, fit — is unchanged. Byte-identity can pass with a row-alignment bug that silently shifts quarters; the truncation test cannot. Adopted as the gating spine test.

## 3) Revisions

- **Q1:** add the truncation test as the gate; keep stitch at 2023-07, my tolerances, 45-day staleness guard.
- **Q3:** replace my bare 8-char weight tag with Astra's per-row manifest (code version, snapshot hash, announcement-table hash, train-end, n_obs, w, standardisation, base rate), hashed into one ledger field. Keep scheduled re-anchoring: NBER-table change or 12 months elapsed, whichever first; bridge line at the splice.
- **Q4:** concede Claude's Y′ for the oracle-free score — my as-of-date censoring with the strict onset label scores 2008Q2-type origins as misses that live users experienced as hits. Print it as a distinct event definition, never summed with the primary. Paired rule: extend my two-quarter parallel run to Claude's twelve months **and** backtest both rules on the full walk-forward; the council votes with the backtested disagreement rate, not two live origins.
- **Q7:** adopt Gemini's base-rate gap, resolved my way: the base rate is a calibration parameter — frozen with the weights, updated only at re-anchor events, recorded in the manifest. Not a fixed 18.2 % constant, not monthly drift.
- **Q5, Q6, Q8:** unchanged. My Q8 block 3 is not triggered by Claude's amended plan, since the paired-rule switch is not in this release.

## AGREE
- Stitch at 2023-07; no full rebuild; automated overlap tolerances; staleness guard (all four).
- Frozen weights, scheduled re-anchoring; monthly refit is dead (all four — Claude moved).
- Episode table plus LOEO as diagnostic, not co-primary (all four).
- v5.0.1 framed as data correction; side-by-side before/after reporting; version recorded in ledger (all four).
- No councillor proposes re-firing the fallback on the new panel — make the prohibition explicit in the README.

## DISAGREE
- **Q5:** fix-and-rerun (me, Claude, Astra) vs document-only (Gemini).
- **Oracle-free label:** Claude's Y′ (me, Claude) vs Gemini's zero-imputation vs Astra's onset-only with archived forecasts — three variants live.
- **Q2:** single common mask (me, Claude, Gemini) vs Astra's pairwise evaluation samples.
- **Paired-rule endgame:** permanent accompaniment (Gemini) vs becomes the verdict rule after a parallel year (Claude; me: council vote after 12 months plus backtest).
- **Anchor month:** January (Claude) vs September (Astra, Gemini) vs rolling 12-month (me) — trivial, unresolved.

## CHANGED-MY-MIND
- Oracle-free label: from my as-of-date onset-only spec to Claude's Y′ — the 2008Q2 argument is decisive for a user-experience metric.
- Parallel run: two quarters → twelve months plus a full walk-forward backtest; two live origins cannot estimate a disagreement rate.
- Weight tag → full per-row manifest hash (Astra's construction is strictly stronger than mine at equal cost).
- Spine gating test: added Claude's truncation regression test; byte-identity alone is insufficient.