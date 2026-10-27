# ROUND1 — samlet


---

## GPT-6.1 Sol Pro (OpenAI)

## A) Agenda decisions

### Q1 — Part A: approve only after amendment

The formula is correct for a **synthetic 91-day bill’s ACT/365 simple investment yield**, not an exact reconstruction of CMT: use \(b(d)=365d/(360-91d/100)\), with both \(b\) and \(d\) expressed in percentage points, converting both TB3MS and DTB3 without splicing GS3M. Call the resulting feature “91-day BEY proxy”; converting a monthly average discount yield is also not identical to averaging converted daily yields. Amend the uncertainty output to **10,000 paired episode-block draws, seed 42, a 5th–95th percentile interval**, with block construction pinned and identical resamples for both configurations; reproduce all three existing evaluation protocols, and hash the diagnostic inputs and outputs even though they remain outside the production manifest. The convention mismatch is a measurement limitation, not evidence that the consistently estimated discount-basis model is invalid, so nothing changes before the refit and any later switch requires its own sealed replay. This post-hoc diagnostic is acceptable because it is disclosed, published regardless of outcome, and cannot select an operational configuration; Claude’s predicted two-percentage-point bound must not become an acceptance criterion.

### Q2 — Part B: B3 only; no historical reopening

Reject B1/B2 and authorize only a separately sealed prospective tracking protocol, contingent on the revision audit and the existing context firewall. E3 tested an implementation that combined a different feature specification, an F5 baseline, and a missing-history fallback: it did **not** isolate the expectations hypothesis, but that does not restore an untouched historical test after the result and literature have been inspected. I disagree with declaring ACM *permanently* closed by analogy: §8.2 explicitly makes that determination for EBP, while ACM’s governing rule is a closed search requiring a fresh council mandate, which I decline to grant. B1/B2’s proposed symmetric threshold does not solve the two-candidate multiplicity or retrospectively selected common-panel problems, and would not support a nominal confirmatory claim. B3 is acceptable despite its post-hoc motivation only as unscored prospective tracking, with no pre-2027 performance evidence and no scored assessment before two post-sealing onsets.

### Q3 — C5 and C6: amend both

C5’s claim that the entire gap “is convention” is false: converted DTB3 and CMT still differ because they represent different instruments and construction methods. Replace C5 with: **“The model uses discount-basis TB3MS for calibration and DTB3 live; the same-window CMT spread is +0.95 pp, versus +1.12 pp for the operational spread. This difference reflects yield quotation conventions and instrument/construction differences. Substituting CMT into the frozen coefficients would change the input definition; a separately sealed sensitivity is proposed for 2027.”** Replace C6 with: **“Context only: Kim–Wright estimates for 16 October decompose the 5.09% ten-year yield into a 0.99-percentage-point term premium and a 4.10% expected-rate component. These are model-dependent, revisable estimates, not an independently validated recession signal for this model; they do not alter P, its band, or its verdict. A previous ACM-adjusted specification was rejected in the closed feature search; that evaluation included a missing-history fallback.”** Delete the 98% headline, the mixed-convention residuals, and the categorical literature claim: their arithmetic or provenance does not validate their use as a counter-signal to P. These post-hoc corrections are acceptable because they remove misleading interpretation rather than introduce a selected forecasting claim.

### Q4 — C1–C4 and C7: conditional ratification, not blanket approval

Ratify C1’s disclosed post-hoc 5 bp deadband **only for steepening/flattening terminology**; inside it, print “curve change below 5 bp” plus the two leg changes, since “parallel shift” asserts more than a small spread change establishes. Amend C2 to print the complete required sentence, not merely an oracle-free cross-reference: **“Walk-forward skill is +20.37% over 219 origins using oracle-free fixed λ, +27.05% over 198 origins using oracle-censored fixed λ, and +18.32% over 198 origins using nested λ with oracle censoring; power is limited by the small number of recession episodes.”** Ratify C3, but amend C4 to say only “first seen by us [date]; BEA advance-release vintage not verified,” unless actual BEA release metadata establish the vintage—the quarter-end-plus-42-day heuristic cannot do that. **Do not ratify C7:** its F5/curve-only labels reverse the attribution in the brief’s verified gate calculation, so reconcile them against named replay artifacts before publication. The historical paired-loss interval may follow the complete skill sentence, explicitly labelled “oracle-censored, 198 origins, nine cycle blocks, 90% interval”; describe the 8.9% as a bootstrap draw share, not a p-value. These are acceptable post-hoc presentation repairs only after those corrections, with no retrospective ledger edits.

### Q5 — verdict wording: clarify the dashboard, preserve the ledger

Keep the sealed verdict and ledger wording unchanged, but use **“Not distinguishable under the primary band rule”** on the dashboard, followed by **“The paired-difference supplement places P below the base rate; it does not determine the verdict.”** Reject “no robust signal”: robustness across methods has not been established, and the two methods actually disagree here. The band rule is more conservative on the examined 198-origin sample, but that does not establish superior calibration or justify describing it as a paired hypothesis test. This post-hoc explanation is acceptable because it clarifies the existing rule without changing classifications, scoring, or historical records.

## B) Verdict on Claude’s positions

- **Q1 — Amend.** Keep convert-both, no CMT splice, unconditional publication, and no automatic switch. Add the proxy terminology, reproducible diagnostic artifacts and explicit bootstrap specification above; do not use the numerical prediction as a gate.
- **Q2 — Amend.** Keep B3 only and the revision-audit requirement. Strike the claim that ACM has EBP’s explicit permanent prohibition; retain the practical decision not to reopen historical testing.
- **Q3 — Reject as written.** C5 must acknowledge instrument/construction differences. Replace C6 rather than preserving a selectively persuasive 98% statistic and a categorical predictive interpretation.
- **Q4 — Reject blanket ratification.** C2 is incomplete, C4’s heuristic does not identify a release vintage, and C7 contains an unresolved attribution contradiction. C1 and C3 survive with the qualifications above.
- **Q5 — Amend.** Preserve the primary rule and ledger wording; clarify what the dashboard’s verdict actually means.

## C) Biggest risk in my proposal

**B3 could become a shadow forecasting model:** readers may treat a regularly displayed expectations component as an unofficial correction to P despite the firewall. The mitigation is strict: no directional recession interpretation, thresholds, counts, retrospective success anecdotes, or placement suggesting that it overrides the operational forecast.

---

## Gemini 4 Argon (Google)

### A) Agenda Answers

**Q1 — Part A (3m Convention Sensitivity)**
Seal Part A for the September 2027 refit, but elevate its decision rule from an unscored sensitivity to a pre-committed non-inferiority switch. Comparing a bond-equivalent 10-year yield to a money-market discount 3-month rate is a unit-of-account error that introduces a non-linear level bias of up to 81 bp in the 1979–1982 Volcker era (4 of our 12 onsets). The conversion formula $\text{BEY}(d) = \frac{365 \cdot d}{360 - 0.91 \cdot d}$ (with $d$ in percent) applied uniformly to `TB3MS` and `DTB3` from 1934 onward is exact and avoids the structural break of splicing `GS3M` in 1981-09. However, Claude’s proposal to leave the switch to an unguided 2027 council vote invites post-hoc rationalization. Instead, seal a binding decision rule now: at the 2027 refit, we switch the operational model to `Curve_BEY` (with its own full sealed replay per §1.3) unless `Curve_BEY` is demonstrably inferior to `Curve_discount` on the oracle-free walk-forward path, defined as $\Delta \text{skill}_{\text{OF}}(\text{BEY} - \text{disc}) < -0.50\text{ pp}$. Fixing a mathematical bug does not require the corrected series to beat the buggy series; it only requires that fixing the bug does not break the model.

**Q2 — Part B (Expectations Component)**
Reject B1 and B2 permanently; adopt B3 strictly as an unscored context series and future tracking column under §8.3. While the step-4 test (`ablation4_features.py`, dLL $-77.88\text{ pp}$) was badly designed because it imputed the base rate prior to 1961 inside a 5-feature model, we cannot run a "clean" 1961–2026 historical test now. Why? Because Rosenberg & Maurer (2008) was published using 1961–2008 data, and we are proposing this test specifically because we observed the 2023 false alarm and the current 2026 term-premium surge—meaning the entire historical path is doubly contaminated. Furthermore, with 8 onsets since 1961, the minimum detectable effect at 80% power is $\sim 30\text{ pp}$ of log-loss skill, making a $1.96 \cdot \text{SD}_{\text{block}}$ hurdle statistical theater that is guaranteed to yield an uninformative null. Under B3, track Kim-Wright (`THREEFYTP10`) in context and subject it to the $\ge 12$-snapshot revision audit before adding it as an unscored ledger column; because affine term-structure models re-estimate parameters across the full sample, historical back-revisions must be quantified first.

**Q3 — C5 and C6 (Convention Note and Expectations Warning)**
Keep C5 with one amendment, and heavily rewrite C6. In C5, strike the last clause (*"a sensitivity test is proposed... requires the council's mandate"*) and replace it with *"the council has sealed a bond-equivalent conversion test for the September 2027 refit (spec2027/7)"* once ratified. C6, as committed by Claude in `2e22ac5`, is a blatant violation of the firewall’s spirit: citing a single day’s Kim-Wright decomposition ("98% of the curve that day is term premium") alongside Rosenberg-Maurer (2008) is a rhetorical nudge telling the user that $P = 14.8\%$ is an underestimate and the "true" recession probability is near the flat-curve base rate ($\sim 42\%$). Amend C6 by stripping the "98%" ratio, the Rosenberg-Maurer endorsement, and the step-4 excuse, reducing it to neutral, two-model factual reporting:
> *"Curve decomposition (context, not in P): Affine models split the 10Y yield into expected short rates and a term premium, which is model-dependent and subject to historical revision (Kim-Wright 10Y TP: +0.99pp on 2026-10-16; NY Fed ACM: +0.84pp in 2026-07). Subtracting the Kim-Wright TP leaves an expectations spread of +0.02pp vs DTB3 (−0.16pp vs DGS3MO). Term-premium adjustments were rejected in pre-registration and are not used in the model."*

**Q4 — C1–C4 and C7 (Presentation Fixes of 2026-10-27)**
Ratify C1, C2, C3, and C4 ex post; amend C7. C1’s 5 bp threshold (`MAERKE_MIN_DK`) was chosen post hoc after seeing $+1.4\text{ bp}$, which is poor process, but labeling $+1.4\text{ bp}$ as "bear steepening" is substantively misleading; 5 bp is standard market convention for a flat curve move and cannot touch $P$, the band, or the ledger. C2, C3, and C4 fix genuine reporting errors verified by the external reviews. However, C7’s placement of the paired loss-bootstrap interval ($+0.120\text{ nats}$, 90% CI $[-0.042; +0.239]$, computed on the 198-origin *oracle-censored* set) directly beneath the §1.2 sentence violates §1.2’s mandate that the oracle-free walk-forward ($+20.37\%$, 219 origins) must lead. Printing an uncertainty interval only for the $+27.05\%$ oracle-censored figure implicitly elevates it as the primary metric. Amend C7 to compute and print the episode-block paired loss bootstrap for **both** the 219-origin oracle-free path and the 198-origin oracle-censored path, in §1.2 order.

**Q5 — Verdict Wording**
Leave the verdict wording unchanged everywhere: *"not distinguishable"* (Danish: *ikke skelnelig*) stays in the verdict, the ledger, and the dashboard text. Review 2 proved that the band rule and paired rule disagree on 12/198 historical origins (including today, where the paired difference is $[-6.5; -0.4]\text{ pp}$), and in all 12 cases the band rule is more conservative. Changing the dashboard prose to *"no robust signal under the band rule"* when the paired supplement is already printed on the very next line is redundant and introduces terminology drift between the dashboard and `BEDOEMMELSESNOEGLE.md`. The clean solution is already in place: the band rule governs the verdict, and the paired supplement is printed right next to it for full transparency.

---

### B) Verdict on Claude’s Draft Positions

*   **Q1 (Part A):** **Amend.** Keep the 91-day BEY formula applied to both `TB3MS` and `DTB3` (no CMT splice). Strike the open-ended decision rule and the pointless preregistered guess ($|\Delta| < 2\text{ pp}$); replace with a binding non-inferiority switch rule ($\Delta \text{skill}_{\text{OF}} \ge -0.50\text{ pp}$) executed at the September 2027 refit.
*   **Q2 (Part B):** **Keep.** Close historical testing permanently (reject B1/B2); proceed with B3 only (`THREEFYTP10` in context, 12-snapshot revision audit before any unscored ledger column).
*   **Q3 (C5/C6):** **Amend C5 slightly; strike and rewrite C6.** Claude's proposed amendment to C6 keeps the "98%" figure, the Rosenberg-Maurer citation, and the step-4 rationalizations. Strike all three and use the strictly neutral text provided in A.Q3 above.
*   **Q4 (C1–C4, C7):** **Keep C1–C4; amend C7.** Require C7 to report the paired loss-bootstrap interval for the 219-origin oracle-free walk-forward first, before the 198-origin oracle-censored interval.
*   **Q5 (Verdict wording):** **Keep.** No change to *"not distinguishable"*.

---

### C) Single Biggest Risk in My Proposal

**The pre-committed non-inferiority switch to `Curve_BEY` in Q1 risks degrading out-of-sample calibration if the discount-basis distortion was accidentally acting as a helpful non-linear transformation during the 1970s/1980s.** Because $P = \text{logit}^{-1}(\beta_0 + \beta_1 \cdot \text{curve})$ is strictly linear in the spread inside the log-odds, the $\sim 50\text{–}81\text{ bp}$ compression of `TB3MS` relative to `BEY` at double-digit interest rates effectively muted the depth of the 1973, 1980, and 1981 inversions unless the slope coefficient $\beta_1$ adjusted to compensate. If high nominal inflation regimes genuinely require a different effective slope than low-rate regimes, removing the discount-rate artifact via a $-0.50\text{ pp}$ non-inferiority gate could slightly worsen log-loss calibration in low-rate regimes even while fixing the theoretical unit-of-account error.

---

## Claude Fable 5.1 (Anthropic (independent instance))

**Round 1 — Claude Fable 5.1**

**A) Agenda**

**Q1 — Part A.** Seal it, with three amendments. The formula is the standard Treasury BEY for bills ≤ 182 days; 91 fixed days is fine (actual maturities vary ±1–2 days, effect < 0.5 bp). Convert both TB3MS and DTB3; never splice GS3M — a splice puts a 0.08 pp level break at 1981-09 (E1's instrument/fitting difference) into the one series the model reads. Amendment 1: disclose that BEY(mean of daily d) ≠ mean of daily BEY(d) (Jensen; convexity of the formula), and compute the daily DTB3 version as mean-of-converted so the live input matches the pinned procedure; quantify the monthly-average bias once on 1954–2026 and print it. Amendment 2: preregister the arithmetic as well as the skill prediction: at d ≈ 4 %, gap 0.10 pp → ΔP ≈ −1.6 pp at today's input; at the 1980–81 inversions (d 12–15 %) the discount curve is overstated by 0.55–0.81 pp, i.e. inversions were *deeper* than the model saw. I accept |Δ walk-forward| < 2 pp as the preregistered band but expect a small positive sign (deeper 1970s–80s inversions, less steep 1980s recoveries); write the sign down so it cannot be claimed afterwards. Is the convention a defect? Yes, a measurement defect, but a self-consistent one: the weights were estimated on the same mismeasured series, so P today is internally coherent. It is not worth breaking the frozen weights or §1.3 over ~1.6 pp; the unscored sensitivity is the right instrument, and the switch decision belongs to the 2027 refit council. Post hoc status: the issue surfaced from a review of today's reading, but the sensitivity cannot touch P — acceptable.

**Q2 — Part B.** B3 only, but Claude's justification is the wrong one and the spec must say so. The EBP analogy is weak: EBP was closed because its *onset pattern* was seen; the step-4 ACM test, by Claude's own admission, never isolated the expectations hypothesis — it measured a missing-history penalty. The decisive argument is power, not contamination: a common panel from 1961Q3 with 8 onsets gives MDE80 ≈ 30 pp of skill, so B1/B2 would return "no difference" whatever the truth, and a result that cannot inform a decision should not be run — not even as a declared second shot. The spec must state verbatim: "E3's −77.88 pp is a result on an implementation, not on the hypothesis; it is not evidence against the expectations component." Otherwise a future council will cite the number as a rejection. For B3: the context line prints *both* estimates (KW daily, ACM monthly-lagged) with their dates, not THREEFYTP10 alone — E2 shows a 0.15 pp disagreement between them on a 1.0 pp curve. The ≥ 12-snapshot revision audit: archive the full ACMTP10/THREEFYTP10 series monthly, report max |revision| of each month's TP over the trailing 24 months across vintages; the unscored column opens only if the audited revision is < 10 bp, which the spec pins now.

**Q3 — C5/C6.** C5: amend one sentence. "The gap (0.18pp) is convention, not data" is wrong by E1's own arithmetic: at d = 4.04, the convention gap is 0.10 pp; the remaining 0.08 pp is DGS3MO vs converted DTB3 — different instruments and curve fitting. Text: "Of the 0.18pp gap, 0.10pp is the discount→BEY convention; 0.08pp is instrument/fitting (DGS3MO vs DTB3). Neither is data error." C6: amend harder than Claude proposes. As written it is a directional claim on P — "the predictive part of the curve is ~0, so P is understated" — sourced from one term-structure model on one day, with the literature cited as authority. No other context line (EBP, Sahm, claims) carries a "the literature says this predicts recessions" sentence; C6 should not either. Strike the Rosenberg-Maurer sentence and the "98 %" framing; fix the rejection sentence. Text: "Curve decomposition (model-dependent, revised ex post): KW 2026-10-16 TP 0.99, expectations 4.10; ACM 2026-07 TP 0.84 (0.51 in 2026-06). The model reads only the sum. A feature using the ACM-adjusted curve was tested in step 4; the result (−77.9pp) measured mainly the pre-1961 panel penalty, not the hypothesis. Closed list; prospective proposal in spec2027/udkast/7. Not in P." The firewall is only honest if context lines are numbers, not arguments.

**Q4 — C1–C4, C7.** C1–C4: ratify ex post. 5 bp is post hoc and cosmetic; any threshold in 2–10 bp would have relabelled today's +1.4 bp, it cannot move P, and 5 bp ≈ 0.8 pp of P is a sensible "indistinguishable from noise" scale — disclose and keep. C7: amend. Printing the 198-origin paired-loss interval (+0.120 nats, +27.1 %) directly under the §1.2 sentence gives the oracle-censored figure the only uncertainty band on the page, so the eye reads +27 % [−4; +24 nats-equivalent] as the headline — a §1.2-spirit breach even if the sentence order is kept. Fix: compute the same episode-block paired bootstrap (1000 draws, seed 42, cycle blocks) on the oracle-free 219-origin set and print both intervals in §1.2 order; this is a diagnostic on existing predictions, touches nothing frozen, and is acceptable pre-refit. Until it exists, label the 198 interval "oracle-censored set; oracle-free interval pending". Also add the plain fact: lower bound < 0, 8.9 % of draws ≤ 0 — one-sided p ≈ 0.09 with 9 blocks; the historical skill is not robust at conventional levels and the dashboard should say so. The gate line "F5 +23.2 % vs curve-only +27.1 %" must carry "(oracle-censored full path; oracle-free headline +20.37 %)".

**Q5 — verdict wording.** Leave it. "No robust signal under the band rule" is a *different* claim — it reads as "nothing is happening", whereas "not distinguishable from the base rate" correctly says the model cannot separate 14.8 % from 18 % (2007Q4 read 16.7 %, same verdict, onset next month). Keep the paired supplement visible whenever it disagrees, with the 12/198 historical disagreement rate stated; the ledger key is not amended.

**B) Verdict on Claude's draft positions**

- Q1: keep, amended (Jensen/mean-of-converted; preregistered sign + ΔP ≈ −1.6 pp arithmetic).
- Q2: keep B3; strike the EBP-analogy justification, replace with power + non-isolation; add the verbatim E3 disclaimer; both TP estimates in the context line; pin the 10 bp revision criterion.
- Q3: amend C5 (0.10 convention / 0.08 instrument); C6 — strike R-M sentence and 98 %, rewrite the step-4 sentence as above. Claude's amendment keeps the two elements that make it a directional signal.
- Q4: ratify C1–C4; amend C7 (oracle-free 219-origin interval first; gate line label; p ≈ 0.09 stated).
- Q5: keep.

**C) Biggest risk in my proposal**

Stripping C6 to numbers removes the one fact a reader of a curve-only model most needs today: that the +1.1 pp curve is almost entirely term premium, and that on the best available literature the model is reading the wrong component. If an onset arrives in 2027 behind a flat expectations curve and a 15 % P, the record will show that the council chose a tidy firewall over a true warning. I accept that risk because the alternative — a context line that argues P is wrong, from a revisable model, without a test that can ever be scored on fewer than two post-sealing onsets — is exactly the unvalidated side-channel the firewall was written to exclude.

---

## Grok 4.7 (xAI)

Q1. Seal Part A for the 2027 refit, as an unscored diagnostic only. Convert both monthly TB3MS and daily DTB3 with the pinned formula BEY(d) = 100·365·(d/100)/(360 − 91·(d/100)), d in percent, fixed 91 days. Do not splice GS3M at 1981-09; that break sits between the high-rate onsets and the later sample and would confound the thing being measured. GS3M from 1981-09 is a check only (mean and max |BEY(TB3MS) − GS3M|), never an input. Outputs (1)–(3) as drafted, λ = 1, origins identity-asserted, episode-block bootstrap 1000 draws, seed 42, 10–90%. Add one reported table, not a criterion: mean (BEY curve − discount curve) by decade and by 3m-rate bins (0–4, 4–8, 8–12, >12). The level dependence is the point — gap 0.10 pp at 4%, 0.28 at 8%, 0.81 at 15% — and four of twelve onsets sit in the high-rate window where the discount curve understates inversion depth by several tenths of a point. At the local derivative (−1.6 pp of P per 10 bp) today’s 0.18 pp convention gap is ~3 pp of P; in 1980–81 it is an order larger. That is a real measurement defect. It is not a reason to touch frozen weights or to publish any BEY probability before a later council, a sealed spec, and that configuration’s own replay (§1.3). No automatic switch. Item (4), the refit-date BEY probability, stays inside `uscorede.konvention_bey` and off the dashboard.

Q2. Closed historically. B1/B2 are a second shot after a seen rejection (dLL −77.88 pp, 0% of LOEO folds positive, 192 origins). The missing-history penalty was in the sealed step-4 design; discovering that it dominates the number is not new economics. Rosenberg–Maurer was known, direction included, before that run. Power settles it: 8 onsets, MDE80 ≈ 2.8·SD_block, order 30 pp, so the likely print is “no difference,” which would launder a rejected feature back onto the agenda. Strike B1/B2 from the spec; do not leave them parked “in case.” If a future council is outvoted into running them anyway, the bar in the draft is not acceptable as written: 1.96·SD_block with ~8 episode blocks is a normal approximation on a sample that cannot support it; “neither crosses ⇒ incumbent stays” must be labelled a lock, not evidence of equivalence; the spec must print E3 in full and state that curve-only on the 1961Q3 panel is a different configuration from operational +20.37% (219) and may not be cited as it. B3 only, and narrower than drafted: after the ≥12-snapshot revision audit, an unscored ledger column may carry the bare expectations-minus-3m number from THREEFYTP10. No literature sentence, no “share of the curve,” no threshold, no count. A scored test waits on ≥2 post-sealing onsets and is decades away. That cost is the closed search working.

Q3. C5 stays, with one added sentence: the gap is not an input, and no alternative P is to be computed by substituting the CMT curve into the frozen weights. Without that sentence a reader does exactly the illegal substitution (discount +1.124 → 14.8%; CMT +0.95 fed into the same logit → ~17.9%) and treats 18% as the corrected figure. C6 as written fails the firewall. “98% is term premium; the literature says the expectations component is what predicts” is a directional claim that the operational signal is the non-predictive part, from one model (KW TP 0.99) on one day, against ACM at 0.84 two months earlier, on series that revise. Strip the 98% figure and the Rosenberg–Maurer sentence from the live note. What may remain under P: term-premium estimates are model-dependent and revised, and are not inputs. The economic argument belongs in the unsealed spec, not beside the number.

Q4. C2, C3, C4: ratify. C2 closes a §1.2 breach; C3 states the spread actually used; C4 replaces a false “advance” label. Pin the C4 rule as quarter-end + 32 + 10 days so “later vintage” cannot be widened after the next awkward print. C1: ratify ex post, and this is acceptable despite being post hoc, because it is a label, the old label was false at +1.4 bp, and it cannot move P, the band, the verdict, or the ignition column. Disclose in the same sentence that 5 bp was set after seeing +1.4 bp. Freeze `MAERKE_MIN_DK` until the 2027 refit; a retune after the next flat month is a second fork. C7’s gate label (“F5 +23.2% vs curve-only +27.1%, same full path”) is correct and should stay. The bootstrap interval does not stay where it was put. It is the oracle-censored 198-origin interval, mean +0.120 nats, 90% [−0.042, +0.239], 8.9% of draws ≤ 0. Parking that under the §1.2 sentence attaches uncertainty to figure (ii) only and makes the censored number the one with statistical standing. Either compute and print the same episode-block interval for oracle-free +20.37% (219) in the same slot, same draw count and pinned seed, or move the censored interval to a footnote that says it attaches to (ii) only and is not the uncertainty of the lead figure. Do not leave it as drafted.

Q5. No change to the verdict string. “Not distinguishable” stays in the verdict, the ledger, and the dashboard. The paired supplement this month is [−6.5, −0.4] pp and the backtest disagrees on 12/198, always with the paired rule saying distinguishable and the band saying not. That is the band rule being more conservative, which is why it is the rule. A dashboard gloss of “no robust signal under the band rule” is a second verdict in plain language. One methods sentence may record the 12/198 fact and the direction of every disagreement. It does not appear on the verdict line.

Claude, as written, amended, or struck. Q1: amend. Seal Part A, convert-both, no splice, no automatic switch — that part stands. Strike |Δ oracle-free| < 2 pp as anything a reader could treat as a test; a level-dependent gap of 0.8 pp in the Volcker window makes 2 pp of skill a wish, not a bound. If the sentence survives, it is labelled “author’s prior, not a criterion,” and it is not printed next to the result. Q2: amend by deletion. “Only B3” stands; “B1/B2 listed only because” does not — listing them is the second shot half-authorized. The EBP analogy is rhetoric; the closure reason to write down is a seen rejection plus forking paths, not §8.2 by nickname. Q3: C5 keep with the anti-substitution sentence. C6 as Claude amended (keep 98%, add model-dependence) is struck; model-dependence replaces the 98% and the literature sentence, it does not accompany them. Q4: C1–C4 as Claude says, plus the freeze on 5 bp; C7 interval placement struck and replaced as above. Q5: keep as written.

Biggest risk in this proposal. Item (4) and a B3 column, even unscored and even off the manifest hash, become the alternative model the moment they diverge from P. Today’s illegal CMT substitution is already ~3 pp; a BEY refit probability printed anywhere a screenshot can reach will be cited as the real P, which is a §1.3 breach by distribution rather than by code. The mitigation is physical: BEY P never renders on the dashboard or in LOG.md, and the expectations column, if it ever exists, is a bare number with no sentence next to it.

---

## Kimi K3.1 Pro (Moonshot AI)

## A) Agenda positions

### Q1 — Seal Part A, with additional diagnostics
Seal it before any code; the post hoc motivation is acceptable because the sensitivity is unscored, cannot alter the frozen configuration, and will be published regardless of result. The pinned conversion is correct for a 91-day discount quote: \(BEY=100\cdot365(d/100)/[360-91(d/100)]\); apply it separately to TB3MS and DTB3, never splice in GS3M, and keep the post-1981 mean/max absolute discrepancy strictly descriptive. Add the fitted intercept/slope and paired origin-level log-loss and probability differences, summarised over TB3MS bins **<4%, 4–8%, ≥8%** with onset counts, because an average can conceal the high-rate episode; Claude’s predicted \(|\Delta\text{ oracle-free skill}|<2\) pp may remain only as a preregistered prediction, not a criterion. The discount basis is internally consistent, so this is a specification risk, not yet a demonstrated defect. Any switch requires a subsequent council decision, new fit and manifest, and that configuration’s sealed replay; neither skill nor live-P movement alone suffices.

### Q2 — Historical Part B stays closed; seal only a strengthened B3
Do **not** mandate B1/B2: step 4’s missing-history penalty confounded the hypothesis, but relaxing the closure after seeing −77.88 pp is precisely a second shot, and eight onsets with MDE80 around 30 pp offer little confirmatory value. B3 is acceptable despite its post hoc motivation because it is prospective and supplies no historical evidence; use Kim–Wright, but permit no standing decomposition line or ledger column until the revision audit is complete. For that audit, archive **12 consecutive monthly full-history vintages**, each with sha256, and for every date present in vintage 1 report median and maximum absolute revisions from vintage 1 to each later vintage for both TP and \(E=(y10-TP)-3m\), in pp. Any subsequent scored test requires a separate seal and at least two post-sealing onsets; pre-2027 observations remain inadmissible as evidence. If the council overrides me, use the common-origin block bootstrap but replace 1.96 with **2.2414·SD_block**, the two-sided 5% Bonferroni cutoff across two candidates, symmetrically in both directions, and disclose E3 in full—including base-rate scoring before 1961, 0% positive folds, and the never-run truncated comparison—as contamination, not justification for calling the rerun independent.

### Q3 — Amend C5; remove C6 as a standing warning
C5 is not accurate verbatim: the 0.18 pp gap is not entirely convention. Replace it with: **“Convention: the model’s 3m leg is DTB3/TB3MS on the discount basis. On this window DGS10−DGS3MO (CMT) is +0.95 pp, versus +1.12 pp using DTB3. At DTB3 4.04%, the pinned BEY conversion gives 4.14%; the remaining ≈0.08 pp to DGS3MO 4.22% reflects instrument/fitting differences. Neither BEY nor CMT may be fed to the frozen weights; Part A is an unscored refit sensitivity.”** Remove C6 rather than merely adding another caveat: retaining “98%” beside P, the literature direction, and a near-zero expectations spread functionally tells readers that P is too low, despite the closed and confounded ACM test. The 98% is only \(0.99/1.01\), an unstable ratio when its denominator is near zero, and KW 2026-10-16 and ACM 2026-07 are neither contemporaneous nor interchangeable. The ACM rejection and its limitation belong in methods documentation; these post hoc presentation corrections are acceptable because they make no numerical or ledger change.

### Q4 — Ratify only with amendments
**C1:** retain 5 bp prospectively, but say “near-parallel,” always print both leg changes and Δcurve, and disclose that the threshold was chosen after seeing +1.4 bp; that post hoc choice is acceptable solely because the label cannot affect any output. **C2:** ratify only if the complete, ordered §1.2 sentence—including +18.32% and the power clause—accompanies every public skill display, not merely +20.37% beside +27.05%. **C3:** ratify. **C4:** retain “first seen by us,” but replace the quarter-end+42-day inference with “after the usual advance-release window” unless the actual BEA release calendar establishes that the snapshot postdates advance. **C7:** strike the gate line as written because “+27.1%” is again standalone; state instead that curve-only exceeded F5 by **3.89 pp** on the same oracle-censored path. The bootstrap may follow, not interrupt, the full §1.2 sentence, labelled: “oracle-censored, 198 origins, 9 episode blocks; mean +0.120 nats/origin, 90% interval [−0.042,+0.239], 8.9% of draws ≤0”; it is a post hoc uncertainty disclosure, not independent confirmation of oracle-free skill.

### Q5 — Clarify the dashboard; leave the rule and ledger untouched
Amend Claude’s no-change position. Use: **“Primary band rule: not distinguishable from the 18.0% base rate (90% band 10.2–21.2%).”** If the paired supplement is displayed, add immediately: **“Descriptive paired supplement: 90% interval −6.5 to −0.4 pp; it does not determine the verdict.”** Do not use an unqualified “no robust signal”: the 12/198 disagreements demonstrate rule dependence, while historical ledger rows remain unchanged. This post hoc wording clarification is acceptable because it changes no threshold, verdict, or stored row.

## B) Disposition of Claude’s draft positions

- **Keep:** Q1’s convert-both/no-splice design and no-automatic-switch rule; Q2’s rejection of B1/B2 and prospective-only objective; C3.
- **Amend:** Q1 with rate-regime diagnostics; B3 with audit-before-publication; C1, C2, C4 and C7 as above; Q5 with rule-explicit dashboard wording.
- **Strike:** C5 verbatim, C6’s standing 98% warning, and any claim that step 4’s confounding itself earns another historical shot.
- Claude’s Q4 blanket ex-post ratification is not acceptable: C2 and C7 still risk standalone oracle-censored skill figures.

## C) Biggest risk in my own proposal

The largest risk is **diagnostic creep**: rate-binned convention results and a regularly displayed Kim–Wright decomposition could become a narrative shadow model, later treated as independent evidence despite their post hoc, revisable origins. The necessary safeguards are no present probability implication, no automatic decision trigger, and a fresh mandate plus sealed replay before any operational change.

---

## DeepSeek V4 Pro (DeepSeek)

**A) Agenda answers**

**Q1 — Part A: Seal, with one amendment.** Seal the conversion sensitivity as drafted. The formula is correct arithmetic; 91 days is the right fixed tenor; converting both TB3MS and DTB3 into one consistent 1934–series is the only defensible choice—splicing CMT post-1981 would introduce a level break at exactly the point where the convention gap is largest (E1 shows the gap is level-dependent, so a splice would bias the high-rate 1970s–80s window where 4 of 12 onsets sit). The check against GS3M post-1981 is appropriate as a diagnostic, not a criterion. I would amend the decision rule: the spec should state explicitly that if |Δ oracle-free| ≥ 2 pp, the council must convene before the next refit to discuss whether the operational convention is a defect—not to switch automatically, but to put the question on the agenda with a sealed follow-up. The convention is not a defect in the model's internal consistency (weights were estimated on discount basis; P is computed on discount basis); it is a presentation risk because external readers compare against T10Y3M. The unscored sensitivity plus the C5 note handles this adequately. Do not change the operational convention before the refit; do not let Part A become a backdoor feature search.

**Q2 — Part B: B3 only. Closed historically.** I agree with B3 as the only acceptable option, but I reach it by a different route than Claude. The step-4 ACM test is not the EBP situation: EBP's historical test was sealed, run once, and the onset pattern was seen—the question is closed because the answer was observed. ACM's step-4 test was contaminated by the missing-history penalty, so the economic hypothesis was never isolated. That is a reason to be *more* cautious, not less: re-running B1/B2 would be a second shot at a target that was already fired at once, and the forking-paths risk is real even if the first shot was badly aimed. The symmetric bar as drafted is acceptable in form but the power calculation is damning: MDE80 ≈ 2.8·SD_block, order 30 pp, with 8 onsets. A test that is virtually guaranteed to return "no difference" is not a test; it is a ritual. B3's prospective design is the only honest option: seal the context line now, run the revision audit, and let future onsets accumulate. If the council wants to revisit B1/B2 in a decade when more onsets exist post-sealing, that is a future council's decision under §8.3. The spec must state in §0: "This idea was tested once in step 4 (result: dLL −77.88 pp, 0 % positive folds); that result is contaminated by the missing-history penalty and is not evidence for or against the economic hypothesis; the idea is closed historically regardless."

**Q3 — C5 and C6: Keep C5 verbatim. Amend C6 substantially.** C5 is a factual convention note; it informs without signalling. C6 as drafted is a problem: it tells the reader that "98 % of the curve is term premium" and that "the literature finds the expectations component is what predicts recessions"—two statements that, juxtaposed, amount to "P is too low because the model reads the wrong part of the curve." That is a firewalled context line doing signal work. The firewall exists to prevent exactly this. My amendment: keep the decomposition arithmetic (TP 0.99, expected 4.10, expectations-minus-3m +0.02 pp) but add the model-dependence caveat Claude proposes (KW vs ACM), and strike the Rosenberg-Maurer sentence and the "98 %" framing. Replace with: "Term-premium estimates are model-dependent and revised; the expectations component's predictive role is contested in the literature and was tested once in step 4 (rejected, contaminated). This line is context, not P." The reader who wants the literature can find it; the dashboard should not be the place where the model's own verdict is undercut by a one-day decomposition from a model that was itself rejected.

**Q4 — C1–C4, C7: Ratify all, with one disclosure amendment.** C1: the 5 bp threshold is post hoc and disclosed as such; it is a label on a curve change, not a model output, and cannot move P, band, verdict, or the ignition column. I would add one sentence to the label logic: "Threshold set 2026-10-27 after observing +1.4 bp; disclosed as post hoc." C2, C3, C4: all factual presentation fixes that close §1.2 breaches and reviewer-identified ambiguities; ratify as written. C7: the 4.4 paired loss-bootstrap interval under the §1.2 sentence is acceptable *only if* it is labelled oracle-censored and never appears without the oracle-free figure—which the draft already does. The order requirement in §1.2 is about the skill statement itself; the interval is a supplement, not a replacement. I would require the interval to carry the same "oracle-censored" label as the +27.05 % figure it accompanies, and to be printed in smaller type or a footnote so it cannot be read as the primary skill number.

**Q5 — Verdict wording: No change to the ledger. Amend the dashboard only.** The band rule is the sealed primary rule; changing its wording in the ledger would be a governance breach (the ledger is append-only under a preregistered scoring key). The paired rule is systematically less conservative (disagrees on 12/198 origins, always in the direction of "distinguishable"), and adopting its wording would loosen the verdict standard without a council mandate. Review 1's suggestion—"no robust signal under the band rule"—is acceptable as a dashboard gloss *if* it appears only in the plain-language explanation, never in the ledger or the verdict field itself, and *if* it is accompanied by the existing "not distinguishable" in parentheses. My position: keep "not distinguishable" everywhere; add the gloss to the dashboard's tooltip or footnote only.

**B) Verdict on Claude's draft positions**

- **Q1 (Part A):** Keep the seal recommendation; amend the decision rule as above (add the ≥ 2 pp convening trigger).
- **Q2 (Part B):** Keep B3-only; amend the §0 disclosure to state explicitly that the step-4 result is contaminated and is not evidence either way.
- **Q3 (C5/C6):** Keep C5 verbatim; strike the Rosenberg-Maurer sentence and the "98 %" framing from C6; keep the model-dependence caveat and the ACM-rejection sentence.
- **Q4 (C1–C4, C7):** Keep all; add the post-hoc disclosure sentence to C1 and require the oracle-censored label on the 4.4 interval.
- **Q5:** Keep "not distinguishable" in the ledger and verdict; accept the dashboard gloss only as a tooltip/footnote, not as a replacement.

**C) The single biggest risk in my proposal**

The biggest risk is that the C6 amendment, by striking the Rosenberg-Maurer sentence, leaves the dashboard *less* informative about a genuine economic concern (the expectations component's role) while the underlying issue remains unresolved. If the expectations component really is the predictive part of the curve, and the model reads only the sum, then P is systematically biased in high-term-premium regimes—and my amendment buries that concern in a context line that says "contested." The alternative risk—leaving C6 as drafted—is that the firewall becomes decorative and the dashboard starts doing the model's job. I choose the first risk because the firewall is a governance commitment, not a convenience; but I flag it so Rasmus knows the trade is deliberate.

---

## Claude (Opus 5.5) (Anthropic — interested party, co-builder and secretary)

**Claude Opus 5.5 — Round 1 (interested party: I made C1–C7 and wrote draft spec 7).**

**A) The agenda**

**Q1 — Part A: seal it, convert both legs, never splice.** The convention is a measurement choice inside the one
operational feature, so testing it is not a feature search, and E1 shows it is not cosmetic: the discount curve is
overstated by 0.3–0.8 pp exactly where four of twelve onsets sit (1970s–80s), against 0.02–0.10 pp in the low-rate
years. A level-dependent measurement error in the only regressor can bias β. Procedure: BEY(d) = 365d/(360 − 91d)
on TB3MS (1934–) and DTB3 (live), one consistent series; CMT (GS3M) only as a reported check from 1981-09. A splice
would put a level break at 1981-09 inside the training data, which is worse than the convention it fixes. Outputs
as drafted, oracle-free first. Prediction, written now: |Δ oracle-free walk-forward| < 2 pp and |Δβ| < 0.15 per pp.
It is not a defect needing more than this: the calibration and live input are internally consistent, the weights
are frozen, and §1.3 forbids presenting a converted-curve skill as the operational model's. A switch, if ever, is
a council decision from a later refit with its own sealed replay.

**Q2 — Part B: closed historically; B3 only.** Two contaminations are disqualifying. (1) The step-4 number is seen;
it is uninformative about the economics, but anyone designing B1/B2 now knows that the penalty, not the idea,
sank it, and will design the panel so that it cannot sink it again: that is precisely a second shot tuned on the
first. (2) The literature's direction over 1961–2008 is known, and those years are 7 of the 8 onsets B1/B2 would
use. With MDE80 ≈ 30 pp the test cannot distinguish anyway, so its only possible output is a number that invites
over-reading. B3: THREEFYTP10 (daily, Fed Board, public domain) as the context line; a ≥ 12-snapshot revision
audit of the KW history before any unscored column; scored evaluation only after ≥ 2 post-sealing onsets.

**Q3 — keep C5 verbatim; amend C6; keep both.** C5 removes a real confusion (readers compare with FRED's T10Y3M)
and explicitly says the CMT curve cannot be fed into the weights. C6 is the strongest objection to my own work:
it is a context line that argues against P. I keep it because the standing warnings already do exactly that (the
level-not-history warning, the long-end paradox) and the firewall governs what enters P, the verdict and the
ignition column — not whether the reader is told the model's known blind spot. But C6 overstates precision. Amended
text: replace "98 % of the curve that day is term premium" by "on that day almost all of the curve is term premium
in the Kim-Wright model (TP 0.99 of +1.01 pp); term-premium estimates are model-dependent and revised (ACM 0.84 in
2026-07)", keep the ACM-rejection sentence, and add "this is not a threshold and is never counted".

**Q4 — ratify C1–C4 and C7 ex post.** C2 is not discretionary at all: it repairs a breach of §1.2 that already
binds. C3/C4 make labels true. C1: 5 bp was chosen after seeing 1.4 bp, but the threshold only governs a word; it
cannot move P, the verdict or the ignition column, and any value between 2 and 10 bp gives the same label this
month — so there is no outcome the choice selects. Record it as post hoc and freeze it. C7: the 4.4 interval is
oracle-censored; it stays under the §1.2 sentence (never before it) and carries the word "oracle-censored".

**Q5 — no change.** "Not distinguishable from the base rate" is already a non-claim (§7.3: no nominal significance
claim). Renaming it in the dashboard only would create two vocabularies for one verdict; the ledger column must
not change meaning mid-ledger.

**B) Verdict on my own draft**

Keep: Part A's procedure and decision rule; Part B's recommendation of B3; the disclosure in §0. Amend: Part B
should drop B1/B2 from the spec text entirely if the council closes B, so a future reader cannot pick them up as a
ready-made design; and §0 must record that the BEY gap table (E1) was computed before sealing. Strike nothing else.

**C) The biggest risk in my proposal**

That Part A is itself a disguised second shot at the 2023 false alarm: a convention change that lowers the
high-rate-era curve could also change how 2022–23 reads, and a council that later "adopts BEY" because its replay
looks better would be choosing a measurement on its outcome. The decision rule (no switch on skill alone, §1.3,
own sealed replay) is the only guard; if the council thinks it is too weak, Part A should be unscored forever.
