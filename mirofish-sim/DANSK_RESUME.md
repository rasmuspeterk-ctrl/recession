# MiroFish-simulering: "US recession inden august 2027?" — dansk resumé

**Kørt 2026-08-09** · Seed: dagens makrosnapshot (seed.md) · 6 agent-grupper (Fed, husholdninger, retail, institutionelle, virksomheder, boligbyggere/medier) · 30 runder på Twitter+Reddit-parallelverden · Model: qwen/qwen3.7-flash via OpenRouter · Zep-vidensgraf · Original rapport på kinesisk: rapport_kinesisk.md

## Sværmens dom

**Overskriften er dramatisk, kroppen er betinget.** Abstraktet konkluderer at recessionssandsynligheden inden for 12 måneder er "meget høj" under "low spark, high fuel"-konfigurationen. Men rapportens egen analysesektion er mere præcis: *"markedet gennemgår en voldsom reprising — men reprising er ikke det samme som recession"*, og den citerer MOTOR's 4-9% mod basisraten 13-15% samt at 0 af 4 recessionsflag er aktive. Sværmens reelle påstand: **recessionsrisikoen er væsentligt forhøjet i forhold til normalen HVIS reprisingen kommer og Fed reagerer for sent** — med resonansvindue **ultimo 2026 til medio 2027**.

## Triggerkæden (3 faser)

1. **Reprising strammer de finansielle forhold.** Ekstrem værdiansættelse (CAPE 42, negativ risikopræmie −2,22pp) + rekordmarginlån (+51,5%) giver nul fejlmargin. Institutionelle er "åbent lange, hemmeligt bearish" og trækker likviditeten ved første knæk; retail's tvangssalg (margin calls) accelererer faldet.
2. **Omvendt formueeffekt + kreditkanalen fryser.** Husholdninger skærer forbrug når aktiver falder (realt kontantafkast er allerede negativt); virksomheder rammer 2027-refinansieringsmuren ved høje realrenter; banker strammer.
3. **Arbejdsmarkedet revner og bekræfter recessionen.** Ansættelsesstop → claims stiger → Sahm > 0,5 → selvopfyldende pessimisme-loop ("de-leverage → mindre forbrug → færre ansatte → mindre forbrug").

## Sværmens konkrete early warnings

| Indikator | Nu | Alarmtærskel |
|---|---|---|
| HY OAS | 271bp | hurtig bevægelse mod 400bp+ (recessionsalarm 600bp) |
| Initial claims (4-ugers snit) | ~199k | brud over ~220k |
| Sahm-reglen | −0,03 | nærmer sig +0,50 |
| Realt kontantafkast (FF−PCE) | −0,04pp | vedvarende negativt → opsparing drænes |
| Virksomheds-refinansiering | — | commercial paper-spænd vider ud H2 2026-primo 2027 |

## Sammenligning: tre stemmer om samme spørgsmål

| Stemme | Metode | Svar |
|---|---|---|
| **MOTOR v5** (valideret model) | Walk-forward-logit på 5 features | **4,3%** — under basisraten; rolig kurve, roligt arbejdsmarked |
| **MiroFish-sværmen** (narrativ simulation, uvalideret) | 6 agenter, 30 runder | **"Væsentligt forhøjet"** — betinget af reprising-transmission; vindue ultimo 2026-medio 2027 |
| **Rådet** (7 modeller, enstemmigt) | Metodedebat | Værdiansættelsesflag er "market conditions — NOT recession evidence"; kun det validerede tal må kaldes en sandsynlighed |

Bemærk at sværmen præcis satser på den kanal (værdiansættelse→realøkonomi) som rådet bevidst har sat uden for den validerede model, fordi den aldrig har bestået en walk-forward-test. Det gør ikke sværmen forkert — 1929/2000/2007 er dens historiske ankre — men det betyder at dens dom skal læses som et **scenarie-stresstest af "high fuel"-kanalen**, ikke som en kalibreret sandsynlighed. v4's egen formulering dækker begge: *"lav gnist, højt brændstof — markedsrisiko FØR økonomisk risiko."*

## Forbehold

Én kørsel (intet ensemble), 6 agentgrupper, 30 runder, lille og billig model (qwen3.7-flash), simulation på kinesisk (MiroFish's interne prompts), og sværmen fik MOTOR's egen læsning i seedet (forankringsrisiko). Runneren hang efter runde 30 (maskinen sov) og blev stoppet manuelt — alle 30 runder var gennemført.
