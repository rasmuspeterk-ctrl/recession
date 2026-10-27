# UDKAST (ikke forseglet) — spec 7: rentekonventionen og kurvens forventningsdel

**Skrevet 2026-10-27 efter to eksterne reviews. Forslag til raadet foer september-refitten 2027.**
Udkastet er hverken ratificeret eller forseglet, og ingen kode bruger det. Indtil raadet har taget stilling,
beregnes intet af det nedenstaaende (ingen fit, ingen walk-forward, intet P). Ratificerer raadet en del, flyttes
den ordret til `spec2027/7_<navn>.md`, forsegles (sha256 i `protokol2027.SPECS`) og pushes foer koden
(RAADETS_2027 §12 trin 3). Del A er en foelsomhed paa den operationelle feature; del B er en ny feature og
kraever derfor raadets mandat og en symmetrisk bar fastlagt foer koersel (RAADETS_2027 §5.2).

## 0. Hvad der var kendt, da udkastet blev skrevet (kontaminationserklaering)

- **Konventionsgabet.** I live-vinduet 2026-09-24..2026-10-23 (21 dage) er DGS10 − DTB3 = +1,124pp
  (modellens input) og DGS10 − DGS3MO = +0,949pp (FRED's T10Y3M-konvention); gabet er 0,175pp i snit.
  P ved de frosne vaegte paa +0,949pp (ca. 17,9 %) er set i et review. Det er ikke en gyldig sammenligning,
  fordi vaegtene er estimeret paa diskontobasis, og det indgaar ikke i nogen del af testen.
- **Kurvens sammensaetning.** Kim-Wright 2026-10-16: 10Y 5,09 = term-praemie 0,99 + forventet 4,10.
  Forventningsdelen minus 3m er +0,02pp mod DTB3 og −0,16pp mod DGS3MO samme dag.
- **Litteraturen.** Rosenberg & Maurer (2008, FRBNY Economic Policy Review) finder, at forventningsdelen af
  spaendet forudsiger recessioner, mens term-praemien ikke goer. Resultatet er kendt og er motivationen for
  del B; testen kan ikke vaere blind for det.
- **Ideen er testet foer.** Blueprintets sektion 5 ("ACM som een forseglet test", koert i trin 4,
  `ablation4_features.py`) erstattede kurven med curve_adj = (y10 − ACMTP10) − tb3m, altsaa praecis
  forventningsdelen, i 5-feature-modellen paa fuld sti. Resultat: −77,9pp log-loss (192 parrede origins, 0 % positive folds),
  ADOPTERET = False. Tabet skyldes primaert straffen for de manglende aar foer 1961 og den korte faelles
  historik (README trin 4), men tallet er set, og ACM staar paa listen over lukkede soegninger.
- **IKKE set:** noget fit, walk-forward-, skill- eller P-tal under nogen af konfigurationerne nedenfor,
  herunder en univariat forventningsdel paa et panel fra 1961.

## A. Foelsomhed: 3m-benet paa obligationsaekvivalent basis

**Formaal.** Maale, om kalibreringens diskonto-konvention (TB3MS; live DTB3) flytter vaegte, skill eller P.
Det er ikke en feature-soegning: samme feature (kurven), samme label, samme univers og samme origins; kun
3m-benets konvention aendres.

**Konvertering (fastlaast).** For hver diskontorente d (i procent; maanedlig TB3MS og daglig DTB3):

  BEY(d) = 100 · 365 · (d/100) / (360 − 91 · (d/100))

med fast loebetid 91 dage. 10-aars-benet og rygraden foer GS10 er uaendrede. Kurve_BEY = 10y − BEY(3m).

**Kontrol (rapporteres, er ikke et kriterium).** Fra 1981-09, hvor GS3M findes: middel og max af
|BEY(TB3MS) − GS3M| pr. maaned. CMT og konverteret diskonto er ikke identiske (forskellige papirer og
maalemetoder); afvigelsen skal staa ved resultatet.

**Hvad der beregnes ved refitten (R >= 2027-09).** Af diagnostik.py, i `diagnostik.json` under
`uscorede.konvention_bey` (uden for manifestets indholds-hash, aldrig i P, baand eller dom):
1. Fit af curve-only paa Kurve_BEY med samme λ = 1, samme berettigede origins og samme labels. Identiteten
   asserteres og fejler hoejlydt: samme origin-maengde, 0 label-uenigheder.
2. Walk-forward i §1.2's raekkefoelge: oracle-fri fast λ foerst, derefter orakel-censureret.
3. Den parrede forskel BEY − diskonto paa identiske origins, episode-blok-bootstrap (1000 traek, seed 42),
   10–90 %-interval.
4. P ved refittens live-input under BEY-konfigurationen (trailing maaned af DGS10 − BEY(DTB3)), maerket
   "uscoret foelsomhed, ikke P".

**Beslutningsregel (fastlagt foer koersel).** Resultatet publiceres uanset udfald. Konventionen skiftes
aldrig automatisk. Et skift er en raadsbeslutning og maa ikke begrundes med skill-tallet alene; tallene
tilhoerer den konfiguration, der producerede dem (§1.3). Vaelger raadet BEY, gaelder det fra en senere
refit med sin egen forseglede replay.

## B. Kurvens forventningsdel (kraever mandat, §5.2; ideen er allerede testet og afvist een gang)

**Udkastets anbefaling er B3 nedenfor**, ikke en ny historisk test. En ny test af en idé, der er testet og
afvist, er et andet skud paa samme maal; det er netop den forking-paths-risiko, som lukningen af
feature-soegningen skulle forhindre. B1/B2 staar her kun, fordi ACM-testen blandede to ting: ideen
(forventningsdelen) og panelet (straffen foer 1961 i 5-feature-modellen). Vil raadet adskille dem, er
B1/B2 den eneste rene maade, og det skal i saa fald staa i protokollen som andet skud.

**Data.** Kim-Wright (THREEFYTP10) starter 1990 og daekker kun onsets 1990, 2001, 2008 og 2020; det er for
lidt til en walk-forward. ACM (NY Fed, maanedlig fra 1961-06, `ACMTP10` som i ACM-testen) daekker 8 onsets
(1970, 1973, 1980, 1981, 1990, 2001, 2008, 2020). Udkastet foreslaar ACM. Licensen tjekkes foer forsegling.

**Feature.** E = (y10 − ACMTP10) − 3m, samme definition som ACM-testens curve_adj, med samme 3m-ben som den
operationelle kurve paa koerselstidspunktet (diskonto, medmindre raadet har vedtaget del A).
Maanedssnit, kvartalsaggregering som kurven.

**Kandidater (fastlagt foer koersel, ingen andre).**
- B1: E alene som erstatning for kurven (univariat bytte).
- B2: E og term-praemien (ACMTP10) som to features (dekomponeret kurve).

**Den symmetriske bar (§5.2, numerisk).** Paa identiske origins (panel fra 1961Q3; identiteten asserteres)
er Δ = skill(kandidat) − skill(curve-only), oracle-fri fast λ = 1. En kandidat krydser baren, hvis
Δ > 1,96 · SD_block(Δ); curve-only krydser den samme bar mod kandidaten, hvis −Δ > 1,96 · SD_block(Δ).
SD_block beregnes med episode-blok-bootstrap, 1000 traek, seed 42, paa det faelles panel. Krydser ingen,
er udfaldet "ingen forskel", og curve-only forbliver operationel ved raadets laas (RAADETS_V501 §6). Det
staar i protokollen som en asymmetri i udfaldet, ikke som evidens for curve-only. Krydsning udloeser kun
et dagsordenspunkt (§2.3), aldrig et automatisk skift.

**Styrke.** Med 8 onsets er MDE80 ca. 2,8 · SD_block, af stoerrelsesordenen 30pp som i §2.3. Testen kan
sandsynligvis ikke skelne kandidaterne fra curve-only, og det skrives i resultatet.

**Kontamination.** B1/B2 er kontamineret to gange: ACM-testens resultat er set, og litteraturens resultat
daekker store dele af 1961–2008 med kendt retning. Raadet skal tage stilling til, om det er samme situation
som EBP (§8.2, lukket permanent). Udkastet mener ja og foreslaar derfor:
- **B3 (prospektiv, uscoret; anbefalet):** forventningsdelen som en fast kontekstlinje og, efter en revisionsaudit
  paa mindst 12 snapshots, som en uscoret kolonne i hovedbogen, paa §8.3's betingelser (forseglet foer de
  onsets, den bedoemmes paa; ingen foer-2027-observation som evidens; en scoret test kraever mindst 2
  onsets efter forseglingen).

## C. Hvad der allerede er sket (dokumentation, P uroert)

Fra 2026-10-27 viser motor og dashboard to tekstlinjer: konventionsnoten under P (`live_input.konvention`)
og en staaende advarsel om forventningsdelen (`advarsler.forventningsdel`). Begge er kontekst. De aendrer
ikke P, baandet, dommen, vaegtene, manifestet eller hovedbogens raekker.
