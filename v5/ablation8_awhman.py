#!/usr/bin/env python3
"""
ablation8_awhman.py — det SIDSTE praeregistrerede feature-skud: AWHMAN
(ugentlige arbejdstimer, industri, FRED 1939+). Raadets grand review delte sig
6-5 om skuddet; Rasmus godkendte det 2026-08-10. Efter denne test er
informationssoegningen LUKKET uanset udfald (naeste kandidat kraever ny
oekonomisk begrundelse og nyt raads-mandat).

SOLS FORSEGLEDE SPEC (fra reviewets runde B, laast FOER koersel):
  awh = 6-maaneders annualiseret %-aendring i AWHMAN, publikationslagget 1 md:
        awh(m) = ((AWHMAN[m-1]/AWHMAN[m-7])^2 - 1) * 100
  Forventet koefficient-fortegn: NEGATIVT (faldende timer -> hoejere onset-risiko).

PRIMAER SAMMENLIGNING (afgoer optagelse): [curve, awh] vs [curve] — den
operationelle model. Sekundaer diagnostik (rapporteres, afgoer intet):
[F5 + awh] vs F5.

GATES — praecis trin 4's ratificerede optagelsesgates (symmetrisk med
sahm/claims/permits; AWHMAN er oekonomisk begrundet, ikke data-foreslaaet,
saa v5.1-testens ekstra-gates gaelder ikke, men aera-splittet RAPPORTERES):
  G1  determinisme
  A1  parret dLL >= +2,0pp OG dBrier >= +2,0pp (mod curve-only)
  A2  begge niveauer i >= 80% af LOEO-folds; dLL > 0 i ALLE folds
  A3  negativt fortegn i fuld-fit OG i >= 80% af LOEO-refits
  Bootstrap-persistens og MDE printes; aera-split (pre/post-1990) printes.

Kun stdlib + numpy.  Koer:  python ablation8_awhman.py [--check]
"""
import json, sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

import calibrate as C
import ablation2_nber as A2
import ablation4_features as A4

HERE = Path(__file__).parent
PROTOCOL = "5.2-awhman"

def build(snap):
    shiller = C.read_shiller(snap)
    gs10 = C.read_fred(snap, "GS10")
    tb3ms = C.read_fred(snap, "TB3MS")
    gdp_g = C.read_fred(snap, "A191RL1Q225SBEA")
    awh_raw = C.read_fred(snap, "AWHMAN")
    keys, M = C.build_monthly(shiller, gs10, tb3ms)
    a = np.array([awh_raw.get(k, np.nan) for k in keys])
    awh = np.full(len(a), np.nan)
    for i in range(7, len(a)):
        if not (np.isnan(a[i - 1]) or np.isnan(a[i - 7])) and a[i - 7] != 0:
            awh[i] = ((a[i - 1] / a[i - 7]) ** 2 - 1) * 100     # 6m ann., lagget 1md
    M["awh"] = awh
    qkeys, cols = C.to_quarterly(keys, M, gdp_g)
    rec_now, Y_tek = C.make_labels(cols)
    mask = ~np.isnan(Y_tek)
    for f in C.BASE10 + ["awh"]:
        mask &= ~np.isnan(cols[f])
    keep = [i for i in range(len(qkeys)) if mask[i]]
    D = dict(qk=[qkeys[i] for i in keep])
    D["qend"] = np.array([A2.qend_idx(y, q) for (y, q) in D["qk"]])
    D["year"] = np.array([y for (y, _) in D["qk"]])
    D["X"] = {f: cols[f][mask] for f in C.F5 + ["awh"]}
    return D

def wf(D, feats, eps, avail, usrec):
    Ds = dict(F=np.stack([D["X"][f] for f in feats], axis=1),
              qend=D["qend"], year=D["year"], qk=D["qk"])
    res, _, _ = A2.wf_nber(Ds, eps, avail, usrec, A2.L_EMBARGO)
    return {(y, q): (p, yy) for (y, q, p, yy) in res}

def sign_stability(D, eps, usrec):
    F = np.stack([D["X"]["curve"], D["X"]["awh"]], axis=1)
    n = len(D["qend"])
    Y = np.zeros(n); in_rec = np.zeros(n, bool)
    for j in range(n):
        lo, hi = D["qend"][j] + 1, D["qend"][j] + 12
        Y[j] = 1.0 if any(lo <= o <= hi for o, _ in eps) else 0.0
        in_rec[j] = usrec.get(int(D["qend"][j]), 0) == 1
    rows0 = ~in_rec
    def coef(rows):
        X = F[rows]; y = Y[rows]
        mu, sd = X.mean(0), X.std(0, ddof=1); sd[sd == 0] = 1
        return C.fit((X - mu) / sd, y)[2]          # [int, curve, awh]
    full = coef(rows0)
    hits = total = 0
    for o, tr_ in eps:
        drop = np.array([(D["qend"][j] + 1 <= o <= D["qend"][j] + 12) or
                         (o <= D["qend"][j] <= tr_) for j in range(n)])
        rows = rows0 & ~drop
        if rows.sum() < 80 or Y[rows].sum() < 5:
            continue
        total += 1
        if coef(rows) < 0:
            hits += 1
    return float(full), (hits / total * 100 if total else 0.0), total

def run(snap):
    usrec = A2.load_usrec(snap)
    eps = A2.episodes_from_usrec(usrec)
    avail = A2.load_announcements(eps)
    D = build(snap)

    m_ca = wf(D, ["curve", "awh"], eps, avail, usrec)
    m_c = wf(D, ["curve"], eps, avail, usrec)
    ia, ba, ic, bc, npair, ks = A4.paired_metrics(m_ca, m_c)
    dll, dbr = ia - ic, ba - bc
    folds = A4.loeo_deltas(m_ca, m_c, ks, eps)
    lvl = sum(1 for (_, a, b) in folds if a >= 2.0 and b >= 2.0)
    pos_all = all(a > 0 for (_, a, _) in folds)
    persist, mde = A4.bootstrap_persist(m_ca, m_c, ks, eps)
    full_coef, sstab, sfolds = sign_stability(D, eps, usrec)

    pre = [k for k in ks if k[0] < 1990]; post = [k for k in ks if k[0] >= 1990]
    def imp_on(keys, m):
        rows = [(y, q, m[(y, q)][0], m[(y, q)][1]) for (y, q) in keys]
        return C.metrics(rows)[2]
    d_pre = imp_on(pre, m_ca) - imp_on(pre, m_c)
    d_post = imp_on(post, m_ca) - imp_on(post, m_c)

    m_f6 = wf(D, C.F5 + ["awh"], eps, avail, usrec)
    m_f5 = wf(D, C.F5, eps, avail, usrec)
    i6, b6, i5, b5, n2, _ = A4.paired_metrics(m_f6, m_f5)

    return dict(curve_awh=dict(improvement=round(ia, 2), brier=round(ba, 2)),
                curve_only=dict(improvement=round(ic, 2), brier=round(bc, 2)),
                dLL=round(dll, 2), dBrier=round(dbr, 2), n_parret=npair,
                folds_niveau_pct=round(lvl / len(folds) * 100 if folds else 0, 0),
                alle_folds_positive=bool(pos_all),
                persistens_pct=round(persist, 1), mde_pp=round(mde, 2),
                awh_koef_fuldfit=round(full_coef, 4), fortegn_neg_pct=round(sstab, 0),
                fortegn_folds=sfolds,
                aera_pre1990_dLL=round(d_pre, 2), aera_post1990_dLL=round(d_post, 2),
                sekundaer_f5=dict(dLL=round(i6 - i5, 2), dBrier=round(b6 - b5, 2), n=n2))

def main():
    snap = C.find_snapshot(sys.argv)
    meta = json.loads((snap / "meta.json").read_text(encoding="utf-8"))
    print(f"=== ablation8_awhman — {PROTOCOL} — snapshot {snap.name} ===")
    print("Sidste praeregistrerede skud. Spec forseglet af Sol (review runde B).\n")
    res = run(snap)
    det_ok = True
    if "--check" in sys.argv:
        det_ok = (res == run(snap))
        print("G1 DETERMINISME: " + ("OK" if det_ok else "FEJL"))

    print(f"\ncurve+awh:  +{res['curve_awh']['improvement']:.1f}% LL / +{res['curve_awh']['brier']:.1f}% Brier")
    print(f"curve-only: +{res['curve_only']['improvement']:.1f}% LL / +{res['curve_only']['brier']:.1f}% Brier   (parret, n={res['n_parret']})")
    print(f"parret forskel: dLL={res['dLL']:+.2f}pp  dBrier={res['dBrier']:+.2f}pp  (MDE {res['mde_pp']:.1f}pp)")
    print(f"LOEO: {res['folds_niveau_pct']:.0f}% paa niveau; alle positive: {res['alle_folds_positive']}")
    print(f"awh-koefficient: {res['awh_koef_fuldfit']:+.4f} (forventet negativ); "
          f"negativ i {res['fortegn_neg_pct']:.0f}% af {res['fortegn_folds']} LOEO-refits")
    print(f"aera-split (diagnostik): pre-1990 {res['aera_pre1990_dLL']:+.2f}pp | post-1990 {res['aera_post1990_dLL']:+.2f}pp")
    print(f"persistens: {res['persistens_pct']:.1f}%")
    print(f"sekundaer (F5+awh vs F5, diagnostik): dLL={res['sekundaer_f5']['dLL']:+.2f}pp "
          f"dBrier={res['sekundaer_f5']['dBrier']:+.2f}pp")

    A1 = res["dLL"] >= 2.0 and res["dBrier"] >= 2.0
    A2g = res["folds_niveau_pct"] >= 80 and res["alle_folds_positive"]
    A3 = res["awh_koef_fuldfit"] < 0 and res["fortegn_neg_pct"] >= 80
    print("\nGATES (trin 4's ratificerede, forhaandsregistreret):")
    for navn, ok in [("G1 determinisme", det_ok), ("A1 dLL>=2 & dBrier>=2", A1),
                     ("A2 LOEO 80% + alle pos", A2g), ("A3 negativt fortegn 80%", A3)]:
        print(f"  {navn:<26}{'BESTAAET' if ok else 'FEJLET'}")
    verdict = all([det_ok, A1, A2g, A3])
    flag = " [<60% PERSISTENS-FLAG]" if res["persistens_pct"] < 60 else ""
    print(f"\nSAMLET: {'OPTAGET' if verdict else 'TESTET, IKKE BESTAAET'}{flag}")
    print("INFORMATIONSSOEGNINGEN ER HERMED LUKKET (raadets grand review + Rasmus' mandat).")

    out = dict(protocol_version=PROTOCOL,
               created_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
               snapshot=snap.name, snapshot_sha256=meta["snapshot_sha256"],
               spec="awh(m)=((AWHMAN[m-1]/AWHMAN[m-7])^2-1)*100; forseglet af GPT-5.6 Sol, review runde B",
               gates=dict(G1=bool(det_ok), A1=bool(A1), A2=bool(A2g), A3=bool(A3),
                          OPTAGET=bool(verdict)), **res)
    (HERE / "ablation8_resultat.json").write_text(json.dumps(out, indent=1), encoding="utf-8")

    wfile = HERE / "weights.json"
    W = json.loads(wfile.read_text(encoding="utf-8"))
    W["benchmarks"]["curve_awh"] = dict(
        wf_improvement=res["curve_awh"]["improvement"], wf_brier=res["curve_awh"]["brier"],
        status=("OPTAGET — afventer promotion" if verdict else "testet, ikke bestaaet (sidste skud; soegning lukket)"))
    wfile.write_text(json.dumps(W, indent=1), encoding="utf-8")
    print("ablation8_resultat.json skrevet; benchmark-linje foejet til weights.json.")

if __name__ == "__main__":
    main()
