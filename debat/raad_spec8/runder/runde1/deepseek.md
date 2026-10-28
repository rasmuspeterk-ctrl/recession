## A) Positions on the agenda

**Q1 — At all?** Yes, a shadow model, but only as an unscored ledger field. The existing context lines are narrative; they cannot generate a likelihood or a future test. The question is whether the model should have memory, and the only honest way to answer that is to log a prospective, non-user-facing `p_hukommelse` with no role in P. This is not a second P; it is a data column that accumulates evidence. I accept it despite the post hoc motivation, because the decision costs almost nothing and does not touch the operational model.

**Q2 — Variable and horizon.** Use the pre-existing v4 definition:  
`curve_min12_t = min_{i=t−11,…,t}(DGS10_i − DTB3_i)`, observed monthly at the row’s latest month. I keep `H=12` solely because the definition predates E1/E2 and was part of the v4 grid. I reject H=24/36: E2 shows that choice would be picking today’s value, and no pre-registered rule justifies it. I reject candidates (b)–(d) because their thresholds or caps would now have to be chosen after seeing E1/E2. I accept the v4 tie-breaker only in its narrow form: `curve_min12` is a 12-month floor, not a duration memory. The spec must say that explicitly. Today it is +0.24, so the shadow will read near P; that is the honest consequence, not a bug.

**Q3 — Form and fitting.** Curve plus memory, not memory alone. Operational form stays two features: standardised curve and standardised `curve_min12`, L2 logit with λ=1, intercept, same universe and labels as P, quarterly origins 1947Q2 onward, 12 onsets. Standardisation uses the calibration sample mean and standard deviation frozen in the spec; coefficients are estimated on that sample and refit only at the September refit from the operational calibration’s snapshot and R, exactly as Claude proposes. Pre-2027 data may be used for fitting under §8.3, but only descriptively. The spec must disclose contamination from E1–E4, the grand review, and yesterday’s re-run. Formula:  
`p_hukommelse = logit⁻¹(β₀ + β₁·z_curve + β₂·z_curve_min12)`.

**Q4 — Where logged and shown.** Hovedbog only, as `p_hukommelse`, unscored, never on the dashboard, never in LOG.md before the September 2027 refit, and never presented next to P anywhere a screenshot can reach. This follows yesterday’s distribution argument. The field should be logged on the same row with the same curve vintage as P, and it is not revised. I keep Claude’s position as written.

**Q5 — Evaluation.** Unscored tracking now. A scored comparison happens only after at least two post-sealing onsets, and only against curve-only P on the same rows. I specify the bar exactly: compare mean paired log-loss per quarterly origin since sealing,  
`Δ = (1/N) Σᵢ [ −yᵢ ln p_shadow,ᵢ − (1−yᵢ) ln(1−p_shadow,ᵢ) + yᵢ ln p_P,ᵢ + (1−yᵢ) ln(1−p_P,ᵢ) ]`,  
with the difference computed shadow-minus-P so a positive value means shadow is worse. Use a moving-block bootstrap on the paired differences with block length 20 quarters; trigger an agenda item if `|mean Δ| > 1.96·SD_block`. Never an automatic switch. This is a pinned symmetric bar, but it is descriptive only until the onset count makes it informative.

**Q6 — Start date.** Start with the November 2026 row, log window 10–13 November, as Claude proposes. This begins the record before the current cycle resolves, which is the only way the record is prospective relative to this cycle. The spec must be sealed before that row is written.

## B) Verdict on Claude’s draft positions

- **Q1 — keep as written.** The framing is correct, and it respects the council lock that nothing changes P.
- **Q2 — keep the choice, amend the justification.** The v4 pre-existence is the valid tie-breaker, but Claude’s sentence that `curve_min12` “matches E1” overstates it. It is not the same as “every onset came within 9 months of an inversion’s end”; it is a rolling 12-month minimum. I would also add the disclosure that H=12 forgets the duration and depth of the 2022–24 inversion, so the shadow is a floor-memory model, not a full inversion-memory model.
- **Q3 — keep with amendments.** Add the exact standardisation and freeze the formula now. The refit schedule is acceptable, but the spec must state that all historical coefficients are contaminated and that no historical comparison is evidence.
- **Q4 — keep as written.**
- **Q5 — keep the unscored-then-scored structure, amend the bar.** Claude’s “beyond 1.96·SD_block” is too loose; I would pin the block bootstrap and the all-origin paired log-loss formula above.
- **Q6 — keep as written.**

## C) Single biggest risk in my own proposal

The biggest risk is that the shadow model is treated, later, as a real test of “memory” when it is not. With 12 onsets and a 12-month floor feature, `p_hukommelse` will differ from P largely through sampling noise and through a short-horizon floor that may not capture the mechanism the grand review actually named. If the current cycle resolves in a direction that makes the shadow look prescient, a future council may overweight a contaminated, underpowered result and push it toward P. Mitigation: keep it unscored, keep it off every user-facing surface, and require the council mandate and sealed prospective test before any scored comparison is even interpreted as evidence.