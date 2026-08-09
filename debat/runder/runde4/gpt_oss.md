VOTE: APPROVE

**Reservations for the record**

1. **Manual CAPE/margin debt updates** – The model still relies on a human‑edited override for Shiller CAPE and FINRA margin debt. A clear, versioned update protocol (e.g., a scheduled GitHub action that pulls the latest spreadsheet and flags any changes) should be documented to avoid stale inputs.

2. **Bootstrapped sensitivity band** – The 10–90 % band printed with each probability is an estimation‑sensitivity range, not a frequentist predictive interval. The documentation should explicitly state this distinction and advise users that the band reflects model‑parameter uncertainty, not future‑outcome uncertainty.

3. **6‑month training embargo** – Excluding the most recent six quarters from each refit protects against look‑ahead bias, but the rule may need adjustment if data revision lags shrink or if the GDP series becomes more stable. A periodic audit (e.g., annually) to confirm that the embargo still yields unbiased training windows is recommended.