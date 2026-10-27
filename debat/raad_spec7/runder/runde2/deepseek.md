## 1) Attack

**Gemini's Q1 non-inferiority switch rule is a governance error dressed as rigor.** Gemini proposes sealing a binding rule now: switch to Curve_BEY at the 2027 refit unless Δskill_OF < −0.50 pp. This inverts the burden of proof. The operational configuration is frozen by manifest 72c3371d and RAADETS_2027 §1.3; a switch requires the new configuration's own sealed replay *and a council decision at that time*. Pre-committing a switch unless the challenger is "demonstrably inferior" means the incumbent must beat the challenger to survive — a presumption of change that §1.3 does not grant. Worse, the −0.50 pp threshold is arbitrary: with 219 origins and 12 onsets, the episode-block SD of Δskill is order 5–10 pp (MDE80 ≈ 30 pp per the draft's own power section). A −0.50 pp bar is far below noise; it would trigger a switch on a coin flip. Gemini's own risk section concedes the discount distortion may have been "accidentally helpful" — that is exactly why the decision belongs to a future council looking at the full replay, not to a pre-committed rule that cannot see the result it is deciding on.

**Kimi's Bonferroni correction (2.2414·SD_block) for B1/B2 is statistically incoherent.** Kimi proposes replacing 1.96 with 2.2414 (two-sided 5% Bonferroni across two candidates) if B1/B2 were ever run. But the symmetric bar as drafted compares *each candidate against curve-only*, not candidates against each other. The multiplicity is not two tests of one null; it is two separate nulls (B1 = curve-only, B2 = curve-only), each tested once. Bonferroni across them is conservative in the wrong direction: it protects against false rejection of curve-only when curve-only is true, but the draft's design already has curve-only as the locked incumbent — the asymmetry of outcome, not evidence. With 8 onsets and MDE80 ≈ 30 pp, the test is underpowered regardless; multiplying the threshold by 1.14 changes nothing substantive while pretending to fix multiplicity. If B1/B2 are run (I recommend they are not), the bar should stay 1.96·SD_block per candidate, with the power statement printed prominently.

## 2) Steelman

**Claude Fable 5.1's C7 amendment — compute the paired loss bootstrap on the oracle-free 219-origin set and print both intervals in §1.2 order — is the single best idea I missed.** My Round 1 accepted the 198-origin interval under the §1.2 sentence with a label. Fable is right: the only uncertainty band on the page attaches to the oracle-censored figure, so the eye reads +27% as the headline with statistical standing. Printing the oracle-free interval first (same bootstrap, 219 origins, seed 42) fixes the optics without touching anything frozen. I adopt this.

## 3) Revised positions

**Q1:** Seal Part A as drafted, with my convening trigger (|Δ oracle-free| ≥ 2 pp → council agenda item before next refit). I now also adopt Fable's Jensen disclosure: BEY(mean of daily d) ≠ mean of daily BEY(d); compute the live input as mean-of-converted and quantify the monthly-average bias once. Reject Gemini's non-inferiority switch rule.

**Q2:** B3 only. I keep my position but adopt Fable's verbatim §0 disclaimer: "E3's −77.88 pp is a result on an implementation, not on the hypothesis; it is not evidence against the expectations component." I also adopt Fable's requirement that the context line print *both* TP estimates (KW and ACM) with dates, not THREEFYTP10 alone.

**Q3:** C5 verbatim. C6: my amendment stands (strike Rosenberg-Maurer and "98%"; keep model-dependence caveat and ACM-rejection sentence). I now add Fable's point: no other context line carries a "the literature says this predicts recessions" sentence; C6 should not either.

**Q4:** C1–C4 ratify with my post-hoc disclosure on C1. C7: adopt Fable's amendment — compute the oracle-free 219-origin interval and print both in §1.2 order. Until it exists, label the 198 interval "oracle-censored set; oracle-free interval pending." Also adopt Fable's p ≈ 0.09 statement (8.9% of draws ≤ 0, one-sided, 9 blocks).

**Q5:** No change to ledger or verdict. Dashboard gloss only as tooltip/footnote, with "not distinguishable" in parentheses.

## AGREE

- Part A seals as an unscored sensitivity; convert both TB3MS and DTB3; never splice GS3M; no automatic switch.
- B1/B2 are not run; B3 prospective-only is the only acceptable Part B.
- C6 as committed (with "98%" and Rosenberg-Maurer) fails the firewall; must be amended or struck.
- C2 repairs a §1.2 breach and is not discretionary.
- Ledger and verdict wording unchanged; "not distinguishable" stays.
- The 198-origin interval must not appear as the only uncertainty band under §1.2.

## DISAGREE

- **Gemini vs. everyone:** pre-committed non-inferiority switch rule for BEY at 2027 refit.
- **Kimi vs. Fable/me:** Bonferroni 2.2414 vs. 1.96·SD_block if B1/B2 were ever run (moot if B closed).
- **Claude Opus vs. Fable/Grok/Kimi/me:** whether C6 keeps the "98%" figure and Rosenberg-Maurer sentence (Opus: keep, amended; others: strike).
- **Gemini vs. Fable/me:** whether C7 requires the oracle-free interval computed now, or the 198 interval suffices with a label.
- **Kimi vs. Opus/Gemini:** whether C6 is removed entirely (Kimi) or amended (Opus, Gemini, me).

## CHANGED-MY-MIND

- **C7:** I now require the oracle-free 219-origin paired-loss interval computed and printed first, not merely a label on the 198 interval. Fable's argument about the eye reading the censored figure as the headline is correct.
- **Q2 §0:** I adopt Fable's verbatim disclaimer that E3's result is not evidence against the hypothesis. My original wording ("contaminated and is not evidence either way") was weaker; Fable's is sharper and prevents future citation of −77.88 pp as a rejection.
- **Q2 context line:** I now require both KW and ACM TP estimates printed with dates, not THREEFYTP10 alone. E2's 0.15 pp disagreement on a 1.0 pp curve makes single-model reporting misleading.
- **Q1:** I adopt the Jensen/mean-of-converted disclosure. I had not considered that the monthly-average conversion bias is quantifiable and should be printed once.