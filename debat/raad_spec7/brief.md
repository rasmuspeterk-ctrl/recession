# COUNCIL BRIEF — MOTOR v5.0.1: two external reviews, the presentation fixes of 2026-10-27, and draft spec 7

## Who you are

You are one of seven members of an advisory council convened by Rasmus, a Danish solo developer, on 2026-10-27.
The council: **GPT-6.1 Sol Pro** (OpenAI), **Gemini 4 Argon** (Google), **Claude Fable 5.1** (Anthropic,
independent instance), **Grok 4.7** (xAI), **Kimi K3.1 Pro** (Moonshot AI), **DeepSeek V4 Pro** (DeepSeek), and
**Claude Opus 5.5** (Anthropic — co-built the model, made the changes and wrote the draft spec under debate, and is
the secretary; treat it as an interested party and attack its positions at least as hard as anyone else's). You
act as senior macro-econometricians. You advise; Rasmus decides. The debate ends when all seven vote APPROVE on a
consensus text. Most of you sat on the 2026-10-15 council that ratified RAADETS_2027 7/7.

## Ground rules (ratified; not on the agenda)

- **Nothing changes P before the September-2027 refit.** Weights frozen at manifest 72c3371d.
- **RAADETS_2027 governs.** The clauses that matter here, verbatim:
  - §1.2 [now]: every published skill statement prints, in this order and in one sentence, (i) oracle-free
    fixed-λ walk-forward (+20.37 %, 219 origins), (ii) oracle-censored fixed-λ (+27.05 %, 198), (iii) nested λ
    oracle-censored (+18.32 %, 198), with the power clause. "**+27.05 % never appears as a standalone public figure.**"
  - §1.3: "Figures belong to the configuration that produced them. No historical figure is presented as the
    performance of a changed configuration without that configuration's own sealed replay."
  - §5.2: "Any future search (only by council mandate) fixes one numerically pinned symmetric bar for incumbents
    and challengers in the sealed spec before any run."
  - §8.2: "The historical sealed test of EBP is **closed permanently**: the onset pattern has been seen."
    §8.3: a future council may specify a prospective-only evaluation if it is sealed before any onset it would be
    judged on; no pre-2027 observation is ever used as evidence; whether pre-2027 data may be used for fitting is
    for that council's sealed spec, which must disclose the contamination; a scored test needs ≥ 2 post-sealing
    onsets (decades), and this is stated; even an unscored tracking column requires a ≥ 12-snapshot revision audit.
  - §12 step 3: every sealed spec is committed and pushed before the code that uses it; code pins its sha256.
- **The feature search is closed** (v5.0 council): sahm, claims, permits, **ACM**, curve+cape and AWHMAN were each
  tested once, published and rejected. Re-opening needs new economic rationale + council mandate + a sealed spec.
- **Context lines are firewalled**: no influence on P, band, verdict or the ledger's ignition column; no
  thresholds; no counts. The ledger (LOG.md, UDFALD.csv, hovedbog.jsonl) is append-only under a preregistered
  scoring key (BEDOEMMELSESNOEGLE.md, not amended).
- **Every number below is already known.** For each decision say whether it is acceptable despite being post hoc.

## The model and today's reading (mid-month reading 2026-10-27, not logged)

Label: NBER onset within 4 quarters; quarterly origins from 1947Q2; real-time labels; 12 onsets in the fit
(1948, 1953, 1957, 1960, 1970, 1973, 1980, 1981, 1990, 2001, 2008, 2020). Model: curve-only L2-logit, fixed
λ = 1. Raw form **P = logit⁻¹(−0.2915 − 1.2948 · curve)**, curve = 10y − 3m in pp. The calibration uses monthly
GS10 − TB3MS; the live input is the trailing month of daily **DGS10 − DTB3** (both 3m legs on the **discount
basis**). Pre-1953 the 10y leg is Shiller's long rate.

Today: trailing curve +1.124 pp (21 days, 2026-09-24..10-23) → **P 14.8 %**, band 10.2–21.2 %, base rate 18.0 %
→ "not distinguishable". Paired supplement (P minus base per bootstrap draw) [−6.5; −0.4] pp would say "below the
base rate"; it never changes the verdict. Spot curve 10-23 +0.96 → 17.7 % (context). Ledger: 08-12 20.1 %,
09-09 18.0 %, 10-10 15.1 %, all "not distinguishable". P peaked at 35.4 % (2025-10); the inversion ended 2024-11
(depth −1.57 pp). Historically P was below its peak at the last origin before onset in 6/8 onsets (median −21 pp);
2007Q4 read 16.7 % [10.4–27.4], not distinguishable, and the onset came the next month. dP/dcurve ≈ −1.6 pp per
10 bp. Context (firewalled): CPI 3.7 % y/y (3m ann. 4.6 %), Fed hiked in September to 3.88 %, 10Y 5.00 % (5.31 %
early October), WTI $108 (+85 % y/y), HY OAS 338 bp, EBP −0.39, Sahm 0.00, claims 198k, payrolls +0.3 % y/y.

## Two external reviews (2026-10-27) and what was verified against the code

**Review 1** (report-level, a three-model panel). Verified FALSE: (a) "the gate's 3.9 pp contradicts the table
(36.8 − 34.3 = 2.5)" — the gate is F5 vs curve-only on the same full path, 27.05 − 23.16 = 3.89; (b) "the
Estrella-Mishkin 12.8 % must be the NY Fed's own figure; at 1.12 it gives 10.7 %" — the engine computes it on the
same window with DGS10 − DGS3MO (CMT, the NY Fed convention) = 0.949 → 12.84 %; (c) "12 onsets is wrong; there are
11 since 1953" — the panel starts 1947Q2. Verified TRUE: the "bear steepening" label sat on a +0.01 pp curve change
(10y +0.08, 3m +0.06); the benchmark table showed +27.05 % alone (a §1.2 breach); the DTB3/DGS3MO convention gap;
the near-flat expectations component (below); the "advance estimate" monitor showed our first-seen vintage, not
BEA's advance; the forecast window starts in the logging month (sealed key rule (b); not touched).

**Review 2** (code-level: cloned the repo, ran all 220 tests, recomputed). Confirmed P, the window, EM, the onsets
and the purging; retracted its own gate/onset/log-date criticisms. Standing: label threshold, tandem, convention
note. New: show the historical paired loss bootstrap next to the skill figures (mean +0.120 nats/origin = +27.1 %
of the base-rate log-loss 0.442; 90 % interval [−0.042; +0.239]; 8.9 % of draws ≤ 0; 9 cycle blocks; this is the
oracle-censored 198-origin set); the verdict-rule backtest disagrees on 12/198 origins and in every case the
paired rule says "distinguishable" and the band rule "not" (the band rule is systematically more conservative).

## Changes made 2026-10-27 WITHOUT council mandate (presentation only; commit 2e22ac5)

P, band, verdict, weights, manifest and ledger rows are unchanged; 223 tests pass; the CI dashboard replay is
bit-identical. Rasmus approved them; the council has not.

- **C1** Month-change label: if |Δcurve| < `MAERKE_MIN_DK` = **5 bp**, "parallel shift up/down" (or "almost
  unchanged") instead of steepening/flattening. 5 bp was chosen after seeing this month's +1.4 bp.
- **C2** The curve-only benchmark row carries: "the wf column is oracle-censored like the other rows; cited only
  together with oracle-free +20.37 % (219 origins), RAADETS_2027 §1.2".
- **C3** Estrella-Mishkin row shows the spread used ("trailing 10y-3m (CMT) +0.95pp").
- **C4** GDP monitor says "first seen by us dd-mm" and adds "later vintage than advance" when our first snapshot
  came after quarter end + 32 + 10 days.
- **C5** Convention note under P: "Convention: the 3m rate is DTB3 on the discount basis, like the calibration's
  TB3MS. FRED's T10Y3M uses DGS3MO (CMT, bond-equivalent); on the same window that curve is +0.95pp. The gap
  (0.18pp) is convention, not data. The frozen weights were estimated on the discount basis, so the CMT curve
  cannot be fed into them; a sensitivity test is proposed for the 2027 refit (spec2027/udkast/7, requires the
  council's mandate)."
- **C6** Standing warning "expectations component": "Curve decomposition (Kim-Wright, 2026-10-16): 10Y 5.09 = term
  premium 0.99 + expected 4.10. The expectations component minus 3m is +0.02pp vs DTB3 (discount, the model's
  convention) and −0.16pp vs DGS3MO (CMT); 98 % of the curve that day (+1.01pp) is term premium. The literature
  (Rosenberg-Maurer 2008) finds that the expectations component is what predicts recessions; the model reads only
  the sum. An ACM version was tested and rejected in step 4 (−77.9pp full path, mainly the penalty for the years
  before 1961). Context, not in P; a proposal to the council is in spec2027/udkast/7."
- **C7** Dashboard: the gate line is labelled "F5 +23.2 % vs curve-only +27.1 %, same full path"; the 4.4 paired
  loss-bootstrap interval is printed under the §1.2 sentence.

## Evidence for draft spec 7

**E1 — the convention gap is level-dependent.** Bond-equivalent yield of a 91-day bill at discount rate d:
BEY = 365·d / (360 − 91·d). Gap BEY − d: 0.02 pp at d = 1 %; 0.10 at 4 %; 0.18 at 6 %; 0.28 at 8 %; 0.40 at 10 %;
0.55 at 12 %; **0.81 at 15 %**. So the discount convention overstates the curve most in the high-rate 1970s–80s,
where 4 of the 12 onsets sit. Today: DTB3 4.04 → BEY 4.14; DGS3MO was 4.22 (CMT and converted discount differ by
~0.08 pp: different instruments and fitting). GS3M (3m CMT, monthly) exists only from 1981-09; TB3MS from 1934.
Arithmetic only — no model has been fitted on the converted series.

**E2 — the decomposition is model-dependent and revisable.** Kim-Wright (THREEFYTP10, daily from 1990) on 10-16:
TP 0.99. ACM (NY Fed, monthly from 1961-06; local archive ends 2026-07): TP 0.84 in 2026-07 (0.51 in 2026-06).
Both are model estimates re-fitted on new data, so history can be revised.

**E3 — the idea has been tested once.** v5.0 blueprint section 5 ("ACM as one sealed test", run 2026-08 in step 4,
`ablation4_features.py`): curve_adj = (y10 − ACMTP10) − tb3m replaced the curve **inside the 5-feature model**
(baseline: F5 with the raw curve, then operational), full path on identical origins; where the ACM model could not
be fitted/predicted for lack of pre-1961 history, origins were scored at the training base rate ("the penalty for
missing history"); adoption iff dLL ≥ +0.5 pp and ≥ 80 % of LOEO folds positive; if |dLL| < 0.5 pp a secondary
comparison on ACM-valid origins only would be printed; explicitly not judged on 2023 (the 93.8 % false alarm that
motivated it). **Result: dLL −77.88 pp, dBrier −30.82 pp, 192 paired origins, 0 % positive folds, not adopted;
the secondary truncated comparison never ran.** Claude's reading: the number mostly measures the missing-history
penalty, so the economic hypothesis was never isolated; but the number and the rejection are seen, and ACM is on
the closed list.

**E4 — the literature.** Rosenberg & Maurer (2008, FRBNY Economic Policy Review): the expectations component of
the spread predicts recessions; the term-premium component does not. Known to everyone here, direction included.

## Draft spec 7 (Claude's; English rendering of the Danish file `v5/spec2027/udkast/7_konvention_og_forventningsdel.md`)

Status: draft, not ratified, not sealed, no code; nothing below is computed until the council decides. A ratified
part moves verbatim into `spec2027/7_<name>.md`, is sealed and pushed before code. Part A is a sensitivity on the
operational feature; part B is a new feature and needs a mandate and a symmetric bar fixed before any run (§5.2).
§0 discloses everything listed under E1–E4.

**Part A — the 3m leg on the bond-equivalent basis.** Purpose: measure whether the discount convention moves
weights, skill or P. Not a feature search: same feature, label, universe, origins; only the 3m leg's convention.
Conversion (pinned): BEY(d) = 100·365·(d/100) / (360 − 91·(d/100)), fixed 91 days, applied to monthly TB3MS and
daily DTB3; 10y leg and pre-GS10 backbone unchanged. Check (reported, not a criterion): from 1981-09, mean and max
|BEY(TB3MS) − GS3M|. Computed at the refit (R ≥ 2027-09) by diagnostik.py into `uscorede.konvention_bey` (outside
the manifest content hash; never in P, band or verdict): (1) curve-only fit on Curve_BEY, λ = 1, identical eligible
origins and labels, identity asserted; (2) walk-forward in §1.2's order (oracle-free first); (3) paired difference
BEY − discount on identical origins, episode-block bootstrap, 1000 draws, seed 42, 10–90 % interval; (4) P at the
refit's live input under BEY, labelled "unscored sensitivity, not P". Decision rule: published whatever it shows;
the convention never switches automatically; a switch is a council decision, may not rest on the skill figure
alone (§1.3), and applies from a later refit with its own sealed replay.

**Part B — the expectations component (needs a mandate, §5.2; the idea was tested and rejected once).** The
draft's recommendation is **B3**, not a new historical test: re-testing a rejected idea is a second shot at the
same target — the forking-paths risk the closed search exists to prevent. B1/B2 are listed only because the step-4
test mixed the idea with the panel penalty; if the council wants to separate them, B1/B2 is the only clean way and
must be recorded as a second shot. Data: Kim-Wright from 1990 covers 4 onsets (too few); ACM (`ACMTP10`, monthly
from 1961-06) covers 8 (1970, 1973, 1980, 1981, 1990, 2001, 2008, 2020); licence checked before sealing.
Feature: E = (y10 − ACMTP10) − 3m (step 4's curve_adj), 3m leg as the operational curve at run time.
Candidates (fixed, no others): B1 E alone replacing the curve; B2 E and ACMTP10 as two features.
Symmetric bar: on identical origins (panel from 1961Q3; identity asserted), Δ = skill(candidate) − skill(curve-only),
oracle-free fixed λ = 1; a candidate crosses if Δ > 1.96·SD_block(Δ); curve-only crosses the same bar against the
candidate if −Δ > 1.96·SD_block(Δ); SD_block by episode-block bootstrap, 1000 draws, seed 42, on the common panel.
If neither crosses the outcome is "no difference" and curve-only stays operational by the council lock (an
asymmetry of outcome, not evidence). Crossing only triggers an agenda item (§2.3), never a switch. Power: with 8
onsets MDE80 ≈ 2.8·SD_block, order 30 pp; the test will very likely not distinguish, and the result says so.
Contamination: twice (step 4's number; the literature's direction over most of 1961–2008). The draft thinks this
is the EBP situation (§8.2) and proposes **B3 (prospective, unscored; recommended)**: the expectations component
as a fixed context line and, after a ≥ 12-snapshot revision audit, an unscored ledger column, on §8.3's conditions
(sealed before the onsets it is judged on; no pre-2027 observation as evidence; a scored test needs ≥ 2 onsets
after sealing).

**Part C (already done):** C5 and C6 above; context only.

## Claude's draft positions (an interested party — attack them)

- **Q1 (Part A):** seal it as drafted. Convert both TB3MS and DTB3 with the one pinned formula (one consistent
  series 1934–); use CMT post-1981 only as a check, never spliced (a splice puts a level break at 1981-09).
  Preregister a prediction now: |Δ oracle-free walk-forward| < 2 pp. No automatic switch.
- **Q2 (Part B):** closed historically, as EBP. Only B3. THREEFYTP10 (daily, Fed Board, public domain) for the
  context line; the revision audit first.
- **Q3 (C5/C6):** keep C5 verbatim. Amend C6: add "term-premium estimates are model-dependent (KW 0.99 on 10-16;
  ACM 0.84 in 2026-07) and revised", keep the ACM-rejection sentence, keep the 98 % figure (it is the day's
  arithmetic).
- **Q4 (C1–C4, C7):** ratify ex post. 5 bp is disclosed as post hoc; it is a label and cannot move P, verdict or
  ignition column. The 4.4 interval stays under the §1.2 sentence, marked oracle-censored.
- **Q5 (verdict wording):** no change. "Not distinguishable" stays in verdict, ledger and dashboard.

## Agenda

- **Q1 — Part A.** Seal the convention sensitivity for the 2027 refit? Is the conversion right (formula, 91 days,
  convert-both vs splice CMT post-1981)? Outputs and decision rule as drafted? Given the level dependence (E1), is
  the operational convention a defect the council should address beyond an unscored sensitivity — and if so how,
  without breaking §1.3 or the frozen weights?
- **Q2 — Part B.** Closed permanently (EBP precedent), B3 prospective only, or B1/B2 as a declared second
  historical shot? If B1/B2: is the symmetric bar acceptable as drafted; what must the spec say about E3?
- **Q3 — C5 and C6.** Fair firewalled context, or an unvalidated signal that undercuts the firewall (C6 in effect
  tells the reader P is too low, from one model on one day)? Keep, amend (give the text), or remove each.
- **Q4 — C1–C4, C7.** Ratify ex post, amend, or strike each. Is the 5 bp threshold acceptable given it was set after
  seeing +1.4 bp? Is the 4.4 interval (oracle-censored) next to the §1.2 sentence consistent with §1.2's order?
- **Q5 — verdict wording.** Both reviews raised band vs paired; nobody proposes changing the primary rule (band).
  Should the plain-language dashboard text describe a band verdict as "no robust signal under the band rule"
  (review 1) while the ledger keeps "not distinguishable" — or leave it?
