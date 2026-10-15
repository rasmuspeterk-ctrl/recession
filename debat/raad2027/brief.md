# COUNCIL BRIEF — MOTOR v5.0.1: the agenda for the September-2027 refit

## Who you are

You are one of seven members of an advisory council convened by Rasmus, a Danish solo developer, on 2026-10-15.
The council: **GPT-6.1 Sol Pro** (OpenAI), **Gemini 4 Argon** (Google), **Claude Fable 5.1** (Anthropic,
independent instance), **Grok 4.7** (xAI), **Kimi K3** (Moonshot AI), **DeepSeek V4 Pro** (DeepSeek), and
**Claude Opus 5.5** (Anthropic — co-built the model with Rasmus, ran the analyses below, wrote the draft
positions, and is the secretary; treat it as an interested party and attack its positions as hard as anyone
else's). You act as senior macro-econometricians. You advise; Rasmus decides. The debate ends when all seven
vote APPROVE on a consensus text.

## Ground rules (already ratified; not on the agenda)

- **Nothing changes P before the September-2027 refit.** Decisions taken now are preregistered: committed and
  pushed before the refit runs, effective from the refit (R = 2027-09). The weights in operation stay frozen
  until then (manifest 72c3371d).
- **Every number below is already known.** Any rule chosen now is chosen after seeing its effect. For each
  decision, say whether it is acceptable despite being post hoc, and why. Thresholds are never relaxed after
  the result is seen (Grok, v5.0.1 council R6).
- **The feature search is closed** (v5.0 council). Re-opening needs new economic rationale + council mandate +
  a sealed spec pushed before any run.
- **Curve-only is the operational model, locked by council decision** (RAADETS_V501 §6). The 5-feature model
  (F5: curve, realrate, dd, d_infl, cape_pct) is printed as a benchmark only.
- **The ledger** (LOG.md, UDFALD.csv, hovedbog.jsonl) has a preregistered scoring key (BEDOEMMELSESNOEGLE.md),
  pushed before row 4. Rows are never edited.

## The model in one paragraph

Label: NBER recession onset within the next 4 quarters, quarterly origins 1947Q2–, real-time labels from a
committed NBER announcement table with an 18-month floor; origins inside a recession are censored.
Model: curve-only L2-logit (10y − 3m spread, **fixed λ = 1** inherited from v4), standardised on the training
window. Frozen calibration 72c3371d (refit 2026-09 on snapshot 2026-09-19): w = [−2.0697, −1.4884],
n_obs 267 (48 positive), base rate 17.98 % (fit sample). Validation: purged expanding-origin walk-forward;
skill = log-loss improvement over the pooled base rate. Published: **curve-only +27.05 % (Brier +24.15 %) on
198 origins 1967Q4–2024Q1; F5 +23.16 %**; oracle-free supplement (all live-publishable origins) +20.37 % on 219.
Live input since 2026-09-28: trailing month of daily DGS10 − DTB3. An episode-block bootstrap gives a 10–90 %
"estimation-sensitivity band"; if it contains the base rate, the verdict is "not distinguishable from the base rate".

**Ledger so far** (one row per month, written before the outcome is known):
2026-08-12 P 20.1 % [14.4–29.2] curve +0.87 · 2026-09-09 P 18.0 % [12.7–26.3] +0.96 ·
2026-10-10 P 15.1 % [10.4–21.6] +1.11 — all "not distinguishable". Worst walk-forward false alarm: 93.8 % at
2023Q2 (no onset followed).

**Published prediction for the September-2027 refit** (F35, if NBER dates no peak before then): n_obs 267 → 271
(2024Q2–2025Q1, all label 0); β −1.295 → ≈ −1.18 per pp; P(+1.11) 15.1 → ≈ 14.8 %; walk-forward +27.1 → ≈ +21 %;
F5 ≈ +17 %, so curve-only stays operational.

## The evidence: seven analyses run 2026-10-15

All seven are deterministic, change nothing in operation, reproduce the published anchors exactly (72c3371d,
+27.05/198, +23.16), and were each re-computed by an independent verifier. Numbers below include the verifiers'
corrections.

### E1 — Nested λ and nested model selection (preregistered ablation9 + exploratory robustness)
- Preregistered (pushed before the run): curve-only **fixed λ = 1 +27.05 %**, **nested λ +18.32 %**
  (inner leave-one-episode-block-out CV, grid 0.1–100); F5 fixed +23.16 %, nested +7.34 %;
  **nested per-origin model selection +8.52 %** — the inner CV picks F5 in 100 % of origins from 2000.
  Predictions: nested curve-only in [+17, +25] held; selection ≤ nested curve held; "curve chosen in most
  origins from 2000" **falsified**.
- Robustness over 11 inner-CV designs: nested curve-only +17.96 … +23.35 %. 7 of the 11 are variants of the
  reference design; the two genuinely different families both lie above it (expanding 19.8–21.4; blocked k-fold
  19.9–22.2). Caveat: λ chosen on smaller inner folds over-penalises the full-window refit.
- Where nested loses: −9.4 pp in 1970s–80s origins (inner CV picks λ 30–100 in early windows where the curve
  had negative inner skill pre-1966); +2.6 pp in 2021Q4–2024Q1. Episode-block bootstrap (9 blocks): nested minus
  fixed −8.7 pp, SD 5.5 — not beyond 1.96 SD.
- **Every non-degenerate selector loses 9–10 pp vs nested curve-only**: argmin +8.52, MDE-gated +8.41, paired
  1-SE model rule +7.87, paired 1-SE λ +8.17/+9.18. The loss sits almost entirely in the 2022–24 false alarm
  (−11.0 pp); before 2021Q4 nested curve and nested F5 are equal (+30.3/+30.3).
- **F5's inner-CV advantage is carried by one block**: 6 training rows 1947Q2–1948Q3 (4 positive; post-war
  inflation without inversion) give 72–76 % of it (ratio of sums 75.7 %). Without that block F5's inner
  advantage (+1.7 pp) exceeds the 4.42 pp threshold in 0 % of origins.
- Correlation per origin between F5's inner-CV advantage and its realised advantage: Pearson −0.16.
- Today (R = 2026-09): CV picks λ = 3 for curve-only; every selection rule picks curve-only. P at curve +1.11:
  15.1 % (λ = 1, operation), 15.8 % (λ = 3), 18.2 % (λ = 30).

### E2 — Frequency gate (blueprint §2; review G1.3)
Blueprint §2 gates the monthly model on its **own** full monthly walk-forward; the ablation3 code gated on a
quarter-thinned score (months m%3==0). Requirement: monthly ≥ quarterly − 1 pp.
- v5.0.1 panel, curve-only: quarterly +27.05 % (198); **full monthly +29.24 % (591)**; thinned +26.03 % vs
  requirement 26.05 → literal reading: monthly primary; code reading: quarterly (fails by **0.02 pp**).
  The other two thinning phases pass (m%3==1 +32.13, m%3==2 +29.58).
- Across 6 cells (3 panels × F5/curve-only): the literal reading passes in all 6; the code reading fails in 4
  (passes only legacy curve-only, which is two cells). Only the quarter-end phase ever fails.
- Noise: thinned-minus-quarter differences −1.0 … −3.1 pp vs MDE 4.4–8.5. Full-minus-quarter +1.4 … +3.6 pp vs
  block-MDE 2.5–4.9; legacy curve-only +3.01 pp exceeds its MDE 2.54 (CI10–90 [+1.58, +4.67]); v5.0.1 curve-only
  +2.19 (MDE 2.99) has a CI excluding 0. Full monthly and quarterly are scored on different origin sets with
  their own pooled base rates; 591 overlapping 12-month windows are not 591 independent observations.
- Counterfactual monthly curve-only fit at R = 2026-09: n_obs 800, β −1.41/pp vs quarterly −1.29. P at today's
  live curve +1.12: monthly 14.4 % [9.3–20.9] vs quarterly 14.9 % [10.3–21.3].
- Note: the live input is already a monthly (trailing-month) reading; a monthly *fit* changes the slope, not
  the reading frequency.

### E3 — Universe start (review F34)
1947Q2 (protocol) includes 24 quarters using Shiller's LTR before GS10 starts (1953-04); pre-1960 fit origins
are 36.6 % positive vs 14.6 % after.
- Fit base rate 18.0 / 16.6 / 14.6 % and β −1.29 / −1.41 / −1.40 per pp at start 1947Q2 / 1953Q2 / 1960Q1.
- P at live curve +1.12: **14.9 / 12.4 / 10.4 %**; the band contains the base rate at every start → verdict
  word unchanged. (The paired-Δ supplementary rule says "distinguishable, below" at all three, as in October.)
- Walk-forward curve-only on own origins +27.05 (198) / +30.28 (178) / +21.89 % (158); on the 158 common
  origins (1980Q3–, only 5 of the 8 scored onsets) +20.5 / +21.4 / +21.9 %. Oracle-free +20.4 / +21.0 / +22.6 %.
- F5 is extremely start-sensitive: +23.16 / −0.73 / +3.71 % (p = 0.99 in 1978 without onset at 1953Q2 start;
  misses 1981 with p = 0.01 at 1960Q1). Gate difference −3.89 / −31.00 / −18.18 pp; the gate's own MDE 21–56 pp.

### E4 — Symmetric demotion (review G1.4)
Step 4 kept the 5 incumbents under an asymmetric rule (an incumbent fell only if *dropping* it gained
≥ +1/+1 pp; a challenger had to *add* ≥ +2/+2 pp, ≥ 80 % LOEO folds at level, sign stable).
- Incumbent-as-challenger (same A1/A2/A3 bar), v5.0.1 panel: add-effects curve +34.6/+38.6; realrate −1.45/−0.50;
  dd −0.60/−0.39; d_infl −4.43/+0.03; cape_pct **+4.11/+2.37 but only 5/8 folds at level** (needs 7/8).
  Simultaneous and backward elimination both end in **curve-only** (= the operational model), on both panels.
- Alternative symmetry ("same +2/+2 bar applied to the drop effect"): **nobody is demoted.** The outcome depends
  on which symmetry is chosen.
- A neutral LL rule gives curve+cape: +29.69 vs +27.05 % (dLL +2.64, dBrier +1.58) — fails v5.1's G2/G3/G5
  (pre-1990 −0.34 pp); below MDE 4.42 and far below the gate's own MDE (~13 pp).

### E5 — Ledger reference and power (scoring key §3; review G3.2/G3.5)
A monthly walk-forward replay of what the ledger would have shown 1968-09..2024-04 under the key's own rules
(one row per month, September refits with frozen rounded weights, logged base rate in force, P to 1 decimal):
- **Real-time censoring (engine's open-episode rule): +24.41 %** (Brier +22.22; 561 rows, 86 positive).
  **Without the USREC-vintage assumption** behind that rule (day-precise announcement, final trough):
  **+28.95 %**. **Oracle: +33.28 %** (583 rows). The whole drop 28.95 → 24.41 is 83 open-episode months,
  including the entire 1980-08..1981-05 run-up to the 1981 onset (10 positive rows, P up to 96.6 %).
- The key's rule (a) "logged base rate in force" is generous: the logged base rate averages 22.8 % over scored
  rows vs a realised onset rate of 15.3 % (early calibrations carry the 1948–61 era); pooled ex post: +21.2 %.
- The key's preregistered reference is **+20.4 %** (quarterly oracle-free supplement).
- Per cycle block (trough to trough), real-time skill +8 % (1970–75) to +59 % (2009–20); the open 2020-05..2024-03
  block (no onset, P up to 95 %) −494 %. Cluster-t over all 9 blocks 1.37 (oracle 1.85).
- **Power** (resampling the 9 blocks, 3000 sims): cluster-t reaches 80 % power at ≈ **150 calendar years of
  ledger** (≈ 131 years of scored rows), or ≈ 18 years if the 2020–24 false-alarm block is excluded from the
  resampling pool. The key's minimum of 3 complete cycle blocks is reached with probability 0.25 after 20 years.
  Naive iid tests and the key's 4.4 block bootstrap reject a true null 36–53 % of the time at 5–20 years.
  Parametric cross-check: 112–183 years. These are orders of magnitude, optimistic for the live ledger
  (oracle censoring; quarterly refits vs frozen weights).

### E6 — NBER content trigger (review G4.1)
Today a refit happens every September, plus when the NBER announcement table's hash changes. A content trigger
would also refit when `eligible_fit` at today's R contains a positive label (or relabel) the manifest lacks.
- Counterfactual 1977–2026, 6 onsets: the first positive origin matures 18–20 months after onset (9–15 after
  the peak announcement). The peak-announcement hash refit added 0 positives for its own onset in 6/6.
  Under the current rule, positives entered 0/4/6/8/0/0 months after maturing; 85 origin-months of delay total.
- Content trigger: 24 content-triggered refits, 6 coinciding with Septembers → **18 net extra refits in 49
  years**; 0 relabels (all peak lags ≤ 12 < floor 18). P difference at the actual curve: 53 of 588 months
  differ, mean |ΔP| 0.13 pp, max 1.05 pp.
- Projection (peak 2027-01, onset 2027-02, announced 2027-09-15): first positive label (2026Q1) matures
  2028-09 — a September, so it enters at the same time under all rules (+0.44 pp isolated). Second (2026Q2)
  matures 2028-12: content trigger refits then; current rule waits to 2029-09 (2029-01 if the trough is
  announced in time): 0.37 pp for 9 months. Delay is 0/3/6/9 months depending only on the onset month.

### E7 — Open items carried over
- **EBP / Baa-10y (review F37):** an open preregistration candidate, NOT in P. EBP (Fed Board, 1973–) is free
  but a model residual whose history may revise monthly (the reason NFCI was rejected); Baa-10y (1953–) is
  Moody's data that cannot be redistributed (local file only). The review has already *seen* EBP at onsets:
  high 12 months before 1990 and 2001 (+0.59/+0.58), low before 1980 (−0.31), 2008 (−0.51) and 2020 (−0.10).
  Gate MDE ≈ 4.4 pp; only ~3 EBP onsets before 1990.
- **L_R audit interpretation (review):** the annual audit of the announcement lag uses peak announcements
  measured from the peak (code today → L_R = 18 = floor). Including trough announcements (lags 20–21 in 1991,
  2001) would lift L_R to 21 and change the eligible origins. Must be fixed before the audit first runs.
- **Gate threshold (review F8):** the decision rule uses a borrowed 4.42 pp (the frequency test's MDE); the
  gate's own MDE is 21.06 pp.
- **Operational changes made without mandate (F29), for ratification:** live curve = trailing month of daily
  DGS10 − DTB3 instead of the latest published monthly GS10 − TB3MS (row 3 onward; every row from row 4 also
  carries P on the monthly figure); swarm tripwires moved out of the ignition column (restoring an R3 decision);
  log day = first weekday from the 10th + 3 days (in the preregistered key); live censoring of readings inside
  an announced recession.

## AGENDA — answer every question

- **Q1 (λ).** At the 2027 refit: keep fixed λ = 1, switch to nested CV-selected λ, or something else? Which skill
  number is the headline from then on (fixed-λ +27.1 %, nested +18.3 %, oracle-free +20.4 %)?
- **Q2 (model selection and the gate).** Blueprint §4's nested selection would have chosen the worse model.
  Amend §4 formally? What does the F5 benchmark gate decide from 2027, and against which threshold
  (borrowed 4.42 pp, own MDE ≈ 21 pp, both)?
- **Q3 (frequency).** Quarterly or monthly fit from 2027, given both readings of §2 are now known?
- **Q4 (universe start).** Keep 1947Q2, or move to 1953Q2/1960Q1?
- **Q5 (demotion).** What, if anything, follows from E4 — for documentation, for the F5 benchmark, for any
  future search?
- **Q6 (content trigger).** Adopt the content trigger from the 2027 refit, or keep September + hash?
- **Q7 (ledger key).** Does anything in E5 justify amending the preregistered key (reference, base-rate rule,
  censoring, minimum blocks), or only a published supplement? How should the power result be stated publicly?
- **Q8 (EBP/Baa).** Open a sealed test before 2027, defer, or close?
- **Q9 (L_R).** Peak-only or all announcements?
- **Q10 (ratification).** Ratify the F29 changes, individually?

## Claude's draft positions under debate

- **D1.** Keep λ = 1 as a fixed protocol constant and formally amend blueprint §3 ("λ fixed, not selected").
  With 9–13 episode blocks inner CV cannot select λ reliably (design-dependent λ, early windows pick 30–100,
  bootstrap difference within 2 SD). From 2027 every skill statement prints the pair "fixed-λ +x % / nested
  +y %", and the oracle-free figure beside it. Weakness I concede: λ = 1 came from v4, built on overlapping
  history, so "fixed a priori" is only partly true.
- **D2.** Amend §4: curve-only is operational by council decision, not by per-origin selection; no selector is
  run. F5 stays as a printed benchmark. The gate becomes two-tier and never switches anything: |Δ| > 4.42 pp
  → put on the next council agenda; |Δ| > the gate's own MDE → stated as evidence.
- **D3.** Keep the quarterly fit. Both readings are known, so either choice is post hoc; the status quo wins a
  tie, and the timeliness argument for §2 is already met by the monthly live input. Record G1.3 as
  "readings disagree, status quo retained", with both outcomes published.
- **D4.** Keep 1947Q2 (a locked constant; moving it now would be chosen knowing it lowers P by 2.5–4.5 pp).
  Print the start-sensitivity line permanently.
- **D5.** Nothing in operation. Document that "5 incumbents pass" holds only under the asymmetric rule. Any
  future search (if ever mandated) uses one symmetric bar for incumbents and challengers, fixed in the sealed spec.
- **D6.** Adopt the content trigger from the 2027 refit (September + hash + content). It is mechanical,
  removes a 0–9-month lag that depended on when NBER happens to announce troughs, and costs ~18 extra refits
  per 49 years.
- **D7.** Do not amend the key (it was preregistered before row 4). Publish E5 as a supplement with all three
  censoring variants side by side. State publicly: the ledger cannot reach a verdict with 80 % power within any
  practical horizon; it is an honesty instrument, not a test.
- **D8.** Defer. No sealed test before 2027: contamination (onset values seen), EBP revision risk unaudited,
  Baa not redistributable, power too low (MDE ≈ 4.4 pp with 8 onsets). Re-examine only after ≥ 12 monthly EBP
  snapshots show its history does not revise.
- **D9.** Peak-only: the label is the onset; trough announcements do not determine onset labels.
- **D10.** Ratify all four F29 changes.
