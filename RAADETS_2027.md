# RÅDETS KONSENSUS 2027 — dagsordenen til september-refitten 2027

Ratificeret **7/7 den 2026-10-15** (runde 5). Fuldt transkript, brief, sekretærfiler og kostlog ligger i
[debat/raad2027/](debat/raad2027/).

## Hvad rådet blev indkaldt om

Kode-reviewet 2026-10-15 sendte ti spørgsmål til "rådet før september 2027". De handlede om:
- λ og nested selektion (G1.1/G1.2);
- frekvensgaten (G1.3);
- universets start (F34);
- demotionsreglen (G1.4);
- NBER-indholdstriggeren (G4.1);
- hovedbogens referencetal og styrke (G3.2/G3.5);
- EBP/Baa (F37);
- L_R-audittens fortolkning;
- gatens tærskel (F8);
- driftsændringerne uden mandat (F29).

Syv analyser blev kørt først. De er deterministiske og uafhængigt verificeret
([v5/analyser/](v5/analyser/README.md)). Rådet fik tallene **inklusive verifikatorernes rettelser**.

Rådet bestod af syv medlemmer:
- seks af de nyeste flagskibsmodeller via OpenRouter: GPT-6.1 Sol Pro (OpenAI), Gemini 4 Argon (Google), Claude Fable 5.1 (Anthropic, uafhængig instans), Grok 4.7 (xAI), Kimi K3 (Moonshot AI) og DeepSeek V4 Pro (DeepSeek);
- Claude Opus 5.5 som erklæret part og sekretær.

## Hvad rådet besluttede (sammenfatning — den engelske tekst nedenfor er den gældende)

Intet ændrer P før september-refitten 2027. Beslutningerne er præregistreret i dag og træder i kraft ved
refitten. Undtaget er punkter mærket **[now]**, som kun er dokumentation.

1. **λ = 1 bevares som arvet konstant** (ikke "optimal", ikke "bekræftet af ablation9"). Skill vises fremover
   altid i samme sætning og i denne rækkefølge:
   - oracle-fri fast λ (+20,4 %);
   - orakel-censureret fast λ (+27,1 %);
   - nested λ (+18,3 %, orakel-censureret).

   Styrkeklausulen står i samme sætning: ca. 150 kalenderårs hovedbog for 80 % styrke. +27,1 % står aldrig
   alene. **[now]** Indført i motor, dashboard.json (`skill_saetning`) og README.
2. **Ingen selektor; F5 er en frossen benchmark.** De gamle "MDE"-tal (4,42 / 21,06 pp) er kritiske værdier
   (1,96·SD), ikke MDE'er, og omdøbes. Fra 2027 gælder:
   - gaten er ensidet mod sin egen kritiske værdi og udløser kun et punkt på rådets dagsorden — aldrig "evidens", aldrig et skift;
   - den lånte 4,42 pp fjernes.
3. **Kvartalsfittet bevares — og protokollen siger det ligeud:** blueprintets §2-gate *som skrevet* bestod, og
   rådet afviste at anvende den. Begrundelsen:
   - sammenligningen som skrevet er uparret;
   - den parrede sammenligning på identiske 198 origins er −1,02 pp;
   - +2,19 pp ligger under den kritiske værdi 2,99;
   - λ-normaliseringen var ikke forseglet.

   Fra 2027 logges et månedligt fits P som en uscoret kolonne. "Skriftlig specifikation går forud for koden"
   indføres fremadrettet i begge retninger.
4. **1947Q2 bevares**; P ved start 1953Q2/1960Q1 printes permanent.
5. **Demotion:** begge symmetri-læsninger dokumenteres **[now]**. En fremtidig søgning bruger én fastlåst
   symmetrisk bar.
6. **Indholdstrigger:** én refit pr. ny recession, ved første modne positive label, plus enhver omlabeling.
   Ingen trigger på negative modninger. Replayen for netop den konfiguration forsegles før refitten.
7. **Bedømmelsesnøglen ændres ikke.** E5 publiceres som supplement **[now]**: +24,41 / +28,95 / +33,28 %,
   logget basisrate 22,8 % mod realiseret 15,3 %. Hovedbogen beskrives som et ærlighedsinstrument, ikke en test.
8. **Baa-10y lukket** (kan ikke videregives). **EBP's historiske test lukket permanent** (onset-mønstret er set).
   Kun en fremtidig, prospektiv evaluering forseglet før den onset, den bedømmes på, kan nogensinde tælle.
9. **L_R = max(18, max peak-lag, max trough-lag − 12)**, i dag 18. Alder måles fra vinduets slutning (q + 30).
   Datostemplede tests (1991, 2001) skal bestå, før audit'en kører første gang.
10. **F29 ratificeret ex post**:
    - daglig live-kurve som erklæret instrumentskifte, med dobbeltlogning på GS10 − TB3MS;
    - tripwires ud af antændingskolonnen;
    - logdagen;
    - live-censurering, på betingelse af at reglen er byte-identisk med nøglens, og at der føres en uscoret kolonne med P og udfald for censurerede måneder.

## Hvad der flyttede sig undervejs

- **Frekvens:** Claude skiftede i runde 2 til månedlig, fordi blueprintets tekst var entydig. Sol og Fable var
  enige. Kompromiset (kvartal + protokolleret tilsidesættelse + uscoret månedskolonne) blev godkendt af alle
  i runde 3. Claude, Sol og Fable nedlagde veto mod at holde kvartal uden at sige, at gaten som skrevet bestod.
- **L_R:** Argon og Fable ville hæve L_R til 21. De trak forslaget tilbage, da mekanismen blev regnet igennem:
  en origin modner først ved q + 30, og trough-lag har historisk højst været 21.
- **Gate-tærsklen:** de "MDE"-tal, repoet har brugt siden v5.0, viste sig at være kritiske værdier (Sol, Fable).
- **Runde 4 (5–2):** Sol krævede en præcis definition af "alder". Grok betvivlede, at −1,02 pp var parret;
  sekretæren dokumenterede det fra resultatfilen (198 identiske origins, 0 uenige labels), og Grok trak
  indsigelsen tilbage. **Runde 5: 7–0.**

## Afstemningsforløb og pris

| Runde | Indhold | Resultat | Pris (OpenRouter) |
|---|---|---|---|
| 1 | Uafhængige forslag | 7 svar | $0,81 |
| 2 | Angreb og revision | 7 svar | $1,03 |
| 3 | Konvergens mod sekretærens matrix | 7 svar | $0,87 |
| 4 | Ratifikation | 5 APPROVE / 2 REJECT (Sol, Grok) | $0,66 |
| 5 | Ratifikation af ændret tekst | **7 APPROVE** | $0,53 |
| | | i alt | **$3,90** |

## Artefakt-pins (Kimi/Grok, runde 5)

Begrundelsen i §3.2(b) hviler på `v5/analyser/frekvensgate_resultat.json`
(`paneler/b_v501/modeller/curve_only/parret_tyndet_vs_kvartal`). Analysefilerne er committet sammen med denne
protokol. sha256 er beregnet af de committede bytes (LF), og kun `created_utc` varierer ved genkørsel:

| Fil (v5/analyser/) | sha256 |
|---|---|
| `demotion_resultat.json` | `e19447392a611aa202acb732916c9ebac57256115b7aeb0c93b1cdb487110b2c` |
| `frekvensgate_resultat.json` | `cafcadc5c45ce5b5538b6c9a697bce00689d740cdd85c025c7115beb43cb72f9` |
| `hovedbog_reference_resultat.json` | `e5afb43abec1c52eca944d57eb661a4e4bc22aac4ec93d83558b522916d2873a` |
| `nber_indholdstrigger_resultat.json` | `efada47e00229192496c1e982266303a71c3cf64264979cb683e7fd72d70e225` |
| `nested_robusthed_resultat.json` | `efd530453a59961ba6f8cde9f06c17abbb6634db32ab2a13703f1673ecc4970b` |
| `styrke_simulation_resultat.json` | `9192cd0912dd47d2a8f8e49f1f6e85cd7fd7110b090414263479015540dbe8a7` |
| `universstart_resultat.json` | `0bc22376bb3e78cb2f71d21f89fbb0ee650b957142455a10b74dd05e09ebf5ce` |

Kontrol i en ren klon: `sha256sum v5/analyser/*_resultat.json`.

---

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

---

# FORBEHOLD TIL PROTOKOLLEN (runde 5, ordret)

### GPT-6.1 Sol Pro (OpenAI)

VOTE: APPROVE

§9.2 now defines maturity unambiguously as \(R \ge q+12+L_R\): with \(L_R=18\), eligibility starts at **q + 30 months**, not q + 18. The date-stamped 1991/2001 tests address my remaining blocking objection.

The supplied artifact citation and origin-identity verification support §3.2(b)’s paired interpretation. The minutes explicitly acknowledge overriding the written frequency gate; they do not disguise that decision as compliance.

I accept all ten agenda decisions despite their known effects for the reasons recorded in §11. Keeping λ = 1 is protocol continuity, not evidence that it is optimal; retaining quarterly fitting is an acknowledged discretionary override, not a statistical victory.

**Reservations for the record—non-blocking:**

1. **Power wording (§1.2).** “≈150 calendar years” is conditional on the nine-block resampling design, including the adverse 2020–24 block. It is neither a universal waiting-time forecast nor a lower bound. The public interpretation should remain: **this replay does not support a realistically timed, adequately powered confirmatory ledger test**. The 36–53% false-rejection rates concern the evaluated inference procedures, not ledger recording itself.

2. **Monthly regularisation (§3.3).** The sealed monthly specification should match quarterly shrinkage per observation. Under summed log-loss, that means \(\lambda_m=\lambda_qN_m/N_q\), recalculated within each training window. Otherwise the diagnostic changes sampling frequency and effective regularisation simultaneously.

### Gemini 4 Argon (Google)

VOTE: APPROVE

The Round 5 amendments resolve the remaining ambiguities in §9.2–9.3 (explicitly anchoring $L_R$ maturity to the forecast-window end $H(q) = q + 12$ and requiring date-stamped 1991/2001 verification tests) and verify the exact 198-origin, 0-label-disagreement identity in §3.2(b) via `v5/analyser/frekvensgate_resultat.json`. All post-hoc choices remain acceptable for the reasons recorded in §11.

**Reservations for the record (non-blocking):**

1. **Monthly Fit Loss Normalisation (§3.3):** When the specification for the unscored monthly curve-only column is sealed prior to 2027-09, the L2 regularisation penalty must be scaled to match the quarterly per-observation weight ($\lambda_{\text{monthly}} = \lambda_{\text{quarterly}} \cdot (N_m / N_q) \approx 3.0$ under a summed log-loss, or switching both models to mean log-loss with $\lambda$ scaled by $1/N_q$). Logging an unnormalised summed-loss monthly fit with $\lambda = 1$ on $N \approx 800$ rows applies roughly one-third the effective shrinkage of the $N = 267$ quarterly model, confounding sampling frequency with regularisation relaxation ($\beta = -1.41$ vs $-1.29$).
2. **Pre-2027 EBP Estimation Leakage (§8.3):** While §8.3 rightly bars pre-2027 EBP observations from ever serving as confirmatory evidence, allowing a future council to include pre-2027 EBP data in the *fitting* sample of a prospective evaluation still leaks the already-inspected historical sign pattern (high before 1990/2001, low before 1980/2008/2020) into the estimated coefficient $\hat{\beta}_{\text{EBP}}$. If a future council ever mandates a prospective EBP test, any coefficient estimated on pre-2027 data carries post-hoc selection bias that disclosure alone cannot purge.
3. **One-Per-Onset Trigger Residual Lag (§6.1):** Restricting the content trigger to only the *first* matured positive origin of a new recession leaves up to 3 subsequent positive origins of that same episode waiting up to 9 months for the September refit. While the historical mean $|\Delta P|$ is negligible (0.13 pp, max 1.05 pp) and this compromise avoids intra-year refit churn, it only partially eliminates the NBER calendar-alignment artifact identified in E6.

### Claude Fable 5.1 (Anthropic, uafhaengig instans)

VOTE: APPROVE

The Round-4 condition is met. §3.2(b) now cites an artifact with path, n_parrede_origins 198, labels_uenige 0, identical pooled base rate 0.1616 and baseline log-loss 0.4423; the count is consistent with censoring (226 quarter-end months 1967-12…2024-03 less censored origins = 198, so 591/3 ≈ 197 was the wrong arithmetic on my side). §3.3 seals the in-code identity check on the 2027 panel, §9.2 is Sol's wording, §1.2 takes the power-clause relabelling. Nothing in §11 has changed in substance; each row remains a tightening, a disclosure, or the status quo with the override recorded verbatim, and P is untouched before 2027-09.

Reservations for the record, non-blocking:

1. **§3.2(b) is verified by an interested party.** I accept it on the cited artifact and the independent verifier's reproduction via ablation3's own `wf_monthly`, not on the secretary's note. The in-code check in §3.3 should assert the three identities (origin set, labels, pooled base rate) and fail loudly, not merely print them. The minute's "does not favour monthly" must not be read as "monthly is worse": −1.02 pp with SD 2.58 is sign-uninformative.

2. **§9.3 tests need negative controls.** For each of 1991 and 2001, the date-stamped tests should check both boundaries: the origin is excluded at R = H(q) + L_R − 1 and included at R = H(q) + L_R, and an origin inside the episode stays censored at every R before the trough announcement. A test that only confirms inclusion would not catch the age-from-origin bug Sol identified.

3. **§8.3 remains a half-open door.** Gemini's point stands: a β_EBP fitted on the inspected 1973–2026 pattern and scored on two later onsets largely tests recurrence of what was seen. Disclosure does not remove that bias. A future council should read §8.3 as "prospective fit and prospective score", with pre-2027 use requiring an explicit, sealed justification — not as a default permission.

### Grok 4.7 (xAI)

VOTE: APPROVE

I was wrong on the origin sets. The brief’s “different origin sets / own base rates” sentence is the unpaired full-monthly contrast (591 vs 198). `parret_tyndet_vs_kvartal` is a different object: m%3==0 scored from `wf_monthly` on the same 198 quarter-end origins, 0 label disagreements, shared base rate 16.16% and baseline log-loss 0.4423, gap −1.02 pp, 10–90% [−4.47, +1.32]. That is the paired diagnostic. Citing it meets the veto.

Reservations (non-blocking):

1. Acceptance of §3.2(b) is conditional on `v5/analyser/frekvensgate_resultat.json` being in the same push as RAADETS_2027.md, with those fields and seed 42 intact. A secretary citation without the file is not evidence. Rasmus hash-checks it against the independent verifier before the push.

2. §3.3 must pin the penalty, not merely “include normalisation.” Under a summed loss, λ = 1 on ~800 rows is about one-third the per-observation penalty of λ = 1 on 267 (E2: β −1.29 → −1.41 per pp; P at +1.12 is 14.9% → 14.4%). Seal either λ_monthly = 1 × (N_m/N_q) or mean log-loss with λ scaled by 1/N_q. An unpinned spec confounds frequency with shrinkage in the unscored column.

3. §3.2’s “written gate passed; council declines to apply it” must not be read as the pre-run ablation3 gate having passed. That gate failed, 26.03 vs 26.05. The override is of the unpaired written reading, justified by (a)–(d) plus the paired −1.02 pp, not by a passed executed test.

### Kimi K3 (Moonshot AI)

VOTE: APPROVE

Both Round-4 rejections were resolved by verification, not negotiation. Sol's eligibility rule is now executable, and the check of `frekvensgate_resultat.json` establishes that the m%3==0 thinned set is origin-identical to the 198 quarterly origins (0 label disagreements, same pooled base rate 0.1616). That converts my Round-4 reservation 2 from "close, not exact" to exact, and Grok's objection is answered by artifact, not assertion. All three of my Round-4 reservations are now in the text: nested oracle-free computed at the 2027 refit (§1.2), the paired diagnostic re-run with code-checked origin identity (§3.3), three censoring variants with real-time first (§6.2). Neither veto is triggered.

Reservations for the record (non-blocking):

1. **§3.2(b) — pin the artifact by hash, and record what 0.02 pp means.** With origin identity established, the executed gate failed by 0.02 pp against a paired SD of 2.58 pp — 0.008 SD. The paired difference itself is −0.40 SD with an interval [−4.47, +1.32] that does not favour monthly. The minutes should state this in numbers: the council is not overriding evidence, it is declining to act on noise. And because −1.02 pp is the load-bearing reason for declining a preregistered gate, the JSON's commit hash belongs in the minutes — a path can be regenerated, a hash cannot. The secretary verified its own artifact; independent reproduction is noted, but the pin should be cryptographic.

2. **§3.3 — pin the normalisation numerically, not as a promise.** "Including the loss/penalty normalisation" is not a number. Under a summed loss, λ_m = λ_q·(N_m/N_q) ≈ 3.0; E2's counterfactual monthly fit (β −1.41 vs −1.29; live P 14.4 vs 14.9) ran at roughly one-third effective shrinkage, so the unscored column as prototyped confounds sampling frequency with relaxed penalisation. The sealed spec should state the chosen normalisation and its value before any run.

3. **§9.3 — add 1980–81 to the date-stamped tests.** 1991/2001 exercise the trough-lag term; the double-dip is the hardest case for §9.2 condition (2): E5's 83 open-episode months include the entire 1980-08..1981-05 run-up (10 positive rows, P to 96.6 %). A test suite that skips back-to-back onsets has not tested censoring resolution where it actually binds.

### DeepSeek V4 Pro (DeepSeek)

VOTE: APPROVE

The §3.2(b) verification resolves the paired-comparison objection. Reservations for the record:

1. **§3.2 framing.** The minutes still describe the written §2 gate as "passed" and the council as "declining to apply it." I do not accept that as the operative governance description. The only pre-run executed comparison failed (26.03 vs 26.05); the literal full-monthly comparison is unpaired across different origin sets and base rates. I record the operative description as "executed gate failed; literal reading noted as incommensurable," not "gate passed and overrode." The paired same-origin artifact, now verified, is an ex post diagnostic, not the pre-run gate.

2. **§9.3.** The text now includes my peak-lag halt condition. I reserve that the trough term (`max lag_trough − 12`) is an audit check on open-episode censoring resolution, not a maturation floor. Onset eligibility is label maturity; trough announcements matter only for resolving censoring. If the implementation folds these into one parameter, a peak-lag breach must still halt the refit on its own.

3. **§1.2.** The nested figure remains oracle-censored. The sentence "oracle-free counterpart has not been computed" must never be deleted without first computing that configuration under the same sealed replay rules; the 2027 refit must produce that nested oracle-free figure before any headline uses it.

### Claude Opus 5.5 (Anthropic — part i sagen og sekretaer)

VOTE: APPROVE

Reservations for the record (they do not block):

1. On §3.2(b), Grok's Round 4 objection was factually wrong (the comparison is origin-identical, as the cited JSON shows), but his demand was right: a reason for overriding a preregistered gate must cite its artifact, not the secretary's summary. It now does.
2. Sol's §9.2 wording is better than mine was. "Age" was undefined in my draft, and the implementation could have read it from the origin, which would have admitted labels 12 months early.
3. My earlier reservations stand: §3 keeps quarterly against my R2–R3 preference, §6 depends on the replay being sealed in time, and I am both secretary and party.
