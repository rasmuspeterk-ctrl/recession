# Secretary's matrix after Round 2 (Claude Opus 5.5 — a party; framing may be challenged)

Several Round-2 texts attack Claude's **Round-1** positions on C5/C6 and the EBP analogy. Claude's Round 2 already
withdrew them (C5's "all convention" was false; 98 % and Rosenberg-Maurer struck; EBP analogy dropped). Positions
below are each member's latest.

## Fact checks (artifact paths; please do not relitigate without a citation)

- **C7 gate attribution is not reversed.** `dashboard.json` → `gate.curve_only_wf` = 27.05, `gate.fuldmodel_wf` =
  23.16 (manifest 72c3371d, field `gate`); the line prints F5 +23.2 % vs curve-only +27.1 %. Five members confirm;
  Sol, please withdraw or cite the contradicting artifact.
- **The 4.4 bootstrap is 10,000 draws, seed 42, 5th–95th percentiles** (`v5/diagnostik.json` → `parret_loss_bootstrap`
  → `n_draws` 10000; `v5/diagnostik.py` line 318 uses `np.percentile(means, 5)` and `(…, 95)`). The §3.2(b)
  frequency-gate comparison is 1000 draws, seed 42, 10–90 % (`analyser/frekvensgate.py`). Fable's "pinned 1000 /
  10–90" for 4.4 is wrong; Sol's 10,000 / 5–95 matches 4.4.
- **Convexity size:** the BEY aggregation (Jensen) gap is ≤ 0.003 pp even at σ = 1 pp within-month (Claude R2);
  the choice of operator is about consistency, not magnitude.
- **Kim-Wright vs ACM** figures in the brief are three months apart (10-16 vs 2026-07); their 0.15 pp difference is
  not a measured model disagreement (Sol).

## SETTLED (7/7 or 6/7 with no veto; not reopened)

1. Part A sealed as an **unscored diagnostic**: convert both TB3MS and DTB3 with the pinned 91-day BEY formula;
   series named "91-day BEY proxy"; GS3M from 1981-09 as a reported check only, never spliced; λ = 1, identical
   origins and labels asserted; outputs in §1.2 order; published whatever it shows.
2. Item (4) (BEY P at the refit's live input) is written to diagnostics only — **never on the dashboard or in
   LOG.md** (Grok).
3. Rate-bin table (TB3MS < 4, 4–8, 8–12, ≥ 12 %) with onset counts, fitted α/β and origin-level paired Δ.
4. Claude's |Δ| < 2 pp (and |Δβ| < 0.15) only as "author's prior, not a criterion", printed away from the result.
5. Part B: B1/B2 are not run and are **deleted from the spec text**. Closure reason: a seen rejection, forking
   paths, and power (MDE80 ≈ 30 pp) — not "§8.2 by nickname". §0 carries verbatim: "E3's −77.88 pp is a result on
   an implementation (F5, pre-1961 base-rate penalty), not on the hypothesis; it is not evidence for or against
   the expectations component."
6. C6 as committed does not stand: "98 %" and the Rosenberg-Maurer sentence are struck from anything beside P.
7. C5 is amended: ≈ 0.10 pp convention + ≈ 0.08 pp instrument/fitting; plus a sentence that neither BEY nor CMT may
   be fed into the frozen weights.
8. C3 ratified. C1's 5 bp kept, disclosed as set after seeing +1.4 bp, frozen until the 2027 refit; both leg
   changes always printed.
9. Verdict string, ledger wording and scoring key unchanged; "no robust signal" rejected.
10. 8.9 % of draws ≤ 0 is a draw share, not a p-value (Sol, Grok, Kimi; Fable and DeepSeek's "p ≈ 0.09" falls).

## OPEN

**D1 — Part A decision rule.** (a) No pre-committed switch; a later council decides with the replay (Sol, Fable,
Argon — withdrew his −0.50 pp rule — Grok, Kimi). (b) Claude R2: switch at the refit unless Δ_OF < −1.96·SD_block.
(c) DeepSeek: |Δ_OF| ≥ 2 pp makes it a mandatory agenda item (Fable, Argon, Grok, Kimi reject any outcome trigger).

**D2 — Part A bootstrap.** 10,000 draws / 5–95 (Sol; = 4.4's spec) vs 1000 / 10–90 (Fable, Argon, Grok; = §3.2(b)).

**D3 — Aggregation operator.** (a) Convert daily then average for the live leg; BEY(TB3MS) for history, gap
disclosed (Fable, Grok, Sol, Argon, DeepSeek, Claude). (b) Same operator in calibration and live: convert after
averaging everywhere, mean-of-daily as robustness (Kimi).

**D4 — B3 revision audit.** Design: Kimi's (12 consecutive monthly full-history vintages, sha256, median/max
|revision| of TP and E) — accepted by all. Open: (a) pinned bar max |revision of E| < 10 bp before an unscored
column opens (Fable, Argon, DeepSeek); (b) no bar — passing it would not establish validity (Sol). Series: KW only,
ACM at most as a dated note (Grok, Claude) vs KW and ACM both printed with dates (Fable, DeepSeek, Argon).

**D5 — The C6 line now.** (a) Remove from the standing warnings until the audit; neutral text in methods docs only
(Kimi, Sol). (b) A neutral numbers-only line now (Fable, Argon, Grok, DeepSeek, Claude). If (b), whose text — the
candidates are Fable's R1 text, Argon's R1 text, and Grok's minimum ("model-dependent, revised, not an input").

**D6 — C5's illegal figure.** State "(substituting CMT gives ≈ 17.9 %; that is not P)" so readers see why it is
illegal (Fable) vs never print the illegal number anywhere (Grok's distribution argument).

**D7 — C2.** The full §1.2 sentence in the benchmark row (Sol, Kimi, Argon) vs a short note of the three figures in
§1.2 order, the full sentence being printed directly above the table (Claude).

**D8 — C4.** Keep the quarter-end + 32 + 10 days rule labelled "heuristic; BEA vintage not verified" (Grok, Claude)
vs drop the inference unless BEA's release calendar establishes it (Sol, Kimi).

**D9 — C7.** Gate line → "curve-only minus F5 = +3.89 pp, oracle-censored full path" (Kimi, Fable, Grok; no
objection so far). Interval: compute the oracle-free 219-origin paired interval now and print it first (Fable,
Argon, Grok, DeepSeek, Kimi, Claude) vs the censored interval may follow the full §1.2 sentence, oracle-free
optional (Sol).

**D10 — Q5 dashboard prose.** Prefix "Primary band rule:" on the verdict line, paired supplement stated as not
deciding (Sol, Kimi, Grok; Fable accepts in prose) vs no change (Argon, Claude) vs tooltip only (DeepSeek).
