#!/usr/bin/env python3
"""
fetch.py — v5 datalag (trin 1 i raadets byggeorden).

Henter alle FRED-serier noeglefrit via fredgraph.csv (parallelt), skriver et
dateret, byte-eksakt hashet snapshot i data/raw/<YYYY-MM-DD>/ og printer diff
mod forrige snapshot til menneskeligt eftersyn (raadets T6): ny observation,
aendret sidste vaerdi eller stille revision af historikken.

Snapshottet bygges i data/raw/<dato>.ny og flyttes foerst paa plads naar alt er
hentet: fejler en kraevet serie (reserveserierne GDPC1/CPIAUCSL/THREEFYTP10
undtaget) eller mangler shiller.csv/manual.json, gemmes forsoeget som
data/raw/<dato>.ukomplet ("complete": false; ignoreres af calibrate/motor), og et
eksisterende komplet dagssnapshot roeres ikke (koer fetch.py igen).

Rygraden (v5.0.1, RAADETS_V501 §1): Yales ie_data.xls er frosset ved 2023-09, saa
snapshottets spine.csv bygges som komposit — manual/shiller_yale_2023-09.csv (uforanderlig
kopi) byte-identisk t.o.m. 2023-07, derefter FRED SP500 (dagligt -> maanedsmiddel), CPIAUCNS,
GS10 som LTR og multpl's maanedlige CAPE, med proveniens-kolonne. Overlap-tolerancer (§1.2),
multpl-assertions (§1.3), outlier-guard (§1.6, `--accept-outlier "<hvad blev tjekket; hvorfor>"`)
og den udgivelses-bevidste friskheds-guard (§1.7) haandhaeves her; resultatet staar i meta.json.

Manuelle inputs (dokumenteret protokol, raadets Section 9):
  manual/manual.json  — {"spx_vs_hi": .., "cape": .., "margin_yoy": ..,
                         "as_of": "YYYY-MM-DD"}  (S&P vs 12m-hoejde som decimal,
                        live Shiller-CAPE fra multpl.com, FINRA marginlaan y/y %).

Kun stdlib. Koer:  python fetch.py
"""
import csv, hashlib, io, json, shutil, sys, time, urllib.error, urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone
from pathlib import Path

import spine as SP

HERE = Path(__file__).parent
RAW = HERE / "data" / "raw"
MANUAL = HERE / "manual"
WORKERS = 8          # parallelle FRED-kald: 20 serier tog ~12 s serielt, ~1 s parallelt

# Serier og hvorfor de hentes (raadets blueprint, Section 8-9 + kandidatliste)
SERIES = {
    "GS10":            "10-aarig statsrente, maanedlig (feature: curve/realrate)",
    "TB3MS":           "3-mdr T-bill, maanedlig (feature: curve)",
    "CPIAUCNS":        "CPI NSA (inflations-features; Shiller-konsistent)",
    "CPIAUCSL":        "CPI SA (reserve/diagnostik)",
    "UNRATE":          "ledighed (Sahm-transform-kandidat, trin 4)",
    "SAHMREALTIME":    "Sahm-reglen realtid (monitor + benchmark)",
    "ICSA":            "initial claims, ugentlig (kandidat, trin 4)",
    "PERMIT":          "byggetilladelser (kandidat, trin 4)",
    "BAMLH0A0HYM2":    "HY OAS, daglig (monitor — ineligible som feature)",
    "USREC":           "NBER-recessionsmaaneder (label fra trin 2)",
    "A191RL1Q225SBEA": "real BNP %-aendring ann. (teknisk label + advance-diagnostik)",
    "GDPC1":           "real BNP niveau (reserve)",
    "FEDFUNDS":        "effektiv fed funds (market conditions: realt kontantafkast)",
    "PCEPI":           "PCE-prisindeks (market conditions: realt kontantafkast)",
    "THREEFYTP10":     "ACM 10-aars term-praemie, FRED-spejl 1990+ (trin 4: substitutionstest)",
    "RECPROUSM156N":   "Chauvet-Piger glattet recessionssandsynlighed (benchmark, coincident nowcast)",
    "AWHMAN":          "ugentlige arbejdstimer, industri, 1939+ (trin: sidste praeregistrerede feature-skud)",
    "RIFSPPFAAD90NB":  "90-dages AA finansiel commercial paper-rente (svaerm-tripwire: funding-spaend)",
    "DTB3":            "3-mdr T-bill sekundaermarked, daglig (til CP-spaendet)",
    "MORTGAGE30US":    "30-aars realkreditrente, ugentlig (svaerm-tripwire: fiskal/term-praemie-kanalen)",
    "SP500":           "S&P 500 dagligt luk, ~10 aar (rygradens SP500-kolonne efter 2023-07 som maanedsmiddel)",
}
MULTPL_URL = "https://www.multpl.com/shiller-pe/table/by-month"
YALE = "shiller_yale_2023-09.csv"          # uforanderlig kopi af Yales ie_data.xls (sidste raekke 2023.09)

def parse_rows(raw):
    """FRED-csv-bytes -> [(dato, vaerdi)] uden manglende ('.'/tomme) observationer."""
    rows = list(csv.reader(io.StringIO(raw.decode("utf-8-sig"))))
    if len(rows) < 2 or len(rows[0]) != 2:
        raise RuntimeError(f"uventet format ({rows[:1]})")
    return [(d, v) for d, v in rows[1:] if v not in (".", "")]

def fetch_series(sid, attempts=3):
    """Raa bytes + parsede raekker. Netvaerksfejl, 5xx, 429 (ratelimit) og misdannede
    svar proeves igen; oevrige 4xx (ukendt serie) ikke."""
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}"
    last_err = None
    for k in range(attempts):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                raw = r.read()
            data = parse_rows(raw)             # inde i forsoeget: et flygtigt ikke-CSV-svar retries
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

def sha256(b):
    return hashlib.sha256(b).hexdigest()

def snapshot_complete(d):
    """Komplethedsflaget som calibrate laeser det (dubleret her: fetch er stdlib-only, calibrate traekker numpy)."""
    m = d / "meta.json"
    if not m.exists():
        return False
    try:
        return bool(json.loads(m.read_text(encoding="utf-8")).get("complete", True))
    except ValueError:
        return False

def last_snapshot_before(today_dir):
    """Diff-baseline = nyeste KOMPLETTE snapshot (samme valg som calibrate/motor), ikke blot nyeste mappe."""
    if not RAW.exists():
        return None
    dirs = sorted(d for d in RAW.iterdir() if d.is_dir() and d != today_dir and snapshot_complete(d))
    return dirs[-1] if dirs else None

def diff_mark(prev_s, prev_dir, sid, data, cur):
    """Diff mod forrige snapshot: hash, sidste observation, og (for at fange stille revisioner)
    om det gamle snapshots observationer stadig er et praefiks af de nye. Mangler seriens
    meta-post, men filen findes, koeres praefikstjekket alligevel."""
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
            old = parse_rows(pf.read_bytes())
            if data[:len(old)] != old:
                marks.append("REVIDERET historik")
        except Exception:
            marks.append("forrige fil ulaeselig")
    return "  <-- " + (", ".join(marks) if marks else "andet indhold")

RESERVE = {"GDPC1", "CPIAUCSL", "THREEFYTP10", "SP500"}   # fejl her nedlaegger ikke veto (SP500: rygraden stopper blot)
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

def monthly_last(data):
    """FRED-maanedsserie [(YYYY-MM-DD, v)] -> {YYYY-MM: float} (stemplet den 1.)."""
    return {d[:7]: float(v) for d, v in data}

def byg_rygrad(outdir, series_data, argv, today):
    """Bygger spine.csv (§1) + koerer overlap/outlier/friskheds-guards. Returnerer (meta-blok, kritiske_fejl)."""
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
                              foerste=min(cape_m), sidste=max(cape_m))
        (outdir / "cape_multpl.csv").write_text(
            "Date,CAPE\n" + "".join(f"{k},{cape_m[k]}\n" for k in sorted(cape_m)), encoding="utf-8")
    except Exception as e:
        info["multpl"] = dict(fejl=str(e)[:300])
        cape_m = {}
    sp_d = series_data.get("SP500"); cpi_d = series_data.get("CPIAUCNS"); gs_d = series_data.get("GS10")
    sp500_m = SP.monthly_mean(sp_d) if sp_d else {}
    # daglig SP500: en maaned taeller kun som lukket hvis den er FOER hentemaaneden
    sp500_m = {k: v for k, v in sp500_m.items() if k < today.isoformat()[:7]}
    cpi_m = monthly_last(cpi_d) if cpi_d else {}
    gs10_m = monthly_last(gs_d) if gs_d else {}

    # §1.2 overlap (kun hvis begge kilder kom hjem)
    if sp500_m and cape_m:
        ov = SP.overlap_check(yale, sp500_m, cape_m)
        info["overlap"] = ov
        if not ov["bestaaet"]:
            kritiske.append("rygrad: overlap-tolerancer (§1.2) ikke overholdt")
    # §1.6 outlier-guard paa komposit-delen
    probs = SP.outlier_check(cape_m, fra=SP.SEAM) if cape_m else []
    if probs:
        if "--accept-outlier" in argv:
            begr = argv[argv.index("--accept-outlier") + 1] if len(argv) > argv.index("--accept-outlier") + 1 else ""
            info["outlier_override"] = dict(observationer=[f"{k}: {p}" for k, p in probs],
                                            tjekket="multpl CAPE mod FRED SP500-maanedsmiddel og CPIAUCNS (ingen uafhaengig CAPE-kilde findes)",
                                            begrundelse=begr)
        else:
            info["outliers"] = [f"{k}: {p}" for k, p in probs]
            kritiske.append("rygrad: CAPE-outlier (§1.6) — gentag med --accept-outlier \"<hvad blev tjekket; hvorfor>\"")
    rows = SP.build_spine(yale, sp500_m, cpi_m, gs10_m, cape_m)
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
    info.update(seam=SP.SEAM, raekker=len(rows), sidste=rows[-1][0] if rows else None,
                komposit_maaneder=len(komposit), cpi_huller=SP.cpi_huller(rows),
                sha256=sha256((outdir / "spine.csv").read_bytes()))
    seam_f = MANUAL / "seam_check_2023.json"          # §1.4: engangs-krydstjek af de to erstattede maaneder
    if seam_f.exists():
        try:
            info["seam_check"] = json.loads(seam_f.read_text(encoding="utf-8"))
        except ValueError:
            info["seam_check"] = {"fejl": "ulaeselig seam_check_2023.json"}
    return info, kritiske

def main():
    today = date.today().isoformat()
    final_dir = RAW / today
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
            cur = dict(rows=len(data), first=data[0][0], last=last_d, last_value=last_v,
                       sha256=sha256(raw), purpose=why)
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
    spine_info, spine_krit = byg_rygrad(outdir, series_data, sys.argv, idag)
    meta["spine"] = spine_info
    if spine_info.get("sidste"):
        sidste_dato["spine"] = spine_info["sidste"] + "-01"
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
    for k in spine_krit:
        print(f"rygrad: {k}")

    kritiske = [s for s in failed if s not in RESERVE] + manglende_manual + spine_krit + stale_krit
    reserve_fejl = [s for s in failed if s in RESERVE]
    meta["complete"] = not kritiske
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
        print(f"ADVARSEL: reserveserier fejlede ({', '.join(reserve_fejl)}) — bruges af ingen forbruger; "
              "snapshottet er stadig komplet.")
    if kritiske:
        kv = RAW / f"{today}.ukomplet"
        if kv.exists():
            shutil.rmtree(kv)
        outdir.rename(kv)
        print(f"\nFEJLEDE: {', '.join(kritiske)} — forsoeget er gemt UKOMPLET som {kv.name} "
              f"(ignoreres af calibrate/motor); et evt. eksisterende {today}-snapshot er uroert. Koer fetch.py igen.")
        sys.exit(1)
    if final_dir.exists():
        shutil.rmtree(final_dir)              # dagens tidligere snapshot erstattes foerst NU — af et komplet
    outdir.rename(final_dir)
    print(f"\nSnapshot-hash: {meta['snapshot_sha256'][:16]}...  ({final_dir})")

if __name__ == "__main__":
    main()
