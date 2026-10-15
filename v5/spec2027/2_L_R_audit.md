# Forseglet spec 2/4 — L_R-audit og eligibility fra september-refitten 2027 (RAADETS_2027 §9)

**Forseglet 2026-10-15.** Teksten er committet og pushet, FOER koden der bruger den skrives (RAADETS_2027 §12
trin 3). Koden laaser filens sha256 (LF-normaliseret) og stopper refitten hoejlydt, hvis filen er aendret
efter forseglingen. En aendring kraever en raadsbeslutning. Er spec og kode uenige, gaelder spec'en (§3.4).

Ratificeret tekst (§9, ordret):

> 9.1 The annual audit computes **L_R = max(18, max lag_peak, max lag_trough − 12)**:
> - lag_peak is measured from peak month to peak announcement;
> - lag_trough is measured from trough month to trough announcement;
> - the −12 is the label window, since an origin matures at q + 12 + L_R.
>
> Today: max(18, 12, 9) = 18.
>
> 9.2 An origin dated q, with forecast-window end H(q) = q + 12 months under the committed quarterly dating
> convention, enters `eligible_fit(R)` iff:
> 1. R ≥ H(q) + L_R; and
> 2. its censoring status is resolved using only announcement information available at R.
>
> "Age ≥ L_R" means age **since forecast-window end**, not age since origin. With L_R = 18, minimum maturity is
> therefore q + 30 months, not q + 18.
>
> 9.3 Both inequalities of §9.1 are written into the audit before it first runs. If either is breached, the
> refit halts pending a council decision. Before the first audit runs, date-stamped eligibility tests
> (including the 1991 and 2001 episodes) must verify both conditions of §9.2. The trough term is an audit
> check on censoring resolution, and a breach of the peak term halts the refit on its own (DeepSeek).

## 1. Ikrafttraeden

Auditten koerer ved hver refit med refit-maaned **R >= 2027-09** (foerste gang ved september-refitten 2027) og
erstatter da v5.0.1's top-only L_R-print (finalize6.L_R_audit, F51). En refit med R < 2027-09 koerer den gamle
audit uaendret. Den operationelle embargo L = 18 (`ablation2_nber.L_EMBARGO`) er en protokolkonstant; auditten
aendrer den aldrig, den kontrollerer den.

## 2. Datering (den committede kvartalskonvention)

- Maaneder taelles som midx = aar · 12 + (maaned − 1).
- Et origin q er et kvartal; dets dato er kvartalets sidste maaned (qend). H(q) = qend + 12.
- Annonceringsmaaned = maaneden i `announcement_date` (maanedsgranularitet, som `ablation2_nber.load_announcements`).
- lag_peak = annonceringsmaaned − `cycle_month` for hver `peak_*`-raekke i nber_announcements.csv.
- lag_trough = annonceringsmaaned − `cycle_month` for hver `trough_*`-raekke.
- Kun tabellens raekker indgaar i lag-maksimaerne. Pre-1979-episoderne har ingen annonceringer; deres
  konvention (top og bund kendt ved trough + 18, `PRE1979_TROUGH_LAG`) indgaar ikke i L_R.

I dag: max lag_peak = 12 (peak_2007), max lag_trough = 21 (trough_1991), L_R = max(18, 12, 9) = 18.

## 3. De to uligheder (§9.1/§9.3)

Med den operationelle L = 18:

- **Top-leddet:** max lag_peak <= L.
- **Bund-leddet:** max lag_trough − 12 <= L.

Er en af dem brudt, stopper refitten (SystemExit, intet skrevet) med besked om, hvilket led der er brudt, og
at raadet skal tage stilling. Et brud paa top-leddet stopper refitten alene, uanset bund-leddet (DeepSeek).
Begge led rapporteres altid hver for sig (vaerdi, raekke, graense).

## 4. Censurstatus med kun den information, der er tilgaengelig ved R (§9.2 betingelse 2)

For hver USREC-episode (onset O = foerste USREC = 1-maaned, bund T = sidste USREC = 1-maaned) bruges:

- aP = maaneden hvor toppen er kendt: peak-raekkens annonceringsmaaned (raekken matches til onset +/- 2 mdr,
  som `load_announcements`); pre-1979: T + 18.
- aT = maaneden hvor bunden er kendt: trough-raekkens annonceringsmaaned (matches til T +/- 2 mdr); pre-1979:
  T + 18; en igangvaerende episode eller en post-1979-episode uden trough-raekke: aldrig (uendelig).

Origin q's censurstatus ved R, `censur_status(q, R)`, gennemloeber episoderne kronologisk:

- episoder med aP > R (ikke annonceret ved R) eller q < O springes over;
- er aT <= R (bunden kendt): q <= T -> **"censureret"**; ellers fortsaettes (q ligger efter episoden);
- er aT > R (bunden ikke kendt ved R): -> **"aaben"** (inde i en aaben episode efter motorens aabne-episode-regel;
  status ikke afgjort);
- ingen episode rammer -> **"fri"**.

T bruges kun, naar aT <= R. Ingen information efter R indgaar.

## 5. Eligibility (§9.2)

`eligible_2027(q, R)` er sand, hvis og kun hvis

1. qend + 12 + L_R <= R (alder maalt fra vinduets slutning; minimum q + 30 mdr ved L_R = 18), OG
2. `censur_status(q, R) == "fri"` (status afgjort med information ved R og ikke censureret).

Origins med status "censureret" eller "aaben" er ude. Labelen ved R er uaendret (`ablation2_nber`): 1, hvis en
onset i (qend, qend + 12] er annonceret senest i R, ellers 0.

## 6. Hvad auditten kontrollerer ved hver refit (stop ved brud)

1. **Ulighederne** (pkt. 3).
2. **Overensstemmelse med produktionskoden.** For hvert origin i curve-only-universet og hver maaned R' fra
   1979-01 til og med refit-maaneden R skal `ablation2_nber.eligible_fit` (den kode, der fitter) give samme
   eligibility som `eligible_2027`. En konflikt er en uoverensstemmelse mellem spec og kode (§3.4): refitten
   stopper, og konflikten (origin, R') rapporteres til raadet.
3. **Finalitet (ingen tilbagevirkende redigering).** For hver maaned R' i samme interval og hvert origin, der er
   modent ved R' (qend + 12 + L_R <= R'), skal (eligibility, label) ved R' vaere lig (eligibility, label) ved R.
   Et brud betyder, at en moden raekke er blevet redigeret efter modning (Fable R2) — refitten stopper.

Intervallet starter 1979-01, fordi tabellens annonceringer starter dér; foer 1979 gaelder trough + 18-konventionen,
som per konstruktion giver provisoriske nuller (ablation2's flips) og ikke er en annonceringsforsinkelse.

## 7. Hvor det skrives

Manifestets `L_R_audit` (uden for indholds-hashen, som i dag) faar: `protokol` ("RAADETS_2027 §9"), `spec_sha256`,
`L_embargo`, `L_R`, `top_led` (max lag, raekke, ok), `bund_led` (max lag, max lag − 12, raekke, ok),
`konflikter` (antal + de foerste 10), `finalitetsbrud` (antal + de foerste 10), `interval`, `ok`.
finalize6 printer een linje pr. led og resultatet af kontrol 2 og 3.

## 8. Datostemplede tests (skal bestaa, foer auditten koerer foerste gang)

Med den rigtige annonceringstabel og USREC fra det committede snapshot. For hver af episoderne 1990-91, 2001
og 1980-81 (dobbeltdyk, Kimi):

- **Graensetest paa alder (Fable):** et origin, der modnes, er ude ved R = qend + 12 + L_R − 1 og inde ved
  R = qend + 12 + L_R; ude ved R = qend + 18 (alder maalt fra origin — Sols fejl ville have lukket det ind 12
  maaneder for tidligt).
- **Negativ kontrol paa censurering (Fable):** et origin inde i episoden er "aaben" ved hver R fra
  topannonceringen til maaneden foer bundannonceringen og "censureret" fra bundannonceringen; det er aldrig
  eligible.
- **Afgoerelse ved bundannonceringen:** et origin lige efter bunden er "aaben" ved R = aT − 1 og "fri" ved R = aT.
- **Labels ved modning:** et positivt origin foer toppen har label 1 ved modning (toppen er annonceret); et
  origin efter bunden har den label, den endelige kronologi giver.
- Konkret: 1990Q1 (pos.), 1990Q4 og 1991Q1 (inde), 1991Q2 (efter bunden); 2000Q2 (pos.), 2001Q2 og 2001Q3
  (inde), 2001Q4 (efter bunden); 1980Q1 og 1980Q2 (inde i 1980), 1980Q3 og 1981Q2 (efter 1980-bunden, label 1 fra
  1981-onsettet), 1981Q3 (inde i 1981-82), 1982Q4 (efter 1982-bunden).
- Auditten paa det committede snapshot: L_R = 18, begge led ok, 0 konflikter, 0 finalitetsbrud.
- Et syntetisk brud paa hvert led (en top-raekke med lag 19; en bund-raekke med lag 31) stopper refitten, og
  top-bruddet stopper den, selv naar bund-leddet er ok.
