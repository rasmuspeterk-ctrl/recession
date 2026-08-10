#!/usr/bin/env python3
"""
MOTOR v5.0 — maanedlig aflaesning efter raadets Section 8-spec (trin 6).

Output: operationel P + estimation-sensitivity-baand + basisrate (ratio kun
naar baandet udelukker basisraten), z-inputs, benchmark-tabel (intercept,
curve-only, realtids-Sahm, Chauvet-Piger separat, v4-arv), monitors uden
taellinger, market conditions-sektion, skabelon-genereret dom der aldrig
overstiger tallene. Sprogregler (Section 6) haandhaeves mekanisk.

Koer:  python motor.py [--allow-stale]
"""
import json, sys
from datetime import date
from pathlib import Path
import numpy as np

import calibrate as C

HERE = Path(__file__).parent
STALE_DAYS = 40

def latest(series, n=1):
    return sorted(series.items())[-n]

def p_of(x, feats, mu, sd, w):
    z = [(x[f] - mu[f]) / sd[f] for f in feats]
    return 1 / (1 + np.exp(-np.clip(w[0] + sum(w[i + 1] * z[i] for i in range(len(feats))), -30, 30)))

def main():
    wf = HERE / "weights.json"
    if not wf.exists():
        sys.exit("FEJL: weights.json mangler. Koer calibrate/ablation/finalize-kaeden.")
    W = json.loads(wf.read_text(encoding="utf-8"))
    if W.get("protocol_version") != "5.0-final":
        sys.exit(f"FEJL: weights.json er {W.get('protocol_version')} — koer finalize6.py")
    snap = C.find_snapshot(sys.argv)
    meta = json.loads((snap / "meta.json").read_text(encoding="utf-8"))
    age = (date.today() - date.fromisoformat(snap.name)).days
    if age > STALE_DAYS and "--allow-stale" not in sys.argv:
        sys.exit(f"FEJL: snapshottet er {age} dage gammelt (>{STALE_DAYS}). fetch.py eller --allow-stale.")
    if W["snapshot_sha256"] != meta["snapshot_sha256"]:
        print("ADVARSEL: weights kalibreret paa andet snapshot — koer finalize6.py igen.")

    man = json.loads((snap / "manual.json").read_text(encoding="utf-8"))
    gs10 = C.read_fred(snap, "GS10"); tb3 = C.read_fred(snap, "TB3MS")
    cpi = C.read_fred(snap, "CPIAUCNS")
    (d_y10, y10) = latest(gs10); (d_tb, tb3m) = latest(tb3)
    ck = sorted(cpi)
    k0, k1 = ck[-1], (ck[-1][0] - 1, ck[-1][1])
    k2 = (k1[0] - 1, k1[1])
    cpi_yoy = (cpi[k0] / cpi[k1] - 1) * 100
    cpi_yoy_1 = (cpi[k1] / cpi[k2] - 1) * 100

    shiller = C.read_shiller(snap)
    cape_hist = np.array([r[4] for r in shiller])
    cape_live = float(man["cape"])
    with np.errstate(invalid="ignore"):
        cape_pct = float(np.mean(cape_live > np.append(cape_hist, cape_live)))

    x = dict(curve=y10 - tb3m, realrate=y10 - cpi_yoy, dd=float(man["spx_vs_hi"]),
             d_infl=cpi_yoy - cpi_yoy_1, cape_pct=cape_pct)

    op = W["op"]
    p_op = float(p_of(x, op["features"], op["mu"], op["sd"], op["w"]))
    zc = (x["curve"] - op["mu"].get("curve", W["fuldmodel"]["mu"]["curve"])) / \
         op["sd"].get("curve", W["fuldmodel"]["sd"]["curve"])
    band_ps = []
    for wb in W["band"]["W"]:
        band_ps.append(float(p_of(x, op["features"], op["mu"], op["sd"], wb)))
    lo, hi = np.percentile(band_ps, 10), np.percentile(band_ps, 90)
    base = W["base_rate"]
    band_excludes_base = (base < lo) or (base > hi)

    fm = W["fuldmodel"]
    p_full = float(p_of(x, fm["features"], fm["mu"], fm["sd"], fm["w"]))
    bm = W["benchmarks"]["curve_only"]
    p_curve = float(p_of(x, ["curve"], {"curve": bm["mu"]}, {"curve": bm["sd"]}, bm["w"]))

    # v4-arv (teknisk label), hvis filen findes
    p_arv = None
    arvf = HERE / "weights_trin1_teknisk.json"
    if arvf.exists():
        A = json.loads(arvf.read_text(encoding="utf-8"))
        p_arv = float(p_of(x, A["features"], A["mu"], A["sd"], A["w"]))

    sahm = latest(C.read_fred(snap, "SAHMREALTIME"))
    cp = latest(C.read_fred(snap, "RECPROUSM156N"))
    oas_d, oas_pct = latest(C.read_fred(snap, "BAMLH0A0HYM2")); oas_bp = oas_pct * 100
    gq = sorted(C.read_fred(snap, "A191RL1Q225SBEA").items()); adv2 = [v for _, v in gq[-2:]]
    ff = latest(C.read_fred(snap, "FEDFUNDS"))
    pce = C.read_fred(snap, "PCEPI"); pk = sorted(pce)
    pce_yoy = (pce[pk[-1]] / pce[(pk[-1][0] - 1, pk[-1][1])] - 1) * 100

    fkeys = sorted(set(gs10) & set(tb3))
    curve_m = np.array([gs10[k] - tb3[k] for k in fkeys])
    inv = {i for i, v in enumerate(curve_m) if v < 0}
    if inv:
        li = max(inv); run0 = li
        while run0 - 1 in inv:
            run0 -= 1
        slut = fkeys[li]
        inv_note = (f"sluttede {slut[0]}-{slut[1]:02d} ({len(curve_m)-1-li} mdr siden), "
                    f"dybde {float(np.min(curve_m[run0:li+1])):+.2f}pp")
    else:
        inv_note = "ingen inversion i historikken"

    # ---------------------------------------------------------------- output
    print("=" * 74)
    print(f" MOTOR v5.0   snapshot {snap.name} (hash {meta['snapshot_sha256'][:10]}...)")
    print(f" operationel model: {'CURVE-ONLY-LOGIT' if W['operationel']=='curve_only' else 'FULDMODEL'} "
          f"paa {W['label_tekst']}")
    print(f" kalibreret {W['created_utc'][:10]} paa {W['n_obs']} kvartaler / {W['n_episoder']} onsets")
    print("=" * 74)

    print(f"\n1) SANDSYNLIGHED   [operationel wf: +{op['wf_improvement']:.1f}% log-loss / "
          f"+{op['wf_brier']:.1f}% Brier]")
    print(f"   P({W['label_tekst']})     {p_op*100:>6.1f}%")
    print(f"   Estimation-sensitivity-baand (10-90%)   {lo*100:.1f}% - {hi*100:.1f}%")
    print(f"   Basisrate                               {base*100:.1f}%")
    if band_excludes_base:
        print(f"   Forhold til basisrate                   {p_op/base:.2f}x")
    else:
        print("   (ratio undertrykt: baandet indeholder basisraten — Section 6)")
    print(f'   Fodnote: "{W["band"]["fodnote"]}"')

    print("\n2) MODEL-INPUTS (fuldmodellens fem, z mod kalibrering):")
    NAVN = dict(curve="Rentekurve 10y-3m", realrate="Realrente 10y-CPI",
                dd="S&P vs 12-mdr hoejde", d_infl="Aendring i inflation",
                cape_pct="CAPE-percentil (expanding)")
    for f in fm["features"]:
        z = (x[f] - fm["mu"][f]) / fm["sd"][f]
        star = "  <- operationel" if f in op["features"] else ""
        print(f"   {NAVN[f]:<26}{x[f]:>8.2f}{z:>9.2f}{star}")

    print("\n3) BENCHMARK-TABEL (printes ogsaa naar den er usmigrende):")
    print(f"   {'model':<34}{'wf-skill':>10}{'live-P':>9}")
    print(f"   {'intercept (basisrate)':<34}{'+0.0%':>10}{base*100:>8.1f}%")
    print(f"   {'curve-only-logit (NY Fed-stil-bm.)':<34}{'+'+format(W['benchmarks']['curve_only']['wf_improvement'],'.1f')+'%':>10}{p_curve*100:>8.1f}%"
          + ("   <- OPERATIONEL" if W["operationel"] == "curve_only" else ""))
    print(f"   {'fuldmodel (5 features)':<34}{'+'+format(fm['wf_improvement'],'.1f')+'%':>10}{p_full*100:>8.1f}%"
          f"   [{fm['status']}]")
    cc = W["benchmarks"].get("curve_cape")
    if cc:
        print(f"   {'curve+cape (praereg. v5.1-test)':<34}{'+'+format(cc['wf_improvement'],'.1f')+'%':>10}{'':>9}   [{cc['status']}]")
    ca = W["benchmarks"].get("curve_awh")
    if ca:
        print(f"   {'curve+awh (praereg. v5.2-test)':<34}{'+'+format(ca['wf_improvement'],'.1f')+'%':>10}{'':>9}   [{ca['status']}]")
    if p_arv is not None:
        print(f"   {'v4-arv (teknisk label)':<34}{'':>10}{p_arv*100:>8.1f}%   [andet maal — arv]")
    print(f"   {'realtids-Sahm (trigger 0,50)':<34}{'':>10}{sahm[1]:>8.2f}    [naerhorisont-signal]")
    print(f"   {'Chauvet-Piger nowcast':<34}{'':>10}{cp[1]:>8.1f}%   [coincident, "
          f"{cp[0][0]}-{cp[0][1]:02d}, publiceringslag — anden disciplin]")
    print(f"   Note: {fm['note']}")
    print(f"   MODEL-DIVERGENS: operationel {p_op*100:.1f}% vs fuldmodel {p_full*100:.1f}% "
          f"(delta {abs(p_op-p_full)*100:.1f}pp).")
    zc_cape = (x['cape_pct'] - fm['mu']['cape_pct']) / fm['sd']['cape_pct']
    zc_dd = (x['dd'] - fm['mu']['dd']) / fm['sd']['dd']
    print(f"   Divergensen drives af fuldmodellens ekstra led (CAPE z={zc_cape:+.2f}, dd z={zc_dd:+.2f});"
          f"\n   modellerne er statistisk uadskillelige paa skill — den simple vandt paa regel (raadsreview 2026-08).")

    print("\n4) MONITORS   [individuelle linjer, ingen taellinger, ingen indflydelse paa P]")
    mon = [
        ("Kurven inverteret", x["curve"] < 0, f"{x['curve']:+.2f}pp", "operationel feature"),
        ("Sahm > 0,50", sahm[1] > 0.50, f"{sahm[1]:.2f} ({sahm[0][0]}-{sahm[0][1]:02d})", "testet, ikke bestaaet (trin 4)"),
        ("Claims-momentum", None, "se ICSA i snapshot", "testet, ikke bestaaet (trin 4)"),
        ("Permits y/y", None, "se PERMIT i snapshot", "testet, ikke bestaaet (trin 4)"),
        ("HY OAS > 600bp", oas_bp > 600, f"{oas_bp:.0f}bp ({oas_d[0]}-{oas_d[1]:02d})", "ineligible (historik 1997-)"),
        ("S&P drawdown > 20%", x["dd"] < -0.20, f"{x['dd']*100:+.0f}%", "fuldmodel-feature"),
        ("Advance-estimat: 2 neg. BNP-print", len(adv2) == 2 and all(v < 0 for v in adv2),
         f"{adv2[0]:+.1f}%, {adv2[1]:+.1f}%", "uvalideret realtidsdiagnostik (vintage-flip dokumenteret, trin 5)"),
        ("Inversionsnote", None, inv_note, "uvalideret kontekst"),
    ]
    for navn, aktiv, vaerdi, status in mon:
        boks = "[X]" if aktiv else ("[ ]" if aktiv is not None else "[-]")
        print(f"   {boks} {navn:<36}{vaerdi:<48}{status}")

    print("\n5) MARKET CONDITIONS — not recession evidence   [kvalitativ]")
    erp = 100 / cape_live - y10
    for navn, vaerdi in [("CAPE-percentil (expanding)", f"{cape_pct*100:.1f}. pct"),
                         ("Aktierisikopraemie 1/CAPE - y10", f"{erp:+.2f}pp"),
                         ("Marginlaan y/y", f"{float(man['margin_yoy']):+.1f}% (manual, {man.get('as_of','?')})"),
                         ("Realt kontantafkast FF - PCE", f"{ff[1]-pce_yoy:+.2f}pp")]:
        print(f"       {navn:<34}{vaerdi}")

    print("\n6) DOM (skabelon-genereret — overstiger aldrig tallene)")
    if band_excludes_base:
        retning = "under" if p_op < base else "over"
        dom = (f"P er {p_op*100:.1f}% mod basisraten {base*100:.1f}%; baandet "
               f"[{lo*100:.1f}-{hi*100:.1f}%] udelukker basisraten — laesningen er {retning} basisraten.")
    else:
        dom = (f"P er {p_op*100:.1f}% mod basisraten {base*100:.1f}%, men baandet "
               f"[{lo*100:.1f}-{hi*100:.1f}%] indeholder basisraten: "
               f"IKKE SKELNELIG FRA BASISRATEN.")
    print(f"   {dom}")
    print(f"   P er betinget af NBER-datering pr. {snap.name}. 2023-fejlalarmen "
          f"(76,9% uden recession)\n   staar permanent: kurveregime-risiko gaelder begge veje. "
          f"Eksogene chok kan ikke forudsiges.")
    print("   STI-ADVARSEL (raadsreview 2026-08, enstemmig): modellen laeser kurvens NIVEAU;"
          "\n   +0,87pp efter en netop afsluttet dyb inversion behandles som +0,87pp uden"
          "\n   forhistorie. Historiske onsets er ofte sket i re-steepening-fasen; balance-"
          "\n   sheet-drevne recessioner uden frisk inversion er usynlige for modellen.")

if __name__ == "__main__":
    main()
