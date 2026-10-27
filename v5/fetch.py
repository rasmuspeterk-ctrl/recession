#!/usr/bin/env python3
"""
fetch.py — v5 datalag (trin 1 i raadets byggeorden).

Henter alle serier noeglefrit via fredgraph.csv (parallelt; EBP fra Fed Boards CSV), skriver et
dateret, byte-eksakt hashet snapshot i data/raw/<YYYY-MM-DD>/ og printer diff mod forrige
snapshot til menneskeligt eftersyn (raadets T6): ny observation, aendret sidste vaerdi, stille
revision af historikken — og for de rullende licensvinduer (SP500, HY OAS) blot 'start flyttet'.

Seriernes roller staar i EEN tabel, spine.SERIER (kode-review 2026-10-15, F18): kun serierne med
rolle P/refit (spine.VETO) nedlaegger veto, naar de fejler; alt andet er kontekst. Licensmaerket
'lokal' (ICE HY OAS, S&P 500, Moody's Baa og multpl-siden) hentes og hashes, men committes aldrig
(.gitignore) — meta.json beholder sha256/first/last/last_value (F1/F12).

Snapshottet bygges i data/raw/<dato>.ny og flyttes foerst paa plads naar alt er hentet: fejler en
vetoserie eller mangler manual.json/rygraden, gemmes forsoeget som data/raw/<dato>.ukomplet
("complete": false; ignoreres af calibrate/motor), og et eksisterende komplet dagssnapshot roeres
ikke. En senere vellykket koersel samme dag sletter det afloeste .ukomplet-forsoeg (F24).

Rygraden (v5.0.1, RAADETS_V501 §1): Yales ie_data.xls er frosset ved 2023-09, saa snapshottets
spine.csv bygges som komposit — manual/shiller_yale_2023-09.csv (uforanderlig kopi) byte-identisk
t.o.m. 2023-07, derefter FRED SP500 (dagligt -> maanedsmiddel), CPIAUCNS, GS10 som LTR og multpl's
maanedlige CAPE, med proveniens-kolonne. Overlap-tolerancer (§1.2; FRED's foerste, delvise maaned
indgaar aldrig — F2), multpl-assertions og revisionsdiff (§1.3, F25), outlier-guard (§1.6,
`--accept-outlier "<hvad blev tjekket; hvorfor>"`; accepterede (maaned, vaerdi)-par gemmes i
manual/outliers_accepteret.json, F31) og den udgivelses-bevidste friskheds-guard (§1.7) haandhaeves
her. Snapshottet faar `spine.refit_klar` (F5): false hvis multpl eller SP500 fejlede, eller rygraden
er stale — saa naegter finalize6/diagnostik at rekalibrere, mens den maanedlige laesning fortsaetter.

Manuelle inputs (dokumenteret protokol, raadets Section 9):
  manual/manual.json  — {"spx_vs_hi": .., "cape": .., "margin_yoy": .., "as_of": "YYYY-MM-DD",
                         "margin_periode": "YYYY-MM", "cape_dato": "YYYY-MM-DD", "spx_dato": "YYYY-MM-DD"}
                        (S&P vs 12m-hoejde som decimal, live Shiller-CAPE fra multpl.com, FINRA
                        marginlaan y/y % og hvilken datamaaned/-dag tallene gaelder, F30).
  Fra 2026-10-27 beregner fetch selv de tre tal (meta.json -> "afledte"): S&P fra FRED SP500, CAPE fra
  multpl-sidens live-raekke og marginlaan fra FINRA's margin-statistics.xlsx. manual.json er derefter kun
  reserve: motor bruger det nyeste af de to og viser hvilken kilde, der blev brugt.

Kun stdlib. Koer:  python fetch.py
"""
import csv, hashlib, io, json, re, shutil, sys, time, urllib.error, urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone
from pathlib import Path

import spine as SP

HERE = Path(__file__).parent
RAW = HERE / "data" / "raw"
MANUAL = HERE / "manual"
LOG = HERE.parent / "LOG.md"
WORKERS = 8          # parallelle kald: 37 serier ~3-5 s parallelt

# Serier og hvorfor de hentes: afledt af spine.SERIER (+ ikke-FRED-kilder i spine.EKSTERNE)
SERIES = {sid: v[3] for sid, v in SP.SERIER.items()}
SERIES.update({sid: v["formaal"] for sid, v in SP.EKSTERNE.items()})
MULTPL_URL = "https://www.multpl.com/shiller-pe/table/by-month"
YALE = "shiller_yale_2023-09.csv"          # uforanderlig kopi af Yales ie_data.xls (sidste raekke 2023.09)
OUTLIERS_ACC = "outliers_accepteret.json"  # F31: accepterede (maaned, vaerdi)-par, committes

def parse_rows(raw, kolonne=None):
    """FRED-csv-bytes -> [(dato, vaerdi)] uden manglende ('.'/tomme) observationer. `kolonne`
    vaelger en navngiven vaerdikolonne i en bredere CSV (EBP-filen); ellers kraeves praecis 2 kolonner."""
    rows = list(csv.reader(io.StringIO(raw.decode("utf-8-sig"))))
    if kolonne is not None:
        if len(rows) < 2 or kolonne not in rows[0]:
            raise RuntimeError(f"uventet format (kolonne {kolonne!r} mangler: {rows[:1]})")
        j = rows[0].index(kolonne)
        return [(r[0], r[j]) for r in rows[1:] if len(r) > j and r[j] not in (".", "")]
    if len(rows) < 2 or len(rows[0]) != 2:
        raise RuntimeError(f"uventet format ({rows[:1]})")
    return [(d, v) for d, v in rows[1:] if v not in (".", "")]

def fetch_series(sid, attempts=3):
    """Raa bytes + parsede raekker. Netvaerksfejl, 5xx, 429 (ratelimit) og misdannede
    svar proeves igen; oevrige 4xx (ukendt serie) ikke."""
    ekst = SP.EKSTERNE.get(sid)
    url = ekst["url"] if ekst else f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (MOTOR v5 fetch)"}) if ekst else url
    last_err = None
    for k in range(attempts):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                raw = r.read()
            data = parse_rows(raw, ekst["kolonne"] if ekst else None)   # inde i forsoeget: et flygtigt ikke-CSV-svar retries
            if not data:
                raise RuntimeError("tom serie")
            return raw, data
        except urllib.error.HTTPError as e:
            if 400 <= e.code < 500 and e.code != 429:
                raise
            last_err = e
        except Exception as e:
            last_err = e
        if k < attempts - 1:
            time.sleep(2 * (k + 1))
    raise RuntimeError(f"opgivet efter {attempts} forsoeg ({last_err})")

def logget_snapshots():
    """Snapshot-datoerne i hovedbogens snapshot-kolonne (LOG.md)."""
    if not LOG.exists():
        return set()
    return {c[2].strip() for c in (ln.split("|") for ln in LOG.read_text(encoding="utf-8").splitlines()
                                   if ln.startswith("| 2")) if len(c) > 2}

def sha256(b):
    return hashlib.sha256(b).hexdigest()

def snapshot_complete(d):
    """Komplethedsflaget som calibrate laeser det (dubleret her: fetch er stdlib-only, calibrate traekker numpy)."""
    m = d / "meta.json"
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", d.name) or not m.exists():    # '<dato>.ny'/'.ukomplet' er ikke snapshots
        return False
    try:
        return bool(json.loads(m.read_text(encoding="utf-8")).get("complete", True))
    except ValueError:
        return False

def skift_paa_plads(ny, final):
    """Flyt et komplet <dato>.ny paa plads som <dato> (2026-10-24). Det gamle dagssnapshot OMDOEBES foerst til
    <dato>.gammel og slettes foerst, naar det nye staar paa plads. Kan det gamle ikke flyttes (paa Windows fx fordi
    en terminal eller et program har mappen som arbejdsmappe), er INTET roert: det gamle snapshot er intakt, det nye
    ligger komplet i <dato>.ny, og fetch stopper hoejlydt. Foer blev det gamle toemt med rmtree, rename fejlede, og
    motor faldt tilbage til et aeldre snapshot (mellemlaesningen 2026-10-23)."""
    gammel = final.with_name(final.name + ".gammel")
    if gammel.exists():
        shutil.rmtree(gammel)
    if final.exists():
        try:
            final.rename(gammel)
        except OSError as e:
            sys.exit(f"FEJL: kan ikke flytte {final.name} (laast? luk terminaler/programmer, der staar i mappen): {e}\n"
                     f"Det gamle snapshot er uroert; det nye, komplette ligger i {ny.name}. Koer fetch.py igen.")
    try:
        ny.rename(final)
    except OSError as e:
        if gammel.exists() and not final.exists():
            gammel.rename(final)              # rul tilbage: det gamle snapshot paa plads igen
        sys.exit(f"FEJL: kan ikke flytte {ny.name} paa plads: {e}\nDet gamle snapshot er genetableret. Koer fetch.py igen.")
    if gammel.exists():
        try:
            shutil.rmtree(gammel)
        except OSError as e:
            print(f"ADVARSEL: {gammel.name} kunne ikke slettes ({e}); det ignoreres af motor/calibrate — slet den manuelt.")


def last_snapshot_before(today_dir):
    """Diff-baseline = nyeste KOMPLETTE snapshot (samme valg som calibrate/motor), ikke blot nyeste mappe."""
    if not RAW.exists():
        return None
    dirs = sorted(d for d in RAW.iterdir() if d.is_dir() and d != today_dir and snapshot_complete(d))
    return dirs[-1] if dirs else None

def diff_mark(prev_s, prev_dir, sid, data, cur):
    """Diff mod forrige snapshot: hash, sidste observation, og (for at fange stille revisioner)
    om det gamle snapshots vaerdier er uaendrede paa de FAELLES datoer (F23). En observation der
    er forsvundet midt i det nye vindue er ogsaa en revision. At vinduets START er flyttet (FRED's
    rullende licensvinduer for SP500 og HY OAS) er ikke en revision og markeres for sig. Mangler
    seriens meta-post, men filen findes, koeres tjekket alligevel."""
    pf = (prev_dir / f"{sid}.csv") if prev_dir else None
    if prev_s is None and not (pf and pf.exists()):
        return "  (ny serie)"
    if prev_s and prev_s.get("sha256") == cur["sha256"]:
        return ""
    marks = []
    if prev_s is None:
        marks.append("mangler i forrige meta")
    elif prev_s.get("last") != cur["last"]:
        marks.append("ny obs")
    elif prev_s.get("last_value") != cur["last_value"]:
        marks.append("AENDRET sidste vaerdi")
    if pf and pf.exists():
        try:
            ekst = SP.EKSTERNE.get(sid)
            old = dict(parse_rows(pf.read_bytes(), ekst["kolonne"] if ekst else None))
            new = dict(data)
            start = min(new) if new else ""
            faelles = [d for d in old if d in new]
            forsvundet = [d for d in old if d not in new and d >= start]
            foran = [d for d in old if d < start]          # raekker faldet af FORAN: kun ok for de rullende vinduer
            indsat = [d for d in new if d not in old and old and d <= max(old) and (sid not in ROLLING or d >= min(old))]
            if any(old[d] != new[d] for d in faelles) or forsvundet or indsat or (foran and sid not in ROLLING):
                marks.append("REVIDERET historik")
            if foran and sid in ROLLING:
                marks.append(f"rullende vindue (start flyttet {min(old)} -> {start})")
        except Exception:
            marks.append("forrige fil ulaeselig")
    return "  <-- " + (", ".join(marks) if marks else "andet indhold")

ROLLING = {"SP500", "BAMLH0A0HYM2"}       # FRED serverer kun et rullende vindue (~10 / ~3 aar): frafald foran er ingen revision
RESERVE = {s for s in SERIES if s not in SP.VETO}      # fejl her nedlaegger ikke veto (F18)
# (SP500: rygraden baeres videre / refit_klar=false; DFF: motor falder tilbage til FEDFUNDS)
KRAEVEDE_MANUAL = ("manual.json",)                 # calibrate/motor kan ikke koere uden

def fetch_multpl(attempts=3):
    """multpl's maanedlige CAPE-tabel (HTML) — raa bytes hashes som en FRED-serie."""
    req = urllib.request.Request(MULTPL_URL, headers={"User-Agent": "Mozilla/5.0 (MOTOR v5 fetch)"})
    last_err = None
    for k in range(attempts):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except Exception as e:
            last_err = e
            time.sleep(3 * (k + 1))
    raise RuntimeError(f"multpl opgivet efter {attempts} forsoeg ({last_err})")

FINRA_URL = "https://www.finra.org/sites/default/files/2021-03/margin-statistics.xlsx"


def fetch_finra(attempts=3):
    """FINRA's margin-statistik (xlsx). Licensbegraenset som multpl-siden: gemmes lokalt, committes aldrig."""
    req = urllib.request.Request(FINRA_URL, headers={"User-Agent": "Mozilla/5.0 (MOTOR v5 fetch)"})
    last_err = None
    for k in range(attempts):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except Exception as e:
            last_err = e
            time.sleep(3 * (k + 1))
    raise RuntimeError(f"FINRA opgivet efter {attempts} forsoeg ({last_err})")


def afledte_tal(outdir, series_data, hent_finra=True):
    """De tre tal manual.json foer kraevede i haanden, beregnet af snapshottets egne filer (2026-10-27).
    En fejl her koster kun det enkelte tal (motor falder tilbage til manual.json), aldrig snapshottet."""
    ud = {}
    try:
        r = SP.spx_fra_top(series_data["SP500"]) if "SP500" in series_data else None
        ud["spx_vs_hi"] = (r | dict(kilde="FRED SP500: seneste luk mod hoejeste luk de seneste 12 maaneder")
                           if r else dict(fejl="SP500 blev ikke hentet"))
    except Exception as e:
        ud["spx_vs_hi"] = dict(fejl=str(e)[:200])
    try:
        f = outdir / "multpl_cape.html"
        r = SP.multpl_live(f.read_bytes()) if f.exists() else None
        ud["cape"] = r | dict(kilde="multpl.com/shiller-pe, seneste raekke") if r else dict(fejl="multpl-siden mangler eller har intet live-tal")
    except Exception as e:
        ud["cape"] = dict(fejl=str(e)[:200])
    if hent_finra:
        try:
            b = fetch_finra()
            (outdir / "finra_margin.xlsx").write_bytes(b)
            ud["margin_yoy"] = SP.finra_margin(b) | dict(kilde="FINRA margin statistics (debit balances, samme maaned aaret foer)",
                                                          sha256=sha256(b))
        except Exception as e:
            ud["margin_yoy"] = dict(fejl=str(e)[:200])
    return ud


def read_yale(path):
    """{YYYY-MM: (sp500, cpi, ltr, cape)} fra den uforanderlige Yale-kopi (tomme felter -> None)."""
    out = {}
    with path.open(encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            def num(k):
                v = (row.get(k) or "").strip()
                return float(v) if v not in ("", ".") else None
            out[row["Date"].strip()] = (num("SP500"), num("CPI"), num("LTR"), num("CAPE"))
    return out

def read_cape_csv(path):
    """cape_multpl.csv -> {YYYY-MM: cape} ({} hvis filen mangler eller er ulaeselig)."""
    try:
        with path.open(encoding="utf-8") as fh:
            return {r["Date"]: float(r["CAPE"]) for r in csv.DictReader(fh)}
    except Exception:
        return {}

def read_spine_sp500(path):
    """Komposit-raekkernes SP500 fra en tidligere spine.csv -> {YYYY-MM: sp500} (F2-baering)."""
    try:
        with path.open(encoding="utf-8") as fh:
            return {r["Date"]: float(r["SP500"]) for r in csv.DictReader(fh)
                    if r.get("Kilde") != "shiller" and r.get("SP500")}
    except Exception:
        return {}

def read_spine_cape(path):
    """Komposit-raekkernes CAPE fra en tidligere spine.csv -> {YYYY-MM: cape} (revisionsdiff-fallback, F25)."""
    try:
        with path.open(encoding="utf-8") as fh:
            return {r["Date"]: float(r["CAPE"]) for r in csv.DictReader(fh)
                    if r.get("Kilde") != "shiller" and r.get("CAPE")}
    except Exception:
        return {}

def rygrad_kilde(today_dir):
    """Nyeste KOMPLETTE snapshot med intakt rygrad (komposit + bestaaet overlap): kilden til F2-baeringen af
    lukkede SP500-maaneder og til overlap-arven. Et enkelt multpl-udfald (komplet snapshot, tom komposit) maa
    aldrig bryde kaeden."""
    if not RAW.exists():
        return None
    for d in sorted((d for d in RAW.iterdir() if d.is_dir() and d != today_dir and snapshot_complete(d)), reverse=True):
        try:
            sp = json.loads((d / "meta.json").read_text(encoding="utf-8")).get("spine", {})
        except ValueError:
            continue
        if sp.get("komposit_maaneder") and sp.get("overlap", {}).get("bestaaet") and (d / "spine.csv").exists():
            return d
    return None

def monthly_last(data):
    """FRED-maanedsserie [(YYYY-MM-DD, v)] -> {YYYY-MM: float} (stemplet den 1.)."""
    return {d[:7]: float(v) for d, v in data}

def byg_rygrad(outdir, series_data, argv, today, prev=None):
    """Bygger spine.csv (§1) + koerer overlap/outlier/revisions-guards. Returnerer (meta-blok, kritiske_fejl).
    `prev` = forrige komplette snapshot (multpl-revisionsdiff, F25; baering af lukkede SP500-maaneder, F2)."""
    info, kritiske = {}, []
    yale_src = MANUAL / YALE
    if not yale_src.exists():
        return {"fejl": f"manual/{YALE} mangler"}, [f"manual/{YALE}"]
    shutil.copy(yale_src, outdir / YALE)
    yb = yale_src.read_bytes()
    info["yale"] = dict(fil=YALE, sha256=sha256(yb), bytes=len(yb))
    yale = read_yale(yale_src)

    # multpl
    try:
        html = fetch_multpl()
        (outdir / "multpl_cape.html").write_bytes(html)
        cape_m = SP.parse_multpl(html, today)
        info["multpl"] = dict(sha256=sha256(html), bytes=len(html), maaneder=len(cape_m),
                              foerste=min(cape_m), sidste=max(cape_m),
                              note="seneste maanedsraekke er multpl's foreloebige vaerdi og kan revideres (§1.3)")
        with (outdir / "cape_multpl.csv").open("w", encoding="utf-8", newline="\n") as fh:   # LF paa alle maskiner
            fh.write("Date,CAPE\n" + "".join(f"{k},{cape_m[k]}\n" for k in sorted(cape_m)))
        # §1.3 revisionsmarkering (F25): diff mod forrige snapshots LOKALE kopi (filen committes ikke, F12);
        # mangler den (frisk klon, eller multpl fejlede sidst), bruges den committede spine.csv's CAPE-kolonne
        gl = read_cape_csv(prev / "cape_multpl.csv") if prev else {}
        kilde_gl = "cape_multpl.csv"
        if not gl and prev and (prev / "spine.csv").exists():
            gl, kilde_gl = read_spine_cape(prev / "spine.csv"), "spine.csv (komposit-maaneder)"
        if gl:
            rev = {k: [gl[k], cape_m[k]] for k in sorted(set(gl) & set(cape_m)) if abs(gl[k] - cape_m[k]) > 1e-9}
            info["multpl"]["revideret"] = rev
            info["multpl"]["diff_mod"] = f"{prev.name}/{kilde_gl}"
        else:
            info["multpl"]["revisionsdiff"] = "ikke mulig (intet forrige snapshot med CAPE)"
    except Exception as e:
        info["multpl"] = dict(fejl=str(e)[:300])
        cape_m = {}
    sp_d = series_data.get("SP500"); cpi_d = series_data.get("CPIAUCNS"); gs_d = series_data.get("GS10")
    sp500_m = SP.monthly_mean(sp_d) if sp_d else {}
    # daglig SP500: en maaned taeller kun som lukket hvis den er FOER hentemaaneden — og FRED's
    # rullende 10-aars vindue starter midt i en maaned, saa den FOERSTE maaned er delvis (F2): den
    # indgaar hverken i overlap-tjekket eller i kompositten (dokumenteret undtagelse, §1.2)
    sp500_m = {k: v for k, v in sp500_m.items() if k < today.isoformat()[:7]}
    if sp500_m:
        info["sp500_delvis_foerste_maaned_udeladt"] = min(sp500_m)
        sp500_m = {k: v for k, v in sp500_m.items() if k != min(sp500_m)}
    cpi_m = monthly_last(cpi_d) if cpi_d else {}
    gs10_m = monthly_last(gs_d) if gs_d else {}
    kilde = rygrad_kilde(outdir) or prev
    tidl = read_spine_sp500(kilde / "spine.csv") if kilde and (kilde / "spine.csv").exists() else {}

    # §1.2 overlap (kun hvis begge kilder kom hjem)
    if sp500_m and cape_m:
        ov = SP.overlap_check(yale, sp500_m, cape_m)        # sp500_m er allerede uden den delvise foerste maaned (F2)
        kilde = rygrad_kilde(outdir) if min(sp500_m) > "2022-08" else None
        if kilde is not None and ov["sp500_n"] < 12:
            # Fra ~2033 overlapper FRED's 10-aars vindue ikke laengere Shiller. KUN SP500-delen arves (fra nyeste
            # komplette snapshot med intakt rygrad); CAPE-overlappet (multpl mod Shiller) tjekkes stadig live.
            gl_ov = json.loads((kilde / "meta.json").read_text(encoding="utf-8")).get("spine", {}).get("overlap", {})
            if gl_ov.get("bestaaet"):
                cape_ok = bool(ov.get("cape_n")) and ov["cape_median_abs_pct"] <= SP.TOL["cape_median"] \
                    and ov["cape_max_abs_pct"] <= SP.TOL["cape_max"]
                ov = dict(ov, **{k: v for k, v in gl_ov.items() if k.startswith("sp500")},
                          sp500_arvet_fra=gl_ov.get("sp500_arvet_fra", kilde.name), bestaaet=cape_ok,
                          note="SP500-overlap verificeret tidligere (vinduet er rullet forbi Shiller); CAPE tjekket live")
        info["overlap"] = ov
        if not ov["bestaaet"]:
            kritiske.append("rygrad: overlap-tolerancer (§1.2) ikke overholdt")
    # §1.6 outlier-guard paa komposit-delen; allerede accepterede (maaned, vaerdi)-par springes over (F31)
    acc_f = MANUAL / OUTLIERS_ACC
    acc = json.loads(acc_f.read_text(encoding="utf-8")) if acc_f.exists() else {}
    probs = SP.outlier_check(cape_m, fra=SP.SEAM, accepterede={k: v["cape"] for k, v in acc.items()}) if cape_m else []
    if probs:
        if "--accept-outlier" in argv:
            begr = argv[argv.index("--accept-outlier") + 1]          # valideret i main() foer noget skrives
            info["outlier_override"] = dict(observationer=[f"{k}: {p}" for k, p in probs],
                                            tjekket="multpl CAPE mod FRED SP500-maanedsmiddel og CPIAUCNS (ingen uafhaengig CAPE-kilde findes)",
                                            begrundelse=begr)
            for k, p_ in probs:
                acc[k] = dict(cape=cape_m[k], begrundelse=begr, observation=p_, accepteret=today.isoformat(),
                              tjekket=info["outlier_override"]["tjekket"])
            info["_acc_ny"] = acc                 # skrives af main() FOERST naar snapshottet er komplet
        else:
            info["outliers"] = [f"{k}: {p}" for k, p in probs]
            kritiske.append("rygrad: CAPE-outlier (§1.6) — gentag med --accept-outlier \"<hvad blev tjekket; hvorfor>\"")
    if acc:                                   # accepterede par i dette snapshots CAPE -> motor noterer dem i foerste lograekke
        info["outliers_accepteret"] = {k: v for k, v in acc.items() if k in cape_m}
    rows = SP.build_spine(yale, sp500_m, cpi_m, gs10_m, cape_m, tidligere_sp500=tidl)
    baaret = sorted(k for k in tidl if k > SP.SEAM and k not in sp500_m and any(r[0] == k for r in rows))
    if baaret:
        info["sp500_baaret_fra_forrige"] = dict(fra=kilde.name, maaneder=baaret)
    # Shiller-raekker skrives ORDRET fra Yale-kopien (§1.1: byte-identiske felter), komposit med 6 dec.
    raa = {}
    for line in yale_src.read_text(encoding="utf-8-sig").splitlines()[1:]:
        if line.strip():
            d, rest = line.split(",", 1)
            raa[d.strip()] = rest.rstrip("\r")
    with (outdir / "spine.csv").open("w", encoding="utf-8", newline="\n") as fh:
        fh.write("Date,SP500,CPI,LTR,CAPE,Kilde\n")
        for k, sp, cpi, ltr, cape, kilde in rows:
            if kilde == "shiller":
                fh.write(f"{k},{raa[k]},shiller\n")
            else:
                f = lambda v: "" if v is None else f"{v:.6f}"
                fh.write(f"{k},{f(sp)},{f(cpi)},{f(ltr)},{f(cape)},{kilde}\n")
    komposit = [r for r in rows if r[5] != "shiller"]
    huller, ikke_udgivet = SP.cpi_huller(rows)
    nye = sorted(set(huller) - SP.KENDTE_CPI_HULLER)
    if nye:
        print(f"rygrad: NYT CPI-hul midt i serien {nye} (kendte: {sorted(SP.KENDTE_CPI_HULLER)}) — motor interpolerer "
              "hoejlydt; tjek BLS/FRED og tilfoej det til spine.KENDTE_CPI_HULLER naar aarsagen er kendt.")
    info.update(seam=SP.SEAM, raekker=len(rows), sidste=rows[-1][0] if rows else None,
                komposit_maaneder=len(komposit), cpi_huller=huller, cpi_ikke_udgivet=ikke_udgivet,
                sha256=sha256((outdir / "spine.csv").read_bytes()))
    seam_f = MANUAL / "seam_check_2023.json"          # §1.4: engangs-krydstjek af de to erstattede maaneder
    if seam_f.exists():
        try:
            info["seam_check"] = json.loads(seam_f.read_text(encoding="utf-8"))
        except ValueError:
            info["seam_check"] = {"fejl": "ulaeselig seam_check_2023.json"}
    return info, kritiske

def refit_klar(spine_info, reserve_fejl, stale):
    """F5: et snapshot er kun egnet til (re)kalibrering hvis rygraden er hel og frisk. Den maanedlige
    curve-only-laesning paavirkes ikke (§1.7) — kun finalize6/diagnostik naegter at koere."""
    grunde = []
    if "fejl" in spine_info.get("multpl", {}):
        grunde.append("multpl fejlede (CAPE-kolonnen mangler efter 2023-07)")
    if "SP500" in reserve_fejl:
        grunde.append("SP500 fejlede (komposittens prisserie mangler)")
    if "spine" in stale:
        grunde.append(f"rygraden er stale (sidste {stale['spine']['sidste']})")
    if not spine_info.get("sidste"):
        grunde.append("ingen rygrad bygget")
    return not grunde, grunde

def main():
    if "--accept-outlier" in sys.argv:                  # §1.6: begrundelsen er obligatorisk — tjekkes foer <dato>.ny oprettes
        i = sys.argv.index("--accept-outlier") + 1
        if i >= len(sys.argv) or not sys.argv[i].strip() or sys.argv[i].startswith("--"):
            sys.exit('FEJL: --accept-outlier kraever en begrundelse (§1.6): --accept-outlier "<hvad blev tjekket; hvorfor>"')
    today = date.today().isoformat()
    final_dir = RAW / today
    if final_dir.exists() and today in logget_snapshots():
        sys.exit(f"FEJL: snapshot {today} er grundlaget for en hovedbogsraekke i LOG.md og erstattes ikke "
                 "(raekkens tal skal kunne genskabes fra sit snapshot). Hent igen i morgen.")
    outdir = RAW / f"{today}.ny"          # arbejdsmappe: et eksisterende komplet dagssnapshot roeres foerst ved succes
    if outdir.exists():
        shutil.rmtree(outdir)
    outdir.mkdir(parents=True)
    prev = last_snapshot_before(outdir)
    prev_series = {}
    if prev and (prev / "meta.json").exists():
        prev_series = json.loads((prev / "meta.json").read_text(encoding="utf-8")).get("series", {})

    meta = {"retrieved_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "series": {}, "manual": {}}
    print(f"=== fetch.py — snapshot {today}   (diff mod {prev.name if prev else 'intet forrige snapshot'}) ===")
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = {sid: ex.submit(fetch_series, sid) for sid in SERIES}
    print(f"{'serie':<18}{'raekker':>8}{'sidste dato':>13}{'vaerdi':>10}{'forrige':>10}")
    failed = []
    series_data, sidste_dato = {}, {}
    for sid, why in SERIES.items():
        ps = prev_series.get(sid)
        prev_v = ps.get("last_value", "") if ps else ""
        try:
            raw, data = futs[sid].result()
            (outdir / f"{sid}.csv").write_bytes(raw)      # byte-eksakt: hashen nedenfor ER filens hash
            last_d, last_v = data[-1]
            rolle, licens, kilde = (SP.SERIER[sid][:3] if sid in SP.SERIER
                                    else (SP.EKSTERNE[sid]["rolle"], SP.EKSTERNE[sid]["licens"], SP.EKSTERNE[sid]["kilde"]))
            cur = dict(rows=len(data), first=data[0][0], last=last_d, last_value=last_v,
                       sha256=sha256(raw), purpose=why, rolle=rolle, licens=licens, kilde=kilde)
            mark = diff_mark(ps, prev, sid, data, cur)  # inde i try: en fejl her koster serien, ikke snapshottet
        except Exception as e:
            failed.append(sid)
            print(f"{sid:<18}  FEJL: {e}")
            continue
        meta["series"][sid] = cur
        series_data[sid] = data
        sidste_dato[sid] = last_d
        print(f"{sid:<18}{len(data):>8}{last_d:>13}{last_v:>10}{prev_v:>10}{mark}")

    # manuelle filer kopieres byte-eksakt ind i snapshottet og hashes med
    manglende_manual = []
    for name in ("manual.json", "acm.csv"):
        src = MANUAL / name
        if src.exists():
            shutil.copy(src, outdir / name)
            b = src.read_bytes()
            meta["manual"][name] = dict(sha256=sha256(b), bytes=len(b))
            print(f"manual/{name:<12} kopieret ind i snapshot (sha256 {sha256(b)[:12]}...)")
        else:
            print(f"manual/{name:<12} MANGLER — se docstring for format")
            if name in KRAEVEDE_MANUAL:
                manglende_manual.append(f"manual/{name}")

    # ---- rygraden (§1) + friskheds-guard (§1.7) ----
    idag = date.fromisoformat(today)
    spine_info, spine_krit = byg_rygrad(outdir, series_data, sys.argv, idag, prev=prev)
    acc_ny = spine_info.pop("_acc_ny", None)
    meta["spine"] = spine_info
    if spine_info.get("sidste"):
        sidste_dato["spine"] = spine_info["sidste"] + "-01"
    meta["afledte"] = afledte_tal(outdir, series_data, hent_finra="--uden-finra" not in sys.argv)
    for k, v in meta["afledte"].items():
        print(f"automatisk {k:<10} " + (f"FEJL: {v['fejl']} (motor bruger manual.json)" if "fejl" in v else
                                        f"{v['vaerdi']} ({v.get('dato') or v.get('periode')}; {v['kilde']})"))
    stale = SP.staleness(sidste_dato, idag)
    if stale:
        meta["stale"] = stale
        for sid, v in stale.items():
            print(f"FRISKHED: {sid:<12} sidste {v['sidste']} er {v['alder_dage']} dage gammel (graense {v['graense']})"
                  + ("  <-- KRITISK" if v["kritisk"] else ""))
    stale_krit = [f"friskhed: {sid}" for sid, v in stale.items() if v["kritisk"]]
    if spine_info.get("sidste"):
        print(f"rygrad: spine.csv {spine_info['raekker']} raekker, Shiller t.o.m. {SP.SEAM}, komposit "
              f"{spine_info['komposit_maaneder']} mdr -> {spine_info['sidste']}"
              + (f"; overlap SP500 median {spine_info['overlap'].get('sp500_median_abs_pct')} % / CAPE median "
                 f"{spine_info['overlap'].get('cape_median_abs_pct')} % -> {'OK' if spine_info['overlap'].get('bestaaet') else 'FEJL'}"
                 if "overlap" in spine_info else "; (overlap ikke tjekket: kilde manglede)"))
    rev = spine_info.get("multpl", {}).get("revideret")
    if rev:
        print(f"rygrad: multpl REVIDEREDE {len(rev)} maaned(er) mod {spine_info['multpl']['diff_mod']}: "
              + ", ".join(f"{k} {a}->{b}" for k, (a, b) in list(rev.items())[:6]) + (" ..." if len(rev) > 6 else ""))
    for k in spine_krit:
        print(f"rygrad: {k}")

    kritiske = [s for s in failed if s not in RESERVE] + manglende_manual + spine_krit + stale_krit
    reserve_fejl = [s for s in failed if s in RESERVE]
    meta["complete"] = not kritiske
    klar, grunde = refit_klar(spine_info, reserve_fejl, stale)
    meta["spine"]["refit_klar"] = klar
    if grunde:
        meta["spine"]["refit_blokeret"] = grunde
        print("rygrad: ikke komplet til rekalibrering — " + "; ".join(grunde)
              + ". Curve-only paavirkes ikke (finalize6 advarer); fuldmodellens gate kan blive 'comparison unavailable'.")
    meta["lokale_filer"] = dict(serier=[s for s in SP.LOKALE if s in meta["series"]],
                                filer=[f for f in SP.LOKALE_FILER if (outdir / f).exists()],
                                note="licensbegraensede kilder: hashet her, committes aldrig (.gitignore; README 'Datakilder og vilkaar')")
    if reserve_fejl:
        meta["reserve_fejlede"] = reserve_fejl
    rygrad_hashes = [f"spine:{meta['spine'].get('sha256', '')}",
                     f"yale:{meta['spine'].get('yale', {}).get('sha256', '')}",
                     f"multpl:{meta['spine'].get('multpl', {}).get('sha256', '')}"]
    combined = "".join(sorted(f"{k}:{v['sha256']}" for k, v in meta["series"].items())
                       + [f"{k}:{v['sha256']}" for k, v in sorted(meta["manual"].items())]
                       + rygrad_hashes)                       # v5.0.1: rygraden indgaar i snapshot-hashen
    meta["snapshot_sha256"] = sha256(combined.encode())
    (outdir / "meta.json").write_bytes(json.dumps(meta, indent=1).encode("utf-8"))
    if reserve_fejl:
        print(f"ADVARSEL: ikke-veto-serier fejlede ({', '.join(reserve_fejl)}) — motor viser dem som utilgaengelige; "
              "snapshottet er stadig komplet til den maanedlige laesning.")
    kv = RAW / f"{today}.ukomplet"
    if kritiske:
        if kv.exists():
            shutil.rmtree(kv)
        outdir.rename(kv)
        print(f"\nFEJLEDE: {', '.join(kritiske)} — forsoeget er gemt UKOMPLET som {kv.name} "
              f"(ignoreres af calibrate/motor); et evt. eksisterende {today}-snapshot er uroert. Koer fetch.py igen.")
        sys.exit(1)
    skift_paa_plads(outdir, final_dir)       # dagens tidligere snapshot erstattes foerst NU — af et komplet
    if acc_ny is not None:                    # F31: kun et KOMPLET snapshot kan acceptere en outlier
        (MANUAL / OUTLIERS_ACC).write_text(json.dumps(acc_ny, indent=1, ensure_ascii=False, sort_keys=True) + chr(10),
                                           encoding="utf-8")
    if kv.exists():
        shutil.rmtree(kv)                     # F24: det afloeste forsoeg ville ellers blokere motor --log
        print(f"(afloest forsoeg {kv.name} slettet)")
    print(f"\nSnapshot-hash: {meta['snapshot_sha256'][:16]}...  ({final_dir})")

if __name__ == "__main__":
    main()
