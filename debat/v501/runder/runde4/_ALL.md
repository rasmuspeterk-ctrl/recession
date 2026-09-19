# ROUND4 — samlet


---

## GPT-6 Astra (OpenAI)

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

---

## Gemini 3.8 Flash (Google)

VOTE: APPROVE

### Reservations for the record

1. **Paired-difference coverage width (§4.3):** Adopting the 10–90% bootstrap band (80% coverage) as the supplementary criterion is adequate for an informational diagnostic, but it remains an unusually permissive threshold for distinguishing an operational forecast from the unconditional base rate. Prior to any future council debate regarding an operational verdict migration, the backtest must formally evaluate the empirical Type I error rate of this interval against synthetic, uninformative exchangeable sequences.

2. **Asymmetric loss impact of unannounced contractions (§4.5):** Disclosing the count and loss contribution of "additional live-publishable origins" (unannounced in-recession quarters) correctly prevents penalizing curve-steepening onset dynamics. However, the council must recognize that printing the score excluding these origins creates an unavoidable selection bias: it evaluates the model exclusively on cycles where the NBER dating committee acted with sufficient speed or where expansions persisted. Both variants must be interpreted strictly in tandem, never cited in isolation.

3. **Parameter variance across event-driven refits (§3.2, §3.4):** Triggering an immediate re-anchor upon NBER turning-point announcements introduces parameter volatility precisely during cyclical transition regimes. While the deterministic execution rule and mandatory bridge row eliminate discretion, estimating weights on freshly minted turning points risks over-indexing on the terminal dynamics of the latest shock. The bridge row must be monitored carefully to verify that absorbing a new trough does not induce sudden probability compression in the subsequent non-recession quarters.

---

## Kimi K3 (Moonshot AI)

VOTE: APPROVE

All three of my Round-3 conditions are in the text. §2's gate assertion is a hard error printing "comparison unavailable", with per-model estimation end and n_obs in the manifest — a divergent-sample operational estimate is identifiable from the ledger hash. §4.5 prints the oracle-free supplement twice under the strict onset label and explicitly excludes scoring any other target; my Y′ veto is not engaged. §4.3 fixes the backtest specification (same origins, same draws, disagreement count and disagreeing origins published), bars automatic verdict migration, and mandates the README sentence; my O4 veto is not engaged. §3.2's trigger is a hash change adding a peak or trough, executed at the next publication run — deterministic, as required. §1.5 puts `--accept-outlier` in the ledger note column. §1.6 implements the staleness guard first, and §8 commits §1–§3 before §4–§7 are seen. The preregistration logic is enforced by execution order, not by goodwill.

Reservations for the record (non-blocking):

1. **§3.5's n_obs assertion assumes monotonic growth.** "n_obs must grow by exactly that number" is wrong in general: a newly dated peak simultaneously matures pre-peak origins (label 1) and censors post-peak origins the 18-month floor had just released. The assertion should be that n_obs equals the audit's *signed* eligible count — additions minus reclassifications, both lists printed. As written it will false-fail at the next recession dating, or worse, be silently relaxed when it does.

2. **The seam months are adopted, not verified.** The composite takes multpl CAPE for 2023-08/09 — precisely the two months with the largest overlap deviations (−1.25 %, −3.28 %), where Yale was preliminary. §1.2 documents the exception; nothing checks the adopted value. Add a one-time archived cross-check: CAPE for those two months hand-computed from FRED SP500 monthly means and published S&P earnings, stored in meta.json.

3. **The multpl failure mode is underspecified.** §1.3 guarantees no partial spine and §2 frees curve-only estimation from CAPE, but the monthly full-model line ("tested, did not pass") has no stated behavior when CAPE is stale. Specify: on multpl failure that line prints "unavailable — CAPE stale"; the last good value is never carried forward silently.

---

## Claude (Opus 5) (Anthropic — interested party)

VOTE: APPROVE

Reservations for the record, none blocking:

1. **§1.5 override record.** "Independent verification performed" for a CAPE outlier will in practice mean checking multpl's value against the S&P 500 monthly mean and CPI we already fetch — i.e. against the *inputs* to CAPE, not an independent CAPE. There is no keyless independent CAPE source; the record should say what was checked rather than imply an independence that does not exist.

2. **§3.3 schema migration.** Adding the `kalibrering` column to the two existing ledger rows is the first time anything is written into a historical row other than its note field. The consensus text authorises it explicitly as metadata; I want the README to quote that authorisation next to the rule "historical rows are never edited" so a reader does not have to reconcile them.

3. **§8 ordering.** Step 1 requires the new tests to *fail* on the current state before the fix. The staleness guard and the eligibility audit will; the legacy replay by construction passes already. That is fine — but the commit history should show the failing tests first, so the repair is visibly a response to a detected defect and not a refactor with tests added afterwards.
