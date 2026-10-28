## A) Independent proposal

### Q1 — Authorise one memory shadow, not another feature search

**Yes: authorise exactly one sealed shadow model, with no effect on operational P, its band, or its verdict.** Existing context communicates the concern but cannot produce a reproducible prospective forecast record for a specified memory model. This is acceptable despite being post hoc because the mandate creates an experiment, not evidence that memory improves prediction; historical performance must not determine whether it is launched or retained. No parallel memory candidates, tuning runs, or retrospective winner selection are authorised.

### Q2 — Use the existing `curve_min12`, without claiming it is optimal

Choose **the repository’s existing 12-month minimum, including its minimum-six-observations rule**:
\[
m_t=\min\{c_s:s=t-11,\ldots,t\},\qquad c_s=GS10_s-TB3MS_s,
\]
provided at least six observations are available; otherwise the feature is missing. Archive the exact v4 implementation and its provenance before running the shadow fit, and construct every historical feature using information available at that origin. The pre-existing definition is a valid tie-breaker, **not a clean preregistration**: it belonged to an earlier model grid, and its unrecorded result could have influenced project choices. I accept this post-hoc choice because it minimises new researcher discretion, not because E1 validates twelve months—E1 omits inversion-free onsets and does not establish an optimal predictive horizon. Reject 24/36 months and the other constructions under this mandate; their present-day consequences are already known.

### Q3 — Add memory to curve; reproduce the operational fitting convention

Fit
\[
p^{M}_t=\operatorname{logit}^{-1}\!\left(\alpha+\beta z(c_t)+\gamma z(m_t)\right),
\]
using an unpenalised intercept, L2 slope penalty, and **exactly the operational implementation of \(\lambda=1\)**, including its loss normalisation and standardisation convention. Estimate standardisation parameters on the fitting sample only; use operational labels, origin calendar, universe and eligibility, with one explicit exception: rows missing the memory feature are ineligible, and that exclusion must be reported. Use pre-2027 data for fitting, accepting the contamination openly; disclose E1–E4, the earlier v4 grid, the grand review and yesterday’s inspection, and forbid interpreting fitted coefficients or historical scores as validation. Fit once for launch using a sealed, dated snapshot, freeze until September 2027, and subsequently refit only alongside the operational schedule. **Do not assert that today’s shadow P will be close to P**: a positive minimum does not imply this, because adding a correlated predictor changes the fitted intercept and both slopes.

### Q4 — Machine archive only, with a public specification

Record `p_hukommelse` on every ledger row, labelled **experimental, unscored, not used in the verdict**, with model-version and fitting-snapshot identifiers. Keep the probability out of LOG.md, the dashboard, alerts and narrative summaries; publish the specification and existence of the experiment instead. If `hovedbog.jsonl` is publicly distributed or rendered downstream, use a private append-only companion ledger rather than pretending that a machine-readable probability is not user-facing. This placement is acceptable despite being decided post hoc: it limits distribution, not statistical selection, and every scheduled forecast must be retained regardless of value. September reports may document completeness and implementation faults, but must not promote favourable tracking results.

### Q5 — Unscored tracking only; reject Claude’s significance rule

**Authorise unscored tracking, not a formal superiority test under this spec.** For descriptive monitoring, on the existing quarterly origin calendar compute paired log-loss differences
\[
d_t=\ell(P_t,y_t)-\ell(p^M_t,y_t),\quad
\ell(p,y)=-y\log p-(1-y)\log(1-p),
\]
using identical origins, mature labels and both forecasts as actually issued. Origins before 2027 are audit records only, never evidence; overlapping four-quarter labels must not be presented as independent observations. Claude’s “\(1.96\,SD_{\rm block}\)” is not a sealed numerical bar: it leaves the estimator, block construction, standard-error interpretation and repeated September looks unspecified, while two onsets are merely a minimum eligibility condition, not adequate effective sample size. This post-hoc descriptive protocol is acceptable because it makes no historical superiority claim; any future scored test requires a separate council mandate sealed before the onsets used for that test, and existing tracking outcomes cannot be retroactively converted into confirmatory evidence.

### Q6 — Launch in November 2026

Start with the **November 2026 row**, provided the code, fitting snapshot, specification and archive controls are frozen before that row is generated. The November–December records establish operational integrity but are explicitly excluded from evidentiary use under the no-pre-2027 rule. Record the first scheduled output even if its level is inconvenient; do not postpone launch after inspecting it. This start date is acceptable despite being post hoc because no forecast is backfilled and no current-cycle result is claimed as validation.

## B) Verdict on Claude’s draft

| Draft position | Decision |
|---|---|
| **Q1: Shadow, never in P** | **Keep the operative decision. Amend the rationale:** prospective logging enables evaluation of this particular algorithm; it does not guarantee that a tiny number of future cycles will settle the general memory question. |
| **Q2: `curve_min12`** | **Keep the variable; amend the justification.** Prior implementation reduces discretion but is contaminated by the v4 search. Strike the claim that the nine-month historical maximum validates it, and strike the prediction that today’s shadow must be close to P. |
| **Q3: Two features, standardised, λ=1** | **Keep the core form; amend the implementation contract.** Specify penalty scaling, training-only standardisation, missing-feature exclusions, snapshot provenance, launch fit and freeze dates. No historical candidate comparison. |
| **Q4: Ledger only** | **Keep the distribution restriction; amend the storage rule.** A public ledger is distribution. Use a private companion archive if necessary, while publishing the methodology. |
| **Q5: Tracking plus eventual \(1.96\,SD_{\rm block}\) comparison** | **Keep unscored tracking; strike the proposed scored trigger.** Neither its uncertainty estimator nor its sequential decision rule is specified. “Two onsets” does not repair that. |
| **Q6: November start** | **Keep**, conditional on sealing before generation and explicitly excluding 2026 origins from evidence. |

## C) Biggest risk in my proposal

**The shadow can acquire policy authority without ever earning it.** With perhaps only a handful of informative episodes over decades, an appealing divergence from P could become an unofficial override long before predictive value is established. Private storage and a prohibition on probability-based commentary reduce that risk, but Rasmus must enforce the boundary: **a more plausible narrative is not a validated probability.**