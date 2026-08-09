# KIMI K3 — ROUND 1 PROPOSAL

## A) Verdict on v4 architecture

- **LAG 1:** Keep the engine (L2 logit). Change the label to NBER, go monthly, kill the p9 = 1−Π(1−p_h) combination.
- **LAG 2:** Keep as checklist, but strip the bucket percentages — in-sample frequencies on ~11 episodes printed as "14% / 38% / 56%" is pseudo-validation wearing a lab coat.
- **LAG 3:** Keep as flags. Hard rule: flag counts must never enter probability language, not even in the verdict.
- **Verdict layer:** Keep. Must print an uncertainty band and benchmark deltas; no decimal points without a band attached.

## B) Q1–Q8

**Q1 — Label.** Switch to NBER (USREC). It is what users mean by "recession," it adds 2001 (12 episodes), and it is *never revised* — which deletes the GDP-vintage look-ahead entirely. The 2022 problem disappears (NBER: no recession). Declared late, but dates are final, so training labels are stable; the live task becomes "NBER will date a recession within 12m," same convention as the NY Fed. Hybrid = two labels = two models: rejected.

**Q2 — Frequency/horizon.** Monthly. ~780 obs 1960–2026; episodes stay ~12, so the gain is calibration precision, not new events. Two direct models: 3m and 12m-ahead-anytime labels. Kill the product rule: horizon events are nested, so independence is false; direct labels need no assumption.

**Q3 — Features.** Cap at 5; ~12 episodes with shrinkage cannot honestly support more. Current 5 stay as incumbent. Pre-registered ladder: one candidate at a time — Sahm, initial claims, ACM-adjusted curve — admitted only on ≥2% relative walk-forward log-loss gain AND sign stability across episode-blocked folds. HY OAS rejected as a feature (1997+ = 3 episodes). Note: Sahm/claims are near-term signals; expect them to help the 3m model, not the 12m. Horizons may legitimately carry different feature sets.

**Q4 — Statistics.** L2 logit stays. GBM or Markov-switching on 12 events is curve-fitting by construction; Bayesian logit ≈ L2 with extra machinery. Add episode-blocked bootstrap (resample the 12 episodes, 1000 draws): CIs on skill scores and a 10–90% band on the live probability. Report episode-level skill (max p per episode vs. outcome) alongside monthly log-loss — this is the correction for overlapping labels.

**Q5 — Regime instability.** Test the ACM-adjusted curve (10y − ACM term premium − 3m; free from NY Fed, 1961+) as a straight swap, pre-registered: it must improve *full-sample* walk-forward, not just 2023. My prior: it fails — term-premium estimates are model-laden and themselves revised. Default: keep the raw curve, carry the 2023 error in the verdict text. No balance-sheet feature: collinear with the curve, no walk-forward case.

**Q6 — Architecture.** The layering is sound — it *is* the honesty firewall. The flaw is presentation, not structure. Fix by labeling (every unvalidated "%" gets "in-sample, n≈11" attached), not integration: flags-as-ensemble-member on 12 episodes fails the walk-forward rule on arrival.

**Q7 — Data/ops.** Automate. FRED serves CSVs without an API key (`fredgraph.csv?id=...`); urllib + numpy suffices. ~10 of 12 inputs are FRED; CAPE and margin debt stay manual with fallback. **Skip ALFRED**: with a USREC label and unrevised market/rate/survey series, vintage risk shrinks to CPI seasonal revisions — immaterial. Simplicity stops paying when transcription-error risk exceeds maintenance burden; at 12 manual numbers, we are there.

**Q8 — Output/benchmarks.** Report p_3m, p_12m with band, flags, verdict, plus a benchmark table: NY Fed probit, real-time Sahm, Chauvet–Piger (all free). The bar is not "beat" — 12 episodes cannot establish superiority statistically — it is "not dominated": walk-forward log-loss within the bootstrap band of the curve-only probit. If one series matches us, the extra features aren't paying, and the output must say so.

## C) Top-3 changes, ranked

1. **Label/frequency switch (USREC, monthly).** Test: identical 5-feature walk-forward 1960–2024 on the new label; accept if log-loss improvement ≥ +20% (no material degradation) AND 2001 max p ≥ 2× base rate in the 12 months prior. Fail → stay quarterly/technical.
2. **Pre-registered feature ladder: Sahm, claims, ACM-curve swap, one at a time vs. incumbent.** Admit on ≥2% relative walk-forward gain + sign stability across episode-blocked folds. Anything admitted enters the model; everything else is labeled checklist.
3. **Episode-block bootstrap band + episode-level skill metric.** Test: band calibration in walk-forward (outcomes inside the 10–90% band ≈80% of months). This converts "8.8% vs. 13.4% is not statistically certain" from a caveat into a printed number — likely something like 8.8% [4–19%], visibly overlapping base.

## D) Biggest risk in my own proposal

The label/frequency switch reopens the garden of forking paths: the five features earned their place on the *quarterly technical* label, and the walk-forward has only ~12 events of power to re-arbitrate every decision I'm demanding of it. Monthly 12m-ahead labels also overlap ~12 months per episode, mechanically inflating apparent skill. If episode-level metrics are not enforced from day one, v5 can look *better* validated than v4 while being worse. Mitigation: run both labels in parallel for 12 months and report both skills before retiring the old one.