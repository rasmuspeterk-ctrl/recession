# Forseglet spec 7A — 3m-benet paa obligationsaekvivalent basis: en uscoret diagnostik ved refitten (RAADETS_SPEC7 §1)

**Forseglet 2026-10-27.** Teksten er committet og pushet, FOER koden der bruger den skrives (RAADETS_2027 §12
trin 3). Koden laaser filens sha256 (LF-normaliseret) og stopper hoejlydt, hvis filen er aendret efter
forseglingen. En aendring kraever en raadsbeslutning. Er spec og kode uenige, gaelder spec'en (RAADETS_2027 §3.4).

Ratificeret tekst (ordret, RAADETS_SPEC7.md §1, 7/7 i runde 4 den 2026-10-27):

> 1.1 An **unscored diagnostic**, published whatever it shows. Never in P, band, verdict, gate or trigger.
> 1.2 Series: "91-day BEY proxy", BEY(d) = 100·365·(d/100) / (360 − 91·(d/100)), d in percent. History: BEY(TB3MS).
> Live leg: each DTB3 day converted, then averaged over the trailing window. Robustness, printed once: the
> convert-after-averaging operator on both, and the Jensen bound (≤ 0.003 pp at within-month σ = 1 pp). The 10y leg
> and the pre-GS10 backbone are unchanged. GS3M (from 1981-09) is a reported check only (mean and max |BEY(TB3MS) −
> GS3M|), never spliced. The converted curve is still not unit-consistent with the semiannual par 10y CMT; the spec
> says so.
> 1.3 Outputs, into `diagnostik.json` → `uscorede.konvention_bey`, with the sha256 of inputs and the code commit:
> (1) curve-only fit on the BEY proxy, λ = 1, identical eligible origins and labels (identity asserted, fails loudly);
> (2) walk-forward in §1.2 order, oracle-free first; (3) the paired difference BEY − discount on identical origins,
> episode-block bootstrap with 4.4's cycle blocks, **10,000 draws, seed 42, 5th–95th percentiles** (primary), the
> 10th–90th from the same draws printed and labelled "80 % interval"; (4) a rate-bin table (TB3MS < 4, 4–8, 8–12,
> ≥ 12 %) with onset counts, fitted α and β, and origin-level paired log-loss and probability differences;
> (5) P at the refit's live input under the BEY proxy — **written to diagnostics only; never rendered on the
> dashboard, in LOG.md or hovedbog.jsonl**.
> 1.4 Decision: **no pre-committed switch and no outcome trigger.** Part A's output is an **unconditional agenda
> item** of the 2027 refit council, which decides the convention with both configurations' replays, the rate bins
> and calibration in hand. Any later switch needs its own sealed replay (§1.3) and takes effect from a refit.
> 1.5 Claude's prior, recorded in the spec's §0 only and never printed beside the result: |Δ_OF| < 2 pp —
> "author's prior, not a criterion".
> 1.6 Post hoc: acceptable — unconditional, unscored, cannot select a configuration.

## 0. Hvad der var kendt ved forseglingen

- Konventionsgabet BEY(d) − d er niveauafhaengigt: 0,02pp ved d = 1 %, 0,10 ved 4 %, 0,18 ved 6 %, 0,28 ved 8 %,
  0,40 ved 10 %, 0,55 ved 12 %, 0,81 ved 15 % (ren regning, beregnet foer forseglingen). Fire af de tolv onsets
  (1970, 1973, 1980, 1981) ligger i hoejrente-aarene.
- I live-vinduet 2026-09-24..10-23 er DGS10 − DTB3 = +1,124pp og DGS10 − DGS3MO (CMT) = +0,949pp.
- Jensen-graensen: BEY er konveks (f'' ca. 0,51 i decimalenheder ved 4 %); BEY(middel d) − middel BEY(d) er under
  0,003pp selv ved en spredning inden for maaneden paa 1pp.
- **Forfatterens prior, ikke et kriterium** (Claude, 2026-10-27): |Δ oracle-fri walk-forward| < 2pp. Den printes
  aldrig ved resultatet.
- IKKE set: noget fit, nogen walk-forward, noget skill- eller P-tal paa den omregnede serie.

## 1. Ikrafttraeden og status

Beregnes af diagnostik.py for kalibreringer med refit-maaned **R >= 2027-09** (`protokol2027.IKRAFT`). Foer det
skrives intet af nedenstaaende. Feltet `uscorede.konvention_bey` staar uden for manifestets indholds-hash. Det
indgaar aldrig i P, baand, dom, gate, trigger eller hovedbogens antaendingskolonne, og intet af det vises paa
dashboardet ud over en henvisning til, at diagnostikken findes.

## 2. Serien

- **Omregning (fastlaast):** `protokol2027.bey(d)` = 100·365·(d/100) / (360 − 91·(d/100)), d i procent, fast
  loebetid 91 dage.
- **Historik:** hver maaneds TB3MS omregnes, FOER den maanedlige kurve og kvartalsaggregeringen bygges
  (`calibrate.build_monthly`/`ablation2_nber.build_dataset` med TB3MS erstattet af BEY(TB3MS)). 10-aars-benet
  (GS10; Shillers LTR foer GS10) er uaendret. Universet, origins, labels og eligibility er de samme som for den
  operationelle kurve; identiteten asserteres og fejler hoejlydt.
- **Live:** hver DTB3-dag i det trailing vindue omregnes, derefter tages middelvaerdien.
- **Robusthed (printes een gang, er ikke et kriterium):** omregning EFTER middelvaerdien (BEY af vinduets middel
  DTB3; BEY af kvartalets middel TB3MS) og den maalte forskel mod hovedoperatoren.
- **Kontrol (rapporteres, er ikke et kriterium):** fra 1981-09, middel og max af |BEY(TB3MS) − GS3M| pr. maaned.
  GS3M splejses aldrig ind.
- **Enheder:** den omregnede kurve er stadig ikke enhedskonsistent med 10-aars-benet (semiannual par CMT); en
  simpel ACT/365-rente mod en semiannual par-rente. Det skrives i outputtet.

## 3. Outputs (`diagnostik.json` → `uscorede.konvention_bey`)

Med sha256 af inputfilerne (TB3MS, DTB3, GS10, DGS10, GS3M, USREC, annonceringstabellen) og kode-committen.

1. **Fit:** curve-only paa BEY-proxyen, λ = 1, `calibrate.fit` som det operationelle fit; mu, sd, w (4 decimaler),
   n_obs, n_pos.
2. **Walk-forward** i §1.2-raekkefoelgen: oracle-fri fast λ foerst, derefter orakel-censureret fast λ.
3. **Parret forskel** BEY − diskonto paa identiske origins (begge varianter): per-origin log-loss-forskel mod den
   poolede basisrate, episode-blok-bootstrap med 4.4's cykelblokke (`diagnostik.blok_af`), **10.000 traek, seed
   42, 5.–95. percentil** (primaert); 10.–90. percentil fra samme traek printes og kaldes "80 %-interval".
   Flere traek mindsker Monte Carlo-stoej, ikke usikkerheden fra faa episoder.
4. **Rentebin-tabel** (TB3MS < 4, 4–8, 8–12, >= 12 %): antal origins og onsets pr. bin, origin-niveau parret
   log-loss- og P-forskel pr. bin, og fittede α og β pr. bin. **Bin-fittene er beskrivende og uden inferens**:
   de hoeje bins rummer i praksis 1973 og 1980–81 og er naesten uidentificerede. De er ikke et vaegtforslag; et
   regime-afhaengigt β er en ny model og kraever egen forseglet spec og replay.
5. **P ved refittens live-input under BEY-proxyen**, maerket "uscoret foelsomhed, ikke P". Skrives KUN til
   diagnostik.json. Det vises aldrig paa dashboardet, i LOG.md eller i hovedbog.jsonl, og motor printer det ikke.

## 4. Beslutningen

Ingen forudbestemt skifteregel og ingen udloeser. Del A's output er et **ubetinget dagsordenspunkt** for
raadet ved refitten 2027, uanset stoerrelsen. Det raad beslutter konventionen med begge konfigurationers replay,
rentebins og kalibrering i haanden; det kan ogsaa veje enhedskonsistens som et maaleargument. Et senere skift
kraever den nye konfigurations egen forseglede replay (RAADETS_2027 §1.3) og gaelder fra en refit.
