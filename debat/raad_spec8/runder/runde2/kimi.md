## Attacks

**Claude Opus:** “Every historical onset came during an inversion or within 9 months of its end” is false. The 1957, 1960 and 1990 onsets—**3 of the 12 fitting onsets**—had no qualifying inversion; 1966 supplies an inversion without a recession. E1 therefore cannot validate \(H=12\). Nor does today’s \(m_t=+0.24\) imply that the shadow will read “close to P”: joint fitting changes the intercept, both slopes and standardisation, so no bound on \(p_{\text{hukommelse}}-P\) exists before fitting.

**Gemini:** A scored sample of “only prospective origins logged from November 2026 onward” does **not** satisfy §8.3. November–December 2026 origins are pre-2027 observations and must remain audit-only. Its instruction to confirm \(\beta_2<0\) “or re-parameterize” is also an outcome-contingent specification fork. Replacing \([z(C),z(M)]\) with \([z(C),z(C-M)]\) changes the L2 penalty; ridge regularisation is not invariant to that transformation. It is a second model, not innocuous orthogonalisation.

**Grok:** The claim that §8.3 sealing is “not satisfied by sealing the bar in the same sitting that shopped H” is incorrect. The judged onsets can all postdate sealing, and every pre-2027 origin can be excluded from scoring. Contamination prevents historical validation and requires disclosure; it does not prohibit prospective instrumentation. Grok’s narrower point stands: \(H=12\) cannot answer whether memory binds after the current 22-month lag.

## Steelman

GPT’s strongest contribution is that **a public machine-readable ledger is distribution**. My Round 1 treatment of `hovedbog.jsonl` as automatically non-user-facing was unjustified. If it is public or rendered downstream, `p_hukommelse` belongs in a private append-only companion ledger keyed to public row identifiers and hashes. Publish the specification, code, vintages and completeness audits—not the probability series.

## Revisions

I retain one two-feature shadow, the operational fitting conventions and the November start. I now justify \(H=12\) primarily by its equality with the four-quarter label horizon; v4 supplies implementation provenance, not statistical support. The choice remains post hoc and cannot address long-duration memory.

Q3 must additionally disclose that resolved zero labels through 2025Q3 already inform the fit about the 2022–24 episode. There will be no coefficient-sign gate or reparameterisation.

I retain Q5’s single paired comparison, but explicitly as a **descriptive agenda screen, not a confirmatory superiority test**: quarterly origins from 2027 onward only, matched curve-only vintages, my fixed stopping rule and 16-quarter block procedure. No repeated September significance tests; failure to cross the bar is not evidence against memory. November establishes operational integrity and future prospective coverage, not validation on the present cycle.

AGREE:
- Operational P, its band and verdict remain untouched; no 24/36-month runs or additional memory candidates.
- If anything is fitted, use curve plus `curve_min12`; pre-2027 fitting is contaminated and is not validation.
- No dashboard display and no LOG.md exposure before the 2027 refit; any future comparison requires at least two post-sealing onsets and never switches P automatically.

DISAGREE:
- **Grok versus the other six:** log only `curve_min12`, or nothing, versus logging a shadow probability.
- **GPT and Grok versus Kimi, Gemini, Fable, DeepSeek and Claude Opus:** defer any numerical comparison rule versus sealing an agenda screen now.
- **Block procedure among screen supporters:** 4-quarter moving blocks, mean-8 stationary bootstrap, 16-quarter blocks, 20-quarter blocks, or episode blocks.
- **Storage:** GPT and Kimi require a private companion if `hovedbog` is public; the draft supporters still specify `hovedbog` directly.

CHANGED-MY-MIND:
- Demoted v4 pre-existence to an implementation tie-breaker; adopted the label-horizon rationale and abandoned E1 as validation.
- Extended the distribution argument to public machine-readable ledgers.
- Narrowed the November-start rationale: 2026 rows are audit-only, and this shadow cannot test the motivating 22-month-lag hypothesis.