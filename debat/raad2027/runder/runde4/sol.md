VOTE: REJECT

One executable ambiguity remains. Fix it and I approve.

**Replace §9.2 with:**

> An origin dated \(q\), with forecast-window end \(H(q)=q+12\) months under the committed quarterly dating convention, enters `eligible_fit(R)` iff:
> 1. \(R \ge H(q)+L_R\); and
> 2. its censoring status is resolved using only announcement information available at \(R\).
>
> “Age ≥ \(L_R\)” means age **since forecast-window end**, not age since origin. With \(L_R=18\), minimum maturity is therefore \(q+30\) months, not \(q+18\).

**Add to §9.3:**

> Date-stamped eligibility tests, including the 1991 and 2001 episodes, must verify both conditions before the first audit runs.

The current draft explicitly invokes \(q+12+L_R\) in §9.1 but leaves “age” undefined in its operative eligibility rule. Implementing age from the origin would admit labels 12 months prematurely and invalidate the arithmetic supporting the lag compromise. This is not a cosmetic objection.

Everything else incorporates my compromises: the frequency override is explicit; the gate makes no calibrated significance claim; and the content-trigger regime receives its own replay. I accept those decisions despite their known effects for the reasons recorded.