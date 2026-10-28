# ROUND1 — samlet


---

## GPT-6.1 Sol Pro (OpenAI)

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

---

## Gemini 4 Argon (Google)

### A) Agenda Answers

**Q1 — At all?**
Yes, log a shadow memory model, never in $P$. Context lines on the dashboard require subjective human synthesis, which cannot be scored prospectively or tested against a null hypothesis. The fundamental vulnerability of a level-only yield curve model is bull-steepening immediately prior to onset (as in 1990, 2001, 2007Q4, and 2020), where the Federal Reserve cuts short rates in anticipation of weakness, driving the spread positive and collapsing $P$ right before the recession starts. Logging a shadow probability now is the only way to accumulate out-of-sample, prospective log-loss evidence on whether capturing the prior inversion fixes this structural flaw without generating excessive false positives during soft landings.

**Q2 — Which single memory variable, and which horizon?**
Use `curve_min12`: the rolling 12-month minimum of the monthly spread, defined at origin $t$ as $M_t = \min_{k \in \{0,\dots,11\}} (\text{GS10}_{t-k} - \text{TB3MS}_{t-k})$. Given E2, any choice of $H \in \{24, 36\}$ is heavily contaminated by the knowledge that the 2022–2024 inversion ended 22 months ago, making it a textbook post-hoc forking path designed to inflate today's probability. The pre-existing v4 code definition (`curve_min12` in `calibrate.build_monthly`) is the only objective, pre-committed tie-breaker available that avoids tuning the horizon to the current cycle. Furthermore, $H=12$ is structurally matched to the model's 4-quarter target horizon and aligns with E1, where the maximum historical lag from inversion end to onset was 9 months (2007-04 to 2008-01). Accepting $H=12$ means accepting that the shadow model reads near $P$ today (+0.24 pp min vs +1.12 pp level), which proves we are not fitting to the current cycle.

**Q3 — Model form and fitting.**
Use a two-feature L2-penalised logistic regression: $P_{\text{mem}} = \text{logit}^{-1}(\beta_0 + \beta_1 \tilde{C}_t + \beta_2 \tilde{M}_t)$, where $\tilde{C}_t$ and $\tilde{M}_t$ are the current curve and `curve_min12`, each z-scored using the in-sample training mean and standard deviation. Keep $\lambda = 1.0$, the exact operational quarterly universe (from 1947Q2), the 4-quarter-ahead onset label, and the operational eligibility and annual September refit rules. However, we must check the historical correlation between $C_t$ and $M_t$ before sealing: because both are standardization-scaled and penalized equally by $\lambda = 1$, high collinearity will split the slope coefficient and dilute the signal during active inversions unless we verify how L2 handles the pair; alternatively, parameterize the model orthogonalized by construction as level $C_t$ and re-steepening $\Delta_t^+ = C_t - M_t \ge 0$, standardized. Pre-2027 data may be used for fitting under RAADETS_2027 §8.3, provided the spec explicitly discloses that the feature selection and motivation were contaminated by E1–E4, the August grand review, and the 2026 walk-forward inspection.

**Q4 — Where it is logged and shown.**
Log `p_hukommelse` exclusively in `hovedbog.jsonl` on every monthly run, and print its comparative tracking diagnostics in the annual September refit report; keep it entirely out of `LOG.md` and the public dashboard (even after 2027). The precedent from RAADETS_SPEC7 (Grok's distribution argument) is decisive here: a secondary probability on the dashboard—especially one bearing an intuitive label like "memory"—will immediately be screenshotted and treated as the "true" model whenever it diverges from $P$. Unlike `P_1953Q2` or `P_1960Q1`, which are minor sample-start sensitivity checks, a two-feature memory model is a competing economic specification and must not dilute the single-number operational verdict.

**Q5 — Evaluation.**
Conduct unscored tracking in the ledger, transitioning to a formal scored comparison only after at least 2 prospective NBER recession onsets have occurred post-sealing (and their 4-quarter evaluation windows have fully closed). At that point, evaluate the paired per-origin log-loss difference $d_t = \ell(y_t, P_t) - \ell(y_t, P_{\text{mem},t})$ exclusively on prospective post-sealing origins, using a moving-block bootstrap (block length 4 quarters, 10,000 replications) to compute $\text{SD}_{\text{block}}(\bar{d})$. Pin the symmetric bar from RAADETS_2027 §5.2 now: if $|\bar{d}| / \text{SD}_{\text{block}}(\bar{d}) > 1.96$, the result triggers a mandatory council agenda item to consider promoting or retiring the shadow model, never an automatic switch.

**Q6 — Start date.**
Start logging `p_hukommelse` with the November 2026 row (log window 10–13 November 2026), computing the initial weights from the frozen 72c3371d calibration snapshot (`1947Q2` through the last eligible origin in that snapshot). Waiting until September 2027 discards 10 months of prospective out-of-sample data during the exact macro regime—22 months post-inversion—that prompted this debate. Sealing and logging now ensures the model's record covers the resolution of the 2022–2024 cycle before its outcome is known.

---

### B) Verdict on Claude's Draft Positions

* **Q1 (Shadow model, never in P):** **Keep as written.** The rationale is sound and respects the v5.0.1 lock.
* **Q2 (`curve_min12`):** **Keep as written.** Using the pre-existing v4 definition is the only rigorous defence against post-hoc horizon shopping given E2.
* **Q3 (Two features, curve + `curve_min12`, $\lambda=1$):** **Amend.** Claude proposes raw $C_t$ and $M_t$ standardized with $\lambda=1$, but fails to address collinearity and how live daily trailing inputs map to monthly minimums. Amend Q3 to: (1) explicitly define live `curve_min12` at the monthly log window as $\min(C_{\text{live}}, \min_{k \in \{1,\dots,11\}} C_{\text{monthly}, t-k})$ so the live trailing month is compared against the preceding 11 calendar months without waiting for FRED monthly release lags; and (2) require the sealed spec to document the exact fitted coefficients ($\beta_0, \beta_1, \beta_2$) on the 72c3371d snapshot so we confirm $\beta_2 < 0$ (or re-parameterize as $C_t$ and $C_t - M_t$).
* **Q4 (Where logged and shown):** **Amend.** Claude writes "not in LOG.md before the 2027 refit; not on the dashboard." Strike "before the 2027 refit" and make the exclusion from `LOG.md` and the dashboard permanent (until a council vote post-evaluation). `LOG.md` is user-facing in the repo; putting `p_hukommelse` there in September 2027 violates the distribution argument just as much as putting it there in November 2026.
* **Q5 (Evaluation):** **Amend.** Claude's draft leaves it ambiguous whether the 2-onset scored comparison includes pre-sealing historical data or is strictly prospective. Amend to explicitly state that the scored comparison uses *only* prospective origins logged from November 2026 onward, per RAADETS_2027 §8.3 ("no pre-2027 observation is ever used as evidence"), and specify the 4-quarter block length for $\text{SD}_{\text{block}}$.
* **Q6 (Start date Nov 2026):** **Keep as written.**

---

### C) Single Biggest Risk in My Proposal

**Statistical irrelevance due to low power and collinearity dilution.** By strictly enforcing RAADETS_2027 §8.3 (prospective evaluation only, requiring $\ge 2$ onsets) and locking $\lambda=1$ on two highly correlated features ($C_t$ and $M_t$), we face a dual trap. First, during inverted regimes, $C_t \approx M_t$, so L2 regularization splits the weight between them, tracks the curve-only model closely, and yields tiny log-loss differences ($d_t \approx 0$) for 90% of origins. Second, because $d_t$ only diverges during the brief window when the curve re-steepens after an inversion (roughly 2–4 quarters per cycle), achieving a $t$-statistic $> 1.96$ over just 2 prospective recessions is nearly impossible unless both recessions follow the exact 2007Q4 bull-steepening pattern and the model avoids false alarms in between. Consequently, we are likely building a shadow column that will sit in `hovedbog.jsonl` for 15 to 20 years without ever crossing the 1.96 $\text{SD}_{\text{block}}$ threshold, functioning merely as a disciplined bureaucratic archive rather than an actionable path to model improvement.

---

## Claude Fable 5.1 (Anthropic (independent instance))

## A) Agenda

**Q1 — Yes, but with the purpose stated honestly.** The draft sells the shadow as "the only evidence that can ever settle the question." It will not settle anything: with onsets arriving at ~1.5/decade and MDE80 ≈ 30 pp, two post-sealing onsets give a paired comparison with power near zero against any plausible effect. What a shadow row does buy is a pre-committed, time-stamped statement about *this* episode, made before its resolution, that cannot be reconstructed afterwards to fit the outcome. That is worth one ledger field. The context lines are not enough because they are prose; a number can be wrong in a way prose cannot. So: yes, with the spec saying in plain words that the shadow is a pre-registration, not a test with usable power.

**Q2 — Minimum-over-H (candidate a), H = 12, but not for the draft's reason.** "Pre-existing definition" is a weak tie-breaker: v4 tested `curve_min12`, did not choose it, and did not record why. A variable with an unrecorded negative result is not neutral, and the spec must say so. The defensible pin is structural: H equals the label horizon. The target is onset within 4 quarters; a feature that remembers exactly as far back as the label looks forward gives the model a 24-month span (12 back + 12 forward) over any inversion, covering E1's maximum 9-month lag with slack without being tuned to it. Candidates (b)–(d) are worse: (b) is undefined with no prior inversion and its cap is a free parameter; (c) throws away depth; (d) is depth × duration, which is exactly what makes 2022–24 extreme — choosing it now is choosing the variable that fires today. I accept that H = 12 is also chosen knowing E2; the difference is that the justification (label horizon) exists independent of E2 and would be the same argument if H = 12 read −1.2 today. The spec should also log the feature value `curve_min12` itself every row, so the record is reconstructible without the model. One definitional point the draft misses: E2 uses monthly GS10 − TB3MS; the live input is a trailing month of daily DGS10 − DTB3. The memory feature must be built from the same monthly aggregation `build_monthly` already uses for calibration — min over the last 12 calendar-month means of the operational spread, ≥ 6 months required, else null — or the shadow is two series pretending to be one.

**Q3 — Curve + `curve_min12`, standardised on the fit sample, λ = 1, same universe/labels/eligibility/refit.** Memory replacing curve is a different level model, not a memory test. Pre-register the expected sign: coefficient on standardised `curve_min12` negative. If the fit returns a positive or near-zero coefficient, log it anyway; no re-specification. Pre-2027 fitting is allowed and must be disclosed as contaminated by E1–E4, the grand review, yesterday's re-run, and the v4 grid — plus the item the draft omits: the operational sample already contains resolved zero labels for origins through 2025Q3 after the 2022–24 inversion, so the fit has partly seen the episode the shadow is meant to speak to. The spec should print, once, a second coefficient vector fitted on origins ≤ 2022Q3 as disclosure; only the full-sample fit is logged. Standardisation means/SDs frozen with the weights until each September refit.

**Q4 — `hovedbog.jsonl` only, two fields: `p_hukommelse` and `curve_min12`. Not LOG.md, not dashboard, before September 2027.** The distribution argument holds. The dashboard's existing unscored fields are variants of the *same* curve-only model; a second specification is a competitor and will be read as the "fixed" P the moment the two diverge. Transparency is served by publishing the sealed spec text, which is public, not by publishing the number.

**Q5 — Unscored tracking plus one pinned, two-sided bar, evaluated only once ≥ 2 post-sealing onsets have resolved labels.** Δ̄ = mean over all resolved post-sealing origins of [log-loss(shadow) − log-loss(curve-only)]; SE from a stationary bootstrap over those origins with mean block 8 quarters (the existing walk-forward convention); trigger if |Δ̄| > 1.96·SE. This is an agenda trigger, never a switch. Be explicit in the spec that with 2 onsets this bar will almost certainly not trigger either way — the scored comparison is there so the rule exists, not because it will decide. Separately, an unscored "onset scorecard": at each onset, record P and `p_hukommelse` at the last origin before onset, alongside the four historical rows (28.5/35.7/16.7/40.9). That table is the only thing anyone will actually read.

**Q6 — November 2026 row.** Waiting for September 2027 discards ten months of the one episode where the shadow's reading (+0.24, memory expired) and a hypothetical 36-month reading (−1.22) disagree most. If an onset arrives in 2027–28, it counts as post-sealing onset #1 for Q5; that is the whole point of sealing now.

## B) Verdict on Claude's draft

- **Q1 keep the decision, strike the justification.** Replace "builds the only evidence that can ever settle the question" with "pre-registers a falsifiable number for this episode; has no usable power."
- **Q2 keep `curve_min12`, strike "pre-existing definition" as the primary argument.** Replace with the label-horizon pin; disclose the unrecorded v4 result; pin the series and aggregation to the operational monthly spread; log the feature value.
- **Q3 keep, amend:** add sign pre-registration, frozen standardisation parameters, and the ≤ 2022Q3 disclosure fit.
- **Q4 keep as written,** plus the feature field.
- **Q5 amend:** "1.96·SD_block" is underspecified; pin the stationary-bootstrap SE over all resolved post-sealing origins and state that the bar is expected not to trigger. Add the onset scorecard.
- **Q6 keep.**

## C) Biggest risk in my proposal

The H = 12 pin. I have supplied a structural argument (horizon = label horizon), but I know the alternatives light up today and this one does not, and I cannot prove to myself that I would have reached for the same argument had H = 12 read −1.22. If an onset comes in 2027 and the shadow sat at 15 % beside P at 14.8 %, the council will be told — correctly in form — that it chose the one memory variable that could not have fired. The only defence is to put that exact sentence into the sealed spec now, with the E2 values beside it, so the choice is on record as made in full knowledge.

---

## Grok 4.7 (xAI)

Q1. No shadow probability. The inversion note, the P path, and the standing warning already state the facts a reader needs: inversion ended 2024-11, depth −1.57 pp, lag now 22 months against a historical maximum of 9, and P was below its peak before 6 of 8 onsets. A second logit does not add memory. It converts those facts into an unidentified probability. Walk-forward skill on the operational model is +20.37% with a 90% interval [−0.062, +0.172] nats; MDE80 on a paired skill gap is about 30 pp with 8 onsets. A memory coefficient estimated off roughly four post-re-steepening origins (2001, 2008, 2020, and a dubious 1990) cannot be told from zero. Logging it anyway manufactures a number that will be quoted before it has any evidential content.

Q2. If a state is logged at all, one variable: `curve_min12`, the v4 object, minimum of monthly GS10−TB3MS over the last 12 months, at least 6 observations. Pin: H is the smallest multiple of 12 that covers the maximum inversion-end-to-onset lag in E1, which is 9 months, so H=12. That rule uses 1966–2020, not the 2026 reading. Pre-existence is a valid tie-breaker against (b), (c), and (d), none of which has a definition that predates this sitting, and against H=24/36, which have no v4 object. It is not an absolution. Reject (b): any cap is chosen against a known 22. Reject (c): same H fork, and a binary drops depth that runs from −0.17 to −2.65. Reject (d): no pre-existing definition, and duration×depth is not identified on nine episodes. Claude’s sentence “every historical onset came within 9 months of an inversion’s end” is false: 1957, 1960, and 1990 had no ≥3-month inversion.

Q3. Do not fit. `curve_min12` is a state, not a regressor. Memory must not replace the curve. Pre-2027 data may not be used to estimate a memory coefficient in this item; there is nothing to estimate. Fallback only if Rasmus overrules Q1: same L2-logit, λ=1, intercept treatment, labels, eligibility, and universe as the operational model; design matrix extended by one column; both columns standardized on eligible training origins of that snapshot only (mean and sd from those origins, live row excluded); refit each September on the operational snapshot; never a standalone memory model. The spec must disclose that feature, horizon, and the decision to fit were fixed after E1–E4, the August review, and the October 2026 backtest, and that H=12 was already known to be +0.24 at the 2026-09 input. A coefficient from that fit is not evidence.

Q4. No dashboard. No LOG.md column before or after the 2027 refit. No field whose name or value is a probability — `p_hukommelse` is struck. Yesterday’s distribution point extends to `hovedbog.jsonl`: Rasmus reads it, and a second P in a file he reads becomes the real P in the next quote. If a state is logged, the field is `curve_min12`, a yield spread in percentage points, in `hovedbog.jsonl` only, marked unscored. The inversion note remains the user-facing memory.

Q5. This council seals no scored comparison and pins no bar. A 1.96·SD_block rule written today, after every historical onset and after E2, is a feature search with a lab coat on. §8.3’s “sealed before any onset it is judged on” is not satisfied by sealing the bar in the same sitting that shopped H. With two post-sealing onsets the test still cannot resolve a 30 pp gap; the bar would fire on one odd origin or never fire. A future council may seal a scored test. It must then pin one symmetric bar before any run, require ≥2 post-sealing onsets, say in the spec that two onsets will not settle it, and compare against curve-only on the same rows. No automatic switch. This text does not pre-write that bar.

Q6. Do not start a shadow in November 2026. As of 2026-09, `curve_min12` is +0.24. The 2022–24 inversion is already outside the window. A November row cannot record the memory this agenda is about; the episode under debate has expired for H=12. Starting then preserves a series that has forgotten the only open question — whether a lag past 9 months still binds — and it does so after we have seen that it forgot. A fitted fallback, if forced, waits for the September 2027 refit. It does not get a one-off coefficient on the current snapshot.

B. Claude, item by item.

Q1 strike. “Prospective” is doing false work. A probability fitted on all 12 onsets, with the feature chosen after the current lag was known, is not an experiment. The only prospective objects are post-sealing onsets, decades out, underpowered at MDE80 ≈ 30 pp. What a monthly `p_hukommelse` actually is, through 2026–27, is a monitoring number beside a live P of 14.8%. That is the use, and it is the use yesterday’s council refused.

Q2 amend the variable, strike the reason. Keep `curve_min12` and H=12 under the pin in Q2 above. Strike “today it holds no memory, so the shadow reads close to P” as a justification. That is selecting the horizon because E2 says it will not diverge from P during the anomalous lag. H=24 is −0.41 and H=36 is −1.22; preferring the silent one after seeing those three numbers is the forking path, whatever v4 called the object. Also strike the false claim that every onset followed an inversion within 9 months.

Q3 strike. No two-feature logit. The collinearity is structural: once the curve has been positive for 12 months, `curve_min12` is a lag of the same series, and the ridge at λ=1 will split one signal into two shrunk coefficients. The shadow will hug P except exactly when someone is tempted to quote it. Contamination disclosure in the draft is necessary but not sufficient; disclosure does not identify a coefficient on four origins.

Q4 amend. Placement restrictions (not dashboard, not LOG.md) are right and stay. The object is wrong. Log `curve_min12` or log nothing. A field named `p_*` is a second verdict regardless of the “unscored” tag.

Q5 strike the sealed bar. Keep, as a constraint on any future council, ≥2 post-sealing onsets, no automatic switch, and an explicit statement that the test is underpowered. Do not adopt 1.96·SD_block today.

Q6 strike. November 2026 is too late for H=12 to see the 2022–24 inversion and too early for a fit. The draft’s “before anyone knows how this cycle ends” does not apply: for this variable, the cycle’s memory has already ended.

C. Biggest risk in this proposal. The open empirical question is whether memory survives past 12 months, because 22 is already outside every historical lag and outside `curve_min12`. I refuse both a longer H and a fitted P, so this council records nothing that can speak to the question that put the item on the agenda. If a recession begins while the curve stays near +1.12 and `curve_min12` stays positive, the ledger will look exactly as it does now, and a later council will reopen this with the same post hoc pressure plus one more onset. That is the cost of not installing an unidentified second P. I accept it. Choosing H=24 or H=36 today, knowing they equal −0.41 and −1.22, would be worse: it would launder the current anomaly into the definition of memory.

---

## Kimi K3.1 Pro (Moonshot AI)

## Q1 — At all?

**Yes: build one shadow model, never alter P.** The context lines describe history but cannot estimate whether memory changes probability assessments; only a timestamped prospective record can. The motivation is entirely post hoc, which is acceptable for research instrumentation because no pre-sealing result will count as evidence and the operational model remains untouched.

## Q2 — Variable and horizon

Choose **(a), `curve_min12`, with H = 12**, implemented by the existing v4 code without another candidate run: \(m_t=\min(c_{t},c_{t-1},\ldots,c_{t-11})\) on monthly GS10 − TB3MS, requiring at least six observations only where the v4 historical-start rule requires it. Do not run H = 24/36 “sensitivities”; given E2, those would be selections informed by today’s value. Pre-existence is a valid **audit and implementation tie-breaker**, not statistical validation: this choice remains post hoc and is acceptable only for prospective tracking. Claude’s E1 claim is false as written—1957, 1960 and 1990 had no qualifying inversion, while some other onsets occurred during rather than after one—and today’s \(m_t=+0.24\) does **not** guarantee a shadow reading close to P after a joint refit.

## Q3 — Form and fitting

Use **curve plus memory**, not memory alone. For each fit vintage \(v\), calculate training-only means and population standard deviations, set \(z_{1t}=(c_t-\mu_{1v})/\sigma_{1v}\), \(z_{2t}=(m_t-\mu_{2v})/\sigma_{2v}\), and fit \(p_{H,t}=\operatorname{logit}^{-1}(\alpha+\beta_1z_{1t}+\beta_2z_{2t})\) by minimising
\[
\sum_{t\in T_v}\{\log(1+e^{\eta_t})-y_t\eta_t\}+\beta_1^2+\beta_2^2,
\]
with the intercept unpenalised and the operational calibration’s λ = 1 convention. Use the same universe, NBER-onset-within-four-quarters labels, eligibility rules, snapshot and R; initially fit on the operational calibration snapshot, then refit only on its September schedule, storing training cut-off, scalers, coefficients and code/data hashes for every vintage. Pre-2027 fitting is permitted under §8.3, but the sealed spec must explicitly disclose contamination from E1–E4, v4’s candidate, the grand review and yesterday’s backtest, and must state that none of it is validation.

## Q4 — Logging and display

Log `p_hukommelse` on every eligible `hovedbog.jsonl` row, together with \(m_t\), model vintage and missingness/eligibility status. Keep it out of LOG.md and the dashboard; the September 2027 refit must not automatically change that rule. Transparency comes from versioned public code, specification and reproducible ledger fields, not from publishing a second screenshot-able probability. This display decision is not evidence and requires no historical justification.

## Q5 — Evaluation

Begin with unscored tracking, but seal now **one** scored comparison after at least two NBER onsets dated after sealing; when the second occurs, fix the sample end at that quarter and wait four quarters for all labels to mature. Score eligible quarterly origins, not triple-counted monthly ledger rows, against a curve-only comparator fitted on the identical vintage, snapshot, penalty and schedule—otherwise memory is confounded with recalibration. For \(d_t=LL_{\text{curve},t}-LL_{\text{memory},t}\), where positive values favour memory and \(LL=-y\log p-(1-y)\log(1-p)\), compute \(\bar d\) and the standard deviation of its mean using 10,000 circular moving-block bootstrap replications with 16-quarter blocks and seed 20261028. The symmetric bar is \(|\bar d|>1.96\,SD_{\text{block}}\), in either direction, and crossing it opens a council agenda item—never a switch. September diagnostics remain descriptive with no repeated significance tests; two onsets satisfy the sealing rule’s eligibility minimum, not a claim of adequate power.

## Q6 — Start date

Start with the **November 2026 row**, after sealing the specification, code hash and initial fitted vintage before the 10–13 November logging window. Waiting until September 2027 sacrifices a year of prospective observations and removes none of the existing contamination. If NBER subsequently dates an onset on or before the sealing date, that episode remains tracking material rather than post-sealing evidence.

## Verdict on Claude’s draft

- **Keep Q1 and Q6 as written.**
- **Keep Q2’s variable and horizon, but amend its rationale:** pre-existence limits implementation forking; it supplies no confirming evidence. Strike the claims that E1 covers every onset and that today’s shadow must read close to P.
- **Amend Q3** with the exact fitting convention, vintage metadata and explicit leakage/contamination language above.
- **Amend Q4:** no automatic LOG.md or dashboard promotion at the 2027 refit.
- **Amend Q5:** use a matched curve-only vintage, quarterly origins, a fixed stopping rule and a numerical block procedure. Two onsets must not be marketed as a powerful test.
- **Strike no whole position**, but strike Q2’s two overclaims.

## Biggest risk in my proposal

The two-feature logit is underidentified: curve and its trailing minimum are highly collinear, and 12 onsets cannot reliably separate their effects. Consequently, early shadow deltas may be large and unstable, and a long prospective ledger could give those numerically precise but fragile outputs an authority the design cannot support.

---

## DeepSeek V4 Pro (DeepSeek)

## A) Positions on the agenda

**Q1 — At all?** Yes, a shadow model, but only as an unscored ledger field. The existing context lines are narrative; they cannot generate a likelihood or a future test. The question is whether the model should have memory, and the only honest way to answer that is to log a prospective, non-user-facing `p_hukommelse` with no role in P. This is not a second P; it is a data column that accumulates evidence. I accept it despite the post hoc motivation, because the decision costs almost nothing and does not touch the operational model.

**Q2 — Variable and horizon.** Use the pre-existing v4 definition:  
`curve_min12_t = min_{i=t−11,…,t}(DGS10_i − DTB3_i)`, observed monthly at the row’s latest month. I keep `H=12` solely because the definition predates E1/E2 and was part of the v4 grid. I reject H=24/36: E2 shows that choice would be picking today’s value, and no pre-registered rule justifies it. I reject candidates (b)–(d) because their thresholds or caps would now have to be chosen after seeing E1/E2. I accept the v4 tie-breaker only in its narrow form: `curve_min12` is a 12-month floor, not a duration memory. The spec must say that explicitly. Today it is +0.24, so the shadow will read near P; that is the honest consequence, not a bug.

**Q3 — Form and fitting.** Curve plus memory, not memory alone. Operational form stays two features: standardised curve and standardised `curve_min12`, L2 logit with λ=1, intercept, same universe and labels as P, quarterly origins 1947Q2 onward, 12 onsets. Standardisation uses the calibration sample mean and standard deviation frozen in the spec; coefficients are estimated on that sample and refit only at the September refit from the operational calibration’s snapshot and R, exactly as Claude proposes. Pre-2027 data may be used for fitting under §8.3, but only descriptively. The spec must disclose contamination from E1–E4, the grand review, and yesterday’s re-run. Formula:  
`p_hukommelse = logit⁻¹(β₀ + β₁·z_curve + β₂·z_curve_min12)`.

**Q4 — Where logged and shown.** Hovedbog only, as `p_hukommelse`, unscored, never on the dashboard, never in LOG.md before the September 2027 refit, and never presented next to P anywhere a screenshot can reach. This follows yesterday’s distribution argument. The field should be logged on the same row with the same curve vintage as P, and it is not revised. I keep Claude’s position as written.

**Q5 — Evaluation.** Unscored tracking now. A scored comparison happens only after at least two post-sealing onsets, and only against curve-only P on the same rows. I specify the bar exactly: compare mean paired log-loss per quarterly origin since sealing,  
`Δ = (1/N) Σᵢ [ −yᵢ ln p_shadow,ᵢ − (1−yᵢ) ln(1−p_shadow,ᵢ) + yᵢ ln p_P,ᵢ + (1−yᵢ) ln(1−p_P,ᵢ) ]`,  
with the difference computed shadow-minus-P so a positive value means shadow is worse. Use a moving-block bootstrap on the paired differences with block length 20 quarters; trigger an agenda item if `|mean Δ| > 1.96·SD_block`. Never an automatic switch. This is a pinned symmetric bar, but it is descriptive only until the onset count makes it informative.

**Q6 — Start date.** Start with the November 2026 row, log window 10–13 November, as Claude proposes. This begins the record before the current cycle resolves, which is the only way the record is prospective relative to this cycle. The spec must be sealed before that row is written.

## B) Verdict on Claude’s draft positions

- **Q1 — keep as written.** The framing is correct, and it respects the council lock that nothing changes P.
- **Q2 — keep the choice, amend the justification.** The v4 pre-existence is the valid tie-breaker, but Claude’s sentence that `curve_min12` “matches E1” overstates it. It is not the same as “every onset came within 9 months of an inversion’s end”; it is a rolling 12-month minimum. I would also add the disclosure that H=12 forgets the duration and depth of the 2022–24 inversion, so the shadow is a floor-memory model, not a full inversion-memory model.
- **Q3 — keep with amendments.** Add the exact standardisation and freeze the formula now. The refit schedule is acceptable, but the spec must state that all historical coefficients are contaminated and that no historical comparison is evidence.
- **Q4 — keep as written.**
- **Q5 — keep the unscored-then-scored structure, amend the bar.** Claude’s “beyond 1.96·SD_block” is too loose; I would pin the block bootstrap and the all-origin paired log-loss formula above.
- **Q6 — keep as written.**

## C) Single biggest risk in my own proposal

The biggest risk is that the shadow model is treated, later, as a real test of “memory” when it is not. With 12 onsets and a 12-month floor feature, `p_hukommelse` will differ from P largely through sampling noise and through a short-horizon floor that may not capture the mechanism the grand review actually named. If the current cycle resolves in a direction that makes the shadow look prescient, a future council may overweight a contaminated, underpowered result and push it toward P. Mitigation: keep it unscored, keep it off every user-facing surface, and require the council mandate and sealed prospective test before any scored comparison is even interpreted as evidence.

---

## Claude (Opus 5.5) (Anthropic — interested party, co-builder and secretary)

**Claude Opus 5.5 — Round 1 (interested party: I proposed this item).**

**A) The agenda**

**Q1 — yes, but only as a logged shadow, and I want the council to test whether even that is worth it.** The
context lines already tell the reader the inversion history. What they cannot do is accumulate evidence: a
shadow P written every month, before outcomes are known, is the only way the memory question can ever be settled,
and it costs nothing in P. The case against: with ≥ 2 post-sealing onsets needed, the record may take decades to
mean anything — but that is also true of the ledger itself, and the record is cheap.

**Q2 — `curve_min12` (rolling 12-month minimum of the monthly curve, ≥ 6 observations), as defined in
`calibrate.build_monthly` since v4.** Three reasons. (1) Least forking: its definition predates E1, E2 and this
debate; every other horizon would be chosen knowing what it shows today. (2) It agrees with E1: every historical
onset came during an inversion or within 9 months of its end, so a 12-month memory covers the documented window.
(3) Its consequence is uncomfortable and therefore honest: today it holds no inversion (+0.24), so the shadow will
read close to P. If the council prefers a longer horizon, it must say why on grounds that do not depend on E2 — and
it should know that 24 or 36 months would light the shadow up precisely in the one cycle (2022–24) that has
produced no recession so far. (b)–(d) all need extra choices (cap, threshold, area) made after E1/E2.

**Q3 — curve + curve_min12, both standardised, λ = 1;** the operational universe (1947Q2), labels, 18-month floor
and eligibility; fitted on the operational calibration's snapshot and R (2026-09-19, R = 2026-09) and refitted
with it every September. Not memory replacing curve: the question is whether memory adds to the level. Fitting on
pre-2027 data is allowed and the spec discloses the contamination: E1–E4, the grand review's diagnosis, yesterday's
backtest, and that v4 once fitted curve_min12 alone with an unrecorded result.

**Q4 — `hovedbog.jsonl` only (`p_hukommelse`, 6 decimals, plus the memory value), from the first row; not in
LOG.md before the 2027 refit (a column change mid-ledger needs its own decision); not on the dashboard.** The
distribution argument from yesterday applies with more force: a model designed in response to a backtest is
exactly the "real P" a screenshot would circulate. The September diagnostics print the tracking record.

**Q5 — unscored tracking; a scored comparison only after ≥ 2 onsets after sealing,** on identical rows against the
logged P, Δ log-loss with an episode-block SD; |Δ| > 1.96·SD_block either way is an agenda item, never a switch.

**Q6 — from the November 2026 row.** Starting before anyone knows how this cycle ends is the whole point.

**B) Verdict on my own draft** — I keep all of it. The weakest part is Q2's "pre-existing definition" tie-breaker:
it is procedural, not economic. If the council has an economic argument for a horizon that does not lean on E2, I
will move.

**C) The biggest risk** — that curve_min12 is a memory with no memory exactly when it matters: if the 2022–24 cycle
ends in a recession in 2027, a 12-month horizon will have been blind to it, and the record will say the shadow
"added nothing" for a reason we chose. The alternative risk is the mirror image, and E2 makes it visible: a
24-month horizon chosen today would read high now and be scored on the cycle that motivated it.
