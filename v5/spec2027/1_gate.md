# Forseglet spec 1/4 — benchmark-gaten fra september-refitten 2027 (RAADETS_2027 §2.1-2.3)

**Forseglet 2026-10-15.** Teksten er committet og pushet, FOER koden der bruger den skrives (RAADETS_2027 §12
trin 3). Koden laaser filens sha256 (LF-normaliseret) og stopper refitten hoejlydt, hvis filen er aendret
efter forseglingen. En aendring kraever en raadsbeslutning. Er spec og kode uenige, gaelder spec'en, og
uenigheden erklaeres og forelaegges raadet (§3.4).

Ratificeret tekst (§2.3, ordret):

> From 2027 the gate is as follows.
> - Δ = skill(F5) − skill(curve) on common origins.
> - If Δ > 1.96·SD_block(Δ), recomputed at each refit, the result is a **mandatory council agenda item**. This
>   is an *administrative review boundary, not a calibrated significance test*: crossing it is never labelled
>   "evidence" and never switches anything.
> - Printed beside it: the 80 %-power MDE (≈ 2.8·SD_block; ≈ 30 pp today), Δ without the largest-contributing
>   episode block, and Δ at universe starts 1953Q2 and 1960Q1.
> - The borrowed 4.42 pp is removed from the gate.

## 1. Ikrafttraeden

Gaelder for hver kalibrering med refit-maaned **R >= 2027-09**. En kalibrering med R < 2027-09 (herunder
enhver reproduktion af manifest 72c3371d) beholder v5.0.1-gaten uaendret, saa intet i driften flytter sig foer
refitten. Gaten skifter aldrig noget, uanset version (§2.1: ingen selektor; curve-only er operationel ved
raadets laas, RAADETS_V501 §6; F5 er en frossen benchmark).

## 2. Definitioner

- **Modeller.** F5 (fuldmodellen, fem features) og curve-only, hver estimeret paa sit eget raekkeunivers
  (RAADETS_V501 §2), fast lambda = 1.
- **Skill.** Walk-forward log-loss-forbedring i % mod den poolede basisrate over de scorede origins
  (`calibrate.metrics`; den publicerede definition). Walk-forwarden er `ablation2_nber.wf_nber` med L = 18,
  scoring fra 1960 og R_score = R (kun modne labels scores, §3.5).
- **Faelles origins.** Gaten beregnes kun, naar de to raekkeuniverser har identiske origin-identiteter
  (RAADETS_V501 §2, uaendret: ellers "comparison unavailable"). Koden asserter desuden, at de to
  walk-forwards' scorede lister af (origin, label) er identiske. Er de ikke det, stopper refitten med en fejl:
  en uparret gate maa aldrig printes som parret.
- **Δ (delta_pp)** = skill(F5) − skill(curve-only) paa de faelles origins, i procentpoint.
- **SD_block (sd_block_pp)** = standardafvigelsen (ddof = 1) over 1000 episode-blok-bootstrap-traek af den
  parrede Δ: seed 42, blokke = `ablation3_frekvens.episode_group` (origin-aaret -> naermeste efterfoelgende
  onset), blokke trukket med tilbagelaegning, traek med basisrate 0 eller 1 kasseres og erstattes. Det er
  praecis `ablation3_frekvens.mde_bootstrap` med F5's P som foerste og curve-onlys P som anden model.
  Genberegnes ved hver refit.
- **Kritisk vaerdi K (kritisk_vaerdi_pp)** = 1,96 · SD_block.

## 3. Reglen (ensidet)

- **Δ > K** (sammenlignet paa de uafrundede tal) -> `dagsordenspunkt = true`: et **obligatorisk punkt paa raadets
  dagsorden**.
- Ellers -> `dagsordenspunkt = false`.

Graensen er en administrativ reviewgraense, ikke en kalibreret signifikanstest. Udfaldet kaldes aldrig
"evidens", skifter aldrig den operationelle model og aendrer aldrig vaegte, baand, basisrate eller dom.

**Den laante 4,42 pp er fjernet.** 2027-gaten laeser ikke `ablation3_resultat.json`, og tallet 4,42 optraeder
ikke i nogen 2027-gate (manifest, weights.json, motor-output, diagnostik.json). Ordet "MDE" bruges kun om
80 %-MDE'en i pkt. 4.1; 1,96 · SD kaldes "kritisk vaerdi" (§2.2).

## 4. Printes altid ved siden af (ogsaa naar Δ <= K)

1. **80 %-MDE (mde80_pp)** = (z_0,975 + z_0,80) · SD_block = (1,959964 + 0,841621) · SD_block
   = 2,801585 · SD_block. Maerkes "normalteori-approksimation" (§1.2).
2. **Δ uden den stoerst bidragende episodeblok.** For hver blok k i de parrede origins beregnes Δ_−k: samme
   skill-definition paa de parrede origins uden blok k (den poolede basisrate genberegnes paa de resterende
   origins; er den 0 eller 1, er Δ_−k udefineret og blokken springes over). Den stoerst bidragende blok er
   k* = argmax_k (Δ − Δ_−k), dvs. den blok hvis udeladelse saenker Δ mest; ved lighed den tidligste blok.
   Printes: k*'s blok-id, foerste og sidste origin, antal origins, og Δ_−k*. Alle Δ_−k gemmes. Der refittes
   ikke: de samme walk-forward-P'er scores uden blokken.
3. **Δ ved universstart 1953Q2 og 1960Q1.** Begge modellers raekkeuniverser afkortes til kvartaler >= start
   (samme snit som `diagnostik.start_sensitivitet`), walk-forward som i pkt. 2, og Δ paa de faelles origins
   under samme identitetskrav. Kan identitetskravet ikke opfyldes ved en start, printes "comparison
   unavailable" for netop den start (ingen fejl, ingen tal).

## 5. Hvor det skrives

Manifestets og weights.json's `gate`-blok for en 2027-kalibrering har praecis disse felter:
`protokol` ("RAADETS_2027 §2.3"), `spec_sha256`, `identiske_origins`, `n_origins`, `curve_only_wf`,
`curve_only_brier`, `fuldmodel_wf`, `fuldmodel_brier`, `delta_pp`, `sd_block_pp`, `kritisk_vaerdi_pp`,
`dagsordenspunkt`, `mde80_pp`, `uden_stoerste_blok`, `ved_start`, `note`. Felterne `mde_pp`, `mde_gate_pp`,
`forskel_pp`, `fuldmodel_slaar` og `raadsbeslutning_paakraevet` findes ikke i en 2027-gate.

Uden identiske origins: `identiske_origins = false`, `curve_only_wf`, `curve_only_brier`, `note`
("comparison unavailable ..."), og ingen af de oevrige tal.

`note` (skabelon): "Delta {delta:+.2f}pp {'>' | '<='} kritisk vaerdi {K:.2f}pp (1,96 x SD_block {sd:.2f}pp):
{'obligatorisk punkt paa raadets dagsorden' | 'intet dagsordenspunkt'}. Administrativ reviewgraense, ikke en
kalibreret signifikanstest; kaldes aldrig evidens og skifter intet (RAADETS_2027 §2.3)."

Fuldmodellens statustekst i weights.json: ved Δ > K "Delta over kritisk vaerdi: obligatorisk punkt paa raadets
dagsorden (administrativ reviewgraense, ikke evidens); frossen benchmark, ikke operationel (RAADETS_2027
§2.1)"; ellers "frossen benchmark (RAADETS_2027 §2.1); Delta under kritisk vaerdi — intet dagsordenspunkt".

finalize6 printer gate-linjen, 80 %-MDE, Δ_−k* og Δ ved de to starter. Ved Δ > K printes desuden
"DAGSORDENSPUNKT (RAADETS_2027 §2.3): ..." — refitten fortsaetter, og intet skiftes. diagnostik.json's
`gate_mde`-blok (som baerer trin 3's 4,42) skrives ikke for en 2027-kalibrering; motor printer ikke
stoejgulv-linjen med 4,42 for en 2027-kalibrering.

## 6. Tests foer brug

- Reglen er ensidet: et stort negativt Δ udloeser intet; Δ lige over K udloeser; Δ = K udloeser ikke.
- 2027-gaten indeholder ikke 4,42 og ingen af de fjernede felter.
- 80 %-MDE = 2,801585 · SD_block; Δ_−k* er den blok, hvis udeladelse saenker Δ mest.
- En kalibrering med R < 2027-09 faar v5.0.1-gaten uaendret (manifest 72c3371d genskabes bit-identisk).
- Uparrede scorede lister stopper refitten.
