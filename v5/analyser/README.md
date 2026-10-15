# Analyser til raadets dagsorden 2027 (koert 2026-10-15)

Syv deterministiske analyser af de punkter, kode-reviewet 2026-10-15 sendte videre til raadet foer
september-refitten 2027. **Ingen af dem aendrer noget i driften**: vaegte, manifester, snapshots og
hovedbog er uroerte, og hvert script skriver kun sin egen `*_resultat.json`. Alle reproducerer de
publicerede ankre eksakt (manifest 72c3371d: w [-2.0697, -1.4884], n_obs 267; curve-only +27,05 % /
Brier +24,15 % paa 198 origins; F5 +23,16 %), og hver er genberegnet af en uafhaengig verifikator.
Tallene herunder er efter verifikatorernes rettelser; hvor scriptets egen sammenfatning afviger, gaelder
tallene her.

Koersel (fra `v5/`): `python analyser/<navn>.py`. Koeretid 4 s til 5,5 min (nested_robusthed).
Kun `created_utc` varierer mellem koersler.

| Script | Review-fund | Hovedresultat |
|---|---|---|
| `nested_robusthed.py` | G1.1/G1.2 (opfoelgning paa ablation9, eksplorativ) | Nested curve-only +17,96..+23,35 % over 11 indre-CV-designs; alle ikke-degenererede selektorer taber 9-10 pp, naesten alt i 2022-24 |
| `frekvensgate.py` | G1.3 | Bogstavelig §2: maanedlig primaer i 6/6 celler; kodens tyndede laesning fejler i 4/6 (v5.0.1 curve-only med 0,02 pp) |
| `universstart.py` | F34 | P ved live-kurve 14,9 / 12,4 / 10,4 % ved start 1947Q2 / 1953Q2 / 1960Q1; dom-ordet uaendret |
| `demotion.py` | G1.4 | Symmetrisk udfordrer-regel: kun kurven overlever; drop-symmetri: ingen demoteres |
| `hovedbog_reference.py` | G3.5 / noeglens §3 | Maanedlig hovedbogs-replay: realtid +24,41 %, uden vintage-antagelse +28,95 %, orakel +33,28 % |
| `styrke_simulation.py` | G3.2 | 80 % styrke kraever ca. 150 kalenderaars hovedbog (ca. 18 aar uden fejlalarm-blokken) |
| `nber_indholdstrigger.py` | G4.1 | Indholdstrigger: 18 netto ekstra refits paa 49 aar, max abs(dP) 1,05 pp ved faktisk kurve |

## Rettelser fra verifikationen (gaelder over scripternes egne resuméer)

**frekvensgate.** Laesningerne er uenige i **4 af 6** celler (ikke 5: legacy curve-only er to celler, der begge
bestaar). Ikke alle forskelle ligger under stoejgulvet: legacy curve-only fuld-minus-kvartal er **+3,01 pp**
mod MDE 2,54 (CI10-90 [+1,58, +4,67]); v5.0.1 curve-only +2,19 pp (MDE 2,99) har et CI, der udelukker 0.

**universstart.** Gate-forskellen ved 1953Q2 er -31,00 pp (ikke -31,01) og paa de 158 faelles origins -3,14
(ikke -3,15). Faellesmaengden (158 origins fra 1980Q3) daekker kun 5 af de 8 scorede onsets (1970, 1973 og
1980 falder ud). Den illustrative fuldmodel-P med hver starts egen mu er 0,2-0,3 pp lavere ved 1953Q2/1960Q1.

**demotion.** Udfaldet "kun kurven overlever" gaelder incumbent-som-udfordrer-laesningen af symmetri. Under
den status quo-venlige laesning (samme +2/+2-taerskel anvendt paa drop-effekten) demoteres ingen.

**hovedbog_reference.** Primaertallet +24,41 % hviler paa en uverificeret antagelse om FREDs USREC-vintage
(aaben episode indtil bunden er annonceret). Dag-praecis annoncering med endelig bund giver **+28,95 %**
(Brier +26,89, n 644); hele faldet til +24,41 skyldes 83 aabne-episode-maaneder, heriblandt optakten til
1981-onsettet. Trin "+ september-refits" er mest et startpunkt-skift (+1,1 pp); selve refit-effekten er
ca. +0,5 pp. Noeglens regel (a) er generoes: den loggede basisrate er i snit 22,8 % mod realiseret 15,3 %.
Cluster-t citeres som 1,37 / 1,85 over alle 9 blokke, ikke 7,92 / 8,79 over de 7 komplette (som udelader
den eneste negative blok).

**styrke_simulation.** T er **kalenderaar** hovedbog inkl. censurerede maaneder: "80 % ved 150 aar" svarer til
ca. 131 aars scorede raekker (plus ca. 2,5 aars modning). Variant B er 7 komplette cyklusser plus en afskaaret
aabningsblok 1967-12..1970-11. P(>= 3 hele cyklusblokke) ved 20 aar er 0,25 (scriptets 0,36 medregner
fejlalarm-blokken). Cluster-t's hoeje "falsk-positiv-rate" ved 50-200 aar i variant A er en egenskab ved det
centrerede blandings-H0 (betinget paa fejlalarm-blokken er FP 0,5-8 %). Like-for-like-krydstjekket giver
112-183 aar (samme stoerrelsesorden).

**nested_robusthed.** 1-SE-lambda-reglen er den UPARREDE variant og degenererer til grid-loftet alene fordi
episodeblokkenes basisrater spaender 0-67 %. Den parrede variant giver curve-only +16,53 % og selektorerne
+9,18 (argmin) / +8,17 (MDE) i stedet for +14,55 / +12,98; dermed vaelger **alle** regler curve-only i dag,
og selektionstabet er -9 til -10 pp under alle ikke-degenererede selektorer. F5's indre fordel kommer 72-76 %
fra 1948-blokken (forhold mellem summer 75,7 %; scriptets 79,4 % er et middel af forhold). 7 af 11 designs er
varianter af referencedesignet; de to reelt andre familier ligger over det (19,8-22,2). MDE 4,42 er en
heuristisk taerskel for indre CV, ikke et signifikansniveau. F5 nested p i 2022Q4-2024Q1 er 0,93-0,99.

**nber_indholdstrigger.** 24 indholdsudloeste refits, hvoraf 6 falder sammen med september: **netto 18 ekstra**
(B 79 mod A 61 refits). Den isolerede dateringseffekt +6,04 pp ved 1981-09 er ved n_obs 106 (ikke ca. 101).
Bagudsimuleringen forudsaetter, at bund-raekken tilfoejes i annonceringsmaaneden (det er dét, der "redder"
1981 og 2001). Fremskrivningens panel er ufuldstaendigt fra 2029-03 (+0,91 pp med 2 positive er en
undergraense).

## Status

Analyserne var raadets faktagrundlag ([debat/raad2027](../../debat/raad2027/)). Beslutningerne er ratificeret
7/7 den 2026-10-15 og staar i [RAADETS_2027.md](../../RAADETS_2027.md), med sha256-pins af de syv resultatfiler
(beregnet af de committede LF-bytes). Intet traeder i kraft foer september-refitten 2027. Afsnittet ovenfor
er E5-supplementet, som RAADETS_2027 §7.2 kraever publiceret.
