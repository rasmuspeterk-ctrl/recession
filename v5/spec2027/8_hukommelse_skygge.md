# Forseglet spec 8 — en hash-forpligtet hukommelses-skyggemodel ved siden af P (RAADETS_SPEC8)

**Forseglet 2026-10-29.** Teksten er committet og pushet, FOER koden der bruger den skrives (RAADETS_2027 §12
trin 3). Koden laaser filens sha256 (LF-normaliseret) og stopper hoejlydt, hvis filen er aendret efter
forseglingen. En aendring kraever en raadsbeslutning. Er spec og kode uenige, gaelder spec'en (RAADETS_2027 §3.4).

Ratificeret tekst (ordret, RAADETS_SPEC8.md, 7/7 i runde 4 den 2026-10-29):

> ## 1. What is authorised
>
> 1.1 Exactly one memory shadow model, fitted and logged prospectively, with no operational authority: never in P, the
> band, the verdict, a gate, a trigger or the ignition column; never in LOG.md or on the dashboard, including after the
> 2027 refit, without a new council decision. No launch, retention or change may depend on its fitted values.
>
> 1.2 Purpose, stated plainly in the spec: a pre-committed, time-stamped forecast for future cycles that cannot be
> reconstructed after the outcome is known. It is not a test with usable power (MDE80 ≈ 30 pp) and **it cannot speak to
> the current cycle**: with H = 12 the 2022–24 inversion is already outside its window (curve_min12 = +0.24 at 2026-09),
> and it is blind to onsets without a prior inversion (1957, 1960, 1990) and to any lag past 12 months. For this cycle
> the record is P, the ledger and the context lines.
>
> ## 2. The model (sealed)
>
> 2.1 Memory variable: `curve_min12`, the v4 object in `calibrate.build_monthly` — rolling minimum of monthly
> GS10 − TB3MS over the last 12 months, ≥ 6 observations. Live value: the last 12 **published** monthly values (no
> trailing-daily month); the logged record states the monthly data cutoff, and the shadow's memory may lag live P's
> curve by up to one unpublished month.
> 2.2 Why H = 12: the operative reason is pre-existence (the v4 definition predates this debate), a discretion-limiting
> tie-breaker, not validation; v4 once fitted it alone with an unrecorded result. The equality with the four-quarter
> label horizon is recorded as a mnemonic only; backward memory and forward horizon are distinct quantities and the
> equality identifies nothing. The choice was made knowing E2: H = 12 → +0.24, H = 24 → −0.41, H = 36 → −1.22.
> 2.3 Form: logit⁻¹(α + β₁·z(curve) + β₂·z(curve_min12)), raw columns standardised on the training rows only (ddof as
> the operational fit), intercept unpenalised, λ = 1 exactly as `finalize6.fit_model`. Curve column at the live input =
> the operational live curve (trailing month of daily DGS10 − DTB3), as P uses. No reparameterisation, no sign gate;
> the fit is logged whatever it shows (expected sign of β₂ negative, recorded as expectation only).
> 2.4 Fitting: the operational calibration's snapshot (2026-09-19), R (2026-09), universe (1947Q2), labels, 18-month
> floor and eligible rows, identity with the operational fit asserted in code (fails loudly). The operational P is
> therefore the matched curve-only comparator; no separate control. Refitted only together with the operational
> September refit.
> 2.5 Disclosures in the spec: E1–E4 of the brief; the grand review's diagnosis; the 2026-10-28 backtest; the
> collinearity of the two columns (their correlation on the fit rows, printed with the coefficients and scaling at
> sealing); the fit sample ends 2024Q1 and contains six zero-labelled inversion-period origins (2022Q4–2024Q1, where
> curve ≈ curve_min12) and no post-inversion origin, so those zeros barely identify β₂. No second, cycle-selected fit.
>
> ## 3. Storage: hash commitment
>
> 3.1 Each ledger row's shadow record — row id (log date), origin, curve_min12 and its monthly cutoff, p_hukommelse,
> fit-vintage id, scaling, code commit, snapshot hash, missingness, and a fresh secret random nonce of ≥ 128 bits — is
> serialised canonically (sorted keys, fixed float formatting, UTF-8, LF) as one line in a local, git-ignored,
> append-only file `skygge_hukommelse.jsonl`.
> 3.2 The public `hovedbog.jsonl` row carries only `skygge_sha256` (sha256 of that line), written in the same commit as
> the ledger row; one line, one hash, no alternates. The nonce prevents recovering the probability by guessing.
> 3.3 The file is backed up outside the repository and revealed only to an evaluating council (§4); at reveal every line
> must hash to its committed value, with completeness checked against the ledger. A row that could not be produced is
> logged as missing with a reason; nothing is ever backfilled.
>
> ## 4. Evaluation
>
> 4.1 No scored rule in this spec. Tracking is unscored. Constraints on any future council: a scored test is sealed
> before the onsets it counts and counts ≥ 2 onsets after that sealing; accumulated tracking is never promoted into
> confirmatory evidence; quarterly origins only (not monthly rows); pre-2027 origins (incl. Nov–Dec 2026) audit-only;
> comparator = operational P from the identical fit vintage; Kimi's stopping rule (sample ends at the quarter of the
> second counted onset, labels mature four quarters, one evaluation); stated as underpowered; never an automatic switch.
> 4.2 At any reveal, descriptive output may include the repo's episode-block bootstrap (cycle blocks, seed 42, 10,000
> draws) with no threshold and no significance language, and an onset scorecard (P and p_hukommelse at the last origin
> before each counted onset). No new bootstrap procedure.
>
> ## 5. Start
>
> From the November 2026 ledger row (log window 10–13 November): spec 8 sealed and pushed, code committed, before the
> window. If not ready, the row records the shadow as missing with a reason; no backfill.
>
> ## 6. Post hoc
>
> Acceptable: the shadow is instrumentation, not evidence; its definition, storage and start were fixed before any
> shadow forecast was computed, and none of them can be changed by what it shows.

---

## 0. Hvad der var kendt ved forseglingen (§2.5)

- **E1–E4 fra briefen**, ordret:

> **E1 — inversion episodes in monthly GS10 − TB3MS (≥ 3 consecutive negative months) and the next onset:**
>
> | Inversion | Months | Depth | Next onset (first USREC month) | Months from inversion end to onset |
> |---|---|---|---|---|
> | 1966-09..1967-01 | 5 | −0.34 | none | — (no recession) |
> | 1969-11..1970-01 | 3 | −0.17 | 1970-01 | 0 |
> | 1973-06..1974-06 | 13 | −1.27 | 1973-12 | onset during inversion |
> | 1978-12..1980-04 | 17 | −2.45 | 1980-02 | onset during inversion |
> | 1980-11..1981-08 | 10 | −2.65 | 1981-08 | 0 |
> | 2000-08..2000-12 | 5 | −0.53 | 2001-04 | 4 |
> | 2006-08..2007-04 | 9 | −0.38 | 2008-01 | 9 |
> | 2019-06..2019-09 | 4 | −0.32 | 2020-03 | 6 |
> | 2022-11..2024-11 | 25 | −1.57 | none so far | 22 months and counting |
>
> (1990-08 had no ≥ 3-month monthly inversion; 1989 was brief and shallow. 1953–1965 had no ≥ 3-month inversion
> either: the 1957 and 1960 onsets came without one. Pre-1953 the 10y leg is Shiller's long rate.) The longest historical lag from the end of
> an inversion to an onset is 9 months. Today it is 22 months. The 2022–24 inversion was the longest on record and
> the deepest since 1981.
>
> **E2 — the memory value today depends almost entirely on the horizon** (minimum of monthly GS10 − TB3MS over the
> last H months, latest month 2026-09): H = 12 → +0.24 (no inversion in the window); H = 24 → −0.41 (2024-10);
> H = 36 → −1.22 (2023-12). Any horizon chosen now is chosen knowing this.
>
> **E3 — prior work.** `calibrate.build_monthly` has computed `curve_min12` (rolling 12-month minimum, min 6
> observations) since v4; v4's model grid included "1b: curve 12m-min" as a stand-alone model. Its result is not
> recorded in the repository and it was not chosen. No memory variable has been tested in v5.
>
> **E4 — power.** 12 onsets in the fit, 8 in the walk-forward; MDE80 for a paired skill difference ≈ 30 pp. No
> historical test can distinguish a memory model from curve-only; any historical figure is in-sample to everything
> above.

- **Grand reviewets diagnose** (august 2026, citeret i briefen): *"It is reading the trigger being pulled as the
  gun being put away."*
- **Backtesten 2026-10-28** (oracle-fri walk-forward, curve-only, de publicerede tal reproduceret): P ved sidste
  origin foer hver onset og hoejeste P i optakten.

  | Onset | Hoejeste P | P ved sidste origin foer onset |
  |---|---|---|
  | 1970 | 34,7 % | 34,7 % |
  | 1973 | 66,8 % | 66,8 % |
  | 1980 | 88,1 % | 88,1 % |
  | 1981 | 96,8 % | 80,5 % |
  | 1990 | 46,8 % | 28,5 % (kurve +0,75) |
  | 2001 | 73,4 % | 35,7 % (kurve +0,47) |
  | 2008 | 70,1 % | 16,7 % (kurve +1,10) |
  | 2020 | 61,9 % | 40,9 % (kurve +0,32) |

  Ved 30 % var alle otte flaget; rene fejlalarmer 1967–68, 1995, 1997–98 og 2022–24 (top 93,8 %).
- **IKKE beregnet:** nogen skygge-P — hverken in-sample, i en walk-forward eller ved noget live-input. Der er
  ingen historisk sammenligning af skyggemodellen med curve-only, og der laves ingen (§1.2, §4.1, E4).

## 1. Fittet ved forseglingen (§2.3–2.5)

Fittet med den eksisterende kode (`ablation2_nber.build_dataset` med features `["curve", "curve_min12"]` og
`finalize6.fit_model`, λ = 1) paa kalibreringens snapshot **2026-09-19**, R **2026-09**,
manifest **72c3371d**.

- **Identitet (asserteret):** de berettigede origins er identiske med manifestets 267 origins;
  curve-only-fittet paa samme rygrad genskaber manifestets w, mu og sd eksakt.
- n_obs 267, n_pos 48, basisrate 0,1798, fittet slutter 2024Q1,
  universet 1947Q2–2026Q1.

| | konstant | curve | curve_min12 |
|---|---|---|---|
| skalering mu (pp) | | +1,3733 | +0,9362 |
| skalering sd (pp, ddof 1) | | +1,1495 | +1,0604 |
| w (standardiseret) | -2,0932 | -0,9111 | -0,6883 |
| raa koefficient (pr. pp) | -0,3970 | -0,7926 | -0,6491 |

- **Kollinearitet:** korrelationen mellem curve og curve_min12 paa de 267 fit-raekker er
  **+0,8595**; curve_min12 ligger under kurven i 71,9 % af raekkerne. β₂ er derfor daarligt bestemt
  og maa ikke laeses som en effekt.
- **De seks nul-origins i inversionen** (alle label 0; ingen post-inversions-origin i fittet):

  | Origin | curve | curve_min12 |
  |---|---|---|
  | 2022Q4 | -0,63 | -0,63 |
  | 2023Q1 | -1,03 | -1,03 |
  | 2023Q2 | -1,41 | -1,57 |
  | 2023Q3 | -0,94 | -1,57 |
  | 2023Q4 | -1,22 | -1,57 |
  | 2024Q1 | -1,03 | -1,57 |

  curve ≈ curve_min12 holder 2022Q4–2023Q1; fra 2023Q2 ligger curve_min12 (-1,57) 0,2–0,6pp under
  kurven. Ingen af de seks er efter inversionens afslutning, saa de identificerer naeppe β₂ for den situation,
  modellen skal sige noget om.
- β₂'s fortegn er negativt, som forventet; forventningen var registreret foer fittet (§2.3) og er ikke et
  kriterium.

## 2. Implementering (bindende for koden)

- **Hvor:** `v5/skygge.py`. Fittet skrives een gang pr. operationel kalibrering med `python skygge.py --fit` til
  `v5/kalibreringer/skygge_<manifest>.json` (offentlig: koefficienterne er offentliggjort efter §2.5). Filen
  overskrives aldrig; en ny kalibrering faar sin egen fil ved september-refitten. Identiteten asserteres hver gang.
- **Live curve_min12 (§2.1):** v4-funktionen `calibrate.build_monthly` paa det loggede snapshots maanedspanel, med
  samme rygrad og samme forlaengelse som curve-only, aflaest ved den seneste maaned med en kurve (cutoff = seneste
  maaned med publiceret GS10 og TB3MS). Ingen trailing-daglig maaned.
- **Kurven i linjen (§2.3):** den operationelle live-kurve (trailing maaned af daglige DGS10 − DTB3), som P bruger.
  p_hukommelse beregnes af de vaerdier, der staar i linjen (kurve og curve_min12 med 4 decimaler), og fit-filens
  mu, sd og w.
- **Linjen (§3.1):** `format`, `raekke` (logdato), `origin` (maaneden foer logningsmaaneden, noeglens regel),
  `vindue`, `kurve`, `curve_min12`, `curve_min12_cutoff`, `curve_min12_vindue`, `p_hukommelse`, `fit` (fit-id),
  `manifest`, `skalering` (mu og sd), `kode` (commit), `snapshot`, `snapshot_sha256`, `mangler` (antal
  observationer i vinduet og maaneder uden kurve) og `nonce` (256 bit fra `secrets`).
- **Kanonisk serialisering:** alle decimaltal er strenge med fast antal decimaler (sandsynlighed 6, kurver og
  koefficienter 4); JSON med sorterede noegler, separatorerne `,` og `:` uden mellemrum, UTF-8 uden escapes.
  Linjen afsluttes med LF i filen; `skygge_sha256` er sha256 af linjens UTF-8-bytes uden LF.
- **Raekkefoelge ved `motor.py --log`:** LOG.md-raekken skrives; linjen tilfoejes `skygge_hukommelse.jsonl`
  (repo-roden, git-ignoreret, append-only, fsync) og backup-filen uden for repoet (mappen i `MOTOR_SKYGGE_BACKUP`,
  ellers `MOTOR-skygge-backup` i brugerens OneDrive eller hjemmemappe); hovedbog.jsonl-recorden faar
  `skygge_sha256`. Det gaelder hver raekke logget 2026-11-01 eller senere (§5). Kan linjen ikke laves eller
  skrives, faar recorden `skygge_sha256: null` og `skygge_mangler` med grunden. Motor printer aldrig p_hukommelse.
- **Verifikation (§3.3):** `python skygge.py --verificer` tjekker, at hver hash i hovedbog.jsonl har en linje i den
  private fil og i backuppen, og at hver linje hasher til sin vaerdi. Den viser antal og raekke-id'er, aldrig tal.
