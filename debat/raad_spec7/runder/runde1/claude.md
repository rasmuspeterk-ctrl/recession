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
