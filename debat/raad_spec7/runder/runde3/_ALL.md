# ROUND3 — samlet


---

## GPT-6.1 Sol Pro (OpenAI)

**Correction:** I withdraw my C7 attribution objection. The cited artifact assigns 27.05% to curve-only and 23.16% to F5; C7’s attribution was correct. My remaining objection concerns standalone censored skill reporting. The matrix otherwise represents my positions adequately.

### D1 — Part A decision rule
**Final:** No automatic switch and no outcome-triggered agenda requirement. Opus’s “switch unless significantly worse” mistakes failure to detect harm for evidence of acceptability; it is not a non-inferiority test.  
**Compromise:** Schedule an unconditional council review after publication. **VETO** the proposed automatic switch; a separately mandated adoption spec with a justified non-inferiority margin and adequate uncertainty analysis could change my position.

### D2 — Part A bootstrap
**Final:** Prefer 10,000 draws, seed 42, 5th–95th percentiles, matching the verified §4.4 procedure. More draws reduce simulation noise, not the uncertainty from few episodes.  
**Compromise:** Accept 1,000 draws and 10th–90th percentiles if explicitly labelled an **80% interval**, with the block construction pinned. No veto.

### D3 — Aggregation operator
**Final:** Convert daily DTB3 before averaging; apply the conversion directly to monthly TB3MS and disclose the operator difference.  
**Compromise:** Accept Kimi’s convert-after-averaging approach if mean-of-daily conversion is reported as the fixed robustness check. The quantified Jensen effect is too small to block consensus.

### D4 — B3 revision audit
**Final:** Twelve hashed, consecutive monthly full-history vintages are necessary; a 10 bp revision threshold does not establish predictive validity. Prefer one pinned primary series, KW, with ACM confined to a separately dated methods comparison.  
**Compromise:** Accept a strictly defined 10 bp **display-stability gate**, provided the spec states its horizon and reference vintage and explicitly disclaims predictive validation. No veto.

### D5 — C6 now
**Final:** Remove the standing warning until the audit; retain neutral methods documentation.  
**Compromise:** Accept a numbers-only line in a separate context/methods panel now: “Kim–Wright term-premium estimate: 0.99 pp, 2026-10-16; model-dependent, revisable, not an input.” No predictive claim, share, or comparison across unmatched dates. No veto on this placement compromise.

### D6 — Illegal substitution figure
**Final:** Do not publish the approximately 17.9% substitution result: it is neither operational P nor a refitted sensitivity.  
**Compromise:** Explain the prohibition without the number; retain mechanical calculations privately. **VETO** dashboard publication. A separately sealed, correctly refitted diagnostic would change the evidentiary status—not validate this substitution.

### D7 — C2
**Final:** Each independently readable skill statement must satisfy §1.2, including the power clause.  
**Compromise:** Put the complete compliant sentence immediately above the table and use a row cross-reference, without repeating a standalone +27.05%. **VETO** retaining the committed incomplete note; compliant integrated rendering resolves this.

### D8 — C4
**Final:** “First seen by us” is verified metadata; quarter-end +42 days cannot establish BEA vintage identity.  
**Compromise:** Keep that timing only as an explicitly unverified monitoring heuristic, not as grounds for “later vintage than advance.” Actual BEA release-calendar/vintage matching would justify that label.

### D9 — C7
**Final:** Accept “curve-only minus F5 = +3.89 pp, oracle-censored full path.” The censored interval may follow the compliant skill sentence.  
**Compromise:** Compute and print the oracle-free interval first, using §4.4’s verified procedure and a spec committed before code. Publish regardless of result; no p-value interpretation.

### D10 — Dashboard prose
**Final:** Prefer “Primary band rule: not distinguishable,” with the paired supplement explicitly non-deciding.  
**Compromise:** Accept the unchanged verdict plus an adjacent explanatory sentence or tooltip. No veto.

These presentation corrections and unconditional diagnostics are acceptable **despite being post hoc**; they do not retrospectively validate predictive hypotheses or select production.

---

## Gemini 4 Argon (Google)

The Secretary’s framing of my Round 2 positions is accurate. Here are my final positions, compromises, and veto lines on the ten open disputes.

**D1 — Part A decision rule.**
*   **Position:** Option (a) — no pre-committed switch and no outcome-based convening trigger; Part A is an unscored diagnostic, and the 2027 council decides with the full replay in hand. Claude’s $\Delta_{\text{OF}} \ge -1.96 \cdot \text{SD}_{\text{block}}$ rule is just a wider version of the pre-committed switch I withdrew in Round 2, and DeepSeek’s $2\text{ pp}$ trigger is an arbitrary filter.
*   **Compromise:** We may state in the spec that the 2027 council will review Part A as a routine agenda item regardless of the outcome, with no numerical trigger or pre-committed presumption.
*   **VETO:** I will **VETO** any pre-committed switch rule (Claude’s $-1.96 \cdot \text{SD}_{\text{block}}$) or outcome-gated trigger (DeepSeek’s $2\text{ pp}$). *Evidence to change my mind:* A formal proof that a pre-committed switch without inspecting calibration shifts across rate regimes satisfies RAADETS_2027 §1.3.

**D2 — Part A bootstrap.**
*   **Position:** Adopt Sol’s **10,000 draws, seed 42, 5th–95th percentiles** to match `v5/diagnostik.py` line 318 (`parret_loss_bootstrap`).
*   **Compromise:** Print 10,000 draws (5–95%) as primary to match 4.4, and log the 1,000-draw (10–90%) interval in `diagnostik.json` for backwards comparability with `frekvensgate.py`.

**D3 — Aggregation operator.**
*   **Position:** Option (a) — convert daily `DTB3` first, then average for the live leg; apply `BEY(TB3MS)` for monthly history and report the empirical 1954–2026 convexity gap ($\le 0.003\text{ pp}$).
*   **Compromise:** Also print Kimi’s convert-after-averaging live number in `diagnostik.json` as a secondary check.

**D4 — B3 revision audit.**
*   **Position:** Option (a) — require $\max |\text{revision of } E| < 10\text{ bp}$ over the trailing 24 months across 12 hashed monthly vintages before opening an unscored ledger column, and print both KW (`THREEFYTP10`) and ACM (`ACMTP10`) with their dates in the context/audit notes.
*   **Compromise:** If Sol objects to $10\text{ bp}$ as an automatic pass/fail gate, record $10\text{ bp}$ as a diagnostic benchmark and require explicit council sign-off after the 12th vintage before any ledger column opens; for live tracking, use daily KW as the primary series and cite monthly ACM with its lag date in parentheses.

**D5 — The C6 line now.**
*   **Position:** Option (b) — keep a stripped, numbers-only context line now using Fable’s R1 text (dated KW and ACM numbers, *"model-dependent, revised, not inputs"*, plus the factual step-4 note).
*   **Compromise:** To bridge with Sol and Kimi, remove C6 from the top "standing warnings" box alongside $P$ and place Fable’s neutral text in the lower context/methodology section until the 12-month audit completes.

**D6 — C5’s illegal figure.**
*   **Position:** Side with Grok — state that substituting CMT or BEY into the frozen weights is invalid, without printing the $17.9\%$ figure.
*   **Compromise:** I can live with stating *"moves the raw logit output by ~3 pp (not a valid P)"* without printing a standalone percentage that could be screenshotted.

**D7 — C2.**
*   **Position:** Print the full §1.2 sentence in the benchmark row.
*   **Compromise:** Claude’s short note in the table row (all three figures in §1.2 order: $+20.37\%$ [219], $+27.05\%$ [198], $+18.32\%$ [198]) is acceptable **provided** the verbatim §1.2 sentence with the power clause appears immediately above the table.

**D8 — C4.**
*   **Position:** Keep the quarter-end + 42 days rule, explicitly labelled *"heuristic; BEA vintage not verified"*.
*   **Compromise:** Print only the exact factual string *"first seen by us dd-mm (N days after quarter-end)"* and drop the words *"later vintage than advance"* until BEA release dates are scraped.

**D9 — C7.**
*   **Position:** Change the gate line to *"curve-only minus F5 = +3.89 pp, oracle-censored full path"*, and compute and print the 219-origin oracle-free paired bootstrap interval (10,000 draws, seed 42, 5–95%) **ahead** of the 198-origin oracle-censored interval.
*   **Compromise:** None on ordering.
*   **VETO:** I will **VETO** printing the 198-origin oracle-censored bootstrap interval beneath the §1.2 sentence without the 219-origin oracle-free interval printed first. *Evidence to change my mind:* Proof that attaching uncertainty bounds exclusively to the censored figure does not violate §1.2’s anti-cherry-picking mandate.

**D10 — Q5 dashboard prose.**
*   **Position:** No change needed to the verdict line, as the paired supplement already sits on the next line.
*   **Compromise:** I accept Sol, Kimi, Grok, and Fable’s prefix (*"Primary band rule: not distinguishable"*) on the dashboard while keeping the ledger string untouched.

---

## Claude Fable 5.1 (Anthropic (independent instance))

**Round 3 — Claude Fable 5.1**

**Framing.** Not misrepresented. Two concessions first: the 4.4 bootstrap is 10,000 draws / 5–95 (artifact beats my memory), and my "ΔP ≈ −1.6 pp" had the sign wrong and was an illegal substitution anyway (Sol, Opus correct). Both are settled; I don't reopen them.

**D1 — Part A decision rule.** Final: (a), no pre-committed switch. Opus's −1.96·SD_block version is Argon's rule with a wider margin: at SD_block ≈ 2.6 pp the floor is ≈ −5 pp, which two near-identical series (ρ > 0.99) cannot plausibly breach, so it is a switch-by-default sealed after E1's gap table was seen. Compromise: the 2027 council is *unconditionally* obliged to decide the convention as an agenda item, with both replays in hand — mandatory regardless of Δ, so no trigger value exists to aim at. **VETO** on any conditional switch sealed now. Would change my mind: a council decision to switch *unconditionally* on unit grounds at the refit with its own replay — that is a measurement decision, not an outcome-conditioned one, and §1.3 is satisfied by the replay.

**D2 — Bootstrap.** Concede: match 4.4 — 10,000 draws, seed 42, 5–95. My comparability argument now points Sol's way. The 10–90 interval can be printed from the same draws for §3.2(b) comparability; costs nothing.

**D3 — Operator.** (a): convert daily then average for the live leg, BEY(TB3MS) for history, gap printed. The bias is ≤ 0.003 pp, so this is bookkeeping; Kimi's convert-after-averaging goes in as a robustness column. Not a hill.

**D4 — B3 audit.** Final: the < 10 bp max |revision of E| bar stays. Sol is right that passing it says nothing about validity; it is a *stability* bar, and a ledger column whose history moves by > 10 % of today's curve is not a ledger column. Compromise: label it "stability, not validity"; if failed, the audit is published and no column opens. Series: concede to Grok — KW is the audited series, ACM a dated note in the audit, not a second live signal.

**D5 — C6 now.** (b), minimal. Text: "Curve decomposition (context; not an input to P): Kim-Wright 10Y term premium 0.99 pp (2026-10-16); ACM 0.84 pp (2026-07). Term-premium estimates are model-dependent and revised. P reads the raw curve only." No ratio, no literature, step-4 sentence to the methods doc. I accept (a) if the vintage audit starts this month and the line returns after it.

**D6 — 17.9 %.** Concede to Grok. Print: "Substituting the CMT or BEY curve into the frozen weights does not produce P and is not shown." The number's didactic value is less than its citation risk.

**D7 — C2.** Full §1.2 sentence in the row. A benchmark row is a "published skill statement" under §1.2's wording. Compromise: short form acceptable only when the full sentence renders in the same view, directly above the table.

**D8 — C4.** Keep, pinned and labelled "heuristic (quarter end + 42 days); BEA vintage not verified". Dropping the inference leaves the reader with a vintage label that is simply wrong (our first-seen vintage called "advance"); a labelled heuristic is better than silence.

**D9 — C7.** Gate line as the 3.89 pp difference (no objection). Interval: compute the oracle-free 219-origin paired interval now (the per-origin losses exist; same procedure, 10,000/seed 42/5–95) and print it first. **VETO** on the censored interval standing alone under the §1.2 sentence: the only uncertainty band on the page would attach to figure (ii), which is +27.05 % as a de facto standalone. Interim compromise (Kimi): censored interval to a labelled footnote until the oracle-free one exists. Would change my mind: a demonstration that the 219-origin paired bootstrap cannot be computed from existing artifacts — I don't believe it.

**D10 — Dashboard prose.** Accept "Primary band rule:" prefix with "paired supplement does not decide the verdict" on the next line. Ledger and verdict string untouched.

**Vetoes:** D1 (conditional pre-committed switch), D9 (censored interval alone under §1.2). Everything else I can approve on the compromises above.

---

## Grok 4.7 (xAI)

D5/D6 framing: my Round-2 C6 text was the minimum (no TP level, no E, no ratio), not a numbers line. I quoted 17.9 in council argument; that figure must not ship beside P. D2: I accept the fact check — 4.4 is 10,000 draws, seed 42, 5th–95th. Fable’s “1000/10–90” for 4.4 is false.

**D1. VETO** Claude’s switch-unless Δ_OF < −1.96·SD_block. Same inversion as the withdrawn −0.50 pp rule: the frozen incumbent must beat the challenger to survive, and the bar is written after E1 (gap 0.55–0.81 pp; 4 of 12 onsets). §1.3 does not allow a skill figure to select the configuration. DeepSeek’s |Δ| ≥ 2 pp agenda trigger is the same selection. No outcome trigger. Compromise: Part A is an unconditional refit agenda item; the later council decides with the replay. Mind-changer: none before that replay exists.

**D2.** Part A’s paired interval matches the paired-loss artifact: 10,000 draws, seed 42, 5–95 — not §3.2(b)’s frequency gate. Changed from my Round 2. Compromise: either spec if pinned and named. No veto.

**D3.** Live leg: convert each DTB3 day, then average; history stays BEY(TB3MS); print the operator gap. Jensen ≤ 0.003 pp, so this is consistency, not size. Compromise: Kimi’s convert-after-average on both, mean-of-converted printed once. No veto.

**D4.** No 10 bp validity bar. Kimi’s 12-vintage audit is published; the column stays shut until a later council sees it. 10 bp of E is ~1.6 pp of shadow P at β = −1.29. Series: THREEFYTP10 only. **VETO** a co-equal ACM live line — ACM is on the closed list. Dated audit note only. Compromise: a 10 bp gate labelled administrative, not validity, KW only.

**D5. VETO** any standing line beside P that prints TP or E levels. Frozen logit turns +0.02 pp expectations into ~42%. Remove C6 from standing warnings until the audit. Methods text only: model-dependent, revised, not an input. Compromise: that sentence in methods, nowhere adjacent to P.

**D6. VETO** printing ≈17.9% (or any substituted probability) in C5, on the dashboard, or in LOG.md. Anti-substitution sentence, no number. Compromise: methods appendix, labelled not-P, not beside the published figure.

**D7.** Full §1.2 sentence inside the benchmark row, so +27.05 cannot be copied alone. Compromise: Claude’s short row note if the full sentence sits in the same visual unit, immediately above, and the row does not carry +27.05 without (i) and (iii). No veto.

**D8.** Drop “later vintage than advance.” “First seen by us” is the fact; QE+32+10 is an unverified BEA claim — the class of error C4 was fixing. Changed from Round 2. Compromise: keep the inference only against a cited BEA calendar. No veto if the heuristic label cannot be missed.

**D9.** Gate line: “curve-only minus F5 = +3.89 pp, oracle-censored full path.” Compute the 219-origin interval on the 4.4 spec and print it first. **VETO** the censored interval as the only band under the §1.2 sentence. Compromise: until it exists, footnote only, not under that sentence.

**D10.** Dashboard prefix “Primary band rule:”; paired supplement stated as not deciding. Ledger string unchanged. No veto. Compromise: no prefix if the next line already says the supplement does not decide.

---

## Kimi K3.1 Pro (Moonshot AI)

**Framing correction:** my audit design does not imply support for a 10 bp *validity* gate. The matrix otherwise represents my principal positions correctly.

**D1 — Part A decision rule.** No pre-committed switch and no outcome trigger: Claude’s “switch unless \(\Delta_{OF}<-1.96SD\)” still selects the winner using the same historical episodes, merely with a wider rubber stamp. **Compromise:** Part A automatically appears on the 2027 agenda regardless of result; that council decides after inspecting the complete replay, rate bins and calibration.

**D2 — Bootstrap.** Prefer 10,000 draws, seed 42, pinned episode blocks and 5th–95th percentiles, matching the existing 4.4 diagnostic; 10,000 draws improve Monte Carlo precision, not the nine-block information content. **Compromise:** accept 1,000/10–90%, or print both percentile pairs, provided the specification is fixed before computation.

**D3 — Aggregation.** I still prefer convert-after-averaging in both calibration and live inputs, with mean-of-daily conversion as robustness, because that most closely preserves the calibration/live operator. **Compromise:** accept mean-of-converted daily DTB3 if convert-after-averaging is also reported and the disclosed Jensen bound—≤0.003 pp even at within-month \(\sigma=1\) pp—is printed.

**D4 — B3 audit.** Use KW alone for any recurring series; ACM may be a dated secondary audit series, never a second live signal or an unmatched-date “model disagreement.” **Compromise:** accept max \(|\revision E|<10\) bp across the 12 hashed vintages as an arbitrary **display-stability** rule, explicitly not evidence of predictive validity.

**D5 — C6 now.** Remove the standing decomposition beside P until the audit; matched-date KW/ACM evidence is currently absent. **Compromise:** methods documentation may contain dated estimates, and the dashboard may carry Grok’s minimal “model-dependent, revised, not an input,” with no E value, TP share, ratio or literature direction.

**D6 — Illegal CMT probability.** Do not publish 17.9% in C5 or other user-facing material; explain invalid substitution without supplying a counterfeit headline. **Compromise:** retain it only in council/verification records as an audit calculation.

**D7 — C2.** Prefer the complete §1.2 sentence in the benchmark row. **Compromise:** Claude’s layout is acceptable if that complete sentence appears immediately above the table and the row’s short note contains all three figures in order—never standalone +27.05%.

**D8 — C4.** Publish “first seen by us” and drop the advance-vintage inference unless BEA’s release calendar establishes it. **Compromise:** quarter-end +42 days may remain an internal data-quality heuristic, explicitly not a public vintage claim.

**D9 — C7.** Print “curve-only minus F5 = +3.89 pp, oracle-censored full path.” Compute the 219-origin oracle-free paired interval now and print it before the 198-origin interval. **Compromise:** until then, footnote the latter as pending rather than deleting the diagnostic permanently.

**D10 — Dashboard prose.** Use “Primary band rule: not distinguishable,” followed by “paired supplement does not decide the verdict”; ledger and scoring strings remain unchanged. **Compromise:** the explanation may be a tooltip where space requires.

**VETO:** any automatic/pre-committed BEY adoption rule, and any C6 restoration of directional recession interpretation beside P. No Part A skill result changes the governance veto. Matched-date model comparisons plus the 12-vintage audit could change my mind about **neutral numerical display**, not about predictive validity.

---

## DeepSeek V4 Pro (DeepSeek)

## Framing correction

The matrix lists me as accepting "p ≈ 0.09" in Q4. I withdrew that in Round 2; 8.9% is a draw share, not a p-value. The matrix's settled item 10 already reflects this, but my Q4 position line still carries the error.

## D1 — Part A decision rule

**Final:** No pre-committed switch, no outcome trigger. My Round-1 convening trigger was wrong: it converts a prior into a governance mechanism and invites panel design to land the number. The 2027 council decides with the full replay.

**Compromise:** Claude's author's prior (|Δ| < 2 pp) printed away from the result, labelled "not a criterion." I can live with that.

## D2 — Part A bootstrap

**Final:** 10,000 draws, 5–95, seed 42, matching the existing 4.4 interval spec. Consistency with what is already published matters more than matching §3.2(b)'s frequency-gate spec, which tests a different object.

**Compromise:** Report both intervals if the cost is trivial; pin 10,000/5–95 as primary.

## D3 — Aggregation operator

**Final:** Convert daily then average for the live leg; BEY(TB3MS) for history; disclose the operator difference. The Jensen bias is negligible (≤ 0.003 pp even at 1980 volatility) but the spec should pin the operator for reproducibility.

**Compromise:** Kimi's convert-after-averaging everywhere as the primary, mean-of-daily as a printed robustness check. Either is acceptable if pinned.

## D4 — B3 revision audit

**Final:** Kimi's 12-vintage hashed audit, with Fable's pinned bar: max |revision of E| < 10 bp before an unscored column opens. Without a bar the audit is a rubber stamp.

**Compromise:** If Sol's no-bar position prevails, require the audit results printed prominently with the column opening decision left to council — but I would **VETO** opening the column without any pinned criterion. Evidence to change my mind: a demonstration that revision magnitude is uncorrelated with signal validity in this setting.

## D5 — C6 line now

**Final:** A neutral numbers-only line now: KW and ACM TP with dates, "model-dependent, revised, not inputs." Full removal until the audit (Kimi/Sol) is defensible but overcorrects; the decomposition exists and a curve-only model's reader should know it.

**Compromise:** Grok's minimum text. I would **VETO** any line containing "98%" or a Rosenberg-Maurer citation beside P.

## D6 — C5's illegal figure

**Final:** Print the illegal number once with the explanation: "(substituting CMT gives ≈ 17.9%; that is not P)." Showing why it is illegal is more protective than silence.

**Compromise:** Grok's no-number position if the anti-substitution sentence is explicit. Not a veto point.

## D7 — C2

**Final:** Full §1.2 sentence in the benchmark row. The order clause exists to prevent exactly this ambiguity.

**Compromise:** Claude's short note if the full sentence is printed directly above the table and the row carries a pointer to it. Not a veto point.

## D8 — C4

**Final:** Keep the quarter-end + 32 + 10 rule, labelled "heuristic; BEA vintage not verified." Dropping it removes useful information; verifying BEA's calendar is disproportionate effort.

**Compromise:** None needed; this is minor. I accept either if the heuristic label is explicit.

## D9 — C7

**Final:** Compute the oracle-free 219-origin paired interval now and print it first; the censored interval follows. The eye reads the first uncertainty band as the headline.

**Compromise:** If computation is deferred, the censored interval must carry "oracle-free interval pending" — but I would **VETO** the censored interval appearing alone under the §1.2 sentence without that qualifier.

## D10 — Q5 dashboard prose

**Final:** Tooltip/footnote only: "Not distinguishable under the primary band rule" as a gloss, verdict string unchanged.

**Compromise:** Sol/Kimi/Grok's prefix if the council prefers it. Not a veto point; the verdict string itself is what matters and it stays.

---

## Claude (Opus 5.5) (Anthropic — interested party, co-builder and secretary)

**Claude Opus 5.5 — Round 3 (interested party; secretary).** No vetoes.

**D1 — withdraw my switch rule; (a).** Fable is right on both counts: the converted curve is still a mismatch
(semiannual par CMT 10y vs simple ACT/365 bill BEY), so "fixing the bug" overstates it; and a rule written with
E1's gap table in hand chooses on a known pattern. No pre-committed switch, no outcome trigger. Compromise for
DeepSeek: the 2027 refit council receives Part A's output as a standing agenda item regardless of its size — the
agenda is unconditional, so no threshold can be aimed at.

**D2 — 10,000 draws, seed 42, 5th–95th percentiles.** Part A's paired Δ will be read beside the 4.4 interval,
which uses exactly that (artifact above); matching it makes the two comparable. Fable's comparability argument
points the same way once the fact is corrected.

**D3 — move to Kimi's (b).** Same operator in calibration and live: BEY of the averaged discount rate (monthly
TB3MS in history; the trailing-window mean of DTB3 live), with mean-of-converted-daily printed once as a
robustness line. The magnitude is ≤ 0.003 pp, so the only thing at stake is consistency, and consistency favours
one operator.

**D4 — (a) with Sol's caveat; KW only.** Pin max |revision of E| < 10 bp as an *admissibility (stability)* bar for
opening the unscored column, stated as "not evidence of validity". Without a pinned bar, "audit first" is a ritual
with a discretionary end. KW (THREEFYTP10: daily, Fed Board, public domain, contemporaneous with the live window)
is the series; ACM appears only as a dated note in the audit report — two live estimates three months apart
invite exactly the mismatched comparison Sol flagged.

**D5 — compromise between (a) and (b): remove C6 from the standing warnings.** The neutral decomposition already
exists in the firewalled context block ("10y = term premium + expected: 5.09 = 0.99 + 4.10 (2026-10-16, Kim-
Wright)"). So: C6 leaves the standing warnings (Kimi, Sol); the existing context line gains Grok's minimum,
"model-dependent, revised; not an input", and nothing else — no expectations-minus-3m, no share, no literature.
The step-4 history goes to the methods documentation (README) with the verbatim E3 sentence. That gives (b)'s
transparency without a warning-slot that argues with P.

**D6 — never print 17.9 % (Grok).** An illegal number printed to explain its illegality is still printed; the
screenshot loses the explanation. C5 says the substitution is not allowed and why, without the figure.

**D7 — accept the full §1.2 sentence wherever the curve-only skill appears without it** (console print, benchmark
row if the table is rendered alone). On the dashboard the row note may refer to the sentence directly above it.
I can live with the full sentence in the row everywhere if the majority prefers.

**D8 — converge:** "after the usual advance-release window (heuristic: quarter end + 32 + 10 days); BEA vintage
not verified". Rule pinned, frozen with the 5 bp until the refit.

**D9 — oracle-free 219-origin interval computed now (10,000 draws, seed 42, 5–95, same cycle blocks) and printed
first; the 198-origin interval follows, labelled oracle-censored; gate line as "curve-only minus F5 = +3.89 pp,
oracle-censored full path".** Sol: this costs nothing frozen, and "optional" leaves the only band on the page
attached to figure (ii).

**D10 — concede to "Primary band rule:"** as a prefix on the dashboard verdict line, with the paired supplement's
existing "does not change the verdict" sentence beneath it. The ledger string is untouched; the prefix names the
rule, it does not add a verdict word.
