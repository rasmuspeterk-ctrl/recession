## Attacks

**Gemini:** “we switch … unless \(\Delta\mathrm{skill}_{OF}<-0.50\) pp” is not a non-inferiority rule; it is an automatic adoption rule using an unvalidated margin and a point estimate. Here 0.50 pp of relative skill equals only \(0.005\times0.442=0.00221\) nats/origin, yet no standard error or power calculation for the BEY–discount comparison is supplied. A proper non-inferiority decision needs a justified margin and a one-sided uncertainty bound. More fundamentally, it makes an outcome-based skill statistic decide which measurement convention is correct—the post-hoc selection Part A is supposed to avoid.

**Claude Opus:** “the firewall governs what enters P … not whether the reader is told the model’s known blind spot” assumes the disputed conclusion. The expectations hypothesis has not been isolated: step 4 rejected a particular implementation dominated by pre-1961 base-rate scoring. Beside P, “almost all … is term premium” plus Rosenberg–Maurer still instructs the reader to discount P. The arithmetic is also fragile: 98% is merely \(0.99/1.01\), with a denominator near zero; substituting ACM’s 0.84 for KW’s 0.99 changes the expectations spread by 0.15 pp, several times the reported +0.02 pp. That is not a sufficiently stable “known blind spot” for a standing warning.

**GPT:** C7 does not “reverse the attribution.” The verified numbers are curve-only 27.05% and F5 23.16%, so \(27.05-23.16=3.89\) pp; C7’s rounded 27.1% versus 23.2% attributes the difference correctly. Its defect is presenting oracle-censored skill outside the complete §1.2 context, not reversing the gate.

## Steelman and revisions

The best idea I missed is **Fable’s Jensen-aggregation warning**. Because BEY conversion is convex, converting a monthly mean is not equivalent to averaging daily conversions. I would pin convert-after-averaging for both monthly calibration inputs and the trailing live means, while reporting mean-of-daily conversion as a robustness diagnostic and quantifying the bias. Otherwise Part A could conflate convention with aggregation.

My other positions stand: seal Part A with rate-binned diagnostics, unconditional publication and no automatic switch; keep B1/B2 closed and remove their ready-to-run designs from the ratified spec; require B3’s revision audit before publication; retain my corrected C5 and remove standing C6. On C7, I now require the same paired bootstrap for the 219-origin oracle-free path before displaying the 198-origin interval beneath §1.2; until then, move the latter to an explicitly labelled footnote. The 8.9% draw share is not a one-sided p-value. My dashboard clarification under Q5 is unchanged.

AGREE:
- Convert TB3MS and DTB3 consistently; never splice GS3M; no pre-refit change to P or weights.
- Part A is published regardless of result, and Claude’s 2 pp prediction is not an acceptance criterion.
- No B1/B2 mandate; B3 is prospective, unscored and audit-gated.
- The 0.18 pp CMT gap is not wholly convention: approximately 0.10 pp is conversion and 0.08 pp instrument/fitting.

DISAGREE:
- **Gemini versus the rest:** automatic BEY adoption through a −0.50 pp rule; DeepSeek additionally wants a ≥2 pp convening trigger.
- **Kimi/Grok versus Claude Opus:** remove standing C6 versus retain its directional warning; most others favour an intermediate rewrite.
- **Fable/Gemini/Grok, now Kimi, versus DeepSeek/Claude Opus:** oracle-free uncertainty must accompany the oracle-censored interval, rather than merely labelling the latter.
- **Kimi/GPT/DeepSeek versus Gemini/Grok/Fable/Claude Opus:** rule-explicit dashboard clarification versus leaving “not distinguishable” entirely unglossed.

CHANGED-MY-MIND:
- Added Fable’s aggregation/Jensen diagnostic and pinned a calibration/live-consistent aggregation rule.
- Strengthened C7: compute the oracle-free interval first or footnote the oracle-censored one; I also reject GPT’s claimed gate-attribution error while retaining my §1.2 objection.