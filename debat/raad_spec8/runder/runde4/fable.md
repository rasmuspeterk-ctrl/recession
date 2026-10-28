VOTE: APPROVE

The text carries everything I conditioned on: canonical serialisation, same-commit hash, one line per row, episode-block bootstrap named as the only procedure, Kimi's stopping rule, ≥ 2 post-sealing onsets, matched comparator, 2024Q1 disclosure, November start. Three reservations for the record.

**R1 — the hash timestamps; it does not hide.** §2.5 prints β₁, β₂ and the scaling at sealing, and `curve_min12` is reconstructible from FRED forever. Anyone with the spec and the live curve can recompute `p_hukommelse` to four decimals; the 128-bit nonce only stops guessing the line, not computing its content. That is acceptable — the commitment's job is to prove what was forecast when, and the distribution veto concerns a rendered number, not a recomputable one — but §3.2 should not imply secrecy. Suggested wording: "the hash proves the record's existence and content at commit time; the probability is in principle recomputable from the sealed coefficients." Rasmus should decide knowingly whether the coefficient vector goes in the spec or in the private file; I prefer the spec (auditability over concealment).

**R2 — the live row can violate the training invariant.** In the fit, curve ≥ curve_min12 by construction. On the live row (§2.3 + §2.1), curve is a trailing-daily month and min12 is over published months, so curve can fall *below* min12 in a fast steepening-reversal. The model then sees a feature configuration it never trained on. Not fatal; log a flag `min12_lt_curve` on the shadow line so a future council can see how often it happened.

**R3 — one refit vintage per evaluation, stated.** §2.4 refits every September; §4.1 pairs each row with its own vintage's P. Fine for paired log-loss, but the tracking record is then a sequence of models, not one. The spec should say that any onset scorecard labels each row's fit-vintage id, so a 2032 council cannot read a 2029-vintage slope as the sealed-2026 slope.

None blocks. Approve.