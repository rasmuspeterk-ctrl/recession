# MOTOR v5.0 — dashboard-brief

Fast skabelon til den månedlige læsning. Kopiér alt under stregen ind i det
designværktøj du bruger, og vedhæft månedens data (se Datakontrakt).

Opdateres kun når `motor.py`'s output-struktur ændres.

---

## KONTEKST — læs først, reglerne følger af den

Du skal designe et månedligt dashboard for MOTOR v5.0, en model der estimerer
sandsynligheden for at en amerikansk recession (NBER-dateret) *begynder* inden
for de næste fire kvartaler.

Det afgørende ved denne model: **den er ærlig om at den næsten ikke kan noget.**
Den er en logistisk regression på én eneste variabel — rentekurven (10-årig minus
3-måneders). Den er kalibreret på 264 kvartaler med kun 12 recessionsstarter. Dens
værste fejlalarm i historisk test var 93,8 % sandsynlighed for en recession der
aldrig kom. Lige nu siger den 18,0 % mod en basisrate på 18,2 % — altså: den ved
reelt ikke mere end at tælle hvor ofte recessioner sker.

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
Struktur:

```json
{
  "version": "5.0.1",
  "manifest_hash": "72c3371d",
  "forrige_manifest": "6baeade4",
  "raa": {"beta_curve_pr_pp": -1.2948, "alpha": -0.2915},
  "bro": {"trin": {"i_legacy_rygrad": {"P": 0.18}, "iii_udvidet_panel": {"P": 0.177}}, "saetning": "A lower or higher recalibrated probability is changed estimation, not changed economic risk."},
  "diagnostik": {"episode_tabel": "...", "loeo": "...", "domsregler_backtest": "...", "oracle_fri": "..."},
  "snapshot": "2026-09-19",
  "snapshot_hash": "c8c2ffa526",
  "model": "curve-only-logit",
  "label": "NBER-onset inden 4 kvartaler",
  "kalibreret": "2026-09-10",
  "n_obs": 264,
  "n_episoder": 12,
  "wf_log_loss": 34.3,
  "wf_brier": 32.9,

  "p": 0.180,
  "baand": [0.127, 0.263],
  "basisrate": 0.182,
  "baand_udelukker_basisrate": false,
  "ratio": null,
  "baand_fodnote": "Not a predictive interval; reflects weight sensitivity to episode composition",
  "dom": "P er 18,0 % mod basisraten 18,2 %, men båndet [12,7-26,3 %] indeholder basisraten: IKKE SKELNELIG FRA BASISRATEN.",

  "inputs": [
    {"navn": "Rentekurve 10y-3m", "vaerdi": 0.96, "z": -0.39, "operationel": true},
    {"navn": "Realrente 10y-CPI", "vaerdi": 1.32, "z": -0.16, "operationel": false}
  ],

  "benchmarks": [
    {"navn": "intercept (basisrate)", "wf": 0.0, "live_p": 0.182, "status": null},
    {"navn": "curve-only-logit", "wf": 34.3, "live_p": 0.180, "status": "OPERATIONEL"},
    {"navn": "fuldmodel (5 features)", "wf": 33.2, "live_p": 0.090, "status": "testet, ikke bestået"}
  ],

  "monitors": [
    {"navn": "Kurven inverteret", "tilstand": "inaktiv", "vaerdi": "+0,96pp", "klasse": "operationel feature"},
    {"navn": "Claims-momentum", "tilstand": "kontekst", "vaerdi": "4u-snit 206k; 12m -12,3 %", "klasse": "testet, ikke bestået"},
    {"navn": "CP-spænd 3m > 75bp", "tilstand": "inaktiv", "vaerdi": "3bp", "klasse": "sværm-tripwire"}
  ],

  "market_conditions": [{"navn": "CAPE-percentil", "vaerdi": "92,4. pct"}],
  "pengepolitik":      [{"navn": "Fed funds (effektiv)", "vaerdi": "3,63 %"}],

  "advarsler": {
    "vaerste_fejlalarm": {"p": 0.938, "origin": "2023Q2"},
    "sti_advarsel": "Modellen læser kurvens NIVEAU; +0,96pp behandles som +0,96pp uden forhistorie…",
    "eksogen": "Eksogene chok kan ikke forudsiges."
  },

  "hovedbog": [
    {"logget": "2026-08-12", "p": 0.201, "baand": [0.144, 0.292], "basisrate": 0.182,
     "dom": "ikke skelnelig", "kurve": 0.87, "antaending": "ingen", "note": ""},
    {"logget": "2026-09-09", "p": 0.180, "baand": [0.127, 0.263], "basisrate": 0.182,
     "dom": "ikke skelnelig", "kurve": 0.96, "antaending": "ingen", "note": ""}
  ]
}
```

`version`/`manifest_hash` viser hvilken kalibrering læsningen bygger på; hovedbogsrækker fra v5.0.1 bærer
samme hash i feltet `kalibrering` (ældre rækker har det ikke — vis dem uden). `bro` findes kun efter en
rekalibrering og skal vises som to tal ved identiske inputs, aldrig som "før/efter-forbedring".
`diagnostik` er valgfri kontekst: episode-tabellen må tegnes, men aldrig sammenfattes til én score.

Tre felter styrer betinget visning og må ikke ignoreres:
`baand_udelukker_basisrate`, `ratio` (kan være `null`) og `monitors[].tilstand`
(`aktiv` / `inaktiv` / `kontekst`).

## SEKTIONER — i prioriteret rækkefølge

1. **Læsningen.** P, båndet og basisraten i **én** visuel ramme. Under den:
   `dom` gengivet ordret, og `baand_fodnote` ved båndet.
2. **Hovedbogen.** Tidsserie over alle logførte læsninger: P med bånd pr.
   måned, basisraten som vandret referencelinje. Dette er modellens eneste ægte
   eksamen — hver læsning er logført før udfaldet var kendt. Giv den plads
   svarende til det. Med kun to punkter skal den stadig se rigtig ud.
3. **Månedens ændring.** P og kurve mod sidste logførte læsning. Rene tal.
4. **Benchmark-tabel.** Alle rækker, inkl. de tre "testet, ikke bestået" og
   arve-modellen. Kolonner: model, walk-forward-skill, live-P, status.
5. **Model-inputs.** De fem features med værdi og z-score. Markér hvilken der
   faktisk er operationel (kun én er).
6. **Monitorer.** Individuelle linjer grupperet efter `klasse`. Aldrig talt sammen.
7. **Market conditions** og **Pengepolitik & inflation**. Begge med deres
   firewall-mærkat synlig.
8. **De stående advarsler.** Værste fejlalarm, sti-advarsel, eksogene chok.
   Permanent synlige, ikke bag en fold-ud.

## UFRAVIGELIGE REGLER

1. **P står aldrig alene.** Bånd og basisrate skal være i samme visuelle ramme og
   have visuel vægt på niveau med punktestimatet. En læser der kun ser tallet skal
   ikke kunne opstå.
2. **Ratio vises kun når `baand_udelukker_basisrate` er sand.** Ellers skal feltet
   være helt fraværende — ikke nedtonet, ikke gråt, ikke "n/a".
3. **Intet speedometer, måler, termometer eller trafiklys.** De signalerer en
   præcision modellen ikke har.
4. **Farve må ikke kode fare.** Ingen rød ved høj P, ingen grøn ved lav. Farve må
   kun skelne *klasser* (operationel / testet-ikke-bestået / firewallet kontekst).
5. **Monitorer tælles aldrig sammen.** Ingen "3 af 11 aktive", ingen samlet
   risikoscore, ingen procentdel. Hver linje står for sig selv.
6. **Benchmark-tabellen vises altid**, også når den er usmigrende for den
   operationelle model. De fejlslagne kandidater er en feature, ikke en bug.
7. **`dom` gengives ordret.** Den er skabelon-genereret netop for ikke at kunne
   blive skarpere end tallene. Omskriv ikke, forkort ikke, tilføj ikke udråbstegn.
8. **Firewall-mærkaterne er synlige**, ikke i tooltips: "ingen indflydelse på P"
   på sværm-tripwires og pengepolitik, "not recession evidence" på market conditions.
9. **Ingen fremskrivning.** Ingen trendlinje gennem hovedbogen, ingen pil, ingen
   ekstrapolation, ingen "måneder til recession".
10. **Båndet er ikke et konfidensinterval.** Kald det aldrig det. Det er et
    estimations-sensitivitetsbånd, og fodnoten skal stå ved det.

## ANTI-MØNSTRE — nævnt fordi de er fristende

Speedometernål der peger på "MODERATE". Stort rødt tal øverst. Badge med
"RECESSION RISK: ELEVATED". Nedtælling. Pulserende alarmfarve. Sparkline med pil.
Sammentalte tripwires. "Model confidence: 82 %". Alt der får 18,0 % mod en
basisrate på 18,2 % til at se ud som information.

## VISUELT SPROG

- **Tone:** dokumentarisk og rolig. Nærmere en videnskabelig rapport eller et
  centralbank-appendiks end et fintech-produkt. Det må gerne være smukt — det må
  bare ikke være spændende på tallenes vegne.
- **Typografi:** tal i monospace eller tabular figures, så kolonner flugter.
  Rigelig luft; hellere færre elementer med plads end tæt pakning.
- **Palette:** neutral grundtone. Én accentfarve, brugt til at markere hvad der er
  operationelt. Dæmpede toner til firewallede sektioner, så øjet ser at de er en
  anden slags information.
- **Båndet:** vandret interval-bar med punktestimatet markeret i den, og
  basisraten som en tydelig lodret linje der skærer igennem. Når linjen ligger
  inde i baren skal det være umiddelbart synligt hvorfor dommen lyder som den gør.
- **Lys og mørk baggrund.** Begge skal fungere.
- **Skal kunne screenshottes** og stadig give mening som ét billede i en tråd.
- **Sprog:** dansk med rigtige æ, ø og å. Kildedataene staver "baand" og "aendring"
  af konsol-hensyn — det skal ikke slå igennem i dashboardet.

## LEVERANCE

Én selvstændig HTML-fil, responsiv fra telefon til bred skærm, uden
build-værktøjer. Læser JSON'en beskrevet ovenfor. Tomme eller `null`-felter skal
håndteres uden at layoutet falder sammen — hovedbogen kan indeholde alt fra to
til mange rækker.
