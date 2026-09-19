#!/usr/bin/env python3
"""
MOTOR v5.0 — maanedlig aflaesning efter raadets Section 8-spec (trin 6).

Output: operationel P + estimation-sensitivity-baand + basisrate (ratio kun
naar baandet udelukker basisraten), z-inputs, benchmark-tabel (intercept,
curve-only, realtids-Sahm, Chauvet-Piger separat, v4-arv), monitors uden
taellinger, market conditions-sektion, skabelon-genereret dom der aldrig
overstiger tallene. Sprogregler (Section 6) haandhaeves mekanisk.

Koer:  python motor.py [--allow-stale] [--log]
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

def read_fred_raw(snap, sid):
    """FRED-csv -> [(dato, vaerdi)] i filens raekkefoelge. Noedvendig for ugeserier:
    C.read_fred kollapser til (aar, maaned) og beholder kun maanedens sidste obs."""
    import csv as _csv
    out = []
    with (snap / f"{sid}.csv").open(encoding="utf-8-sig") as fh:
        for row in _csv.DictReader(fh):
            d, v = list(row.values())[:2]
            if v not in (".", ""):
                out.append((d, float(v)))
    return out

def laes_hovedbog(logf):
    """LOG.md-tabellen -> [dict] med alle kolonner. P/kurve beholder tekstformen;
    dashboardet faar tal via tal_af()."""
    kol = ("logget", "snapshot", "P", "baand", "basisrate", "dom", "kurve", "antaending", "note", "kalibrering")
    # v5.0.1 (§3.3): kolonnen 'kalibrering' findes kun i raekker skrevet fra og med v5.0.1 — aeldre raekker
    # har 9 celler og faar ingen vaerdi (historiske raekker roeres aldrig; se kalibreringer/legacy_mapping.json)
    ud = []
    if not logf.exists():
        return ud
    for ln in logf.read_text(encoding="utf-8").splitlines():
        if ln.startswith("| 2"):
            c = [f.strip() for f in ln.split("|")]
            ud.append(dict(zip(kol, c[1:1 + len(kol)])))
    return ud


def tal_af(txt, faktor=1.0):
    """"18.0%" -> 0.18 ved faktor 0.01. Uparsbart -> None."""
    try:
        return round(float(str(txt).rstrip("%").replace(",", ".")) * faktor, 6)
    except (TypeError, ValueError):
        return None



def ann_rate(series, n):
    """Annualiseret aendring over n maaneder. Kun paa SAESONKORRIGEREDE serier."""
    ks = sorted(series)
    if len(ks) < n + 1:
        return float("nan")
    return ((series[ks[-1]] / series[ks[-1 - n]]) ** (12 / n) - 1) * 100


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
    # v5.0.1 §3: vaegtene er FROSNE mellem rekalibreringer, saa snapshot-hashen afviger som regel.
    # Det der skal tjekkes er de to deterministiske triggere (§3.2): (b) annonceringstabellen
    # aendret siden manifestet, (a) september-koerslen forfalden. Begge blokerer --log.
    rekal_paakraevet = []
    ann_f = HERE / "nber_announcements.csv"
    if W.get("announcement_table_sha256") and ann_f.exists():
        import hashlib as _hl
        if _hl.sha256(ann_f.read_bytes()).hexdigest() != W["announcement_table_sha256"]:
            rekal_paakraevet.append("nber_announcements.csv er aendret siden manifest "
                                    f"{W.get('manifest_hash')} (§3.2b: ny top/bund -> refit ved denne koersel)")
    if W.get("refit_maaned"):
        ry, rm = int(W["refit_maaned"][:4]), int(W["refit_maaned"][5:7])
        naeste_sep = (ry + 1, 9) if (rm <= 9) else (ry + 2, 9)   # naeste september EFTER refit-maaneden
        if (date.today().year, date.today().month) >= naeste_sep:
            rekal_paakraevet.append(f"den aarlige september-rekalibrering er forfalden (sidste refit {W['refit_maaned']}, §3.2a)")
    for r in rekal_paakraevet:
        print(f"REKALIBRERING PAAKRAEVET: {r} — koer finalize6.py && diagnostik.py foer --log.")
    if W.get("manifest_hash"):
        print(f"vaegte frosne: manifest {W['manifest_hash']} (refit {W.get('refit_maaned', '?')}); "
              f"snapshot {snap.name} er nyere end kalibreringen — det er forventet (§3).")

    manual_f = snap / "manual.json"
    if not manual_f.exists():
        sys.exit("FEJL: manual.json mangler i snapshottet (spx_vs_hi, cape, margin_yoy). "
                 "Laeg den i manual/ og koer fetch.py igen.")
    man = json.loads(manual_f.read_text(encoding="utf-8"))
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
    band_ps = []
    for wb in W["band"]["W"]:
        band_ps.append(float(p_of(x, op["features"], op["mu"], op["sd"], wb)))
    lo, hi = np.percentile(band_ps, 10), np.percentile(band_ps, 90)
    base = W["base_rate"]
    band_excludes_base = (base < lo) or (base > hi)

    fm = W["fuldmodel"]
    fm_ok = "w" in fm                         # v5.0.1 §2: 'unavailable — CAPE stale' har ingen vaegte
    p_full = float(p_of(x, fm["features"], fm["mu"], fm["sd"], fm["w"])) if fm_ok else float("nan")
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
    ver = W.get("version", "5.0")
    print(f" MOTOR v{ver}   snapshot {snap.name} (hash {meta['snapshot_sha256'][:10]}...)"
          + (f"   kalibrering {W['manifest_hash']}" if W.get("manifest_hash") else ""))
    print(f" operationel model: {'CURVE-ONLY-LOGIT' if W['operationel']=='curve_only' else 'FULDMODEL'} "
          f"paa {W['label_tekst']}")
    print(f" kalibreret {W['created_utc'][:10]} paa {W['n_obs']} kvartaler / {W['n_episoder']} onsets"
          + (f"   (estimering t.o.m. {op['estimering_slut']}; vaegte frosne til naeste rekalibrering)" if op.get("estimering_slut") else ""))
    if op.get("raa"):
        r = op["raa"]
        print(f" raa: P = logit^-1({r['alpha']:+.4f} {r['beta_curve_pr_pp']:+.4f} * kurve_pp)   [beta = w1/s, alpha = w0 - w1*mu/s]")
    if meta.get("stale"):
        print(f" FRISKHED (§1.7): stale inputs {', '.join(meta['stale'])} — se meta.json")
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
    if W["band"].get("base"):                  # v5.0.1 §4.3: parret regel, supplement — Section 6 uaendret
        d = np.array(band_ps) - np.array(W["band"]["base"])
        dlo, dhi = np.percentile(d, 10), np.percentile(d, 90)
        parret_skelnelig = (dlo > 0) or (dhi < 0)
        print(f"   Supplement (parret, §4.3): Delta = P - basisrate pr. bootstrap-traek, central 80 %-baand "
              f"[{dlo*100:+.1f}, {dhi*100:+.1f}]pp -> {'skelnelig' if parret_skelnelig else 'ikke skelnelig'} fra 0 "
              f"({'enig' if parret_skelnelig == band_excludes_base else 'UENIG'} med baandreglen). "
              "Diagnostik: aendrer ikke dommen. Coverage not established.")

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
    if fm_ok:
        print(f"   {'fuldmodel (5 features)':<34}{'+'+format(fm['wf_improvement'],'.1f')+'%':>10}{p_full*100:>8.1f}%"
              f"   [{fm['status']}]")
    else:
        print(f"   {'fuldmodel (5 features)':<34}{'':>10}{'':>9}   [{fm['status']}]")
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

    # claims/permits: samme definition som trin 4 (12m %-aendring paa maanedens
    # sidste obs) + atlassets 4-ugers niveau. Delvis sidste maaned springes over.
    icsa_raw = read_fred_raw(snap, "ICSA")
    claims_4w = sum(v for _, v in icsa_raw[-4:]) / 4
    mcount = {}
    for _d, _ in icsa_raw:
        mcount[_d[:7]] = mcount.get(_d[:7], 0) + 1
    _mk = sorted(mcount)
    full = _mk[-1] if mcount[_mk[-1]] >= 4 else _mk[-2]
    def _last_in(key):
        vals = [v for _d, v in icsa_raw if _d[:7] == key]
        return vals[-1] if vals else None
    c_now, c_prev = _last_in(full), _last_in(f"{int(full[:4]) - 1}{full[4:]}")
    claims_12m = (c_now / c_prev - 1) * 100 if c_now and c_prev else float("nan")

    pmt = C.read_fred(snap, "PERMIT")
    pmk = sorted(pmt)[-1]
    pm_prev = pmt.get((pmk[0] - 1, pmk[1]))
    permits_yoy = (pmt[pmk] / pm_prev - 1) * 100 if pm_prev else float("nan")

    print("\n4) MONITORS   [individuelle linjer, ingen taellinger, ingen indflydelse paa P]")
    mon = [
        ("Kurven inverteret", x["curve"] < 0, f"{x['curve']:+.2f}pp", "operationel feature"),
        ("Sahm > 0,50", sahm[1] > 0.50, f"{sahm[1]:.2f} ({sahm[0][0]}-{sahm[0][1]:02d})", "testet, ikke bestaaet (trin 4)"),
        ("Claims-momentum", None,
         f"4u-snit {claims_4w/1000:.0f}k; 12m {claims_12m:+.1f}% ({full})",
         "testet, ikke bestaaet (trin 4)"),
        ("Permits y/y", None,
         f"{pmt[pmk]:.0f} ({pmk[0]}-{pmk[1]:02d}); 12m {permits_yoy:+.1f}%",
         "testet, ikke bestaaet (trin 4)"),
        ("HY OAS > 600bp", oas_bp > 600, f"{oas_bp:.0f}bp ({oas_d[0]}-{oas_d[1]:02d})", "ineligible (historik 1997-); svaerm-zone 350-450bp"),
        ("S&P drawdown > 20%", x["dd"] < -0.20, f"{x['dd']*100:+.0f}%", "fuldmodel-feature"),
        ("Advance-estimat: 2 neg. BNP-print", len(adv2) == 2 and all(v < 0 for v in adv2),
         f"{adv2[0]:+.1f}%, {adv2[1]:+.1f}%", "uvalideret realtidsdiagnostik (vintage-flip dokumenteret, trin 5)"),
        ("Inversionsnote", None, inv_note, "uvalideret kontekst"),
    ]
    # svaerm-tripwires (trigger-atlas 2026-08; scenarie-baserede, uvaliderede)
    cp_d, cp_r = latest(C.read_fred(snap, "RIFSPPFAAD90NB"))
    tb_d, tb_r = latest(C.read_fred(snap, "DTB3"))
    cp_spread_bp = (cp_r - tb_r) * 100
    mg_d, mg = latest(C.read_fred(snap, "MORTGAGE30US"))
    acm_f = snap / "acm.csv"
    tp_txt = ""
    if acm_f.exists():
        import csv as _csv
        with acm_f.open(encoding="utf-8-sig") as fh:
            rows = list(_csv.DictReader(fh))
        tp_txt = f" / ACM TP {float(rows[-1]['ACMTP10']):+.2f}pp"
    mon += [
        ("CP-spaend 3m > 75bp", cp_spread_bp > 75,
         f"{cp_spread_bp:.0f}bp ({cp_d[0]}-{cp_d[1]:02d})", "svaerm-tripwire: funding-stress foer kreditspaend"),
        ("10Y > 5,25%", y10 > 5.25, f"{y10:.2f}%{tp_txt}", "svaerm-tripwire: fiskal/term-praemie-kanalen"),
        ("Realkredit 30Y > 7,8%", mg > 7.8, f"{mg:.2f}% ({mg_d[0]}-{mg_d[1]:02d})", "svaerm-tripwire: boligkanalen"),
    ]
    for navn, aktiv, vaerdi, status in mon:
        boks = "[X]" if aktiv else ("[ ]" if aktiv is not None else "[-]")
        print(f"   {boks} {navn:<36}{vaerdi:<48}{status}")

    print()
    print("5) MARKET CONDITIONS — not recession evidence   [kvalitativ]")
    erp = 100 / cape_live - y10
    for navn, vaerdi in [("CAPE-percentil (expanding)", f"{cape_pct*100:.1f}. pct"),
                         ("Aktierisikopraemie 1/CAPE - y10", f"{erp:+.2f}pp"),
                         ("Marginlaan y/y", f"{float(man['margin_yoy']):+.1f}% (manual, {man.get('as_of','?')})")]:
        print(f"       {navn:<34}{vaerdi}")

    # ---- pengepolitik & inflation: KONTEKST, firewallet som atlassets tripwires ----
    # Momentum kun paa saesonkorrigerede serier (PCEPI, CPIAUCSL). Modellens egen
    # cpi_yoy bruger CPIAUCNS — korrekt for y/y, forkert for 3m/6m.
    pol = [("Fed funds (effektiv)", f"{ff[1]:.2f}% ({ff[0][0]}-{ff[0][1]:02d})"),
           ("Realt kontantafkast FF - PCE", f"{ff[1] - pce_yoy:+.2f}pp"),
           ("3m-bill minus Fed funds", f"{(tb_r - ff[1]) * 100:+.0f}bp ({tb_d[0]}-{tb_d[1]:02d}, diskonto)"),
           ("PCE-infl. 3m/6m/12m ann.", f"{ann_rate(pce, 3):.1f} / {ann_rate(pce, 6):.1f} / {pce_yoy:.1f}%")]
    if (snap / "CPIAUCSL.csv").exists():
        cpi_sa = C.read_fred(snap, "CPIAUCSL")
        pol.append(("CPI (SA) 3m/6m/12m ann.",
                    f"{ann_rate(cpi_sa, 3):.1f} / {ann_rate(cpi_sa, 6):.1f} / {ann_rate(cpi_sa, 12):.1f}%"))
    if (snap / "THREEFYTP10.csv").exists():
        _tp = C.read_fred(snap, "THREEFYTP10")
        tp10 = _tp[sorted(_tp)[-1]]
        pol.append(("10y = term-praemie + forventet", f"{y10:.2f} = {tp10:.2f} + {y10 - tp10:.2f}"))
    print()
    print("   PENGEPOLITIK & INFLATION   [kontekst — ingen indflydelse paa P]")
    for navn, vaerdi in pol:
        print(f"       {navn:<34}{vaerdi}")
    print("       Rente og inflation indgaar i P via kurven (operationel feature) og via")
    print("       realrate/d_infl i fuldmodellen — testet, ikke bestaaet (trin 6). Linjerne")
    print("       her er kontekst: hverken i P eller i hovedbogens antaendings-kolonne.")

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
    fa = op.get("vaerste_fejlalarm")
    if not fa:
        sys.exit("FEJL: weights.json mangler op.vaerste_fejlalarm (aeldre/backup-vaegte?) — koer finalize6.py igen.")
    fa_txt = f"Vaerste fejlalarm i walk-forward: {fa['p']*100:.1f}% ({fa['origin']}) uden onset"
    print(f"   P er betinget af NBER-datering pr. {snap.name}. {fa_txt}\n   staar permanent: "
          "kurveregime-risiko gaelder begge veje. Eksogene chok kan ikke forudsiges.")
    print(f"   STI-ADVARSEL (raadsreview 2026-08, enstemmig): modellen laeser kurvens NIVEAU; {x['curve']:+.2f}pp"
          f"\n   behandles som {x['curve']:+.2f}pp uden forhistorie. Seneste inversion: {inv_note}."
          "\n   Historiske onsets er ofte sket i re-steepening-fasen; balance-sheet-drevne"
          "\n   recessioner uden frisk inversion er usynlige for modellen.")

    # ---- 7) hovedbogen: diff mod sidste log + evt. --log-append ----
    logf = HERE.parent / "LOG.md"
    aktive = [navn for navn, aktiv, _, _ in mon if aktiv]
    dom_ord = ("under basisraten" if (band_excludes_base and p_op < base)
               else "over basisraten" if band_excludes_base else "ikke skelnelig")
    rows = laes_hovedbog(logf)
    print("\n7) HOVEDBOG (LOG.md)")
    if rows:
        last = rows[-1]
        try:
            dP = p_op * 100 - float(last["P"].rstrip("%"))
            dK = x["curve"] - float(last["kurve"])
            print(f"   Sidste log {last['logget']}: P {last['P']}, kurve {last['kurve']}")
            print(f"   AENDRING SIDEN SIDST: P {dP:+.1f}pp, kurve {dK:+.2f}pp")
        except ValueError:
            print(f"   Sidste log {last['logget']} (kunne ikke parse diff)")
    else:
        print("   Foerste laesning — ingen historik endnu.")
    if "--log" in sys.argv:
        idag = date.today().isoformat()
        nyeste = sorted(d for d in C.RAW.iterdir() if d.is_dir())[-1]
        if rekal_paakraevet:
            print("   --log AFVIST: rekalibrering paakraevet (§3.2) — den deterministiske trigger udfoeres ved denne "
                  "publiceringskoersel, ikke efter skoen. Koer finalize6.py && diagnostik.py, derefter motor.py --log.")
        elif nyeste != snap:
            print(f"   --log AFVIST: laesningen bygger paa {snap.name}, men nyeste snapshot-mappe er "
                  f"{nyeste.name} (ukomplet/ubrugelig). Hovedbogen faar kun friske data — koer fetch.py igen.")
        elif rows and rows[-1]["logget"][:7] == idag[:7]:
            print(f"   --log AFVIST: {idag[:7]} er allerede logget ({rows[-1]['logget']}). "
                  "Historiske raekker roeres ikke.")
        else:
            noter = []
            kh = W.get("manifest_hash", "")
            # §3.4 bro-raekke: foerste raekke under et nyt manifest printer P under gamle OG nye vaegte ved samme input
            sidste_kal = rows[-1].get("kalibrering", "") if rows else ""
            if kh and sidste_kal != kh and W.get("forrige_manifest"):
                fm_f = HERE / "kalibreringer" / f"manifest_{W['forrige_manifest']}.json"
                if fm_f.exists():
                    gl = json.loads(fm_f.read_text(encoding="utf-8"))["modeller"]["curve_only"]
                    p_gl = float(p_of(x, gl["features"], gl["mu"], gl["sd"], gl["w"]))
                    noter.append(f"bro: P(v{gl.get('version', '?')} {W['forrige_manifest']})={p_gl*100:.1f}% / "
                                 f"P(v{W.get('version', '?')} {kh})={p_op*100:.1f}% ved identiske inputs")
            ov = meta.get("spine", {}).get("outlier_override")
            if ov:
                noter.append(f"--accept-outlier: {ov.get('begrundelse', '')} ({'; '.join(ov.get('observationer', []))})")
            linje = (f"| {idag} | {snap.name} | {p_op*100:.1f}% | {lo*100:.1f}-{hi*100:.1f}% | "
                     f"{base*100:.1f}% | {dom_ord} | {x['curve']:+.2f} | "
                     f"{', '.join(aktive) if aktive else 'ingen'} | {'; '.join(noter)} | {kh} |")
            with logf.open("a", encoding="utf-8", newline="\n") as fh:
                fh.write(linje + "\n")
            print(f"   LOGGET som raekke {len(rows) + 1}: {idag}, P {p_op*100:.1f}%, dom '{dom_ord}'.")

    # ---- 8) diagnostik (RAADETS_V501 §4): printes, aendrer intet ----
    diag = None
    df = HERE / "diagnostik.json"
    if df.exists():
        try:
            diag = json.loads(df.read_text(encoding="utf-8"))
        except ValueError:
            diag = None
    print("\n8) DIAGNOSTIK (RAADETS_V501 §4 — printes ved siden af, aendrer hverken gate, vaegte eller dom)")
    if not diag:
        print("   diagnostik.json mangler — koer python diagnostik.py efter rekalibrering.")
    else:
        if diag.get("manifest_hash") != W.get("manifest_hash"):
            print(f"   ADVARSEL: diagnostik.json er fra kalibrering {diag.get('manifest_hash')}, vaegtene er {W.get('manifest_hash')} — koer diagnostik.py igen.")
        pr = diag["primaer"]
        print(f"   4.1 Episode-tabel (curve-only wf, {pr['n']} origins; bidrag summerer til +{diag['episode_tabel']['sum_bidrag_pp']}pp):")
        print(f"       {'episode':<24}{'n':>4}{'pos':>5}{'bidrag':>9}{'max P':>8}")
        for r in diag["episode_tabel"]["raekker"]:
            print(f"       {r['episode']:<24}{r['n']:>4}{r['n_pos']:>5}{r['bidrag_pp']:>+8.2f}p{r['max_p']*100:>7.1f}%")
        nb = diag["episode_tabel"]["negative_pr_blok"]
        print("       negative pr. blok (op til onset): " + "; ".join(f"{b['blok']} {b['origins']} {b['bidrag_pp']:+.2f}pp (max {b['max_p']*100:.0f}%)" for b in nb))
        lo8 = diag["loeo"]
        print(f"   4.2 LOEO (sensitivitet): {len(lo8['blokke'])} blokke, median {lo8['median']:+.1f}%, min {lo8['min']:+.1f}%"
              + (f", udefineret {lo8['udefinerede']}" if lo8.get("udefinerede") else "") + " — aldrig co-primaer")
        bt = diag["domsregler_backtest"]
        print(f"   4.3 Domsregler backtestet ({bt['n_origins']} origins x {bt['n_draws']} traek): baandreglen skelnelig {bt['baand_skelnelig']}, "
              f"parret {bt['parret_skelnelig']}, uenige {bt['uenige']} ({bt['uenighedsrate']*100:.1f} %)"
              + (": " + ", ".join(u["origin"] for u in bt["uenige_origins"][:6]) + (" ..." if len(bt["uenige_origins"]) > 6 else "") if bt["uenige"] else ""))
        print("       Ingen automatisk migration af domsreglen: et skift er en separat raadsbeslutning mod praeregistrerede kriterier.")
        pl = diag["parret_loss_bootstrap"]
        print(f"   4.4 Historisk parret loss-bootstrap: middel {pl['middel_pp']:+.3f}, 90 %-interval [{pl['interval_90'][0]:+.3f}, {pl['interval_90'][1]:+.3f}], "
              f"P(<=0) = {pl['andel_ikke_positiv']:.3f}  (skill-diagnostik ved siden af MDE)")
        oc = diag["oracle_fri"]; a = oc["additional_live_publishable"]
        print(f"   4.5 Oracle-fri (censurering som af origin-datoen, modellens egen label): alle live-publicerbare "
              f"{oc['alle_live_publicerbare']['n']} origins +{oc['alle_live_publicerbare']['improvement']}% | ekskl. {a['n']} additional "
              f"live-publishable origins +{oc['ekskl_additional']['improvement']}% (max P blandt dem {a['max_p']*100:.0f}%). Tolkes i tandem.")
        s73 = diag["skill_73"]
        print(f"   §7.3 Trunkeret panel +{s73['trunkeret_panel']['improvement'] if s73.get('trunkeret_panel') else '?'}% | udvidet: faelles origins "
              f"+{s73['udvidet_faelles_origins']['improvement']}%, tilfoejede " + ", ".join(f"{t['origin']} P={t['p']*100:.0f}% Y={int(t['Y'])}" for t in s73["tilfoejede_origins"]))
        print(f"   §3.6 Baseline: publiceret = poolet basisrate (+{pr['improvement']}%); expanding-intercept-udgave +{pr['improvement_expanding']}% (ekstra kolonne, aendrer ikke gaten)")

    if "--json" in sys.argv:
        k = sys.argv.index("--json")
        har_sti = len(sys.argv) > k + 1 and not sys.argv[k + 1].startswith("-")
        ud = Path(sys.argv[k + 1]) if har_sti else HERE.parent / "dashboard.json"

        bm = [dict(navn="intercept (basisrate)", wf=0.0, live_p=round(base, 6), status=None),
              dict(navn="curve-only-logit (NY Fed-stil-bm.)",
                   wf=W["benchmarks"]["curve_only"]["wf_improvement"], live_p=round(p_curve, 6),
                   status="OPERATIONEL" if W["operationel"] == "curve_only" else None),
              dict(navn="fuldmodel (5 features)", wf=fm["wf_improvement"],
                   live_p=round(p_full, 6), status=fm["status"])]
        for navn, blok in (("curve+cape (praereg. v5.1-test)", cc), ("curve+awh (praereg. v5.2-test)", ca)):
            if blok:
                bm.append(dict(navn=navn, wf=blok["wf_improvement"], live_p=None, status=blok["status"]))
        if p_arv is not None:
            bm.append(dict(navn="v4-arv (teknisk label)", wf=None, live_p=round(p_arv, 6),
                           status="andet maal - arv"))
        bm.append(dict(navn="realtids-Sahm (trigger 0,50)", wf=None, live_p=None,
                       vaerdi=sahm[1], status="naerhorisont-signal"))
        bm.append(dict(navn="Chauvet-Piger nowcast", wf=None, live_p=round(cp[1] / 100, 6),
                       status="coincident, publiceringslag - anden disciplin"))

        mc = [("CAPE-percentil (expanding)", f"{cape_pct*100:.1f}. pct"),
              ("Aktierisikopraemie 1/CAPE - y10", f"{erp:+.2f}pp"),
              ("Marginlaan y/y", f"{float(man['margin_yoy']):+.1f}% (manual, {man.get('as_of','?')})")]

        hb = laes_hovedbog(logf)
        for r in hb:
            b = [tal_af(v, 0.01) for v in r.get("baand", "").split("-")]
            r["p_tal"] = tal_af(r.get("P"), 0.01)
            r["baand_tal"] = b if len(b) == 2 and None not in b else None
            r["basisrate_tal"] = tal_af(r.get("basisrate"), 0.01)
            r["kurve_tal"] = tal_af(r.get("kurve"))

        sti = ("Modellen laeser kurvens NIVEAU; "
               f"{x['curve']:+.2f}pp behandles som {x['curve']:+.2f}pp uden forhistorie. "
               f"Seneste inversion: {inv_note}. Historiske onsets er ofte sket i "
               "re-steepening-fasen; balance-sheet-drevne recessioner uden frisk "
               "inversion er usynlige for modellen.")

        data = dict(
            version=W.get("version", "5.0"), manifest_hash=W.get("manifest_hash"),
            forrige_manifest=W.get("forrige_manifest"), raa=op.get("raa"), bro=W.get("bro"),
            gate=W.get("gate"), stale=meta.get("stale"), diagnostik=diag,
            snapshot=snap.name, snapshot_hash=meta["snapshot_sha256"][:10],
            model="curve-only-logit" if W["operationel"] == "curve_only" else "fuldmodel",
            label=W["label_tekst"], kalibreret=W["created_utc"][:10],
            n_obs=W["n_obs"], n_episoder=W["n_episoder"],
            wf_log_loss=op["wf_improvement"], wf_brier=op["wf_brier"],
            p=round(p_op, 6), baand=[round(float(lo), 6), round(float(hi), 6)],
            basisrate=base, baand_udelukker_basisrate=bool(band_excludes_base),
            ratio=round(p_op / base, 4) if band_excludes_base else None,
            baand_fodnote=W["band"]["fodnote"], dom=dom,
            inputs=[dict(navn=NAVN[f], vaerdi=round(x[f], 4),
                         z=round((x[f] - fm["mu"][f]) / fm["sd"][f], 4),
                         operationel=f in op["features"]) for f in fm["features"]],
            benchmarks=bm,
            monitors=[dict(navn=n,
                           tilstand="aktiv" if a else ("inaktiv" if a is not None else "kontekst"),
                           vaerdi=v, klasse=s) for n, a, v, s in mon],
            market_conditions=[dict(navn=n, vaerdi=v) for n, v in mc],
            pengepolitik=[dict(navn=n, vaerdi=v) for n, v in pol],
            advarsler=dict(vaerste_fejlalarm=fa, sti_advarsel=sti,
                           eksogen="Eksogene chok kan ikke forudsiges."),
            hovedbog=hb,
        )
        ud.write_text(json.dumps(data, indent=2, ensure_ascii=False) + chr(10), encoding="utf-8")
        print(f"{chr(10)}   JSON skrevet: {ud}  ({len(hb)} hovedbogsraekker)")



if __name__ == "__main__":
    main()
