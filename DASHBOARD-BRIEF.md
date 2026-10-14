# MOTOR v5.0.1 — dashboard-brief

Fast skabelon til den månedlige læsning. Kopiér alt under stregen ind i det
designværktøj du bruger, og vedhæft månedens data (se Datakontrakt).

Opdateres kun når `motor.py`'s output-struktur ændres.

---

## KONTEKST — læs først, reglerne følger af den

Du skal designe et månedligt dashboard for MOTOR v5.0.1, en model der estimerer
sandsynligheden for at en amerikansk recession (NBER-dateret) *begynder* inden
for de næste fire kvartaler.

Det afgørende ved denne model: **den er ærlig om at den næsten ikke kan noget.**
Den er en logistisk regression på én eneste variabel — rentekurven (10-årig minus
3-måneders). Den er kalibreret på 267 kvartaler med kun 12 recessionsstarter. Dens
værste fejlalarm i historisk test var 93,8 % sandsynlighed for en recession der
aldrig kom. Ved den seneste logførte læsning (10. oktober 2026) sagde den 15,1 % mod
en basisrate på 18,0 %, og båndet indeholdt basisraten — altså: den ved reelt ikke
mere end at tælle hvor ofte recessioner sker.

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
Struktur (eksempel: 10/10-2026-læsningen, forkortet):

```json
{
  "version": "5.0.1",
  "manifest_hash": "72c3371d",
  "forrige_manifest": "6baeade4",
  "raa": {"beta_curve_pr_pp": -1.2948, "alpha": -0.2915},
  "bro": {"trin": {"i_legacy_rygrad": {"P": 0.1804}, "ii_korrigerede_kilder_samme_origins": {"P": 0.1804},
                   "iii_udvidet_panel": {"P": 0.1773}}, "saetning": "A lower or higher recalibrated probability is changed estimation, not changed economic risk."},
  "gate": {"curve_only_wf": 27.05, "fuldmodel_wf": 23.16, "forskel_pp": -3.89, "mde_pp": 4.42, "fuldmodel_slaar": false},
  "diagnostik": {"episode_tabel": "...", "loeo": "...", "domsregler_backtest": "...", "oracle_fri": "..."},
  "live_input": {"kilde": "daglig", "vindue": ["2026-09-09", "2026-10-08"], "n_dage": 22, "curve": 1.1059, "p_maanedlig": 0.160963},
  "trigger": "manuel/reparation (foerste kalibrering efter v5.0)",
  "delta_vs_forrige": {"max_abs_dP": 0.0779, "origin_max": "1974Q1", "mean_abs_dP": 0.0173},
  "stale": null,
  "snapshot": "2026-10-10",
  "snapshot_hash": "4397dbc136",
  "model": "curve-only-logit",
  "label": "NBER-onset inden 4 kvartaler",
  "kalibreret": "2026-09-19",
  "n_obs": 267,
  "n_episoder": 12,
  "wf_log_loss": 27.05,
  "wf_brier": 24.15,

  "p": 0.151424,
  "baand": [0.104202, 0.216084],
  "basisrate": 0.1798,
  "baand_udelukker_basisrate": false,
  "ratio": null,
  "baand_fodnote": "Not a predictive interval; reflects weight sensitivity to episode composition",
  "dom": "P er 15.1% mod basisraten 18.0%, men baandet [10.4-21.6%] indeholder basisraten: IKKE SKELNELIG FRA BASISRATEN.",

  "inputs": [
    {"navn": "Rentekurve 10y-3m", "vaerdi": 1.1059, "z": -0.2326, "operationel": true},
    {"navn": "Realrente 10y-CPI", "vaerdi": 1.7144, "z": -0.0208, "operationel": false}
  ],

  "benchmarks": [
    {"navn": "intercept (basisrate)", "wf": 0.0, "live_p": 0.1798, "status": null},
    {"navn": "curve-only-logit (NY Fed-stil-bm.)", "wf": 27.05, "live_p": 0.151424, "status": "OPERATIONEL"},
    {"navn": "fuldmodel (5 features)", "wf": 23.16, "live_p": 0.067481, "status": "testet, ikke bestaaet mod benchmark (trin 6; genkoert v5.0.1)"}
  ],

  "monitors": [
    {"navn": "Kurven inverteret", "tilstand": "inaktiv", "vaerdi": "+1.11pp", "klasse": "operationel feature"},
    {"navn": "Claims-momentum", "tilstand": "kontekst", "vaerdi": "4u-snit 198k; 12m -14.3% (maanedssnit 2026-09)", "klasse": "testet, ikke bestaaet (trin 4)"},
    {"navn": "CP-spaend 3m > 75bp", "tilstand": "inaktiv", "vaerdi": "3bp (2026-10-06)", "klasse": "svaerm-tripwire: funding-stress foer kreditspaend"}
  ],

  "market_conditions": [{"navn": "CAPE-percentil (expanding)", "vaerdi": "92.7. pct"}],
  "pengepolitik":      [{"navn": "Fed funds (effektiv)", "vaerdi": "3.88% (2026-10-08, DFF dagligt)"}],

  "advarsler": {
    "vaerste_fejlalarm": {"p": 0.9383, "origin": "2023Q2"},
    "sti_advarsel": "Modellen laeser kurvens NIVEAU; +1.11pp behandles som +1.11p…",
    "eksogen": "Eksogene chok kan ikke forudsiges."
  },

  "hovedbog": [
    {"logget": "2026-08-12", "snapshot": "2026-08-12", "P": "20.1%", "baand": "14.4-29.2%", "basisrate": "18.2%", "dom": "ikke skelnelig", "kurve": "+0.87", "antaending": "ingen", "note": "", "kalibrering": "", "p_tal": 0.201, "baand_tal": [0.144, 0.292], "basisrate_tal": 0.182, "kurve_tal": 0.87},
    {"logget": "2026-10-10", "snapshot": "2026-10-10", "P": "15.1%", "baand": "10.4-21.6%", "basisrate": "18.0%", "dom": "ikke skelnelig", "kurve": "+1.11", "antaending": "ingen", "note": "input: daglig (…); bro: …; trigger: …", "kalibrering": "72c3371d", "p_tal": 0.151, "baand_tal": [0.104, 0.216], "basisrate_tal": 0.18, "kurve_tal": 1.11}
  ]
}
```

`version`/`manifest_hash` viser hvilken kalibrering læsningen bygger på; hovedbogsrækker fra v5.0.1 bærer
samme hash i feltet `kalibrering` (ældre rækker har feltet tomt — vis dem uden). `bro` findes efter en
rekalibrering: `bro.trin` har tre trin (i legacy-rygrad, ii korrigerede kilder, iii udvidet panel) med P ved
samme faste input; vis dem side om side, aldrig som "før/efter-forbedring". `gate`, `trigger`,
`delta_vs_forrige` og `stale` er proveniens om kalibreringen og data (gate-udfaldet, hvad der udløste
kalibreringen, hvor meget den flyttede historiske P, evt. forældede serier) — valgfri kontekst.
`diagnostik` er valgfri kontekst: episode-tabellen må tegnes, men aldrig sammenfattes til én score.
`live_input` fortæller hvilke data kurven er målt på (`kilde`: daglig/månedlig, `vindue`) og bærer
`p_maanedlig` — P på de publicerede månedstal. Vis inputvinduet ved læsningen; `p_maanedlig` må vises som
en lille sammenligningslinje, aldrig som et alternativt hovedtal.

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
   `klasse` er fritekst; gruppér på leddet før kolon/parentes (operationel feature /
   testet, ikke bestaaet / svaerm-tripwire / uvalideret / ineligible / fuldmodel-feature).
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
  af konsol-hensyn — det skal ikke slå igennem i dashboardet. Det gælder også `dom`:
  translitteration (aa→å, ae→æ, oe→ø) og dansk talformat (15,1 %) er de eneste tilladte
  ændringer af den ordrette tekst (regel 7).

## LEVERANCE

Én selvstændig HTML-fil, responsiv fra telefon til bred skærm, uden
build-værktøjer. Læser JSON'en beskrevet ovenfor. Tomme eller `null`-felter skal
håndteres uden at layoutet falder sammen — hovedbogen kan indeholde alt fra to
til mange rækker.
