## 1. Attacks

**Gemini: “switch … unless … Δskill < −0.50 pp” is not a non-inferiority test.** It is a point-estimate adoption rule with no uncertainty requirement. Demonstrating non-inferiority against a −0.50 pp margin would require a suitably constructed lower confidence bound above −0.50 pp, not merely an estimated difference above it. With roughly a dozen onset episodes, a result near zero can coexist with substantial deterioration. Nor is this necessarily a “mathematical bug”: calibration and production consistently use the same discount-basis feature. Harmonising yield quotations is economically defensible, but changes a nonlinear regressor and therefore requires estimation and evaluation. Reject the automatic switch.

**Claude Fable: “gap 0.10 pp → ΔP ≈ −1.6 pp” has the sign reversed.** Converting the short rate upward reduces \(10y-3m\). The coefficient is negative, so the frozen-coefficient probability **increases**, approximately **+1.6 pp**, not decreases. That calculation is only a mechanical illustration—not the probability change after refitting. Grok likewise calls the entire 0.18 pp CMT difference a “convention gap”; approximately 0.10 pp is conversion and 0.08 pp remains instrument/construction difference at the stated rates.

**Claude Fable: “one-sided p ≈ 0.09” does not follow from 8.9% of bootstrap draws being nonpositive.** The reported distribution resamples the observed data; it is not automatically a null-imposed reference distribution. Report the draw share, not a p-value. Also, KW October minus ACM July is not a measured **model disagreement**: it mixes model differences with three months of economic change. A disagreement estimate needs matched dates.

**Claude Opus: keeping “almost all … is term premium” preserves the problem, not its solution.** Removing “98%” while retaining the same ratio in prose and the predictive-literature sentence leaves the directional argument intact. Moreover, “the gap … is convention, not data” remains factually incomplete. A firewall disclaimer does not repair either attribution.

Several councillors also overstate the power argument. An MDE of 30 skill points means approximately 80% power at that assumed effect—not that the test “cannot distinguish anyway.” Low power supports declining a reopening; it does not guarantee its outcome.

## 2. Best idea I missed

**Kimi’s reproducible revision audit:** twelve consecutive monthly, full-history vintages with hashes, reporting revisions in both term premium and the derived expectations spread. Counting snapshots without specifying what is archived and compared is inadequate.

I adopt that design, including a fixed extraction date and treatment of missing observations. I reject Fable’s additional 10 bp admission threshold: it is an unmotivated gate, and passing it would not establish predictive validity.

## 3. Revised agenda positions

**Q1 — Amend and seal.** Retain the synthetic 91-day investment-yield proxy, convert both series, never splice CMT, and explicitly convert daily observations **before** averaging the live window. Monthly TB3MS conversion necessarily remains conversion-of-an-average; disclose that difference. Retain my 10,000 paired block draws, seed 42, 5th–95th percentiles, pinned blocks and hashed artifacts. No automatic switch, no ±2 pp decision trigger. This post-hoc, unconditional diagnostic is acceptable; its results cannot select production by themselves.

**Q2 — B3 only.** Adopt Kimi’s audit-before-standing-display requirement. Remove executable B1/B2 designs from the ratified spec, while preserving their rejection and E3’s complete provenance. ACM is closed under the existing search rule, not automatically subject to EBP’s explicit permanent prohibition. No historical reopening now; no scored prospective assessment before two post-sealing onsets.

**Q3 — Amend C5; remove C6 as a standing warning.** I strengthen my Round-1 position: defer even a neutral recurring decomposition line until the audit. Keep the neutral explanatory text in methods documentation. C5 must distinguish quotation conventions from instrument/construction differences; do not combine spot conversion arithmetic with window-average comparisons. These post-hoc corrections remove misleading claims.

**Q4 — Conditional ratification.** Keep my C1 wording, complete C2 skill sentence, C3, and metadata-based C4 correction. For C7, the brief contradicts itself about which configuration owns 27.05%; named replay artifacts must resolve attribution. An explicitly labelled censored bootstrap supplement may follow the complete §1.2 sentence; an oracle-free interval would improve balance but is not required by its ordering clause. No p-value interpretation.

**Q5 — Unchanged from my Round 1.** Preserve ledger/verdict strings; clarify the dashboard as “Not distinguishable under the primary band rule.” Reject “no robust signal.”

**AGREE:**
- Frozen production; no ledger rewriting; convert-both/no-splice; B3 only now.
- Disclose post-hoc choices; no historical figure transferred to a changed configuration.

**DISAGREE:**
- Gemini versus others: automatic BEY adoption.
- Opus versus most others: directional C6 warning.
- Sol/Kimi versus blanket ratification advocates: C2 completeness and C4 vintage verification.
- Council divided: supplementary interval placement and dashboard clarification.

**CHANGED-MY-MIND:**
- Adopt Kimi’s hashed, twelve-month full-history audit.
- Defer recurring decomposition display until that audit; neutral methods documentation remains acceptable.