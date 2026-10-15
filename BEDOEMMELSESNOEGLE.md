# BEDØMMELSESNØGLE — hvordan hovedbogen scores

**Præregistreret 2026-10-15, før hovedbogsrække 4** (kode-review 2026-10-15, G3.1–G3.6). Nøglen
fastlægger, hvordan rækkerne i [LOG.md](LOG.md) en dag skal bedømmes. Den er skrevet, før nogen
af rækkerne kan afgøres: række 1 (2026-08-12) har tidligst sit udfald ved udgangen af 2028.

Nøglens hash (sha256 af filen med LF-linjeskift, første 8 tegn) skrives automatisk i noten
`noegle <hash>` i den første række, der logges under den. En ændring af nøglen giver en ny hash og
en ny note. Den gælder kun fremadrettet og ændrer aldrig, hvordan allerede loggede rækker scores,
undtagen hvor reglen udtrykkeligt siger det. Ændringer kræver en begrundet commit, der pushes,
før den række, ændringen gælder for, logges.

## 1. Hvad der scores

**(a) Metrik.** Den primære metrik er log-loss mod rækkens *loggede* basisrate (kolonnen
`basisrate`, altså kalibreringens basisrate på logningstidspunktet), ikke mod en ex post-poolet
rate. Skill = 1 − LL(model) / LL(basisrate) over de scorede rækker. Brier-skill mod samme
basisrate er sekundær. Tallene beregnes på `P` som logget, med 1 decimal.

**(b) Vindue pr. række.** Origin = måneden før logningsmåneden. Vinduet er logningsmåneden og de
følgende 11 måneder (12 måneder i alt). Reglen afledes af rækkens egne data, så række 1–3 kan
scores uden redigering:

| række | vindue |
|---|---|
| 2026-08-12 | 2026-08 .. 2027-07 |
| 2026-09-09 | 2026-09 .. 2027-08 |
| 2026-10-10 | 2026-10 .. 2027-09 |

Fra række 4 står vinduet i kolonnen `vindue`.

**(c) Afgørelse.** Y = 1, når NBER annoncerer en top, hvis onset (første USREC = 1-måned, dvs.
toppen + 1) ligger i vinduet. Datoen er annonceringsdatoen. Y = 0, når vinduets sidste måned + L_R
(18 måneder, embargogulvet; se L_R-auditten i finalize6) er passeret uden en sådan annoncering.
Indtil da er rækken *uafgjort*, og en uafgjort række tæller aldrig som et provisorisk nul.

**(d) Realtidscensurering.** En række, der er logget inde i en *annonceret* recession (dom
`censureret`), scores ikke, fordi onset-sandsynligheden ikke er defineret. En række, der er logget
inde i en recession, som *endnu ikke* var annonceret, scores som logget og får typisk Y = 0
(onset ligger før vinduet). Det er netop forskellen mellem den publicerede walk-forward (orakel-
censurering) og live-virkeligheden. Sammenligningstallet er derfor diagnostik 4.5's
oracle-fri variant (se pkt. 3), og de to tolkes i tandem.

**(e) Alle rækker scores som logget.** Manifest (`kalibrering`) og måleinstrument (`input`:
månedstal før 2026-09-28, daglig trailing måned derefter) er strata. De rapporteres separat, men
bruges aldrig til at udelukke rækker. `ikke logget`-rækker er manglende data: de imputeres ikke,
og antallet rapporteres ved siden af resultatet.

**(f) Udfald føres i [UDFALD.csv](UDFALD.csv)** (append-only: rækkens logget-dato, Y,
afgørelsesdato og kilde, fx nber.org-annonceringen). Hovedbogsrækker redigeres aldrig, heller ikke
note-feltet.

## 2. Inferens og hvornår en dom må formuleres

**(g) Inferens på cyklusblokke.** Månedsrækker inden for samme konjunkturcyklus er stærkt
afhængige (overlappende 12-måneders vinduer, samme kurveregime). Inferens sker derfor kun med
cluster-robust t på cyklusblokke (bund til bund). Følgende er **forbudt**:

- iid-tests på overlappende månedsrækker. Kode-reviewet viste, at de forkaster i ca. 78 % af
  5-årshovedbøger, også når en tredjedel af dem ikke indeholder nogen onset.
- 4.4's blok-bootstrap ved færre end 5 blokke. Den er degenereret og "forkaster" i ca. 82 %.

**(h) Ingen dom før minimum.** Der må ikke formuleres bestået/ikke bestået, ingen samlet score og
ingen hovedbogs-dom (heller ikke på dashboardet), før mindst **3 komplette cyklusblokke** er
scoret. Selv da er styrken kun ca. 0,21 (tabellen nedenfor). En dom ved 3 blokke er en beskrivelse,
ikke en test.

**Styrketabel** (diagnostik.json → `styrke`; parametrisk skaleret fra den historiske walk-forward:
middel log-loss-gevinst 0,1197 pr. origin, cluster-SE 0,081 ved 9 historiske blokke; ensidet 5 %;
6,4 år pr. blok i gennemsnit):

| komplette cyklusblokke | ca. år | styrke |
|---|---|---|
| 1 | 6 | 0,12 |
| 3 | 19 | 0,21 |
| 5 | 32 | 0,29 |
| 10 | 64 | 0,46 |
| 20 | 129 | 0,71 |
| 26 | 168 | **0,80** |
| 40 | 258 | 0,93 |

Konsekvensen er, at hovedbogen ikke kan skelne en model med den historiske skill fra basisraten
inden for en menneskelig tidshorisont. Den kan fange grove fejl, fx systematisk høj P uden
onsets, og den beskytter mod look-ahead. Den kan ikke "bevise" modellen. Selv i det mest gunstige
scenarie, hvor en fejlalarm som 2022–24 aldrig gentager sig, kræves ca. 20 år (ca. 3 onsets).

## 3. Referencetallet hovedbogen skal sammenlignes med

Den publicerede walk-forward-skill (+27,1 %, v5.0.1) er **ikke** det tal, hovedbogen kan forventes
at vise. Den censurerer med den endelige kronologi (et orakel) og måler mod den poolede, ex post
realiserede basisrate. Den kvartalsvise analog til nøglens regler er diagnostik 4.5,
"alle live-publicerbare origins": **+20,4 %** (219 origins, realtidscensurering). Kode-reviewets
genberegning på månedsrækker mod en fast logget basisrate gav ca. +25 % med realtidscensurering
og ca. +30 % med orakelcensurering. Hovedbogens resultat sammenlignes med +20,4 % og printes ved
siden af det, aldrig ved siden af +27,1 % alene.

## 4. Logning

**(i) Én række pr. måned, logget i logvinduet dag 10–20.** Første kørsel i vinduet efter
`fetch.py` er den, der logges. Motor afviser `--log` uden for vinduet. Undtagelse kun med
`--log-uden-for-vindue "<begrundelse>"`, og begrundelsen skrives i rækkens note.

**(j) Mellemlæsninger logges aldrig.** En måned uden række i vinduet skrives ved næste logning som
en eksplicit `ikke logget`-række. Rækker kan ikke springes over i stilhed, og en "god" måned kan
ikke vælges.

**(k) --log blokeres**, når en rekalibrering er påkrævet (§3.2), når annonceringstabellen er ude
af synk med USREC, når diagnostik.json ikke passer til kalibreringen i drift, eller når nyeste
snapshot er ukomplet. Blokeringen udskyder logningen inden for vinduet, aldrig ud over det. Kan
den ikke løses i vinduet, bliver måneden en `ikke logget`-række.

**(l) Fuld record.** Hver række får en JSON-record i [hovedbog.jsonl](hovedbog.jsonl): snapshot-
hash, manifest, live-inputvindue, P, bånd, basisrate, P på månedstal, alle monitor- og
scenarielinjer, noter og nøglens hash. Så kan rækken scores og genberegnes uden at læse koden.
