# MOTOR v4.0 — FINAL, 8. august 2026

## Brug
```
python3 MOTOR.py
```
Opdater seks tal i INPUT-blokken øverst. Én gang om måneden, ~5 min.

| Input | Kilde | Nu |
|---|---|---|
| y10 | FRED DGS10 | 4,40% |
| tb3m | FRED TB3MS | 3,73% |
| cpi_yoy | BLS | 3,50% |
| cpi_yoy_1 | BLS, forrige år | 2,70% |
| spx_vs_hi | markedet | 0,00 |
| cape | multpl.com/shiller-pe | 42,0 |

## Aflæsning nu
```
P(recession 12 mdr)   8,8%   (basisrate 13,4% -> 0,66x)
P(recession  9 mdr)   9,4%
Recessions-flag       0/4
Repricing-flag        3/3
Debaserings-flag      1/1
```

## Kalibrering
359 kvartaler, 11 episoder, 1947-2024.
Shiller 1871-2026 + US Treasury TB3MS 1934-2026 + BEA real BNP.
Walk-forward fra 1960. Modellen ser aldrig fremtiden.
Log-loss forbedring +22,9%. Brier-skill +19,4%.

## Hvad der er valideret
LAG 1 (recession) — ja.
LAG 2-4 — nej. Tjeklister, ikke tal.

## Løst i denne version
Uenigheden 8,6% vs 44,2% (model vs analogmetode) er afgjort.
Inversions-eftervirkningen betyder noget FØRST over score 1,0.
Vi er på 0,68 -> 14% historisk, mod basisrate 13%.
Som model-feature gjorde den resultatet DÅRLIGERE (+22,9% -> +18,8%).
Derfor: separat tjek, ikke feature.

## Eneste trigger med bevist ledetid
Rentekurven under nul. Nu +0,67pp. Afstand 67bp.

## Filer
MOTOR.py     kør denne
curve.py     hovedkalibrering
inv.py       inversionstesten
ni.py        horisont-dekomponering
hvorhen.py   analogmetoden
vaerdi.py    CAPE-analyse
tjek.py      CAPE-korrektion
real.py      første ægte-data-kørsel (uden kurve)
diag/loop/minimal/motor_v3  arkiv, fejlede modeller
data/        alle rådata
