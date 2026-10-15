# Protokoltekst 5 — live-censureringens regel (RAADETS_2027 §10.4)

**Skrevet i protokollen 2026-10-15, foer september-refitten 2027.** Teksten er committet og pushet, FOER koden der
bruger den (RAADETS_2027 §12 trin 3). Regelteksten mellem markeringerne nedenfor er byte-identisk med
bedoemmelsesnoeglens regel (BEDOEMMELSESNOEGLE.md §1 (d), LF-linjeskift); testsuiten haandhaever det i CI, og
koden laaser filens sha256. Noeglen aendres ikke (RAADETS_2027 §7.1); en aendring af reglen kraever en ny noegle
efter noeglens egen procedure OG en raadsbeslutning.

Ratificeret tekst (§10.4, ordret):

> 10.4 Live censoring inside an announced recession: ratified on two conditions:
> - the live rule is byte-identical to the key's open-episode rule and is written into the protocol before the
>   2027 refit;
> - every censored month keeps an **unscored** record of P and the eventual outcome (UDFALD.csv supplementary
>   column).
>
> The minutes note that (1) and (4) were made without mandate and are ratified ex post.

## Regelteksten (byte-identisk med BEDOEMMELSESNOEGLE.md §1 (d))

<!-- REGEL START -->
**(d) Realtidscensurering.** En række, der er logget inde i en *annonceret* recession (dom
`censureret`), scores ikke, fordi onset-sandsynligheden ikke er defineret. En række, der er logget
inde i en recession, som *endnu ikke* var annonceret, scores som logget og får typisk Y = 0
(onset ligger før vinduet). Det er netop forskellen mellem den publicerede walk-forward (orakel-
censurering) og live-virkeligheden. Sammenligningstallet er derfor diagnostik 4.5's
oracle-fri variant (se pkt. 3), og de to tolkes i tandem.
<!-- REGEL SLUT -->

## Anvendelse (implementeringsnote — ikke en del af regelteksten)

- "Logget inde i en annonceret recession" afgoeres for laesningens maaned (live-inputvinduets sidste dag; ellers
  logningsdatoen). Maaneden er inde i en annonceret recession, naar den ligger i en USREC-episode, hvis top er
  annonceret senest i den maaned (nber_announcements.csv), og episoden daekker maaneden efter snapshottets
  USREC-vintage: frem til og med bunden, eller — saa laenge USREC's seneste maaned er 1 — uden slut (den aabne
  episode). Det er motorens aabne-episode-regel: `ablation2_nber.i_annonceret_recession`, kaldt fra `motor.py`,
  som giver dommen `censureret`.
- En recession, hvis top endnu ikke er annonceret i laesningens maaned, censurerer ikke: raekken scores som logget.
- Den anden betingelse i §10.4 (uscoret record af P og det endelige udfald for hver censureret maaned) er
  spec2027/4_maanedligt_fit_uscorede.md §6: `uscoret_censur` i hovedbog.jsonl og UDFALD.csv's kolonne
  `uscoret_censureret`.
- Hovedbogs-replayens variant 1 ("realtid, motorens aabne-episode-regel", spec 3 §3.3) er samme regel anvendt
  historisk med dag-praecise annonceringer pr. logdag.
- Er implementeringen og regelteksten uenige, gaelder regelteksten (§3.4); uenigheden erklaeres og forelaegges
  raadet.
