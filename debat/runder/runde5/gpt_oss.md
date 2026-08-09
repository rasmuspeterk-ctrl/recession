VOTE: APPROVE

**Reservations**

1. The 1‑percentage‑point non‑inferiority margin for the monthly gate may be too generous given the small number of episodes; a tighter margin (e.g. 0.5 pp) would reduce the risk of adopting a noisier monthly model.

2. The episode‑bootstrap band (10–90 %) is a useful sensitivity diagnostic, but its computation adds non‑trivial runtime and memory overhead; a simpler 90‑10 % confidence interval on the log‑loss could be considered as an alternative.

3. The blueprint requires a maintained table of NBER announcement dates. If this table is not updated promptly, the real‑time label rule may misclassify recent horizons. A lightweight automated check against the NBER API (or a static snapshot) would mitigate this risk.