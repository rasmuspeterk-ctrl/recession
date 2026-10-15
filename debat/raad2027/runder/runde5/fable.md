VOTE: APPROVE

The Round-4 condition is met. §3.2(b) now cites an artifact with path, n_parrede_origins 198, labels_uenige 0, identical pooled base rate 0.1616 and baseline log-loss 0.4423; the count is consistent with censoring (226 quarter-end months 1967-12…2024-03 less censored origins = 198, so 591/3 ≈ 197 was the wrong arithmetic on my side). §3.3 seals the in-code identity check on the 2027 panel, §9.2 is Sol's wording, §1.2 takes the power-clause relabelling. Nothing in §11 has changed in substance; each row remains a tightening, a disclosure, or the status quo with the override recorded verbatim, and P is untouched before 2027-09.

Reservations for the record, non-blocking:

1. **§3.2(b) is verified by an interested party.** I accept it on the cited artifact and the independent verifier's reproduction via ablation3's own `wf_monthly`, not on the secretary's note. The in-code check in §3.3 should assert the three identities (origin set, labels, pooled base rate) and fail loudly, not merely print them. The minute's "does not favour monthly" must not be read as "monthly is worse": −1.02 pp with SD 2.58 is sign-uninformative.

2. **§9.3 tests need negative controls.** For each of 1991 and 2001, the date-stamped tests should check both boundaries: the origin is excluded at R = H(q) + L_R − 1 and included at R = H(q) + L_R, and an origin inside the episode stays censored at every R before the trough announcement. A test that only confirms inclusion would not catch the age-from-origin bug Sol identified.

3. **§8.3 remains a half-open door.** Gemini's point stands: a β_EBP fitted on the inspected 1973–2026 pattern and scored on two later onsets largely tests recurrence of what was seen. Disclosure does not remove that bias. A future council should read §8.3 as "prospective fit and prospective score", with pre-2027 use requiring an explicit, sealed justification — not as a default permission.