# HOVEDBOG — prospektive læsninger

Den eneste ægte out-of-sample-eksamen: hver læsning logges **før** udfaldet kendes.
Én række pr. måned via `python v5/motor.py --log`. Historiske rækker redigeres ALDRIG
(kun note-feltet må udfyldes bagefter, fx når NBER senere daterer en onset).

Dom-sproget følger Section 6-reglerne mekanisk. "Antænding" = aktive tripwires blandt
antændings-klassen (kurve-inversion, Sahm, HY OAS, drawdown, advance-print, CP-spænd,
10Y, realkredit); forudsætnings-tripwires (margin, permits, realt kontantafkast) står
i motor-outputtets market conditions.

Kolonnen `kalibrering` (manifest-hash, v5.0.1 §3.3) findes kun i rækker skrevet fra og med
2026-09-19; de to ældre rækker er urørte og hører til v5.0-manifestet (se v5/kalibreringer/legacy_mapping.json).

| logget | snapshot | P | baand 10-90 | basisrate | dom | kurve | antaending aktiv | note | kalibrering |
|---|---|---|---|---|---|---|---|---|---|
| 2026-08-12 | 2026-08-12 | 20.1% | 14.4-29.2% | 18.2% | ikke skelnelig | +0.87 | ingen |  |
| 2026-09-09 | 2026-09-09 | 18.0% | 12.7-26.3% | 18.2% | ikke skelnelig | +0.96 | ingen |  |
