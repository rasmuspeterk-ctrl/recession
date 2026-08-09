# RÅDETS GRAND REVIEW — MOTOR v5.0, komplet systemaudit

**9. august 2026 · 18 modeller, 2 runder (uafhængig review + krydsforhør) · 17/18 svarede i begge runder (Gemma 31B's gratis-pulje overbelastet; hendes 26B-søster deltog) · Pris: $0,73**

Udvidet råd: de oprindelige 7 (GPT-5.6 Sol, Kimi K3, Gemini Pro, Grok 4.5, Nemotron Ultra 550B, Gemma, GPT-OSS) + **DeepSeek V4 Pro** + 10 nye gratis (Nemotron Super 120B/Omni 30B/Nano 30B/12B/9B, Gemma 26B, Ling 3.0, Laguna S/XS, North Mini). Fuldt transkript: [debat/runder/reviewA+B](debat).

---

## R1 — Korrekthed: ingen fatale fejl; én navnefejl fundet og rettet; tre lødige forbedringspunkter

**Rettet med det samme:**
- **"Probit"-navnefejlen (Gemini):** den operationelle model blev *kaldt* "curve-only-probit" i output og dokumentation, men koden er L2-**logit** hele vejen (verificeret: begge modeller i release-gaten fittes af samme `C.fit` — sammenligningen var logit vs logit, ingen genkørsel nødvendig). Alle labels omdøbt til "curve-only-logit (NY Fed-stil-benchmark)".

**Afvist efter verifikation:**
- **DeepSeeks look-ahead-mistanke** (runde A): "brugte træningen ægte realtidslabels?" — bekræftet i koden: `yR` bygges udelukkende af annonceringer ≤ refit-datoen (ablation2_nber.py), og de 7 rapporterede provisoriske nuller beviser at gaten faktisk bandt. Sol afviste selv påstanden i krydsforhøret.
- **North Minis censurerings-indvending:** endelig kronologi bruges kun til *scoring*-eksklusion (definerer det betingede spørgsmål "onset givet ikke-i-recession"), aldrig i fit. Gemini: "not a look-ahead leak; it correctly defines the conditional probability."

**Åbne forbedringspunkter (logget, mekaniske — ingen nye modeller):**
1. **Pooled-origin-inflation (Kimi → Gemini/DeepSeek):** +34,3% pooler 4-8 korrelerede origins pr. episode; episode-dekomponering af skill-tallet bør publiceres, og LOEO bør overvejes som co-primær metrik ved næste rekalibrering.
2. **Orakel-scoring (Sol):** scoringen betinger på endelig kronologi; en supplerende score uden denne eksklusion (alle live-udgivelige origins) bør trykkes ved siden af.
3. **Sprogregel-forfining (Sol):** "skelnelig fra basisraten" bør på sigt afgøres af parret forskels-usikkerhed mod basisrate-prognosen, ikke af om punktbåndet krydser 18,2%.

## R2 — Informationsdækning: rådet er delt 6-5; kun ÉN kandidat overlever — AWHMAN

Optælling af slutlisterne: **6 stemmer "ingen kandidat består gaten"** (Gemini, DeepSeek, Gemma 26, GPT-OSS, Laguna S, Ling) · **5 stemmer "ét skud på AWHMAN"** (Sol, Grok, Kimi, Laguna XS, Nemotron 9B) · småmodel-spredning på olie/M2/CFNAI — **strukturelt tilbagevist** af sværvægterne (olie: USA er nettoproducent post-2008, transmissionen er flippet og 1973/79/90 ville være "reddende episoder"; NFCI/CFNAI: reviderede/coincidente; M2: velocity-brud; SLOOS/JOLTS: for korte — claims-lektionen). NB: Nemotron 30B *opdigtede* "pilot-test-tal" for olie — hallucination, nedvægtet til nul.

**AWHMAN (gennemsnitlige ugentlige arbejdstimer, industri, FRED 1939+):**
- For: dækker alle 12 onsets, klassisk LEI-komponent, ægte ledetid (timer skæres før hoveder), lav korrelation med kurven, kan testes på fuld sample — alt det claims_mom døde af, har den ikke
- Imod (Geminis vægtigste): sekulær nedtrend kræver detrending-valg = frihedsgrader; DeepSeek forventer at selv den ikke når 2pp uafhængigt af kurven
- Sols forseglede spec hvis skuddet tages: fast 6-måneders annualiseret ændring, publikationslagget, forventet fortegn negativt

**Beslutningen er din** (protokollen kræver dit go før enhver præregistreret kørsel): tag det ene AWHMAN-skud, eller erklær informationssøgningen lukket. Alle øvrige kandidater: monitorer højst (NFCI, SLOOS, BIS-kreditgab) eller regimekontekst (olie, fiskal, udland). Konsensus-sætningen på tværs af begge lejre: *"ved n≈12 er MDE'en — ikke feature-loftet — den bindende begrænsning; mere data er ikke mere uafhængig information."*

## R3 — Kommunikation: overskriften består; to mekaniske tilføjelser implementeret

Enstemmigt: **"20,1%, ikke skelnelig fra basisraten" er den korrekte operationelle overskrift.** Implementeret i motor.py pr. rådets forslag:
1. **Model-divergens-linjen** (Gemini/DeepSeek): operationel vs fuldmodel-delta (10,1pp) trykkes eksplicit med de drivende z-værdier (CAPE, drawdown) og sætningen "statistisk uadskillelige på skill — den simple vandt på regel". Divergensen er selv informativ — uden at bryde firewallen.
2. **Sti-advarslen** (enstemmig R4-konklusion) i den permanente advarselsblok.
MiroFish forbliver uden for modeloutputtet (scenarie-appendiks) — enstemmigt.

## R4 — Næste recession: enstemmig blandt sværvægterne — systemet er mest sandsynligt FOR LAVT

Alle fire betalte + DeepSeek konvergerede uafhængigt på samme mekanisme: **modellen læser kurvens NIVEAU og har hukommelsestab om STIEN.** +0,87pp efter en netop afsluttet 20-måneders dyb inversion behandles identisk med +0,87pp uden forhistorie — men historisk (1990, 2001, 2007) er onsets netop sket i re-steepening-fasen, ofte drevet af kreditbrud eller Fed-panik. Dertil: balance-sheet-drevne recessioner uden frisk inversion (2008-typen; nutidens rekordgearing + negativ risikopræmie) er strukturelt usynlige for en kurve-alene-model. Geminis formulering blev rådets: *"It is reading the trigger being pulled as the gun being put away."* Kimi tilføjede den levende modelrisiko: 2022-24-inversionen uden recession fortynder kurve-koefficienten i realtid ved hver refit.

Advarslen står nu permanent i motor-outputtet. Bemærk symmetrien: den validerede model siger "intet usædvanligt"; de firewallede monitorer og sværmen peger op; rådet siger at hvis systemet tager fejl i 2026-27, er det mest sandsynligt i den retning — **men ingen af delene er en valideret sandsynlighed, og det er hele pointen med firewallen.**

---

*Proces: runde A uafhængig (17 svar), runde B krydsforhør med navngivne angreb (17 svar). Sekretær: Claude Fable 5 — verifikationer mod kildekoden er sekretærens, markeret som sådan. Samlet API-forbrug hele projektet (design-debat + review): ~$4,3.*
