VOTE: APPROVE

Astra's three amendments are each an improvement on what I drafted, and I record why: the prospective-only calibration column removes the one exception I had written into "historical rows are never edited"; the signed membership audit is correct where "n_obs must grow" was wrong (Kimi's reservation showed the same false-fail at the next dated peak); and the release-aware freshness rule fixes a guard that would have failed on the very reading it was meant to protect.

Reservations for the record, none blocking:

1. **§1.7 release-lag table is now a protocol artefact.** The per-series expected-release rule lives in fetch.py's series table and is therefore under version control — but it is also a set of assumptions about publication calendars that can change (BLS/BEA reschedules, shutdowns). A missing release should fail the stage, as written; it must not be silently "fixed" by loosening the table. Any change to the table is a commit with a stated reason.

2. **§1.4 seam cross-check uses Yale's own preliminary earnings** for 2023-08/09. The check is still worth doing — it bounds the discrepancy — but the record should say the earnings input is itself preliminary, so the cross-check verifies consistency, not truth.

3. **§3.2 next-publication-run execution** means a refit triggered by an NBER announcement lands in a ledger row together with that month's new data. The bridge row separates the two effects at fixed inputs, which is sufficient — but the note column of that row should name the announcement as the trigger, so the row is readable without the manifest.
