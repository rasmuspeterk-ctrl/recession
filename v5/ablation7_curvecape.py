#!/usr/bin/env python3
"""
ablation7_curvecape.py — praeregistreret v5.1-test af curve+cape_pct-subsettet.

ADVARSEL OM OPHAV (permanent): hypotesen er DATA-FORESLAAET — affoedt af trin 4's
drop-analyse og trin 6's benchmark paa samme walk-forward som doemmer den her.
Derfor er gates STRAMMERE end trin 4's, og resultatet baerer stemplet uanset udfald.
Der findes ingen tiende delmaengde-hypotese efter denne uden ny oekonomisk
begrundelse (nedskrevet i README foer koersel).

FORHAANDSREGISTREREDE GATES (alle skal bestaas; fastlagt FOER koersel):
  G1  determinisme (to koersler identiske)
  G2  slaar den OPERATIONELLE model (curve-only): parret dLL >= +2,0pp OG
      dBrier >= +2,0pp
  G3  LOEO: begge niveauer holder i >= 80% af folds; dLL > 0 i ALLE folds
  G4  fortegns-STABILITET: cape-koefficienten har samme fortegn i >= 80% af
      LOEO-refits (ingen retning praeregistreres — ingen trovaerdig prior;
      repricing-historien siger +, fittet historik siger −)
  G5  aera-split (anti-forurening): parret dLL vs curve-only > 0 i BEGGE
      halvdele separat (scorede origins < 1990 og >= 1990)
  G6  bootstrap-persistens >= 60% (1000 episode-blok-traek, seed 42); MDE printes

UDFALD (besluttet nu):
  Alle bestaaet -> curve+cape promoveres operationelt MED permanent stempel
  "data-foreslaaet, promoveret 2026-08" i weights.json og motor-output.
  Een fejlet -> permanent benchmark-linje "testet, ikke bestaaet (data-foreslaaet)".

Kun stdlib + numpy.  Koer:  python ablation7_curvecape.py [--check] [--promote]
"""
import json, sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

import calibrate as C
import ablation2_nber as A2
import ablation4_features as A4
import finalize6 as F6

HERE = Path(__file__).parent
PROTOCOL = "5.1-curvecape"
SEED = 42
FEATS = ["curve", "cape_pct"]
IDX = [0, 4]                      # positioner i C.F5

def wf_subset(D, eps, avail, usrec, idx):
    Ds = dict(F=D["F"][:, idx], qend=D["qend"], year=D["year"], qk=D["qk"])
    res, _, _ = A2.wf_nber(Ds, eps, avail, usrec, A2.L_EMBARGO)
    return {(y, q): (p, yy) for (y, q, p, yy) in res}

def cape_sign_stability(D, eps, usrec):
    """Fuld-fit-fortegn for cape_pct i 2-feature-modellen + andel LOEO-refits med samme fortegn."""
    F = D["F"][:, IDX]
    n = len(D["qend"])
    Y = np.zeros(n); in_rec = np.zeros(n, bool)
    for j in range(n):
        lo, hi = D["qend"][j] + 1, D["qend"][j] + 12
        Y[j] = 1.0 if any(lo <= o <= hi for o, _ in eps) else 0.0
        in_rec[j] = usrec.get(int(D["qend"][j]), 0) == 1
    base_rows = ~in_rec
    def coef(rows):
        X = F[rows]; y = Y[rows]
        mu, sd = X.mean(0), X.std(0, ddof=1); sd[sd == 0] = 1
        return C.fit((X - mu) / sd, y)[2]          # [int, curve, cape]
    full = coef(base_rows)
    hits = 0; total = 0
    for o, tr_ in eps:
        drop = np.array([(D["qend"][j] + 1 <= o <= D["qend"][j] + 12) or
                         (o <= D["qend"][j] <= tr_) for j in range(n)])
        rows = base_rows & ~drop
        if rows.sum() < 80 or Y[rows].sum() < 5:
            continue
        total += 1
        if np.sign(coef(rows)) == np.sign(full):
            hits += 1
    return float(np.sign(full)), (hits / total * 100 if total else 0.0), total

def run(snap):
    usrec = A2.load_usrec(snap)
    eps = A2.episodes_from_usrec(usrec)
    avail = A2.load_announcements(eps)
    D = A2.build_dataset(snap)

    m2 = wf_subset(D, eps, avail, usrec, IDX)          # curve+cape
    mc = wf_subset(D, eps, avail, usrec, [0])          # curve-only (operationel)
    i2, b2, ic, bc, npair, ks = A4.paired_metrics(m2, mc)
    dll, dbr = i2 - ic, b2 - bc

    folds = A4.loeo_deltas(m2, mc, ks, eps)
    lvl = sum(1 for (_, a, b) in folds if a >= 2.0 and b >= 2.0)
    pos_all = all(a > 0 for (_, a, _) in folds)
    persist, mde = A4.bootstrap_persist(m2, mc, ks, eps)
    fsign, sstab, sfolds = cape_sign_stability(D, eps, usrec)

    pre = [k for k in ks if k[0] < 1990]; post = [k for k in ks if k[0] >= 1990]
    def imp_on(keys, m):
        rows = [(y, q, m[(y, q)][0], m[(y, q)][1]) for (y, q) in keys]
        return C.metrics(rows)[2]
    d_pre = imp_on(pre, m2) - imp_on(pre, mc)
    d_post = imp_on(post, m2) - imp_on(post, mc)

    return dict(curvecape=dict(improvement=round(i2, 2), brier=round(b2, 2)),
                curveonly=dict(improvement=round(ic, 2), brier=round(bc, 2)),
                dLL=round(dll, 2), dBrier=round(dbr, 2), n_parret=npair,
                folds_niveau_pct=round(lvl / len(folds) * 100 if folds else 0, 0),
                alle_folds_positive=bool(pos_all),
                persistens_pct=round(persist, 1), mde_pp=round(mde, 2),
                cape_fortegn=int(fsign), fortegn_stab_pct=round(sstab, 0), fortegn_folds=sfolds,
                aera_pre1990_dLL=round(d_pre, 2), aera_post1990_dLL=round(d_post, 2),
                n_pre=len(pre), n_post=len(post))

def main():
    snap = C.find_snapshot(sys.argv)
    meta = json.loads((snap / "meta.json").read_text(encoding="utf-8"))
    print(f"=== ablation7_curvecape — {PROTOCOL} — snapshot {snap.name} ===")
    print("STEMPEL: data-foreslaaet hypotese — gates er stramme med vilje.\n")
    res = run(snap)
    det_ok = True
    if "--check" in sys.argv:
        det_ok = (res == run(snap))
        print("G1 DETERMINISME: " + ("OK" if det_ok else "FEJL"))

    print(f"\ncurve+cape: +{res['curvecape']['improvement']:.1f}% LL / +{res['curvecape']['brier']:.1f}% Brier")
    print(f"curve-only: +{res['curveonly']['improvement']:.1f}% LL / +{res['curveonly']['brier']:.1f}% Brier   "
          f"(parret, n={res['n_parret']})")
    print(f"parret forskel: dLL={res['dLL']:+.2f}pp  dBrier={res['dBrier']:+.2f}pp  "
          f"(MDE {res['mde_pp']:.1f}pp)")
    print(f"LOEO: {res['folds_niveau_pct']:.0f}% af folds paa niveau; alle positive: {res['alle_folds_positive']}")
    print(f"cape-fortegn: {'+' if res['cape_fortegn'] > 0 else '-'} i fuld-fit; "
          f"stabilt i {res['fortegn_stab_pct']:.0f}% af {res['fortegn_folds']} LOEO-refits")
    print(f"aera-split dLL: pre-1990 {res['aera_pre1990_dLL']:+.2f}pp (n={res['n_pre']})  |  "
          f"post-1990 {res['aera_post1990_dLL']:+.2f}pp (n={res['n_post']})")
    print(f"persistens: {res['persistens_pct']:.1f}%")

    g2 = res["dLL"] >= 2.0 and res["dBrier"] >= 2.0
    g3 = res["folds_niveau_pct"] >= 80 and res["alle_folds_positive"]
    g4 = res["fortegn_stab_pct"] >= 80
    g5 = res["aera_pre1990_dLL"] > 0 and res["aera_post1990_dLL"] > 0
    g6 = res["persistens_pct"] >= 60
    print("\nGATES (forhaandsregistreret):")
    for navn, ok in [("G1 determinisme", det_ok), ("G2 dLL>=2 & dBrier>=2", g2),
                     ("G3 LOEO 80% + alle pos", g3), ("G4 fortegnsstabilitet 80%", g4),
                     ("G5 aera-split begge pos", g5), ("G6 persistens 60%", g6)]:
        print(f"  {navn:<28}{'BESTAAET' if ok else 'FEJLET'}")
    verdict = all([det_ok, g2, g3, g4, g5, g6])
    print(f"\nSAMLET: {'PROMOVER curve+cape (med permanent data-foreslaaet-stempel)' if verdict else 'TESTET, IKKE BESTAAET (data-foreslaaet) — curve-only forbliver operationel'}")

    out = dict(protocol_version=PROTOCOL,
               created_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
               snapshot=snap.name, snapshot_sha256=meta["snapshot_sha256"],
               stempel="data-foreslaaet hypotese (trin 4-drop + trin 6-benchmark)",
               gates=dict(G1=bool(det_ok), G2=bool(g2), G3=bool(g3), G4=bool(g4),
                          G5=bool(g5), G6=bool(g6), promoveret=bool(verdict)), **res)
    (HERE / "ablation7_resultat.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print("ablation7_resultat.json skrevet.")

    # benchmark-linjen skrives ALTID ind i weights.json (permanent, uanset udfald)
    wfile = HERE / "weights.json"
    W = json.loads(wfile.read_text(encoding="utf-8"))
    W["benchmarks"]["curve_cape"] = dict(
        wf_improvement=res["curvecape"]["improvement"], wf_brier=res["curvecape"]["brier"],
        status=("operationel (data-foreslaaet, promoveret 2026-08)" if verdict and "--promote" in sys.argv
                else "testet, ikke bestaaet (data-foreslaaet)" if not verdict
                else "bestaaet — afventer --promote"))
    if verdict and "--promote" in sys.argv:
        usrec = A2.load_usrec(snap); eps = A2.episodes_from_usrec(usrec)
        D = A2.build_dataset(snap)
        Y, _, in_rec = A2.nber_labels(D, eps, usrec)
        fitm = ~in_rec
        X = D["F"][fitm][:, IDX]; y = Y[fitm]
        mu, sd = X.mean(0), X.std(0, ddof=1); sd[sd == 0] = 1
        w = C.fit((X - mu) / sd, y)
        Wb, _ = F6.boot_weights((X - mu) / sd, y, D["qend"][fitm], eps, 1000)
        bk = HERE / f"weights_backup_{W['protocol_version']}-{W['operationel']}.json"
        bk.write_text(json.dumps(W, indent=1), encoding="utf-8")
        W["operationel"] = "curve_cape"
        W["op"] = dict(features=FEATS,
                       mu={f: round(float(m), 4) for f, m in zip(FEATS, mu)},
                       sd={f: round(float(s), 4) for f, s in zip(FEATS, sd)},
                       w=[round(float(v), 4) for v in w],
                       wf_improvement=res["curvecape"]["improvement"],
                       wf_brier=res["curvecape"]["brier"],
                       stempel="data-foreslaaet, promoveret 2026-08")
        W["band"] = dict(metode="episode-blok-bootstrap af vaegte, fast standardisering",
                         fodnote="Not a predictive interval; reflects weight sensitivity to episode composition",
                         seed=SEED, n_draws=len(Wb), W=Wb)
        print("PROMOVERET: weights.json er nu curve+cape (backup skrevet).")
    wfile.write_text(json.dumps(W, indent=1), encoding="utf-8")

if __name__ == "__main__":
    main()
