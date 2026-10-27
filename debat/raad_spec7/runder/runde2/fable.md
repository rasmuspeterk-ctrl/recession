**Round 2 — Claude Fable 5.1**

**1) Attacks**

**Sol Pro:** "Do not ratify C7: its F5/curve-only labels reverse the attribution in the brief's verified gate calculation." False. The brief verifies the gate as curve-only 27.05 − F5 23.16 = 3.89 pp. C7 prints "F5 +23.2 % vs curve-only +27.1 %". Same numbers, same assignment. There is no reversal; striking C7 on that ground would reopen a verified item. Sol Pro's separate request for 10,000 draws and a 5–95 % interval is also wrong in context: the existing 4.4 interval is pinned at 1000 draws, seed 42, 10–90 %, and Part A's purpose is comparability with it. Changing the bootstrap spec for one diagnostic makes the two intervals non-comparable for no gain in precision that matters at 9 blocks.

**Gemini:** "we switch the operational model to Curve_BEY … unless Δskill_OF(BEY − disc) < −0.50 pp." This is an unconditional switch dressed as a test. The two series differ by a smooth monotone transform; over 1954–2026 their correlation is > 0.99, and the paired skill difference will be a fraction of a pp either way. A −0.50 pp floor can essentially never bind, so the only outcome the rule admits is "switch". Worse, the rule is set with E1's gap table in hand — direction and magnitude known — which is exactly the outcome-informed selection §5.2 forbids. And "fixing the bug" is overstated: the 10y leg is a semiannual par CMT yield; BEY(d) is simple ACT/365 investment yield. The converted curve is *less* mismatched, not consistent. Gemini's own risk section concedes β may have absorbed the compression. Keep the switch a 2027 council decision with its own replay.

**DeepSeek:** "if |Δ oracle-free| ≥ 2 pp, the council must convene." This converts an author's prior into a trigger — the thing Grok and Sol Pro correctly warn against. A trigger at 2 pp creates an incentive to design the comparison panel so the number lands on the preferred side. Publish the prediction as "author's prior, not a criterion", off the result line. Also, DeepSeek accepts C7's interval "if labelled oracle-censored": labelling does not fix the asymmetry that only figure (ii) carries an uncertainty band.

**2) Steelman**

Grok's physical rule for item (4): the BEY P at the refit's live input never renders on the dashboard or in LOG.md. I had item (4) in `uscorede.konvention_bey` and treated the manifest hash as the firewall. Grok is right that the breach is by distribution, not code: the illegal CMT substitution already gives ~17.9 %, and a BEY-P screenshot would be cited as "the real P" the moment it diverges. Adopt: item (4) is written to the diagnostics file only. Same for Grok's anti-substitution sentence in C5, with the 17.9 % stated so the reader sees why it is illegal.

**3) Revisions**

**Q1:** unchanged core (seal, convert both, no splice, Jensen disclosure, mean-of-converted daily). Add: item (4) off dashboard and ledger (Grok); the |Δ| < 2 pp prediction labelled "author's prior, not a criterion", not printed beside the result (Grok); Kimi's binned paired diagnostics (<4, 4–8, ≥8 % with onset counts) — the high-rate episodes are the point and a mean hides them. Reject Gemini's switch rule and DeepSeek's trigger.

**Q2:** B3 only; delete B1/B2 from the spec text entirely (Grok, Opus) — a parked design is a half-authorised second shot. Replace my revision-audit sketch with Kimi's: 12 consecutive monthly full-history vintages, each sha256'd, median and max |revision| from vintage 1 for both TP and E = (y10 − TP) − 3m. Keep my pinned opening criterion but on E, not TP: max revision < 10 bp. Keep the verbatim E3 disclaimer ("a result on an implementation, not on the hypothesis").

**Q3:** C5 amended as in Round 1 (0.10 convention / 0.08 instrument) plus Grok's anti-substitution sentence. C6: my strip-to-numbers text stands; I reject Kimi's full removal (a reader of a curve-only model should see the decomposition exists) and Opus's amended text (keeps "almost all is term premium" + the literature, which is the directional claim in softer words).

**Q4:** C7 gate line: adopt Kimi — print "curve-only exceeded F5 by 3.89 pp on the same oracle-censored path" and drop the raw +27.1 %, which otherwise sits without the oracle-free figure. Oracle-free 219-origin interval first, as in Round 1. Freeze `MAERKE_MIN_DK` until the refit (Grok).

**Q5:** verdict string unchanged. I accept Kimi/Sol Pro's explanatory qualifier "under the primary band rule" in the dashboard prose only; "no robust signal" stays rejected.

**AGREE:** seal Part A, convert both, no GS3M splice, GS3M as check only; no automatic switch; B1/B2 not run; B3 after a revision audit; C6 as committed breaches the firewall's spirit — 98 % and Rosenberg-Maurer go; C2, C3 ratified; C1's 5 bp disclosed as post hoc and frozen; ledger wording "not distinguishable" unchanged.

**DISAGREE:** (a) Gemini's non-inferiority switch vs everyone else; (b) DeepSeek's 2 pp convening trigger vs Grok/Sol Pro/me; (c) C6 — remove (Kimi) vs strip to numbers (me, Grok, Gemini) vs keep with model-dependence caveat (Opus, DeepSeek); (d) C7 interval — both intervals in §1.2 order (me, Gemini, Grok) vs footnote/label only (DeepSeek, Sol Pro); (e) C7 gate line — Sol Pro's "reversal" claim is factually wrong and should be withdrawn; (f) bootstrap spec: Sol Pro's 10,000/5–95 vs the pinned 1000/10–90.

**CHANGED-MY-MIND:** item (4) off the dashboard (Grok — distribution breach); delete B1/B2 text rather than list them (Grok/Opus); Kimi's audit design replaces mine (more concrete, both TP and E); gate line as a 3.89 pp difference (Kimi — removes the last standalone +27.1 %); explanatory "band rule" qualifier in dashboard prose (Kimi/Sol Pro — clarifies without a second verdict).