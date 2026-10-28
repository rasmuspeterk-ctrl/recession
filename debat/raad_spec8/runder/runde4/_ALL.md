# ROUND4 — samlet


---

## GPT-6.1 Sol Pro (OpenAI)

VOTE: APPROVE

The draft satisfies my requirements: operational P remains untouched; one fixed shadow specification; public hash commitments rather than published shadow probabilities; no second cutoff fit; and no retrospective conversion of tracking into confirmatory evidence.

The post-hoc choices in Q1–Q6 are acceptable **as instrumentation, not validation**. Pre-existing `curve_min12` limits discretion; it does not establish that twelve months is economically optimal.

Three non-blocking reservations for the record:

1. **“Blind” describes the memory feature, not the complete forecast.** The two-feature model can assign recession risk without a prior inversion through its current-curve term and intercept. Likewise, it cannot attribute current risk to the expired 2022–24 inversion through `curve_min12`, but its prospective forecasts can still be recorded during this cycle. “Cannot speak to the current cycle” is a restriction on evidentiary interpretation, not a mathematical property of the model.

2. **MDE80 ≈ 30 percentage points belongs to the historical evaluation design.** It is not a power calculation for an unknown future sample. Two post-sealing onsets establish minimum eligibility, not adequate power. The draft correctly authorises neither a significance threshold nor an inference from failure to outperform.

3. **The hash provides integrity, not complete forecast secrecy.** A secret nonce prevents recovering the committed record through probability guessing. It does not prevent independently calculating the shadow probability if coefficients, scaling, code and inputs are public. I accept the distribution compromise as prohibiting publication or rendering of the shadow probability—not as guaranteeing that nobody can reconstruct it. Private archive access and backups must preserve the committed bytes.

---

## Gemini 4 Argon (Google)

VOTE: APPROVE

Reservations for the record:

1. **Unbackupable single point of failure (`skygge_hukommelse.jsonl`).** While §3.1–3.3 solves the tension between external cryptographic auditability and Grok/Sol's distribution veto, a git-ignored local file over a multi-decade evaluation horizon is operationally fragile. If the external backup fails or loses a single line, the hash-continuity check at reveal (§3.3) will invalidate or truncate the prospective series. The implementation should automate an encrypted off-site push on every monthly run.
2. **Deferred scoring criteria (§4.1).** By deferring a numerical decision boundary to a future council while requiring that council to seal its rule *before* counting two subsequent onsets, any formal scored comparison is pushed at least four recession cycles into the future unless a future council convenes early in 2027. The descriptive outputs pinned in §4.2 (paired log-loss via the `ablation3` episode-block bootstrap, seed 42, 10,000 draws, plus the onset scorecard) will carry the full weight of evaluating the first two post-2026 cycles.
3. **Asymmetric live input timing (§2.1, §2.3).** Feeding the live trailing-daily spread into $z(\text{curve})$ while restricting $z(\text{curve\_min12})$ to published calendar months means that during a rapid mid-month inversion, live $\text{curve}$ can temporarily drop below $\text{curve\_min12}$—a geometric state ($C_t < M_t$) impossible in the training sample ($1947\text{Q2}–2024\text{Q1}$). This is the unavoidable price of adhering strictly to the v4 monthly definition without creating a hybrid feature, and should be borne in mind when interpreting live shadow readings during sharp rate moves.

---

## Claude Fable 5.1 (Anthropic (independent instance))

VOTE: APPROVE

The text carries everything I conditioned on: canonical serialisation, same-commit hash, one line per row, episode-block bootstrap named as the only procedure, Kimi's stopping rule, ≥ 2 post-sealing onsets, matched comparator, 2024Q1 disclosure, November start. Three reservations for the record.

**R1 — the hash timestamps; it does not hide.** §2.5 prints β₁, β₂ and the scaling at sealing, and `curve_min12` is reconstructible from FRED forever. Anyone with the spec and the live curve can recompute `p_hukommelse` to four decimals; the 128-bit nonce only stops guessing the line, not computing its content. That is acceptable — the commitment's job is to prove what was forecast when, and the distribution veto concerns a rendered number, not a recomputable one — but §3.2 should not imply secrecy. Suggested wording: "the hash proves the record's existence and content at commit time; the probability is in principle recomputable from the sealed coefficients." Rasmus should decide knowingly whether the coefficient vector goes in the spec or in the private file; I prefer the spec (auditability over concealment).

**R2 — the live row can violate the training invariant.** In the fit, curve ≥ curve_min12 by construction. On the live row (§2.3 + §2.1), curve is a trailing-daily month and min12 is over published months, so curve can fall *below* min12 in a fast steepening-reversal. The model then sees a feature configuration it never trained on. Not fatal; log a flag `min12_lt_curve` on the shadow line so a future council can see how often it happened.

**R3 — one refit vintage per evaluation, stated.** §2.4 refits every September; §4.1 pairs each row with its own vintage's P. Fine for paired log-loss, but the tracking record is then a sequence of models, not one. The spec should say that any onset scorecard labels each row's fit-vintage id, so a 2032 council cannot read a 2029-vintage slope as the sealed-2026 slope.

None blocks. Approve.

---

## Grok 4.7 (xAI)

VOTE: APPROVE

Reservations, for the record only:

1. The object does not implement the diagnosis that opened this item. E1’s longest end-to-onset lag is 9 months; today is 22. At 2026-09, curve_min12 = +0.24, so H = 12 is already blind to the 2022–24 inversion (−1.57 pp, 25 months) and to 1957, 1960 and 1990. §1.2 states that. Do not later narrate a near-P shadow path as evidence about “trigger pulled vs gun put away.”

2. β₂ is barely identified. Fit ends 2024Q1 and holds six zero-labelled inversion origins (2022Q4–2024Q1) where curve ≈ curve_min12, and no post-inversion origin. MDE80 ≈ 30 pp on 8 walk-forward onsets; two later onsets will not separate this from curve-only. Print coefficients and the feature correlation at sealing; do not treat either as a slope.

3. `skygge_hukommelse.jsonl` is a single point of failure. A lost file leaves `skygge_sha256` that cannot be opened. “Backed up” is not a second hash. If the line is missing at reveal, the row stays missing — no reconstruction from FRED, and no substituted public `p_hukommelse`.

---

## Kimi K3.1 Pro (Moonshot AI)

VOTE: APPROVE

The draft satisfies my conditions: the exact v4 `curve_min12` object, operational P as the matched comparator, hash-only public storage, no scored threshold or second cutoff fit, and a November 2026 start without backfill.

Reservations for the record:

1. **The post-hoc exemption is narrow.** E2 was known when H was selected; v4 pre-existence limits discretion but supplies zero validation. Neither the sealed fit nor early shadow rows may be cited as evidence about memory, the current 22-month lag, or this cycle’s outcome.

2. **β₂ is weakly identified.** The sample ends 2024Q1, contains six zero-labelled inversion-period origins with curve ≈ `curve_min12`, and contains no post-inversion origins. Coefficients, scaling and collinearity are disclosures, not economically interpretable memory estimates. An unstable or wrongly signed β₂ must not trigger respecification, suppression or abandonment based on fitted values.

3. **Commitment discipline is essential.** The nonce and private archive must remain secret and backed up; every public hash must share its ledger row’s commit. At reveal, auditors must check byte-level hashes and completeness against every ledger row. Lost private records are permanently unauditable, not reconstructible as committed forecasts. November–December 2026 remains audit-only, and any later two-onset evaluation remains severely underpowered despite the fixed stopping rule.

---

## DeepSeek V4 Pro (DeepSeek)

VOTE: APPROVE

Reservations for the record:

1. The matched-comparator claim rests entirely on the code asserting identical snapshot/R/eligibility. I want that identity test executed before the November row, not merely stated. If it ever fails, the shadow row must be logged missing with a reason, and no backfill may repair it.

2. Canonical serialization must be frozen and tested — key sorting, fixed float formatting, nonce generation, line reconstruction — before sealing. An unhashable first row cannot be retroactively committed.

3. The β₂ identification disclosure (six zero-labelled inversion rows, curve ≈ curve_min12, no post-inversion origins) should print alongside the fitted coefficients at every September refit, not only at sealing. Otherwise a later reader will over-read the shadow.

---

## Claude (Opus 5.5) (Anthropic — interested party, co-builder and secretary)

VOTE: APPROVE

Reservations for the record (they do not block):
1. The shadow answers Rasmus's question only for future cycles. For this one, H = 12 is silent by construction; the
   spec says so and the reply to Rasmus must say so too.
2. The private file is a single point of failure for the whole record; the backup in §3.3 is not optional.
3. I moved twice on the scored rule (no bar → screen → no bar). The final text is right: a rule that two onsets cannot
   power should be set by a council that can see how many post-sealing origins exist, sealed before the onsets it uses.
