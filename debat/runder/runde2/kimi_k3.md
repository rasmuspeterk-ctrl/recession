# KIMI K3 — ROUND 2: CRITIQUE AND REVISE

## 1) Attack

**GPT-OSS is factually wrong on frequency.** "Stay quarterly… episodes would drop to <10 if monthly." Episodes are events in calendar time; monthly USREC 1960–2024 contains the same ~12 recessions as quarterly. Frequency changes observations per episode (calibration precision), not event count. Its stated reason for the biggest architectural decision is a math error. Its 1% log-loss admission threshold for forward selection is a garden of forking paths with a gate sign — on 12 episodes, 1% is noise.

**Nemotron's label argument conflates knowability with stability.** "NBER is unknowable in real-time (6–18 month lag)" — the *target* of a 12-month forecast doesn't need to be contemporaneously knowable; that's what forecasting means. What matters is that training labels are final. The technical rule's "real-time knowability" is illusory: 2022 H1 was a technical recession until BEA revised it away. Nemotron's preferred label carries exactly the disease it diagnoses. Its ACM swap is self-defeating by its own arithmetic: starting 1961 leaves 7–8 episodes, and a feature that halves the event count fails the walk-forward rule on arrival. And "validate each flag category as a sub-model with Bayesian model averaging" is the backdoor-for-vibes with extra machinery — three more models fitted on 12 events.

**Gemma: a disclaimer doesn't fix a broken estimator.** Keeping p9 = 1−Π(1−p_h) "with a warning" prints a number known to be biased upward (nested horizon events are positively dependent; the independence formula overstates the union) and labels it a probability. That violates the honesty firewall directly. Kill it; a direct 12m label needs no assumption. Also: "confidence score from the standard error of the log-loss" is a category error — score dispersion is not a probability interval. Bands come from block-bootstrap of the probability path.

**Gemini's flattening goes too far.** Deleting flags because they might be misread is paternalism, not honesty. The tests showed flags don't improve *the model's* log-loss — not that they carry zero information — and repricing flags were never recession predictors. Label, don't delete. But Gemini and Sol are right that v4's verdict breaches the firewall ("FORHOEJET. Handl."); flag counts must never drive probability language.

**Sol, minor:** killing LAG 2 outright vs. my strip-the-percentages — the bucket table (14%/38%/56% on n≈11) is the offending object, not the inversion history itself. Remove the pseudo-precision, keep the checklist.

## 2) Steelman

**Gemini's selection/holdout split — the catch I missed.** v4's five features were chosen by maximizing over seven candidate sets on the *same* walk-forward that produced the headline +22.9%. That number is a max-over-search and therefore optimistic; the incumbent features enjoy grandfather immunity they never earned. Fix: select features and L2 penalty on pre-1990 data only (or nested inside training windows, Sol's version), then evaluate **once** on 1990–2024. This is the single most important integrity upgrade on the table.

## 3) Revisions to my Q1–Q8

- **Q2:** Concede to Sol — v5 ships **one** direct 12m model. My 3m companion doubles the selection surface; it becomes a separate pre-registered experiment only if Sahm/claims earn admission.
- **Q3:** Incumbents get no immunity. All five re-arbitrated under the pre-1990/post-1990 protocol alongside my locked candidate list (Sahm, claims, ACM-swap), one test each, no second chances.
- **Q4:** Add nested selection of the L2 penalty inside training windows; report that post-selection walk-forward skill is an upper bound.
- **Q7:** Partial concession on ALFRED. My "skip" stands for the *live* tool (NBER label + unrevised market series leaves only CPI seasonal revisions), but I'll accept a **one-time vintage audit** in the calibration script: quantify revised-vs-vintage CPI/unemployment delta, publish it, revisit only if >2pp log-loss. That answers Sol/Gemini's legitimate concern without a permanent pipeline.
- **Q8:** Adopt Sol's framing — Chauvet–Piger is a coincident nowcast, displayed separately, never benchmarked against a 12m forecast.

## AGREE
- Kill the p9 product rule (all except Gemma).
- NBER label, 2001 in (Sol, Gemini, Grok, GPT-OSS, me).
- L2 logit engine survives; boosting/Markov-switching rejected.
- Episode-blocked bootstrap/CV for overlapping labels.
- Automate data pulls; verdict must never let flags override the model.
- 2023: communicate, no regime dummies (Nemotron dissents).

## DISAGREE
- **ALFRED:** live vintage pipeline (Sol, Gemini, Grok, Nemotron, Gemma) vs. one-time audit (me).
- **LAG 2/3:** delete (Sol, Gemini) vs. keep-labeled (me, Grok, Gemma, GPT-OSS) vs. validate-and-integrate (Nemotron).
- **Frequency:** monthly (Sol, Gemini, Grok, me) vs. quarterly (Nemotron, Gemma, GPT-OSS).
- **ACM curve:** swap (Nemotron) vs. challenger-test (me, Grok) vs. reject (Gemini).

## CHANGED-MY-MIND
- Dropped my 3m second model — Sol's selection-surface argument.
- Adopted Gemini's pre-1990-select/post-1990-holdout; the +22.9% headline is a max-over-search and must be re-derived honestly.
- Moved from "skip ALFRED" to "one-time audit, no pipeline."
- Adopted Sol's Chauvet–Piger-as-nowcast separation.