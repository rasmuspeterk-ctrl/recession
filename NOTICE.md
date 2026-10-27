# NOTICE — hvad der er licenseret hvordan

Indført 2026-10-15 (kode-review F21). Repoet indeholder tre slags materiale, og de har forskellige vilkår.

| Materiale | Vilkår |
|---|---|
| **Kildekode** (`*.py`, `.github/workflows/*`) | MIT — se [LICENSE](LICENSE). |
| **Egen tekst og egne resultater** (README'er, LOG.md, BEDOEMMELSESNOEGLE.md, UDFALD.csv, hovedbog.jsonl, RAADETS_*.md-sammenfatningerne, REVIEW-2026-10-15.md, DASHBOARD-BRIEF.md, TRIGGER-ATLAS.md, `v5/*_resultat.json`, `v5/kalibreringer/`, `v5/analyser/`, `dashboard.json`) | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) — kreditér "Rasmus Kristensen, MOTOR (github.com/rasmuspeterk-ctrl/recession)". |
| **Tredjepartsdata** (`v5/data/raw/**`, `v5/manual/**`) | **Ikke** omfattet af MIT eller CC BY. Hver kilde er underlagt sine egne vilkår — se "Datakilder og vilkår" i [README.da.md](README.da.md) (på engelsk: "Data sources and terms" i [README.md](README.md)). Licensbegrænsede kilder (ICE BofA HY OAS, S&P 500, Moody's Baa, multpl.com-siden) committes ikke; deres hash står i hvert snapshots `meta.json`. Afledte månedstal i `spine.csv` er gengivet med kildeangivelse (data courtesy of Robert J. Shiller; S&P 500 via FRED). |
| **Modelgenereret tekst** (`debat/**`, `mirofish-sim/**`) | Output fra tredjeparts sprogmodeller (via OpenRouter og MiroFish) gengivet som dokumentation af rådsdebatterne og sværm-simulationerne. Ejerskab og vilkår følger de respektive modeludbyderes betingelser; **ikke** omfattet af MIT eller CC BY. Rasmus' egne prompts og sekretærsammenfatninger i disse mapper er CC BY 4.0. |

Intet i repoet er investeringsrådgivning. Modellen er ikke et handelssignal.

Spørgsmål om rettigheder, eller en anmodning om at fjerne materiale: opret et issue på GitHub. Licensbegrænsede filer,
der ligger i git-historikken fra før 2026-10-15, fjernes efter fremgangsmåden i v5/README.md ("Historik og
licensbegrænsede filer"), hvis en rettighedshaver anmoder om det.
