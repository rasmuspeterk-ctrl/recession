VOTE: APPROVE

Reservations for the record:

1. The 6-feature hard cap with only 11 episodes still risks overfitting; the admission gate's dual-threshold (≥2% log-loss + ≥2pp Brier) plus LOEO stability is necessary but not sufficient. I would prefer an explicit out-of-sample holdout (e.g., post-2010) as a final gate, but accept the bootstrap-persistence flag as a pragmatic compromise.

2. The ACM term-premium test's "pre-1961 missing years score at base rate" injects 27 quarters of uninformative predictions into the walk-forward path, which penalizes the substitution mechanically rather than diagnostically. The truncated-sample secondary comparison (A5) mitigates this, but the primary test's penalty should be acknowledged as a design choice, not a pure skill test.

3. The monthly gate's −1pp non-inferiority margin is arbitrary relative to the minimum detectable effect (MDE) at n≈12 episodes. Printing the MDE next to the gate result (A3) is good, but the decision rule should reference the MDE explicitly: adopt monthly only if the skill difference's confidence interval excludes −MDE, not merely a fixed −1pp.