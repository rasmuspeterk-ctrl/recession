# MOTOR v5 — kode, ritualer og byggelog

Bygget efter raadets enstemmige blueprint ([../RAADETS_KONSENSUS.md](../RAADETS_KONSENSUS.md)).
**I drift:** v5.0.1 (manifest 72c3371d, refit 2026-09), curve-only-logit paa NBER-onset-labelen,
daglig live-kurve fra 2026-09-28, kode-review 2026-10-15 indarbejdet (afsnittet nederst).
Byggeloggen fra trin 1 og frem staar laengere nede som historik — den beskriver hvordan modellen
blev til, ikke hvordan den koeres i dag.

## Filerne (aktuel drift)

| Fil | Rolle |
|---|---|
| `fetch.py` | Henter 37 serier noeglefrit (36 FRED + Fed Boards EBP-CSV) parallelt (~30 s), skriver byte-eksakt hashet snapshot i `data/raw/<dato>/`, bygger rygraden, printer diff mod forrige snapshot (ny obs / aendret vaerdi / revideret historik / rullende vindue) |
| `spine.py` | Rygraden (komposit Shiller + FRED + multpl) og dens guards — og **seriernes rolletabel** `SERIER` (rolle P/refit/rygrad/kontekst + licens). Kun P- og refit-serier nedlaegger veto |
| `motor.py` | Maanedlig aflaesning og hovedbogslogning (`--log` kun dag 10-20), `--json` til dashboardet |
| `finalize6.py` | Rekalibrering — KUN ved en §3.2-trigger (september-snapshot eller ny raekke i `nber_announcements.csv`); ellers kraeves `--reparation "<begrundelse>"`. `--legacy` = legacy-replay |
| `diagnostik.py` | RAADETS_V501 §4-diagnostik + sti, universstart, flips, styrke -> `diagnostik.json` |
| `calibrate.py` | Hjaelpefunktioner for hele kaeden (read_fred, live_kurve, fit ...). Som script HISTORISK (trin 1): skriver `calibrate_resultat.json`, roerer aldrig `weights.json` |
| `ablation2_nber.py` | NBER-labelen, annonceringstabellen, USREC-krydstjekket, eligibility og den forklarede origin-audit. Som script (`--promote`) HISTORISK — koer ikke i drift |
| `ablation3/4/7/8_*.py`, `audit5_alfred.py` | Historiske, afsluttede tests (frekvens, features, curve+cape, AWHMAN, ALFRED) — koer ikke i drift |
| `test_v5.py` | 111 tests, stdlib unittest, ingen netvaerk (~35 s) |
| `nber_announcements.csv` | NBER's annonceringsdatoer (top/bund) — se *NBER-vedligehold* nedenfor |
| `manual/` | `manual.json` (S&P vs 52u-top, live-CAPE, marginlaan y/y + deres datoer), `shiller_yale_2023-09.csv` (uforanderlig Yale-kopi), `seam_check_2023.json`, evt. `outliers_accepteret.json` |
| `kalibreringer/` | Kalibreringsmanifester (v5.0.1 §3.3): et pr. kalibrering, index.json, legacy_mapping.json |
| `weights.json`, `diagnostik.json` | Den kalibrering der er i drift og dens diagnostik (skrives kun af finalize6/diagnostik) |

## Maanedligt ritual (~5 min) — logvindue dag 10-20

```
python fetch.py                  # hent + rygrad + guards + diff-tjek med oejnene
# opdater manual/manual.json: spx_vs_hi + spx_dato, cape + cape_dato, margin_yoy + margin_periode
python fetch.py                  # igen, saa snapshottet baerer de manuelle tal
python motor.py --log --json     # aflaesning, prospektiv raekke i ../LOG.md + ../hovedbog.jsonl, dashboard.json
python -m unittest test_v5       # 111 tests
```
Hovedbogen (`../LOG.md`) er den eneste fuldt prospektive test: een raekke pr. maaned, skrevet FOER
udfaldet kendes; historiske raekker roeres aldrig. Den beskytter mod look-ahead, men er statistisk
svag — hvordan den scores, og hvorfor ingen dom maa formuleres foer mindst 3 komplette cyklusblokke,
staar i [../BEDOEMMELSESNOEGLE.md](../BEDOEMMELSESNOEGLE.md). `--log` virker kun dag 10-20; en maaned
uden raekke bliver en eksplicit `ikke logget`-raekke. Mellemlaesninger (motor uden `--log`) er frie.

## NBER-vedligehold (F7) — FOER fetch.py, hver maaned

Tjek [nber.org/research/business-cycle-dating](https://www.nber.org/research/business-cycle-dating).
Har komiteen dateret en ny top eller bund, tilfoej en raekke i `nber_announcements.csv`
(`event,cycle_month,announcement_date,source`, fx `peak_2027,2027-01,2027-09-15,nber.org/...`) og commit
den FOER fetch.py. Motor krydstjekker tabellen mod USREC ved hver koersel og blokerer `--log`
("ANNONCERINGSTABEL UDE AF SYNK MED USREC"), hvis USREC har en post-1979-onset uden peak-raekke, eller
tabellen har en raekke uden USREC-episode (fx fordi FRED endnu ikke har opdateret USREC — vent saa).
En ny raekke er en deterministisk rekalibreringstrigger (§3.2b). Tabellen hashes kanonisk (raekkernes
indhold, ikke bytes), saa linjeskift og formatering ikke udloeser en falsk datering.

## Rekalibrering (RAADETS_V501 §3) — hver september, eller naar nber_announcements.csv faar en ny top/bund

```
python finalize6.py      # gulv + forklaret audit mod forrige manifest + bro + manifest -> weights.json
python diagnostik.py     # §4-diagnostik -> diagnostik.json (~95 s)
python motor.py --json   # verificer; naeste --log-raekke faar automatisk bro-noten
```
Vaegte, standardisering og basisrate er frosne mellem rekalibreringer. finalize6 naegter at koere uden
deterministisk trigger (en reparation kraever `--reparation "<begrundelse>"`, som skrives i manifestet),
paa et snapshot hvis rygrad ikke er refit-klar (multpl/SP500-udfald eller stale rygrad), og naar
annonceringstabellen er ude af synk med USREC. En ny kalibrering faar en ny version (5.0.2, 5.0.3 ...),
en uaendret genbruger manifestet og registrerer koerslen i `weights.json.koersel`. Et skift af den
operationelle model kraever `kalibreringer/raadsbeslutning.json` (§6). Legacy-replay til enhver tid:
`python finalize6.py --legacy` (skal give w=[-2.1755,-1.6907], n_obs 264; CI koerer den ved hvert push).

Test (stdlib unittest, ingen netvaerk, ~35 s): `cd v5 && python -m unittest -v test_v5`. Koer den
efter enhver kodeaendring, foer maanedsritualet.

# Byggelog (historik)

## MANGLER FOER ACCEPTANCETESTEN KAN KOERES: manual/shiller.csv

v4's kalibrering brugte Shiller-historikken 1871+ (data/spx.csv), som ikke fulgte
med i zippen. Laeg filen som `manual/shiller.csv` med header:

```
Date,SP500,CPI,LTR,CAPE
1871-01,4.44,12.46,5.32,
...
```

(= v4's data/spx.csv-kolonner: Date, SP500, Consumer Price Index, Long Interest
Rate, PE10. Kilde: ie_data.xls fra www.econ.yale.edu/~shiller/data.htm.)

## Acceptancetest — status 2026-08-09 (foerste koersel)

Koert paa Yales offentlige ie_data.xls (automatisk konverteret). Resultat:

- **DETERMINISME: OK** — to koersler giver identisk weights.json
- **Episoder: 11 = 11** (2001 korrekt fravaerende under teknisk label) og
  tabellens rangorden matcher v4 (saet 5 bedst af 1-5; kontrol-uden-kurve daarligst)
- **AFVIGER paa niveau**: 305 kvartaler (1947Q2-2023Q2) vs v4's 359; wf-forbedring
  +19,1% vs +22,9%; mu/sd-forskydninger i realrate/d_infl

Attribuerede aarsager (dokumenteret, ikke jagtet — raadets S2):
1. Yales offentlige Shiller-fil slutter **sep 2023**; v4's spx.csv gik til 2026.
2. v4's gdp.csv daekkede mere end A191RL1Q225SBEA (1947Q2-); v4 talte 359 kvartaler.
3. v4's y10.csv var formentlig daglig DGS10 (v4's juli-2026 = 4,40%); vi bruger
   GS10-maanedsgennemsnit (juli 2026 = 4,60%) — smaa kurve-niveauforskelle.

For fuld v4-identitet: laeg v4's originale data/-filer (spx.csv → manual/shiller.csv
m.fl.) ind og genkoer. Bemaerk dog at raadet allerede har PENSIONERET +22,9% som
max-over-search (blueprint sektion 4) — v5-baselinen genudledes under nested
selektion i trin 2-4, saa pipeline-troskab (determinisme, episoder, rangorden)
er acceptancetestens reelle formaal, og DEN er bestaaet.

## Byggeorden-status (blueprint sektion 10)

- [x] **1. Reproducerbarheds-refaktor** — denne mappe (determinisme OK; niveaudiff mod v4 attribueret, se ovenfor)
- [x] **2. Label-ablation: teknisk → NBER-onset** — `ablation2_nber.py`, alle gates bestaaet
      (+33,2% log-loss / +33,6% Brier vs teknisk +19,1%; 2001 fanges med max p 76%;
      embargo-spaend L=12/18/24 kun 1,7pp; PROMOVERET — weights.json er nu NBER-onset,
      teknisk baseline gemt som weights_trin1_teknisk.json; resultat: ablation2_resultat.json)
- [x] **3. Frekvens-ablation** — `ablation3_frekvens.py`: TESTET, IKKE BESTAAET.
      Kvt-tyndet maanedlig 32,1% vs krav 32,2% (kvartal 33,2 − 1pp-gate) — fejlet
      med 0,1pp. Parret forskel −1,1pp, MDE 4,4pp: forskellen ligger dybt under
      stoejgulvet, men gaten lempes ikke efter resultatet (Grok R6). KVARTAL
      FORBLIVER PRIMAER. Fuld maanedlig (36,8%) rapporteret som reference —
      overlaps-inflateret. Resultat: ablation3_resultat.json
- [x] **4. Feature-genforsvar** — `ablation4_features.py`: FEATURE-SAETTET UAENDRET.
      Alle 3 udfordrere "testet, ikke bestaaet" (sahm_t dLL −1,7; claims_mom −61,9
      paa kort sample; permits_yoy −14,5 — alle med persistens-flag <60%).
      Bemaerk: sahm_t's fortegn VENDER under onset-censureringen (hoej Sahm uden
      for recession = typisk lige-efter-recession) — Statistikerens R1-forudsigelse
      bekraeftet. Incumbents: curve uundvaerlig (drop koster 44,6pp), cape_pct
      bekraeftet (drop koster 3,2pp — Geminis R1-position afkraeftet); realrate/dd/
      d_infl marginale men under demotions-gaten. ACM-substitution: −77,9pp fuld-sti
      (pre-1961-straffen + kort faelleshistorik) — raa kurve bestaar, 2023 forbliver
      dokumenteret fejlmode. Resultat: ablation4_resultat.json
- [x] **5. ALFRED vintage-audit** — `audit5_alfred.py`: AUDIT FROSSET, ingen pipeline.
      CPI-revisioner maalt paa 52 vintages/312 obs: gns |d|=0,003pp, max 0,12pp;
      worst-case skill-udsving 0,11pp << 2pp-graensen. 2022 H1-vintage-flippet
      dokumenteret (advance −1,6/−0,9 fyrer; revideret −1,0/+0,6 fyrer ikke).
      Resultat: audit5_resultat.json
- [x] **6. Output/dom-ombygning** — `finalize6.py` + nyt `motor.py`: GATEN BED.
      Curve-only (+34,3% LL) slaar fuldmodellen (+33,2%) paa NBER-onset-labelen;
      forhaandsforpligtet fallback eksekveret: OPERATIONEL MODEL = CURVE-ONLY-
      PROBIT, fuldmodellen printes ved siden af som "testet, ikke bestaaet mod
      benchmark" (LL-forskel 1,1pp < stoejgulv ~4pp; Brier gaar modsat — kontekst
      printes, dommen aendres ikke). Foerste laesning: P=20,1% [14,4-29,2%] vs
      basisrate 18,2% — IKKE SKELNELIG FRA BASISRATEN.

## v5.0 ER KOMPLET — alle 6 trin gennemfoert 2026-08-09

*(v5.0-tekst, afloest af v5.0.1:)* Rekalibreringskaede (sjaelden): `fetch.py` → `ablation2_nber.py --promote` →
`finalize6.py`. Maanedligt ritual uaendret: `fetch.py` + manual.json + `motor.py`. **I dag:** kun
`finalize6.py && diagnostik.py` ved en §3.2-trigger; `ablation2 --promote` koeres ikke.

## v5.2-testen: AWHMAN — TESTET, IKKE BESTAAET; INFORMATIONSSOEGNINGEN LUKKET

Koert 2026-08-10 efter grand review (6-5-splittet raad) og Rasmus' go.
`ablation8_awhman.py`, Sols forseglede spec (6m annualiseret aendring, lagget,
negativt fortegn). Resultat: dLL −0,44pp (goer modellen DAARLIGERE), persistens
43,1%, aera-split vender (+0,98 pre-1990 / −1,81 post-1990); fortegnet var
korrekt og 100% stabilt — oekonomien er aegte, men informationen ligger allerede
i kurven ved 12m-horisonten (DeepSeeks forudsigelse ordret). Sekundaer F5+awh:
+0,04pp ≈ nul. HERMED ER FEATURE-SOEGNINGEN LUKKET: sahm, claims, permits, ACM,
curve+cape og AWHMAN — alle testet, alle publiceret, alle afvist. Kurven staar
alene, og hver fremtidig maanedslaesning er den egentlige eksamen.

## v5.1-testen: curve+cape — TESTET, IKKE BESTAAET (data-foreslaaet)

Koert 2026-08-09 efter Rasmus' godkendelse (`ablation7_curvecape.py`, een koersel).
Fejlede 3 af 6 forhaandsregistrerede gates: G2 (Brier +1,47 < 2,0; LL +2,49 bestod),
G3 (kun 50% af LOEO-folds paa niveau) og — vigtigst — G5, anti-forurenings-tjekket:
fordelen findes KUN post-1990 (+5,31pp); pre-1990 er subsettet DAARLIGERE (−0,34pp).
Selektionsforureningens signatur. MDE 12,3pp. Linjen staar permanent i benchmark-
tabellen; delmaengde-jagten er LUKKET — ingen ny subset-hypotese uden ny oekonomisk
begrundelse (praeregistreret i ablation7's header). Resultat: ablation7_resultat.json

## Vedligehold 2026-09-08 (kode-review, ingen modelaendring)

- `finalize6.py` bygger de permanente benchmark-linjer (curve+cape, curve+awh) fra
  `ablation7_resultat.json`/`ablation8_resultat.json` i stedet for fra den gamle weights.json:
  `ablation2 --promote` overskrev den foer finalize6 laeste den, saa linjerne forsvandt ved
  hvert maanedsritual (vaek siden 2026-08-12). `n_episoder` og fuldmodel-noten beregnes nu i
  stedet for at vaere haandskrevne, og den operationelle models vaerste walk-forward-fejlalarm
  gemmes i weights.json og printes i dommen (foer: v4's 76,9% som fast tekst).
- `fetch.py` henter parallelt, skriver raa bytes (hash i meta.json = filens hash paa disk;
  foer hashedes LF-tekst mens Windows skrev CRLF, 20/20 mismatch), flagger ny obs / aendret
  sidste vaerdi / revideret historik, og maerker snapshots med fejlede serier
  `"complete": false` (ignoreres af calibrate/motor).
- `.gitattributes`: `v5/data/**` og `v5/manual/**` er `-text` (ingen linjeskift-konvertering),
  saa hashene holder paa tvaers af checkouts. Eksisterende snapshotfiler er normaliseret til
  LF i arbejdskopien; git-indholdet er uaendret.
- `calibrate.fit` stopper ved konvergens (7-8 Newton-skridt) i stedet for altid 300: kaeden
  `ablation2 --promote` + `finalize6` tager ~2 s i stedet for ~33 s. Verificeret bit-identisk
  paa ablation2/3/4/7/8-resultatfilerne og weights.json.

## Vedligehold 2026-09-09 (kode-review af 09-08-fixene, ingen modelaendring)

- `fetch.py` bygger nu i `data/raw/<dato>.ny` og flytter foerst paa plads ved fuld succes; et
  fejlet forsoeg gemmes som `<dato>.ukomplet` og roerer aldrig et eksisterende komplet
  dagssnapshot. Skrivning/diff ligger igen inde i per-serie-try'en; 429 og misdannede svar
  retries; reserveserierne (GDPC1/CPIAUCSL/THREEFYTP10, ingen forbrugere) nedlaegger ikke
  veto *(afloest 2026-10-15: kun P/refit-serierne i spine.SERIER nedlaegger veto)*; manglende shiller.csv/manual.json goer snapshottet ukomplet; diff-baselinen er det
  nyeste KOMPLETTE snapshot.
- `calibrate.find_snapshot` advarer hoejlydt naar det nyeste snapshot springes over, og
  `snapshot_complete` kraever nu ogsaa alle serier/filer kaeden laeser (aeldre snapshots uden
  de senere serier er ubrugelige). `motor.py --log` naegter at logfoere paa andet end det
  nyeste snapshot; motor kraever `op.vaerste_fejlalarm` (ingen 76,9%-fallback) og guard'er
  manual.json.
- `finalize6.py` bevarer en promoveret one-shot-model (fx curve_cape) i stedet for at
  revertere til curve_only, advarer i stedet for at tie naar en resultatfil/gate mangler, og
  `benchmarks.curve_only` baerer nu ogsaa `vaerste_fejlalarm`.
- `debat/debate.py` laeser/skriver `runder/runde<N>` (arkivets layout) og fejler hoejlydt
  paa tomme runder.
- Datareparation: LF-normaliseringen 09-08 aendrede shiller.csv/acm.csv-bytes i de gamle
  snapshots uden at opdatere meta.json; hashene (+ snapshot_sha256) er genberegnet fra
  filerne paa disk (markeret `hash_repareret` i meta), og weights.json er genankret.

## Vedligehold 2026-09-10 (udfyldte monitor-pladser + pengepolitik/inflation som kontekst)

- De to tomme monitor-pladser er udfyldt. `Claims-momentum` viser nu 4-ugers niveau
  (atlassets claims-zone — rettet i G2.5-erratumet: Q2-varsler 225-290k, 220k er falsifikator-niveau, 200k prompt-ekko) og 12m %-aendring paa sidste KOMPLETTE maaned (trin 4's
  definition); `Permits y/y` viser niveau + 12m %-aendring. Begge beholder `aktiv=None`
  ([-]), saa hovedbogens antaendings-kolonne er uaendret og raekkerne forbliver
  sammenlignelige paa tvaers af maaneder.
- Ny firewallet blok i Section 5: PENGEPOLITIK & INFLATION — Fed funds, realt
  kontantafkast, 3m-bill minus Fed funds (markedets Fed-prissaetning), PCE- og CPI-momentum
  3m/6m/12m annualiseret, samt 10y opdelt i term-praemie + forventet rente. INGEN
  indflydelse paa P, ikke i hovedbogen — samme firewall som atlassets svaerm-tripwires.
- Hvorfor kontekst og ikke features: rente og inflation ER allerede i modellen. Kurven
  (10y-3m) er den operationelle feature, og realrate (10y-CPI) + d_infl er to af
  fuldmodellens fem. Fuldmodellen blev testet i trin 6 og tabte til curve-only
  (+33,2% mod +34,3%). At tilfoeje dem igen ville ikke vaere en ny hypotese, men en
  gentagelse af en afgjort test. FEATURE-SOEGNINGEN ER FORTSAT LUKKET: en aendring af P
  kraever ny oekonomisk begrundelse + raads-mandat + praeregistrering, som ved v5.1/v5.2.
- Momentum-linjerne bruger KUN saesonkorrigerede serier (PCEPI, CPIAUCSL). Modellens egen
  `cpi_yoy` bruger CPIAUCNS, hvilket er korrekt for y/y (saesonen gaar ud over 12 mdr),
  men ville vaere forkert for 3m/6m.
- Nye helpers i `motor.py`, daekket af tests (42 i alt): `read_fred_raw` (noedvendig fordi
  `C.read_fred` kollapser ugeserier til maanedens sidste obs og derfor ikke kan give et
  4-ugers snit) og `ann_rate`.

**BEMAERKET, IKKE RETTET:** `ablation4_features.monthly_mean` er reelt en no-op —
`C.read_fred` har allerede kollapset ICSA til een vaerdi pr. maaned, saa der er kun eet
element pr. gruppe at tage middel af. Trin 4's `claims_mom` blev derfor testet paa
maanedens SIDSTE uge, ikke paa maanedsmidlen som modulets header angiver. Afvisningen var
-61,9pp, saa konklusionen staar uanfaegtet, men specifikation og kode er uenige. En
rettelse ville aendre et publiceret trin 4-resultat og kraever derfor eksplicit mandat.

## Dashboard

`python motor.py --json [sti]` skriver hele laesningen som JSON (default
`../dashboard.json`): P, baand, basisrate, `baand_udelukker_basisrate`/`ratio`,
dommen ordret, de fem inputs med z-scores, hele benchmark-tabellen, monitorerne med
`tilstand` (aktiv/inaktiv/kontekst) og klasse, market conditions, pengepolitik-blokken,
de staaende advarsler og hele hovedbogen med baade tekst- og talfelter.

Designbriefen ligger i `../DASHBOARD-BRIEF.md` og indeholder datakontrakten plus de
ufravigelige designregler: P aldrig uden baand og basisrate, ratio kun naar baandet
udelukker basisraten, ingen speedometre, ingen farvekodning af fare, ingen sammentaelling
af monitorer, benchmark-tabellen altid synlig, dommen gengivet ordret. Reglerne findes
for at et dashboard ikke kan komme til at love mere end modellen kan holde.

## v5.0.1 — foerste rekalibrering (RAADETS_V501.md, ratificeret 4/4 2026-09-19)

Udfoeres i konsensustekstens §8-raekkefoelge. Trin 1 (guards + tests, commit 928748f) efterlod
een ROED test med vilje: `test_nyeste_snapshot_har_frisk_rygrad` — rygraden i snapshot 2026-09-10
slutter 2023-09. Dette afsnit er trin 2 og er committet FOER trin 3-7 er koert.

### FORUDSIGELSE (§7.1) — skrevet foer koersel, falsificerbar, ikke en acceptancetest

Tilskrevet Kimi K3 (raadet, runde 3). Naar panelet forlaenges fra 2023Q2 til de nu modne origins,
forventes:

1. **Mindre absolut negativ kurvekoefficient** (raa `beta_curve = w1/s_curve` mindre i absolut vaerdi
   end i v5.0: w = [-2,1755, -1,6907], s = 1,126 -> beta = -1,502 pr. pp).
2. **Lavere walk-forward-skill paa det udvidede panel** end det trunkerede panels +34,3 % log-loss.
3. **Lavere P ved faste inputs** (september-snapshottets x: kurve +0,96) end v5.0's 18,0 %.

Astras forbehold, ordret fra konsensusteksten: *"the fixed-input probability and the historical skill
are different objects, and none of the three directions is guaranteed once the intercept,
standardisation and sample change together."* Udfaldet publiceres uanset om forudsigelsen holder.

Sekretaerens (Claudes) egne forventninger, ogsaa skrevet foer koersel:

- **Origin-audit:** forventet tilfoejet = 2023Q3, 2023Q4, 2024Q1 (vinduets slut + 18 mdr <= 2026-09),
  alle med label 0 (dyb inversion, ingen onset); forventet fjernet = ingen; omlabelede = ingen;
  n_obs 264 -> 267.
- **Legacy-replay (§1.5a):** eksakt w = [-2,1755, -1,6907], n_obs 264 (allerede verificeret i trin 1).
- **Korrektionsbro (§1.5b):** den korrigerede rygrad trunkeret ved 2023-09 giver identiske vaegte,
  fordi de to erstattede maaneder (2023-08/09) kun beroerer 2023Q3, som ligger uden for
  raekkeuniverset (teknisk label udefineret).
- **Seam-tjek (§1.4, Kimi R5):** CAPE for 2023-08/09 genberegnet fra FRED SP500-maanedsmiddel, CPIAUCNS
  og Yales egen (forloebige) indtjeningskolonne forventes at reproducere Yales forloebige vaerdier
  (30,47 / 30,81) snarere end multpl's (30,09 / 29,80); afvigelsen (-1,25 % / -3,28 %) tilskrives
  reviderede indtjeningstal og den endelige S&P-print. Tjekket maaler konsistens, ikke sandhed.
- **Gaten paa det udvidede panel (§6):** forventet at curve-only fortsat slaar fuldmodellen; uanset
  udfald flytter det ikke den operationelle model.

### ERKLAERET FEJL I KONSENSUSTEKSTEN (§3.6)

Konsensusteksten siger "expanding intercept inside the walk-forward". Det skrev sekretaeren (Claude)
i matrixen, og det er forkert om koden: `calibrate.metrics()` bruger den POOLEDE middelvaerdi af de
scorede origins som baseline, og det er den definition alle publicerede skill-tal (+34,3 % osv.)
hviler paa. At aendre gate-metrikkens definition post hoc er praecis det protokollen forbyder (Astra,
Kimi, Claude nedlagde alle veto mod det). Derfor: den publicerede definition beholdes som gate, og
en expanding-intercept-udgave printes som EKSTRA diagnostik i §4-tabellen. Ingen tal i broen
aendres af dette.

### RESULTAT (§7) — koert 2026-09-19/20, manifest 72c3371d (forrige: 6baeade4 = v5.0)

**Forudsigelsen holdt paa alle tre punkter** (ja/ja/ja):

| Trin i broen (fast input: kurve +0.96pp) | P | w (std.) | beta pr. pp | alpha | n_obs | basisrate |
|---|---|---|---|---|---|---|
| (i) legacy-rygrad (Yale t.o.m. 2023-09) | 18.0 % | [-2.1755, -1.6907] | -1.5016 | -0.0718 | 264 | 18.2 % |
| (ii) korrigerede kilder, samme origins | 18.0 % | [-2.1755, -1.6907] | -1.5016 | -0.0718 | 264 | 18.2 % |
| (iii) udvidet panel (v5.0.1) | **17.7 %** | [-2.0697, -1.4884] | **-1.2948** | -0.2915 | **267** | 18.0 % |

*"A lower or higher recalibrated probability is changed estimation, not changed economic risk."* Attributionen er raekkefoelge-afhaengig (Astra).

- **Origin-audit (§3.5):** 264 -> 267; tilfoejet 2023Q3, 2023Q4, 2024Q1 (alle label 0); fjernet ingen; omlabelet ingen; identitet OK. Praecis som forventet.
- **Legacy-replay (§1.5a):** eksakt — w [-2.1755, -1.6907], n_obs 264, wf +34.32 %. **Korrektionsbro (§1.5b):** trin (ii) = trin (i) til sidste decimal; de to erstattede maaneder roerer ikke raekkeuniverset.
- **Walk-forward publiceret to gange (§7.3):** trunkeret panel +34.32 % (195 origins); udvidet panel +27.05 % (198 origins), heraf faelles origins +34.32 % (identisk, samme traeningssaet) og tilfoejede 2023Q3 P=87 % Y=0, 2023Q4 P=92 % Y=0, 2024Q1 P=89 % Y=0. Forskellen er per konstruktion de tre tilfoejede origins: tre ~90 %-fejlalarmer koster 7.3pp.
- **Gaten (§6):** fuldmodel +23.16 % mod curve-only +27.05 %; forskel 3.9pp < MDE 4.42pp. Curve-only forbliver operationel — mekanisk, og uanset udfald kunne den ikke have flyttet sig (raadsbeslutning kraeves). De seks andre afvisninger beholder deres tal med fodnoten "panel t.o.m. 2023Q2".
- **Vaerste fejlalarm** staar: 93.8 % (2023Q2).

**Diagnostik (§4, `diagnostik.json`, motor sektion 8):**

- 4.1 Episode-tabel: 8 onset-raekker + alle negative; bidragene summerer eksakt til +27.05pp. Den negative blok efter sidste onset (2020Q2..2024Q1) bidrager -14.2pp alene — hele skill-tabet sidder i 2022-24-inversionen.
- 4.2 LOEO: 7 blokke, median +37.51 %, min +21.06 %; ['1981-08'] udefineret (kun positive origins). Sensitivitet, aldrig co-primaer.
- 4.3 Begge domsregler backtestet (198 origins x 1000 traek): baandreglen "skelnelig" 154, den parrede 166, uenige 12 (6.1 %). Live (sep-26): parret baand [-3.5, +3.7]pp, enig med baandreglen. **Ingen automatisk migration** — et skift er en separat raadsbeslutning mod praeregistrerede kriterier inkl. Type I-fejl paa syntetiske serier.
- 4.4 Historisk parret loss-bootstrap: middel +0.120, 90 %-interval [-0.042, 0.2388], P(<=0) = 0.0893.
- 4.5 Oracle-fri (censurering som af origin-datoen, modellens egen label): alle live-publicerbare 219 origins +20.37 %; ekskl. 21 *additional live-publishable origins* +27.05 % (= primaer). Max P blandt de 21: 95 %. Tolkes i tandem, citeres aldrig hver for sig. Pre-1979-onsets rekonstrueret med konventionen trough + 18 mdr.
- §3.6: expanding-intercept-baseline giver +29.21 % mod publiceret (poolet) +27.05 %. Gaten er uaendret.

**Erratum (§5):** claims_mom genkoert med korrekt maanedsmiddel paa det trunkerede panel: dLL **-72.79pp** (publiceret -61,9pp = superseded implementation result), fortegn 75 %, folds 0 % -> testet, ikke bestaaet. sahm_t og permits_yoy identiske (-1.71 / -14.53): panelet er bevist det samme. Audit af fejlklassen: kun dette ene sted aggregerede forkert. `ablation4_erratum_resultat.json`.

**Hvad der aendrede sig i driften:**

- Maanedsritualet er nu `fetch.py` -> manual.json -> `motor.py --log --json`. **Ingen maanedlig re-ankring.** Vaegte, standardisering og basisrate er frosne til naeste rekalibrering: hver september, eller ved hash-aendring i `nber_announcements.csv` (ny top/bund), eksekveret ved naeste maanedskoersel: `python finalize6.py && python diagnostik.py`.
- Hovedbogen har faaet kolonnen `kalibrering` (manifest-hash) — **kun fremadrettet**. De to historiske raekker er byte-identiske; `kalibreringer/legacy_mapping.json` kobler dem til v5.0-manifestet (6baeade4). Den foerste raekke under 72c3371d (oktober) faar automatisk en bro-note med P under begge vaegtsaet ved identiske inputs.
- Rygraden: `manual/shiller_yale_2023-09.csv` (uforanderlig) + `spine.csv` i hvert snapshot (komposit m. proveniens). Friskheds-guarden (§1.7) koerer i fetch: GS10/TB3MS/USREC nedlaegger veto, resten staar i meta. Er multpl nede, printer fuldmodel-linjen "unavailable — CAPE stale", og curve-only koerer videre. **Det er accepteret design, ikke en defekt** (Kimi R5): multpl er en enkelt, ukontraheret kilde uden noeglefrit alternativ; fuldmodellen er ikke operationel, og et permanent fravaer af dens linje maa ikke laeses som et pipeline-svigt.
- Kimis Δ-diagnostik (R5 #2): hver kalibrering baerer `delta_vs_forrige` — max|ΔP| og max|Δw| over ALLE origins i raekkeuniverset mellem to kalibreringer, ikke kun ved eet inputpunkt. v5.0 -> v5.0.1: max|ΔP| 7,8pp ved 1974Q1, middel 1,7pp, 10 % af 316 origins flytter >5pp, Δβ +0,21 pr. pp. Feltet og `trigger` (nber-datering / september / manuel) ligger uden for manifest-hashen (proveniens om aendringen, ikke kalibreringsindhold). Bro-noten i hovedbogen naevner triggeren.
- Motor haandhaever de frosne vaegte (§3): et nyere snapshot end kalibreringen er forventet og giver ingen advarsel; en aendret `nber_announcements.csv` eller en forfalden september-koersel blokerer `--log` ("REKALIBRERING PAAKRAEVET") indtil `finalize6.py && diagnostik.py` er koert — triggeren er deterministisk, ikke skoensmaessig. En genkoersel uden dataaendring genbruger manifestet (idempotent).
- CI: `.github/workflows/tests.yml` koerer suiten + legacy-replay ved hvert push.
- Nye filer: `spine.py`, `diagnostik.py`, `kalibreringer/` (manifester + index + legacy_mapping), `manual/seam_check_2023.json`, `ablation4_erratum_resultat.json`. Tests: 66.

Commit-historikken viser de fejlende tests foer reparationen (928748f -> 8165745), som §8 kraever.

## Drift 2026-09-28: daglige live-input (vaegtene uaendrede, kalibrering 72c3371d)

**Hvorfor.** GS10, TB3MS og FEDFUNDS er maanedssnit, der foerst publiceres efter maanedens udgang, saa
motorens live-input kunne vaere op til en maaned gammelt. Den 28/9-2026 viste motoren augusts 10Y (4,68 %),
mens den daglige var 5,18 % — 7bp fra 5,25-tripwiren — og Fed funds (3,63) var fra foer Feds hævning den
16/9 (3,88). I walk-forward'en er inputtet altid maaneden der LIGE sluttede; en maaned gammel live-input
var en forsinkelse, backtesten aldrig havde.

**Hvad.** (1) Den operationelle kurve maales som TRAILING kalendermaaned af de daglige serier DGS10 - DTB3
(faelles handelsdage, datoer efter samme dato forrige maaned) — `calibrate.live_kurve()`. Realrenten i
fuldmodel-linjen bruger samme 10Y. (2) Tripwire-niveauer og aktierisikopraemien bruger SENESTE daglige 10Y.
(3) Pengepolitik-blokken bruger DFF (daglig effektiv Fed funds); CP-spaendet laeses paa samme dag for begge
ben; 10Y-dekomponeringen paa term-praemiens dato. (4) P paa de publicerede maanedstal printes altid ved
siden af. Ingen ny feature, ingen ny kalibrering.

**Samme statistik — bevist.** Kalendermaanedssnittet af DGS10 reproducerer GS10 i alle 776 maaneder siden
1962 med max 0,50bp afvigelse (afrunding); DTB3 mod TB3MS ligesaa. Kurven paa faelles dage: max 0,91bp
siden 1990. Trailing-vinduet ved maanedens sidste handelsdag: median 0,41bp, max 3,36bp. Paastanden er en
permanent test (`TestLiveKurve`).

**Effekt 2026-09-28.** Kurve +0,96 -> +1,01 (vindue 25/8-24/9, 22 dage); P 17,7 -> 16,9 % [12,0-24,1]; 10Y-
tripwire 4,68 -> 5,18 %; realt kontantafkast -0,07 -> +0,18pp; 3m-bill minus Fed funds +45 -> +20bp.
Dekomponeret paa samme dato steg 10Y 28bp fra 28/8 til 18/9, heraf 20bp forventet rentesti og 8bp
term-praemie — septembers udsalg er primaert en opjustering af den ventede pengepolitik.

**Drift.** DGS10 og DTB3 er nu kritiske (fejl eller forældelse > 10 dage goer snapshottet ukomplet); DFF er
reserve (motor falder tilbage til FEDFUNDS). Snapshots foer 2026-09-28 mangler DGS10 og er dermed ubrugelige
for kaeden — som ved tidligere serieudvidelser. Foerste hovedbogsraekke paa daglig input faar noten
"input: daglig", og 10Y-tripwiren i antaendings-kolonnen reagerer nu paa det seneste daglige niveau.

**Erratum, hovedbogsraekke 2026-10-10:** bro-noten skriver `P(v? 6baeade4)` i stedet for `P(v5.0 6baeade4)` —
motor laeste versionen i manifestets model-blok i stedet for i toppen. Hashen 6baeade4 identificerer v5.0
entydigt, og ingen tal er beroert. Raekken er IKKE redigeret (historiske raekker roeres aldrig); fejlen er
rettet i koden efter logfoeringen og daekket af en test.


## Kode-review 2026-10-15 — alt rettet, intet i P aendret

Et adversarielt review af hele setuppet (`REVIEW-2026-10-15.md`, 85 verificerede fund) blev rettet i
fem batches. **Hverken vaegte, P, baand, basisrate eller historiske hovedbogsraekker er aendret.**
Legacy-replay er eksakt, og diagnostikken reproducerer de publicerede tal til sidste decimal.

**Tidskritiske fejl (ville have ramt november-laesningen):**

- **F3 CPI-hullet:** BLS udgav aldrig oktober 2025. Naar oktober-CPI 2026 udkommer, ville motor
  crashe (KeyError), og "CPI (SA) 12m" var allerede en 13-maaneders aendring. Nu bruges
  kalendernoegler: y/y er udefineret, fuldmodellen staar "unavailable — CPI-hul", og P er uaendret.
- **F2 SP500-overlap:** FRED's rullende 10-aars vindue starter midt i en maaned, og den delvise
  foerste maaned vaeltede overlap-tjekket (foerste gang ca. 9.-30. nov. 2026). Maaneden udelades nu
  (dokumenteret undtagelse, §1.2). Allerede lukkede komposit-maaneder baeres videre fra forrige
  rygrad, naar vinduet ruller forbi dem (fra 2033).
- **F24:** Et afloest `.ukomplet`-forsoeg slettes nu efter en vellykket genkoersel samme dag (det
  blokerede `--log`).
- **F15:** Annonceringstabellen hashes kanonisk, og `.gitattributes` beskytter den mod CRLF. En
  linjeskiftsaendring udloeste foer en falsk "nber-datering".
- **F4:** September-formlen skubbede rekalibreringen et aar ved enhver refit uden for september. Ny
  formel: `(aar, 9) if maaned < 9 else (aar + 1, 9)`, testet for alle 12 maaneder.
- **F13:** "fuldmodel unavailable"-stien crashede motor. Den er nu crash-fri i alle sektioner og i JSON.

**Licenser og kildeangivelse (F1, F12, F19, F20, F56):** ICE BofA HY OAS og S&P 500 (FRED: "Copyrighted:
Pre-Approval Required"), Moody's Baa og multpl-siden ordret committes ikke laengere (`.gitignore`;
hentes og hashes lokalt; meta.json beholder sha256/sidste vaerdi, og motor falder tilbage til den).
`spine.csv`'s afledte S&P-maanedssnit beholdes, fordi kalibreringen kraever dem. Se rod-README'ens
"Datakilder og vilkaar". **Ikke gjort (Rasmus' beslutning):** filerne ligger stadig i git-historikken
siden 2026-08-09; en omskrivning (filter-repo + force-push) giver alle commits nye SHA'er og svaekker
hovedbogens proveniens. Repoet har endnu ingen LICENSE.

**Seriernes roller (F18):** EEN tabel (`spine.SERIER`), som VETO/RESERVE/KRAEVEDE afledes af. Kun
GS10, TB3MS, DGS10, DTB3, USREC, A191RL1Q225SBEA og CPIAUCNS nedlaegger veto. En manglende
monitor-serie vises som `[?] utilgaengelig` og noteres i hovedbogen, og den vaelter aldrig laesningen.

**Firewallen genoprettet (F9, G2.1-G2.4, F27, F28, F47):** De tre MiroFish-tripwires (CP-spaend, 10Y,
realkredit) staar nu i et separat SCENARIE-APPENDIKS uden for antaendings-kolonnen, som grand reviewets R3
besluttede enstemmigt. LOG.md-headeren har en dateret note. Ingen af dem har vaeret aktive i raekke 1-3.
Linjerne baerer deres proveniens (1 kanal; kanalens antagne trigger, ikke et varsel). CP-spaendet bruger
atlassets definition (alle 10 seneste faelles handelsdage) og markeres stale efter 10 dage, og hver linje
viser max og antal dage over taersklen siden sidste logning. HY-linjen siger nu, at 600bp er et v4-flag,
og at 350-450bp-zonen er den eneste atlas-taerskel med 3+ kanaler.

**Mere information — kun kontekst, aldrig i P (F10, F11, F30, F32, F33, F36, F38-F41, F46, F58, F59):**

- dekomposition af maanedens kurveaendring (d10Y/d3m og hvert bens P-bidrag ved frosne vaegte,
  bear/bull) og saetningen om at et lang-ende-udsalg saenker P mekanisk (~1,6pp pr. 10bp i dag);
- P-stien ved frosne vaegte (top, maaneder siden top, fald). Sti-advarslen har faaet historiske tal:
  P var under sin top ved sidste origin foer onset i 6 af 8 onsets, med et median-fald paa 21pp og
  median 9 mdr fra top til onset. 2007Q4 havde P 16,7 % og var "ikke skelnelig" en maaned foer onset;
- manuelle inputs med datoer og friskhedsflag (CAPE > 45 dage -> fuldmodel unavailable);
- BNP-linjen paa FOERSTE print (advance) pr. kvartal, udledt af de arkiverede snapshots;
- fuldmodellens dd paa kalibreringens statistik (trailing maanedsmiddel mod 12-mdr max af
  maanedsmidler), naar SP500 findes lokalt. Monitoren viser fortsat den manuelle dagsluk;
- kurvens sammensaetning (front 2y-3m + bag 10y-2y) og near-term forward spread (DGS1/DGS2/DGS3MO);
- kredit ud over HY: EBP + GZ-spaend (Fed Board) og Baa-10Y. NBER-komiteens seks indikatorer (y/y og
  afstand fra 12m-top, uden taerskler). WTI y/y som regimekontekst. Claims som maanedsmiddel af alle
  uger (erratum §5) + fortsatte ansoegninger + vikarer. AWHMAN 6m. Forudsaetnings-tripwires med aktuel
  status.

**Protokol (F6, F7, F8, F14, F26, F45, F48-F51, F54, G1.7, G3.x, G4.x):**

- Origin-auditten var en tautologi (n_ny = n_gl + tilf - fjern gaelder altid). Nu skal hver aendring
  forklares: *modnet* (kvartalsslut + 30 mdr i (R_gl, R]), *censureret* (top annonceret i (R_gl, R]) eller
  *omlabelet* (onset annonceret i (R_gl, R]). Alt andet stopper finalize6.
- `load_announcements` fejler haardt ved en post-1979-onset uden peak-raekke. Trough+18 bruges kun foer
  1979 og aldrig paa en aaben episode. Motor krydstjekker tabellen mod USREC.
- **Live-censurering (F14):** en laesning inde i en annonceret recession faar dommen `censureret`.
- Gatens egen MDE beregnes og printes: **21,2pp** (episode-blok-bootstrap af den parrede skill-forskel).
  Beslutningsreglen bruger fortsat den ratificerede trin 3-MDE (4,42pp, laant fra frekvenstesten).
  En taerskel aendres ikke efter at resultatet er set — til raadet foer september 2027.
- diagnostik.py bruger kalibreringens refit-maaned og snapshot. finalize6/diagnostik afviser et
  snapshot, hvis rygrad ikke er refit-klar. `--log` blokeres, naar diagnostik.json ikke passer til
  vaegtene.
- calibrate.py roerer aldrig `weights.json`. Bro-noten slaar op i den kalibrering, der staar i sidste
  raekke, og `|` i noter neutraliseres. Fuldmodellens statustekst foelger gatens beslutning.
- Manifesterne baerer python/numpy-version, en hash af baandets vaegte, L_R-auditten (stoerste
  top-annonceringslag 12 mdr -> L_R = 18 = gulvet) og dateringens faktiske effekt. CI laaser numpy.
- Versionen bumpes af kaeden (naeste nye kalibrering = 5.0.2). Et genbrugt manifest beholder sin
  refit-maaned, og koerslen registreres separat (`weights.json.koersel`), saa september-kravet stadig
  opfyldes. `n_episoder` taeller fra naeste refit kun onsets med et berettiget positivt origin (G4.1).
- **Bedoemmelsesnoeglen** (`../BEDOEMMELSESNOEGLE.md`) er praeregistreret foer raekke 4: metrik, vindue,
  afgoerelse, censurering, cluster-inferens, styrketabel (80 % styrke kraever ca. 26 cyklusblokke ≈ 168
  aar), referencetal +20,4 % (ikke +27,1 %) og logvindue dag 10-20. Udfald foeres i `../UDFALD.csv`, og
  hver raekke faar en fuld record i `../hovedbog.jsonl`.

### Afvigelser fra blueprintet (erklaeret 2026-10-15)

Reviewet gik blueprintets §1-§10 igennem punkt for punkt. Det meste er implementeret. Disse
afvigelser var tavse indtil nu og erklaeres her. Ingen af dem aendrer P i dag.

| # | Blueprintet siger | Koden goer | Konsekvens / status |
|---|---|---|---|
| G1.1 | §3/§6: L2-straffen vaelges INDE i hvert traeningsvindue | Fast λ = 1 overalt (arvet fra v4/curve.py) | v5.0's modelvalg vendte allerede ved λ = 2 (legacy-panel). Ved nested λ falder curve-onlys wf-skill til 17-23 %, men curve-only vinder i alle varianter. +27,1 % maerkes "fast λ=1, ikke nested". Et nested design praeregistreres separat foer koersel |
| G1.2 | §4/§6: nested selektion; kun den sti kaldes wf-skill | +27,1 % (og +34,3 %) er en max over to modeller paa den fulde sti | Maerket "fuld-sti-valg mellem to modeller (ikke nested)" i motor og dashboard. Med al moden historik vaelger en nested selektor i dag curve-only |
| G1.3 | §2: frekvensgaten | Rollerne er byttet: den bogstavelige gate ville have gjort den maanedlige model primaer | Forelaegges raadet ved september-refit 2027 med begge udfald publiceret. Intet skiftes automatisk |
| G1.4 | §4: "ingen arvefred" for incumbents | Demotionsreglen var asymmetrisk; realrate, dd og d_infl ville vaere faldet under udfordrernes bar | "5 incumbents bestaar" laeses som "beholdt under asymmetrisk demotionsregel". Fuldmodellen er ikke operationel, og soegningen er lukket |
| G1.5 | Praeregistrering foer koersel | Gates for trin 2-4, 6 og v5.1 ligger i filer, der er committet sammen med resultatet | Kun blueprintets og RAADETS_REVIEW's gates er verificerbare udefra. Fremtidige praeregistreringer pushes i en separat commit foer koersel (som V501 §8) |
| G1.6 | §9: ALFRED-audit af alle realtidsinputs | Kun CPI og BNP; UNRATE, claims og permits er udeladt | Erklaeret i koden, nu ogsaa her. Immaterielt: de tre er afviste features, og realtids-Sahm er tjekket separat |
| F8 | Gaten maaler mod stoejgulvet | Gulvet 4,42pp er frekvenstestens MDE; gatens egen er ~21pp | Begge printes. Reglen aendres kun ved raadsbeslutning (erratum-procedure) foer sept. 2027 |
| F34 | Universstart | 1947Q2 inkl. 24 kvartaler med Shiller-LTR i stedet for 10Y; dommens basisrate (18,0 %) er fit-samplets, ikke walk-forwardens (16,2 %) | Diagnostik: P 17,7/15,0/12,6 % ved start 1947Q2/1953Q2/1960Q1. Universstarten er en protokolkonstant og saettes paa raadets dagsorden foer sept. 2027 med praeregistrering |
| F51 | §1: aarlig L_R-audit | Var ikke implementeret | Implementeret i finalize6 (manifestets `L_R_audit`). Korrektionsbroens trin (ii) er nu en test |
| F52 | §4.1-4.2: 12 onset-raekker / 12 LOEO-blokke | 8 onset-raekker og 7 LOEO-blokke | De 4 onsets 1948-1960 ligger foer foerste scorede origin (1960). 1981-blokken har kun positive origins (udefineret skill) |
| G1.8 | §1: rapportér provisoriske nuller der senere blev et; Kimi R6 | Kun et antal (7) ved L = 18 | diagnostik.json: flips L12/L18/L24 = 8/7/4 (alle pre-1979-konventionen). Kimi R6: median 32 episoder i traeningen pr. origin (min 27); skill uden nyeste episodeblok +20,5 % mod +27,1 % |

### Driftsaendringer uden raadsmandat (F29) — forelaegges til ratifikation ved september-refit 2027

| Dato / commit | Aendring | Hvorfor uden mandat | Sporbarhed |
|---|---|---|---|
| 2026-09-28 / 8cdb9f0 | Live-kurven maales paa trailing maaned af daglige DGS10 - DTB3 i stedet for seneste publicerede GS10 - TB3MS | Samme statistik, uden publiceringsforsinkelse (bevist i TestLiveKurve). Vaegtene er uaendrede, men maaleinstrumentet for P er aendret midt i hovedbogen | Raekke 3 har noten "input: daglig". Fra raekke 4 staar `P_maanedlig` (P paa maanedstal) i hver raekke |
| 2026-09-28 / 8cdb9f0 | 10Y-tripwiren laeser seneste daglige niveau | Samme begrundelse | Linjen er siden flyttet til scenarie-appendikset |
| 2026-10-15 | Svaerm-tripwires ud af antaendings-kolonnen | Retter en tavs afvigelse fra R3 (enstemmig) | LOG.md-headerens note |
| 2026-10-15 | Advance-print fra arkiverede snapshots; CP paa atlas-definitionen; fuldmodellens dd paa kalibreringsstatistik | Fejlrettelser (F32/F27/F33). Kun advance-print er i antaendings-klassen og har aldrig vaeret aktiv | Kode-review-afsnittet ovenfor |
| 2026-10-15 | Logvindue dag 10-20, `ikke logget`-raekker, live-censurering, nye kolonner | Praeregistreret i bedoemmelsesnoeglen foer raekke 4 | BEDOEMMELSESNOEGLE.md + noten `noegle <hash>` |

### FORUDSIGELSE: september-refit 2027 (F35) — skrevet 2026-10-15, et aar foer koersel

Som §7.1, falsificerbar og ikke en acceptancetest. Beregnet ved at koere den uaendrede refit-kode med
R = 2027-09 paa snapshot 2026-10-15 og **antage at NBER ikke daterer en top foer da**:

- **Origin-audit:** tilfoejet 2024Q2, 2024Q3, 2024Q4, 2025Q1 (alle modnet, alle label 0); fjernet ingen;
  omlabelet ingen; n_obs 267 -> 271.
- **Kurvekoefficienten svaekkes igen:** beta -1,295 -> **ca. -1,18** pr. pp (alpha -0,29 -> -0,43).
- **P ved faste inputs falder lidt:** P(kurve +1,11) 15,1 % -> **ca. 14,8 %**. Ved inversion falder den mere:
  P(0,0) 42,8 -> 39,3 %, P(-0,5) 58,8 -> 53,9 %. Inversionssignalet svaekkes, fordi 2023-25 var en lang
  inversion uden onset.
- **Walk-forward-skill:** +27,1 % -> **ca. +21 %** (Brier +24,1 -> ca. +16,8 %). Fuldmodellen ca. +17 %, saa
  curve-only forbliver operationel.
- Afviger tallene ved koerslen, skyldes det datarevisioner eller en NBER-datering. Begge publiceres.

Geminis forbehold fra v5.0.1-raadet gaelder ogsaa her (sammenfattet, ikke citeret): en lang
inversion uden onset fortynder inversionssignalet ved hver refit. Det er modellens kendte
regime-risiko og ikke en fejl, og det er grunden til, at forudsigelsen er skrevet nu.

### Register: vurderede, fravalgte monitorkandidater (F60)

En kandidat genaabnes kun med et nyt argument.

| Kandidat (serie) | Status | Grund | Noeglefri? |
|---|---|---|---|
| NFCI / ANFCI (Chicago Fed) | fravalgt | Kraftigt revideret (vintage-audittens lektion); konstrueret med kendskab til senere kriser | ja |
| STLFSI4 (St. Louis Fed stressindeks) | fravalgt | Samme revisionsproblem; overlapper HY OAS + EBP | ja |
| SLOOS (udlaanspraksis) | fravalgt | Kvartalsvis, kort historik, allerede afvist som feature-klasse | ja |
| BIS-kreditgab | fravalgt | Lang publiceringsforsinkelse | ja |
| VIX (VIXCLS) | fravalgt | Maaler aktievolatilitet (coincident), som allerede ses i dd/CAPE-blokken; Cboe-copyright (kildeangivelse paakraevet) | ja |
| Michigan-forbrugertillid (UMCSENT) | fravalgt | Sentiment med svag ledetid ud over kurven; copyright (kildeangivelse paakraevet) | ja |
| ISM PMI | fravalgt | Proprietaer, ikke paa FRED | nej |
| Conference Board LEI | fravalgt | Proprietaer; indeholder kurven selv | nej |
| 10y-2y-kurven | indbygget som kontekst | Vises som front/bag-opdeling af den operationelle kurve; ingen ny feature | ja |
| EBP / GZ-spaend (Fed Board) | **tilfoejet som kontekst 2026-10-15** | Kreditkanalen ud over HY OAS; lang historik (1973-) | ja |
| Baa-10Y (Moody's) | **tilfoejet som kontekst** (lokal fil) | Kredit 1986-; Moody's forbyder videregivelse, saa filen committes ikke | ja, men licensbegraenset |
| NBER's seks indikatorer | **tilfoejet som kontekst** | Komiteens egne coincident-serier; ingen taerskler | ja |
| WTI (DCOILWTICO) | **tilfoejet som kontekst** | Regime (atlassets kanal 6); USA er nettoproducent | ja |
| Fortsatte ansoegninger, vikarer | **tilfoejet i claims-linjen** | Arbejdsmarkedskanalen | ja |

### Aaben praeregistreringskandidat: EBP (F37) — IKKE i P

Feature-soegningen blev lukket uden en kreditvariabel med lang historik. Gilchrist-Zakrajseks excess
bond premium (1973-) har en oekonomisk begrundelse uafhaengig af den aktuelle laesning: kreditudbuddets
pris, renset for default-risiko, leder realoekonomien. Den er derfor noteret som en AABEN kandidat. Den
kommer kun i P via: raadsmandat; forseglet spec (niveau, lag, forventet fortegn +) committet og pushet
foer koersel; G5-aera-split; og en deklaration af, at EBP's vaerdier op til onsets er SET i dette review
(kontamineringsrisiko). Indtil da er EBP kun en kontekstlinje.

### Snapshot-arkivet og FRED's vilkaar (F20)

Snapshots af public domain-serier arkiveres i repoet af hensyn til reproducerbarheden (hver P kan
genberegnes byte for byte). FRED's vilkaar har bestemmelser om arkivering og maskinlaering, ogsaa for
offentlige serier. Anbefalet handling (Rasmus): send en kort forespoergsel til FRED
(stlsFRED@stls.frb.org) om et skriftligt OK til et ikke-kommercielt, offentligt forskningsarkiv. Hvis
svaret er nej, hentes de operationelle serier fra primaerkilden (Fed Boards H.15). Tallene er de samme,
men pipelinen og hasherne aendres, saa det kraever en protokolbeslutning.
