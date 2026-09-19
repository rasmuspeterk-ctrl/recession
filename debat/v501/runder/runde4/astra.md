VOTE: REJECT

The negotiated O1–O7 compromises are incorporated. Three implementation clauses still need correction; none requires reopening those compromises.

**1. §3.3 — Preserve the historical-ledger constraint.**  
Adding calibration hashes to existing rows is prohibited by the stated rule allowing retrospective changes **only in the note column**. Replace the migration sentence with:

> “Existing rows remain unchanged except for optional provenance annotations in their note column. A separate committed mapping links historical readings to the legacy calibration manifest. The new calibration column is populated prospectively.”

**2. §3.5 — Audit membership changes, not necessarily increasing counts.**  
“N_obs must grow by exactly [new origins]” is not generally valid under announcement-triggered recalibration: newly established chronology can change censoring, and corrected eligibility can remove observations. Replace it with:

> “Before fitting, publish added, removed and relabeled origin IDs with reasons. Assert \(n_{\mathrm{new}}=n_{\mathrm{old}}+n_{\mathrm{added}}-n_{\mathrm{removed}}\), exact membership agreement with the audited set, and label agreement for retained origins. Unexplained changes fail.”

Retain the 18-month-floor and synthetic-observation tests. This catches accidental sample changes without prohibiting legitimate ones.

**3. §1.6 — Make freshness release-aware and failure scope model-specific.**  
Age measured from an observation’s timestamp is not release latency. For example, August monthly data stamped August 1 are already **49 days old on September 19**, despite potentially being the latest available release. Replace the blanket limits with:

> “Each source has a committed release-lag/calendar rule specifying the latest observation expected at the publication cutoff. Unexpected missing releases fail the affected stage. Missing CAPE or another non-operational input blocks the full-model comparison and affected diagnostics, not an otherwise valid curve-only reading. No partial composite is accepted as complete.”

Otherwise the universal hard fail reintroduces the CAPE-hostage failure that §2 explicitly removes.

With those three edits, I vote APPROVE. The remaining compromises—including deterministic NBER-triggered refits and the supplementary paired rule—stand.