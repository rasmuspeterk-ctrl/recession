# Secretary's matrix after Round 2 (Claude Opus 5.5 — a party; framing may be challenged)

Several Round-2 texts attack Claude's **Round-1** E1 sentence ("every onset came within 9 months…") and "the shadow
will read close to P". Claude's Round 2 already withdrew both. Positions below are each member's latest.

## Fact checks (artifact paths)

- **The fit sample ends 2024Q1, not 2025Q3.** Eligibility at R = 2026-09 requires quarter end + 12 + 18 ≤ R, so the
  last eligible origin is 2024Q1 (`v5/kalibreringer/manifest_72c3371d.json` → `modeller.curve_only.estimering_slut`
  = "2024Q1"). The fit contains the inversion-period zeros 2022Q4–2024Q1 (where curve ≈ curve_min12), not the
  post-inversion re-steepening (2024Q4 onward). Fable's and Argon's "resolved zeros through 2025Q3" is wrong; Sol's
  doubt was right.
- **The repo has no stationary bootstrap.** Its convention is the episode-block bootstrap over cycle blocks, seed 42
  (`ablation3.mde_bootstrap`, used by the gate, the frequency gate and the nested robustness analysis; 4.4 uses the
  same blocks with 10,000 draws). "Mean block 8 quarters = walk-forward convention" (Fable, adopted by Argon) is not
  an existing convention.
- **The shadow's comparator.** If the shadow is fitted on exactly the operational calibration's snapshot, R and
  eligible rows (identity asserted), the logged operational P *is* the matched curve-only control (Sol/Kimi's
  concern), and both are refitted together each September. A separate control is needed only if eligibility
  differs (e.g. rows missing curve_min12 — none are expected: the monthly curve exists from 1934).

## SETTLED (≥ 6 of 7; not reopened)

1. Nothing changes P, its band or verdict; no automatic switch, ever.
2. If anything is logged: one memory variable, `curve_min12` (rolling 12-month minimum of monthly GS10 − TB3MS, ≥ 6
   observations — the v4 object); H = 24/36 and candidates (b)–(d) rejected; no alternative-horizon runs.
3. Curve + memory (never memory alone), raw standardised columns; Argon's (C, C − M) reparameterisation withdrawn.
4. λ = 1 exactly as the operational fit; training-only standardisation frozen with the vintage; same universe,
   labels, eligibility, snapshot and R; refit only with the operational September refit. No coefficient-sign gate
   or post-fit re-specification; the fit is logged whatever it shows.
5. Pre-2027 fitting allowed and disclosed as contaminated (E1–E4, v4's unrecorded result, the grand review, the
   backtest, collinearity). The spec states it is blind to 1957, 1960, 1990 and to the current 22-month lag, and
   that no bound on shadow − P exists before the fit.
6. Never in LOG.md or on the dashboard, including after 2027, without a new council decision.
7. Pre-2027 origins (incl. Nov–Dec 2026) are audit-only, never evidence; scoring (if ever) on quarterly origins,
   not monthly rows (Kimi); ≥ 2 post-sealing onsets; stated as underpowered.

## OPEN

**D1 — A shadow probability at all.** Six yes; Grok no ("a monitoring number beside a live P"). Note Claude R2:
logging only `curve_min12` adds no information (the curve does not revise; the state is reconstructible forever).

**D2 — Storage.** (a) public field `p_hukommelse` in `hovedbog.jsonl` (Fable, Argon); (b) private append-only
companion archive (Sol, Kimi, DeepSeek); (c) hash commitment: the shadow line in a local git-ignored file, its
sha256 in the public `hovedbog.jsonl` row; revealed at evaluation (Claude R2 — not yet seen by others). Fable's
objection to (b): "a record nobody can audit is a diary." (c) is auditable and publishes no probability. Grok:
no `p_*` field anywhere.

**D3 — A scored rule now.** (a) none in this spec; a future council seals one before the onsets it uses (Sol, Grok,
DeepSeek, Claude); (b) pin a descriptive agenda screen now (Fable: "the only moment it can be set without knowing
the outcomes"; Kimi; Argon). If (b): one procedure only — the repo's episode-block bootstrap is the only existing
convention; the block-length variants (4 / 8 / 16 / 20) are new choices.

**D4 — The H justification in the spec.** Label horizon (Fable, Argon, Kimi) vs pre-existence only (Sol: backward
memory and forward label are distinct quantities; Grok; DeepSeek). Either way the spec records E2's three values
and that the choice was made knowing them.

**D5 — Fable's ≤ 2022Q3 disclosure fit.** Print once a coefficient vector fitted on origins ≤ 2022Q3 (Fable, Argon,
Grok-as-fallback) vs reject — another cutoff chosen after inspecting this cycle (Sol). Correct the premise first: the
fit already stops at 2024Q1.

**D6 — Live value of curve_min12.** (a) v4 object exactly: minimum of the last 12 published monthly GS10 − TB3MS (Sol:
anything else is a new feature); (b) the live trailing month as month 12 plus 11 published months (Argon).

**D7 — Start.** November 2026 (six) vs not before a fit is justified (Grok).
