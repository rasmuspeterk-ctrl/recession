VOTE: APPROVE

All three blocking amendments from my previous vote are incorporated: historical ledger rows remain protected; eligibility changes are audited by origin identity rather than assumed monotonic growth; freshness checks are release-aware and do not make curve-only production dependent on CAPE.

Three non-blocking reservations for the implementation record:

1. **§8 — Not every new test should fail before repair.** The staleness and omitted-eligible-origin tests must expose the existing defect. Legacy replay should already pass. Synthetic-observation and eligibility tests need explicit defective fixtures where appropriate. The acceptance criterion is demonstrated defect detection—not artificially making every assertion fail.

2. **§4.3 — “80% coverage” is nominal, not established.** The 10–90% endpoints contain the central 80% of bootstrap draws; that does not establish 80% repeated-sample coverage with 13 dependent episode blocks. Print **“central 80% bootstrap estimation-sensitivity band; coverage not established.”** The supplementary rule remains diagnostic, with Section 6 unchanged.

3. **§7.1–7.2 — Report coefficients on comparable scales.** Alongside the standardised coefficient, print the raw curve slope \( \beta_{\mathrm{curve}}=w_1/s_{\mathrm{curve}} \), with the curve measured in percentage points, and the raw intercept \( \alpha=w_0-w_1\mu_{\mathrm{curve}}/s_{\mathrm{curve}} \). Otherwise a change in training-window dispersion can be misreported as coefficient dilution. Fixed-input probabilities remain the relevant measure of the recalibration’s operational effect.

This approval authorises the specified repair and reporting protocol—not feature reopening, automatic full-model promotion, or retrospective alteration of published forecasts.