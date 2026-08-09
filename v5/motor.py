#!/usr/bin/env python3
"""
MOTOR v5.0-trin1 — aflaesning fra weights.json + seneste snapshot.
Ingen haandkopierede konstanter: vaegte kommer fra calibrate.py, live-inputs
fra fetch.py-snapshottet + manual.json, og CAPE-percentilen beregnes af
snapshottets egen expanding-historik (raadets R5-forbehold: ingen 2026-knuder).

Koer:  python motor.py [--allow-stale]
"""
import json, sys
from datetime import date, datetime
from pathlib import Path
import numpy as np

import calibrate as C   # genbruger indlaesning/feature-logik — een sandhed

HERE = Path(__file__).parent
STALE_DAYS = 40

def latest(series, n=1):
    items = sorted(series.items())
    return items[-n]

def main():
    wf = HERE / "weights.json"
    if not wf.exists():
        sys.exit("FEJL: weights.json mangler. Koer foerst: python calibrate.py")
    W = json.loads(wf.read_text(encoding="utf-8"))
    snap = C.find_snapshot(sys.argv)
    meta = json.loads((snap / "meta.json").read_text(encoding="utf-8"))

    age = (date.today() - date.fromisoformat(snap.name)).days
    if age > STALE_DAYS and "--allow-stale" not in sys.argv:
        sys.exit(f"FEJL: snapshottet er {age} dage gammelt (>{STALE_DAYS}). "
                 f"Koer fetch.py, eller brug --allow-stale.")
    if W["snapshot_sha256"] != meta["snapshot_sha256"]:
        print("ADVARSEL: weights.json er kalibreret paa et ANDET snapshot "
              f"({W['snapshot']}). Genkalibrer med: python calibrate.py")

    manual_f = snap / "manual.json"
    if not manual_f.exists():
        sys.exit("FEJL: manual.json mangler i snapshottet (spx_vs_hi, cape, margin_yoy). "
                 "Se fetch.py's docstring, laeg filen i manual/ og koer fetch.py.")
    man = json.loads(manual_f.read_text(encoding="utf-8"))

    # ---- live-inputs fra data, ikke fra taster ----
    gs10 = C.read_fred(snap, "GS10");   tb3 = C.read_fred(snap, "TB3MS")
    cpi  = C.read_fred(snap, "CPIAUCNS")
    (d_y10, y10) = latest(gs10); (d_tb, tb3m) = latest(tb3)
    ck = sorted(cpi); cpi_yoy   = (cpi[ck[-1]] / cpi[tuple(np.subtract(ck[-1], (1, 0)))] - 1) * 100 \
        if tuple(np.subtract(ck[-1], (1, 0))) in cpi else None
    if cpi_yoy is None:
        sys.exit("FEJL: kan ikke danne CPI y/y fra snapshottet")
    k1 = tuple(np.subtract(ck[-1], (1, 0)))
    cpi_yoy_1 = (cpi[k1] / cpi[tuple(np.subtract(k1, (1, 0)))] - 1) * 100

    shiller = C.read_shiller(snap)
    cape_hist = np.array([r[4] for r in shiller])
    cape_live = float(man["cape"])
    hist = np.append(cape_hist, cape_live)
    with np.errstate(invalid="ignore"):
        cape_pct = float(np.mean(cape_live > hist))   # expanding, ingen faste knuder

    x = dict(curve=y10 - tb3m, realrate=y10 - cpi_yoy, dd=float(man["spx_vs_hi"]),
             d_infl=cpi_yoy - cpi_yoy_1, cape_pct=cape_pct)
    F, MU, SD, Wv = W["features"], W["mu"], W["sd"], W["w"]
    z = {f: (x[f] - MU[f]) / SD[f] for f in F}
    logit = Wv[0] + sum(Wv[i + 1] * z[f] for i, f in enumerate(F))
    p12 = 1 / (1 + np.exp(-np.clip(logit, -30, 30)))
    base = W["base_rate"]

    print("=" * 74)
    print(f" MOTOR v5.0-trin1   snapshot {snap.name} (hash {meta['snapshot_sha256'][:10]}...)")
    print(f" vaegte: {W['protocol_version']} kalibreret {W['created_utc'][:10]} "
          f"paa {W['n_obs']} kvartaler / {W['n_episoder']} episoder")
    print("=" * 74)
    print(f"\nLAG 1 — P(teknisk recession inden 4 kvartaler)   [walk-forward "
          f"+{W['wf_table']['5: + CAPE']['improvement']:.1f}% log-loss]\n")
    NAVN = dict(curve="Rentekurve 10y-3m", realrate="Realrente 10y-CPI",
                dd="S&P vs 12-mdr hoejde", d_infl="Aendring i inflation",
                cape_pct="CAPE-percentil")
    print(f"  {'Input':<24}{'Vaerdi':>9}{'z-score':>10}   kilde")
    kilder = dict(curve=f"GS10 {d_y10[0]}-{d_y10[1]:02d} / TB3MS {d_tb[0]}-{d_tb[1]:02d}",
                  realrate="GS10 - CPIAUCNS y/y", dd=f"manual ({man.get('as_of','?')})",
                  d_infl="CPIAUCNS", cape_pct=f"manual CAPE {cape_live} + Shiller-historik")
    for f in F:
        print(f"  {NAVN[f]:<24}{x[f]:>9.2f}{z[f]:>10.2f}   {kilder[f]}")
    print(f"\n  {'P(recession, 4 kvt)':<24}{p12*100:>8.1f}%")
    print(f"  {'Basisrate':<24}{base*100:>8.1f}%")
    print("  (usikkerhedsbaand kommer i trin 4-6; indtil da: ingen 'lav/hoej'-sprog,")
    print("   jf. raadets sprogregel T10/Section 6)")

    # ---- monitors (individuelle linjer, ingen taellinger — Section 8) ----
    sahm = latest(C.read_fred(snap, "SAHMREALTIME"))
    oas_d, oas_pct = latest(C.read_fred(snap, "BAMLH0A0HYM2"))
    oas_bp = oas_pct * 100          # FRED-serien er i procent; taersklen er i bp
    gq   = sorted(C.read_fred(snap, "A191RL1Q225SBEA").items())
    adv2 = [v for _, v in gq[-2:]]
    ff   = latest(C.read_fred(snap, "FEDFUNDS"))
    pce  = C.read_fred(snap, "PCEPI"); pk = sorted(pce)
    pce_yoy = (pce[pk[-1]] / pce[tuple(np.subtract(pk[-1], (1, 0)))] - 1) * 100

    # inversionsnote beregnes af FULD GS10/TB3MS-historik (ikke Shiller-trunkeret)
    fkeys = sorted(set(gs10) & set(tb3))
    curve_m = np.array([gs10[k] - tb3[k] for k in fkeys])
    inv_set = {i for i, v in enumerate(curve_m) if v < 0}
    if inv_set:
        last_inv = max(inv_set)
        mdr_siden = (len(curve_m) - 1) - last_inv
        run_start = last_inv
        while run_start - 1 in inv_set:
            run_start -= 1
        dybde = float(np.min(curve_m[run_start:last_inv + 1]))
        slut = fkeys[last_inv]
        inv_note = (f"sluttede {slut[0]}-{slut[1]:02d} ({mdr_siden} mdr siden), "
                    f"dybde {dybde:+.2f}pp")
    else:
        inv_note = "ingen inversion i historikken"

    print("\nMONITORS   [status pr. raadets protokol — ingen indflydelse paa P]")
    mon = [
        ("Kurven inverteret",  x["curve"] < 0, f"{x['curve']:+.2f}pp", "kandidat (genforsvar, trin 4)"),
        ("Sahm > 0,50",        sahm[1] > 0.50, f"{sahm[1]:.2f} ({sahm[0][0]}-{sahm[0][1]:02d})", "kandidat (trin 4)"),
        ("HY OAS > 600bp",     oas_bp > 600, f"{oas_bp:.0f}bp ({oas_d[0]}-{oas_d[1]:02d})", "ineligible som feature (historik 1997-)"),
        ("S&P drawdown > 20%", x["dd"] < -0.20, f"{x['dd']*100:+.0f}%", "kandidat (trin 4)"),
        ("Advance-estimat: 2 neg. BNP-print", len(adv2) == 2 and all(v < 0 for v in adv2),
         f"{adv2[0]:+.1f}%, {adv2[1]:+.1f}%", "uvalideret realtids-diagnostik (Nemotrons linje)"),
        ("Inversionsnote",     None, inv_note, "uvalideret kontekst (LAG2-rest, T4)"),
    ]
    for navn, aktiv, vaerdi, status in mon:
        boks = "[X]" if aktiv else ("[ ]" if aktiv is not None else "[-]")
        print(f"  {boks} {navn:<36}{vaerdi:<48}{status}")

    print("\nMARKET CONDITIONS — not recession evidence   [kvalitativ, T5]")
    erp = 100 / cape_live - y10
    mc = [
        ("CAPE-percentil (expanding)", f"{cape_pct*100:.1f}. pct"),
        ("Aktierisikopraemie 1/CAPE - y10", f"{erp:+.2f}pp"),
        ("Marginlaan y/y", f"{float(man['margin_yoy']):+.1f}% (manual, {man.get('as_of','?')})"),
        ("Realt kontantafkast FF - PCE", f"{ff[1] - pce_yoy:+.2f}pp"),
    ]
    for navn, vaerdi in mc:
        print(f"      {navn:<34}{vaerdi}")

    print(f"""
ADVARSEL (staar permanent, T8)
  2023: modellens vaerste fejl, 76,9% uden recession — kurveregime-risiko
  gaelder begge veje. {W['n_episoder']} episoder er faa; forskellen fra
  basisraten er endnu ikke forsynet med baand (trin 4-6). Teknisk label
  (2 neg. kvartaler) skiftes til NBER-onset i trin 2 — 2001 mangler i
  denne kalibrering. Eksogene chok kan ikke forudsiges.
  P er betinget af BNP-data som revideret pr. snapshot-datoen.""")

if __name__ == "__main__":
    main()
