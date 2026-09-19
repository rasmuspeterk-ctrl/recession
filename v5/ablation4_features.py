#!/usr/bin/env python3
"""
ablation4_features.py — trin 4 i raadets byggeorden: feature-genforsvar,
laaste udfordrere og ACM-substitutionstesten. Label (NBER-onset, L=18) og
frekvens (kvartal) holdes fast fra trin 2-3.

FORHAANDSREGISTRERET (fastlagt FOER koersel — blueprint Section 4-5):

  UDFORDRERE (een chance hver; definitioner laast her):
    sahm_t      = ma3(UNRATE) - min(ma3(UNRATE) over j-12..j-1)   forventet fortegn +
    claims_mom  = 12m %-aendring i maanedsmiddel af ICSA           forventet fortegn +
    permits_yoy = 12m %-aendring i PERMIT                          forventet fortegn -

  OPTAGELSESGATE (alle betingelser, parret mod baseline paa identiske origins):
    A1  dLL >= +2,0pp forbedring OG dBrier >= +2,0pp
    A2  i >= 80% af LOEO-folds holder A1; OG dLL > 0 i ALLE folds (ingen reddende episode)
    A3  forventet koefficientfortegn i >= 80% af LOEO-refits
    Bootstrap-persistens (1000 episode-blok-traek, seed 42) printes for ALLE
    kandidater; < 60% flagges permanent. MDE printes ved hver kandidat.

  DEMOTION af incumbent (sekretaerens forhaandsregistrerede fortolkning af
  "ingen arvefred"): drop-one; demoteres KUN hvis dLL(drop) >= +1,0pp OG
  dBrier(drop) >= +1,0pp OG dLL(drop) > 0 i >= 80% af folds.

  ACM-SUBSTITUTION (Section 5, een forseglet test):
    curve_adj = (y10 - ACMTP10_NYFed) - tb3m, serie 1961-06+
    Fuld-sti paa identiske origins; hvor ACM-modellen ikke kan fitte/predikere
    scores traeningsbasisraten (straffen for manglende historik).
    Adoption iff dLL >= +0,5pp OG dLL > 0 i >= 80% af LOEO-folds.
    Miss < 0,5pp -> sekundaer trunkeret sammenligning (kun ACM-gyldige origins)
    printes som diagnostik; ingen adoption. Doemmes IKKE paa 2023.

  Multi-optagelse: stoerste dLL foerst; oevrige bestaaede faar EEN retest mod
  ny baseline; haard cap 6 features i alt.

Kun stdlib + numpy.  Koer:  python ablation4_features.py [--check] [--promote]
"""
import json, sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

import calibrate as C
import spine as SP
import ablation2_nber as A2

HERE = Path(__file__).parent
PROTOCOL = "5.0-trin4-features"
SEED = 42
L = A2.L_EMBARGO
KAND = {"sahm_t": +1, "claims_mom": +1, "permits_yoy": -1}

def ma3(a):
    out = np.full(len(a), np.nan)
    for i in range(2, len(a)):
        w = a[i - 2:i + 1]
        if not np.any(np.isnan(w)):
            out[i] = w.mean()
    return out

def sahm_transform(u):
    m = ma3(u)
    out = np.full(len(u), np.nan)
    for i in range(12, len(u)):
        w = m[i - 12:i]
        if not np.isnan(m[i]) and not np.any(np.isnan(w)):
            out[i] = m[i] - w.min()
    return out

def monthly_mean(weekly):
    """ERRATUM (RAADETS_V501 §5): denne funktion var en no-op, fordi C.read_fred allerede havde
    kollapset ugeserien til maanedens SIDSTE observation, saa hver gruppe havde eet element.
    Trin 4's claims_mom (-61,9pp, ablation4_resultat.json) blev derfor testet paa sidste uge i
    maaneden, ikke paa maanedsmidlen som headeren specificerer. Bevaret uaendret som dokumentation
    af fejlen; den korrekte aggregering er icsa_maanedsmiddel() nedenfor."""
    agg = {}
    for (y, mo), v in weekly.items():
        agg.setdefault((y, mo), []).append(v)
    return {k: float(np.mean(v)) for k, v in agg.items()}

def icsa_maanedsmiddel(snap):
    """Korrekt implementering af den praeregistrerede spec: maanedsmiddel af ALLE ugeobservationer."""
    import csv as _csv
    rows = []
    with (snap / "ICSA.csv").open(encoding="utf-8-sig") as fh:
        for row in _csv.DictReader(fh):
            d, v = list(row.values())[:2]
            rows.append((d, v))
    m = SP.monthly_mean(rows)
    return {(int(k[:4]), int(k[5:7])): v for k, v in m.items()}

SPINE_FILE = None        # saettes af --erratum: den trunkerede Yale-rygrad, saa kun claims_mom aendres

def read_acm(snap):
    import csv as _csv
    out = {}
    f = snap / "acm.csv"
    if not f.exists():
        return None
    for row in _csv.DictReader(f.open(encoding="utf-8-sig")):
        y, m = map(int, row["Date"].split("-"))
        out[(y, m)] = float(row["ACMTP10"])
    return out

def build(snap):
    """Kvartalsdata med incumbents + kandidater + curve_adj, samme univers som trin 2."""
    shiller = C.read_shiller(snap, SPINE_FILE)
    gs10 = C.read_fred(snap, "GS10")
    tb3ms = C.read_fred(snap, "TB3MS")
    gdp_g = C.read_fred(snap, "A191RL1Q225SBEA")
    unrate = C.read_fred(snap, "UNRATE")
    icsa_m = icsa_maanedsmiddel(snap)              # erratum §5: maanedsmiddel som spec'en siger
    permit = C.read_fred(snap, "PERMIT")
    acm = read_acm(snap)

    keys, M = C.build_monthly(shiller, gs10, tb3ms)
    def align(d):
        return np.array([d.get(k, np.nan) for k in keys]) if d else np.full(len(keys), np.nan)
    u = align(unrate); ic = align(icsa_m); pm = align(permit); tp = align(acm)
    M["sahm_t"] = sahm_transform(u)
    M["claims_mom"] = C.pct_change12(ic)
    M["permits_yoy"] = C.pct_change12(pm)
    M["curve_adj"] = (M["y10"] - tp) - M["tb3m"]

    qkeys, cols = C.to_quarterly(keys, M, gdp_g)
    rec_now, Y_tek = C.make_labels(cols)
    mask = ~np.isnan(Y_tek)
    for f in C.BASE10:
        mask &= ~np.isnan(cols[f])
    keep = [i for i in range(len(qkeys)) if mask[i]]
    D = dict(qk=[qkeys[i] for i in keep])
    D["qend"] = np.array([A2.qend_idx(y, q) for (y, q) in D["qk"]])
    D["year"] = np.array([y for (y, _) in D["qk"]])
    D["X"] = {f: cols[f][mask] for f in
              C.F5 + list(KAND) + ["curve_adj"]}
    return D

def wf(D, feats, eps, avail, usrec, pad_missing=False, start=1960):
    """Generel purget walk-forward. Returnerer {(y,q): (p,y_final)}."""
    n = len(D["qend"])
    F = np.stack([D["X"][f] for f in feats], axis=1)
    valid = ~np.any(np.isnan(F), axis=1)
    win, Yf, in_rec = [], np.zeros(n), np.zeros(n, bool)
    for j in range(n):
        lo, hi = D["qend"][j] + 1, D["qend"][j] + 12
        wo = [o for o, _ in eps if lo <= o <= hi]
        win.append(wo); Yf[j] = 1.0 if wo else 0.0
        in_rec[j] = usrec.get(int(D["qend"][j]), 0) == 1
    out = {}
    for i in range(n):
        if D["year"][i] < start or in_rec[i]:
            continue
        R = D["qend"][i]
        tr = [j for j in range(i)
              if valid[j] and D["qend"][j] + 12 + L <= R
              and not (A2.episode_of(int(D["qend"][j]), eps)
                       and avail[A2.episode_of(int(D["qend"][j]), eps)[0]] <= R)]
        yR = np.array([1.0 if any(avail[o] <= R for o in win[j]) else 0.0 for j in tr])
        fit_ok = len(tr) >= 60 and yR.sum() >= 6
        if fit_ok and valid[i]:
            X = F[np.array(tr)]
            mu, sd = X.mean(0), X.std(0, ddof=1)
            sd[sd == 0] = 1
            w = C.fit((X - mu) / sd, yR)
            p = float(C.predict(w, (F[[i]] - mu) / sd)[0])
        elif pad_missing and len(yR) >= 20:
            p = float(yR.mean())          # straf: uinformativ traeningsbasisrate
        else:
            continue
        out[(int(D["year"][i]), int(D["qk"][i][1]))] = (p, float(Yf[i]))
    return out

def paired_metrics(a, b):
    """Parret sammenligning paa faelles origins: (impA, brA, impB, brB, n, faelles-keys)."""
    ks = sorted(set(a) & set(b))
    def mm(m):
        rows = [(y, q, m[(y, q)][0], m[(y, q)][1]) for (y, q) in ks]
        _, _, imp, br = C.metrics(rows)
        return imp, br
    ia, ba = mm(a); ib, bb = mm(b)
    return ia, ba, ib, bb, len(ks), ks

def fold_keys(ks, eps):
    """LOEO-folds: onset -> de faelles origins hvis vindue indeholder den onset."""
    folds = {}
    for (y, q) in ks:
        qe = A2.qend_idx(y, q)
        for o, _ in eps:
            if qe + 1 <= o <= qe + 12:
                folds.setdefault(o, set()).add((y, q))
    return folds

def loeo_deltas(a, b, ks, eps):
    """Parret (dLL, dBrier) pr. fold, hvor foldens origins er FJERNET."""
    folds = fold_keys(ks, eps)
    out = []
    for o, drop in sorted(folds.items()):
        keep = [k for k in ks if k not in drop]
        if sum(a[k][1] for k in keep) == 0:
            continue
        def mm(m):
            rows = [(y, q, m[(y, q)][0], m[(y, q)][1]) for (y, q) in keep]
            _, _, imp, br = C.metrics(rows)
            return imp, br
        ia, ba = mm(a); ib, bb = mm(b)
        out.append((o, ia - ib, ba - bb))
    return out

def bootstrap_persist(a, b, ks, eps, ndraw=1000):
    rng = np.random.default_rng(SEED)
    groups = {}
    for k in ks:
        g = next((i for i, (o, _) in enumerate(eps) if o >= A2.qend_idx(*k)), len(eps))
        groups.setdefault(g, []).append(k)
    gk = sorted(groups)
    diffs = []
    while len(diffs) < ndraw:
        sample = [k for g in rng.choice(gk, size=len(gk), replace=True) for k in groups[g]]
        ys = np.array([a[k][1] for k in sample])
        if ys.mean() in (0.0, 1.0):
            continue
        pa = np.clip(np.array([a[k][0] for k in sample]), 1e-6, 1 - 1e-6)
        pb = np.clip(np.array([b[k][0] for k in sample]), 1e-6, 1 - 1e-6)
        bl = -np.mean(ys * np.log(ys.mean()) + (1 - ys) * np.log(1 - ys.mean()))
        la = -np.mean(ys * np.log(pa) + (1 - ys) * np.log(1 - pa))
        lb = -np.mean(ys * np.log(pb) + (1 - ys) * np.log(1 - pb))
        diffs.append(((1 - la / bl) - (1 - lb / bl)) * 100)
    d = np.array(diffs)
    return float((d > 0).mean()) * 100, float(d.std(ddof=1)) * 1.96

def sign_stability(D, feats, cand, eps, usrec, expected):
    """Kandidatens fortegn i fuld-fit + LOEO-refits (raekker i/ved episoden fjernes)."""
    F = np.stack([D["X"][f] for f in feats], axis=1)
    n = len(D["qend"])
    valid = ~np.any(np.isnan(F), axis=1)
    Yf = np.zeros(n); in_rec = np.zeros(n, bool)
    for j in range(n):
        lo, hi = D["qend"][j] + 1, D["qend"][j] + 12
        Yf[j] = 1.0 if any(lo <= o <= hi for o, _ in eps) else 0.0
        in_rec[j] = usrec.get(int(D["qend"][j]), 0) == 1
    base_rows = valid & ~in_rec
    ci = feats.index(cand) + 1
    def coef(rows):
        X = F[rows]; y = Yf[rows]
        mu, sd = X.mean(0), X.std(0, ddof=1); sd[sd == 0] = 1
        return C.fit((X - mu) / sd, y)[ci]
    onsets = [o for o, _ in eps if D["qend"][0] <= o <= D["qend"][-1] + 12]
    hits = 0; total = 0
    for o, tr_ in eps:
        if o not in onsets:
            continue
        drop = np.array([(D["qend"][j] + 1 <= o <= D["qend"][j] + 12) or
                         (o <= D["qend"][j] <= tr_) for j in range(n)])
        rows = base_rows & ~drop
        if rows.sum() < 80 or Yf[rows].sum() < 5:
            continue
        total += 1
        if np.sign(coef(rows)) == expected:
            hits += 1
    full_sign = np.sign(coef(base_rows))
    return full_sign, (hits / total * 100 if total else 0.0), total

def run(snap):
    usrec = A2.load_usrec(snap)
    eps = A2.episodes_from_usrec(usrec)
    avail = A2.load_announcements(eps)
    D = build(snap)
    base = wf(D, C.F5, eps, avail, usrec)
    res = dict(kandidater={}, incumbents={}, acm={})

    for cand, sgn in KAND.items():
        m = wf(D, C.F5 + [cand], eps, avail, usrec)
        ia, ba, ib, bb, npair, ks = paired_metrics(m, base)
        dll, dbr = ia - ib, ba - bb
        folds = loeo_deltas(m, base, ks, eps)
        ok_lvl = sum(1 for (_, a, b) in folds if a >= 2.0 and b >= 2.0)
        pos_all = all(a > 0 for (_, a, _) in folds)
        persist, mde = bootstrap_persist(m, base, ks, eps)
        fsign, sstab, sfolds = sign_stability(D, C.F5 + [cand], cand, eps, usrec, sgn)
        A1 = dll >= 2.0 and dbr >= 2.0
        A2g = (len(folds) > 0 and ok_lvl / len(folds) >= 0.8 and pos_all)
        A3 = (np.sign(fsign) == sgn) and sstab >= 80.0
        res["kandidater"][cand] = dict(
            dLL=round(dll, 2), dBrier=round(dbr, 2), n_parret=npair,
            egen_imp=round(ia, 2), baseline_imp=round(ib, 2),
            folds_niveau_pct=round(ok_lvl / len(folds) * 100 if folds else 0, 0),
            alle_folds_positive=bool(pos_all),
            persistens_pct=round(persist, 1), mde_pp=round(mde, 2),
            fortegn_fuldfit=int(fsign), fortegn_stab_pct=round(sstab, 0), fortegn_folds=sfolds,
            A1=bool(A1), A2=bool(A2g), A3=bool(A3), OPTAGET=bool(A1 and A2g and A3))

    for f in C.F5:
        rest = [x for x in C.F5 if x != f]
        m = wf(D, rest, eps, avail, usrec)
        ia, ba, ib, bb, npair, ks = paired_metrics(m, base)      # m = uden featuren
        dll, dbr = ia - ib, ba - bb                              # >0 => drop hjaelper
        folds = loeo_deltas(m, base, ks, eps)
        pos = sum(1 for (_, a, _) in folds if a > 0)
        demote = dll >= 1.0 and dbr >= 1.0 and folds and pos / len(folds) >= 0.8
        res["incumbents"][f] = dict(dLL_ved_drop=round(dll, 2), dBrier_ved_drop=round(dbr, 2),
                                    folds_pos_pct=round(pos / len(folds) * 100 if folds else 0, 0),
                                    DEMOTERET=bool(demote))

    if not np.all(np.isnan(D["X"]["curve_adj"])):
        feats_acm = ["curve_adj"] + [f for f in C.F5 if f != "curve"]
        m = wf(D, feats_acm, eps, avail, usrec, pad_missing=True)
        ia, ba, ib, bb, npair, ks = paired_metrics(m, base)
        dll = ia - ib
        folds = loeo_deltas(m, base, ks, eps)
        pos = sum(1 for (_, a, _) in folds if a > 0)
        adopt = dll >= 0.5 and folds and pos / len(folds) >= 0.8
        res["acm"] = dict(dLL_fuldsti=round(dll, 2), dBrier=round(ba - bb, 2), n_parret=npair,
                          folds_pos_pct=round(pos / len(folds) * 100 if folds else 0, 0),
                          ADOPTERET=bool(adopt))
        if not adopt and abs(dll) < 0.5:
            m2 = wf(D, feats_acm, eps, avail, usrec, pad_missing=False)
            ia2, ba2, ib2, bb2, npair2, _ = paired_metrics(m2, base)
            res["acm"]["sekundaer_trunkeret"] = dict(
                dLL=round(ia2 - ib2, 2), dBrier=round(ba2 - bb2, 2), n=npair2)
    else:
        res["acm"] = dict(ADOPTERET=False, note="ACM-data utilgaengelig")
    return res

def main():
    global SPINE_FILE
    erratum = "--erratum" in sys.argv
    if erratum:
        SPINE_FILE = "shiller_yale_2023-09.csv"      # trunkeret panel: samme origins som det publicerede resultat
    snap = C.find_snapshot(sys.argv)
    meta = json.loads((snap / "meta.json").read_text(encoding="utf-8"))
    print(f"=== ablation4_features — {PROTOCOL} — snapshot {snap.name}"
          f"{' — ERRATUM (RAADETS_V501 §5): korrigeret claims-aggregering paa det trunkerede panel' if erratum else ''} ===")
    res = run(snap)
    det_ok = True
    if "--check" in sys.argv:
        det_ok = (res == run(snap))
        print("DETERMINISME: " + ("OK" if det_ok else "FEJL"))

    print("\nUDFORDRERE (gate: dLL>=2 & dBrier>=2, folds>=80% paa niveau + alle positive, fortegn>=80%):")
    print(f"{'kandidat':<13}{'dLL':>7}{'dBrier':>8}{'n':>5}{'folds%':>8}{'allePos':>9}"
          f"{'persist%':>10}{'MDE':>6}{'fortegn%':>10}  gate")
    for k, v in res["kandidater"].items():
        flag = " [<60% PERSISTENS-FLAG]" if v["persistens_pct"] < 60 else ""
        print(f"{k:<13}{v['dLL']:>7.2f}{v['dBrier']:>8.2f}{v['n_parret']:>5}"
              f"{v['folds_niveau_pct']:>7.0f}%{str(v['alle_folds_positive']):>9}"
              f"{v['persistens_pct']:>9.1f}%{v['mde_pp']:>6.1f}{v['fortegn_stab_pct']:>9.0f}%  "
              + ("OPTAGET" if v["OPTAGET"] else "testet, ikke bestaaet") + flag)

    print("\nINCUMBENTS (demotion kun hvis drop giver dLL>=1 & dBrier>=1 & 80% folds):")
    for f, v in res["incumbents"].items():
        print(f"  {f:<12} drop-effekt dLL={v['dLL_ved_drop']:+.2f} dBrier={v['dBrier_ved_drop']:+.2f} "
              f"folds+={v['folds_pos_pct']:.0f}%  -> " + ("DEMOTERET" if v["DEMOTERET"] else "beholdes"))

    a = res["acm"]
    print(f"\nACM-SUBSTITUTION (adoption iff dLL>=+0,5 og folds>=80% positive):")
    if "dLL_fuldsti" in a:
        print(f"  fuld-sti dLL={a['dLL_fuldsti']:+.2f}pp dBrier={a['dBrier']:+.2f}pp "
              f"(n={a['n_parret']}, folds+={a['folds_pos_pct']:.0f}%)  -> "
              + ("ADOPTERET" if a["ADOPTERET"] else "testet, ikke bestaaet"))
        if "sekundaer_trunkeret" in a:
            s = a["sekundaer_trunkeret"]
            print(f"  sekundaer trunkeret (kun ACM-gyldige origins): dLL={s['dLL']:+.2f}pp "
                  f"dBrier={s['dBrier']:+.2f}pp (n={s['n']}) — diagnostik, aendrer ikke dommen")
    else:
        print(f"  {a.get('note','')}")

    admitted = [k for k, v in res["kandidater"].items() if v["OPTAGET"]]
    demoted = [f for f, v in res["incumbents"].items() if v["DEMOTERET"]]
    changed = bool(admitted or demoted or res["acm"].get("ADOPTERET"))
    print(f"\nSAMLET: optaget={admitted or 'ingen'}, demoteret={demoted or 'ingen'}, "
          f"ACM={'adopteret' if res['acm'].get('ADOPTERET') else 'nej'}"
          f" -> feature-saettet {'AENDRES' if changed else 'er UAENDRET: de 5 incumbents bestaar'}")

    out = dict(protocol_version=PROTOCOL + ("-erratum" if erratum else ""),
               created_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
               snapshot=snap.name, snapshot_sha256=meta["snapshot_sha256"],
               spine=SPINE_FILE or "spine.csv", determinisme=bool(det_ok), **res)
    if erratum:
        out["erratum"] = dict(hvad="claims_mom: monthly_mean var en no-op (read_fred kollapsede ICSA til sidste uge i maaneden)",
                              rettelse="icsa_maanedsmiddel(): maanedsmiddel af alle ugeobservationer, som spec'en siger",
                              panel="trunkeret (Yale-rygrad t.o.m. 2023-09) = de publicerede origins; kun claims_mom kan aendre sig",
                              publiceret_superseded="ablation4_resultat.json claims_mom dLL -61.9pp = superseded implementation result",
                              forfremmelse="ingen uanset udfald; soegningen er lukket")
        (HERE / "ablation4_erratum_resultat.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
        print("ablation4_erratum_resultat.json skrevet (det publicerede ablation4_resultat.json er uroert).")
    else:
        (HERE / "ablation4_resultat.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
        print("ablation4_resultat.json skrevet.")

if __name__ == "__main__":
    main()
