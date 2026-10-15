# HOVEDBOG — prospektive læsninger

Den eneste fuldt prospektive test af modellen: hver læsning logges **før** udfaldet kendes. Den
beskytter mod look-ahead, men er statistisk svag — der kræves mange komplette konjunkturcykler, før
den kan skelne modellen fra basisraten. Hvordan rækkerne scores, står i
[BEDOEMMELSESNOEGLE.md](BEDOEMMELSESNOEGLE.md) (præregistreret 2026-10-15, før række 4).
Én række pr. måned via `python v5/motor.py --log`, i logvinduet dag 10–20. Historiske rækker
redigeres ALDRIG — heller ikke note-feltet: udfald føres i den separate, append-only
[UDFALD.csv](UDFALD.csv). Hver række har også en fuld record i [hovedbog.jsonl](hovedbog.jsonl) (fra række 4).

Dom-sproget følger Section 6-reglerne mekanisk. "Antænding" = aktive tripwires blandt
antændings-klassen. Række 1–3: kurve-inversion, Sahm, HY OAS, drawdown, advance-print, CP-spænd,
10Y, realkredit. **Fra 2026-10-15 (række 4 og frem):** kurve-inversion, Sahm, HY OAS > 600bp,
S&P-drawdown og advance-print (2 negative FØRSTE BNP-print, udledt af de arkiverede snapshots).
De tre MiroFish-sværm-tripwires (CP-spænd, 10Y, realkredit) står i motorens separate
scenarie-appendiks og indgår ikke i kolonnen — rådets grand review R3 besluttede enstemmigt, at
sværmen holdes uden for modeloutputtet, og kode-reviewet 2026-10-15 fandt, at implementeringen
modsagde det (F9/G2.2). Ingen af de tre har været aktive i række 1–3, så kolonnens historik er
uberørt. Forudsætnings-tripwires (margin, permits, realt kontantafkast) står med aktuel status i
motor-outputtets market conditions.

**Nye kolonner fra række 4** (kun fremadrettet, ligesom `kalibrering`): `vindue` (rækkens
scoringsvindue: logningsmåneden + 11 måneder), `input` (daglig trailing-vindue eller månedstal) og
`P_maanedlig` (P på publicerede GS10−TB3MS-månedstal ved samme vægte — den oprindelige serie kan
følges uden brud gennem driftsændringen 2026-09-28). En måned uden række i logvinduet skrives som
en eksplicit `ikke logget`-række. En læsning inde i en annonceret recession får dom `censureret`.
Første række under en ny bedømmelsesnøgle får noten `noegle <hash>`.

Kolonnen `kalibrering` (manifest-hash, v5.0.1 §3.3) findes kun i rækker skrevet fra og med
2026-09-19; de to ældre rækker er urørte og hører til v5.0-manifestet (se v5/kalibreringer/legacy_mapping.json).
Fra 2026-09-28 måles kurven på daglige data (trailing måned af DGS10 − DTB3 — samme statistik som
GS10/TB3MS, uden publiceringsforsinkelse), og 10Y-tripwiren i antændings-kolonnen læser seneste daglige
niveau. De to ældre rækker brugte månedstal; den første række på daglig input får noten "input: daglig".

| logget | snapshot | P | baand 10-90 | basisrate | dom | kurve | antaending aktiv | note | kalibrering | vindue | input | P_maanedlig |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-08-12 | 2026-08-12 | 20.1% | 14.4-29.2% | 18.2% | ikke skelnelig | +0.87 | ingen |  |
| 2026-09-09 | 2026-09-09 | 18.0% | 12.7-26.3% | 18.2% | ikke skelnelig | +0.96 | ingen |  |
| 2026-10-10 | 2026-10-10 | 15.1% | 10.4-21.6% | 18.0% | ikke skelnelig | +1.11 | ingen | input: daglig (kurve = trailing maaned DGS10-DTB3; foer: GS10-TB3MS maanedssnit); bro: P(v? 6baeade4)=15.0% / P(v5.0.1 72c3371d)=15.1% ved identiske inputs; trigger: manuel/reparation (foerste kalibrering efter v5.0) | 72c3371d |
