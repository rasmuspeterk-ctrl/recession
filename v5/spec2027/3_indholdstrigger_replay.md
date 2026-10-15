# Forseglet spec 3/4 — NBER-indholdstriggeren og dens konfigurationsspecifikke replay (RAADETS_2027 §6)

**Forseglet 2026-10-15.** Teksten er committet og pushet, FOER koden der bruger den skrives (RAADETS_2027 §12
trin 3). Koden laaser filens sha256 (LF-normaliseret) og stopper hoejlydt, hvis filen er aendret efter
forseglingen. En aendring kraever en raadsbeslutning. Er spec og kode uenige, gaelder spec'en (§3.4).

Ratificeret tekst (§6, ordret):

> 6.1 From the 2027 refit, refits occur in September, on a change of the announcement table's hash, and on a
> **content trigger**:
> - **one** refit per new onset, in the first month where `eligible_fit(R)` contains a positive label of that
>   onset absent from the manifest;
> - in any month where `eligible_fit(R)` contains a **relabel**.
>
> Routine maturation of negative origins never triggers. Later positives of the same onset wait for September.
> Triggers never alter labels or censoring; the trigger month is logged in the manifest.
>
> 6.2 A configuration-specific replay (September + hash + this trigger) is specified, sealed and pushed before
> the 2027 refit, and published as the ledger supplement for this regime. Like §7.2, it prints all three
> censoring variants (real-time open-episode rule first). Adoption is not conditional on the replay's score.
> The September-only replay figures (+24.41 / +28.95 / +33.28) are never described as this regime's skill.

## 1. Ikrafttraeden

Indholdstriggeren gaelder, naar kalibreringen I DRIFT har refit-maaned >= 2027-09 (dvs. fra og med september-
refitten 2027). Foer det findes kun v5.0.1's triggere (september og tabellens hash). September- og hash-triggerne
er uaendrede.

## 2. Indholdstriggeren (§6.1)

Ved maaned R (koerselsmaaneden = snapshottets maaned) og kalibreringen i drift med manifest M (origin-liste
[aar, kvartal, label] og refit-maaned R_M):

- **Berettigede origins ved R:** `ablation2_nber.eligible_fit(D_curve, eps, avail, usrec, R)` — praecis den
  funktion, der fitter (curve-only-universet, annonceringstabellen paa disk, USREC i snapshottet). Labels pr. R.
- **Onsets i manifestet:** for hvert origin i M med label 1: de USREC-onsets O i vinduet (qend, qend + 12], hvis
  top er annonceret senest i R_M. Foreningen kaldes M's onsets.
- **Ny onset:** en onset O, som et berettiget origin ved R har label 1 for (O i vinduet og annonceret senest i R),
  og som IKKE er blandt M's onsets. Triggeren udloeses een gang for O: den refit, den udloeser, faar O ind i
  manifestet, saa senere positive origins for samme O ikke udloeser igen (de venter paa september).
- **Omlabeling:** et origin, der er berettiget ved R og findes i M, med en anden label ved R end i M.
- **Udloest** = mindst een ny onset eller mindst een omlabeling. Nymodnede negative origins, nymodnede positive
  origins for en onset, der allerede er i M, og origins der forsvinder (censurering ved en ny topannoncering —
  den udloeser hash-triggeren) udloeser aldrig indholdstriggeren.
- Triggeren aendrer aldrig labels, censurering, eligibility eller fit; den bestemmer kun, HVORNAAR der refittes.

**Trigger-maaneden** er den foerste maaned R' i (R_M, R], hvor triggeren er udloest (samme definition, evalueret ved
R'). Koeres refitten senere end trigger-maaneden, er trigger-maaneden stadig den foerste.

### Hvor triggeren evalueres

- **motor.py**: ved hver laesning under en kalibrering, hvor triggeren gaelder. Er den udloest, er en
  rekalibrering paakraevet (samme behandling som september/hash: `--log` blokeres, linjen "REKALIBRERING
  PAAKRAEVET: NBER-indholdstrigger (RAADETS_2027 §6) ..." printes og staar i dashboard.json's
  `rekalibrering_paakraevet`). Mangler manifest-filen for kalibreringen i drift, blokeres `--log` (triggeren kan
  ikke evalueres; fail-closed).
- **finalize6.py**: en udloest indholdstrigger er en deterministisk trigger (§3.2) paa linje med september og
  hash. Manifestet faar feltet `indholdstrigger` (proveniens, uden for indholds-hashen ligesom `trigger`):
  `protokol` ("RAADETS_2027 §6"), `spec_sha256`, `trigger_maaned` (YYYY-MM), `nye_onsets` ({onset: [origins]}),
  `omlabelinger` ([...]), `evalueret_ved` (refit-maaneden). Uden udloest trigger: feltet er null. `trigger`-teksten
  bliver "nber-indhold (RAADETS_2027 §6): trigger-maaned YYYY-MM; ...", medmindre tabellens hash ogsaa er aendret
  (da staar hash-triggeren foerst, og indholdstriggeren noteres efter den).

## 3. Den konfigurationsspecifikke replay (§6.2)

En maanedlig hovedbogs-replay af, hvad hovedbogen ville have vist under DETTE regime (september + hash +
indholdstrigger). Konstruktionen er E5's (`analyser/hovedbog_reference.py`, noeglens regler) med een aendring:
kalibreringsplanen. Script: `v5/replay2027.py`; koeres ved september-refitten 2027 efter finalize6 og diagnostik
(paa refittens snapshot, R_score = refit-maaneden) og skriver `v5/replay2027_resultat.json`.

### 3.1 Raekker og score (som E5)

- Een raekke pr. logningsmaaned. Origin m = maaneden foer logningsmaaneden; input = maanedstallet
  GS10 − TB3MS for m; vindue = logningsmaaneden + 11 maaneder; Y = 1 hvis en USREC-onset (endelig kronologi)
  ligger i vinduet.
- Kun modne raekker: m + 12 + 18 <= R_score.
- P = den kalibrering, der er i kraft ved logningen (seneste refit i en maaned <= logningsmaaneden; en refit i
  logningsmaaneden gaelder for den maaneds raekke), beregnet som motor goer (`finalize6.p_af` paa de afrundede
  manifestvaegte) og logget med 1 decimal. Basisrate = kalibreringens fit-basisrate (den loggede).
- Score: skill = 1 − LL(P som logget) / LL(logget basisrate); Brier-skill sekundaer; clip 1e-6.
- Logdagen = foerste hverdag fra og med den 10. (helligdage ignoreres).

### 3.2 Informationssaet og kalibreringsplan (dette regime)

- **Information ved logningsmaaned M:** tabellens raekker med `announcement_date` <= logdag(M) (dag-praecist).
  avail_M bygges heraf som `ablation2_nber.load_announcements` (annonceringsmaaned; pre-1979: trough + 18).
- **Kalibrering ved refit i M:** `finalize6.fit_model(D_curve, eps, avail_M, usrec, R = M)`. Kraever >= 60
  berettigede origins og >= 6 positive (walk-forwardens minimum); ellers ingen kalibrering ved M.
- **Refit-triggere i M** (alle evalueret mod kalibreringen i kraft FOER M's refit; hoejst een refit pr. maaned):
  1. september: M er en september;
  2. hash: en tabel-raekke (top ELLER bund) bliver synlig i M, dvs. annonceret efter logdag(M − 1) og senest
     logdag(M);
  3. indhold: triggeren i pkt. 2 ovenfor, evalueret med `eligible_fit(D_curve, eps, avail_M, usrec, M)` mod
     kalibreringen i kraft.
- Pre-1979-onsets har ingen tabel-raekker og giver derfor ingen hash-trigger; deres konvention (kendt ved
  trough + 18) virker kun gennem indholdstriggeren.
- Foerste maaned i planen: den foerste september, der giver en kalibrering.

### 3.3 De tre censurvarianter (printes i denne raekkefoelge, alle tre altid)

For raekken med origin m og logdag d = logdag(m + 1). En episode [O, T]; top kendt ved datoen p_d (tabellens
annonceringsdato; pre-1979: den 1. i maaned T + 18), bund kendt ved b_d (tilsvarende).

1. **Realtid (motorens aabne-episode-regel)** — censureret, hvis der findes en episode med p_d <= d og m >= O,
   og enten (b_d <= d og m <= T) eller b_d > d (episoden er aaben). Samme regel som
   `hovedbog_reference.realtid_i_recession` og motorens live-censurering.
2. **Realtid uden USREC-vintage-antagelsen** — censureret, hvis m ligger i [O, T] efter den endelige kronologi og
   p_d <= d (dag-praecis topannoncering, endelig bund).
3. **Orakel** — censureret, hvis USREC(m) = 1 (endelig kronologi; som den publicerede walk-forward).

Pr. variant printes n, positive, skill (LL) og Brier-skill. Derudover: listen af refits med trigger-grund(e) og
antal pr. triggertype, og hvilke onsets indholdstriggeren bragte ind og hvornaar.

### 3.4 Sprog og status

- Overskriften er ordret: "Konfigurationsspecifik replay (september + hash + indholdstrigger) — hovedbogs-
  supplement for dette regime (RAADETS_2027 §6.2). Beskrivelse, ikke en test; vedtagelsen er ikke betinget af
  tallene."
- Realtidsvarianten (1) staar altid foerst; ingen variant printes alene.
- September-alene-tallene (+24,41 / +28,95 / +33,28, E5) beskrives aldrig som dette regimes skill og printes ikke
  af replayen.
- Resultatet publiceres uanset udfald.

## 4. Tests foer brug

- Triggeren: en ny positiv for en ny onset udloeser; en senere positiv for samme onset udloeser ikke; en
  nymodnet negativ udloeser ikke; en omlabeling udloeser; trigger-maaneden er den foerste udloeste maaned.
- motor: under en 2027-kalibrering med udloest trigger blokeres `--log`; foer ikrafttraeden evalueres
  triggeren ikke (dashboard.json uaendret).
- finalize6: en udloest indholdstrigger er en gyldig trigger, og manifestet faar `indholdstrigger` med
  trigger-maaneden; uden trigger (og uden september/hash/reparation) stopper koerslen som i dag.
- Replayen, koert med KUN september-triggeren paa snapshot 2026-09-19 og R_score 2026-09, reproducerer E5 eksakt:
  realtid +24,41 % (n 561), uden vintage-antagelse +28,95 % (n 644), orakel +33,28 % (n 583). Dette er et
  selvtjek af konstruktionen i testsuiten, ikke et tal for dette regime.
- Hash-triggerens maaneder for tabellens raekker er E5's (en annoncering senest paa logdagen rammer samme maaned,
  ellers naeste).
