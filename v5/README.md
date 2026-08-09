# MOTOR v5 — trin 1: reproducerbarheds-refaktor

Bygget efter raadets enstemmige blueprint ([../RAADETS_KONSENSUS.md](../RAADETS_KONSENSUS.md)).
Trin 1 aendrer INGEN modellering: samme L2-logit, samme tekniske label, samme
walk-forward som v4 — men reproducerbart og uden haandkopierede konstanter.

## Filerne

| Fil | Rolle |
|---|---|
| `fetch.py` | Henter 14 FRED-serier noeglefrit, skriver hashet snapshot i `data/raw/<dato>/`, printer diff mod forrige snapshot |
| `calibrate.py` | Genopbygger v4's kalibrering fra snapshottet, skriver `weights.json` (vaegte + datahash + protokolversion). `--check` koerer determinisme-test. Indbygget acceptancetest mod v4's konstanter |
| `motor.py` | Maanedlig aflaesning: laeser weights.json + snapshot + manual.json. Naegter snapshots >40 dage (`--allow-stale` for at overstyre). CAPE-percentil beregnes af snapshottets egen historik — ingen 2026-knuder |
| `nber_announcements.csv` | Committet tabel over NBERs annonceringsdatoer (til trin 2's mekaniske label-regel) |
| `manual/` | Manuelle inputs: `manual.json` (spx_vs_hi, cape, margin_yoy) og `shiller.csv` (se nedenfor) |

## Maanedligt ritual (~5 min, som v4)

```
python fetch.py        # hent + diff-tjek med oejnene
# opdater manual/manual.json (3 tal) og evt. manual/shiller.csv
python motor.py        # aflaesning
```

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
- [ ] 3. Frekvens-ablation (maanedlig vs kvartal, numerisk gate −1pp)
- [ ] 4. Feature-genforsvar + laaste udfordrere (Sahm, claims, permits) + ACM-testen
- [ ] 5. ALFRED vintage-audit
- [ ] 6. Output/dom-ombygning (baand, sprogregler, benchmark-tabel)
