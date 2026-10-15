# Kimi K3 — Round 2

## 1) Attacks

**Q3 — GPT and Fable (monthly fit).** GPT: *"resolving a prose–implementation conflict in favour of the prior written specification is more defensible than inventing a status-quo tie-break after the prose passes."* Wrong on the mechanics. The literal reading was computed for the first time on 2026-10-15; the only gate executed before results were knowable is the thinned code. Declaring the untested sentence "the spec" and the executed test "the bug" is itself post-hoc adjudication. And the literal pass is inferentially empty: +29.24 % on 591 monthly origins vs +27.05 % on 198 quarterly origins is unpaired — different origin sets, different pooled base rates, +2.19 pp against block-MDE 2.99. The only paired evidence in E2 is the three thinnings, and the phase coinciding with quarterly origins is *worse* than quarterly (26.03 vs 27.05). Effective samples: 591 origins with 11-month overlap ≈ 49 independent units; 198 with 3-quarter overlap ≈ 50. Monthly adds no independent cycles; the β steepening (−1.29 → −1.41) reweights the same episodes. GPT's own risk paragraph concedes exactly this ("specification error disguised as textual fidelity") and adopts monthly anyway. Fable's "spec governs code" clause is legitimate *prospectively*; applying it to the conflict that motivated it, knowing it flips the outcome, is the selective principle he claims to reject. A secondary hazard: under monthly, +29.24 % becomes the headline-able number — uncomparable with +27.05 % and certain to be read as an improvement.

**Q9 — Gemini and Fable (L_R = 21).** Gemini: *"claiming L_R = 18 pretends we knew the recession had ended at month 18."* The mechanism is real but it is an *entry-timing* mechanism, not a *label-finality* mechanism. A row already in eligible_fit is invalidated only by a peak announcement placing a peak ≤ origin; peak lags are ≤ 12 < 18, and E6 found 0 relabels in 49 years. Trough lags of 20–21 merely delay entry of post-trough label-0 rows — rows worth ~0.1 pp of weight (E6), absorbed at the next refit. Their fix taxes *every* origin 3 months forever: N = 270 not 271 at the 2027 refit (Gemini's own risk paragraph), and every future positive label enters 3 months later under the content trigger — the precise recalibration lag Q6 exists to remove. It also proves too much: a trough lag of 24 would breach 21 just as 21 breaches 18; the floor is a monitored bound, not a guarantee. Correct fix, two parameters: L_R = max(18, max peak lag) for label maturity; eligibility = (age ≥ L_R) AND (censoring status resolved with information available at R); trough lags audited against the censoring rule. That absorbs Fable's "label and censoring final at R" requirement without the permanent tax.

**Q2 — GPT's MDE point (brief).** *"An MDE is not a significance threshold."* True for the power-concept; false for the gate's operationalisation. Tier 2 as I specified it — 1.96·SD_block of the paired Δ, recomputed each refit — *is* a paired block-bootstrap test. Rename it ("paired 95 % margin") and keep the tier.

## 2) Steelman

Fable's Q10-4: an unscored supplementary column logging P and eventual outcome for months censored under the open-episode rule. E5 quantifies what live censoring discards — the entire 1980-08..1981-05 run-up, 10 positive rows, P to 96.6 %, −4.5 pp replay skill. The double-dip is where the model earns its keep, and my Round 1 ratification let that record vanish silently. The column costs the key nothing and preserves the only evidence that can ever indict or vindicate the censoring rule.

## 3) Revisions

- **Q10 item 4:** ratify *with* Fable's censored-month column as a condition (was: breach annotation only).
- **Q8:** defer → closed in practice. The 12-snapshot audit addresses revision risk only; it cannot decontaminate 6-of-8 seen onsets, and with MDE ≈ 4.4 pp and 3 pre-1990 onsets the historical test is spent regardless. Reopening requires a rationale independent of the seen pattern — Grok's formulation, which I now adopt.
- **Q9:** keep peak-only, but write the two-parameter eligibility rule into the protocol text (above) instead of my vague "separate audit".
- **Q3:** keep quarterly; add the spec-governs-code clause prospectively and permanent dual publication of both §2 readings.

## AGREE
- λ = 1 fixed, §3 amended; nested and oracle-free printed beside fixed-λ in every skill statement (all seven).
- §4 amended: no per-origin selector; curve-only by council lock (all seven).
- 1947Q2 kept; three-start sensitivity printed permanently (all seven).
- Key untouched; E5 supplement with all censoring variants; 150-year and 36–53 % figures in the public sentence (all seven).
- F29 items 2–3 ratified; E4 documented as rule-dependent; future searches use one pre-fixed symmetric bar (all seven).

## DISAGREE
- **Q3:** monthly (GPT, Fable) vs quarterly (Gemini, Grok, DeepSeek, Opus, me).
- **Q9:** L_R = 21 (Gemini, Fable) vs peak-only 18 + separate trough audit (GPT, Grok, DeepSeek, Opus, me).
- **Q6:** adopt trigger (GPT, Gemini, DeepSeek, Opus, me) vs reject (Fable, Grok).
- **Q1 headline:** oracle-free led (GPT, Gemini, Fable) vs fixed-λ led, mandatory triple print (Grok, DeepSeek, Opus, me).
- **Q2 tiers:** drop 4.42 (Gemini, Grok) vs two tiers (DeepSeek, Fable, Opus, me); GPT strikes tier-2 "evidence" language.
- **Q8:** close (Gemini, Grok, now me) vs defer-with-snapshots (GPT, Fable, DeepSeek, Opus).
- **Q10-4:** plain ratification (Gemini, DeepSeek, Opus) vs conditional (Grok: byte-identical rule; Fable, me: censored-month column).

## CHANGED-MY-MIND
- **Q8:** defer → effectively closed; contamination is incurable, snapshots only audit revisions.
- **Q10-4:** added Fable's unscored censored-month column — the 1980–81 excision (P to 96.6 %, −4.5 pp) must not leave the record.
- **Q9:** absorbed the opposition's valid core into an explicit eligibility condition rather than dismissing L_R = 21 as pure post hoc.