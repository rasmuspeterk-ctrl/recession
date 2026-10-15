# MOTOR v5 — dashboard-brief

Fast skabelon til den månedlige læsning. Kopiér alt under stregen ind i det
designværktøj du bruger, og vedhæft månedens data (se Datakontrakt).

Opdateres kun når `motor.py`'s output-struktur ændres. Konteksten og reglerne indeholder
bevidst ingen tal fra den aktuelle måned: de står i `dashboard.json`. Sidst synkroniseret
med `motor.py --json` 2026-10-15 (kode-review F17, F42, F53, G3.3).

---

## KONTEKST — læs først, reglerne følger af den

Du skal designe et månedligt dashboard for MOTOR v5 (versionen står i `version`),
en model der estimerer sandsynligheden for at en amerikansk recession (NBER-dateret)
*begynder* inden for de næste fire kvartaler.

Det afgørende ved denne model: **den er ærlig om at den næsten ikke kan noget.**
Den er en logistisk regression på én eneste variabel — rentekurven (10-årig minus
3-måneders). Den er kalibreret på et par hundrede kvartaler med kun omkring et dusin
recessionsstarter (se `n_obs` og `n_episoder` i dashboard.json). Dens værste
fejlalarm i historisk test var en meget høj sandsynlighed for en recession der aldrig
kom (se `advarsler.vaerste_fejlalarm` i dashboard.json). Dens læsning ligger typisk
tæt på basisraten, og dommen lyder ofte "ikke skelnelig fra basisraten" (se `p`,
`basisrate` og `dom` i dashboard.json) — altså: den ved reelt ikke mere end at tælle
hvor ofte recessioner sker.

Modellen er bygget efter en protokol hvor alle fejlslagne forsøg står trykt ved
siden af det der virkede, og hvor sproget om resultatet genereres mekanisk, så
det aldrig kan blive skarpere end tallene tillader.

**Dashboardet skal forstærke den ærlighed, ikke pakke den ind.** Et almindeligt
finans-dashboard — stort tal, speedometer, rød advarselsfarve, trendpil — ville
gøre modellen til en løgner. Din opgave er et dashboard der er smukt *og* ikke
kan oversælge.

## DATAKONTRAKT

Dashboardet skal drives af én JSON-fil, så det kan genbruges hver måned uden
redesign. Filen genereres af modellen selv som sidste skridt i det månedlige ritual:

```bash
cd v5 && python motor.py --json
```

Den skriver `dashboard.json` i repo-roden (eller til en sti angivet efter flaget).
Eksemplet nedenfor er genereret direkte fra `motor.py --json` (snapshot 2026-10-15)
og **forkortet**: lange lister er skåret ned til et eller få elementer, `diagnostik`
og `bro` til et udvalg af felter, og lange tekster er afkortet med "…". Tallene er
eksempler, ikke den aktuelle læsning. Feltrækkefølgen er motorens.

```json
{
  "version": "5.0.1",
  "manifest_hash": "72c3371d",
  "forrige_manifest": "6baeade4",
  "raa": {
    "beta_curve_pr_pp": -1.2948,
    "alpha": -0.2915,
    "note": "P = logit^-1(alpha + beta * kurve_i_pp); samme model som de standardiserede vaegte"
  },
  "bro": {
    "input_vektor": {"curve": 0.96},
    "snapshot": "2026-09-19",
    "trin": {
      "i_legacy_rygrad": {"P": 0.1804, "n_obs": 264},
      "ii_korrigerede_kilder_samme_origins": {"P": 0.1804, "n_obs": 264},
      "iii_udvidet_panel": {"P": 0.1773, "n_obs": 267}
    },
    "saetning": "A lower or higher recalibrated probability is changed estimation, not changed economic risk."
  },
  "gate": {
    "identiske_origins": true,
    "curve_only_wf": 27.05,
    "curve_only_brier": 24.15,
    "fuldmodel_wf": 23.16,
    "fuldmodel_brier": 23.69,
    "forskel_pp": -3.89,
    "mde_pp": 4.42,
    "fuldmodel_slaar": false,
    "raadsbeslutning_paakraevet": false,
    "note": "LL-forskel 3.9pp < stoejgulv 4.42pp (trin 3-MDE). Gaten er m …"
  },
  "stale": null,
  "diagnostik": {
    "version": "5.0.1",
    "manifest_hash": "72c3371d",
    "snapshot": "2026-09-19",
    "primaer": {"n": 198, "improvement": 27.05, "brier": 24.15},
    "oracle_fri": {
      "alle_live_publicerbare": {"n": 219, "improvement": 20.37},
      "ekskl_additional": {"n": 198, "improvement": 27.05},
      "tolkning": "De to varianter tolkes i tandem og citeres aldrig hver for sig (Gemini R5)."
    }
  },
  "live_input": {
    "kilde": "daglig",
    "vindue": ["2026-09-14", "2026-10-13"],
    "n_dage": 21,
    "curve": 1.1181,
    "y10": 5.15,
    "tb3": 4.0319,
    "y10_seneste": ["2026-10-13", 5.21],
    "tb3_seneste": ["2026-10-13", 4.09],
    "maanedlig": {"curve": 1.05, "y10": 4.99, "tb3": 3.94, "maaned": "2026-09"},
    "p_maanedlig": 0.160963,
    "fed_funds": {"vaerdi": 3.88, "dato": "2026-10-13", "kilde": "DFF dagligt"},
    "sammensaetning": null
  },
  "trigger": "manuel/reparation (foerste kalibrering efter v5.0)",
  "delta_vs_forrige": {
    "n_origins": 316,
    "max_abs_dP": 0.0779,
    "origin_max": "1974Q1",
    "mean_abs_dP": 0.0173,
    "d_beta_pr_pp": 0.2068
  },
  "koersel": null,
  "rekalibrering_paakraevet": [],
  "snapshot": "2026-10-15",
  "snapshot_hash": "d3a14a99b5",
  "model": "curve-only-logit",
  "label": "NBER-onset inden 4 kvartaler",
  "kalibreret": "2026-09-19",
  "n_obs": 267,
  "n_episoder": 12,
  "wf_log_loss": 27.05,
  "wf_brier": 24.15,
  "wf_note": "fast lambda=1 (arvet fra v4); fuld-sti-valg mellem to modeller, ikke nested (G1.1/G1.2)",
  "skill_saetning": "Walk-forward-skill: oracle-fri, fast lambda=1: +20.4% (219 origins); orakel-censureret, fast lambda=1: +27.1%; nested lambda (orakel-censureret; oracle-fri udgave ikke beregnet): +18.3% — og 80 % styrke kraever stoerrelsesordenen 150 kalenderaars hovedbog; ...",
  "p": 0.149408,
  "baand": [0.102461, 0.212921],
  "basisrate": 0.1798,
  "baand_udelukker_basisrate": false,
  "ratio": null,
  "baand_fodnote": "Not a predictive interval; reflects weight sensitivity to episode composition",
  "dom": "P er 14.9% mod basisraten 18.0%, men baandet [10.2-21.3%] indeholder basisraten: IKKE SKELNELIG FRA BASISRATEN.",
  "dom_ord": "ikke skelnelig",
  "parret": {
    "baand": [-0.063774, -0.002335],
    "skelnelig": true,
    "enig_med_baandregel": false,
    "daekning": "coverage not established"
  },
  "censureret": {"aktiv": false, "onset": null},
  "inputs": [
    {"navn": "Rentekurve 10y-3m", "vaerdi": 1.1181, "z": -0.222, "operationel": true},
    {"navn": "Realrente 10y-CPI", "vaerdi": 1.4123, "z": -0.1235, "operationel": false}
  ],
  "dd_kilde": "kalibreringsstatistik (trailing maanedsmiddel fra 2026-09-15 mod 12-mdr max af maanedsmidler)",
  "benchmarks": [
    {
      "navn": "curve-only-logit (NY Fed-stil-bm.)",
      "wf": 27.05,
      "live_p": 0.149408,
      "status": "OPERATIONEL",
      "panel": "fuld sti t.o.m. 2024Q1",
      "note": "fast lambda=1 (arvet fra v4); fuld-sti-v …"
    },
    {
      "navn": "curve-only, samme panel (reference)",
      "wf": 34.32,
      "live_p": null,
      "status": "reference for de afviste kandidater",
      "panel": "t.o.m. 2023Q2"
    },
    {
      "navn": "curve+awh (praereg. v5.2-test)",
      "wf": 33.87,
      "live_p": null,
      "status": "testet, ikke bestaaet (sidste skud; soegning lukket) [panel t.o.m. 2023Q2]",
      "panel": "t.o.m. 2023Q2"
    }
  ],
  "monitors": [
    {
      "navn": "Kurven inverteret",
      "tilstand": "inaktiv",
      "vaerdi": "+1.12pp",
      "klasse": "operationel feature"
    },
    {
      "navn": "HY OAS > 600bp",
      "tilstand": "inaktiv",
      "vaerdi": "316bp (2026-10-13)",
      "klasse": "v4-flag/seed-taerskel 600bp; ineligible (historik 1997-, FRED leverer …"
    },
    {
      "navn": "Claims-momentum",
      "tilstand": "kontekst",
      "vaerdi": "4u-snit 198k; maanedssnit 12m -14.3% (2026-09)",
      "klasse": "testet, ikke bestaaet (trin 4)"
    }
  ],
  "scenarie": [
    {
      "navn": "10Y > 5,25%",
      "tilstand": "inaktiv",
      "vaerdi": "5.21% (2026-10-13) / KW TP +1.07pp (Kim-Wright, Fed Board, 10-09); sid …",
      "klasse": "1 kanal (fiskal); kanalens ANTAGNE trigger, ikke Q2-varsel; maaleregel: seneste daglige niveau"
    }
  ],
  "forudsaetninger": [
    {
      "navn": "Realt kontantafkast FF-PCE < 0",
      "tilstand": "inaktiv",
      "vaerdi": "+0.46pp",
      "klasse": "v4-debaseringsflag (seed-ekko, G2.3)"
    }
  ],
  "market_conditions": [{"navn": "CAPE-percentil (expanding)", "vaerdi": "92.7. pct (CAPE 41.38)"}],
  "pengepolitik": [{"navn": "Fed funds (effektiv)", "vaerdi": "3.88% (2026-10-13, DFF dagligt)"}],
  "kredit": [],
  "nber_indikatorer": [],
  "manual_friskhed": {
    "cape": {"dato": null, "alder_dage": null, "stale": false},
    "spx_vs_hi": {"dato": null, "alder_dage": null},
    "margin_yoy": {"periode": null, "forventet_nyeste": "2026-08", "foraeldet": false}
  },
  "utilgaengelige": [],
  "sti": {
    "punkter": [["2025-10", 0.3538], ["trailing 2026-10-13", 0.1494]],
    "top": "2025-10",
    "p_top": 0.3538,
    "maaneder_siden_top": 12,
    "fald_fra_top_pp": 20.4,
    "note": "beskrivende — ingen fremskrivning, ingen indflydelse paa P (DASHBOARD-BRIEF regel 9)"
  },
  "maanedens_aendring": {
    "fra": "2026-10-10",
    "dP_pp": -0.16,
    "dK_pp": 0.0081,
    "d10Y_pp": 0.0391,
    "d3m_pp": 0.0269,
    "bidrag_10Y_pp": -0.64,
    "bidrag_3m_pp": 0.44,
    "maerke": "lang-ende-drevet (bear steepening)",
    "input_foer": "daglig"
  },
  "advarsler": {
    "vaerste_fejlalarm": {"p": 0.9383, "origin": "2023Q2"},
    "sti_advarsel": "Modellen laeser kurvens NIVEAU; +1.12pp behandles som +1.12pp uden for …",
    "lang_ende": "En stigning i den lange ende saenker P mekanisk (ca. 1.6pp pr. 10bp ve …",
    "eksogen": "Eksogene chok kan ikke forudsiges."
  },
  "hovedbog": [
    {
      "logget": "2026-10-10",
      "snapshot": "2026-10-10",
      "P": "15.1%",
      "baand": "10.4-21.6%",
      "basisrate": "18.0%",
      "dom": "ikke skelnelig",
      "kurve": "+1.11",
      "antaending": "ingen",
      "note": "input: daglig (kurve = trailing maaned DGS10-DTB3; foer: GS1 …",
      "kalibrering": "72c3371d",
      "vindue": "",
      "p_tal": 0.151,
      "baand_tal": [0.104, 0.216],
      "basisrate_tal": 0.18,
      "kurve_tal": 1.11,
      "p_maanedlig_tal": null
    }
  ],
  "hovedbog_note": "Den eneste fuldt prospektive test — beskytter mod look-ahead, men stat …",
  "noegle": null
}
```

### Felternes betydning

**Læsningen**

- `snapshot` og `snapshot_hash`: hvilke rådata læsningen bygger på. `model` og `label`:
  den operationelle model og målvariablen. De står i læsningens rammetekst.
- `p`, `baand` [lav, høj], `basisrate`: tal mellem 0 og 1. `baand` er et 10-90 %
  estimations-sensitivitetsbånd. `baand_fodnote` hører altid til båndet.
- `dom`: skabelon-genereret sætning, gengives ordret. `dom_ord` er det korte domsord, som
  hovedbogen bruger: `ikke skelnelig` / `under basisraten` / `over basisraten` / `censureret`.
- `baand_udelukker_basisrate` og `ratio`: `ratio` er `null`, medmindre båndet udelukker basisraten.
- `censureret`: `{aktiv, onset}`. Er `aktiv` sand, ligger læsningens måned inde i en annonceret
  recession. Så er onset-sandsynligheden ikke defineret, og `dom` siger CENSURERET. P må da kun
  vises som reference, aldrig som hovedtal.
- `parret`: det parrede supplement (RAADETS_V501 §4.3): `{baand, skelnelig, enig_med_baandregel,
  daekning}`. `baand` er 10-90 % for P minus basisraten (i sandsynlighedsenheder), og `daekning`
  er altid `"coverage not established"`. Supplementet **ændrer ikke dommen**. `null` = ikke
  beregnet (kalibrering uden basis-træk).
- `inputs`: de fem features med `vaerdi` og `z`. Kun én har `operationel: true`. `dd_kilde`
  fortæller hvilken drawdown-statistik fuldmodellen fik.
- `live_input`: hvilke data kurven er målt på.
  - `kilde` er `daglig` eller `maanedlig`, og `vindue` er [fra, til] med `n_dage`. `curve`,
    `y10` og `tb3` er trailing-middel; `y10_seneste` og `tb3_seneste` er seneste dag.
  - `maanedlig` er de publicerede månedstal, og `p_maanedlig` er P på dem: en lille
    sammenligningslinje, aldrig et alternativt hovedtal.
  - `fed_funds` er seneste effektive rente med kilde. `sammensaetning` er kurvens front/bag-
    opdeling på samme vindue (`null` hvis 2-års-renten mangler).
- `stale`: `null`, eller `{serie: {sidste, alder_dage, graense, kritisk}}` for serier der var
  for gamle, da snapshottet blev hentet. `kritisk: true` skal være synligt ved læsningen.
- `manual_friskhed`: dato og alder for de manuelle input (`cape`, `spx_vs_hi`, `margin_yoy`).
  `stale`/`foraeldet` sand = vis en lille note ved den berørte linje.
- `utilgaengelige`: serier der mangler eller er forældede i snapshottet. Deres linjer har
  `tilstand: "utilgaengelig"`.

**Kalibreringen**

- `version`, `manifest_hash`, `forrige_manifest`, `kalibreret`, `n_obs`, `n_episoder`:
  hvilken frossen kalibrering læsningen bygger på. `raa` er de rå logit-koefficienter.
- `skill_saetning` (RAADETS_2027 §1.2): DEN måde skill vises på. Gengiv den ordret, som én sætning.
  Det oracle-fri tal står først, og styrkeklausulen står i samme sætning. `wf_log_loss` (+27,05 %)
  må aldrig vises alene som modellens træfsikkerhed.
- `wf_log_loss` og `wf_brier`: den orakel-censurerede walk-forward-skill i %. `wf_note` er
  metodeforbeholdet og skal stå ved tallet.
- `gate`: release-gaten mellem fuldmodel og curve-only på identiske origins: `curve_only_wf`,
  `fuldmodel_wf`, `forskel_pp`, `mde_pp` (støjgulv), `fuldmodel_slaar`,
  `raadsbeslutning_paakraevet` og `note`. Gaten er mekanisk og kan ikke flytte den
  operationelle model. Vis `note` ordret ved benchmark-tabellen.
- `trigger`: hvorfor den gældende kalibrering blev lavet (fx september-rekalibrering,
  NBER-annoncering, manuel reparation).
- `koersel`: seneste kørsel af kalibreringskæden, `{maaned, utc, trigger, manifest_genbrugt}`,
  eller `null`. `manifest_genbrugt: true` = kørslen ændrede ikke vægtene.
- `bro`: findes kun efter en rekalibrering. Den viser P ved **identiske inputs** under
  kalibreringstrinnene (`trin`) og bærer `saetning`, som gengives ordret. Bro-tallene vises
  side om side, aldrig som "før/efter-forbedring".
- `delta_vs_forrige`: hvor meget rekalibreringen flyttede de historiske P'er (`max_abs_dP`,
  `origin_max`, `mean_abs_dP`, `andel_over_5pp`, vægtændringer m.m.). Det er ændret
  estimation, ikke ændret risiko, og vises kun sammen med `bro`.
- `rekalibrering_paakraevet`: liste af tekster, opgjort pr. snapshottets dato (dashboard.json er en
  deterministisk funktion af snapshot, vægte, diagnostik og LOG.md — CI genskaber den bit-identisk, så
  intet i den afhænger af den dag, motoren kørte). Er den ikke tom, er en §3.2-rekalibrering forfalden
  (september eller ny NBER-annoncering). Læsningen vises stadig, men med en tydelig tekstnote
  "REKALIBRERING PÅKRÆVET" og listens tekst ordret.
- `hovedbog_reference`: hovedbogens referencetal (`improvement`, i dag +20,4 % — diagnostik 4.5,
  realtidscensurering) med kilde. Vis det ved hovedbogen i stedet for `wf_log_loss`; hovedbogen må
  aldrig stå ved siden af +27,1 % alene (BEDOEMMELSESNOEGLE.md §3).
- Om en læsning er logført, ses KUN af `hovedbog` (en række med `snapshot` = dette snapshot). Alt
  andet er en mellemlæsning; vis det i lille tekst.
- `diagnostik`: RAADETS_V501 §4-diagnostik (episode-tabel, LOEO, domsregel-backtest,
  oracle-fri varianter, trunkeret panel m.m.). Valgfri kontekst, aldrig én samlet score,
  se regel 11.

**Benchmarks**

- `benchmarks[]`: `{navn, wf, live_p, status, panel}` plus evt. `note` og `vaerdi`. `panel`
  angiver hvilket panel `wf` er målt på: "fuld sti t.o.m. …" for de operationelle rækker og
  "t.o.m. 2023Q2" for de afviste kandidater og deres reference. `panel: null` betyder ingen
  wf-skill (fx basisrate, arv eller nowcast). Rækken "curve-only, samme panel (reference)" er
  referencen for de afviste kandidater (regel 14).

**Monitorer, scenarie og kontekst**

- `monitors[]`: `{navn, tilstand, vaerdi, klasse}`. `tilstand` kan være:
  - `aktiv`: tærsklen er krydset.
  - `inaktiv`: tærsklen er ikke krydset.
  - `kontekst`: linjen har ingen tærskel og kan aldrig tændes.
  - `utilgaengelig`: data mangler. Vis den aldrig som inaktiv.

  Kun aktive linjer i antændings-klassen kan stå i hovedbogens antændings-kolonne.
  `klasse` bærer proveniensen. HY-linjen viser fx noten "I SVAERM-ZONEN 350-450bp" i `vaerdi`,
  når spændet ligger i atlassets zone.
- `scenarie[]`: MiroFish-sværmens tripwires (CP-spænd, 10Y, realkredit; TRIGGER-ATLAS.md)
  i samme form som monitorer. Det er et **særskilt appendiks**. Linjerne indgår aldrig i
  modeloutputtet eller i antændings-kolonnen (rådets R3), se regel 15.
- `forudsaetninger[]`: atlassets forudsætnings-tripwires med aktuel status i samme form
  (margin, permits og realt kontantafkast; det sidste er et v4-flag). Vises under market
  conditions med firewall-mærkat og tælles aldrig.
- `market_conditions[]`, `pengepolitik[]` og `kredit[]` er `{navn, vaerdi}`-kontekst.
  `kredit` (EBP, Baa−10Y) kan være tom.
- `nber_indikatorer[]`: `{serie, navn, maaned, yoy, fra_12m_top, note}`, NBER-komiteens egne
  coincident-serier. De har ingen tærskler, tælles ikke og er en anden disciplin end
  prognosen. Listen kan være tom.
- `sti`: P ved de **nuværende frosne vægte** over de seneste 12 publicerede måneder plus
  trailing-måneden (`punkter`, `top`, `p_top`, `maaneder_siden_top`, `fald_fra_top_pp`,
  `note`). Den er beskrivende og tilbageregnet, altså ikke prospektiv. Den må aldrig tegnes
  som eller sammen med hovedbogen, og den får ingen fremskrivning (regel 9).
- `maanedens_aendring`: ændring mod sidste logførte række. `dP_pp` og `dK_pp` er ændringen i
  P og kurve. Dekompositionen ved frosne vægte er `d10Y_pp`, `d3m_pp`, `bidrag_10Y_pp`,
  `bidrag_3m_pp` og `maerke` (fx "lang-ende-drevet (bear steepening)"). `input_foer` siger om
  den forrige række brugte daglige eller månedlige data. Feltet er `null` uden en tidligere
  række.
- `advarsler`: `vaerste_fejlalarm`, `sti_advarsel`, `lang_ende` (en stigning i den lange ende
  sænker P mekanisk, mens atlassets kanal 5 læser samme bevægelse som risiko) og `eksogen`.
  Alle vises ordret.

**Hovedbogen**

- `hovedbog[]`: én række pr. logført måned fra `LOG.md`. Tekstfelterne gengiver LOG.md
  ordret: `P`, `baand`, `basisrate` og `kurve` er **tekst** (fx `"15.1%"`, `"10.4-21.6%"`,
  `"+1.11"`). De andre felter er:
  - `logget`, `snapshot`, `dom`, `antaending` og `note`.
  - `kalibrering`: manifest-hash. Den er tom streng i rækker fra før v5.0.1, så vis dem uden.
  - `vindue`: rækkens scoringsvindue "ÅÅÅÅ-MM..ÅÅÅÅ-MM".
  - `input`: "daglig fra..til (Nd)" eller "maanedlig ÅÅÅÅ-MM".
  - `P_maanedlig`: P på publicerede månedstal.

  `vindue`, `input` og `P_maanedlig` findes kun i rækker skrevet fra 2026-10-15. Ældre rækker
  mangler felterne eller har en tom streng. **Tegn altid ud fra de numeriske felter**
  `p_tal`, `baand_tal` [lav, høj], `basisrate_tal`, `kurve_tal` og `p_maanedlig_tal`
  (P og bånd som 0-1, kurven i procentpoint). De er `null`, hvor teksten ikke kan læses
  som tal. Rækker med `P: "ikke logget"` (og "(ikke logget)" i `logget`) markerer måneder
  uden læsning i logvinduet. De vises som huller, aldrig interpoleret.
- `hovedbog_note`: teksten der står ved hovedbogen. Den gengives ordret.
- `noegle`: 8-tegns hash af bedømmelsesnøglen (BEDOEMMELSESNOEGLE.md), eller `null` hvis
  nøglen ikke findes. Er den `null`, vises ingen form for score over hovedbogen (regel 13).

Felter der styrer betinget visning og ikke må ignoreres: `baand_udelukker_basisrate`,
`ratio` (kan være `null`), `censureret.aktiv`, `monitors[].tilstand` (`aktiv` / `inaktiv` /
`kontekst` / `utilgaengelig`), `rekalibrering_paakraevet`, `stale` og `noegle`.

## SEKTIONER — i prioriteret rækkefølge

1. **Læsningen.** P, båndet og basisraten i **én** visuel ramme. Under den:
   `dom` gengivet ordret og `baand_fodnote` ved båndet. Under dommen, mindre og tydeligt
   underordnet, kommer det parrede supplement (`parret`) med mærkaten
   "coverage not established" (regel 12). Ved `censureret.aktiv` vises dommen alene.
2. **Hovedbogen.** Tidsserie over alle logførte læsninger: P med bånd pr. måned
   (`p_tal`, `baand_tal`) og basisraten (`basisrate_tal`) som reference.
   Hovedbogen er **den eneste fuldt prospektive test — beskytter mod look-ahead, men
   statistisk svag**: der kræves mange komplette konjunkturcykler, før den kan skelne
   modellen fra basisraten (BEDOEMMELSESNOEGLE.md). Vis den som et register over
   læsninger logført før udfaldet var kendt, med `hovedbog_note` ved siden af, og aldrig
   som en dom over modellen (regel 13). Den skal se rigtig ud med få punkter.
3. **Månedens ændring.** P og kurve mod sidste logførte læsning, med dekompositionen
   (`maanedens_aendring`). Rene tal.
4. **Benchmark-tabel.** Alle rækker, inkl. de "testet, ikke bestået" og arve-modellen.
   Kolonner: model, walk-forward-skill, **panel**, live-P, status. Referencerækken står
   lige over de afviste kandidater (regel 14). `gate.note` står ved tabellen.
5. **Model-inputs.** De fem features med værdi og z-score. Markér hvilken der
   faktisk er operationel (kun én er).
6. **Monitorer.** Individuelle linjer grupperet efter `klasse`. Aldrig talt sammen.
   `klasse` er fritekst; gruppér på leddet før kolon/parentes (operationel feature /
   testet, ikke bestaaet / svaerm-tripwire / uvalideret / ineligible / fuldmodel-feature / utestet monitor).
7. **Market conditions** (inkl. forudsætnings-tripwires), **Pengepolitik & inflation**,
   **Kredit** og **NBER-indikatorer**. Alle med deres firewall-mærkat synlig.
8. **De stående advarsler.** Værste fejlalarm, sti-advarsel, lang ende, eksogene chok.
   Permanent synlige, ikke bag en fold-ud.
9. **Scenarie-appendiks** (`scenarie`). Til sidst og visuelt adskilt fra monitorerne
   (regel 15).

Kalibreringsdetaljer (`bro`, `delta_vs_forrige`, `trigger`, `koersel`, `diagnostik`) og
dataalder (`stale`, `manual_friskhed`, `utilgaengelige`) må gerne
samles i en rolig fodnote-sektion.

## UFRAVIGELIGE REGLER

1. **P står aldrig alene.** Bånd og basisrate skal være i samme visuelle ramme og
   have visuel vægt på niveau med punktestimatet. En læser der kun ser tallet skal
   ikke kunne opstå.
2. **Ratio vises kun når `baand_udelukker_basisrate` er sand.** Ellers skal feltet
   være helt fraværende — ikke nedtonet, ikke gråt, ikke "n/a".
3. **Intet speedometer, måler, termometer eller trafiklys.** De signalerer en
   præcision modellen ikke har.
4. **Farve må ikke kode fare.** Ingen rød ved høj P, ingen grøn ved lav. Farve må
   kun skelne *klasser* (operationel / testet-ikke-bestået / firewallet kontekst /
   scenarie).
5. **Monitorer tælles aldrig sammen.** Ingen "3 af 11 aktive", ingen samlet
   risikoscore, ingen procentdel. Hver linje står for sig selv. Det samme gælder
   forudsætnings-tripwires og scenarie-linjer.
6. **Benchmark-tabellen vises altid**, også når den er usmigrende for den
   operationelle model. De fejlslagne kandidater er en feature, ikke en bug.
7. **`dom` gengives ordret.** Den er skabelon-genereret netop for ikke at kunne
   blive skarpere end tallene. Omskriv ikke, forkort ikke, tilføj ikke udråbstegn.
8. **Firewall-mærkaterne er synlige**, ikke i tooltips: "ingen indflydelse på P"
   på monitorer, forudsætnings-tripwires og pengepolitik, "not recession evidence" på
   market conditions, og "MiroFish-scenarie — uvalideret, ingen indflydelse på P,
   ikke i hovedbogen" på scenarie-appendikset.
9. **Ingen fremskrivning.** Ingen trendlinje gennem hovedbogen, ingen pil, ingen
   ekstrapolation, ingen "måneder til recession". Det gælder også `sti`.
10. **Båndet er ikke et konfidensinterval.** Kald det aldrig det. Det er et
    estimations-sensitivitetsbånd, og fodnoten skal stå ved det.
11. **Oracle-fri tal vises kun i tandem.** De to oracle-fri varianter
    (`diagnostik.oracle_fri.alle_live_publicerbare` og `.ekskl_additional`) vises
    sammen med `tolkning` — eller slet ikke. Én variant alene må aldrig citeres.
12. **Det parrede bånd mærkes "coverage not established".** Teksten tages fra
    `parret.daekning`, ikke fra designet. Supplementet står under dommen, aldrig som
    overskrift. Det udløser aldrig `ratio` og formuleres aldrig som "skelnelig fra
    basisraten" uden forbeholdet. Er `enig_med_baandregel` falsk, er det ikke en
    ny dom; dommen er stadig `dom`.
13. **Hovedbogen vises aldrig med en samlet score, hitrate eller dom over modellen**,
    før bedømmelsesnøglens minimum er nået (BEDOEMMELSESNOEGLE.md, regel (h): mindst 3
    komplette cyklusblokke scoret) — og slet ikke, når `noegle` er `null`. Rækkerne
    vises enkeltvis.
14. **Benchmark-rækker fra forskellige paneler viser deres panel.** Wf-skill må kun
    sammenlignes inden for samme panel. De afviste kandidater (panel t.o.m. 2023Q2)
    sammenlignes med curve-only-referencen på samme panel, ikke med den operationelle
    rækkes wf. Ellers kan en afvist kandidat se bedre ud end den model, der slog den.
15. **Scenarie-appendikset er visuelt adskilt fra monitorerne og tælles aldrig.**
    Det har egen sektion, egen mærkat og dæmpet klassefarve. Ingen af dets linjer
    må fremstå som en del af antændings-kolonnen eller af læsningen.

## ANTI-MØNSTRE — nævnt fordi de er fristende

Speedometernål der peger på "MODERATE". Stort rødt tal øverst. Badge med
"RECESSION RISK: ELEVATED". Nedtælling. Pulserende alarmfarve. Sparkline med pil.
Sammentalte tripwires. "Model confidence: 82 %". Hitrate eller "track record" over
hovedbogen. Det parrede supplement som overskrift. En afvist kandidat sammenlignet med
et andet panel. Alt der får en læsning, som ikke kan skelnes fra basisraten, til at
se ud som information.

## VISUELT SPROG

- **Tone:** dokumentarisk og rolig. Nærmere en videnskabelig rapport eller et
  centralbank-appendiks end et fintech-produkt. Det må gerne være smukt — det må
  bare ikke være spændende på tallenes vegne.
- **Typografi:** tal i monospace eller tabular figures, så kolonner flugter.
  Rigelig luft; hellere færre elementer med plads end tæt pakning.
- **Palette:** neutral grundtone. Én accentfarve, brugt til at markere hvad der er
  operationelt. Dæmpede toner til firewallede sektioner, så øjet ser at de er en
  anden slags information. Scenarie-appendikset er den mest dæmpede.
- **Båndet:** vandret interval-bar med punktestimatet markeret i den, og
  basisraten som en tydelig lodret linje der skærer igennem. Når linjen ligger
  inde i baren skal det være umiddelbart synligt hvorfor dommen lyder som den gør.
- **Lys og mørk baggrund.** Begge skal fungere.
- **Skal kunne screenshottes** og stadig give mening som ét billede i en tråd.
- **Sprog:** dansk med rigtige æ, ø og å. Kildedataene staver "baand", "aendring",
  "paakraevet" osv. af konsol-hensyn — det skal ikke slå igennem i dashboardet. Det gælder også `dom`:
  translitteration (aa→å, ae→æ, oe→ø) og dansk talformat (15,1 %) er de eneste tilladte
  ændringer af den ordrette tekst (regel 7).

## LEVERANCE

Én selvstændig HTML-fil, responsiv fra telefon til bred skærm, uden
build-værktøjer. Læser JSON'en beskrevet ovenfor. Tomme lister, `null`-felter og
manglende felter (ældre hovedbogsrækker) skal håndteres uden at layoutet falder
sammen. Hovedbogen kan indeholde alt fra én til mange rækker, inklusive
"ikke logget"-huller.
