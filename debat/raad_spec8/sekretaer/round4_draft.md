# CONSENSUS TEXT — spec 8: a hash-committed memory shadow model (Round 4 draft)

Assembled by the secretary (Claude Opus 5.5, a party) from Rounds 1–3. Where a veto was declared, the text takes the
vetoing side. Nothing here changes P, its band, its verdict, the weights (72c3371d), the scoring key or any ledger row.

## 1. What is authorised

1.1 Exactly one memory shadow model, fitted and logged prospectively, with no operational authority: never in P, the
band, the verdict, a gate, a trigger or the ignition column; never in LOG.md or on the dashboard, including after the
2027 refit, without a new council decision. No launch, retention or change may depend on its fitted values.

1.2 Purpose, stated plainly in the spec: a pre-committed, time-stamped forecast for future cycles that cannot be
reconstructed after the outcome is known. It is not a test with usable power (MDE80 ≈ 30 pp) and **it cannot speak to
the current cycle**: with H = 12 the 2022–24 inversion is already outside its window (curve_min12 = +0.24 at 2026-09),
and it is blind to onsets without a prior inversion (1957, 1960, 1990) and to any lag past 12 months. For this cycle
the record is P, the ledger and the context lines.

## 2. The model (sealed)

2.1 Memory variable: `curve_min12`, the v4 object in `calibrate.build_monthly` — rolling minimum of monthly
GS10 − TB3MS over the last 12 months, ≥ 6 observations. Live value: the last 12 **published** monthly values (no
trailing-daily month); the logged record states the monthly data cutoff, and the shadow's memory may lag live P's
curve by up to one unpublished month.
2.2 Why H = 12: the operative reason is pre-existence (the v4 definition predates this debate), a discretion-limiting
tie-breaker, not validation; v4 once fitted it alone with an unrecorded result. The equality with the four-quarter
label horizon is recorded as a mnemonic only; backward memory and forward horizon are distinct quantities and the
equality identifies nothing. The choice was made knowing E2: H = 12 → +0.24, H = 24 → −0.41, H = 36 → −1.22.
2.3 Form: logit⁻¹(α + β₁·z(curve) + β₂·z(curve_min12)), raw columns standardised on the training rows only (ddof as
the operational fit), intercept unpenalised, λ = 1 exactly as `finalize6.fit_model`. Curve column at the live input =
the operational live curve (trailing month of daily DGS10 − DTB3), as P uses. No reparameterisation, no sign gate;
the fit is logged whatever it shows (expected sign of β₂ negative, recorded as expectation only).
2.4 Fitting: the operational calibration's snapshot (2026-09-19), R (2026-09), universe (1947Q2), labels, 18-month
floor and eligible rows, identity with the operational fit asserted in code (fails loudly). The operational P is
therefore the matched curve-only comparator; no separate control. Refitted only together with the operational
September refit.
2.5 Disclosures in the spec: E1–E4 of the brief; the grand review's diagnosis; the 2026-10-28 backtest; the
collinearity of the two columns (their correlation on the fit rows, printed with the coefficients and scaling at
sealing); the fit sample ends 2024Q1 and contains six zero-labelled inversion-period origins (2022Q4–2024Q1, where
curve ≈ curve_min12) and no post-inversion origin, so those zeros barely identify β₂. No second, cycle-selected fit.

## 3. Storage: hash commitment

3.1 Each ledger row's shadow record — row id (log date), origin, curve_min12 and its monthly cutoff, p_hukommelse,
fit-vintage id, scaling, code commit, snapshot hash, missingness, and a fresh secret random nonce of ≥ 128 bits — is
serialised canonically (sorted keys, fixed float formatting, UTF-8, LF) as one line in a local, git-ignored,
append-only file `skygge_hukommelse.jsonl`.
3.2 The public `hovedbog.jsonl` row carries only `skygge_sha256` (sha256 of that line), written in the same commit as
the ledger row; one line, one hash, no alternates. The nonce prevents recovering the probability by guessing.
3.3 The file is backed up outside the repository and revealed only to an evaluating council (§4); at reveal every line
must hash to its committed value, with completeness checked against the ledger. A row that could not be produced is
logged as missing with a reason; nothing is ever backfilled.

## 4. Evaluation

4.1 No scored rule in this spec. Tracking is unscored. Constraints on any future council: a scored test is sealed
before the onsets it counts and counts ≥ 2 onsets after that sealing; accumulated tracking is never promoted into
confirmatory evidence; quarterly origins only (not monthly rows); pre-2027 origins (incl. Nov–Dec 2026) audit-only;
comparator = operational P from the identical fit vintage; Kimi's stopping rule (sample ends at the quarter of the
second counted onset, labels mature four quarters, one evaluation); stated as underpowered; never an automatic switch.
4.2 At any reveal, descriptive output may include the repo's episode-block bootstrap (cycle blocks, seed 42, 10,000
draws) with no threshold and no significance language, and an onset scorecard (P and p_hukommelse at the last origin
before each counted onset). No new bootstrap procedure.

## 5. Start

From the November 2026 ledger row (log window 10–13 November): spec 8 sealed and pushed, code committed, before the
window. If not ready, the row records the shadow as missing with a reason; no backfill.

## 6. Post hoc

Acceptable: the shadow is instrumentation, not evidence; its definition, storage and start were fixed before any
shadow forecast was computed, and none of them can be changed by what it shows.
