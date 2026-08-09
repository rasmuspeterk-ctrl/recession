#!/usr/bin/env python3
"""
fetch.py — v5 datalag (trin 1 i raadets byggeorden).

Henter alle FRED-serier noeglefrit via fredgraph.csv, skriver et dateret,
hashet snapshot i data/raw/<YYYY-MM-DD>/ og printer diff mod forrige
snapshot til menneskeligt eftersyn (raadets T6).

Manuelle inputs (dokumenteret protokol, raadets Section 9):
  manual/shiller.csv  — Shiller-historikken 1871+. Format (header paakraevet):
                        Date,SP500,CPI,LTR,CAPE
                        Date = YYYY-MM (maanedlig). Kilde: Shillers ie_data.xls
                        (www.econ.yale.edu/~shiller/data.htm), eksporteret som CSV.
                        Kolonnerne svarer til v4's data/spx.csv.
  manual/manual.json  — {"spx_vs_hi": .., "cape": .., "margin_yoy": ..,
                         "as_of": "YYYY-MM-DD"}  (S&P vs 12m-hoejde som decimal,
                        live Shiller-CAPE fra multpl.com, FINRA marginlaan y/y %).

Kun stdlib. Koer:  python fetch.py
"""
import csv, hashlib, io, json, shutil, sys, urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

HERE = Path(__file__).parent
RAW = HERE / "data" / "raw"
MANUAL = HERE / "manual"

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
}

def fetch_series(sid):
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}"
    with urllib.request.urlopen(url, timeout=60) as r:
        raw = r.read()
    text = raw.decode("utf-8-sig")
    rows = list(csv.reader(io.StringIO(text)))
    if len(rows) < 2 or len(rows[0]) != 2:
        raise RuntimeError(f"{sid}: uventet format ({rows[:1]})")
    data = [(d, v) for d, v in rows[1:] if v not in (".", "")]
    if not data:
        raise RuntimeError(f"{sid}: tom serie")
    return text, data

def sha256(b):
    return hashlib.sha256(b).hexdigest()

def last_snapshot_before(today_dir):
    if not RAW.exists():
        return None
    dirs = sorted(d for d in RAW.iterdir() if d.is_dir() and d != today_dir)
    return dirs[-1] if dirs else None

def main():
    today = date.today().isoformat()
    outdir = RAW / today
    outdir.mkdir(parents=True, exist_ok=True)
    prev = last_snapshot_before(outdir)
    prev_meta = None
    if prev and (prev / "meta.json").exists():
        prev_meta = json.loads((prev / "meta.json").read_text(encoding="utf-8"))

    meta = {"retrieved_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "series": {}, "manual": {}}
    print(f"=== fetch.py — snapshot {today} ===")
    print(f"{'serie':<18}{'raekker':>8}{'sidste dato':>13}{'vaerdi':>10}{'forrige':>10}")
    failed = []
    for sid, why in SERIES.items():
        try:
            text, data = fetch_series(sid)
            (outdir / f"{sid}.csv").write_text(text, encoding="utf-8")
            last_d, last_v = data[-1]
            meta["series"][sid] = dict(rows=len(data), first=data[0][0], last=last_d,
                                       last_value=last_v, sha256=sha256(text.encode()),
                                       purpose=why)
            prev_v = ""
            if prev_meta and sid in prev_meta.get("series", {}):
                prev_v = prev_meta["series"][sid].get("last_value", "")
            mark = "" if prev_v in ("", last_v) else "  <-- AENDRET"
            print(f"{sid:<18}{len(data):>8}{last_d:>13}{last_v:>10}{prev_v:>10}{mark}")
        except Exception as e:
            failed.append(sid)
            print(f"{sid:<18}  FEJL: {e}")

    # manuelle filer kopieres ind i snapshottet og hashes med
    for name in ("shiller.csv", "manual.json", "acm.csv"):
        src = MANUAL / name
        if src.exists():
            shutil.copy(src, outdir / name)
            b = src.read_bytes()
            meta["manual"][name] = dict(sha256=sha256(b), bytes=len(b))
            print(f"manual/{name:<12} kopieret ind i snapshot (sha256 {sha256(b)[:12]}...)")
        else:
            print(f"manual/{name:<12} MANGLER — se docstring for format")

    combined = "".join(sorted(f"{k}:{v['sha256']}" for k, v in meta["series"].items())
                       + [f"{k}:{v['sha256']}" for k, v in sorted(meta["manual"].items())])
    meta["snapshot_sha256"] = sha256(combined.encode())
    (outdir / "meta.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    print(f"\nSnapshot-hash: {meta['snapshot_sha256'][:16]}...  ({outdir})")
    if failed:
        print(f"FEJLEDE serier: {', '.join(failed)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
