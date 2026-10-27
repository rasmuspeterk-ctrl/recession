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
