# MOTOR v5.0.1 — probability of a US recession onset

**English** · [Español](README.es.md) · [中文](README.zh-CN.md) · [Français](README.fr.md) · [Dansk](README.da.md)

[![tests](https://github.com/rasmuspeterk-ctrl/recession/actions/workflows/tests.yml/badge.svg)](https://github.com/rasmuspeterk-ctrl/recession/actions/workflows/tests.yml)

*A US recession-onset probability model: one feature (the 10y–3m yield curve), an L2-logit on the NBER-onset
label, purged expanding-origin walk-forward validation, and a prospective ledger where every reading is logged
before the outcome is known. Free data only. Every failed candidate is published next to the one that survived.*

The model estimates P(an NBER-dated recession begins within the next four quarters). The operational model is a
curve-only logit, locked by the council (RAADETS_V501 §6); the five-feature full model is a benchmark only.
**Walk-forward skill (log-loss improvement over the base rate, RAADETS_2027 §1.2): oracle-free, fixed λ = 1
+20.4 % (219 origins; the figure the ledger is judged against); oracle-censored, fixed λ = 1 +27.1 %; nested λ
(oracle-censored) +18.3 % — and 80 % power requires on the order of 150 calendar years of ledger, while naive
tests reject a true null hypothesis 36–53 % of the time at 5–20 years.** The ledger is therefore an honesty
instrument, not a test.

λ = 1 is inherited from v4 and not selected in a nested way; that is a declared deviation from the blueprint. A
nested model selection would have chosen the full model and scored +8.5 % (see
[v5/README.md](v5/README.md#afvigelser-fra-blueprintet-erklaeret-2026-10-15)). Seven feature candidates were
tested, published and rejected; the search is closed.

**Latest logged reading (2026-10-10, v5.0.1, daily curve):** P = 15.1 % [10.4–21.6 %] against a base rate of
18.0 % — not distinguishable from the base rate. See [LOG.md](LOG.md). A mid-month reading on 2026-10-27 (not
logged) gave 14.8 % [10.2–21.2 %]; the current reading is on the [dashboard](dashboard.html).

### Language

The front page is available in five languages. The detailed documentation ([v5/README.md](v5/README.md), the
scoring key, the dashboard brief), the code's identifiers, comments and printed output, and the ledger are in
Danish (written in ASCII: `aa` = å, `ae` = æ, `oe` = ø). The operative texts of the council decisions
(`RAADETS_*.md`) and the council transcripts in [debat/](debat/) are in English. The Danish originals of sealed or
preregistered documents govern; they are never rewritten, because their hashes are part of the protocol.

## How the model has changed

**Recalibration v5.0.1 (2026-09-19):** the calibration backbone was frozen at 2023 (Yale's Shiller file), so
three mature quarters were missing from the fit. The council ratified the repair 4/4; the same inputs now give
17.7 %, oracle-censored walk-forward skill +27.1 % (from +34.3 %), because the three added quarters are the false
alarms of the 2023–24 inversion. *"A lower or higher recalibrated probability is changed estimation, not changed
economic risk."* Details: [v5/README.md](v5/README.md#v501--foerste-rekalibrering-raadets_v501md-ratificeret-44-2026-09-19).

**Since 2026-09-28 the curve is measured on daily data** (a trailing month of DGS10 − DTB3, without the up to
one month publication lag). This is a declared change of instrument, not measurement-identical to GS10 − TB3MS;
the council ratified it ex post (RAADETS_2027 §10.1). P on the published monthly figures is shown next to it in
every row.

**Context protocol (2026-10-24):** commodities (oil, natural gas, gasoline, diesel, fertiliser, grains, metals),
credit-card debt and house prices in the US are fetched on every run, shown in the engine and the dashboard and
stored in each ledger row's full record — as context with no influence on P and no thresholds. All are official
public-domain series (EIA, BLS, Fed, FHFA, Census). See
[v5/README.md](v5/README.md#kontekst-protokollen-2026-10-24-raavarer-kreditkort-og-bolig-usa--rettelser-fra-mellemlaesningen-2026-10-23).

**The 2027 council (ratified 7/7 on 2026-10-15):** seven analyses and five debate rounds with six of the newest
flagship models settled the ten questions the code review sent to "the council before September 2027":
- λ = 1 and the quarterly fit are kept — and the protocol says plainly that the blueprint's frequency gate *as
  written* passed, and that the council declined to apply it;
- no model selector; 1947Q2 is kept;
- one NBER content trigger per recession;
- the scoring key is not amended;
- the historical test of the excess bond premium (EBP) is closed.

Nothing changes P before the September 2027 refit. See [RAADETS_2027.md](RAADETS_2027.md) and
[v5/analyser/](v5/analyser/README.md). The decisions were implemented (2026-10-15) from six sealed specs in
[v5/spec2027/](v5/spec2027/), each pushed before the code ([v5/protokol2027.py](v5/protokol2027.py),
[v5/replay2027.py](v5/replay2027.py)); they apply only to calibrations from the 2027-09 refit onward.

**The council of 2026-10-27 (ratified 7/7):** two external reviews were checked claim by claim against the code.
The presentation fixes that held were put to the council, which also sealed two further specs: an unscored test of
the 3-month rate's quotation convention (discount vs bond-equivalent basis) at the 2027 refit, and a prospective
revision audit of the Kim-Wright term premium instead of a new historical test of the curve's expectations
component (the idea had already been tested once and rejected). The oracle-free skill now carries its own
uncertainty interval: +0.085 log-loss per origin, 90 % interval [−0.062; +0.172]. See
[RAADETS_SPEC7.md](RAADETS_SPEC7.md).

**Code review 2026-10-15:** 85 verified findings are fixed without changing P or any historical row. The changes
include six time-critical bugs before the November reading, licence-restricted files out of the repository, swarm
tripwires out of the ledger's ignition column (the council's R3), a preregistered
[scoring key](BEDOEMMELSESNOEGLE.md) and a prediction of the September 2027 refit. See
[v5/README.md](v5/README.md#kode-review-2026-10-15--alt-rettet-intet-i-p-aendret).

## Where things are

| File | Contents |
|---|---|
| [v5/README.md](v5/README.md) | Rituals, file map, deviations from the blueprint, build log (Danish) |
| [v5/](v5/) | The code: fetch → (finalize6 → diagnostik at recalibration) → motor (calibrate.py is the step-1 reproduction and does not overwrite the operational weights). 238 tests. |
| [LOG.md](LOG.md) | The ledger — one row per month, logged before the outcome is known. Never edited. |
| [BEDOEMMELSESNOEGLE.md](BEDOEMMELSESNOEGLE.md) | How the ledger is scored — preregistered before row 4, with a power table (Danish) |
| [UDFALD.csv](UDFALD.csv) / [hovedbog.jsonl](hovedbog.jsonl) | Append-only outcome per row / full record per row (hovedbog.jsonl is created at row 4) |
| [RAADETS_KONSENSUS.md](RAADETS_KONSENSUS.md) | The blueprint, ratified 7/7 by a council of language models after six debate rounds |
| [RAADETS_REVIEW.md](RAADETS_REVIEW.md) | Grand review with 18 models |
| [RAADETS_V501.md](RAADETS_V501.md) | The council's consensus on v5.0.1 — the first recalibration (4/4, 19 Sept 2026) |
| [RAADETS_2027.md](RAADETS_2027.md) | The council's consensus on the agenda for the September 2027 refit (7/7, 15 Oct 2026) |
| [RAADETS_SPEC7.md](RAADETS_SPEC7.md) | The council's consensus on the external reviews, the presentation fixes and spec 7 (rate convention, expectations component) (7/7, 27 Oct 2026) |
| [RAADETS_SPEC8.md](RAADETS_SPEC8.md) | The council's consensus on spec 8: a hash-committed memory shadow model beside P, never in it (7/7, 29 Oct 2026) |
| [REVIEW-2026-10-15.md](REVIEW-2026-10-15.md) | The code review of the whole setup (85 findings) |
| [TRIGGER-ATLAS.md](TRIGGER-ATLAS.md) | Swarm-simulated recession channels and tripwires — narrative context, not an input to P |
| [DASHBOARD-BRIEF.md](DASHBOARD-BRIEF.md) | Design rules for a dashboard that cannot oversell (Danish) |
| [dashboard.html](dashboard.html) | The dashboard: one self-contained page that reads `dashboard.json` from the same folder (`python -m http.server` in the repository root, open `/dashboard.html`; opened from disk, choose the file in the page) |
| [debat/](debat/) | Transcripts of the council debates (blueprint, v5.0.1, 2027, spec 7 and spec 8; the grand review's rounds A+B were not archived — see RAADETS_REVIEW.md) |
| [mirofish-sim/](mirofish-sim/) | Raw data and summaries of the swarm simulations |
| [v4/](v4/) | The predecessor |

## Principles

- Free data only (FRED, Fed Board, Shiller, FINRA, multpl). Hashed snapshots. No API keys in the ritual.
- Only walk-forward-validated results get numbers. Complexity has to buy skill.
- The language describing a result is generated mechanically and cannot be sharper than the numbers.
- Failed attempts are published next to what worked.

## Monthly ritual (log day: first weekday from the 10th, + 3 days)

```bash
cd v5
# check nber.org/research/business-cycle-dating — new peak/trough? add a row to nber_announcements.csv and commit
python fetch.py                        # snapshot (FRED + Fed Board EBP), hashed; computes S&P vs 12-month high,
                                       # CAPE (multpl), margin debt (FINRA) and BEA's GDP release calendar itself
python motor.py --log --json           # reading, ledger row (only inside the log window), dashboard.json
python analyser/b3_revisionsaudit.py   # spec 7B: Kim-Wright revision audit (from the 2026-11 row)
python -m unittest test_v5             # 238 tests
```

The weights are frozen between recalibrations (every September, or when NBER dates a new peak/trough):
`python finalize6.py && python diagnostik.py` (first bump `VERSION` in finalize6.py, §3.3). See
[RAADETS_V501.md](RAADETS_V501.md).

Requires Python 3 and numpy. Nothing else.

## Data sources and terms

"Free to download" is not the same as "free to redistribute". The repository archives snapshots for
reproducibility. Sources with licence restrictions are fetched and hashed locally but **not committed**
(`.gitignore`). Their sha256 and last value are in each snapshot's `meta.json`, so anyone who fetches the same
bytes can verify the hash.

| Source | Series | Terms | In the repository |
|---|---|---|---|
| Board of Governors of the Federal Reserve System (H.15, G.17, G.19, H.8, CP; the Kim-Wright term premium THREEFYTP10; the Gilchrist-Zakrajsek EBP) | GS10, TB3MS, GS3M, DGS10, DTB3, DGS1, DGS2, DGS3MO, DFF, FEDFUNDS, INDPRO, RIFSPPFAAD90NB, THREEFYTP10, EBP; REVOLSL, CCLACBW027SBOG, DRCCLACBS, CORCCACBS, DRSFRMACBS | Public domain; citation requested | yes |
| U.S. Bureau of Labor Statistics | CPIAUCNS, CPIAUCSL, UNRATE, PAYEMS, CE16OV, AWHMAN, TEMPHELPS; WPU0652, WPU065201, WPU012, WPU102 | Public domain; citation requested | yes |
| U.S. Bureau of Economic Analysis | A191RL1Q225SBEA, GDPC1, PCEPI, PCEC96, W875RX1 | Public domain; citation requested | yes |
| U.S. Census Bureau (and HUD); U.S. Employment and Training Administration; U.S. Energy Information Administration; U.S. Federal Housing Finance Agency | PERMIT, MSPUS, MSACSR; ICSA, CCSA; DCOILWTICO, DCOILBRENTEU, DHHNGSP, GASREGW, GASDESW; HPIPONM226S | Public domain; citation requested | yes |
| NBER via Federal Reserve Bank of St. Louis | USREC | Copyright, citation required | yes |
| Federal Reserve Bank of St. Louis | CMRMTSPL | Copyright, citation required | yes |
| Freddie Mac | MORTGAGE30US | "Freddie Mac, 30-Year Fixed Rate Mortgage Average in the United States" — copyright Freddie Mac; citation required (FRED: Citation Required) | yes |
| Claudia Sahm; Marcelle Chauvet and Jeremy Piger (via FRED) | SAHMREALTIME; RECPROUSM156N | Public domain; citation requested | yes |
| **ICE Data Indices, LLC** | BAMLH0A0HYM2 (HY OAS) | "Copyrighted: Pre-Approval Required" — reproduction prohibited without written permission | **no (local)** |
| **S&P Dow Jones Indices LLC** | SP500 | "Copyrighted: Pre-Approval Required" | **no (local)**; only the derived monthly averages in `spine.csv` (the calibration needs them) |
| **Moody's** | BAA10Y | "May not be copied or otherwise reproduced" | **no (local)** |
| Robert J. Shiller (Yale) | The backbone through 2023-07 (`manual/shiller_yale_2023-09.csv`) | Data courtesy of Robert J. Shiller | yes |
| multpl.com | Monthly Shiller CAPE after 2023-07 | The page is not copied; only derived monthly figures in `spine.csv` | **page: no (local)** |
| NY Fed (Adrian, Crump and Moench 2013) | `manual/acm.csv` (the ACM term premium, used only in the step-4 test) | © Federal Reserve Bank of New York; redistributed under the NY Fed's Terms of Use with attribution ("Source: Federal Reserve Bank of New York, ACM Treasury term premia") | yes |
| FINRA | Margin debt y/y in `manual.json` (a derived figure) | FINRA Margin Statistics | yes |

Citation for FRED series: *Federal Reserve Bank of St. Louis, [series name] [ID], retrieved from FRED, Federal
Reserve Bank of St. Louis; https://fred.stlouisfed.org/series/[ID]*. The licence labels were taken from FRED's
series pages on 2026-10-15 and are listed per series in `v5/spine.py` (`SERIER`) and in each snapshot's
`meta.json`. BEA's GDP release calendar is read from FRED's release calendar (release 53) and ALFRED vintages.

Licence-restricted files from before 2026-10-15 are still in the git history. The recommendation (code review F1,
carried out 2026-10-15) is NOT to rewrite the history now: that would give every commit a new SHA and weaken the
ledger's provenance (the pushed `ledger-*` tags point at the original commits). The history is cleaned only if a
rights holder asks; the procedure is ready in v5/README.md ("Historik og licensbegrænsede filer").

The code is MIT-licensed, own text CC BY 4.0; third-party data and model-generated text are excluded — see
[LICENSE](LICENSE) and [NOTICE.md](NOTICE.md).

The model is not a trading signal and not investment advice.
