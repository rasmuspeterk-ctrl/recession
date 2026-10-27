#!/usr/bin/env python3
"""
spine.py — den maanedlige rygrad (v5.0.1, RAADETS_V501.md §1) + friskheds-guard (§1.7).

Yales ie_data.xls er frosset ved 2023-09 (Last-Modified 17 Oct 2023). Rygraden bygges
derfor som en komposit: Shillers raekker byte-identisk t.o.m. SEAM (2023-07, sidste
ikke-forloebige raekke), derefter FRED SP500 (dagligt -> maanedsmiddel), FRED CPIAUCNS,
GS10 som LTR og multpl's maanedlige CAPE. Hver raekke baerer en proveniens-kolonne.

Guards (alle rene funktioner, stdlib, testet i test_v5.py):
  parse_multpl     — haarde assertions: >= 1860 raekker, foerste dato 1871-02, kun lukkede maaneder
  monthly_mean     — daglige/ugentlige raekker -> maanedsmiddel (aggregerings-helper; ogsaa erratum §5)
  overlap_check    — SP500/CAPE-overlap mod Shiller inden for tolerancer (§1.2)
  outlier_check    — CAPE-niveau [5,60] og |m/m| < 15 % (§1.6)
  staleness        — udgivelses-bevidst friskhed pr. serie (§1.7): den test der ville have
                     fanget den frosne rygrad i oktober 2023
  datastatus       — udgivelseskalender for ALLE serier (2026-10-27): "nyeste tal" / "naeste tal ventes ca."
                     / "forsinket", saa en serie der gaar i staa kan skelnes fra almindelig udgivelsesforsinkelse
  spx_fra_top, multpl_live, finra_margin — de tal manual.json foer blev tastet ind i haanden, beregnet af
                     snapshottets egne filer (2026-10-27)
"""
import io, re, statistics, zipfile
from datetime import date, timedelta

SEAM = "2023-07"                        # sidste Shiller-raekke der beholdes
PRELIMINAERE = ("2023-08", "2023-09")   # Shillers egne forloebige raekker (erstattes)
MULTPL_MIN_RAEKKER = 1860
MULTPL_FOERSTE = "1871-02"
TOL = dict(sp500_median=0.10, sp500_andel_inden_1pct=0.99,   # %-afvigelse / andel
           cape_median=0.10, cape_max=1.00)
CAPE_NIVEAU = (5.0, 60.0)
CAPE_MM_MAX = 15.0                      # % maaned-til-maaned

# §1.7: forventet seneste observationsperiode ved publiceringstidspunktet, udtrykt som
# max alder i dage af sidste observations-STEMPEL (FRED stempler maanedsserier paa den 1.).
# Reglen er committed og aendres kun med begrundet commit. Serier der ikke staar her
# tjekkes ikke (ingen forbruger er afhaengig af deres friskhed).
FRISKHED_DAGE = {
    # operationelle (veto): kurve, label, raekkeunivers
    "GS10": 70, "TB3MS": 70, "USREC": 75, "A191RL1Q225SBEA": 215,
    # maanedlige, ikke-operationelle
    "CPIAUCNS": 80, "CPIAUCSL": 80, "PCEPI": 100, "UNRATE": 70, "SAHMREALTIME": 70,
    "PERMIT": 90, "AWHMAN": 75, "FEDFUNDS": 70, "RECPROUSM156N": 130,
    # ugentlige / daglige
    "ICSA": 21, "MORTGAGE30US": 14, "BAMLH0A0HYM2": 10, "DTB3": 10, "RIFSPPFAAD90NB": 35,
    "DGS10": 10, "DFF": 10,
    "THREEFYTP10": 21, "SP500": 10,
    # rygrad: sidste komposit-maaned skal vaere forrige lukkede maaned (stempel den 1.)
    "spine": 75,
}
KRITISKE = ("GS10", "TB3MS", "USREC", "DGS10", "DTB3")   # stale her -> snapshot ukomplet
# (GS10/TB3MS: kalibrering; DGS10/DTB3: live-input til kurven; USREC: label)

# ---- seriernes roller (kode-review 2026-10-15, F18/F1/F19): EEN tabel, alt andet afledes heraf ----
# rolle   "P"        kraeves for selve laesningen af P (live-kurve + publiceret maanedssammenligning)
#         "refit"    kraeves af kalibreringen (label, raekkeunivers, rygradens CPI)
#         "rygrad"   bygger rygradens komposit i fetch; fejl nedlaegger ikke laesningen, men goer
#                    snapshottet uegnet til rekalibrering (meta.spine.refit_klar = false, F5)
#         "kontekst" monitor/kontekst/ablation: fejl eller manglende fil nedlaegger ALDRIG veto
# licens  "pd"       FRED: Public Domain: Citation Requested
#         "citation" FRED: Copyrighted: Citation Required — maa videregives med kildeangivelse
#         "lokal"    ophavsretligt begraenset (Pre-Approval Required / 'may not be reproduced'):
#                    hentes og hashes lokalt, committes ALDRIG (.gitignore); meta.json beholder
#                    sha256/first/last/last_value, saa hashen kan efterproeves af alle der henter
#                    samme bytes. Licensmaerker hentet fra FRED's seriesider 2026-10-15.
SERIER = {
    # sid:              (rolle,      licens,     kilde,                                   formaal)
    "GS10":            ("P",        "pd",       "Board of Governors (H.15)",             "10-aarig statsrente, maanedssnit (kalibreringens kurve; publiceret sammenligning)"),
    "TB3MS":           ("P",        "pd",       "Board of Governors (H.15)",             "3-mdr T-bill, maanedssnit (kalibreringens kurve; publiceret sammenligning)"),
    "DGS10":           ("P",        "pd",       "Board of Governors (H.15)",             "10-aarig statsrente, daglig (live-input: trailing maaned; 10Y-linjen)"),
    "DTB3":            ("P",        "pd",       "Board of Governors (H.15)",             "3-mdr T-bill, daglig (live-input: trailing maaned; CP-spaend)"),
    "USREC":           ("refit",    "citation", "NBER via Federal Reserve Bank of St. Louis", "NBER-recessionsmaaneder (label; USREC-krydstjek af annonceringstabellen)"),
    "A191RL1Q225SBEA": ("refit",    "pd",       "U.S. Bureau of Economic Analysis",      "real BNP %-aendring ann. (raekkeunivers via teknisk label; BNP-linjen)"),
    "CPIAUCNS":        ("refit",    "pd",       "U.S. Bureau of Labor Statistics",       "CPI NSA (rygradens CPI; realrate/d_infl i fuldmodellen)"),
    "SP500":           ("rygrad",   "lokal",    "S&P Dow Jones Indices LLC",             "S&P 500 dagligt luk, rullende ~10 aar (rygradens SP500 efter 2023-07 som maanedsmiddel; dd)"),
    "CPIAUCSL":        ("kontekst", "pd",       "U.S. Bureau of Labor Statistics",       "CPI SA (inflationsmomentum, kontekst)"),
    "UNRATE":          ("kontekst", "pd",       "U.S. Bureau of Labor Statistics",       "ledighed (Sahm-transform, trin 4 — afvist)"),
    "SAHMREALTIME":    ("kontekst", "pd",       "Claudia Sahm via FRED",                 "Sahm-reglen realtid (monitor + benchmark)"),
    "ICSA":            ("kontekst", "pd",       "U.S. Employment and Training Administration", "initial claims, ugentlig (monitor; trin 4 — afvist)"),
    "CCSA":            ("kontekst", "pd",       "U.S. Employment and Training Administration", "fortsatte ansoegninger, ugentlig (claims-linjen, F58)"),
    "PERMIT":          ("kontekst", "pd",       "U.S. Census Bureau",                    "byggetilladelser (monitor; trin 4 — afvist)"),
    "BAMLH0A0HYM2":    ("kontekst", "lokal",    "ICE Data Indices, LLC",                 "HY OAS, daglig, rullende 3 aar (monitor — ineligible som feature)"),
    "BAA10Y":          ("kontekst", "lokal",    "Moody's via FRED",                      "Baa minus 10Y, daglig 1986- (kreditkontekst, F36)"),
    "GDPC1":           ("kontekst", "pd",       "U.S. Bureau of Economic Analysis",      "real BNP niveau (reserve)"),
    "FEDFUNDS":        ("kontekst", "pd",       "Board of Governors (H.15)",             "effektiv fed funds, maanedssnit (fallback for DFF)"),
    "DFF":             ("kontekst", "pd",       "Board of Governors (H.15)",             "effektiv fed funds, daglig (pengepolitik-blok)"),
    "PCEPI":           ("kontekst", "pd",       "U.S. Bureau of Economic Analysis",      "PCE-prisindeks (realt kontantafkast, inflationsmomentum)"),
    "THREEFYTP10":     ("kontekst", "pd",       "Board of Governors (Kim-Wright)",       "Kim-Wright 10-aars term-praemie, Fed Board (kontekst; ACM-testen trin 4 brugte manual/acm.csv)"),
    "RECPROUSM156N":   ("kontekst", "pd",       "Marcelle Chauvet og Jeremy Piger via FRED", "Chauvet-Piger glattet recessionssandsynlighed (benchmark, coincident nowcast)"),
    "AWHMAN":          ("kontekst", "pd",       "U.S. Bureau of Labor Statistics",       "ugentlige arbejdstimer, industri (v5.2-testen — afvist; vist som kontekst)"),
    "RIFSPPFAAD90NB":  ("kontekst", "pd",       "Board of Governors (CP)",               "90-dages AA finansiel commercial paper-rente (scenarie-appendiks: CP-spaend)"),
    "MORTGAGE30US":    ("kontekst", "citation", "Freddie Mac",                           "30-aars realkreditrente, ugentlig (scenarie-appendiks)"),
    "DGS1":            ("kontekst", "pd",       "Board of Governors (H.15)",             "1-aarig statsrente, daglig (kurvens sammensaetning, near-term forward spread, F38)"),
    "DGS2":            ("kontekst", "pd",       "Board of Governors (H.15)",             "2-aarig statsrente, daglig (kurvens sammensaetning front/bag, F38)"),
    "DGS3MO":          ("kontekst", "pd",       "Board of Governors (H.15)",             "3-mdr konstant loebetid, daglig (near-term forward spread, F38)"),
    "PAYEMS":          ("kontekst", "pd",       "U.S. Bureau of Labor Statistics",       "loenmodtagerbeskaeftigelse (NBER-indikator, F39)"),
    "CE16OV":          ("kontekst", "pd",       "U.S. Bureau of Labor Statistics",       "husstandsbeskaeftigelse (NBER-indikator, F39)"),
    "INDPRO":          ("kontekst", "pd",       "Board of Governors (G.17)",             "industriproduktion (NBER-indikator, F39)"),
    "W875RX1":         ("kontekst", "pd",       "U.S. Bureau of Economic Analysis",      "real personlig indkomst ekskl. overfoersler (NBER-indikator, F39)"),
    "PCEC96":          ("kontekst", "pd",       "U.S. Bureau of Economic Analysis",      "realt privatforbrug (NBER-indikator, F39)"),
    "CMRMTSPL":        ("kontekst", "citation", "Federal Reserve Bank of St. Louis",     "realt engros/detail/industri-salg (NBER-indikator, F39)"),
    "TEMPHELPS":       ("kontekst", "pd",       "U.S. Bureau of Labor Statistics",       "vikarbeskaeftigelse (arbejdsmarkedskontekst, F58)"),
    "DCOILWTICO":      ("kontekst", "pd",       "U.S. Energy Information Administration", "WTI-oliepris, daglig (regimekontekst, F40)"),
    # Kontekst-protokollen 2026-10-24 (Rasmus' ordre): raavarer, kreditkort og bolig i USA. Kun officielle
    # public domain-kilder (licensmaerker tjekket paa FRED's seriesider 2026-10-24). Ingen indflydelse paa P,
    # dom eller antaendingskolonnen; fejl nedlaegger aldrig veto. S&P/Case-Shiller (CSUSHPINSA) er
    # "Copyrighted: Pre-Approval Required" og bruges derfor ikke — FHFA's indeks er den officielle huspris.
    "DCOILBRENTEU":    ("kontekst", "pd",       "U.S. Energy Information Administration", "Brent-spot, daglig (raavarer; prissaetter US benzin/diesel)"),
    "DHHNGSP":         ("kontekst", "pd",       "U.S. Energy Information Administration", "Henry Hub naturgas spot, daglig (raavarer; goedningens feedstock)"),
    "GASREGW":         ("kontekst", "pd",       "U.S. Energy Information Administration", "US benzin, regular, detail, ugentlig (raavarer)"),
    "GASDESW":         ("kontekst", "pd",       "U.S. Energy Information Administration", "US diesel, detail, ugentlig (raavarer)"),
    "WPU0652":         ("kontekst", "pd",       "U.S. Bureau of Labor Statistics",       "PPI goedningsmaterialer, NSA (raavarer)"),
    "WPU065201":       ("kontekst", "pd",       "U.S. Bureau of Labor Statistics",       "PPI kvaelstofgoedning (nitrogenates), NSA (raavarer)"),
    "WPU012":          ("kontekst", "pd",       "U.S. Bureau of Labor Statistics",       "PPI korn (farm products: grains), NSA (raavarer)"),
    "WPU102":          ("kontekst", "pd",       "U.S. Bureau of Labor Statistics",       "PPI ikke-jernholdige metaller, NSA (raavarer)"),
    "REVOLSL":         ("kontekst", "pd",       "Board of Governors (G.19)",             "revolverende forbrugerkredit, mio. USD, SA (kreditkort)"),
    "CCLACBW027SBOG":  ("kontekst", "pd",       "Board of Governors (H.8)",              "kreditkortlaan i banker, mia. USD, SA, ugentlig (kreditkort)"),
    "DRCCLACBS":       ("kontekst", "pd",       "Board of Governors",                    "restancerate kreditkort, alle banker, %, SA, kvartal (kreditkort)"),
    "CORCCACBS":       ("kontekst", "pd",       "Board of Governors",                    "afskrivningsrate kreditkort, alle banker, %, SA, kvartal (kreditkort)"),
    "HPIPONM226S":     ("kontekst", "pd",       "U.S. Federal Housing Finance Agency",   "FHFA purchase-only huspris-indeks, SA, maanedlig (bolig)"),
    "MSPUS":           ("kontekst", "pd",       "U.S. Census Bureau og HUD",             "median salgspris for solgte huse, USD, kvartal (bolig)"),
    "MSACSR":          ("kontekst", "pd",       "U.S. Census Bureau og HUD",             "udbud af nye huse i maaneder, SA (bolig)"),
    "DRSFRMACBS":      ("kontekst", "pd",       "Board of Governors",                    "restancerate enfamilie-realkredit, alle banker, %, SA, kvartal (bolig)"),
}
# Kontekst-protokollen 2026-10-24: blokkene motor printer, og hvad hver linje viser (EEN tabel; motor, dashboard og
# hovedbog.jsonl afledes heraf). frekv: "d" daglig, "u" ugentlig, "m" maanedlig, "q" kvartal. skala ganger vaerdien.
KONTEKST_BLOKKE = {
    "raavarer": ("RAAVARER (USA-relevante)", (
        ("DCOILWTICO", "WTI spot (EIA)", "d", "$", "/bbl", 1.0),
        ("DCOILBRENTEU", "Brent spot (EIA)", "d", "$", "/bbl", 1.0),
        ("DHHNGSP", "Henry Hub naturgas (EIA)", "d", "$", "/MMBtu", 1.0),
        ("GASREGW", "Benzin, regular, detail (EIA)", "u", "$", "/gal", 1.0),
        ("GASDESW", "Diesel, detail (EIA)", "u", "$", "/gal", 1.0),
        ("WPU0652", "PPI goedningsmaterialer (BLS)", "m", "", " (1982=100)", 1.0),
        ("WPU065201", "PPI kvaelstofgoedning (BLS)", "m", "", " (1982=100)", 1.0),
        ("WPU012", "PPI korn (BLS)", "m", "", " (1982=100)", 1.0),
        ("WPU102", "PPI ikke-jernholdige metaller (BLS)", "m", "", " (1982=100)", 1.0))),
    "kreditkort": ("KREDITKORT & FORBRUGERKREDIT (USA)", (
        ("REVOLSL", "Revolverende forbrugerkredit (G.19)", "m", "$", " mia.", 0.001),
        ("CCLACBW027SBOG", "Kreditkortlaan i banker (H.8)", "u", "$", " mia.", 1.0),
        ("DRCCLACBS", "Restancer kreditkort (30+ dage)", "q", "", "%", 1.0),
        ("CORCCACBS", "Afskrivninger kreditkort", "q", "", "%", 1.0))),
    "bolig": ("BOLIG (USA)", (
        ("HPIPONM226S", "FHFA huspriser (purchase-only, SA)", "m", "", " (1991=100)", 1.0),
        ("MSPUS", "Median salgspris, solgte huse", "q", "$", "", 1.0),
        ("MSACSR", "Udbud af nye huse", "m", "", " mdr.", 1.0),
        ("DRSFRMACBS", "Restancer enfamilie-realkredit", "q", "", "%", 1.0),
        ("MORTGAGE30US", "30-aars realkreditrente (Freddie Mac)", "u", "", "%", 1.0))),
}
# Ikke-FRED-kilder der hentes og hashes som serier (fetch.fetch_series kender URL'en og kolonnen)
EKSTERNE = {
    "EBP": dict(url="https://www.federalreserve.gov/econres/notes/feds-notes/ebp_csv.csv", kolonne="ebp",
                rolle="kontekst", licens="pd", kilde="Board of Governors (Gilchrist-Zakrajsek EBP, FEDS Notes)",
                formaal="excess bond premium + GZ-spaend, maanedlig 1973- (kreditkontekst, F36)"),
}
VETO = tuple(s for s, v in SERIER.items() if v[0] in ("P", "refit"))       # fetch-fejl -> snapshot ukomplet
P_SERIER = tuple(s for s, v in SERIER.items() if v[0] == "P")
LOKALE = tuple(s for s, v in SERIER.items() if v[1] == "lokal")              # committes aldrig
LOKALE_FILER = ("multpl_cape.html", "cape_multpl.csv", "finra_margin.xlsx")  # multpl-siden og FINRA's fil ordret (F12)

# ---- udgivelseskalender (2026-10-27): hvornaar kommer naeste tal normalt? ----
# sid: (frekvens, normal forsinkelse i dage efter periodens slutning, navn i almindeligt dansk)
# frekvens "d" daglig, "u" ugentlig, "m" maanedlig, "q" kvartal. Forsinkelserne er kildernes normale
# udgivelsesrytme paa FRED (fx CPI ca. 2 uger efter maanedens slutning, BNP ca. 1 maaned efter kvartalet).
UDGIVELSE = {
    "GS10": ("m", 3, "10-aarig rente, maanedssnit"), "TB3MS": ("m", 3, "3-maaneders rente, maanedssnit"),
    "DGS10": ("d", 2, "10-aarig rente, dagligt"), "DTB3": ("d", 2, "3-maaneders rente, dagligt"),
    "USREC": ("m", 5, "NBER's recessionsmaaneder"), "A191RL1Q225SBEA": ("q", 32, "BNP-vaekst"),
    "GDPC1": ("q", 32, "BNP, niveau"), "CPIAUCNS": ("m", 16, "Forbrugerpriser (CPI)"),
    "CPIAUCSL": ("m", 16, "Forbrugerpriser, saesonkorrigeret"), "SP500": ("d", 2, "S&P 500-indekset"),
    "UNRATE": ("m", 10, "Ledighed"), "SAHMREALTIME": ("m", 10, "Sahm-reglen"),
    "ICSA": ("u", 6, "Nye ledighedsansoegninger"), "CCSA": ("u", 13, "Fortsatte ledighedsansoegninger"),
    "PERMIT": ("m", 20, "Byggetilladelser"), "BAMLH0A0HYM2": ("d", 2, "Kreditspaend, high yield"),
    "BAA10Y": ("d", 2, "Kreditspaend, Baa minus 10-aarig"), "FEDFUNDS": ("m", 3, "Styrerenten, maanedssnit"),
    "DFF": ("d", 2, "Styrerenten, dagligt"), "PCEPI": ("m", 32, "Forbrugspriser (PCE)"),
    "THREEFYTP10": ("d", 12, "Term-praemie (Kim-Wright)"), "RECPROUSM156N": ("m", 40, "Chauvet-Piger-nowcast"),
    "AWHMAN": ("m", 10, "Arbejdstimer i industrien"), "RIFSPPFAAD90NB": ("d", 5, "Rente paa virksomhedspapirer (CP)"),
    "MORTGAGE30US": ("u", 1, "30-aarig realkreditrente"), "DGS1": ("d", 2, "1-aarig rente"),
    "DGS2": ("d", 2, "2-aarig rente"), "DGS3MO": ("d", 2, "3-maaneders statsobligation"),
    "PAYEMS": ("m", 10, "Loenmodtagere i job"), "CE16OV": ("m", 10, "Beskaeftigede (husstande)"),
    "INDPRO": ("m", 20, "Industriproduktion"), "W875RX1": ("m", 32, "Realindkomst uden overfoersler"),
    "PCEC96": ("m", 32, "Realt privatforbrug"), "CMRMTSPL": ("m", 58, "Salg i handel og industri"),
    "TEMPHELPS": ("m", 10, "Vikarer i job"), "DCOILWTICO": ("d", 8, "Oliepris, WTI"),
    "DCOILBRENTEU": ("d", 8, "Oliepris, Brent"), "DHHNGSP": ("d", 8, "Naturgaspris"),
    "GASREGW": ("u", 2, "Benzinpris"), "GASDESW": ("u", 2, "Dieselpris"),
    "WPU0652": ("m", 18, "Goedningspriser (producent)"), "WPU065201": ("m", 18, "Kvaelstofgoedning (producent)"),
    "WPU012": ("m", 18, "Kornpriser (producent)"), "WPU102": ("m", 18, "Metalpriser (producent)"),
    "REVOLSL": ("m", 40, "Forbrugerkredit (kort og lignende)"), "CCLACBW027SBOG": ("u", 9, "Kreditkortlaan i banker"),
    "DRCCLACBS": ("q", 60, "Kreditkort i restance"), "CORCCACBS": ("q", 60, "Kreditkort afskrevet"),
    "HPIPONM226S": ("m", 60, "Huspriser (FHFA)"), "MSPUS": ("q", 30, "Median huspris, solgte huse"),
    "MSACSR": ("m", 28, "Udbud af nye huse"), "DRSFRMACBS": ("q", 60, "Boliglaan i restance"),
    "EBP": ("m", 35, "Kreditpraemie (EBP)"),
}
SLAEK = {"d": 4, "u": 4, "m": 7, "q": 10}       # dage ekstra foer en serie kaldes forsinket (weekender, helligdage)
MAANED_NAVN = "januar februar marts april maj juni juli august september oktober november december".split()


def _periodens_slut(d, frekv):
    """Sidste dag i den periode, observationen d (FRED-stempel) daekker."""
    if frekv == "m":
        n = date(d.year + (d.month == 12), d.month % 12 + 1, 1)
        return n - timedelta(days=1)
    if frekv == "q":
        m = ((d.month - 1) // 3) * 3 + 3
        n = date(d.year + (m == 12), m % 12 + 1, 1)
        return n - timedelta(days=1)
    return d


def periode_tekst(d, frekv, idag):
    """'september 2026', '2. kvartal 2026', 'uge til 17. okt.', '23. okt.' — til folk, ikke til koden."""
    if frekv == "m":
        return f"{MAANED_NAVN[d.month - 1]} {d.year}"
    if frekv == "q":
        return f"{(d.month - 1) // 3 + 1}. kvartal {d.year}"
    kort = MAANED_NAVN[d.month - 1][:3] + "."
    return (f"uge til {d.day}. {kort}" if frekv == "u" else f"{d.day}. {kort}") + ("" if d.year == idag.year else f" {d.year}")


def datastatus(sid, sidste, idag):
    """Udgivelseskalenderen for een serie: hvornaar burde naeste tal vaere kommet, og er det kommet?
    -> dict(serie, navn, frekvens, sidste, periode, naeste_ventes, status, tekst) eller None (ukendt serie).
    status: 'aktuel' (naeste tal er endnu ikke forfaldent) eller 'forsinket' (forfaldent + slaek er passeret)."""
    if sid not in UDGIVELSE or not sidste:
        return None
    frekv, lag, navn = UDGIVELSE[sid]
    d = date.fromisoformat(sidste[:10] if len(sidste) >= 10 else sidste + "-01")
    if frekv in ("d", "u"):
        naeste_slut = d + timedelta(days=1 if frekv == "d" else 7)
    else:
        naeste_slut = _periodens_slut(_periodens_slut(d, frekv) + timedelta(days=1), frekv)
    ventes = naeste_slut + timedelta(days=lag)
    forsinket = idag > ventes + timedelta(days=SLAEK[frekv])
    per = periode_tekst(d, frekv, idag)
    vt = f"{ventes.day}. {MAANED_NAVN[ventes.month - 1]}" + ("" if ventes.year == idag.year else f" {ventes.year}")
    if forsinket:
        tekst = f"Forsinket: nyeste tal er fra {per}; det naeste burde vaere kommet omkring {vt}."
    elif idag >= ventes:
        tekst = f"Nyeste tal er fra {per}; det naeste kan komme naar som helst."
    else:
        tekst = f"Nyeste tal er fra {per}; det naeste ventes omkring {vt}."
    return dict(serie=sid, navn=navn, frekvens=frekv, sidste=sidste[:10], periode=per, naeste_ventes=ventes.isoformat(),
                status="forsinket" if forsinket else "aktuel", tekst=tekst)


# ---- tal der foer blev tastet ind i manual.json, nu beregnet af snapshottets egne filer (2026-10-27) ----
def spx_fra_top(rows):
    """S&P 500's seneste luk mod hoejeste luk de seneste 365 dage (samme regel som manual.json brugte).
    rows = [(YYYY-MM-DD, vaerdi)]. -> dict(vaerdi, dato, top, top_dato) eller None."""
    rk = [(d, float(v)) for d, v in rows if v not in (None, "", ".")]
    if not rk:
        return None
    d0, v0 = rk[-1]
    fra = (date.fromisoformat(d0) - timedelta(days=365)).isoformat()
    top_d, top_v = max(((d, v) for d, v in rk if d > fra), key=lambda t: t[1])
    return dict(vaerdi=round(v0 / top_v - 1, 4), dato=d0, luk=v0, top=top_v, top_dato=top_d)


def multpl_live(html):
    """multpl's seneste (live) CAPE-raekke, fx 'Oct 26, 2026'. -> dict(vaerdi, dato) eller None."""
    if isinstance(html, bytes):
        html = html.decode("utf-8", "replace")
    m = re.search(r"<td>([A-Z][a-z]{2}) (\d{1,2}), (\d{4})</td>\s*<td>\s*(?:&#x2002;)?\s*([\d.]+)", html)
    if not m:
        return None
    MON = {k: i for i, k in enumerate("Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split(), 1)}
    return dict(vaerdi=float(m.group(4)), dato=f"{m.group(3)}-{MON[m.group(1)]:02d}-{int(m.group(2)):02d}")


def finra_margin(xlsx):
    """FINRA's margin-statistics.xlsx (raa bytes) -> laanesaldo i seneste maaned mod samme maaned aaret foer.
    Laeses med stdlib (xlsx er en zip med XML). -> dict(vaerdi (%), periode, saldo, saldo_aaret_foer)."""
    z = zipfile.ZipFile(io.BytesIO(xlsx))
    ark = z.read("xl/worksheets/sheet1.xml").decode("utf-8")
    rk = {}
    for raekke in re.findall(r"<row[^>]*>(.*?)</row>", ark, re.S):
        a = re.search(r'<c r="A\d+"[^>]*>(?:<is><t>|<v>)([^<]*)<', raekke)
        b = re.search(r'<c r="B\d+"[^>]*><v>([^<]*)</v>', raekke)
        if a and b and re.fullmatch(r"\d{4}-\d{2}", a.group(1).strip()):
            rk[a.group(1).strip()] = float(b.group(1))
    if not rk:
        raise RuntimeError("FINRA-filen har ingen 'YYYY-MM'-raekker med debit balances — formatet er aendret?")
    sidst = max(rk)
    foer = f"{int(sidst[:4]) - 1}{sidst[4:]}"
    if foer not in rk:
        raise RuntimeError(f"FINRA-filen mangler {foer} (samme maaned aaret foer {sidst})")
    return dict(vaerdi=round((rk[sidst] / rk[foer] - 1) * 100, 1), periode=sidst, saldo=rk[sidst], saldo_aaret_foer=rk[foer])


def _mk(d):
    return d[:7]


def monthly_mean(rows):
    """[(YYYY-MM-DD, vaerdi)] -> {YYYY-MM: middel}. Ignorerer '.'/tomme."""
    agg = {}
    for d, v in rows:
        if v in (".", "", None):
            continue
        agg.setdefault(_mk(d), []).append(float(v))
    return {k: statistics.mean(v) for k, v in agg.items()}


def parse_multpl(html, today=None):
    """multpl 'by-month'-tabel -> {YYYY-MM: cape}, kun raekker dateret den 1. i en LUKKET maaned. Bemaerk (F25):
    'lukket' er et datofilter; multpl's seneste maanedsraekke er foreloebig og kan revideres — fetch
    diff'er derfor mod forrige snapshot og gemmer reviderede maaneder i meta.spine.multpl.revideret.
    Haarde assertions: formatet maa ikke drive stille."""
    if isinstance(html, bytes):
        html = html.decode("utf-8", "replace")
    rows = re.findall(r"<td>([A-Z][a-z]{2}) (\d{1,2}), (\d{4})</td>\s*<td>\s*(?:&#x2002;)?\s*([\d.]+)", html)
    if len(rows) < MULTPL_MIN_RAEKKER:
        raise RuntimeError(f"multpl: kun {len(rows)} raekker (< {MULTPL_MIN_RAEKKER}) — formatet er aendret?")
    MON = {m: i for i, m in enumerate("Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split(), 1)}
    today = today or date.today()
    aaben = f"{today.year:04d}-{today.month:02d}"
    out = {}
    for mon, day, year, val in rows:
        if day != "1":
            continue                         # live-raekken (fx 'Sep 18, 2026') er ikke en maanedsvaerdi
        key = f"{year}-{MON[mon]:02d}"
        if key >= aaben:
            continue                         # den loebende maaned er ikke lukket
        out[key] = float(val)
    ks = sorted(out)
    if not ks or ks[0] != MULTPL_FOERSTE:
        raise RuntimeError(f"multpl: foerste maaned er {ks[:1]}, forventede {MULTPL_FOERSTE}")
    return out


def overlap_check(shiller_rows, sp500_m, cape_m):
    """shiller_rows: {YYYY-MM: (sp500, cpi, ltr, cape)}. Returnerer statistik + bestaaet-flag (§1.2)."""
    sp = [(k, 100 * (sp500_m[k] / v[0] - 1)) for k, v in shiller_rows.items()
          if k in sp500_m and v[0] and k not in PRELIMINAERE]
    ca = [(k, 100 * (cape_m[k] / v[3] - 1)) for k, v in shiller_rows.items()
          if k in cape_m and v[3] and k >= "1990-01" and k not in PRELIMINAERE]
    res = dict(sp500_n=len(sp), cape_n=len(ca))
    if sp:
        a = [abs(x) for _, x in sp]
        res.update(sp500_median_abs_pct=round(statistics.median(a), 4),
                   sp500_andel_inden_1pct=round(sum(x <= 1.0 for x in a) / len(a), 4),
                   sp500_max_abs_pct=round(max(a), 4),
                   sp500_undtagelser=[k for k, x in sp if abs(x) > 1.0])
    if ca:
        a = [abs(x) for _, x in ca]
        res.update(cape_median_abs_pct=round(statistics.median(a), 4),
                   cape_max_abs_pct=round(max(a), 4),
                   cape_undtagelser=[k for k, x in ca if abs(x) > 1.0])
    res["preliminaere_afvigelser_pct"] = {
        k: dict(sp500=round(100 * (sp500_m[k] / shiller_rows[k][0] - 1), 3) if k in sp500_m and k in shiller_rows else None,
                cape=round(100 * (cape_m[k] / shiller_rows[k][3] - 1), 3) if k in cape_m and k in shiller_rows else None)
        for k in PRELIMINAERE}
    res["bestaaet"] = bool(
        sp and ca
        and res["sp500_median_abs_pct"] <= TOL["sp500_median"]
        and res["sp500_andel_inden_1pct"] >= TOL["sp500_andel_inden_1pct"]
        and res["cape_median_abs_pct"] <= TOL["cape_median"]
        and res["cape_max_abs_pct"] <= TOL["cape_max"])
    return res


def outlier_check(cape_m, fra=None, accepterede=None):
    """[(maaned, problem)] for CAPE uden for niveau-baandet eller med |m/m| >= CAPE_MM_MAX (§1.6).
    `accepterede` = {maaned: cape} fra manual/outliers_accepteret.json (F31): et (maaned, vaerdi)-par
    der een gang er accepteret med --accept-outlier, udloeser ikke guarden igen ved hver hentning —
    men en senere REVISION af vaerdien (andet tal for samme maaned) fanges igen."""
    acc = {(k, round(float(v), 4)) for k, v in (accepterede or {}).items()}
    ks = sorted(k for k in cape_m if fra is None or k >= fra)
    bad = []
    for i, k in enumerate(ks):
        v = cape_m[k]
        if (k, round(float(v), 4)) in acc:
            continue
        if not (CAPE_NIVEAU[0] <= v <= CAPE_NIVEAU[1]):
            bad.append((k, f"niveau {v:.2f} uden for [{CAPE_NIVEAU[0]:.0f}, {CAPE_NIVEAU[1]:.0f}]"))
        if i > 0:
            mm = 100 * abs(v / cape_m[ks[i - 1]] - 1)
            if mm >= CAPE_MM_MAX:
                bad.append((k, f"m/m-aendring {mm:.1f} % >= {CAPE_MM_MAX:.0f} %"))
    return bad


def build_spine(shiller_rows, sp500_m, cpi_m, gs10_m, cape_m, tidligere_sp500=None):
    """-> [(YYYY-MM, sp500, cpi, ltr, cape, kilde)], Shiller t.o.m. SEAM, komposit derefter saa
    langt SP500 og CAPE begge findes (de to kilder der definerer kompositten; en delvis
    komposit-maaned uden dem accepteres aldrig, §1.7). CPI maa mangle (KENDTE_CPI_HULLER; et NYT hul
    meldes hoejlydt af fetch) for en maaned
    (BLS udgav aldrig oktober 2025) — feltet skrives tomt -> NaN, som Shillers egne huller;
    kvartalsaggregeringen tager sidste ikke-NaN maaned, saa ingen kvartalsfeature tabes.

    `tidligere_sp500` = {YYYY-MM: sp500} fra forrige komplette snapshots spine.csv (F2): FRED
    leverer SP500 som et RULLENDE 10-aars vindue, saa fra 2033 falder de foerste komposit-maaneder
    ud af kilden. Allerede lukkede maaneder baeres da uaendret videre fra forrige rygrad (samme
    tal, ingen ny estimering); maaneder FRED stadig leverer tages altid fra FRED."""
    tidligere_sp500 = tidligere_sp500 or {}
    sp500_m = {**{k: v for k, v in tidligere_sp500.items() if k > SEAM}, **sp500_m}
    out = []
    for k in sorted(shiller_rows):
        if k <= SEAM:
            sp, cpi, ltr, cape = shiller_rows[k]
            out.append((k, sp, cpi, ltr, cape, "shiller"))
    k = SEAM
    while True:
        y, m = int(k[:4]), int(k[5:7])
        m += 1
        if m > 12:
            y, m = y + 1, 1
        k = f"{y:04d}-{m:02d}"
        if k not in sp500_m or k not in cape_m:
            break
        out.append((k, sp500_m[k], cpi_m.get(k), gs10_m.get(k), cape_m[k], "fred+multpl"))
    return out


KENDTE_CPI_HULLER = {"2025-10"}            # BLS udgav aldrig oktober 2025 (shutdown); motor interpolerer hoejlydt

def cpi_huller(rows):
    """Komposit-maaneder uden CPI -> (aegte huller midt i serien, fx 2025-10; endnu ikke udgivne i halen).
    Foer blev en ikke-udgivet sidste maaned (fx 2026-09 den 10/10) ogsaa kaldt et 'aegte hul'."""
    komp = [r for r in rows if r[5] != "shiller"]
    sidst = max((r[0] for r in komp if r[2] is not None), default="")
    return ([r[0] for r in komp if r[2] is None and r[0] < sidst],
            [r[0] for r in komp if r[2] is None and r[0] > sidst])


def staleness(sidste_dato, today=None, regler=None):
    """{serie: 'YYYY-MM-DD'} -> {serie: dict(alder_dage, graense, kritisk)} for de der er for gamle."""
    today = today or date.today()
    regler = regler or FRISKHED_DAGE
    stale = {}
    for sid, d in sidste_dato.items():
        if sid not in regler or not d:
            continue
        try:
            alder = (today - date.fromisoformat(d[:10] if len(d) >= 10 else d + "-01")).days
        except ValueError:
            continue
        if alder > regler[sid]:
            stale[sid] = dict(alder_dage=alder, graense=regler[sid], kritisk=sid in KRITISKE, sidste=d)
    return stale
