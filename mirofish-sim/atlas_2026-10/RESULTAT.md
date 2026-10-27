# Sværm-atlas, oktober 2026 — resultat

**Kørt 27. oktober 2026.** Sammen med svarene: et neutralt faktagrundlag
([seed_v3_neutral.md](seed_v3_neutral.md)), driverscriptet ([svaerm_atlas.py](svaerm_atlas.py)), de rå
interviewsvar ([atlas_raw/](atlas_raw/)), kørselsloggen og optællingen
([optaelling.py](optaelling.py) → [optaelling_output.txt](optaelling_output.txt)). MiroFish med
qwen3.7-flash via OpenRouter; 7 kanaler × 20 runder; 3 interviewspørgsmål.

> **Varedeklaration:** Dette er en agent-sværms fortællinger, ikke sandsynligheder og ikke validerede
> signaler. Intet herfra påvirker modellens sandsynlighed (P), dommen eller hovedbogen.

## Hvad der var anderledes end i august

Kode-reviewet 2026-10-15 fandt, at august-atlasset i høj grad gentog sine egne input
(TRIGGER-ATLAS.md, erratum E1–E3). Denne gang:

- Faktagrundlaget indeholder kun observerede tal. Det har ingen modelsandsynlighed, ingen v4-flag og ingen
  "advarselstærskler" som "600bp". Indramningen "lav gnist, højt brændstof" er også væk.
- Styringsteksterne til de seks styrede kanaler indeholder ingen tal. Før stod der fx "fra 271bp" og
  "+51,5 %".
- Alle rå svar er gemt og committet, så optællingen kan gentages.

## Hvad der kom ud

**1. Agenterne gentager nutidens tal i stedet for at sætte egne tærskler.** Spørgsmålet var: hvilken
dataserie og hvilken tærskel ville først have vist, at vejen mod recession var i gang? Agenterne svarede
typisk med en serie og dens værdi i faktagrundlaget:

- HY-spændet "over 3,38 %" (= dagens 338bp);
- Baa-spændet "over 1,47 %" (= dagens værdi);
- EBP "−0,39" (= dagens værdi);
- olie "$108", 10Y "5,00 %", realkredit "7,32 %" (= dagens værdier).

Det sker, selv om grundlaget ikke nævner nogen tærskler. Sværmen behandler "det nuværende niveau" som
grænsen. Det er netop den fejl, reviewet fandt i august. Den skyldtes altså ikke kun de indlejrede tal, men
også metoden: en sprogmodel, der bliver spurgt om en tærskel, griber det tal, den har fået.

**2. Ingen af scenarie-appendiksets tærskler bliver genfundet.** I svarene om tidligste varsel nævner
ingen agent:

- 10Y over 5,25 %;
- realkredit over 7,8 %;
- CP-spænd over 75bp;
- HY-zonen 350–450bp, som var august-atlassets eneste tærskel med 3+ kanaler.

Én agent (statsgæld-kanalen) nævner ledighedsansøgninger over 250.000 (4-ugers gennemsnit).

**3. Det, der går igen, er hvilke typer data agenterne holder øje med, ikke grænserne.**
Kreditspænd (EBP, Baa, HY) og fundingrenter (CP) nævnes som tidligste varsel i 6 af de 6 kanaler med
svar. Det samme gælder løn/beskæftigelse, inflation og Fed-renten. Det er bredt og forventeligt. Desuden
stod EBP og Baa i faktagrundlaget, så også dét er delvist ekko.

**4. Én kanal mistede to af sine tre spørgsmål.** Aktiekursfald-kanalen (aktie_repricing) fik HTTP 400 på
spørgsmål 1 og 2, fordi MiroFish' simulationsmiljø lukkede, før interviewet. Det er en kendt
MiroFish-fejl. Kun spørgsmål 3 blev besvaret, så kanalen indgår ikke i optællingen af tidligste varsel.

## Hvad det betyder for scenarie-appendikset

- **Tærsklerne ændres ikke.** Sværmen giver ikke noget grundlag for nye tærskler, og den bekræfter heller
  ikke de gamle. Linjerne i appendikset bliver stående som "uvalideret scenarie" med deres
  august-proveniens og erratummet.
- **Metodisk konklusion:** spørgsmålsformen "nævn serien og tærsklen" kan ikke give uafhængige tærskler
  med denne model. Agenterne forankrer i de tal, de får. Det gælder, uanset om tallene står som tærskler,
  som i august, eller som rene observationer, som nu. En fremtidig kørsel giver kun mening med et andet
  design. To muligheder: spørg uden at vise nutidstallene, eller spørg om retning og fart i stedet for
  niveau.
- Intet herfra indgår i P, dommen, hovedbogen eller antændingskolonnen (rådets R3).
