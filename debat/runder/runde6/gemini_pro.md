VOTE: APPROVE

**Reservation 1: The 18-month embargo floor (Section 1)**
The 18-month minimum embargo is excessively conservative. While NBER announcement lags vary (e.g., 2008 was 12 months, 2020 was 3.5 months), forcing a minimum 18-month blind spot starves the walk-forward training set of recent data. A 12-month floor captures the vast majority of historical NBER lags while allowing the model to adapt to regime shifts half a year faster. The annual audit ($L_R$) already protects against longer anomalies.

**Reservation 2: ACM term-premium look-ahead bias (Section 5)**
The ACM term-premium test introduces hidden look-ahead bias and operational fragility. ACM is a derived model, not a raw observable. The NY Fed frequently revises historical ACM estimates based on full-sample smoothing. Using current-vintage ACM data to test historical walk-forward skill violates the strict real-time information constraint unless you source true vintage ACM series (which are not cleanly available via standard FRED APIs). If the ACM test passes, it likely does so on the back of this look-ahead leakage.

**Reservation 3: Bootstrap persistence threshold (Section 4)**
The bootstrap persistence threshold of 60% is too low given the hard cap of 6 features and $n \approx 12$ episodes. A 60% sign-agreement across resamples allows features that fail in 4 out of 10 alternate histories to maintain "admitted" status without a warning flag. A 75% persistence threshold would better guard against overfitting to the specific sequence of late-20th-century recessions.