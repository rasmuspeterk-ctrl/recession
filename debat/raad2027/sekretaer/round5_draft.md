# CONSENSUS TEXT — the September-2027 refit agenda (Round 5 draft for ratification)

Assembled by the secretary (Claude Opus 5.5, a party) from Rounds 1–3. Where a councillor's condition was
accepted, it is written into the text; reservations go on the record and do not block.

**Changes from the Round 4 draft** (Round 4: 5 APPROVE, 2 REJECT):
- §9.2 is replaced by Sol's wording (age is measured from forecast-window end), and §9.3 adds date-stamped 1991/2001 tests (Sol).
- §3.2(b) now cites the artifact and the verified origin identity (Grok; Fable and Kimi reservations).
- §1.2, §3.3 and §6.2 take in non-blocking reservations from Kimi and Fable that tighten without changing any decision.
- Nothing else changed.

**Secretary's verification for Grok, Fable and Kimi (§3.2(b)):** `v5/analyser/frekvensgate_resultat.json`, path
`paneler/b_v501/modeller/curve_only/parret_tyndet_vs_kvartal`:
- forskel_pp −1.02, sd_pp 2.58, ci10 −4.47, ci90 +1.32 (episode-block bootstrap, 1000 draws, seed 42);
- `n_parrede_origins` 198, `labels_uenige` 0.

The thinned m%3==0 set and the quarterly set are the same 198 origins: 1967Q4–2024Q1, quarter-end months
1967-12…2024-03, 32 positives each, identical pooled base rate 0.1616 and identical baseline log-loss 0.4423.
The script's own note reads: "Tyndet m%3==0 er kvartalsslut-maanederne og er origin-identisk med
kvartalsmodellen (parret, som ablation3)".

So (b) *is* a monthly-fit model scored on the 198 quarterly origins, paired against the quarterly fit, with
the same labels and base rate. The independent verifier reproduced it with ablation3's own `wf_monthly`. The
*unpaired* comparison is the full-monthly one (591 vs 198, `blok_fuld_vs_kvartal`, which the JSON itself labels
"forskellige origin-maengder").

## 0. Nature and timing

These decisions are preregistered on 2026-10-15. They are committed and pushed before the September-2027
refit and take effect at that refit (R = 2027-09), unless marked **[now]** (documentation only; P untouched).
The weights in operation stay frozen at 72c3371d until then. Every decision here was taken with its effect
known. The final section states for each one why that is acceptable.

## 1. λ (Q1)

1.1 λ = 1 is kept as an **inherited constant** (from v4, built on overlapping history). §3 of the blueprint
is amended: "L2 penalty fixed at λ = 1; not selected inside training windows". It is never described as
a priori, optimal, or confirmed by ablation9.
1.2 **[now]** Every published skill statement prints, in this order and in one sentence:
- (i) **oracle-free fixed-λ walk-forward** (today +20.37 %, 219 origins; the scoring key's own reference);
- (ii) oracle-censored fixed-λ (today +27.05 %, 198);
- (iii) nested λ, oracle-censored (today +18.32 %, 198; its oracle-free counterpart has not been computed).

  The same sentence carries the power clause: "≈ 150 calendar years of ledger are needed for 80 % power;
  P(3 complete cycle blocks within 20 years) = 0.25; naive tests reject a true null 36–53 % of the time at
  5–20 years". +27.05 % never appears as a standalone public figure.
  At the 2027 refit the nested-λ oracle-free figure is computed, so the sentence compares three realised numbers.
  The power clause is re-derived from the §6.2 configuration-specific replay once it exists, and is labelled
  "order of magnitude". The ≈ 30 pp MDE of §2.3 is labelled a normal-theory approximation.
1.3 Figures belong to the configuration that produced them. No historical figure is presented as the
performance of a changed configuration (§6) without that configuration's own sealed replay.

## 2. Model selection and the benchmark gate (Q2, F8)

2.1 Blueprint §4 is amended: no per-origin model selector is run. Curve-only is operational by council
lock (RAADETS_V501 §6); F5 is a frozen benchmark and never switches anything.
2.2 The repo's "MDE" figures (4.42 pp, 21.06 pp) are 1.96·SD_block of a paired difference, i.e. two-sided
critical values, not 80 %-power MDEs. They are renamed everywhere; **[now]** in documentation.
2.3 From 2027 the gate is as follows.
- Δ = skill(F5) − skill(curve) on common origins.
- If Δ > 1.96·SD_block(Δ), recomputed at each refit, the result is a **mandatory council agenda item**. This is an *administrative review boundary, not a calibrated significance test*: crossing it is never labelled "evidence" and never switches anything.
- Printed beside it: the 80 %-power MDE (≈ 2.8·SD_block; ≈ 30 pp today), Δ without the largest-contributing episode block, and Δ at universe starts 1953Q2 and 1960Q1.
- The borrowed 4.42 pp is removed from the gate.

## 3. Fit frequency (Q3, review G1.3)

3.1 The quarterly fit is retained.
3.2 The minutes record, verbatim: "**The preregistered §2 gate as written in RAADETS_KONSENSUS passed**
(full monthly walk-forward +36.83 % vs requirement 32.23 % on the v5.0 panel, published 2026-08-09; +29.24 %
vs 26.05 % on the v5.0.1 panel). **The gate executed in ablation3 — a quarter-thinned score, fixed before the run
following blueprint-round reservations by Sol, Kimi and Gemma — failed** (32.08 vs 32.23; 26.03 vs 26.05).
**The council declines to apply the written gate.**"

  Reasons recorded:
  - (a) the written comparison is unpaired, across different origin sets with their own pooled base rates;
  - (b) the paired comparison on identical origins is −1.02 pp (10–90 % [−4.47, +1.32]; episode-block bootstrap, 1000 draws, seed 42). It compares the monthly-fit walk-forward scored at the quarter-end months with the quarterly fit, on the same 198 origins, with 0 label disagreements and the same pooled base rate 16.16 %. Source: `v5/analyser/frekvensgate_resultat.json`, `parret_tyndet_vs_kvartal`. This does not favour monthly;
  - (c) +2.19 pp full-vs-quarterly is below its 2.99 pp block critical value;
  - (d) under a summed loss, λ = 1 on ~800 monthly rows is a different penalty per observation than on 267, and no normalisation was sealed in advance.
3.3 From the 2027 refit a monthly curve-only fit is calibrated each September alongside the quarterly one.
Its P is logged as an **unscored** column in every ledger row. Its specification, including the loss/penalty
normalisation, is sealed and pushed before the 2027 refit. The sealed spec also re-runs the paired same-origin
diagnostic of §3.2(b) on the 2027 panel, with origin-set and label identity checked in code. Its outcome is
unknown at sealing, and it is published whatever it shows.
3.4 **General clause, prospective, both directions:** when a ratified written specification and its
implementation conflict, the written specification governs. Any conflict discovered is declared and put
before the council. The clause is not applied retroactively to §2.

## 4. Universe start (Q4, F34)

1947Q2 is kept. **[now]** P at starts 1953Q2 and 1960Q1 is printed in every diagnostics report; from 2027
it is also an unscored field in every ledger row.

## 5. Demotion (Q5, G1.4)

5.1 **[now]** Documentation states both readings:
- under incumbent-as-challenger symmetry only the curve survives (simultaneous and backward elimination);
- under drop-side symmetry nobody is demoted;
- "5 incumbents pass" holds only under step 4's asymmetric rule.
5.2 Any future search (only by council mandate) fixes one numerically pinned symmetric bar for
incumbents and challengers in the sealed spec before any run. curve+cape (+2.64 pp, fails G2/G3/G5) is not a candidate.

## 6. NBER content trigger (Q6, G4.1)

6.1 From the 2027 refit, refits occur in September, on a change of the announcement table's hash, and on a
**content trigger**:
- **one** refit per new onset, in the first month where `eligible_fit(R)` contains a positive label of that onset absent from the manifest;
- in any month where `eligible_fit(R)` contains a **relabel**.

  Routine maturation of negative origins never triggers. Later positives of the same onset wait for September.
  Triggers never alter labels or censoring; the trigger month is logged in the manifest.
6.2 A configuration-specific replay (September + hash + this trigger) is specified, sealed and pushed before
the 2027 refit, and published as the ledger supplement for this regime. Like §7.2, it prints all three censoring
variants (real-time open-episode rule first). Adoption is not conditional on the replay's score.
The September-only replay figures (+24.41 / +28.95 / +33.28) are never described as this regime's skill.

## 7. Ledger key (Q7, G3.2/G3.5)

7.1 BEDOEMMELSESNOEGLE.md is **not amended**.
7.2 **[now]** E5 is published as a supplement:
- real-time (engine open-episode rule) +24.41 %;
- real-time without the USREC-vintage assumption +28.95 %;
- oracle +33.28 %;
- pooled ex post +21.2 %;
- the logged base rate averages 22.8 % against a realised onset rate of 15.3 %;
- per-block skills;
- cluster-t 1.37 over all 9 blocks (the 7-complete-block figure is not cited).

  The 2020–24 block is described as adverse, not invalid.
7.3 **[now]** No nominal significance claim is made from the key's inference machinery. The public sentence
of §1.2 carries the power figures; the ledger is described as an honesty instrument, not a test.

## 8. EBP and Baa-10y (Q8, F37)

8.1 Baa-10y is closed: it cannot be redistributed, so it cannot enter a reproducible public protocol.
8.2 The historical sealed test of EBP is **closed permanently**: the onset pattern (high before 1990/2001;
low before 1980/2008/2020) has been seen. EBP stays a context line.
8.3 A future council may specify a prospective-only evaluation under these conditions:
- it is sealed before any onset it would be judged on;
- no pre-2027 EBP observation is ever used as evidence;
- whether pre-2027 data may be used for fitting is for that council's sealed spec, which must disclose the contamination;
- a scored test needs ≥ 2 post-sealing onsets (decades), and this is stated;
- even an unscored tracking column requires a ≥ 12-snapshot revision audit first.

## 9. Announcement-lag audit (Q9)

9.1 The annual audit computes **L_R = max(18, max lag_peak, max lag_trough − 12)**:
- lag_peak is measured from peak month to peak announcement;
- lag_trough is measured from trough month to trough announcement;
- the −12 is the label window, since an origin matures at q + 12 + L_R.

  Today: max(18, 12, 9) = 18.
9.2 An origin dated q, with forecast-window end H(q) = q + 12 months under the committed quarterly dating
convention, enters `eligible_fit(R)` iff:
1. R ≥ H(q) + L_R; and
2. its censoring status is resolved using only announcement information available at R.

"Age ≥ L_R" means age **since forecast-window end**, not age since origin. With L_R = 18, minimum maturity is
therefore q + 30 months, not q + 18.
9.3 Both inequalities of §9.1 are written into the audit before it first runs. If either is breached, the
refit halts pending a council decision. Before the first audit runs, date-stamped eligibility tests
(including the 1991 and 2001 episodes) must verify both conditions of §9.2. The trough term is an audit
check on censoring resolution, and a breach of the peak term halts the refit on its own (DeepSeek).

## 10. Ratification of operational changes made without mandate (Q10, F29)

10.1 Live curve = trailing month of daily DGS10 − DTB3. **Ratified as an acknowledged instrument change**
(not measurement-identical to GS10 − TB3MS). P on GS10 − TB3MS stays dual-logged in every row permanently.
10.2 Swarm tripwires out of the ignition column: ratified (restores an R3 decision).
10.3 Log day (first weekday from the 10th, + 3 days): ratified as executable in the committed key.
10.4 Live censoring inside an announced recession: ratified on two conditions:
- the live rule is byte-identical to the key's open-episode rule and is written into the protocol before the 2027 refit;
- every censored month keeps an **unscored** record of P and the eventual outcome (UDFALD.csv supplementary column).

  The minutes note that (1) and (4) were made without mandate and are ratified ex post.

## 11. Why each post-hoc decision is acceptable

| § | Decision | Why acceptable despite known effects |
|---|---|---|
| 1 | λ = 1 kept | Incumbent constant, disclosed as inherited; the alternative (nested) is design-dependent with 9–13 blocks; the nested figure stays printed |
| 1.2 | Oracle-free headline | Lowers the headline; matches the preregistered key's reference |
| 2 | No selector; renamed gate | Withdraws a procedure that chose the worse model; renaming moves no number; the threshold is stricter than before |
| 3 | Quarterly retained | The override is recorded in so many words; the paired evidence does not favour monthly; monthly is logged unscored, so the question stays open on the record |
| 4 | 1947Q2 kept | The locked constant; moving it would lower P by 2.5–4.5 pp after seeing that |
| 5 | Documentation | Withdraws an unsupported claim; no number moves |
| 6 | One trigger per onset | Mechanical; max historical effect ≈ 1 pp; replay sealed before adoption; not conditional on its score |
| 7 | Key untouched | The alternative would move goalposts after the score |
| 8 | EBP closed historically | Forbids using what was seen |
| 9 | L_R formula | Binds nowhere historically; tightens (adds a check), relaxes nothing |
| 10 | Ratification | Ex post, recorded as such, with conditions that make each change auditable |

## 12. Order of execution

1. **[now]** Commit this text as RAADETS_2027.md together with the transcripts. Push before any code is written.
2. **[now]** Documentation: §1.2 sentence (README, motor, dashboard), §2.2 renaming, §5.1, §7.2–7.3, §10 notes.
3. Before 2027-09, each in its own commit, each sealed spec pushed before it is used:
   - the gate (§2.3);
   - the L_R audit (§9);
   - the content trigger and its replay spec (§6);
   - the monthly-fit spec and the unscored columns (§3.3, §4, §10.4);
   - the live-censoring rule text (§10.4).
4. 2027-09 refit: run as specified; publish the F35 comparison and all results.
