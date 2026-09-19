VOTE: APPROVE

Reservations for the record, none blocking:

1. **§1.5 override record.** "Independent verification performed" for a CAPE outlier will in practice mean checking multpl's value against the S&P 500 monthly mean and CPI we already fetch — i.e. against the *inputs* to CAPE, not an independent CAPE. There is no keyless independent CAPE source; the record should say what was checked rather than imply an independence that does not exist.

2. **§3.3 schema migration.** Adding the `kalibrering` column to the two existing ledger rows is the first time anything is written into a historical row other than its note field. The consensus text authorises it explicitly as metadata; I want the README to quote that authorisation next to the rule "historical rows are never edited" so a reader does not have to reconcile them.

3. **§8 ordering.** Step 1 requires the new tests to *fail* on the current state before the fix. The staleness guard and the eligibility audit will; the legacy replay by construction passes already. That is fine — but the commit history should show the failing tests first, so the repair is visibly a response to a detected defect and not a refactor with tests added afterwards.
