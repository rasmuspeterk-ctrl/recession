**Claude Opus 5.5 — Round 2 (interested party).**

**1) Attacks**

- **Sol, Q4: "C7's F5/curve-only labels reverse the attribution in the brief's verified gate calculation."** They do
  not. The line is rendered from `dashboard.json` → `gate.fuldmodel_wf` = 23.16 and `gate.curve_only_wf` = 27.05
  (manifest 72c3371d, `gate`), and prints "F5 +23.2 % vs curve-only +27.1 %"; the brief's verified figure is
  27.05 − 23.16 = 3.89 in curve-only's favour. Same numbers, same direction. Kimi's objection to that line is the
  valid one: +27.1 % appears there without the oracle-free figure.
- **Argon, Q1: a binding switch to BEY at 2027 unless Δ_OF < −0.50 pp.** The bar is inside the noise by a factor of
  five: the paired same-origin SD_block for a comparable configuration change was 2.58 pp (§3.2(b)), so −0.5 pp is
  0.2 SD — the rule is a pre-commitment to switch dressed as a test. If the argument is "fixing a unit error need
  not beat the error" (and I now think it is a good argument — see 2), say so and use a bar that can actually fail:
  switch unless BEY is *clearly* worse, Δ_OF < −1.96·SD_block.
- **Fable, Q1: "at d ≈ 4 %, gap 0.10 pp → ΔP ≈ −1.6 pp at today's input".** Sign and legitimacy are both wrong. A
  BEY 3m leg is *higher*, so the curve is 0.10 pp *lower* and the frozen logit gives P *higher*, ≈ +1.6 pp. And, as
  Grok says, feeding any re-defined curve into the frozen weights is exactly the illegal substitution; that
  arithmetic must not be preregistered as a ΔP. Preregister the sign of the walk-forward Δ if anything.
- **Kimi, Q3: "98 % is 0.99/1.01, an unstable ratio when its denominator is near zero."** The denominator was +1.01
  pp, not near zero. The real defect is different and worse: numerator and denominator come from different models
  and conventions (KW zero-coupon TP vs a discount-basis bill), so the ratio has no stable meaning. Your conclusion
  (remove it) stands; your reason does not.
- **DeepSeek, Q3: "keep C5 verbatim".** C5 says "the gap (0.18pp) is convention, not data". By E1's own arithmetic
  0.10 pp is convention and ≈ 0.08 pp is DGS3MO vs converted DTB3 — instrument and fitting. Sol, Fable and Kimi are
  right; C5 as I wrote it is false in a number.

**Fable's Jensen point, quantified:** BEY is convex, f''(d) ≈ 0.51 (decimal units) at d ≈ 4 %. With
within-month σ of daily DTB3 of 0.2 pp the bias of BEY(mean d) vs mean BEY(d) is ½·0.51·(0.002)² ≈ 0.0001 pp; with
σ = 1 pp (1980) ≈ 0.003 pp. Negligible, but the spec should state the bound and pin mean-of-converted for the live
daily leg, BEY(TB3MS) for history.

**2) Steelman** — Argon's: a measurement correction does not have to beat the mismeasured series to be adopted.
My draft's "no switch on skill alone" left the 2027 council free to keep a known unit inconsistency for ever
unless a skill figure argued otherwise — the same post-hoc latitude in the other direction.

**3) Revisions**

- **Q1:** seal Part A, convert both, no splice, Jensen bound stated, rate-bin table (Kimi/Grok: <4, 4–8, 8–12,
  ≥12 %; fitted α, β; origin-level paired Δ). New decision rule, sealed now: *at the 2027 refit the operational
  convention becomes BEY unless Δ_OF(BEY − discount) < −1.96·SD_block(Δ) (episode-block, 10,000 draws, seed 42 —
  Sol); the BEY configuration's own replay is printed (§1.3); the discount configuration is printed for one year as
  an unscored comparison; BEY P never renders on the dashboard before that refit (Grok).* My |Δ| < 2 pp is labelled
  "author's prior, not a criterion", printed away from the result.
- **Q2:** B3 only; delete B1/B2 from the spec (Grok, Kimi). Closure reason written as: a seen rejection, forking
  paths, and power (MDE80 ≈ 30 pp) — not "§8.2 by nickname" (Sol, Fable, Grok, DeepSeek). §0 carries Fable's/
  DeepSeek's sentence: E3 is a result on an implementation, not evidence for or against the hypothesis. B3 audit as
  Kimi specifies (12 monthly full-history vintages, sha256, median/max revision of TP and E); opens a bare-number
  unscored column only if max revision < 10 bp (Fable). No sentence beside it (Grok).
- **Q3:** C5 → Kimi's text plus Grok's anti-substitution sentence. C6 → Fable's numbers-only line (KW and ACM with
  dates; "model-dependent, revised, not inputs"; the step-4 sentence as Fable wrote it). Strike 98 % and the
  literature sentence. I withdraw my own C6 amendment.
- **Q4:** C1 → "near-parallel (curve change < 5 bp)", both legs always printed, post-hoc disclosure, frozen until
  2027. C2 → the row note carries all three §1.2 figures in order, short form. C4 → "after the usual advance-release
  window (quarter end + 42 days); BEA vintage not verified", rule pinned. C7 → compute the oracle-free 219-origin
  paired interval with the same procedure and print both in §1.2 order; gate line gets "(oracle-censored full
  path; oracle-free headline +20.37 %)". C3 ratified.
- **Q5:** no change to the verdict string. The dashboard already prints the paired supplement with "does not
  change the verdict" on the next line, which is what Sol and Kimi ask for.

AGREE: seal A, convert both, no splice; no BEY probability on the dashboard; B1/B2 not run; B3 prospective only
with a revision audit first; strike 98 % and the literature sentence from C6; C5 must stop saying "all
convention"; C2, C3 ratified in substance; 5 bp disclosed as post hoc and frozen; verdict string and ledger unchanged.
DISAGREE: switch rule for A (Argon's −0.5 pp / my −1.96·SD_block vs Sol, Grok, Kimi, DeepSeek: no pre-committed
switch); C6 neutral line vs removal (Kimi); C7 oracle-free interval computed now (Fable, Argon, Grok, me) vs
footnote only (DeepSeek, Sol); Q5 dashboard gloss (Sol, Kimi, DeepSeek-as-footnote vs Fable, Argon, Grok, me);
C4 heuristic kept with caveat vs dropped.
CHANGED-MY-MIND: C5 (number was false), C6 (98 % and R-M struck), EBP analogy dropped as the reason, B1/B2 deleted
from the text, and A's decision rule — from "council decides freely" to a sealed switch-unless-clearly-worse.
