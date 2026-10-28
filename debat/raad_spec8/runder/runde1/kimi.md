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