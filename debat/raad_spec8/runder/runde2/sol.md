## 1. Attack

**Claude Opus: “every historical onset came during an inversion or within 9 months of its end.”** False. E1 explicitly identifies 1957, 1960 and 1990 as onsets without a qualifying inversion. The nine-month maximum is conditional on the selected inversion-linked episodes; it cannot establish coverage of all onsets or validate H=12. Opus should withdraw this justification, not repeat it as supporting evidence.

**Gemini: “require … coefficients … so we confirm β₂ < 0 (or re-parameterize as Cₜ and Cₜ − Mₜ).”** This is an outcome-dependent specification fork. Moreover, the transformation is not orthogonalisation:
\[
\operatorname{Cov}(C,C-M)=\operatorname{Var}(C)-\operatorname{Cov}(C,M),
\]
which is generally nonzero. Under standardisation and ridge, changing coordinates also changes the effective penalty and therefore predictions. Inspecting coefficients and then choosing the parameterisation constitutes another model search. Seal curve plus minimum; retain it even if the memory coefficient is positive.

Gemini’s proposed live minimum also mixes a trailing daily spread with calendar-month GS10−TB3MS. That is a new feature definition, not the existing v4 object.

**Grok: “a probability fitted on all 12 onsets, with the feature chosen after the current lag was known, is not an experiment.”** This confuses contaminated development with prospective evaluation. A predictor fixed today can produce genuinely out-of-sample forecasts tomorrow despite using historical outcomes for training. The prohibition concerns using development observations as evidence, not using them to estimate coefficients. Grok’s distribution objection is serious; his statistical objection does not justify refusing a private forecast archive.

**Claude Fable: “print, once, a second coefficient vector fitted on origins ≤ 2022Q3 as disclosure.”** Reject. That introduces another estimation cutoff after inspecting this cycle. Disclose the actual training eligibility and exposure to this episode; do not manufacture a second fit to illustrate contamination. Also, the brief does not establish that labels through 2025Q3 are eligible under the operational 18-month floor.

## 2. Steelman

**Kimi’s matched curve-only comparator is the best missing idea.** Until September 2027, operational P remains frozen while the shadow receives a newly estimated specification. Thus
\[
L(P_{\rm operational})-L(P_{\rm memory})
\]
measures the combined effect of memory, re-estimation and any eligibility difference—not memory alone.

I would therefore archive one **matched curve-only control**, fitted on exactly the shadow’s eligible rows, snapshot, scaling convention and schedule. This is an experimental control, not another challenger or tuning opportunity. Operational P remains the practical comparator; the matched control isolates incremental memory performance.

## 3. Revised positions

**Q1 — Yes**, exactly one memory specification plus that matched control, all private and without operational authority. This remains acceptable despite post-hoc motivation because no historical result determines launch or retention.

**Q2 — Keep `curve_min12`**, its existing monthly series, calendar window and ≥6-observation rule. Pre-existence limits discretion; it neither preregisters the choice nor validates twelve months. Reject the purported structural necessity of equating backward memory with the forward label horizon: those are distinct economic quantities. No alternate-horizon runs.

**Q3 — Keep curve plus minimum**, operational λ=1 implementation, training-only scaling, unpenalised intercept and operational labels/eligibility. Report additional missing-feature exclusions. Fit on the sealed operational snapshot; freeze until September 2027, then follow its schedule. Add the matched control. Historical fitting is allowed but contaminated; neither coefficients nor historical scores establish usefulness.

**Q4 — Strengthen the archive contract:** store the memory value, both experimental forecasts, vintage identifiers and missingness privately and append-only. If `hovedbog.jsonl` is public, use a private companion archive. Publish methodology, not competing probabilities. No automatic LOG.md promotion in 2027.

**Q5 — Keep unscored tracking only.** Quarterly paired losses, mature labels, no pre-2027 evidence. The proposals’ bootstrap lengths—4, 8, 16 and 20 quarters—demonstrate unresolved design discretion, not four equivalent implementations. Two onsets are an eligibility minimum, not adequate inferential replication. A future scored mandate must be sealed before its counted onsets; accumulated tracking cannot become retrospective confirmation.

**Q6 — Keep November 2026**, conditional on sealing before generation. Exclude 2026 origins from evidence. The logging/display/start decisions remain acceptable post hoc because outputs cannot alter them.

AGREE:
- P stays unchanged; historical results cannot validate this challenger.
- No dashboard probability at launch; genuine evaluation requires prospective outcomes.

DISAGREE:
- Grok rejects a shadow; the other six authorise one.
- I favour unscored tracking; most others propose sealing a scored bar now.
- Opus/DeepSeek leave possible 2027 LOG.md exposure; I reject automatic exposure.

CHANGED-MY-MIND:
- Add Kimi’s matched curve-only control: operational P alone confounds memory with re-estimation and eligibility.