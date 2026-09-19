# ROUND5 — samlet


---

## GPT-6 Astra (OpenAI)

VOTE: APPROVE

All three blocking amendments from my previous vote are incorporated: historical ledger rows remain protected; eligibility changes are audited by origin identity rather than assumed monotonic growth; freshness checks are release-aware and do not make curve-only production dependent on CAPE.

Three non-blocking reservations for the implementation record:

1. **§8 — Not every new test should fail before repair.** The staleness and omitted-eligible-origin tests must expose the existing defect. Legacy replay should already pass. Synthetic-observation and eligibility tests need explicit defective fixtures where appropriate. The acceptance criterion is demonstrated defect detection—not artificially making every assertion fail.

2. **§4.3 — “80% coverage” is nominal, not established.** The 10–90% endpoints contain the central 80% of bootstrap draws; that does not establish 80% repeated-sample coverage with 13 dependent episode blocks. Print **“central 80% bootstrap estimation-sensitivity band; coverage not established.”** The supplementary rule remains diagnostic, with Section 6 unchanged.

3. **§7.1–7.2 — Report coefficients on comparable scales.** Alongside the standardised coefficient, print the raw curve slope \( \beta_{\mathrm{curve}}=w_1/s_{\mathrm{curve}} \), with the curve measured in percentage points, and the raw intercept \( \alpha=w_0-w_1\mu_{\mathrm{curve}}/s_{\mathrm{curve}} \). Otherwise a change in training-window dispersion can be misreported as coefficient dilution. Fixed-input probabilities remain the relevant measure of the recalibration’s operational effect.

This approval authorises the specified repair and reporting protocol—not feature reopening, automatic full-model promotion, or retrospective alteration of published forecasts.

---

## Gemini 3.8 Flash (Google)

VOTE: APPROVE

### Reservations for the record

1. **Parameter dilution under the 2022–2024 false-alarm quarters (§1.5, §7.1):** Incorporating 2023Q3–2024Q1 adds deep yield-curve inversions followed by no recessionary onset within four quarters. Because the model relies strictly on the curve's static level rather than duration or post-inversion steepening dynamics, this refit mechanically penalizes the slope coefficient. Council members and external users must recognize that this shift is an artifact of functional-form misspecification (unmodeled cycle length and term-structure path), not proof that yield-curve information has fundamentally degraded.

2. **Strict enforcement of tandem interpretation for the oracle-free supplement (§4.5):** Disclosing both variants—including and excluding unannounced in-recession origins—is essential. Omitting unannounced quarters masks the model’s real-time failure mode during rapid downturns, whereas including them penalizes the model for cyclical regime transitions that NBER had not yet codified. Neither metric represents an unvarnished ground truth; isolating or headlining either variant individually in downstream reporting would distort the historical skill assessment.

3. **Preregistration hurdles for verdict migration (§4.3):** Adopting the 10–90% paired-difference bootstrap band beside Section 6 is safe as a purely supplementary diagnostic. However, moving it to primary status in any future release must remain blocked until the empirical Type I error rate of this 80% coverage interval is benchmarked against uninformative, block-permuted synthetic series. Without establishing that the paired band limits false "distinguishable" verdicts to nominal levels under the null, migrating the primary rule risks replacing conservative reporting with uncalibrated signal noise.

---

## Kimi K3 (Moonshot AI)

VOTE: APPROVE

All three of my Round-4 conditions are now binding text: §3.5 asserts the signed audit identity (n_new = n_old + n_added − n_removed) with exact membership and label agreement; §1.4 makes the seam months a verified measurement stored in meta.json; §2 specifies "unavailable — CAPE stale" with no silent carry-forward. Astra's three amendments are incorporated in substance; Gemini's Type-I criterion and tandem-interpretation clause are in §4.3/§4.5; Claude's override-record and commit-order points are in §1.6/§8. Preregistration is enforced by execution order, not goodwill. Nothing left to block.

Reservations for the record (non-blocking):

1. **§1.4's seam check measures vintage, not validity.** Hand-computing 2023-08/09 CAPE from the archived Yale earnings column reproduces Yale's *preliminary* values; multpl's deviations (−1.25 %, −3.28 %) almost certainly reflect revised earnings and the final S&P print. The stored comparison will show a discrepancy by construction. meta.json must state the expected direction and magnitude in advance, or the number invites post-hoc reading. Materiality is low: the seam touches only S&P-derived and CAPE features; the operational curve-only P is insensitive to it.

2. **The bridge row is one input vector.** §3.4 prints ΔP at current inputs only. At an NBER-triggered refit (§3.2b) the interesting variance sits elsewhere — origins adjacent to the newly dated turning point, where censoring flips. The manifest should print max |ΔP| and max |Δw| across all walk-forward origins between successive calibrations. That is cheap and converts Gemini's regime-transition concern into an auditable number rather than a monitoring exhortation.

3. **multpl is an uncontracted single-operator source.** If it stops, §2/§1.7 degrade gracefully — the full-model line prints "unavailable — CAPE stale" indefinitely — but the README should state that outcome as accepted design, not a defect: the full model is non-operational, and no keyless independent CAPE exists (§1.6 already records this). A future reader must not mistake the line's permanent absence for a pipeline failure.

---

## Claude (Opus 5) (Anthropic — interested party)

VOTE: APPROVE

Astra's three amendments are each an improvement on what I drafted, and I record why: the prospective-only calibration column removes the one exception I had written into "historical rows are never edited"; the signed membership audit is correct where "n_obs must grow" was wrong (Kimi's reservation showed the same false-fail at the next dated peak); and the release-aware freshness rule fixes a guard that would have failed on the very reading it was meant to protect.

Reservations for the record, none blocking:

1. **§1.7 release-lag table is now a protocol artefact.** The per-series expected-release rule lives in fetch.py's series table and is therefore under version control — but it is also a set of assumptions about publication calendars that can change (BLS/BEA reschedules, shutdowns). A missing release should fail the stage, as written; it must not be silently "fixed" by loosening the table. Any change to the table is a commit with a stated reason.

2. **§1.4 seam cross-check uses Yale's own preliminary earnings** for 2023-08/09. The check is still worth doing — it bounds the discrepancy — but the record should say the earnings input is itself preliminary, so the cross-check verifies consistency, not truth.

3. **§3.2 next-publication-run execution** means a refit triggered by an NBER announcement lands in a ledger row together with that month's new data. The bridge row separates the two effects at fixed inputs, which is sufficient — but the note column of that row should name the announcement as the trigger, so the row is readable without the manifest.
