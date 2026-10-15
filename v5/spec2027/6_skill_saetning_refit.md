# Forseglet spec 6 — skill-saetningen ved september-refitten 2027: nested λ oracle-fri og styrkeklausulen (RAADETS_2027 §1.2)

**Forseglet 2026-10-15.** Teksten er committet og pushet, FOER koden der bruger den skrives ("skriftlig
specifikation gaar forud for koden", RAADETS_2027 §3.3-3.4). Koden laaser filens sha256 (LF-normaliseret) og stopper
hoejlydt, hvis filen er aendret efter forseglingen. En aendring kraever en raadsbeslutning. Er spec og kode
uenige, gaelder spec'en.

Ratificeret tekst (§1.2, ordret, uddrag):

> At the 2027 refit the nested-λ oracle-free figure is computed, so the sentence compares three realised numbers.
> The power clause is re-derived from the §6.2 configuration-specific replay once it exists, and is labelled
> "order of magnitude". The ≈ 30 pp MDE of §2.3 is labelled a normal-theory approximation.

DeepSeeks forbehold (runde 5): saetningen "oracle-free counterpart has not been computed" maa aldrig slettes,
foer den konfiguration er beregnet under de samme forseglede regler; 2027-refitten skal producere tallet, foer en
overskrift bruger det.

Den tredje del er allerede opfyldt: 2027-gatens 80 %-MDE er maerket "normalteori-approksimation" (spec 1 §4.1).

## 1. Ikrafttraeden

Begge beregninger koeres ved hver refit med refit-maaned R >= 2027-09, paa refittens snapshot og R — ikke foer.
Indtil da viser motor og dashboard.json saetningen uaendret (med "oracle-fri udgave ikke beregnet" og den
nuvaerende styrkeklausul).

## 2. Nested λ, oracle-fri (diagnostik.py -> diagnostik.json `nested_oracle_fri`)

- **Origins og traening:** den kvartalsvise curve-only walk-forward med `ablation2_nber.wf_nber`'s regler (fra
  1960; traening = origins modne ved origin-maaneden og ikke i en recession annonceret ved den; >= 60 raekker og
  >= 6 positive; labels ved origin-maaneden; standardisering paa traeningen; R_score = R).
- **λ pr. origin:** praecis ablation9's forseglede design (`ablation9_nested`): grid {0,1; 0,3; 1; 3; 10; 30; 100},
  indre leave-one-episode-blok-out-CV paa traeningen (blok = forrige onset frem til onset k), folds med < 3
  positive i traeningsdelen springes over, λ = argmin af middel-log-loss, uafgjort -> stoerre λ. Funktionerne
  `ablation9_nested.blokke`, `indre_cv` og `vaelg_lambda` bruges uaendrede.
- **Oracle-fri scoring:** diagnostik 4.5's regel ("alle live-publicerbare"): et origin scores, medmindre det ligger
  i en recession, hvis top er annonceret senest ved origin-maaneden — samme origins som noeglens referencetal
  (oracle-fri, fast λ).
- **Metrik:** log-loss-forbedring (og Brier-skill) mod den poolede basisrate over de scorede origins (`C.metrics`).
- **Gemmes:** `nested_oracle_fri` = {`improvement`, `brier`, `n`, `lambda_fordeling`, og til kontrol paa samme
  koersel: `fast_oracle_fri` (skal vaere lig diagnostik 4.5's "alle live-publicerbare"), `nested_orakel`
  (orakel-censureret nested, ablation9's definition)}.
- **Selvtjek i testsuiten (paa v5.0.1-panelet):** samme kode reproducerer oracle-fri fast λ +20,37 % (219 origins)
  og orakel-censureret nested λ +18,32 % (198 origins, ablation9). Det oracle-fri nested tal beregnes ikke foer
  refitten.

## 3. Styrkeklausulen re-afledt af den konfigurationsspecifikke replay (replay2027.py -> `styrke`)

Input: replayens raekker (spec 3 §3) under censurvariant 1 (realtid, motorens aabne-episode-regel) — de raekker,
hovedbogen faktisk ville score. Pr. scoret raekke d = L0 − Lm, hvor L0 er log-loss for raekkens LOGGEDE basisrate
og Lm for P som logget (noeglens metrik). Censurerede maaneder er tomme pladser i kalenderen.

- **Blokke:** bund til bund (USREC-bunde) i kalendermaaneder over replayens origin-maaneder, inkl. censurerede
  maaneder; en blok er komplet, hvis den indeholder en onset. Alle blokke indgaar i puljen (som styrke-
  simulationens variant A).
- **Simulation:** `analyser/styrke_simulation.py`'s maskineri uaendret (`hovedbog`, `koer`, `opsummer`,
  `aar_til_80`): T = 5, 10, 20, 50, 100, 150, 200 aar; 3000 hovedboeger pr. T; 600 bootstrap-traek; seed 11; H1 =
  historisk d, H0 = d centreret paa puljens middel.
- **De tre tal i klausulen:**
  1. aar til 80 % styrke = `aar_til_80(...)["interpoleret_aar"]` for den nominelle cluster-t (afrundet til
     naermeste 10 aar; "over 200" hvis ikke naaet);
  2. P(mindst 3 komplette cyklusblokke inden for 20 aar) = andelen af 3000 simulerede 20-aars-hovedboeger (samme
     traekningsskema som `hovedbog`, seed 11), der indeholder mindst 3 HELE blokke med onset (2 decimaler);
  3. naive tests' falsk-positiv-rate ved 5-20 aar = min..max over T i {5, 10, 20} af H0-forkastelsesraten for den
     naive iid-t og 4.4-blok-bootstrappen (hele procent).

  Definition 2 giver paa styrkesimulationens egen pulje (variant A) 0,25 — verifikatorens tal bag den nuvaerende
  klausul. Definition 3 giver dér 45-53 %; den nuvaerende klausuls "36-53 %" kan ikke genskabes eksakt fra
  resultatfilen. Definitionerne er fastlagt her, foer refitten, og et andet spaend efter refitten er en foelge af
  definitionen og de nye data, ikke et valg.
- **Tekst (skabelon, i samme saetning som skill-tallene):** "80 % styrke kraever stoerrelsesordenen {1} kalenderaars
  hovedbog; P(3 komplette cyklusblokke inden for 20 aar) = {2}; naive tests forkaster en sand nulhypotese {3a}-{3b} %
  af gangene ved 5-20 aar (stoerrelsesorden; re-afledt af den konfigurationsspecifikke replay, RAADETS_2027 §1.2)".

## 4. Saetningen efter refitten (motor.py og dashboard.json `skill_saetning`)

Raekkefoelgen er uaendret og i een saetning: (i) oracle-fri fast λ, (ii) orakel-censureret fast λ, (iii) nested λ.
Naar diagnostik.json for kalibreringen i drift har `nested_oracle_fri`, bliver (iii) "nested lambda, oracle-fri: +X %
(n origins; orakel-censureret nested: +Y %)" — tre realiserede tal paa samme panel. Ellers staar (iii) som i dag med
"oracle-fri udgave ikke beregnet". Naar replay2027_resultat.json hoerer til kalibreringen i drift (samme manifest-
hash), erstatter den re-afledte klausul den nuvaerende; ellers staar den nuvaerende. +27,1 % staar aldrig alene.

## 5. Tests foer brug

- Selvtjekkene i pkt. 2 (20,37 / 219 og 18,32 / 198).
- Definition 2 paa styrkesimulationens egen pulje: 0,25 (+/- 0,005).
- Styrke-funktionen paa en lille simulation (faa traek): blokkene daekker replayens kalendermaaneder, censurerede
  maaneder er tomme, og klausulen udfyldes efter skabelonen.
- skill_saetning: uden de nye felter er teksten uaendret; med dem staar oracle-fri nested og den re-afledte klausul i
  den foreskrevne raekkefoelge, og "ikke beregnet" forsvinder kun, naar tallet findes.
