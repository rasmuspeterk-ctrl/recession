# RÅDETS KONSENSUS — MOTOR v5.0.1 (første rekalibrering)

**19. september 2026 · fire deltagere: GPT-6 Astra, Gemini 3.8 Flash, Kimi K3 og Claude Opus 5 (som selv byggede v5 og skrev udkastet — erklæret part) · fem runder · enstemmigt 4/4 i runde 5 · samlet pris $1,37**

Orkestrator, brief, alle indlæg og sekretærfiler ligger i [`debat/v501/`](debat/v501/). Claudes indlæg blev skrevet til fil før hver runde, så de tre eksterne så dem på lige fod; sekretærens matrix og udkast er mærket som partsindlæg og blev udfordret (Astra korrigerede indramningen af sin egen position i runde 3).

## Hvad rådet blev indkaldt om

Kalibreringspanelets månedlige rygrad er `shiller.csv`, og Yales fil er frosset ved september 2023 (verificeret 19/9: `Last-Modified 17 Oct 2023`). Alle features — også kurven, som FRED leverer til 2026 — ender derfor 2023Q3 i panelet, og rækkeuniverset ender 2023Q2. Konsekvens: ni "re-ankringer" siden trin 6 gav **identiske vægte** (`w = [−2,1755, −1,6907]`, n_obs 264) på fem forskellige snapshots. README'ens ritualskridt "re-anker vægtene" har aldrig ankret noget, og 2–3 kvartaler med kendt label (2023Q3–2024Q1: dyb inversion, ingen onset) står uden for fittet. Claude fremlagde en femtrins-plan (stitch FRED SP500 + multpl CAPE + CPIAUCNS på Shiller ved 2023-07; udvid panelet; episode-tabel; parret sprogregel + oracle-fri score; version v5.0.1) og bad rådet skyde den ned.

## Hvad rådet besluttede — og hvad der blev skudt ned

Hele den engelske konsensustekst står ordret nedenfor; den *er* specifikationen. De afgørende ændringer i forhold til Claudes udkast:

| Udkastet sagde | Rådet besluttede | Hvem drev det |
|---|---|---|
| Månedlig re-ankring fortsætter | **Afskaffet.** Vægte, standardisering og basisrate fryses; refit kun hver september og ved hash-ændring i `nber_announcements.csv` (ny top/bund), eksekveret ved næste månedskørsel — deterministisk, aldrig skønsmæssigt. Måneds-ritualet bliver fetch → manuelle tal → motor. | Gemini (veto mod månedlig), Astra (deterministisk trigger), Kimi |
| Fælles BASE10-maske for alle modeller | **Start fast 1947Q2; slut per models egne features.** Gaten printes kun når origin-identiteterne matcher — ellers hård fejl, "comparison unavailable", curve-only kører videre. Ingen parvise samples. | Astra (veto mod CAPE-gidsel), Gemini/Kimi (identiske origins), Claude (kompromiset) |
| Parret Δ-regel bliver dommen efter 12 mdr | **Supplement, aldrig automatisk.** Begge regler backtestes nu over hele walk-forward'en; enhver ændring af domsreglen er en separat, senere rådsbeslutning mod præregistrerede kriterier inkl. Type I-fejl på syntetiske serier. | Kimi (veto), Astra, Gemini; Claude trak sig |
| Oracle-fri score med Y′ = "recession i gang eller onset" | **Modellens egen label** (ny onset inden 4 kvt), realtids-censurering, printet **to gange** (alle live-publicerbare origins / eksklusive de "additional live-publishable origins" i uannonceret recession), tolket i tandem. | Gemini (stejlings-mekanismen), Astra (estimand-skifte), Kimi; Claude trak Y′ |
| Kalibreringshash skrives ind i de to gamle hovedbogsrækker | **Nej.** Ny kolonne kun fremadrettet; historiske rækker røres aldrig; separat mappingfil til den gamle kalibrering. | Astra (runde 4-afvisning) |
| "n_obs skal vokse med præcis N" | **Fortegnsbevidst audit:** n_new = n_old + tilføjede − fjernede, med publicerede lister og begrundelser — en ny NBER-top både modner og censurerer origins. | Astra, Kimi |
| 45-dages friskhedsregel | **Udgivelses-bevidst:** per serie en committed forventet seneste periode (augustdata stemplet 1/8 er 49 dage gamle 19/9 og stadig nyeste). Manglende CAPE blokerer fuldmodel-linjen, aldrig curve-only. | Astra |
| Claims-fejlen dokumenteres kun | **Rettes og genkøres** som præregistreret erratum; −61,9pp bliver stående som "superseded implementation result"; ingen forfremmelse uanset; pipeline-bred audit af aggregeringsfejl-klassen. | Claude, Astra, Kimi; Gemini gav sig i runde 2 |
| — (manglede i udkastet) | **Gaten på det udvidede panel kan ikke flytte den operationelle model.** Slår fuldmodellen curve-only med mere end MDE, udløser det en rådsbeslutning om v5.1 — aldrig et automatisk skift. | Kimi |
| — (manglede) | **Forudsigelse før kørsel**, tilskrevet Kimi: mindre absolut negativ kurvekoefficient, lavere skill på udvidet panel end +34,3 %, lavere P ved faste inputs. Falsificerbar, ikke acceptancetest; Astras forbehold printes ordret. | Kimi, Astra |
| — (manglede) | **Staleness-guard implementeres først** — den test der ville have fanget den frosne rygrad i oktober 2023. Commit-historikken viser de fejlende tests før reparationen. | Kimi, Astra, Claude |

Feature-søgningen forbliver lukket. Intet kommer ind i P. Section 6-sprogreglerne, den forhåndsforpligtede fallback og alle publicerede afvisninger står. v5.0.1 beskrives overalt som en *data- og estimationsreparation* — den obligatoriske sætning under broen: *"A lower or higher recalibrated probability is changed estimation, not changed economic risk."*

## Afstemningsforløb

- Runde 1: fire uafhængige forslag. Runde 2: angreb og revision (Gemini gav sig på claims; alle tog truncation-testen; Kimi og Claude byttede plads på Y′).
- Runde 3: konvergens på sekretærens matrix — alle syv åbne punkter lukket med kompromiser.
- Runde 4: **3 for, 1 imod** (Astra) med tre minimale ændringsforslag, alle indarbejdet.
- Runde 5: **4/4 APPROVE.** Forbeholdene nedenfor er ikke-blokerende og indgår i implementeringsprotokollen.

---

# CONSENSUS TEXT — MOTOR v5.0.1 (Round 5 draft for ratification)

*Assembled by Claude from Rounds 1–4. Round 3 amendments are marked [A], [G], [K]; Round 4 changes are marked [R4] with the councillor who required them. The Round 4 vote was 3 APPROVE / 1 REJECT (Astra) with three minimal amendments; all three are incorporated in substance, together with the concrete non-blocking reservations of Kimi, Gemini and Claude.*

## 0. Nature of the release

v5.0.1 is a **data-and-estimation repair**. Unchanged: model class (L2-logit), features, label (NBER onset within 4 quarters, announcement-embargoed, in-recession origins censored), gate metric (pooled walk-forward log-loss vs expanding intercept), Section 6 language rules, the precommitted fallback, every published failure. The feature search stays closed. Nothing enters P. The release is described everywhere as a repair, never as an upgrade or deterioration in predictive skill.

## 1. Spine

1.1 **Stitch, no rebuild.** Yale's `ie_data.xls`-derived file is kept in-repo, immutable, under its own name (`shiller_yale_2023-09.csv`). A separately named composite (`spine.csv`) carries Shiller rows through 2023-07 byte-identical, then FRED `SP500` daily → monthly mean, FRED `CPIAUCNS`, and multpl monthly CAPE from 2023-08 onward. Every row has a provenance column. [A][K]
1.2 **Tolerances, asserted in the test suite.** SP500 overlap: median |dev| ≤ 0.1 %, ≥ 99 % of months within 1 %. CAPE overlap 1990-01..2023-07: median |dev| ≤ 0.1 %, max 1 %. CPI: agreement within rounding, not exact equality. Every exception documented, including Shiller's preliminary 2023-08/09. [A][G][K]
1.3 **multpl parser.** Hard assertions: row count ≥ 1860, first date 1871-02, closed calendar months only. Page bytes hashed into meta.json; revisions diff-marked like FRED; a parse failure produces an `.ukomplet` snapshot, never a partial spine.
1.4 **Seam months verified, not adopted.** The two composite months that replace Shiller's preliminary rows (2023-08, 2023-09) are cross-checked once: CAPE hand-computed from the FRED SP500 monthly mean, CPIAUCNS and the earnings column of the archived Yale file (which runs to 2023-09), compared with multpl; the result is stored in meta.json. [R4 Kimi]
1.5 **Two spine tests.** (a) *Legacy replay* — the frozen Yale inputs through the chain must reproduce `w = [−2.1755, −1.6907]`, `n_obs = 264` exactly. (b) *Correction bridge* — the corrected spine truncated at 2023-09 is run and any difference to (a) is measured and reported, not required to be zero. Both are mandatory CI assertions. [A][G][K]
1.6 **Outlier guard.** CAPE outside [5, 60] or |m/m change| ≥ 15 % fails the snapshot unless the run is repeated with `--accept-outlier`. The override records the affected observations, exactly what was checked (in practice multpl's CAPE against the FRED SP500 monthly mean and CPI that feed it — there is no keyless independent CAPE source, and the record must not imply one) and the reason — in meta.json and in the ledger note column of the affected reading. [R4 Claude] It bypasses only the outlier check, never provenance, parsing or eligibility checks. [A][K]
1.7 **Staleness guard — release-aware.** Age measured from an observation's timestamp is not release latency: August monthly data stamped 1 August are 49 days old on 19 September and still the latest release. Each source therefore carries a **committed release-lag rule** in the series table — the latest observation period expected at the publication cutoff (e.g. GS10: previous month; PCEPI: two months back; GDP: previous quarter, advance estimate; multpl CAPE: previous closed month). An unexpected missing release fails the affected stage. Missing CAPE or any other non-operational input blocks the full-model comparison and the affected diagnostics, **not** an otherwise valid curve-only reading; no partial composite is ever accepted as complete. This is the test that would have caught the frozen spine in October 2023; it is implemented first. [R4 Astra; A][K]

## 2. Row universe

The row universe's **start is a protocol constant, 1947Q2** (so the legacy replay holds). Each model's **estimation end** is set by its own features and the label; the operational curve-only model never depends on CAPE availability. [A] A gate comparison is printed **only when origin identities match** — not counts — at every walk-forward training/evaluation split; otherwise it is a hard error, the line prints "comparison unavailable", and curve-only production continues. No pairwise intersection samples, no dual estimates. [A][G][K] The calibration manifest records per-model estimation end and n_obs. [K] When CAPE is stale or unavailable, the monthly full-model line prints "unavailable — CAPE stale"; the last good value is never carried forward. [R4 Kimi]

## 3. Calibration cadence and versioning

3.1 **Frozen between events.** Weights, standardisation parameters and the fitted base rate are frozen between re-anchor events. Monthly re-anchoring is abolished; the monthly ritual becomes fetch → manual inputs → motor.
3.2 **Events.** (a) Annually, at the September publication. (b) A hash change of the committed `nber_announcements.csv` that adds a new peak or trough, executed at the **next monthly publication run** under this deterministic rule — never at a discretionary time, never in response to the resulting probability; formatting changes do not trigger; a triggered refit does not reset the September schedule. [A][K]
3.3 **Manifest.** Each event bumps the version (v5.0.x) and commits a calibration manifest: code commit, snapshot hash, announcement-table hash, train-end, n_obs, w, mu/sd, base rate, per-model estimation end and n_obs. Its 8-character hash is written in a new ledger column `kalibrering`, **populated prospectively only**. Existing rows remain unchanged except for optional provenance annotations in their note column; a separate committed mapping file links the historical readings to the legacy v5.0 calibration manifest. The rule "historical rows are never edited" stands without exception. [R4 Astra; replaces the schema migration]
3.4 **Bridge row.** At each splice the ledger's first row under the new manifest prints P under both the old and the new weights at identical inputs.
3.5 **Refit-time assertions.** Before fitting, the eligibility audit publishes the **added, removed and relabeled origin IDs with reasons** — a newly dated peak both matures pre-peak origins and censors post-peak origins the floor had released, so counts are not monotonic. Assert n_new = n_old + n_added − n_removed, exact membership agreement with the audited set, and label agreement for every retained origin; any unexplained change fails. [R4 Astra, Kimi; replaces "n_obs must grow"] Origins inside the 18-month floor are NaN, never 0 (test). A synthetic new eligible observation must demonstrably reach estimation (test). [A][K]
3.6 **Base rate.** Expanding intercept inside the walk-forward; frozen calibration parameter in the verdict, recorded in the manifest. [G][K]

## 4. Diagnostics printed with the reading (no gate changes)

4.1 **Episode table.** 12 onset rows plus one row containing all negative origins. Per row: n, summed model and baseline log-loss, mean Brier, and the additive contribution 100·Σ(L0−Lm)/ΣL0, which sums exactly to the pooled improvement. Negative-origin losses are additionally shown by the existing chronological bootstrap blocks, whose boundaries are published and never re-optimised. [A][K]
4.2 **LOEO.** Refit excluding each episode's block (no future training data), score the block; all 12, median and minimum printed as sensitivity — never co-primary.
4.3 **Paired rule (supplement).** Δ_b = P_b(x_now) − base_b over the existing episode-block bootstrap draws, paired by draw; the 10–90 % band (80 % coverage, stated as such) excluding zero is the supplementary criterion, printed beside Section 6, whose verdict and ratio suppression are unchanged. Both rules are backtested now over the full walk-forward, same origins, same draws; the disagreement count and the disagreeing origins are published. Any change to the verdict rule is a **separate, later council decision against preregistered criteria**; elapsed time alone is never sufficient, and those criteria must include the empirical Type I error rate of the 80 % band on synthetic, uninformative exchangeable sequences. [R4 Gemini] The README states in one sentence that no automatic migration exists. [A][G][K]
4.4 **Historical paired-loss bootstrap** (Gemini's construction) is a skill diagnostic and is printed next to the MDE in the skill section, not in the verdict.
4.5 **Oracle-free supplement.** Label unchanged: new onset within 4 quarters. Eligibility reconstructed from the announcement table as of each origin; mature labels only; the baseline scored on identical coverage; unreconstructable origins reported, never dropped silently. Printed **twice**: over all live-publishable origins, and excluding the *additional live-publishable origins* (in recession but unannounced at the time), whose count and loss contribution are disclosed. That is the terminology; they are not called "correct but late". The two variants are interpreted strictly in tandem and never cited in isolation: the exclusion variant evaluates the model only on cycles where NBER dated quickly or expansions persisted. [R4 Gemini] Scoring any other target, and zero-filling immature labels, are excluded. [A][G][K]

## 5. Claims erratum

`monthly_mean` is fixed; the claims_mom test is re-run exactly as preregistered, no tuning. −61.9pp is published as "superseded implementation result" beside the corrected number. Whatever the result, no promotion; the search stays closed. A pipeline-wide audit of the aggregation bug class covers all 20 fetched series and the 3 manual inputs, with a weekly→monthly aggregation test. [A][G][K]

## 6. Gate on the extended panel

The curve-only-vs-full comparison is re-run and republished (it is part of finalize6). Its outcome **cannot** change the operational model in v5.0.1: if the full model beats curve-only by more than the MDE, that triggers a council decision for a v5.1 protocol — never an automatic switch. The six other rejected candidates keep their published numbers with the footnote "computed on the panel ending 2023Q2". [C, unopposed]

## 7. Reporting

7.1 The README states, **before the run and attributed to Kimi**, the falsifiable prediction: a smaller absolute negative curve coefficient; extended-panel skill below the truncated panel's +34.3 %; a lower P at fixed inputs. It is a prediction, not an acceptance test; the outcome is published whether it succeeds or fails, with Astra's caveat printed verbatim: the fixed-input probability and the historical skill are different objects, and none of the three directions is guaranteed once the intercept, standardisation and sample change together. [A][K]
7.2 Staged bridge at one fixed current input vector: (i) legacy pipeline; (ii) corrected sources on the original origins; (iii) extended panel. Each stage shows P, base rate, band, coefficients, n_obs; the attribution is stated to be order-dependent. [A]
7.3 The walk-forward is published twice, truncated vs extended; common-origin and added-origin skill are reported separately. [A][K]
7.4 Mandatory sentence under the bridge: *"A lower or higher recalibrated probability is changed estimation, not changed economic risk."* Motor prints the version in its header; dashboard.json carries a version field.

## 8. Order of execution

1. Staleness guard, spine tests, eligibility audit and refit assertions are written first and must fail on the current state. 2. The prediction (7.1) is committed to the README. 3. The spine is built; legacy replay passes; correction bridge reported. 4. Refit; manifest; bridge row. 5. Diagnostics (§4). 6. Erratum and audit (§5). 7. Publication (§7). Nothing in §4–§7 is looked at before §1–§3 are committed. The commit history shows the failing tests before the repair. [R4 Claude]

---
**VOTE requested.** First line 'VOTE: APPROVE' or 'VOTE: REJECT'.


---

# FORBEHOLD TIL PROTOKOLLEN (runde 5, ordret)

### GPT-6 Astra (OpenAI)

VOTE: APPROVE

All three blocking amendments from my previous vote are incorporated: historical ledger rows remain protected; eligibility changes are audited by origin identity rather than assumed monotonic growth; freshness checks are release-aware and do not make curve-only production dependent on CAPE.

Three non-blocking reservations for the implementation record:

1. **§8 — Not every new test should fail before repair.** The staleness and omitted-eligible-origin tests must expose the existing defect. Legacy replay should already pass. Synthetic-observation and eligibility tests need explicit defective fixtures where appropriate. The acceptance criterion is demonstrated defect detection—not artificially making every assertion fail.

2. **§4.3 — “80% coverage” is nominal, not established.** The 10–90% endpoints contain the central 80% of bootstrap draws; that does not establish 80% repeated-sample coverage with 13 dependent episode blocks. Print **“central 80% bootstrap estimation-sensitivity band; coverage not established.”** The supplementary rule remains diagnostic, with Section 6 unchanged.

3. **§7.1–7.2 — Report coefficients on comparable scales.** Alongside the standardised coefficient, print the raw curve slope \( \beta_{\mathrm{curve}}=w_1/s_{\mathrm{curve}} \), with the curve measured in percentage points, and the raw intercept \( \alpha=w_0-w_1\mu_{\mathrm{curve}}/s_{\mathrm{curve}} \). Otherwise a change in training-window dispersion can be misreported as coefficient dilution. Fixed-input probabilities remain the relevant measure of the recalibration’s operational effect.

This approval authorises the specified repair and reporting protocol—not feature reopening, automatic full-model promotion, or retrospective alteration of published forecasts.

### Gemini 3.8 Flash (Google)

VOTE: APPROVE

### Reservations for the record

1. **Parameter dilution under the 2022–2024 false-alarm quarters (§1.5, §7.1):** Incorporating 2023Q3–2024Q1 adds deep yield-curve inversions followed by no recessionary onset within four quarters. Because the model relies strictly on the curve's static level rather than duration or post-inversion steepening dynamics, this refit mechanically penalizes the slope coefficient. Council members and external users must recognize that this shift is an artifact of functional-form misspecification (unmodeled cycle length and term-structure path), not proof that yield-curve information has fundamentally degraded.

2. **Strict enforcement of tandem interpretation for the oracle-free supplement (§4.5):** Disclosing both variants—including and excluding unannounced in-recession origins—is essential. Omitting unannounced quarters masks the model’s real-time failure mode during rapid downturns, whereas including them penalizes the model for cyclical regime transitions that NBER had not yet codified. Neither metric represents an unvarnished ground truth; isolating or headlining either variant individually in downstream reporting would distort the historical skill assessment.

3. **Preregistration hurdles for verdict migration (§4.3):** Adopting the 10–90% paired-difference bootstrap band beside Section 6 is safe as a purely supplementary diagnostic. However, moving it to primary status in any future release must remain blocked until the empirical Type I error rate of this 80% coverage interval is benchmarked against uninformative, block-permuted synthetic series. Without establishing that the paired band limits false "distinguishable" verdicts to nominal levels under the null, migrating the primary rule risks replacing conservative reporting with uncalibrated signal noise.

### Kimi K3 (Moonshot AI)

VOTE: APPROVE

All three of my Round-4 conditions are now binding text: §3.5 asserts the signed audit identity (n_new = n_old + n_added − n_removed) with exact membership and label agreement; §1.4 makes the seam months a verified measurement stored in meta.json; §2 specifies "unavailable — CAPE stale" with no silent carry-forward. Astra's three amendments are incorporated in substance; Gemini's Type-I criterion and tandem-interpretation clause are in §4.3/§4.5; Claude's override-record and commit-order points are in §1.6/§8. Preregistration is enforced by execution order, not goodwill. Nothing left to block.

Reservations for the record (non-blocking):

1. **§1.4's seam check measures vintage, not validity.** Hand-computing 2023-08/09 CAPE from the archived Yale earnings column reproduces Yale's *preliminary* values; multpl's deviations (−1.25 %, −3.28 %) almost certainly reflect revised earnings and the final S&P print. The stored comparison will show a discrepancy by construction. meta.json must state the expected direction and magnitude in advance, or the number invites post-hoc reading. Materiality is low: the seam touches only S&P-derived and CAPE features; the operational curve-only P is insensitive to it.

2. **The bridge row is one input vector.** §3.4 prints ΔP at current inputs only. At an NBER-triggered refit (§3.2b) the interesting variance sits elsewhere — origins adjacent to the newly dated turning point, where censoring flips. The manifest should print max |ΔP| and max |Δw| across all walk-forward origins between successive calibrations. That is cheap and converts Gemini's regime-transition concern into an auditable number rather than a monitoring exhortation.

3. **multpl is an uncontracted single-operator source.** If it stops, §2/§1.7 degrade gracefully — the full-model line prints "unavailable — CAPE stale" indefinitely — but the README should state that outcome as accepted design, not a defect: the full model is non-operational, and no keyless independent CAPE exists (§1.6 already records this). A future reader must not mistake the line's permanent absence for a pipeline failure.

### Claude Opus 5 (Anthropic — part i sagen)

VOTE: APPROVE

Astra's three amendments are each an improvement on what I drafted, and I record why: the prospective-only calibration column removes the one exception I had written into "historical rows are never edited"; the signed membership audit is correct where "n_obs must grow" was wrong (Kimi's reservation showed the same false-fail at the next dated peak); and the release-aware freshness rule fixes a guard that would have failed on the very reading it was meant to protect.

Reservations for the record, none blocking:

1. **§1.7 release-lag table is now a protocol artefact.** The per-series expected-release rule lives in fetch.py's series table and is therefore under version control — but it is also a set of assumptions about publication calendars that can change (BLS/BEA reschedules, shutdowns). A missing release should fail the stage, as written; it must not be silently "fixed" by loosening the table. Any change to the table is a commit with a stated reason.

2. **§1.4 seam cross-check uses Yale's own preliminary earnings** for 2023-08/09. The check is still worth doing — it bounds the discrepancy — but the record should say the earnings input is itself preliminary, so the cross-check verifies consistency, not truth.

3. **§3.2 next-publication-run execution** means a refit triggered by an NBER announcement lands in a ledger row together with that month's new data. The bridge row separates the two effects at fixed inputs, which is sufficient — but the note column of that row should name the announcement as the trigger, so the row is readable without the manifest.
