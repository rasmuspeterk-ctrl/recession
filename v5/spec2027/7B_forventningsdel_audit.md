# Forseglet spec 7B — kurvens forventningsdel: ingen historisk test, prospektiv revisionsaudit (RAADETS_SPEC7 §2)

**Forseglet 2026-10-27.** Teksten er committet og pushet, FOER koden der bruger den skrives (RAADETS_2027 §12
trin 3). Koden laaser filens sha256 (LF-normaliseret) og stopper hoejlydt, hvis filen er aendret efter
forseglingen. En aendring kraever en raadsbeslutning. Er spec og kode uenige, gaelder spec'en (RAADETS_2027 §3.4).

Ratificeret tekst (ordret, RAADETS_SPEC7.md §2, 7/7 i runde 4 den 2026-10-27):

> 2.1 **No historical test.** B1/B2 are not run and are deleted from the spec text. Reason, verbatim in §0: "The idea
> was tested once (v5.0 blueprint section 5, run in step 4: dLL −77.88 pp, dBrier −30.82 pp, 192 paired origins,
> 0 % positive folds). That result is on an implementation — inside F5, with a pre-1961 base-rate penalty, the
> secondary truncated comparison never run — not on the hypothesis; it is not evidence for or against the
> expectations component. The historical search nevertheless stays closed: the result has been seen, a redesign
> could now be aimed around it, and with 8 onsets since 1961 MDE80 ≈ 30 pp." No reliance on §8.2 by analogy.
> 2.2 **B3 — prospective, unscored, audit first.** Series: Kim-Wright `THREEFYTP10` only; E = (y10 − TP) − 3m. ACM
> appears only as a dated secondary series in the audit report, never as a live line. [audit] Vintages: the monthly
> ledger snapshots (each already stores the full THREEFYTP10 history with its sha256 in `meta.json`), **12
> consecutive**, counted from the first ledger row after sealing; earlier snapshots may be reported but do not count.
> For every date in the trailing 24 months of vintage 1: median and max |revision| of TP and of E from vintage 1 to
> each later vintage, in pp; missing dates reported, not imputed.
> 2.3 An unscored ledger column carrying the bare E (no sentence beside it) opens only if **both** (i) max |revision
> of E| < 10 bp — an administrative **display-stability** bar, explicitly not evidence of validity — and (ii) the
> council signs off after the 12th vintage. A scored evaluation needs ≥ 2 onsets after sealing (decades) and its own
> sealed spec; no pre-2027 observation is ever evidence.
> 2.4 Post hoc: acceptable — prospective, unscored, no historical evidence claimed.

## 0. Hvorfor der ikke er nogen historisk test

"The idea was tested once (v5.0 blueprint section 5, run in step 4: dLL −77.88 pp, dBrier −30.82 pp, 192 paired
origins, 0 % positive folds). That result is on an implementation — inside F5, with a pre-1961 base-rate penalty,
the secondary truncated comparison never run — not on the hypothesis; it is not evidence for or against the
expectations component. The historical search nevertheless stays closed: the result has been seen, a redesign
could now be aimed around it, and with 8 onsets since 1961 MDE80 ≈ 30 pp."

Kendt ved forseglingen: Kim-Wright 2026-10-16 TP 0,99, forventet 4,10; ACM 2026-07 TP 0,84. Litteraturens
retning (Rosenberg & Maurer 2008) er kendt. Ingen revision af nogen TP-serie er beregnet.

## 1. Serien (fastlaast regnestykke)

- **TP:** `THREEFYTP10` (Kim-Wright, Fed Board, daglig, public domain), som snapshottet gemmer den.
- **E(t) = (DGS10(t) − TP(t)) − DTB3(t)**, alle tre paa samme dato t (ingen fremfoering). En dato, hvor et af de
  tre mangler, indgaar ikke og taelles i rapporten. 3m-benet er DTB3 paa diskontobasis (den operationelle
  konvention ved forseglingen); skifter raadet konvention efter spec 7A, beslutter samme raad, om auditten foelger.
- **Revision af E holder markedsrenterne faste:** DGS10 og DTB3 tages fra aargang 1 for alle sammenligninger,
  saa en revision af E er revisionen af TP med modsat fortegn paa de datoer, hvor E er defineret. En eventuel
  revision af DGS10/DTB3 mellem aargange rapporteres separat og indgaar ikke i E-revisionen.
- **ACM** (`ACMTP10`, NY Fed, maanedlig) optraeder kun som en dateret sekundaer serie i auditrapporten; aldrig som
  en live-linje og aldrig som en "modeluenighed" paa umatchede datoer.

## 2. Auditten

- **Aargange:** hovedbogens maanedlige snapshots (hver raekkes snapshot gemmer hele THREEFYTP10-historikken med sin
  sha256 i `meta.json`). Aargang 1 er snapshottet bag den foerste hovedbogsraekke logget efter forseglingen
  (2026-11-raekken); derefter de 11 foelgende raekkers snapshots, **12 i traek**. Mangler en maaneds raekke,
  starter taellingen forfra. Snapshots foer forseglingen (2026-08-09..2026-10-27) kan rapporteres, men taeller ikke.
- **Sammenligningssaet:** hver dato t i aargang 1's sidste 24 maaneder (fra aargang 1's sidste dato minus 24
  maaneder til og med den sidste dato). For hver senere aargang k = 2..12 og hver t i saettet: |TP_k(t) − TP_1(t)|
  og |E_k(t) − E_1(t)| i pp. Datoer, der mangler i aargang k, rapporteres, imputeres ikke.
- **Rapport** (`analyser/b3_revisionsaudit.py` → `analyser/b3_revisionsaudit_resultat.json`, med alle aargangenes
  sha256): pr. aargang median og max |revision| af TP og E; samlet max over alle datoer og alle aargange; antal
  manglende datoer; ACM som dateret sekundaer serie.

## 3. Aabning af en uscoret kolonne

Kolonnen (den bare E, ingen tekst ved siden af) aabner kun, hvis **begge** gaelder:
1. det samlede max |revision af E| over alle datoer i sammenligningssaettet og alle aargange 2..12 er **under
   0,10pp** — et administrativt **visningsstabilitetskrav**, udtrykkeligt ikke evidens for validitet. Graensen er
   valgt uden revisionsdata; et senere raad kan aendre den, foer en kolonne aabner, men aldrig efter;
2. raadet godkender efter 12. aargang. Den samme godkendelse afgoer, om den firewallede kontekstblok maa vise E;
   uden godkendelse staar blokken som i RAADETS_SPEC7 §3.6.

Bestaaes kravet ikke, publiceres auditten, og ingen kolonne aabner. En scoret evaluering kraever mindst 2 onsets
efter forseglingen og sin egen forseglede spec; ingen observation foer 2027 bruges nogensinde som evidens.
