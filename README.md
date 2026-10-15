# MOTOR v5.0.1 — sandsynlighed for amerikansk recessionsstart

[![tests](https://github.com/rasmuspeterk-ctrl/recession/actions/workflows/tests.yml/badge.svg)](https://github.com/rasmuspeterk-ctrl/recession/actions/workflows/tests.yml)

*A US recession-onset probability model: one feature (the 10y–3m yield curve), an
L2-logit on the NBER-onset label, purged expanding-origin walk-forward validation, and a
prospective ledger where every reading is logged before the outcome is known. Free data
only. Every failed candidate is published next to the one that survived. Documentation
is in Danish.*

Modellen estimerer P(NBER-dateret recession begynder inden for fire kvartaler). Den
operationelle model er en curve-only-logit, låst af rådet (RAADETS_V501 §6); fuldmodellen med fem features
er kun benchmark. **Walk-forward-skill (log-loss-forbedring over basisraten, RAADETS_2027 §1.2): oracle-fri,
fast λ = 1 +20,4 % (219 origins; det tal, hovedbogen bedømmes mod); orakel-censureret, fast λ = 1 +27,1 %;
nested λ (orakel-censureret) +18,3 % — og 80 % styrke kræver størrelsesordenen 150 kalenderårs hovedbog,
mens naive tests forkaster en sand nulhypotese 36–53 % af gangene ved 5–20 år.** Hovedbogen er derfor et
ærlighedsinstrument, ikke en test.

λ = 1 er arvet fra v4 og ikke valgt nested; det er en erklæret afvigelse fra blueprintet. En nested
modelselektion ville have valgt fuldmodellen og scoret +8,5 % (se
[v5/README.md](v5/README.md#afvigelser-fra-blueprintet-erklaeret-2026-10-15)). Syv feature-kandidater er
testet, publiceret og afvist; søgningen er lukket.

**Seneste logførte læsning (2026-10-10, v5.0.1, daglig kurve):** P = 15,1 % [10,4–21,6 %] mod basisrate
18,0 % — ikke skelnelig fra basisraten. Se [LOG.md](LOG.md).

**Rekalibrering v5.0.1 (2026-09-19):** kalibreringsrygraden var frosset ved 2023 (Yales Shiller-fil), så
tre modne kvartaler manglede i fittet. Rådet ratificerede reparationen 4/4; samme inputs giver nu 17,7 %,
orakel-censureret walk-forward-skill +27,1 % (fra +34,3 %) fordi de tre tilføjede kvartaler er 2023–24-inversionens
fejlalarmer. *"A lower or higher recalibrated probability is changed estimation, not changed economic
risk."* Detaljer: [v5/README.md](v5/README.md#v501--foerste-rekalibrering-raadets_v501md-ratificeret-44-2026-09-19).

**Fra 2026-09-28 måles kurven på daglige data** (trailing måned af DGS10 − DTB3, uden op til en måneds
forsinkelse). Det er et erklæret instrumentskifte, ikke målemæssigt identisk med GS10 − TB3MS; rådet
ratificerede det ex post (RAADETS_2027 §10.1). P på de publicerede månedstal står ved siden af i hver række.

**Rådet 2027 (ratificeret 7/7 den 2026-10-15):** syv analyser og fem debatrunder med seks af de nyeste
flagskibsmodeller afgjorde de ti spørgsmål, kode-reviewet sendte til "rådet før september 2027":
- λ = 1 og kvartalsfittet bevares — og protokollen siger ligeud, at blueprintets frekvensgate *som skrevet*
  bestod, og at rådet afviste at anvende den;
- ingen modelselektor; 1947Q2 bevares;
- én NBER-indholdstrigger pr. recession;
- bedømmelsesnøglen ændres ikke;
- EBP's historiske test lukkes.

Intet ændrer P før september-refitten 2027. Se [RAADETS_2027.md](RAADETS_2027.md) og
[v5/analyser/](v5/analyser/README.md).

**Kode-review 2026-10-15:** 85 verificerede fund er rettet, uden at P eller historiske rækker er
ændret. Ændringerne omfatter seks tidskritiske fejl før november-læsningen, licensbegrænsede filer
ud af repoet, sværm-tripwires ud af hovedbogens antændings-kolonne (rådets R3), en præregistreret
[bedømmelsesnøgle](BEDOEMMELSESNOEGLE.md) og en forudsigelse af september-refitten 2027. Se
[v5/README.md](v5/README.md#kode-review-2026-10-15--alt-rettet-intet-i-p-aendret).

## Hvor er hvad

| Fil | Indhold |
|---|---|
| [v5/README.md](v5/README.md) | Ritualer, filoversigt, afvigelser fra blueprintet, byggelog |
| [v5/](v5/) | Koden: fetch → (finalize6 → diagnostik ved rekalibrering) → motor (calibrate.py er trin-1-reproduktionen og overskriver ikke driftsvægtene). 156 tests. |
| [LOG.md](LOG.md) | Hovedbogen — én række pr. måned, logført før udfaldet kendes. Redigeres aldrig. |
| [BEDOEMMELSESNOEGLE.md](BEDOEMMELSESNOEGLE.md) | Hvordan hovedbogen scores — præregistreret før række 4, med styrketabel |
| [UDFALD.csv](UDFALD.csv) / [hovedbog.jsonl](hovedbog.jsonl) | Append-only udfald pr. række / fuld record pr. række |
| [RAADETS_KONSENSUS.md](RAADETS_KONSENSUS.md) | Blueprintet, ratificeret 7/7 af et råd af sprogmodeller efter seks debatrunder |
| [RAADETS_REVIEW.md](RAADETS_REVIEW.md) | Grand review med 18 modeller |
| [RAADETS_V501.md](RAADETS_V501.md) | Rådets konsensus om v5.0.1 — den første rekalibrering (4/4, 19. sept. 2026) |
| [RAADETS_2027.md](RAADETS_2027.md) | Rådets konsensus om dagsordenen til september-refitten 2027 (7/7, 15. okt. 2026) |
| [REVIEW-2026-10-15.md](REVIEW-2026-10-15.md) | Kode-reviewet af hele setuppet (85 fund) |
| [TRIGGER-ATLAS.md](TRIGGER-ATLAS.md) | Sværm-simulerede recessionskanaler og tripwires — narrativ kontekst, ikke input til P |
| [DASHBOARD-BRIEF.md](DASHBOARD-BRIEF.md) | Designregler for et dashboard der ikke kan oversælge |
| [debat/](debat/) | Transkripter af rådsdebatterne (blueprint, v5.0.1 og 2027; grand reviewets runde A+B blev ikke arkiveret — se RAADETS_REVIEW.md) |
| [mirofish-sim/](mirofish-sim/) | Sværm-simulationernes rådata og resuméer |
| [v4/](v4/) | Forgængeren |

## Principper

- Kun gratis data (FRED, Fed Board, Shiller, FINRA, multpl). Hashede snapshots. Ingen API-nøgler i ritualet.
- Kun walk-forward-valideret får tal. Kompleksitet skal købe skill.
- Sproget om resultatet genereres mekanisk og kan ikke blive skarpere end tallene.
- Fejlslagne forsøg publiceres ved siden af det der virkede.

## Månedsritual (logdag: første hverdag fra den 10., + 3 dage)

```bash
cd v5
# tjek nber.org/research/business-cycle-dating — ny top/bund? tilføj række i nber_announcements.csv og commit
python fetch.py                        # snapshot (FRED + Fed Board EBP), hashet
# opdatér manual/manual.json: S&P vs 12-mdr-høj, CAPE, marginlån y/y — med deres datoer
python fetch.py                        # igen, så snapshottet bærer de nye manuelle tal
python motor.py --log --json           # læsning, hovedbogsrække (kun i logvinduet), dashboard.json
python -m unittest test_v5             # 154 tests
```

Vægtene er frosne mellem rekalibreringer (hver september, eller når NBER daterer en ny top/bund):
`python finalize6.py && python diagnostik.py` (bump først `VERSION` i finalize6.py, §3.3). Se [RAADETS_V501.md](RAADETS_V501.md).

Kræver Python 3 og numpy. Intet andet.

## Datakilder og vilkår

"Gratis at hente" er ikke det samme som "frit at videregive". Repoet arkiverer snapshots af hensyn til
reproducerbarheden. Kilder med licensbegrænsninger hentes og hashes lokalt, men **committes ikke**
(`.gitignore`). Deres sha256 og sidste værdi står i hvert snapshots `meta.json`, så alle, der henter de
samme bytes, kan efterprøve hashen.

| Kilde | Serier | Vilkår | I repoet |
|---|---|---|---|
| Board of Governors of the Federal Reserve System (H.15, G.17, CP; Kim-Wright-termpræmien THREEFYTP10; Gilchrist-Zakrajsek EBP) | GS10, TB3MS, DGS10, DTB3, DGS1, DGS2, DGS3MO, DFF, FEDFUNDS, INDPRO, RIFSPPFAAD90NB, THREEFYTP10, EBP | Public domain; kildeangivelse ønskes | ja |
| U.S. Bureau of Labor Statistics | CPIAUCNS, CPIAUCSL, UNRATE, PAYEMS, CE16OV, AWHMAN, TEMPHELPS | Public domain; kildeangivelse ønskes | ja |
| U.S. Bureau of Economic Analysis | A191RL1Q225SBEA, GDPC1, PCEPI, PCEC96, W875RX1 | Public domain; kildeangivelse ønskes | ja |
| U.S. Census Bureau; U.S. Employment and Training Administration; U.S. Energy Information Administration | PERMIT; ICSA, CCSA; DCOILWTICO | Public domain; kildeangivelse ønskes | ja |
| NBER via Federal Reserve Bank of St. Louis | USREC | Copyright, kildeangivelse påkrævet | ja |
| Federal Reserve Bank of St. Louis | CMRMTSPL | Copyright, kildeangivelse påkrævet | ja |
| Freddie Mac | MORTGAGE30US | "Freddie Mac, 30-Year Fixed Rate Mortgage Average in the United States" — copyright Freddie Mac; kildeangivelse påkrævet (FRED: Citation Required) | ja |
| Claudia Sahm; Marcelle Chauvet og Jeremy Piger (via FRED) | SAHMREALTIME; RECPROUSM156N | Public domain; kildeangivelse ønskes | ja |
| **ICE Data Indices, LLC** | BAMLH0A0HYM2 (HY OAS) | "Copyrighted: Pre-Approval Required" — reproduktion forbudt uden skriftlig tilladelse | **nej (lokal)** |
| **S&P Dow Jones Indices LLC** | SP500 | "Copyrighted: Pre-Approval Required" | **nej (lokal)**; kun de afledte månedssnit i `spine.csv` (kalibreringen kræver dem) |
| **Moody's** | BAA10Y | "May not be copied or otherwise reproduced" | **nej (lokal)** |
| Robert J. Shiller (Yale) | Rygraden t.o.m. 2023-07 (`manual/shiller_yale_2023-09.csv`) | Data courtesy of Robert J. Shiller | ja |
| multpl.com | Månedlig Shiller-CAPE efter 2023-07 | Siden kopieres ikke; kun afledte månedstal i `spine.csv` | **siden: nej (lokal)** |
| NY Fed (Adrian, Crump og Moench 2013) | `manual/acm.csv` (ACM-termpræmien, kun trin 4-testen) | © Federal Reserve Bank of New York; videregivet under NY Fed's Terms of Use med kildeangivelse ("Source: Federal Reserve Bank of New York, ACM Treasury term premia") | ja |
| FINRA | Marginlån y/y i `manual.json` (et afledt tal) | FINRA Margin Statistics | ja |

Kildeangivelse for FRED-serier: *Federal Reserve Bank of St. Louis, [serienavn] [ID], retrieved from FRED,
Federal Reserve Bank of St. Louis; https://fred.stlouisfed.org/series/[ID]*. Licensmærkerne blev hentet
fra FRED's seriesider 2026-10-15 og står pr. serie i `v5/spine.py` (`SERIER`) og i hvert snapshots
`meta.json`.

Licensbegrænsede filer fra før 2026-10-15 findes stadig i git-historikken. Anbefalingen (kode-review F1, udført
2026-10-15) er IKKE at omskrive historikken nu: det giver alle commits nye SHA'er og svækker hovedbogens
proveniens (de pushede `ledger-*`-tags peger på de oprindelige commits). Historikken renses kun, hvis en
rettighedshaver anmoder om det — fremgangsmåden står klar i v5/README.md ("Historik og licensbegrænsede filer").

Koden er MIT-licenseret, egen tekst CC BY 4.0; tredjepartsdata og modelgenereret tekst er undtaget — se
[LICENSE](LICENSE) og [NOTICE.md](NOTICE.md).

Modellen er ikke et handelssignal og ikke investeringsrådgivning.
