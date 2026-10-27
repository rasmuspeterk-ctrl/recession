# TRIGGER-ATLAS — sværmens 7 recessionskanaler

**10. august 2026 · 7 MiroFish-simulationer (6 styrede kanaler + 1 fri kontrol) · ~~de-forankret seed (rå data, ingen modeltal)~~ seed uden MOTOR's P, men med v4-flagtilstande, 600bp-trigger og flagtællinger [E3] · ~~\~340 agentsvar~~ 294 svar (49 personaer × 3 spørgsmål × 2 platforme) fra 6 af 7 kanaler [E4] via miljø-interviews · qwen3.7-flash, samlet kostpris få kroner**

> **STATUS (tilføjet 2026-10-15, F41):** Kolonnerne "Nu" og "Status" i tabellen nedenfor er **historiske pr. 2026-08-10** og opdateres ikke. Aktuelle værdier og status for alle atlas-linjer står i motor-outputtet og i `dashboard.json` (`scenarie`, `forudsaetninger`, `monitors`). Dokumentet har siden 2026-10-15 et proveniens-erratum (nedenfor), der går forud for tabellen og kanalteksterne.

> **NY KØRSEL 2026-10-27:** Sværmen er kørt igen med et neutralt faktagrundlag (oktober-tal, ingen flag eller tærskler) og tal-frie styringstekster. Ingen af tærsklerne nedenfor (10Y 5,25 %, realkredit 7,8 %, CP 75bp, HY 350-450bp) blev genfundet. Agenterne brugte i stedet dagens niveauer som "tærskler". Tærsklerne er derfor uændrede og stadig uvaliderede. Se [mirofish-sim/atlas_2026-10/RESULTAT.md](mirofish-sim/atlas_2026-10/RESULTAT.md).

> **VAREDEKLARATION (firewall):** Alt i dette dokument er narrativ scenarie-analyse fra en agent-sværm — IKKE sandsynligheder, IKKE valideret, IKKE input til MOTOR's P. Atlassets funktion er at gøre monitorerne skarpere: hvilke observerbare serier ville flippe FØRST i hvert scenarie, og ved hvilke tærskler. MOTOR's validerede læsning står uanfægtet; den aktuelle læsning står i hovedbogen ([LOG.md](LOG.md)), ikke her. *[Rettet 2026-10-15, F41: sætningen citerede tidligere læsningen fra 10/8 — "MOTOR v5.0 … P(NBER-onset 4 kvt) = 20,1% [14,4-29,2%], ikke skelnelig fra basisraten" — samme tal som hovedbogens første række (2026-08-12).]*

## Erratum 2026-10-15 (kode-review: proveniens)

Kode-reviewet 2026-10-15 (fund G2.1-G2.6, F22, F41) talte atlassets rådata igennem. Teksten fra 10/8 står urørt nedenfor. Hvor den er rettet, er den overstreget eller markeret [E1]-[E7]. Rettelserne rører hverken P, vægte eller tærskler.

**Reproducerbarhed.** Tabellen fra 10/8 blev kondenseret i hånden. `svaerm_atlas.py` dumper kun interviewsvarene, og `atlas_state.json`/`atlas_raw/` blev aldrig committet. Optællingen i dette erratum kan genskabes med `python mirofish-sim/atlas/optaelling.py` fra repo-roden. Scriptet bruger kun standardbiblioteket og læser rådata i `mirofish-sim/atlas/`. Output står i [`mirofish-sim/atlas/optaelling_output.txt`](mirofish-sim/atlas/optaelling_output.txt). Scriptet tæller *nævnelser* og printer udsnittene. Klassifikationen nedenfor (eget agentsvar / seed-ekko / prompt-ekko) er en læsning af svarene, og den kan efterprøves på udsnittene.

### E1 — "3+ uafhængige kanaler" holder kun for HY OAS-zonen (G2.1)

Tællereglen er, at en tærskel kun tæller for en kanal, når en agent selv sætter den som varseltærskel. Det sker typisk i Q2 ("EARLIEST OBSERVABLE warning … threshold"). Tal, der blot gentager seed eller styringsprompt, tæller ikke.

| Tripwire (tabellen 10/8) | Kanaler med tærsklen | Spørgsmål | Status | Konklusion |
|---|---|---|---|---|
| HY OAS 350-450bp | **5**: kontrol, aktie, fiskal, eksogent (Q2) + kredit (kun Q3) | Q2 i 4 kanaler | eget agentsvar. Står hverken i seed eller prompt (seedet: 271bp nu, "recession warning trigger is 600bp"), og 0 af 294 svar nævner 600bp | **eneste tærskel med 3+ kanaler** |
| CP-spænd >75bp i 2+ uger (CP−T-bill) | specifikationen: **1** agent (aktie). 75bp i alt: **2** kanaler (aktie CP−T-bill; kontrol CP−AAA-obligationer, et andet spænd) | Q2 | eget agentsvar, 1-2 kanaler | funding-spænd holder som *begreb*: CP-tærskler i Q2 i 3 kanaler, men på 35-150bp og mod fire forskellige referencer (T-bill, AAA, EFFR, SOFR). Tærsklen holder ikke |
| Claims >200-220k | 200k: kun arbejdsmarked. 225-290k: fire andre kanaler. 220k: mest Q3 | Q2 / Q3 | 200k = prompt-ekko ("claims trend up from 199k"); 225-290k = egne svar; 220k = falsifikator-niveau | se E5 |
| 10Y >5,25 % | **1** (fiskal) | Q1: 6 svar (5 personaer), Q3: 2, **Q2: 0** | kanalens egen påtvungne trigger: promptens antagelse, kvantificeret i Q1 | ikke et varsel (E2) |
| Realkredit >7,8 % | **1** (fiskal) | Q1: 6 svar, **Q2: 0** | transmission i kanalens antagne scenarie | ikke et varsel (E2) |
| Marginlån >40-50 % | Q2: 4 kanaler (kontrol, kredit, aktie, eksogent; 9 svar) | Q2 | seed-forankret: 6 af 9 svar nævner seedets 51/51,5 % i samme svar, og aktie-prompten indeholder selv "+51.5% y/y". Kun kredit og eksogent har svar med +50 % uden seedværdien. 40 % kommer fra én agent (kontrol), der i samme svar skriver "已攀升至 51%" | tærsklen er seedværdien rundet ned; ikke uafhængig |
| Permits <1,40M + 3 mdr y/y neg. | **2** (kontrol, aktie; én agent hver) | Q2 | eget svar, men 1,40M ligger lige over seedets 1,374M. Ingen af de to svar citerer seedværdien, så forankringen er en fortolkning | 1-2 kanaler |
| Realt kontantafkast <0 | **1** (kontrol; 2 personaer i Q2) | Q1/Q2 | seed-ekko: seedet erklærede selv tilstanden ("debasement" flag active, −0,04pp) | **v4-flag**, ikke sværm-tripwire (E3) |

Kanal 7 (inflation_fed) gav 0 interviews (3 × HTTP 400). Dens ReportAgent-rapport indeholder ingen af de syv tærskler.

Reviewets første optælling sagde, at ingen agent satte en tærskel for realt kontantafkast, og at 50 % for margin altid stod i samme sætning som seedets 51 %. Reviewets egen verifikation rettede begge dele. To kontrol-agenter skriver "跌破0%" / "下穿0%", og tre svar sætter +50 % uden seedværdien. Tabellen bruger den rettede optælling.

**Kanalerne er heller ikke uafhængige.** Alle syv kørsler bruger samme seed, samme LLM, samme FAELLES-suffiks, der beder om "data series + threshold", og samme tre spørgsmål (`svaerm_atlas.py:10, :15-18, :44-48`). Personaerne genereres pr. kørsel, men ud fra seedets samme aktørliste. Uden en kontrolkørsel med en anden LLM kan selv HY-enigheden ikke skelnes fra modellens generiske forudindtagethed.

### E2 — 10Y/realkredit er fiskal-kanalens påtvungne trigger, og den robuste HY-zone var kun en note (G2.2, G2.4)

Fiskal-promptens præmis er *"ASSUME the trigger is fiscal: deficit fears push the 10-year term premium sharply higher … mortgage rates spike"*. I Q1 (trigger-kæden) satte agenterne tal på den antagne trigger: "10Y bryder 5,25 %" og "realkreditrenten springer til 7,8 %". I Q2 (tidligste varsel) nævner 0 af kanalens 10 svar 10Y eller realkredit. De peger på HY OAS (350, 400-450bp) eller gentager seedværdier (HY 271bp, ERP −2,22, CAPE 42). Tærsklen er dermed cirkulær: styringsprompt, så Q1's beskrivelse af scenariet, så tripwire. Den har én kanal som kilde. Kanalteksten nedenfor ("plus 10Y/TP-kombinationen" som tidligste signal) understøttes ikke af Q2.

Implementeringen 10/8 var omvendt af proveniensen. Den eneste flerkanals-tærskel, HY 350-450bp (5 kanaler), blev kun en tekstnote på HY-linjen, som flagede ved 600bp: v4's flag og seedets "warning trigger", som ingen agent nævner. CP, 10Y og realkredit (1-2 kanaler) blev derimod egne linjer i antændings-klassen.

**Ledetider.** "Leder onset med 3-4 kvt" (tabellen) og "3-4 kvartaler … matcher MOTOR's 4-kvartals-vindue pænt" (læsevejledningen) er én agents tal (aktie). HY-agenternes egne ledetider spænder fra **ca. 3 måneder til 4 kvartaler**: 3-5 mdr (fiskal), 6-9 mdr (fiskal, eksogent), 1-2 kvt (kredit), 3-4 kvt (aktie). Atlassets egne kanalafsnit siger 2-4 kvt (kanal 3) og ~7 mdr (kanal 6).

### E3 — Seedet var ikke "de-forankret" (G2.3)

`seed_v2_neutral.md` adskiller sig fra den forankrede første kørsels seed (`mirofish-sim/seed.md`) ved præcis to slettede linjer: MOTOR's P og kildelinjen "model readings from MOTOR v5". Resten står der stadig:

- v4's debaseringsflag som tilstand: *"debasement" flag active* (:15)
- v4's HY-flag: *recession warning trigger is 600bp* (:24)
- v4's samlede flagtællinger: *3 of 3 "repricing" / 0 of 4 recession / 1 of 1 debasement* (:25). Samlede flagtællinger står på blueprintets kill-liste (RAADETS_KONSENSUS.md:120).
- v4's ramme *"low spark, high fuel"* (:4)

Styringsprompterne indlejrer desuden seedtal: "from 271bp", "+51.5% y/y", "from 199k", "CPI pushes past 4%" og "already-negative real cash yields".

Ekkoet kan måles. Af 98 Q2-svar gentager 27 svar CAPE 42, 24 margin 51,5/51 %, 15 HY 271bp, 8 claims 199k og 5 permits 1,374M. Ingen svar gentager 600bp. Det har tre følger:

- **"Realt kontantafkast < 0" omklassificeres til v4-flag.** Den er ordret v4's debaseringsflag (fed funds − PCE < 0, `v4/MOTOR.py:124`), og agenterne gentager kun seedets tilstand.
- Margin-tærsklen (50 %) og permits-tærsklen (1,40M) ligger ved seedets egne værdier, afrundet.
- De tre "🔶 udløst" i tabellen var derfor sande per konstruktion samme dag. For realt kontantafkast er det klart, fordi seedet erklærede flaget aktivt. For margin og permits er det sandsynligt. Kondensatets "bogstaveligt v4's 'lav gnist, højt brændstof'" er seedets egen overskrift, altså ekko og ikke konvergens.

Afgrænsning: de implementerede sværm-linjer (HY-zonen, CP, 10Y, realkredit) er *ikke* seed-ekko. Seedet nævner hverken CP-spænd, realkreditrente eller 10Y-niveau, og zonen ligger mellem seedets 271 og 600bp.

### E4 — Antal svar (G2.6)

"~340 agentsvar" er **294 svar = 49 personaer × 3 spørgsmål × 2 platforme**, fra 6 af 7 kanaler. Kanal 7 bidrog kun via ReportAgent-rapporten. Pr. kanal [Q1, Q2, Q3]:

| Kanal | Svar | Personaer |
|---|---|---|
| kontrol | 22, 22, 22 | 11 |
| inflation/Fed | 0, 0, 0 | 0 |
| kredit | 24, 24, 24 | 12 |
| aktie | 14, 14, 14 | 7 |
| arbejdsmarked | 12, 12, 12 | 6 |
| fiskal | 10, 10, 10 | 5 |
| eksogent | 16, 16, 16 | 8 |

Reddit- og twitter-svaret fra samme persona er forskellige tekster (0 identiske par), men det er samme persona. Der er altså 147 par af persona og spørgsmål.

### E5 — Claims-zonen (G2.5)

~~stabilt >200-220k~~ → **Q2-varsler 225-290k i fire kanaler; 220k er falsifikator-niveau; 200k er prompt-ekko.**

- **225-290k:** Q2-varslerne uden for arbejdsmarked er kontrol 250/255k, kredit 225/240/250k, aktie 250k og eksogent 270/290k.
- **200k:** kommer kun fra arbejdsmarkeds-kanalen. Dens prompt siger "claims trend up from 199k", og agenterne svarer "199,000 to 200,000".
- **220k:** står mest i Q3 som falsifikator ("stabilt under 220k" = stien er brudt). Det var også den forankrede første kørsels alarmtærskel (`mirofish-sim/DANSK_RESUME.md:20`).
- **Nuance:** enkelte Q3-scenarier i kontrol bruger 215-225k som udløser (">215k for 2+ months").

Et claims-niveau omkring 200k er altså ikke "inde i sværmens zone". Samme formulering i `v5/README.md` (vedligeholdelseslog 2026-09-10, "atlassets 200-220k-zone") skal læses med denne rettelse.

### E6 — Term-præmien (F22)

Ved implementeringen 10/8 læste 10Y-linjen NY Fed's **ACM**-term-præmie fra `acm.csv` (månedlig). Tallet "TP +0,84" i tabellen og i kanal 5 er ACM for 2026-07. Opdelingen "10y = term-præmie + forventet" (fra 2026-09-10) brugte i stedet **Kim-Wright**-modellens term-præmie (Kim & Wright 2005, Federal Reserve Board; FRED `THREEFYTP10`) uden at navngive modellen. Fra 2026-09-28 viste 10Y-linjen samme Kim-Wright-serie under navnet "ACM TP". Det er to forskellige modeller med mærkbart forskellige niveauer.

Fra 2026-10-15 mærker motoren serien "KW TP (Kim-Wright, Fed Board)". En eventuel ACM-fallback vises særskilt som "ACM TP (NY Fed, månedlig)". Den afviste ACM-substitutionstest (trin 4) brugte den ægte ACM-serie og er ikke berørt.

### E7 — Status-kolonnerne (F41)

"Nu" og "Status" er øjebliksbilledet pr. 2026-08-10, og "AKTIV"/"udløst" gælder kun den dag. Aktuel status står i motor-outputtet og `dashboard.json`. Tallene gentages ikke her, så noten ikke forældes igen.

### Hvad ændrede sig i MOTOR 2026-10-15

1. **Scenarie-appendiks.** De tre sværm-tripwires (CP-spænd, 10Y, realkredit) er flyttet ud af monitorernes antændings-klasse til et særskilt SCENARIE-APPENDIKS i motor-outputtet (`scenarie` i `dashboard.json`). De skrives ikke længere i hovedbogens antændings-kolonne. Det følger rådets R3: *"MiroFish forbliver uden for modeloutputtet (scenarie-appendiks) — enstemmigt"* ([RAADETS_REVIEW.md](RAADETS_REVIEW.md), R3).
   - Klasse-teksterne bærer proveniensen, fx "1 kanal (fiskal); kanalens ANTAGNE trigger, ikke Q2-varsel" og for CP "1-2 kanaler".
   - Etiketten "boligkanalen" er fjernet.
   - Eksisterende hovedbogsrækker er urørte; alle tre havde "ingen".
2. **CP-linjen** bruger nu atlassets definition: >75bp på **alle 10 seneste fælles handelsdage** (CP minus T-bill), i stedet for én dags niveau.
3. **HY-linjen** mærker 600bp som v4-flag/seed-tærskel. Ligger HY i 350-450bp-zonen, vises noten "I SVAERM-ZONEN 350-450bp", og klasse-teksten siger, at zonen er den eneste atlas-tærskel med 3+ kanaler (5). Der er ikke indført en ny antændingslinje ved 350bp. Det ville være post hoc og bryde rækkernes sammenlignelighed.
4. **Forudsætnings-tripwires** vises med aktuel status under market conditions (`forudsaetninger` i `dashboard.json`), med proveniens og uden indflydelse på P. Det gælder margin >40 %, permits <1,40M + 3 mdr y/y negativ og realt kontantafkast <0 (v4-flag).
5. **Kanal 5-note** (`advarsler.lang_ende`): en stigning i den lange ende sænker P mekanisk (ca. 1,6pp pr. 10bp ved nuværende kurve), mens atlassets kanal 5 læser samme bevægelse som risiko. Dommen er uændret.
6. **Term-præmien** er mærket Kim-Wright (E6).

---

## Hovedresultatet: ~~de robuste tripwires (nævnt på tværs af 3+ uafhængige kanaler)~~ sværmens tripwires — kun HY OAS-zonen (350-450bp) opfylder 3+ kanaler [E1]

| Tripwire | Sværm-tærskel | Nu (2026-08-10) | Status (2026-08-10) [E7] | Overvåges |
|---|---|---|---|---|
| **HY OAS** | aktiveringszone **350-450bp** ~~(leder onset med 3-4 kvt)~~ (ledetider ca. 3 mdr-4 kvt [E2]) · 5 kanaler [E1] | 270bp | rolig | ✓ motor (+ svaerm-zone-note) |
| **CP-spænd 3m** (CP−T-bill) | **>75bp i 2+ uger** — funding-stress FØR kreditspænd · tærsklen: 1-2 kanaler; begrebet: 3 [E1] | 12bp | rolig | ✓ NY monitor-linje → scenarie-appendiks fra 2026-10-15 |
| **Claims 4-ugers** | ~~stabilt **>200-220k**~~ Q2-varsler 225-290k i fire kanaler; 220k er falsifikator-niveau; 200k er prompt-ekko [E5] → Sahm mod 0,50 | ~199k / −0,03 | rolig | ✓ motor |
| **10Y-rente + term-præmie** | **10Y > 5,25%** m. TP-genopretning; realkredit >7,8% · 1 kanal (fiskal), kanalens påtvungne trigger, ikke et varsel [E2] | 4,60% / TP +0,84 (ACM [E6]) / 6,69% | rolig | ✓ NYE monitor-linjer → scenarie-appendiks fra 2026-10-15 |
| **Marginlån y/y** | **>40-50%** = 95. percentil, "sentiment-overophedning" · seed-forankret [E1, E3] | **+51,5% — AKTIV** | 🔶 udløst (per konstruktion [E3]) | ✓ market conditions |
| **Permits** | **<1,40M** + 3 mdr y/y-negativ · 2 kanaler [E1] | **1,374M — under linjen** | 🔶 udløst (per konstruktion [E3]) | ✓ snapshot |
| **Realt kontantafkast** | **<0** → opsparing drænes, forbrugskanal åbnes · v4's debaseringsflag, seed-ekko [E3] | **−0,04pp — AKTIV** | 🔶 udløst (seedets egen tilstand [E3]) | ✓ market conditions |

**Atlassets kondensat:** alle tre AKTIVE tripwires er *forudsætninger* (brændstof); alle *antændings*-signaler (funding, kredit, arbejdsmarked, renteniveau) er rolige. Sværmens samlede billede er bogstaveligt v4's "lav gnist, højt brændstof" — men nu med konkrete tærskler for hvornår gnisten er observérbar. *[E3/E7: "AKTIVE" gjaldt 10/8 og var sandt per konstruktion (seedets egne værdier og v4-flag); "lav gnist, højt brændstof" er seedets egen overskrift, ikke et sværmfund.]*

## Kanalerne

### 1. Fri kontrol (ingen påtvunget trigger)
Sværmen valgte SELV repricing-kanalen: værdiansættelses-/likviditetsinversion + funding-friktion → margin-spiral → formueeffekt. Samme valg som gårsdagens uafhængige kørsel — sværmens modalscenarie er konsistent. Tidligste indikator (agenterne uenige, informativt): CAPE/ERP-ekstremet selv (6-9 kvartalers ledetid), realt kontantafkast < 0, marginlån >40% y/y, permits <1,40M. **Kontrolkørslen rummede også atlassets bedste modstemme** (retail-agenten): "Fed-put + passive flows + gamma-feedback har hedget CAPE-42-bekymringerne væk; de tre bremse-variable prises til nær-nul sandsynlighed" — boblen-fortsætter-scenariet, med præcis de mekanismer der ville holde antændings-signalerne rolige længe.

### 2. Aktie-repricing (styret)
Kæde: CAPE 42/negativ ERP + margin +51,5% → funding-friktion (CP-spænd, GCF-basis, haircuts) → algoritmisk synkron nedgearing → omvendt formueeffekt + capex-frys. Tidligst observerbar: **CP-spænd >75bp i 2+ uger** og **HY OAS gennem 350bp** (3-4 kvartalers ledetid). Falsifikator: Fed-likviditetsværktøjer (PDCF-stil) før spændene løber; arbejdsmarked holder ≤4,0%.

### 3. Kredit/refinansiering (styret)
Kæde: 2027-forfaldsmuren × høj realrente → HY-udstedelsesvindue fryser → privat kredit/CRE-tab → SLOOS-stramning → capex/ansættelsesstop. Tidligst: **HY OAS >300bp + claims op 4 uger i træk** (kombineret signal). Basel III-slutversion som accelerator. Falsifikator: kerne-PCE <2,4% to måneder i træk → forebyggende lempelse; Treasury/Fed-forlængelse af refinansieringsvinduer. Tidslinje: 2-4 kvartaler fra OAS-brud.

### 4. Arbejdsmarkeds-knæk (styret, endogent)
Kæde: skjulte fyringer → claims trend op fra 199k → **Sahm gennem 0,50** → forbrugsspiral ("de-leverage → mindre forbrug → færre ansatte"). Sværmens vigtige detalje: claims-signalet kommer **6-8 uger FØR** Sahm formelt trigger — claims-momentum er den reelle tidlige linje, Sahm er bekræftelsen. Falsifikator: produktivitetsdrevet omstrukturering (fyringer uden efterspørgselsfald), deltagelsesrate-rebound.

### 5. Fiskal/term-præmie (styret)
Kæde: udbudsdrevet lang-ende-selloff → **10Y >5,25% + TP-genopretning** → realkredit ~7,8% → boligstop + duration-repricing af aktier → FCI-stramning uden Fed-handling. Tidligst: HY OAS 350-450 (igen) ~~plus 10Y/TP-kombinationen~~ *[E2: kanalens Q2-svar nævner 0 gange 10Y eller realkredit; 10Y >5,25 % og realkredit 7,8 % er kanalens påtvungne trigger, kvantificeret i Q1]*; realkreditniveauet som forbruger-transmissionen. Falsifikator: Treasury omlægger udstedelse mod korte papirer; QT-stop. Bemærk: nutidens TP er +0,84 *[ACM, 2026-07; E6]* — genopretning er allerede halvvejs fra 2021-bunden.

### 6. Eksogent chok (styret: olie +60%)
Kæde: geopolitisk forsyningsbrud → omkostningsinflation (PCE mod ~3,7%+) → Fed fastlåst (stagflationsdilemma) → realindkomst-klemme + refinansieringsstress samtidigt. Tidligst: IG OAS-udvidelse og **AAA CP−SOFR-præmie** (funding igen!), dernæst HY 450bp-zonen. Interessant: selv i chok-kanalen udpeger sværmen *funding-markedet* som første synlige sted — chokket ses i rørene før det ses i BNP. Tidslinje: ~7 mdr fra kreditsignal til realøkonomisk brud.

### 7. Inflation/Fed-genstramning (styret)
*(Interviews fejlede to gange — runneren lukkede miljøet ved afslutning; indhold via fuld ReportAgent-rapport i stedet, gemt som `mirofish-sim/atlas/inflation_fed_rapport.md`.)*
Kæde: CPI gennem 4% → Fed tvunget til at stoppe lempelser/genoptage stramning → **kurven re-inverterer** → kreditspænd vider ud H2 2026 → margin- og bolig-refinansieringsstress → arbejdsmarkedsrevner (claims op, dernæst Sahm >0,50) bekræfter → onset inden ~aug 2027. Tidslinje ~12 måneder. Tidligst observerbar: **selve kurveformen** — dette er den eneste kanal hvor MOTOR's egen operationelle feature er første tripwire; re-inversion ville mekanisk løfte P. Dernæst: claims-trend før Sahm, realkøbekraft-erosion, permits. Falsifikatorer (rapportens egne, bemærkelsesværdigt ædruelige): re-steepening efter fuldført inversionscyklus kan betyde at signalet fejler (2023-fejlalarmen citeret!); repricing ≠ recession (1987/2022); virksomheder der skærer omkostninger uden fyringer; opsparingsbuffer. Rapporten gengav endda seedets kernesætning om spændingen mellem robust realøkonomi og ekstremt prissat marked som "den centrale usikkerhed".

## Hvad atlasset ændrede i MOTOR (implementeret)

Tre nye **firewallede monitor-linjer** (mærket "svaerm-tripwire", ingen indflydelse på P): CP-spænd 3m (>75bp), 10Y-niveau + ~~ACM-term-præmie~~ term-præmie (>5,25%) *[E6: ved implementeringen NY Fed's ACM fra `acm.csv`; fra 2026-09-28 viste linjen Kim-Wright (FRED THREEFYTP10, Federal Reserve Board) under navnet "ACM TP"; fra 2026-10-15 mærket "KW TP"]*, realkredit 30Y (>7,8%) — plus svaerm-zonen 350-450bp noteret på HY OAS-linjen. Nye FRED-serier i snapshottet: RIFSPPFAAD90NB, DTB3, MORTGAGE30US. *[Fra 2026-10-15 står de tre linjer i motorens scenarie-appendiks, uden for hovedbogens antændings-kolonne; se "Hvad ændrede sig i MOTOR 2026-10-15" i erratummet.]*

**Bevidst IKKE tilføjet:** BIS-kreditgab (lang publikationslag), NFCI (kraftigt revideret — vintage-audittens lektion), SLOOS (kvartalsvis, kort historik — allerede afvist som feature-klasse). Sværmens CAPE/ERP/margin-tærskler er allerede i market conditions-blokken.

## Kreditkanalen ud over HY OAS (tilføjet 2026-10-15, kode-review F36/F37)

Sværmen pegede på kredit (HY OAS-zonen, kanal 3), men MOTOR så kun kreditkanalen gennem ICE's HY OAS — en
serie med kun ~3 års rullende historik på FRED. Fra 2026-10-15 viser motoren som **kontekst** også
Gilchrist-Zakrajseks **excess bond premium** og GZ-spændet (Fed Board, månedlig 1973-) og **Baa minus 10Y**
(Moody's, 1986-). EBP er noteret som **åben præregistreringskandidat** (v5/README.md): kreditudbuddets pris,
renset for default-risiko, har en økonomisk begrundelse uafhængig af den aktuelle læsning. Den kommer kun i P
via rådsmandat, forseglet spec (niveau, lag, forventet fortegn +) pushet før kørsel, G5-æra-split og en
deklaration af, at EBP's værdier op til onsets er set i reviewet. Indtil da: kontekstlinje, ingen tærskel.

## Læsevejledning

Atlasset besvarer "hvad skal jeg kigge efter, og hvornår begynder et scenarie at ligne virkelighed" — ikke "hvad sker der". Sværmens enighed på tværs af kanaler om funding-spænd og HY OAS-zonen er atlassets stærkeste resultat *[E1: for HY-zonen holder det (5 kanaler); funding-spænd holder som begreb, ikke som 75bp-tærskel]*; dens tidslinjer ~~(3-4 kvartaler fra finansiel aktivering til onset) matcher i øvrigt MOTOR's 4-kvartals-vindue pænt~~ *[E2: spænder fra ca. 3 måneder til 4 kvartaler; 3-4 kvartaler var én agents tal]*. Og modstemmen fra kontrolkørslen fortjener at blive husket hver gang panelet er helt grønt: rolige antændings-signaler er også præcis hvad man ville se, hvis Fed-puttet virker og boblen bare fortsætter.
