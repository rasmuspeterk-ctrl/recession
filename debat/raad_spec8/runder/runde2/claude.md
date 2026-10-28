**Claude Opus 5.5 — Round 2 (interested party).**

**1) Attacks**

- **Grok, Q1/Q4: "Log `curve_min12` or log nothing."** Logging the state is logging nothing. GS10 and TB3MS are
  market rates that FRED does not revise; `curve_min12` can be recomputed from public data for any past month, by
  anyone, forever. A ledger field that is fully reconstructible carries zero information about what was believed
  when. The only object a prospective record can add is a *fitted model's* forecast, tied to the fit vintage that
  produced it. So the real choice is "a committed shadow forecast" or "no record at all" — your alternative is the
  second option under the first option's name.
- **Sol, Q4: "use a private append-only companion ledger."** Privacy and credibility pull against each other: a
  file that is not committed can be rewritten after the fact, which destroys the one property that makes the record
  worth having. Both your distribution concern and Grok's are met by a **hash commitment** instead: the shadow
  forecast is written to a local, git-ignored file (`skygge_hukommelse.jsonl`); the public `hovedbog.jsonl` row
  carries only the sha256 of that row's shadow line. Nothing screenshot-able is published, nothing can be backfilled
  or edited, and the file is revealed only when a council evaluates it.
- **Kimi, DeepSeek, Fable, Argon, Q5: four different block lengths (16, 20, 8-mean stationary, 4).** Four members,
  four bars, each written after E2 — Grok's point in numbers. With two post-sealing onsets an episode-block bootstrap
  has two or three blocks; no block length rescues that. A bar pinned today is ritual.
- **Argon, Q3: "re-parameterise as C and C − M to fix collinearity."** For an unpenalised logit (C, M) and
  (C, C − M) are the same model; under λ = 1 on standardised columns they differ only in how the ridge splits a
  shared signal. It does not identify anything the data cannot; it changes which column absorbs the shrinkage. Keep
  (C, M) — the object v4 defined — and disclose the collinearity.

**2) Steelman — Grok's C.** With H = 12 the 2022–24 inversion is already outside the window, so this shadow cannot
speak to the question that put the item on the agenda (does a lag past 9 months still bind?). That must be written
into the spec in plain words: the shadow is about *future* cycles; for this cycle, the record is P, the ledger and
the context lines. Choosing a longer H to make it speak to this cycle is the forking path E2 exposes.

**3) Revisions**

- **E1 overclaim withdrawn** (Grok, Kimi): 1957, 1960 and 1990 came without a ≥ 3-month inversion; 1973 and 1980 came
  during one. And "the shadow will read close to P" is struck (Sol, Kimi): a joint fit moves intercept and both slopes.
- **Q2:** `curve_min12`, justified by the label horizon (Fable: memory back = label forward) plus pre-existence;
  the spec carries Fable's sentence verbatim with E2's three values beside it. Live value (Argon): minimum of the live
  trailing curve and the previous 11 published monthly GS10 − TB3MS values; ≥ 6 observations; same monthly
  aggregation as calibration (Fable).
- **Q3:** curve + curve_min12, λ = 1 exactly as the operational fit, training-only standardisation frozen with the
  vintage, same universe, labels, eligibility, snapshot and R; refit only with the operational September refit.
  Pre-registered sign: β on standardised curve_min12 negative; logged whatever it is (Fable). Disclosures: E1–E4, v4's
  unrecorded result, the grand review, the backtest, the collinearity, and that the fit sample already holds resolved
  zeros after the 2022–24 inversion (Fable).
- **Q4:** hash commitment as above; `hovedbog.jsonl` gets `skygge_sha256` only; never LOG.md, never the dashboard,
  not even after 2027 (Argon) without a new council decision.
- **Q5:** no scored bar in this spec (Sol, Grok). Constraints for any future council: sealed before the onsets it is
  judged on, ≥ 2 post-sealing onsets, comparator = curve-only from the identical fit vintage (Kimi), stated as
  underpowered, never an automatic switch. Fable's onset scorecard (P and shadow at the last origin before each
  post-sealing onset) is printed at evaluation only.
- **Q6:** November 2026 row, sealed and hashed before the log window.

AGREE: curve_min12, H = 12; curve + memory, never memory alone; λ = 1 operational convention; never in P, verdict,
LOG.md or dashboard; contamination disclosed; any future scored test needs ≥ 2 post-sealing onsets and no switch.
DISAGREE: whether to fit a shadow at all (Grok vs five); storage — public `p_hukommelse` (DeepSeek, Kimi, Argon,
Fable), private file (Sol), state only (Grok), hash commitment (Claude); a bar pinned now (Fable, Argon, Kimi, DeepSeek)
vs none (Sol, Grok, Claude); start November (most) vs not (Grok).
CHANGED-MY-MIND: E1 overclaim and "close to P" withdrawn; justification for H moved to the label horizon; storage
from public field to hash commitment; Q5 from a pinned bar to no bar now.
