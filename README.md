# MOTOR v5.0 — sandsynlighed for amerikansk recessionsstart

[![tests](https://github.com/rasmuspeterk-ctrl/recession/actions/workflows/tests.yml/badge.svg)](https://github.com/rasmuspeterk-ctrl/recession/actions/workflows/tests.yml)

*A US recession-onset probability model: one feature (the 10y–3m yield curve), an
L2-logit on the NBER-onset label, purged expanding-origin walk-forward validation, and a
prospective ledger where every reading is logged before the outcome is known. Free data
only. Every failed candidate is published next to the one that survived. Documentation
is in Danish.*

Modellen estimerer P(NBER-dateret recession begynder inden for fire kvartaler). Den
operationelle model er en curve-only-logit, valgt mekanisk fordi den slog fuldmodellen i
walk-forward (+34,3 % mod +33,2 % log-loss-forbedring over basisraten). Syv
feature-kandidater er testet, publiceret og afvist; søgningen er lukket.

**Seneste logførte læsning (2026-09-09, v5.0):** P = 18,0 % [12,7–26,3 %] mod basisrate 18,2 % —
ikke skelnelig fra basisraten. Se [LOG.md](LOG.md).

**Rekalibrering v5.0.1 (2026-09-19):** kalibreringsrygraden var frosset ved 2023 (Yales Shiller-fil), så
tre modne kvartaler manglede i fittet. Rådet ratificerede reparationen 4/4; samme inputs giver nu 17,7 %,
walk-forward-skill +27,1 % (fra +34,3 %) fordi de tre tilføjede kvartaler er 2023–24-inversionens
fejlalarmer. *"A lower or higher recalibrated probability is changed estimation, not changed economic
risk."* Detaljer: [v5/README.md](v5/README.md#v501--foerste-rekalibrering-raadets_v501md-ratificeret-44-2026-09-19).

## Hvor er hvad

| Fil | Indhold |
|---|---|
| [v5/README.md](v5/README.md) | Byggelog: acceptancetests, alle seks trin, vedligehold |
| [v5/](v5/) | Koden: fetch → calibrate → ablation → finalize → diagnostik → motor. 66 tests. |
| [LOG.md](LOG.md) | Hovedbogen — én række pr. måned, logført før udfaldet kendes. Redigeres aldrig. |
| [RAADETS_KONSENSUS.md](RAADETS_KONSENSUS.md) | Blueprintet, ratificeret 7/7 af et råd af sprogmodeller efter seks debatrunder |
| [RAADETS_REVIEW.md](RAADETS_REVIEW.md) | Grand review med 18 modeller |
| [RAADETS_V501.md](RAADETS_V501.md) | Rådets konsensus om v5.0.1 — den første rekalibrering (4/4, 19. sept. 2026) |
| [TRIGGER-ATLAS.md](TRIGGER-ATLAS.md) | Sværm-simulerede recessionskanaler og tripwires — narrativ kontekst, ikke input til P |
| [DASHBOARD-BRIEF.md](DASHBOARD-BRIEF.md) | Designregler for et dashboard der ikke kan oversælge |
| [debat/](debat/) | Fulde transkripter af rådsdebatterne |
| [mirofish-sim/](mirofish-sim/) | Sværm-simulationernes rådata og resuméer |
| [v4/](v4/) | Forgængeren |

## Principper

- Kun gratis data (FRED, Shiller, FINRA, multpl). Hashede snapshots. Ingen API-nøgler i ritualet.
- Kun walk-forward-valideret får tal. Kompleksitet skal købe skill.
- Sproget om resultatet genereres mekanisk og kan ikke blive skarpere end tallene.
- Fejlslagne forsøg publiceres ved siden af det der virkede.

## Månedsritual

```bash
cd v5
python fetch.py                        # FRED-snapshot, hashet
# opdatér manual/manual.json: CAPE, marginlån y/y, S&P vs 12-mdr-høj
python fetch.py                        # igen, så snapshottet bærer de nye manuelle tal
python motor.py --log --json           # læsning, hovedbogsrække, dashboard.json
python -m unittest test_v5             # 66 tests
```

Vægtene er frosne mellem rekalibreringer (hver september, eller når NBER daterer en ny top/bund):
`python finalize6.py && python diagnostik.py`. Se [RAADETS_V501.md](RAADETS_V501.md).

Kræver Python 3 og numpy. Intet andet.

Modellen er ikke et handelssignal og ikke investeringsrådgivning.
