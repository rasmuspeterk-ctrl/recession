**1) Attack**

- **Claude Opus 5.5, Q2:** "It agrees with E1: every historical onset came during an inversion or within 9 months of its end." Reject. E1 itself states 1953–1965 and 1990 had no qualifying ≥3-month inversion, so the 1957, 1960 and 1990 onsets contradict that sentence. A 12-month floor has zero memory signal for 3 of the 12 onsets. Claiming "agrees with E1" filters E1 to the subset the variable can remember while ignoring the rest — and that filtered claim happens to pick the horizon that reads +0.24 today rather than −0.41 or −1.22.

- **Gemini, Q3:** "alternatively parameterize the model orthogonalized by construction as level C_t and re-steepening Δ_t⁺ = C_t − M_t." Reject. L2 logit with λ=1 on two standardized raw columns is not rotation-invariant; changing to C and C−M rewrites the shrinkage target, not merely the representation. C−M has near-zero variance during long inversions and spiky variance at re-steepening. Standardizing it gives unit variance to the noisiest transition points, which worsens estimation with 12 onsets. It is also a newly constructed feature chosen with E1/E2 visible.

**2) Steelman**

GPT-6.1 Sol Pro's Q4 point is the best thing I missed: if `hovedbog.jsonl` is publicly distributed, then a machine-readable `p_hukommelse` field is itself publication. "Unscored" does not stop a screenshot or downstream table. I adopt its fix.

**3) Revise**

- **Q4 changed:** `p_hukommelse` goes into a private append-only companion archive if the main ledger is public. The public gets the sealed spec and code hash, not the number.
- **Q5 changed:** I drop my pre-pinned scored comparison from this spec. GPT is right that block length, SE estimator and repeated looks cannot be pinned before the number of post-sealing origins is known, and two onsets cannot resolve MDE80 ≈ 30 pp. Tracking stays unscored; any scored test requires a future council mandate sealed before the onsets it would use.
- **Q2 amended:** keep `curve_min12` only because it pre-dates E1/E2. I no longer defend it as matching E1; the spec must state it is blind to 1957, 1960, 1990 and to the current 22-month lag.
- **Q3 amended:** freeze standardisation means/SDs, code/data hashes, eligibility exclusions and the fitted coefficient vector as versioned metadata; do not only freeze the formula.

**AGREE**
- Memory model is a shadow only; nothing changes P.
- Single variable `curve_min12`, H=12, v4 definition.
- Curve + memory, standardised, λ=1, operational universe/labels/refit.
- Not dashboard, not LOG.md; public spec, private probability.
- Start November 2026 row; pre-2027 fitting disclosed as contaminated.
- No automatic switch ever.

**DISAGREE**
- Grok: no probability at all, state only vs rest: a shadow probability is acceptable if private.
- GPT/Grok/now DeepSeek: unscored tracking only vs Claude Fable/Kimi/Gemini/Claude Opus: seal a scored bar now.
- Gemini: orthogonalized reparameterization vs others: keep raw standardised features.
- Claude Opus/Gemini Fable: E1/lag justifies H=12 vs GPT/Grok/Kimi/DeepSeek: only pre-existence justifies it.

**CHANGED-MY-MIND**
- Public ledger means public number: moved to private archive.
- Scored comparison: dropped from this spec; future mandate only.
- H=12 "matches E1": withdrawn.