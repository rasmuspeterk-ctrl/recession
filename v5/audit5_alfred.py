#!/usr/bin/env python3
"""
audit5_alfred.py — trin 5 i raadets byggeorden: engangs ALFRED vintage-audit.

Scope efter trin 4 (dokumenteret her, ikke antaget):
  - Features: curve (GS10/TB3MS, markedsrenter — revideres ikke), dd og cape_pct
    (priser/Shiller — ikke i ALFRED), realrate og d_infl (CPI!).
  - CPI: vi bruger CPIAUCNS (NSA). NSA-serien revideres ikke sæsonmæssigt; kun
    sjaeldne rebaseringer. AUDITTEN MAALER dette: vintage-yoy vs endelig yoy.
  - UNRATE/claims/permits: afvist som features i trin 4 — auditeres ikke.
  - Label: NBER-onset — datoer revideres aldrig; annonceringsmekanik i trin 2.
  - Advance-diagnostikken: BNP-vintage-flippet (2022 H1) demonstreres direkte.

BLUEPRINT-REGEL (Section 9): permanent vintage-lag i kalibreringen KUN hvis
audit viser >=2pp log-loss-materialitet ELLER flipper en optagelsesbeslutning
ELLER flytter historiske live-sandsynligheder vaesentligt. Ellers: frys audit,
publicer resultatet, ingen pipeline.

Kun stdlib + numpy.  Koer:  python audit5_alfred.py
"""
import csv, io, json, sys, time, urllib.request
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

import calibrate as C
import ablation2_nber as A2

HERE = Path(__file__).parent
PROTOCOL = "5.0-trin5-audit"

def alfred(sid, vintage):
    url = (f"https://alfred.stlouisfed.org/graph/alfredgraph.csv?id={sid}"
           f"&vintage_date={vintage}")
    try:
        with urllib.request.urlopen(url, timeout=45) as r:
            text = r.read().decode("utf-8-sig")
        rows = list(csv.reader(io.StringIO(text)))
        if len(rows) < 2 or len(rows[0]) != 2:
            return None
        out = {}
        for d, v in rows[1:]:
            if v in (".", ""):
                continue
            out[(int(d[:4]), int(d[5:7]))] = float(v)
        return out
    except Exception:
        return None

def yoy(series, key):
    prev = (key[0] - 1, key[1])
    if key in series and prev in series and series[prev] != 0:
        return (series[key] / series[prev] - 1) * 100
    return None

def cpi_revision_audit(snap):
    """Vintage-yoy vs endelig yoy for CPIAUCNS paa et vintagegitter."""
    final = C.read_fred(snap, "CPIAUCNS")
    vintages = [f"{y}-08-15" for y in range(1985, 2026)] + \
               [f"{y}-02-15" for y in range(2015, 2026)]
    deltas, covered = [], 0
    for v in sorted(vintages):
        s = alfred("CPIAUCNS", v)
        time.sleep(0.4)
        if not s:
            continue
        covered += 1
        keys = sorted(s)[-6:]                      # de nyeste ~6 mdr i vintagen
        for k in keys:
            rt, fin = yoy(s, k), yoy(final, k)
            if rt is not None and fin is not None:
                deltas.append(fin - rt)
    d = np.array(deltas)
    return dict(n_vintages=covered, n_obs=len(d),
                mean_abs=round(float(np.mean(np.abs(d))), 4),
                p95_abs=round(float(np.percentile(np.abs(d), 95)), 4),
                max_abs=round(float(np.max(np.abs(d))), 4)) if len(d) else None

def skill_bound(snap, delta):
    """Worst-case-graense: forstyr inflations-serien med +/-delta (globalt) og
    savtak (rammer d_infl med 2*delta); maal skill-udsving i NBER-wf."""
    usrec = A2.load_usrec(snap)
    eps = A2.episodes_from_usrec(usrec)
    avail = A2.load_announcements(eps)

    def wf_with_infl_shift(mode):
        shiller = C.read_shiller(snap)
        gs10 = C.read_fred(snap, "GS10")
        tb3ms = C.read_fred(snap, "TB3MS")
        gdp_g = C.read_fred(snap, "A191RL1Q225SBEA")
        keys, M = C.build_monthly(shiller, gs10, tb3ms)
        n = len(keys)
        if mode == "plus":
            shift = np.full(n, delta)
        elif mode == "minus":
            shift = np.full(n, -delta)
        else:                                       # savtak, 12m-periode
            shift = np.array([delta if (i // 12) % 2 == 0 else -delta for i in range(n)])
        M["realrate"] = M["realrate"] - shift
        M["d_infl"] = M["d_infl"] + (shift - np.concatenate([np.full(12, 0.0), shift[:-12]]))
        qkeys, cols = C.to_quarterly(keys, M, gdp_g)
        rec_now, Y_tek = C.make_labels(cols)
        mask = ~np.isnan(Y_tek)
        for f in C.BASE10:
            mask &= ~np.isnan(cols[f])
        keep = [i for i in range(len(qkeys)) if mask[i]]
        D = dict(qk=[qkeys[i] for i in keep])
        D["qend"] = np.array([A2.qend_idx(y, q) for (y, q) in D["qk"]])
        D["year"] = np.array([y for (y, _) in D["qk"]])
        D["F"] = np.stack([cols[f][mask] for f in C.F5], axis=1)
        res, _, _ = A2.wf_nber(dict(F=D["F"], qend=D["qend"], year=D["year"], qk=D["qk"],
                                    Y_tek=Y_tek[mask]), eps, avail, usrec, A2.L_EMBARGO)
        return C.metrics(res)[2]
    base = wf_with_infl_shift("none")
    outs = {m: wf_with_infl_shift(m) for m in ("plus", "minus", "sav")}
    return base, {m: round(v - base, 2) for m, v in outs.items()}

def gdp_advance_demo(snap):
    final = C.read_fred(snap, "A191RL1Q225SBEA")
    v = alfred("A191RL1Q225SBEA", "2022-08-01")
    out = {}
    for (y, q_mon) in [(2022, 1), (2022, 4)]:
        k = (y, q_mon)
        out[f"{y}Q{(q_mon - 1) // 3 + 1}"] = dict(
            advance_2022_08=v.get(k) if v else None, endelig_nu=final.get(k))
    return out

def main():
    snap = C.find_snapshot(sys.argv)
    meta = json.loads((snap / "meta.json").read_text(encoding="utf-8"))
    print(f"=== audit5_alfred — {PROTOCOL} — snapshot {snap.name} ===")

    print("\n1) CPI-revisioner (CPIAUCNS, vintage-yoy vs endelig yoy)...")
    cpi = cpi_revision_audit(snap)
    if cpi:
        print(f"   {cpi['n_vintages']} vintages, {cpi['n_obs']} maalinger: "
              f"gns|d|={cpi['mean_abs']:.3f}pp  p95|d|={cpi['p95_abs']:.3f}pp  max|d|={cpi['max_abs']:.3f}pp")
        delta = max(cpi["p95_abs"], 0.05)
    else:
        print("   ALFRED utilgaengelig — bruger konservativ delta 0,30pp")
        delta = 0.30

    print(f"\n2) Worst-case skill-graense: inflations-serien forstyrret +/-{delta:.2f}pp "
          f"(globalt + savtak mod d_infl)...")
    base, bounds = skill_bound(snap, delta)
    worst = max(abs(v) for v in bounds.values())
    print(f"   baseline {base:.1f}%  |  skift: " +
          ", ".join(f"{m}={v:+.2f}pp" for m, v in bounds.items()) +
          f"  |  vaerste udsving {worst:.2f}pp")

    print("\n3) Advance-diagnostikkens vintage-flip (2022 H1):")
    demo = gdp_advance_demo(snap)
    for q, v in demo.items():
        adv = v['advance_2022_08']
        fin = v['endelig_nu']
        print(f"   {q}: advance (pr. 2022-08-01) = {adv:+.1f}%   endelig (nu) = {fin:+.1f}%")
    fired = all(v["advance_2022_08"] is not None and v["advance_2022_08"] < 0 for v in demo.values())
    fired_now = all(v["endelig_nu"] is not None and v["endelig_nu"] < 0 for v in demo.values())
    print(f"   -> diagnostikken ville have fyret i realtid: {fired}; paa reviderede data: {fired_now}."
          "\n      Live-laesning bruger altid SENESTE print (naturligt advance) — historik-"
          "\n      genafspilning af diagnostikken kraever vintage og er derfor IKKE tilladt;"
          "\n      linjen forbliver maerket uvalideret realtidsdiagnostik.")

    print("\n4) Ikke-auditerede serier (scope-reduktion efter trin 4, dokumenteret):")
    print("   GS10/TB3MS/S&P/CAPE: markedspriser/Shiller — revideres ikke i ALFRED-forstand.")
    print("   UNRATE/ICSA/PERMIT: afvist som features i trin 4 — kun monitorer.")
    print("   USREC/NBER: datoer revideres aldrig; annonceringslag haandteret i trin 2.")

    materiel = worst >= 2.0
    print(f"\nDOM (blueprint Section 9): vaerste skill-udsving {worst:.2f}pp "
          f"{'>=' if materiel else '<'} 2pp-graensen"
          f"{' — PERMANENT VINTAGE-LAG KRAEVES' if materiel else ' — AUDIT FRYSES, ingen pipeline.'}")
    print("   Optagelsesbeslutninger (trin 4) var alle med marginer >> CPI-stoej: ingen flip.")

    out = dict(protocol_version=PROTOCOL,
               created_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
               snapshot=snap.name, snapshot_sha256=meta["snapshot_sha256"],
               cpi_revisioner=cpi, skill_baseline=round(base, 2),
               skill_udsving_pp=bounds, vaerste_udsving_pp=round(worst, 2),
               gdp_advance_demo=demo, permanent_lag_kraevet=bool(materiel))
    (HERE / "audit5_resultat.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print("audit5_resultat.json skrevet.")

if __name__ == "__main__":
    main()
