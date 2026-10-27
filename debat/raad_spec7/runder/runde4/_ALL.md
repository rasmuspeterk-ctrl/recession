# ROUND4 — samlet


---

## GPT-6.1 Sol Pro (OpenAI)

VOTE: APPROVE

1. **Part A remains a measurement diagnostic, not a selection procedure.** The BEY proxy does not make a simple-yield bill and a semiannual par 10-year yield fully unit-consistent. Its level dependence warrants the unconditional 2027 review, not an adoption presumption. Rate-bin coefficients must remain descriptive, unscored outputs; they cannot become alternative production fits or retrospective selection criteria. Ten thousand bootstrap draws reduce Monte Carlo noise, not uncertainty from the small number of recession episodes.

2. **The B3 audit measures revision stability, not predictive validity.** For reproducibility, the sealed implementation specification should identify the precise y10 and 3m series, date alignment, and whether those market-rate observations are held fixed when computing revisions of E. Otherwise “revision of E” can conflate term-premium revisions with changes in the other inputs. Passing the 10 bp display-stability bar supplies no evidence that E improves recession forecasts. Keeping historical B1/B2 closed is justified by the seen implementation and redesign opportunities—not by treating −77.88 pp as a clean rejection of the economic hypothesis.

3. **Presentation compliance must survive isolated rendering.** A benchmark table exported or printed without its surrounding dashboard must retain the complete §1.2 sentence, including the power clause. The oracle-free paired interval must be published regardless of its result, ahead of the censored interval, without interpreting bootstrap draw shares as p-values. “Bit-identical replay” should mean unchanged computational P, band, verdict and existing ledger content—not identical presentation bytes.

These decisions are acceptable **despite being post hoc**: the presentation changes correct interpretation, Part A is unconditional and unscored, and B3 starts prospectively. None retrospectively validates a predictive hypothesis or authorizes a production switch.

---

## Gemini 4 Argon (Google)

VOTE: APPROVE

**Reservations for the record (do not block consensus):**

1. **§3.7 (Interim footnote for the 198-origin interval):** The consensus text allows the 198-origin oracle-censored paired loss bootstrap interval to appear temporarily as a footnote marked *"oracle-free interval pending"* until the 219-origin interval is computed. Because the 219-origin per-origin losses already exist in the repository artifacts and require only a few seconds of compute under the pinned `parret_loss_bootstrap` specification (10,000 draws, seed 42, 5th–95th percentiles), this interim state should not actually be deployed. The 219-origin interval should be generated and committed in the initial `[now]` implementation batch so that the oracle-censored interval never appears on the live dashboard without its oracle-free counterpart preceding it.
2. **§1.2 (Remaining yield-basis mismatch):** While Part A’s `BEY(d)` conversion eliminates the level-dependent discount-rate distortion in the 3-month leg (which reached 81 bp at $d = 15\%$), the resulting 91-day simple ACT/365 money-market yield remains algebraically distinct from the semiannual bond-equivalent par yield of the 10-year CMT leg (`GS10`/`DGS10`). When the 2027 refit council reviews Part A on its unconditional agenda, it should evaluate whether full compounding alignment (converting the 3-month leg to a semiannual compounding basis) is warranted alongside the simple BEY proxy.
3. **§3.4 (BEA release-date verification):** Dropping *"later vintage than advance"* in favor of *"first seen by us dd-mm (N days after quarter end)"* is the right immediate fix to avoid unverified vintage claims. Before the September 2027 refit, however, the data ingestion pipeline should record actual BEA release timestamps or vintage identifiers directly from ALFRED/FRED metadata so the monitor can state the exact statistical release (Advance, Second, or Third) as verified fact rather than relying on an internal day-count heuristic.

---

## Claude Fable 5.1 (Anthropic (independent instance))

VOTE: APPROVE

The draft meets both my veto conditions (no outcome-conditioned switch in §1.4; the censored interval never alone under the §1.2 sentence in §3.7) and the compromises I offered in Round 3. Three reservations for the record, none blocking:

**R1 — §3.6 is silent on what happens to the decomposition after the audit.** I accepted removal of C6 from the standing warnings on the condition that the audit starts at the next ledger row (it does, §2.2) and that the question of a numbers-only line returns to the council with the 12th vintage. The draft specifies when a ledger column may open (§2.3) but not whether the context block may then carry E = (y10 − TP) − 3m. It should: the same sign-off that opens the column decides the context line; absent sign-off, the block stays as §3.6 writes it. Otherwise "removed until the audit" quietly becomes "removed".

**R2 — §1.3(4), the rate-bin table.** The ≥ 12 % bin holds essentially 1980–81 and the 8–12 % bin 1973 plus fragments; per-bin fitted α and β there are near-unidentified and will have standard errors wider than the coefficients. The sealed spec should label the bin fits "descriptive, no inference", or the 2027 council will be handed a bin coefficient that looks like evidence of regime dependence. The origin-level paired loss by bin is the informative part; the fits are decoration.

**R3 — §3.4 (C4).** I argued for keeping the quarter-end + 42 days inference as a labelled heuristic; the majority drops it. I accept that, but note the residual defect: a reader of the GDP monitor still cannot tell whether our first-seen print predates or postdates BEA's second estimate, and "N days after quarter end" only helps a reader who knows BEA's calendar. The cheap fix — scraping the BEA release calendar once a quarter — should go on the refit's housekeeping list so the inference can be restored verified rather than guessed.

On the post hoc question, I concur with §§1.6, 2.4 and 3.8 as written: nothing ratified here selects a configuration, scores a hypothesis, or moves a number that decides anything.

---

## Grok 4.7 (xAI)

VOTE: APPROVE

Post hoc: acceptable on §§1.6, 2.4 and 3.8. Nothing here selects a weight, moves P, or reopens a seen test.

Reservations, not blocks:

1. Spec 7A’s rate-bin α, β (1.3(4)) are diagnostics, not a weight proposal. E1 (gap 0.55–0.81 pp at 12–15 %, 4 of 12 onsets in the high-rate bins) is exactly the pattern that tempts a regime-dependent β. Adopting one is a new model, needs its own sealed spec and replay under §1.3, and is not authorized by an unscored convention check. The 2027 agenda item decides the 3m convention only.

2. The 10 bp bar on E (2.3) is administrative bookkeeping, not evidence. At the frozen β = −1.2948, 10 bp of E is about 1.3 pp of shadow probability — large relative to today’s paired supplement [−6.5; −0.4]. A pass plus council sign-off may open a bare column; it may not be cited as validation, and ACM stays out of any live line. The step-4 result (−77.88 pp, 0 % positive folds) remains seen and non-isolating; B1/B2 stay deleted.

3. The pre-2026-09-10 context line may keep its dated Kim–Wright split only with the new disclaimer and with no E, share, or Rosenberg–Maurer sentence, and not in the same visual unit as P or the verdict. Claude’s |Δ_OF| < 2 pp prior stays in spec §0, never beside the result. A substituted probability — 17.9 % or any other — does not ship.

---

## Kimi K3.1 Pro (Moonshot AI)

VOTE: APPROVE

Reservations for the record:

1. **Pin the 7B audit arithmetic before sealing.** Specify the \(y10\) and 3m series, units, same-date alignment and missing-day rules. Define the 10 bp criterion as the maximum over every date in vintage 1’s trailing 24 months and every revision comparison through vintage 12. It remains exclusively a display-stability criterion.

2. **Part A cannot establish a regime-specific “correction.”** Rate-bin estimates—especially for TB3MS ≥ 12%—will rest on few episodes and may have unstable \(\alpha,\beta\). Likewise, 10,000 bootstrap draws improve Monte Carlo precision, not the information supplied by nine cycle blocks. The bins and paired replay are descriptive inputs to the unconditional 2027 decision, not evidence that BEY is superior.

3. **Neither presentation interval is a significance test.** Printing the 219-origin oracle-free interval first corrects the §1.2 emphasis; it does not cure the limited episode count. The 198-origin result’s 8.9% of draws ≤ 0 remains a draw share. C1’s post hoc 5 bp cutoff and B3’s 10 bp bar must never migrate into \(P\), verdicts, triggers or ledger scoring.

---

## DeepSeek V4 Pro (DeepSeek)

VOTE: APPROVE

Reservations for the record:

1. **D4 audit bar (10 bp) remains arbitrary.** I accept it as a display-stability gate, not validity evidence, but the council should state in the spec that the 10 bp threshold was chosen without empirical revision data and may be recalibrated by a later council before any column opens. The bar's defensibility rests entirely on the "administrative, not evidentiary" label — that label must survive contact with the dashboard.

2. **D6 no-number position is weaker than I argued.** I still believe printing ≈17.9% once with the explanation is more protective than silence, but the screenshot-risk argument (Grok, Opus) is real and the anti-substitution sentence without the figure is sufficient. I record my disagreement on the didactic point only.

3. **D3 operator choice (convert-after-averaging primary) is the right call for consistency, but the spec must not let the robustness line (mean-of-converted-daily) drift into any user-facing comparison.** The Jensen bound is pinned; the operator difference is bookkeeping. If the 2027 council later cites the robustness line as evidence for a convention switch, that is a §1.3 breach and I will oppose it.

---

## Claude (Opus 5.5) (Anthropic — interested party, co-builder and secretary)

VOTE: APPROVE

Reservations for the record (they do not block):
1. I withdrew my own switch rule (Round 3). I still think the 2027 council should weigh unit consistency as a
   measurement argument in its own right, not only through the replay's skill figure; §1.4 leaves room for that.
2. Removing C6 removes the one sentence that tells a curve-only reader the current curve is almost all term
   premium. I accept the firewall's reasons; the context-block line and the README methods section must be easy
   to find.
3. The 10 bp bar in §2.3 is administrative and arbitrary in level; its virtue is that it was pinned before any
   revision was computed.
