VOTE: APPROVE

Reservations for the record:

1. **Bootstrap volatility on n≈12:** Bootstrapping a sample of roughly 12 episodes to construct a 10–90% estimation-sensitivity band will yield highly unstable bounds. Small-sample bootstraps systematically underestimate true tail risk. The resulting band will correctly demonstrate uncertainty, but will likely remain overconfident at the extremes.

2. **Monthly non-inferiority gate:** Requiring strict non-inferiority in episode-blocked skill for the monthly model may falsely reject it. Monthly data inherently carries a higher noise-to-signal ratio, which degrades log-loss, but the 60-to-90-day operational lead time gained over quarterly macroeconomic prints has real-world utility that the strict scoring rule ignores. 

3. **ACM pre-1961 penalty:** Forcing the ACM term-premium model to score at the unconditional base rate before 1961 is a necessary stricture to prevent look-ahead bias, but it biases the test against ACM if the 1934–1960 period had a localized base rate significantly different from the full-sample average. If the ACM test fails by <0.5% log-loss, a secondary truncated-sample comparison (1961–2024) should be published alongside it to isolate whether the failure is due to the missing data penalty or actual signal degradation.