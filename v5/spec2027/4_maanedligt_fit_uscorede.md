# Forseglet spec 4/4 — det maanedlige fit og de uscorede felter fra september-refitten 2027 (RAADETS_2027 §3.3, §4, §10.4)

**Forseglet 2026-10-15.** Teksten er committet og pushet, FOER koden der bruger den skrives (RAADETS_2027 §12
trin 3). Koden laaser filens sha256 (LF-normaliseret) og stopper hoejlydt, hvis filen er aendret efter
forseglingen. En aendring kraever en raadsbeslutning. Er spec og kode uenige, gaelder spec'en (§3.4).

Ratificeret tekst (ordret):

> 3.3 From the 2027 refit a monthly curve-only fit is calibrated each September alongside the quarterly one.
> Its P is logged as an **unscored** column in every ledger row. Its specification, including the loss/penalty
> normalisation, is sealed and pushed before the 2027 refit. The sealed spec also re-runs the paired same-origin
> diagnostic of §3.2(b) on the 2027 panel, with origin-set and label identity checked in code. Its outcome is
> unknown at sealing, and it is published whatever it shows.
>
> 4. 1947Q2 is kept. **[now]** P at starts 1953Q2 and 1960Q1 is printed in every diagnostics report; from 2027
> it is also an unscored field in every ledger row.
>
> 10.4 Live censoring inside an announced recession: ratified on two conditions: [...] every censored month keeps
> an **unscored** record of P and the eventual outcome (UDFALD.csv supplementary column).

Forbeholdene til protokollen (Sol, Argon, Grok, Kimi: fastlaas normaliseringen numerisk; Fable: identiteterne
asserteres og fejler hoejlydt; "does not favour monthly" maa ikke laeses som "monthly is worse") er indarbejdet.

## 1. Ikrafttraeden og status

Alt i denne spec gaelder for kalibreringer med refit-maaned **R >= 2027-09** og for hovedbogsraekker logget under
en saadan kalibrering. Foer det skrives intet af det nedenstaaende (hverken i weights.json, manifester, LOG.md,
hovedbog.jsonl eller dashboard.json). Ingen af felterne er scorede: BEDOEMMELSESNOEGLE.md aendres ikke (§7.1), P,
baand, basisrate og dom kommer fortsat kun fra det kvartalsvise curve-only-fit, og felterne indgaar aldrig i en
dom, en gate eller en trigger.

## 2. Det maanedlige curve-only-fit (§3.3)

Beregnes af finalize6 ved hver refit (R >= 2027-09), paa refittens snapshot og R, ved siden af kvartalsfittet.

- **Univers.** Maaneder (aar, maaned), hvor den maanedlige kurve (`calibrate.build_monthly`'s "curve" = 10y − 3m-
  bill; Shillers LTR foer GS10 findes, som i kvartalsuniverset) er defineret, OG hvis kvartal ligger i det
  kvartalsvise curve-only-univers (`ablation2_nber.build_dataset(snap, ["curve"])`). Samme rygrad-forlaengelse
  som kvartalsuniverset (GS10/TB3MS-maaneder efter rygradens sidste maaned). Det er praecis
  `analyser/frekvensgate.byg_maanedligt(snap, Dq, ["curve"])`.
- **Origin og label.** Origin = maaned m; vindue (m, m + 12]; label ved R = 1, hvis en USREC-onset i vinduet er
  annonceret senest i R (`avail`), ellers 0.
- **Berettiget ved R.** m + 12 + 18 <= R, og m ligger ikke i en recession, hvis top er annonceret senest i R —
  samme regel som `ablation2_nber.eligible_fit` (§3.5; §9.2-alderen maales fra vinduets slutning).
- **Standardisering.** mu og sd (ddof = 1) over de berettigede raekker.
- **Tab og straf (fastlaast normalisering).** L2-logit med SUMMERET log-loss og straf (λ/2)·Σ w_k² paa
  haeldningerne (interceptet er ustraffet) — `calibrate.fit(Z, y, l2=λ)`. Kvartalsfittet har λ_q = 1 paa N_q
  raekker. Det maanedlige fit faar samme straf PR. OBSERVATION:

  **λ_m(R) = λ_q · N_m(R) / N_q(R), med λ_q = 1,**

  hvor N_m(R) er antallet af berettigede maanedsraekker ved R, og N_q(R) antallet af berettigede kvartalsraekker
  ved samme R (curve-only, `eligible_fit`). λ_m genberegnes i hvert traeningsvindue (Sol). Ved v5.0.1-panelet er
  N_q = 267 og λ_m ca. 3,0 (Argon, Kimi). Ingen anden normalisering og ingen tuning.
- **Gemmes** i manifestet og weights.json under `uscorede.maanedligt_fit`: `features` (["curve"]), `mu`, `sd`, `w`
  (4 decimaler, som manifestvaegte), `l2`, `N_m`, `N_q`, `n_pos`, `base_rate`, `estimering_slut` (YYYY-MM),
  `spec_sha256`. Feltet `uscorede` staar uden for manifestets indholds-hash (det er ikke den operationelle
  kalibrering); genbruges et manifest, genbruges ogsaa dets `uscorede`.

## 3. Den uscorede kolonne (§3.3)

I hver hovedbogsraekke under en 2027-kalibrering: **P_maanedligt_fit** = det maanedlige fits P ved raekkens
operationelle live-input (samme kurvevaerdi som raekkens P: trailing kalendermaaned af daglige DGS10 − DTB3, ellers
maanedstallet). LOG.md: procent med 1 decimal; hovedbog.jsonl: `p_maanedligt_fit` med 6 decimaler. motor printer
den i sektion 1 som "uscoret (RAADETS_2027 §3.3)" og aldrig i dommen.

## 4. Den parrede samme-origins-diagnostik paa 2027-panelet (§3.3 / §3.2(b))

Koeres af diagnostik.py for hver kalibrering med R >= 2027-09 og skrives i diagnostik.json under
`maanedlig_parret` (motor sektion 8 printer den; dashboard.json faar den via `diagnostik`).

- **Kvartal:** den publicerede walk-forward `ablation2_nber.wf_nber(D_curve, ..., L = 18, R_score = R)`.
- **Maanedlig:** purget expanding-origin walk-forward paa maanedsraekkerne — `ablation3.wf_monthly`/
  `frekvensgate.wf_maanedlig`: refit ved hver origin-maaned i fra 1960 med R = m_i; traening = maaneder j < i, der er
  berettigede ved R (pkt. 2); kraever >= 180 raekker og >= 18 positive; labels ved R; standardisering paa
  traeningen; scoring springes over for origins i recession efter den endelige kronologi og for umodne origins
  (m_i + 12 + 18 > R_score).
- **To straf-varianter, begge publiceres:** (A, primaer) den forseglede normalisering λ_m(R) = N_m(R)/N_q(R) i hvert
  traeningsvindue (N_q(R) = kvartalsraekker berettigede ved samme R); (B, kontinuitet med §3.2(b)) λ = 1.
- **Tynding:** de maanedlige scorer i kvartalsslut-maanederne (marts, juni, september, december) noegles som
  (aar, kvartal).
- **Identiteter, asserteret i kode (fejler hoejlydt, printes ikke blot):** for hver variant skal (1) maengden af
  tyndede maanedlige origins vaere lig maengden af scorede kvartalsorigins, (2) labelen vaere ens paa hvert origin
  og (3) den poolede basisrate vaere ens. Er en af dem brudt, stopper diagnostik.py med en fejl (intet skrevet),
  og bruddet forelaegges raadet.
- **Forskellen:** Δ = skill(tyndet maanedlig) − skill(kvartal) paa de parrede origins (pp), med
  `ablation3.mde_bootstrap` (episode-blok-bootstrap, 1000 traek, seed 42): `forskel_pp`, `sd_pp`, `ci10`, `ci90`,
  `kritisk_vaerdi_pp` (1,96 · SD), `n_parrede_origins`, `labels_uenige` (= 0), `basisrate`.
- **Sprog:** "Beskrivende diagnostik; aendrer intet. |Δ| under den kritiske vaerdi er fortegns-uinformativt — et
  negativt Δ betyder ikke, at maanedlig er daarligere (Fable)." Resultatet publiceres uanset udfald.

## 5. P ved universstart 1953Q2 og 1960Q1 (§4)

- finalize6 fitter ved hver refit (R >= 2027-09) curve-only paa raekkeuniverset afkortet til kvartaler >= 1953Q2
  og >= 1960Q1 (samme snit og samme `finalize6.fit_model` som `diagnostik.start_sensitivitet`) og gemmer
  `uscorede.start_1953Q2` og `uscorede.start_1960Q1` (`mu`, `sd`, `w`, `n_obs`, `base_rate`).
- Hver hovedbogsraekke under en 2027-kalibrering faar **P_1953Q2** og **P_1960Q1** ved raekkens live-input (LOG.md:
  1 decimal; hovedbog.jsonl: `p_start_1953Q2`, `p_start_1960Q1`). 1947Q2 forbliver protokolkonstanten; felterne
  er uscorede.

## 6. Censurerede maaneder (§10.4)

- En raekke logget med dom `censureret` under en 2027-kalibrering beholder P (kolonnen P, som i dag) og faar i
  hovedbog.jsonl blokken `uscoret_censur` = {`p`, `p_maanedlig`, `p_maanedligt_fit`, `vindue`, `note`:
  "uscoret (RAADETS_2027 §10.4): raekken scores ikke (noeglen §1 d); P og det endelige udfald foeres"}.
- **UDFALD.csv** faar den supplerende kolonne `uscoret_censureret` (sidste kolonne). Ved hver afgjort raekke skrives
  "ja", naar raekken er logget med dom `censureret`, ellers "nej". Y for en censureret raekke er det endelige udfald
  efter noeglens regel (c) for raekkens vindue (fx en dobbeltdyk-onset). Raekker med "ja" scores aldrig.
- CI haandhaever konsistensen: hver raekke i UDFALD.csv skal henvise til en logget raekke i LOG.md, Y er 0 eller 1, og
  `uscoret_censureret` er "ja", hvis og kun hvis LOG-raekkens dom er `censureret`.

## 7. LOG.md

Overskriften faar kolonnerne `P_maanedligt_fit | P_1953Q2 | P_1960Q1` efter `P_maanedlig` (dokumenteret som
"fra september-refitten 2027, uscorede"). Raekker under kalibreringer foer 2027-09 skrives som i dag (13 celler);
raekker under en 2027-kalibrering faar 16 celler (en `ikke logget`-raekke faar tre tomme celler). Eksisterende
raekker roeres aldrig.

## 8. Tests foer brug

- Normaliseringen: λ_m = N_m/N_q i fittet og i hvert walk-forward-vindue; λ = 1-varianten er ablation3's.
- Det maanedlige univers er identisk med `frekvensgate.byg_maanedligt`.
- Paa v5.0.1-panelet (snapshot 2026-09-19, R = 2026-09) reproducerer variant B den publicerede §3.2(b)-diagnostik:
  198 parrede origins, 0 uenige labels, Δ −1,02 pp, SD 2,58 pp (kun B; A's tal er ukendte ved forseglingen og
  testes kun for struktur og identiteter).
- Identitetskontrollen fejler hoejlydt ved en syntetisk uoverensstemmelse (manglende origin, anden label).
- Foer ikrafttraeden skriver hverken finalize6, motor eller diagnostik nogen af felterne (manifest 72c3371d genskabes
  bit-identisk; dashboard.json-replayen er bit-identisk).
- UDFALD.csv-tjekket: syntetiske fejl (ukendt raekke, Y uden for {0,1}, censureret raekke uden "ja", "ja" paa en
  ikke-censureret raekke) afvises; den committede fil og LOG.md er konsistente.
