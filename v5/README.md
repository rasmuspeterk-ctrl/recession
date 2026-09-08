# MOTOR v5 — trin 1: reproducerbarheds-refaktor

Bygget efter raadets enstemmige blueprint ([../RAADETS_KONSENSUS.md](../RAADETS_KONSENSUS.md)).
Trin 1 aendrer INGEN modellering: samme L2-logit, samme tekniske label, samme
walk-forward som v4 — men reproducerbart og uden haandkopierede konstanter.

## Filerne

| Fil | Rolle |
|---|---|
| `fetch.py` | Henter 20 FRED-serier noeglefrit (parallelt), skriver byte-eksakt hashet snapshot i `data/raw/<dato>/`, printer diff mod forrige snapshot (ny obs / aendret vaerdi / revideret historik) |
| `calibrate.py` | Genopbygger v4's kalibrering fra snapshottet, skriver `weights.json` (vaegte + datahash + protokolversion). `--check` koerer determinisme-test. Indbygget acceptancetest mod v4's konstanter |
| `motor.py` | Maanedlig aflaesning: laeser weights.json + snapshot + manual.json. Naegter snapshots >40 dage (`--allow-stale` for at overstyre). CAPE-percentil beregnes af snapshottets egen historik — ingen 2026-knuder |
| `nber_announcements.csv` | Committet tabel over NBERs annonceringsdatoer (til trin 2's mekaniske label-regel) |
| `manual/` | Manuelle inputs: `manual.json` (spx_vs_hi, cape, margin_yoy) og `shiller.csv` (se nedenfor) |

## Maanedligt ritual (~5 min, som v4)

```
python fetch.py        # hent + diff-tjek med oejnene
# opdater manual/manual.json (3 tal) og evt. manual/shiller.csv
python ablation2_nber.py --promote && python finalize6.py   # genanker vaegte paa dagens snapshot (~2 s, deterministisk)
python motor.py --log  # aflaesning + prospektiv logfoering i ../LOG.md
```
Hovedbogen (`../LOG.md`) er den eneste aegte out-of-sample-eksamen: een raekke
pr. maaned, skrevet FOER udfaldet kendes; historiske raekker roeres aldrig.

Genkalibrering (sjaeldnere, efter dataopdateringer): `python calibrate.py --check`

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

Rekalibreringskaede (sjaelden): `fetch.py` → `ablation2_nber.py --promote` →
`finalize6.py`. Maanedligt ritual uaendret: `fetch.py` + manual.json + `motor.py`.

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
  veto; manglende shiller.csv/manual.json goer snapshottet ukomplet; diff-baselinen er det
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
