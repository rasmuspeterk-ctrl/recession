# COUNCIL BRIEF — MOTOR v5.0.1, spec 8: a memory shadow model beside P

## Who you are

You are one of seven members of an advisory council convened by Rasmus, a Danish solo developer, on 2026-10-28.
The council: **GPT-6.1 Sol Pro** (OpenAI), **Gemini 4 Argon** (Google), **Claude Fable 5.1** (Anthropic,
independent instance), **Grok 4.7** (xAI), **Kimi K3.1 Pro** (Moonshot AI), **DeepSeek V4 Pro** (DeepSeek), and
**Claude Opus 5.5** (Anthropic — co-built the model, proposed this item and wrote the draft positions; it is the
secretary and an interested party: attack its positions at least as hard as anyone else's). You act as senior
macro-econometricians. You advise; Rasmus decides. The debate ends when all seven vote APPROVE on a consensus text.
You sat on yesterday's council (RAADETS_SPEC7, 7/7).

## Ground rules (ratified; not on the agenda)

- **Nothing changes P.** The operational model stays curve-only (council lock, RAADETS_V501 §6), weights frozen at
  72c3371d until the September 2027 refit.
- **The feature search is closed.** RAADETS_2027 §5.2: "Any future search (only by council mandate) fixes one
  numerically pinned symmetric bar for incumbents and challengers in the sealed spec before any run."
- **RAADETS_2027 §8.3** (written for EBP, the template for prospective-only evaluation): sealed before any onset it
  would be judged on; no pre-2027 observation is ever used as evidence; whether pre-2027 data may be used for
  fitting is for that council's sealed spec, which must disclose the contamination; a scored test needs ≥ 2
  post-sealing onsets (decades), and this is stated; even an unscored tracking column requires a ≥ 12-snapshot
  revision audit first (not relevant here: the curve does not revise).
- **Precedents for unscored fields:** from the 2027 refit every ledger row carries unscored P variants
  (`P_maanedligt_fit`, `P_1953Q2`, `P_1960Q1`; RAADETS_2027 §3.3/§4), shown on the dashboard as "unscored fields —
  not in the verdict". Yesterday the council kept a BEY-convention P **out of every user-facing surface** (Grok's
  distribution argument: an alternative P printed anywhere a screenshot can reach becomes "the real P").
- **Every number below is already known.** For each decision say whether it is acceptable despite being post hoc.

## The model and today's reading

Curve-only L2-logit (fixed λ = 1) on NBER-onset-within-4-quarters, quarterly origins from 1947Q2, 12 onsets.
P = logit⁻¹(−0.2915 − 1.2948·curve). Live input: trailing month of daily DGS10 − DTB3 (+1.12 pp) → **P 14.8 %**,
band 10.2–21.2 %, base rate 18.0 % → "not distinguishable". Oracle-free walk-forward skill +20.37 % (219 origins),
90 % paired-bootstrap interval [−0.062; +0.172] nats per origin.

## Why this is on the agenda: the model has no memory

The model reads the curve's **level**; +1.12 pp after a 25-month inversion is treated exactly like +1.12 pp with no
history. The grand review (August) named it: *"It is reading the trigger being pulled as the gun being put away."*
The dashboard already carries the history as context, not in P: an inversion note (ended 2024-11, depth −1.57 pp),
the P path (peak 35.4 % in 2025-10, −20.5 pp since) and a standing warning (P was below its peak at the last origin
before 6 of 8 onsets; 2007Q4 read 16.7 % the month before onset). Rasmus asks whether the model should have
memory. A re-run of the walk-forward yesterday reproduced the published figures and showed, per onset (oracle-free
P at the last origin before onset): 1990 28.5 % (curve +0.75), 2001 35.7 % (+0.47), 2008 16.7 % (+1.10), 2020
40.9 % (+0.32) — all after the curve had re-steepened; earlier onsets came during or at the end of an inversion.

## Evidence (data, not model results; all known)

**E1 — inversion episodes in monthly GS10 − TB3MS (≥ 3 consecutive negative months) and the next onset:**

| Inversion | Months | Depth | Next onset (first USREC month) | Months from inversion end to onset |
|---|---|---|---|---|
| 1966-09..1967-01 | 5 | −0.34 | none | — (no recession) |
| 1969-11..1970-01 | 3 | −0.17 | 1970-01 | 0 |
| 1973-06..1974-06 | 13 | −1.27 | 1973-12 | onset during inversion |
| 1978-12..1980-04 | 17 | −2.45 | 1980-02 | onset during inversion |
| 1980-11..1981-08 | 10 | −2.65 | 1981-08 | 0 |
| 2000-08..2000-12 | 5 | −0.53 | 2001-04 | 4 |
| 2006-08..2007-04 | 9 | −0.38 | 2008-01 | 9 |
| 2019-06..2019-09 | 4 | −0.32 | 2020-03 | 6 |
| 2022-11..2024-11 | 25 | −1.57 | none so far | 22 months and counting |

(1990-08 had no ≥ 3-month monthly inversion; 1989 was brief and shallow. 1953–1965 had no ≥ 3-month inversion
either: the 1957 and 1960 onsets came without one. Pre-1953 the 10y leg is Shiller's long rate.) The longest historical lag from the end of
an inversion to an onset is 9 months. Today it is 22 months. The 2022–24 inversion was the longest on record and
the deepest since 1981.

**E2 — the memory value today depends almost entirely on the horizon** (minimum of monthly GS10 − TB3MS over the
last H months, latest month 2026-09): H = 12 → +0.24 (no inversion in the window); H = 24 → −0.41 (2024-10);
H = 36 → −1.22 (2023-12). Any horizon chosen now is chosen knowing this.

**E3 — prior work.** `calibrate.build_monthly` has computed `curve_min12` (rolling 12-month minimum, min 6
observations) since v4; v4's model grid included "1b: curve 12m-min" as a stand-alone model. Its result is not
recorded in the repository and it was not chosen. No memory variable has been tested in v5.

**E4 — power.** 12 onsets in the fit, 8 in the walk-forward; MDE80 for a paired skill difference ≈ 30 pp. No
historical test can distinguish a memory model from curve-only; any historical figure is in-sample to everything
above.

## Claude's draft positions (an interested party — attack them)

- **Q1 — yes, a shadow model, never in P.** The context lines tell the reader the history; a shadow P logged every
  month builds the only evidence that can ever settle the question: prospective.
- **Q2 — `curve_min12`, the project's pre-existing definition.** It is the one memory variable whose definition
  predates this debate and E1/E2 (v4), so it carries the least forking. It also matches E1: every historical onset
  came within 9 months of an inversion's end. Its consequence is honest and visible now: today it holds no memory
  (+0.24), so the shadow model will read close to P. A 24- or 36-month horizon would light it up today — choosing
  that after seeing E2 is the forking path.
- **Q3 — two features, curve + curve_min12**, standardised, λ = 1, the operational universe, labels, eligibility and
  refit schedule (fitted on the operational calibration's snapshot and R; refitted with it every September).
  Fitting on pre-2027 data is allowed and disclosed as contaminated (E1–E4, the grand review, yesterday's backtest).
- **Q4 — logged in `hovedbog.jsonl` every row as `p_hukommelse` (unscored); not in LOG.md before the 2027 refit;
  not on the dashboard.** Yesterday's distribution argument applies: a second P beside P is read as the real one.
- **Q5 — unscored tracking; a scored comparison only after ≥ 2 onsets after sealing,** against curve-only on the
  same rows, with a pinned symmetric bar (Δ log-loss beyond 1.96·SD_block either way → agenda item, never an
  automatic switch). Each September's diagnostics print the tracking record.
- **Q6 — start with the November 2026 row** (log window 10–13 November), so the record begins before anyone knows
  how this cycle ends.

## Agenda

- **Q1 — at all?** A memory shadow model logged beside P, or are the existing context lines enough?
- **Q2 — which single memory variable, and which horizon?** Candidates: (a) minimum curve over the last H months
  (H = 12 / 24 / 36); (b) months since the last ≥ 3-month inversion ended (capped); (c) an indicator "a ≥ 3-month
  inversion ended within the last H months"; (d) cumulative inversion (sum of negative curve) over the last H months.
  Given E2, how do you pin H without choosing it by its value today? Is "pre-existing definition" (v4) a valid
  tie-breaker?
- **Q3 — model form and fitting.** Curve + memory, or memory replacing curve? λ, universe, labels, refit schedule.
  May pre-2027 data be used for fitting (§8.3), and what must the spec disclose?
- **Q4 — where it is logged and shown.** hovedbog.jsonl only; also a LOG.md column; on the dashboard? Weigh the
  distribution argument against transparency.
- **Q5 — evaluation.** Unscored tracking only, or a sealed scored comparison after ≥ 2 post-sealing onsets — with
  which bar?
- **Q6 — start date.** From the November 2026 row, or from the September 2027 refit?
