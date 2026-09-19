# MOTOR v5.0 — sandsynlighed for amerikansk recessionsstart

*A US recession-onset probability model: one feature (the 10y–3m yield curve), an
L2-logit on the NBER-onset label, purged expanding-origin walk-forward validation, and a
prospective ledger where every reading is logged before the outcome is known. Free data
only. Every failed candidate is published next to the one that survived. Documentation
is in Danish.*

Modellen estimerer P(NBER-dateret recession begynder inden for fire kvartaler). Den
operationelle model er en curve-only-logit, valgt mekanisk fordi den slog fuldmodellen i
walk-forward (+34,3 % mod +33,2 % log-loss-forbedring over basisraten). Syv
feature-kandidater er testet, publiceret og afvist; søgningen er lukket.

**Seneste læsning (2026-09-09):** P = 18,0 % [12,7–26,3 %] mod basisrate 18,2 % —
ikke skelnelig fra basisraten. Se [LOG.md](LOG.md).

## Hvor er hvad

| Fil | Indhold |
|---|---|
| [v5/README.md](v5/README.md) | Byggelog: acceptancetests, alle seks trin, vedligehold |
| [v5/](v5/) | Koden: fetch → calibrate → ablation → finalize → motor. 47 tests. |
| [LOG.md](LOG.md) | Hovedbogen — én række pr. måned, logført før udfaldet kendes. Redigeres aldrig. |
| [RAADETS_KONSENSUS.md](RAADETS_KONSENSUS.md) | Blueprintet, ratificeret 7/7 af et råd af sprogmodeller efter seks debatrunder |
| [RAADETS_REVIEW.md](RAADETS_REVIEW.md) | Grand review med 18 modeller |
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
python ablation2_nber.py --promote && python finalize6.py   # re-anker vægtene
python motor.py --log --json           # læsning, hovedbogsrække, dashboard.json
python -m unittest test_v5             # 47 tests
```

Kræver Python 3 og numpy. Intet andet.

Modellen er ikke et handelssignal og ikke investeringsrådgivning.
