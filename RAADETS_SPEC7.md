# RÅDETS KONSENSUS 2026-10-27 — de eksterne reviews, præsentationsrettelserne C1–C7 og spec 7

Ratificeret **7/7 den 2026-10-27** (runde 4). Fuldt transkript, brief, sekretærfiler og kostlog ligger i
[debat/raad_spec7/](debat/raad_spec7/).

## Hvad rådet blev indkaldt om

To eksterne gennemgange (en rapportlæsning og en kodegennemgang) blev tjekket mod koden 2026-10-27. Det, der
holdt, blev rettet samme dag uden rådets mandat (C1–C7, commit 2e22ac5), og to spørgsmål blev skrevet som
spec-udkast 7: rentekonventionen (3m-benet på diskonto- mod obligationsækvivalent basis) og kurvens
forventningsdel. Rådet fik fem spørgsmål: del A, del B, konventionsnoten og advarslen (C5/C6), ratifikation af
C1–C4 og C7, og dommens ordlyd.

Rådet bestod af seks af de nyeste flagskibsmodeller via OpenRouter pr. 2026-10-27 — GPT-6.1 Sol Pro, Gemini 4
Argon, Claude Fable 5.1, Grok 4.7, Kimi K3.1 Pro (ny, afløser Kimi K3) og DeepSeek V4 Pro — og Claude Opus 5.5
som erklæret part og sekretær.

## Hvad rådet besluttede (sammenfatning — den engelske tekst nedenfor er den gældende)

Intet ændrer P, båndet, dommen, vægtene, manifestet, bedømmelsesnøglen eller hovedbogens rækker.

- **Del A (rentekonventionen)** forsegles som en uscoret diagnostik til refitten 2027: 3m-benet omregnes til en
  91-dages obligationsækvivalent proxy, både historisk (TB3MS) og live (DTB3); CMT bruges kun som tjek. Ingen
  forudbestemt skifteregel og ingen udløser; resultatet er et ubetinget dagsordenspunkt i 2027. P under den
  omregnede konvention vises aldrig på dashboardet, i LOG.md eller i hovedbog.jsonl.
- **Del B (forventningsdelen)** får ingen historisk test. Ideen blev testet én gang (trin 4, −77,88 pp), men det
  var en test af en implementering, ikke af hypotesen — det står ordret i spec'en. Søgningen forbliver lukket,
  fordi resultatet er set. I stedet: en prospektiv revisionsaudit af Kim-Wright over 12 månedlige snapshots fra
  næste logning; en uscoret kolonne åbner kun ved revisioner under 10 bp (et administrativt stabilitetskrav,
  ikke evidens) og rådets godkendelse.
- **C6 (advarslen om forventningsdelen) fjernes.** "98 %" og litteraturhenvisningen argumenterede mod P ud fra én
  model på én dag. Opdelingen bliver kun stående i den firewallede kontekstblok, med "modelafhængig, revideres;
  ikke et input".
- **C5 (konventionsnoten) rettes:** 0,10 pp er konvention og ca. 0,08 pp er forskellige papirer. Intet
  substitueret tal vises nogen steder.
- **C1** bliver "kurveændring under 5 bp (næsten parallel)", oplyst som sat efter at have set +1,4 bp og frosset
  til 2027. **C2:** den fulde §1.2-sætning står lige over benchmark-tabellen. **C4:** "først set af os dd-mm
  (N dage efter kvartalets udgang)", uden påstand om BEA-vintage. **C7:** gate-linjen bliver "+3,89 pp", og
  bootstrap-intervallet for den oracle-fri variant (219 origins) beregnes og vises før det orakel-censurerede.
- **Dommen** får præfikset "Primær båndregel:" på dashboardet; strengen i hovedbogen er uændret.

## Afstemningsforløb og pris

| Runde | Indhold | Resultat | Pris (OpenRouter) |
|---|---|---|---|
| 1 | Uafhængige forslag | 7 svar | $0,75 |
| 2 | Angreb og revision | 7 svar | $0,87 |
| 3 | Konvergens mod sekretærens matrix | 7 svar; vetoer mod skifteregel, substitueret tal, censureret interval alene, retningsbestemt linje ved P | $0,81 |
| 4 | Ratifikation | **7 APPROVE** | $0,57 |
| | | i alt | **$3,00** |

Undervejs blev to faktuelle påstande afvist mod artefakter: gate-linjen byttede ikke om på tallene
(`dashboard.json` → `gate`), og 4.4-bootstrappen er 10.000 træk og 5.–95. percentil (`v5/diagnostik.py` linje 318).
Claude trak sin egen skifteregel for del A tilbage i runde 3.

---

# CONSENSUS TEXT — the reviews of 2026-10-27, the presentation changes C1–C7, and spec 7 (Round 4 draft)

Assembled by the secretary (Claude Opus 5.5, a party) from Rounds 1–3. Where a veto was declared, the text takes
the vetoing side. Nothing here changes P, the band, the verdict, the weights (72c3371d), the manifest, the scoring
key or any ledger row. **[now]** = presentation/documentation, done after ratification; **[refit]** = computed at
the September-2027 refit; **[audit]** = runs from the first ledger snapshot after sealing.

## 1. Part A — the 3m leg on a bond-equivalent basis (sealed as spec 7A) [refit]

1.1 An **unscored diagnostic**, published whatever it shows. Never in P, band, verdict, gate or trigger.
1.2 Series: "91-day BEY proxy", BEY(d) = 100·365·(d/100) / (360 − 91·(d/100)), d in percent. History: BEY(TB3MS).
Live leg: each DTB3 day converted, then averaged over the trailing window. Robustness, printed once: the
convert-after-averaging operator on both, and the Jensen bound (≤ 0.003 pp at within-month σ = 1 pp). The 10y leg
and the pre-GS10 backbone are unchanged. GS3M (from 1981-09) is a reported check only (mean and max |BEY(TB3MS) −
GS3M|), never spliced. The converted curve is still not unit-consistent with the semiannual par 10y CMT; the spec
says so.
1.3 Outputs, into `diagnostik.json` → `uscorede.konvention_bey`, with the sha256 of inputs and the code commit:
(1) curve-only fit on the BEY proxy, λ = 1, identical eligible origins and labels (identity asserted, fails loudly);
(2) walk-forward in §1.2 order, oracle-free first; (3) the paired difference BEY − discount on identical origins,
episode-block bootstrap with 4.4's cycle blocks, **10,000 draws, seed 42, 5th–95th percentiles** (primary), the
10th–90th from the same draws printed and labelled "80 % interval"; (4) a rate-bin table (TB3MS < 4, 4–8, 8–12,
≥ 12 %) with onset counts, fitted α and β, and origin-level paired log-loss and probability differences;
(5) P at the refit's live input under the BEY proxy — **written to diagnostics only; never rendered on the
dashboard, in LOG.md or hovedbog.jsonl**.
1.4 Decision: **no pre-committed switch and no outcome trigger.** Part A's output is an **unconditional agenda
item** of the 2027 refit council, which decides the convention with both configurations' replays, the rate bins
and calibration in hand. Any later switch needs its own sealed replay (§1.3) and takes effect from a refit.
1.5 Claude's prior, recorded in the spec's §0 only and never printed beside the result: |Δ_OF| < 2 pp —
"author's prior, not a criterion".
1.6 Post hoc: acceptable — unconditional, unscored, cannot select a configuration.

## 2. Part B — the expectations component (sealed as spec 7B)

2.1 **No historical test.** B1/B2 are not run and are deleted from the spec text. Reason, verbatim in §0: "The idea
was tested once (v5.0 blueprint section 5, run in step 4: dLL −77.88 pp, dBrier −30.82 pp, 192 paired origins,
0 % positive folds). That result is on an implementation — inside F5, with a pre-1961 base-rate penalty, the
secondary truncated comparison never run — not on the hypothesis; it is not evidence for or against the
expectations component. The historical search nevertheless stays closed: the result has been seen, a redesign
could now be aimed around it, and with 8 onsets since 1961 MDE80 ≈ 30 pp." No reliance on §8.2 by analogy.
2.2 **B3 — prospective, unscored, audit first.** Series: Kim-Wright `THREEFYTP10` only; E = (y10 − TP) − 3m. ACM
appears only as a dated secondary series in the audit report, never as a live line. [audit] Vintages: the monthly
ledger snapshots (each already stores the full THREEFYTP10 history with its sha256 in `meta.json`), **12
consecutive**, counted from the first ledger row after sealing; earlier snapshots may be reported but do not count.
For every date in the trailing 24 months of vintage 1: median and max |revision| of TP and of E from vintage 1 to
each later vintage, in pp; missing dates reported, not imputed.
2.3 An unscored ledger column carrying the bare E (no sentence beside it) opens only if **both** (i) max |revision
of E| < 10 bp — an administrative **display-stability** bar, explicitly not evidence of validity — and (ii) the
council signs off after the 12th vintage. A scored evaluation needs ≥ 2 onsets after sealing (decades) and its own
sealed spec; no pre-2027 observation is ever evidence.
2.4 Post hoc: acceptable — prospective, unscored, no historical evidence claimed.

## 3. The presentation changes of 2026-10-27 [now]

3.1 **C1 ratified, amended:** below 5 bp the label reads "curve change below 5 bp (near-parallel)", both leg changes
always printed; the 5 bp is disclosed as set after seeing +1.4 bp and is frozen until the 2027 refit.
3.2 **C2 amended:** the complete §1.2 sentence (three figures in order + power clause) sits immediately above the
benchmark table in the same visual unit, on the dashboard and in the console print; the curve-only row's note
carries all three figures in §1.2 order and points to it. +27.05 % never stands alone.
3.3 **C3 ratified.**
3.4 **C4 amended:** the GDP monitor prints "first seen by us dd-mm (N days after quarter end)". "Later vintage than
advance" is dropped; the quarter-end + 42 days heuristic may stay internal, never as a public vintage claim. The
monitor's name is unchanged (ledger continuity of the ignition column).
3.5 **C5 amended:** "Convention: the model's 3m leg is DTB3/TB3MS on the discount basis. On this window DGS10 −
DGS3MO (CMT) is +0.95 pp against +1.12 pp with DTB3. At DTB3 4.04 % the pinned BEY conversion gives 4.14 %; the
remaining ≈ 0.08 pp to DGS3MO reflects instrument/fitting differences. Substituting the CMT or BEY curve into the
frozen weights does not produce P and is not shown; Part A is an unscored refit sensitivity." **No substituted
probability is printed anywhere user-facing.**
3.6 **C6 removed** from the standing warnings. No line beside P prints a TP level, E, a share or a literature
claim. The decomposition stays only where it has been since 2026-09-10 (commit a7a5207): the firewalled context
block ("10y = term premium + expected", Kim-Wright, dated), which gains "model-dependent, revised; not an input"
and nothing else. The step-4 history and the verbatim §2.1 sentence go into the README's methods section.
3.7 **C7 amended:** the gate line reads "curve-only minus F5 = +3.89 pp, oracle-censored full path". The paired
loss bootstrap is computed for the **oracle-free 219-origin set** with 4.4's procedure (10,000 draws, seed 42,
5–95, same cycle blocks) and printed **first**; the 198-origin interval follows, labelled "oracle-censored". Until
the 219-origin interval exists, the 198-origin interval is a footnote marked "oracle-free interval pending",
never alone under the §1.2 sentence. The share of draws ≤ 0 is a draw share, not a p-value.
3.8 Post hoc: acceptable — each removes a false or misleading statement or restores §1.2; none changes a number
that decides anything.

## 4. Verdict wording (Q5) [now]

The dashboard's verdict line is prefixed "Primary band rule:"; the existing paired-supplement line beneath it
states that the supplement does not decide the verdict. The verdict string in `dashboard.json`, LOG.md and the
scoring key are unchanged. "No robust signal" is not used.

## 5. Order of execution

Ratification → spec 7A and 7B written from §§1–2, sealed (sha256 pinned in `protokol2027.SPECS`) and pushed →
the [now] changes of §§3–4 and the 219-origin interval, each before its code → dashboard regenerated
(bit-identical replay) and republished. Part A runs at the refit; the B3 audit runs from the next ledger row.

---

# FORBEHOLD TIL PROTOKOLLEN (runde 4, ordret)

### GPT-6.1 Sol Pro (OpenAI)

VOTE: APPROVE

1. **Part A remains a measurement diagnostic, not a selection procedure.** The BEY proxy does not make a simple-yield bill and a semiannual par 10-year yield fully unit-consistent. Its level dependence warrants the unconditional 2027 review, not an adoption presumption. Rate-bin coefficients must remain descriptive, unscored outputs; they cannot become alternative production fits or retrospective selection criteria. Ten thousand bootstrap draws reduce Monte Carlo noise, not uncertainty from the small number of recession episodes.

2. **The B3 audit measures revision stability, not predictive validity.** For reproducibility, the sealed implementation specification should identify the precise y10 and 3m series, date alignment, and whether those market-rate observations are held fixed when computing revisions of E. Otherwise “revision of E” can conflate term-premium revisions with changes in the other inputs. Passing the 10 bp display-stability bar supplies no evidence that E improves recession forecasts. Keeping historical B1/B2 closed is justified by the seen implementation and redesign opportunities—not by treating −77.88 pp as a clean rejection of the economic hypothesis.

3. **Presentation compliance must survive isolated rendering.** A benchmark table exported or printed without its surrounding dashboard must retain the complete §1.2 sentence, including the power clause. The oracle-free paired interval must be published regardless of its result, ahead of the censored interval, without interpreting bootstrap draw shares as p-values. “Bit-identical replay” should mean unchanged computational P, band, verdict and existing ledger content—not identical presentation bytes.

These decisions are acceptable **despite being post hoc**: the presentation changes correct interpretation, Part A is unconditional and unscored, and B3 starts prospectively. None retrospectively validates a predictive hypothesis or authorizes a production switch.

### Gemini 4 Argon (Google)

VOTE: APPROVE

**Reservations for the record (do not block consensus):**

1. **§3.7 (Interim footnote for the 198-origin interval):** The consensus text allows the 198-origin oracle-censored paired loss bootstrap interval to appear temporarily as a footnote marked *"oracle-free interval pending"* until the 219-origin interval is computed. Because the 219-origin per-origin losses already exist in the repository artifacts and require only a few seconds of compute under the pinned `parret_loss_bootstrap` specification (10,000 draws, seed 42, 5th–95th percentiles), this interim state should not actually be deployed. The 219-origin interval should be generated and committed in the initial `[now]` implementation batch so that the oracle-censored interval never appears on the live dashboard without its oracle-free counterpart preceding it.
2. **§1.2 (Remaining yield-basis mismatch):** While Part A’s `BEY(d)` conversion eliminates the level-dependent discount-rate distortion in the 3-month leg (which reached 81 bp at $d = 15\%$), the resulting 91-day simple ACT/365 money-market yield remains algebraically distinct from the semiannual bond-equivalent par yield of the 10-year CMT leg (`GS10`/`DGS10`). When the 2027 refit council reviews Part A on its unconditional agenda, it should evaluate whether full compounding alignment (converting the 3-month leg to a semiannual compounding basis) is warranted alongside the simple BEY proxy.
3. **§3.4 (BEA release-date verification):** Dropping *"later vintage than advance"* in favor of *"first seen by us dd-mm (N days after quarter end)"* is the right immediate fix to avoid unverified vintage claims. Before the September 2027 refit, however, the data ingestion pipeline should record actual BEA release timestamps or vintage identifiers directly from ALFRED/FRED metadata so the monitor can state the exact statistical release (Advance, Second, or Third) as verified fact rather than relying on an internal day-count heuristic.

### Claude Fable 5.1 (Anthropic, uafhaengig instans)

VOTE: APPROVE

The draft meets both my veto conditions (no outcome-conditioned switch in §1.4; the censored interval never alone under the §1.2 sentence in §3.7) and the compromises I offered in Round 3. Three reservations for the record, none blocking:

**R1 — §3.6 is silent on what happens to the decomposition after the audit.** I accepted removal of C6 from the standing warnings on the condition that the audit starts at the next ledger row (it does, §2.2) and that the question of a numbers-only line returns to the council with the 12th vintage. The draft specifies when a ledger column may open (§2.3) but not whether the context block may then carry E = (y10 − TP) − 3m. It should: the same sign-off that opens the column decides the context line; absent sign-off, the block stays as §3.6 writes it. Otherwise "removed until the audit" quietly becomes "removed".

**R2 — §1.3(4), the rate-bin table.** The ≥ 12 % bin holds essentially 1980–81 and the 8–12 % bin 1973 plus fragments; per-bin fitted α and β there are near-unidentified and will have standard errors wider than the coefficients. The sealed spec should label the bin fits "descriptive, no inference", or the 2027 council will be handed a bin coefficient that looks like evidence of regime dependence. The origin-level paired loss by bin is the informative part; the fits are decoration.

**R3 — §3.4 (C4).** I argued for keeping the quarter-end + 42 days inference as a labelled heuristic; the majority drops it. I accept that, but note the residual defect: a reader of the GDP monitor still cannot tell whether our first-seen print predates or postdates BEA's second estimate, and "N days after quarter end" only helps a reader who knows BEA's calendar. The cheap fix — scraping the BEA release calendar once a quarter — should go on the refit's housekeeping list so the inference can be restored verified rather than guessed.

On the post hoc question, I concur with §§1.6, 2.4 and 3.8 as written: nothing ratified here selects a configuration, scores a hypothesis, or moves a number that decides anything.

### Grok 4.7 (xAI)

VOTE: APPROVE

Post hoc: acceptable on §§1.6, 2.4 and 3.8. Nothing here selects a weight, moves P, or reopens a seen test.

Reservations, not blocks:

1. Spec 7A’s rate-bin α, β (1.3(4)) are diagnostics, not a weight proposal. E1 (gap 0.55–0.81 pp at 12–15 %, 4 of 12 onsets in the high-rate bins) is exactly the pattern that tempts a regime-dependent β. Adopting one is a new model, needs its own sealed spec and replay under §1.3, and is not authorized by an unscored convention check. The 2027 agenda item decides the 3m convention only.

2. The 10 bp bar on E (2.3) is administrative bookkeeping, not evidence. At the frozen β = −1.2948, 10 bp of E is about 1.3 pp of shadow probability — large relative to today’s paired supplement [−6.5; −0.4]. A pass plus council sign-off may open a bare column; it may not be cited as validation, and ACM stays out of any live line. The step-4 result (−77.88 pp, 0 % positive folds) remains seen and non-isolating; B1/B2 stay deleted.

3. The pre-2026-09-10 context line may keep its dated Kim–Wright split only with the new disclaimer and with no E, share, or Rosenberg–Maurer sentence, and not in the same visual unit as P or the verdict. Claude’s |Δ_OF| < 2 pp prior stays in spec §0, never beside the result. A substituted probability — 17.9 % or any other — does not ship.

### Kimi K3.1 Pro (Moonshot AI)

VOTE: APPROVE

Reservations for the record:

1. **Pin the 7B audit arithmetic before sealing.** Specify the \(y10\) and 3m series, units, same-date alignment and missing-day rules. Define the 10 bp criterion as the maximum over every date in vintage 1’s trailing 24 months and every revision comparison through vintage 12. It remains exclusively a display-stability criterion.

2. **Part A cannot establish a regime-specific “correction.”** Rate-bin estimates—especially for TB3MS ≥ 12%—will rest on few episodes and may have unstable \(\alpha,\beta\). Likewise, 10,000 bootstrap draws improve Monte Carlo precision, not the information supplied by nine cycle blocks. The bins and paired replay are descriptive inputs to the unconditional 2027 decision, not evidence that BEY is superior.

3. **Neither presentation interval is a significance test.** Printing the 219-origin oracle-free interval first corrects the §1.2 emphasis; it does not cure the limited episode count. The 198-origin result’s 8.9% of draws ≤ 0 remains a draw share. C1’s post hoc 5 bp cutoff and B3’s 10 bp bar must never migrate into \(P\), verdicts, triggers or ledger scoring.

### DeepSeek V4 Pro (DeepSeek)

VOTE: APPROVE

Reservations for the record:

1. **D4 audit bar (10 bp) remains arbitrary.** I accept it as a display-stability gate, not validity evidence, but the council should state in the spec that the 10 bp threshold was chosen without empirical revision data and may be recalibrated by a later council before any column opens. The bar's defensibility rests entirely on the "administrative, not evidentiary" label — that label must survive contact with the dashboard.

2. **D6 no-number position is weaker than I argued.** I still believe printing ≈17.9% once with the explanation is more protective than silence, but the screenshot-risk argument (Grok, Opus) is real and the anti-substitution sentence without the figure is sufficient. I record my disagreement on the didactic point only.

3. **D3 operator choice (convert-after-averaging primary) is the right call for consistency, but the spec must not let the robustness line (mean-of-converted-daily) drift into any user-facing comparison.** The Jensen bound is pinned; the operator difference is bookkeeping. If the 2027 council later cites the robustness line as evidence for a convention switch, that is a §1.3 breach and I will oppose it.

### Claude Opus 5.5 (Anthropic — part i sagen og sekretaer)

VOTE: APPROVE

Reservations for the record (they do not block):
1. I withdrew my own switch rule (Round 3). I still think the 2027 council should weigh unit consistency as a
   measurement argument in its own right, not only through the replay's skill figure; §1.4 leaves room for that.
2. Removing C6 removes the one sentence that tells a curve-only reader the current curve is almost all term
   premium. I accept the firewall's reasons; the context-block line and the README methods section must be easy
   to find.
3. The 10 bp bar in §2.3 is administrative and arbitrary in level; its virtue is that it was pinned before any
   revision was computed.
