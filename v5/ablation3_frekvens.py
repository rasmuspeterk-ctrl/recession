#!/usr/bin/env python3
"""
ablation3_frekvens.py — trin 3 i raadets byggeorden: frekvens-ablation.
Maanedlig direkte-12m vs kvartalsvis direkte-4q (trin 2-baselinen).
Label (NBER-onset, mekanisk regel, L=18), features, motor og scoring holdes
fast — KUN frekvensen aendres (S2).

FORHAANDSREGISTRERET GATE (blueprint Section 2 + Sol/Kimi/Gemma-forbehold,
fastlagt FOER koersel):
  G1  determinisme (SEED=42 for bootstrap; alt andet deterministisk)
  G2  maanedlig promoveres kun hvis dens KVARTALS-TYNDEDE walk-forward
      log-loss-forbedring >= kvartals-baselinens forbedring - 1,0pp.
      (Tyndingen fjerner overlaps-inflation; fuld maanedlig score printes ved
      siden af men indgaar ikke i gaten.)
  MDE printes ved gaten: 1,96 x bootstrap-SD af den parrede skill-forskel
  (episode-blokket, 1000 traek). Promovering formidles som TIMELINESS-
  beslutning under stoejgulvet — ikke som paavist aekvivalens.

Kun stdlib + numpy.  Koer:  python ablation3_frekvens.py [--check] [--promote]
"""
import json, sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

import calibrate as C
import ablation2_nber as A2

HERE = Path(__file__).parent
PROTOCOL = "5.0-trin3-maanedlig"
SEED = 42
GATE_MARGIN = 1.0   # pp
L = A2.L_EMBARGO    # 18 — uaendret fra trin 2 (S2: een aendring ad gangen)

def build_monthly_dataset(snap, Dq):
    """Maanedligt univers: alle 5 features non-nan OG maanedens kvartal ligger i
    det kvartalsvise D-univers (identisk kalenderspaend)."""
    shiller = C.read_shiller(snap)
    gs10 = C.read_fred(snap, "GS10")
    tb3ms = C.read_fred(snap, "TB3MS")
    keys, M = C.build_monthly(shiller, gs10, tb3ms)
    F = np.stack([M[f] for f in C.F5], axis=1)
    ok_q = set(Dq["qk"])
    rows = []
    for i, (y, m) in enumerate(keys):
        if np.any(np.isnan(F[i])):
            continue
        if (y, (m - 1) // 3 + 1) not in ok_q:
            continue
        rows.append(i)
    return dict(
        F=F[rows],
        midx=np.array([A2.midx(*keys[i]) for i in rows]),
        ym=[keys[i] for i in rows],
    )

def wf_monthly(Dm, eps, avail, usrec, start=1960):
    n = len(Dm["midx"])
    win_onsets, Y_final, in_rec = [], np.zeros(n), np.zeros(n, bool)
    for j in range(n):
        w_lo, w_hi = Dm["midx"][j] + 1, Dm["midx"][j] + 12
        wo = [o for o, _ in eps if w_lo <= o <= w_hi]
        win_onsets.append(wo)
        Y_final[j] = 1.0 if wo else 0.0
        in_rec[j] = usrec.get(int(Dm["midx"][j]), 0) == 1
    out = []
    for i in range(n):
        if Dm["ym"][i][0] < start:
            continue
        R = Dm["midx"][i]
        tr = []
        for j in range(i):
            if Dm["midx"][j] + 12 + L > R:
                continue
            ep = A2.episode_of(int(Dm["midx"][j]), eps)
            if ep and avail[ep[0]] <= R:
                continue
            tr.append(j)
        if len(tr) < 180:                        # = 60 kvartaler i maaneder
            continue
        yR = np.array([1.0 if any(avail[o] <= R for o in win_onsets[j]) else 0.0 for j in tr])
        if yR.sum() < 18:                        # = 6 kvartals-positiver
            continue
        X = Dm["F"][tr]
        mu, sd = X.mean(0), X.std(0, ddof=1)
        sd[sd == 0] = 1
        w = C.fit((X - mu) / sd, yR)
        if in_rec[i]:
            continue
        p = float(C.predict(w, (Dm["F"][[i]] - mu) / sd)[0])
        y, m = Dm["ym"][i]
        out.append((y, m, p, float(Y_final[i])))
    return out

def episode_group(y, eps):
    """Origin -> naermeste efterfoelgende onset (eller halegruppe) til blok-bootstrap."""
    i = A2.midx(y, 6)
    for k, (o, _) in enumerate(eps):
        if o >= i:
            return k
    return len(eps)

def mde_bootstrap(paired, eps, ndraw=1000):
    """Parret skill-forskel (maanedlig-tyndet minus kvartal) med episode-blok-
    bootstrap. Returnerer (mean_diff_pp, sd_pp, ci10, ci90)."""
    rng = np.random.default_rng(SEED)
    groups = {}
    for (y, q, pm, pq, yy) in paired:
        groups.setdefault(episode_group(y, eps), []).append((pm, pq, yy))
    gkeys = sorted(groups)
    def skill_diff(sample_groups):
        pm, pq, yy = [], [], []
        for g in sample_groups:
            for a, b, c in groups[g]:
                pm.append(a); pq.append(b); yy.append(c)
        pm, pq, yy = (np.clip(np.array(pm), 1e-6, 1 - 1e-6),
                      np.clip(np.array(pq), 1e-6, 1 - 1e-6), np.array(yy))
        b = yy.mean()
        if b in (0.0, 1.0):
            return None
        bl = -np.mean(yy * np.log(b) + (1 - yy) * np.log(1 - b))
        llm = -np.mean(yy * np.log(pm) + (1 - yy) * np.log(1 - pm))
        llq = -np.mean(yy * np.log(pq) + (1 - yy) * np.log(1 - pq))
        return ((1 - llm / bl) - (1 - llq / bl)) * 100
    point = skill_diff(gkeys)
    draws = []
    while len(draws) < ndraw:
        d = skill_diff(list(rng.choice(gkeys, size=len(gkeys), replace=True)))
        if d is not None:
            draws.append(d)
    draws = np.array(draws)
    return point, float(draws.std(ddof=1)), float(np.percentile(draws, 10)), float(np.percentile(draws, 90))

def run(snap):
    usrec = A2.load_usrec(snap)
    eps = A2.episodes_from_usrec(usrec)
    avail = A2.load_announcements(eps)
    Dq = A2.build_dataset(snap)

    res_q, _, _ = A2.wf_nber(Dq, eps, avail, usrec, L)
    _, _, imp_q, br_q = C.metrics(res_q)

    Dm = build_monthly_dataset(snap, Dq)
    res_m = wf_monthly(Dm, eps, avail, usrec)
    _, _, imp_m, br_m = C.metrics(res_m)

    thin = [(y, m, p, yy) for (y, m, p, yy) in res_m if m % 3 == 0]
    _, _, imp_t, br_t = C.metrics(thin)

    q_by_key = {(y, q): (p, yy) for (y, q, p, yy) in res_q}
    paired = []
    for (y, m, pm, yy) in thin:
        k = (y, m // 3)
        if k in q_by_key:
            pq, yq = q_by_key[k]
            if yq == yy:
                paired.append((y, m // 3, pm, pq, yy))
    diff, sd, lo, hi = mde_bootstrap(paired, eps)
    mde = 1.96 * sd

    return dict(
        kvartal=dict(improvement=round(imp_q, 2), brier=round(br_q, 2), n=len(res_q)),
        maanedlig_fuld=dict(improvement=round(imp_m, 2), brier=round(br_m, 2), n=len(res_m)),
        maanedlig_tyndet=dict(improvement=round(imp_t, 2), brier=round(br_t, 2), n=len(thin)),
        parrede_origins=len(paired),
        skill_diff_pp=round(diff, 2), diff_sd_pp=round(sd, 2),
        diff_ci10=round(lo, 2), diff_ci90=round(hi, 2), mde_pp=round(mde, 2),
    )

def main():
    snap = C.find_snapshot(sys.argv)
    meta = json.loads((snap / "meta.json").read_text(encoding="utf-8"))
    print(f"=== ablation3_frekvens — {PROTOCOL} — snapshot {snap.name} ===")
    res = run(snap)
    det_ok = True
    if "--check" in sys.argv:
        det_ok = (res == run(snap))
        print("G1 DETERMINISME: " + ("OK" if det_ok else "FEJL"))

    print(f"\n{'':30}{'log-loss-forb.':>15}{'Brier':>9}{'n':>7}")
    print(f"{'Kvartal 4q (trin 2-baseline)':<30}{res['kvartal']['improvement']:>14.1f}%"
          f"{res['kvartal']['brier']:>8.1f}%{res['kvartal']['n']:>7}")
    print(f"{'Maanedlig 12m, FULD':<30}{res['maanedlig_fuld']['improvement']:>14.1f}%"
          f"{res['maanedlig_fuld']['brier']:>8.1f}%{res['maanedlig_fuld']['n']:>7}")
    print(f"{'Maanedlig 12m, KVT-TYNDET':<30}{res['maanedlig_tyndet']['improvement']:>14.1f}%"
          f"{res['maanedlig_tyndet']['brier']:>8.1f}%{res['maanedlig_tyndet']['n']:>7}   <- gate-metrik")

    g_req = res["kvartal"]["improvement"] - GATE_MARGIN
    g2 = res["maanedlig_tyndet"]["improvement"] >= g_req
    print(f"\nParret forskel (tyndet minus kvartal, {res['parrede_origins']} origins): "
          f"{res['skill_diff_pp']:+.1f}pp  [10-90%: {res['diff_ci10']:+.1f} .. {res['diff_ci90']:+.1f}]")
    print(f"MDE (1,96 x bootstrap-SD, episode-blokket, seed={SEED}): {res['mde_pp']:.1f}pp")
    if res["mde_pp"] > abs(res["skill_diff_pp"]):
        print("  -> forskellen ligger UNDER stoejgulvet: gate-udfaldet er en TIMELINESS-")
        print("     beslutning under usikkerhed, ikke paavist aekvivalens (Kimi R4).")

    print("\nGATES (forhaandsregistreret):")
    print(f"  G1 determinisme   {'BESTAAET' if det_ok else 'FEJLET'}")
    print(f"  G2 tyndet >= kvartal-1pp   {'BESTAAET' if g2 else 'FEJLET'}  "
          f"({res['maanedlig_tyndet']['improvement']:.1f}% vs krav {g_req:.1f}%)")
    verdict = det_ok and g2
    print(f"\nSAMLET: {'PROMOVER maanedlig-12m til primaer' if verdict else 'TESTET, IKKE BESTAAET — kvartal forbliver primaer'}")

    out = dict(protocol_version=PROTOCOL,
               created_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
               snapshot=snap.name, snapshot_sha256=meta["snapshot_sha256"],
               gates=dict(G1=bool(det_ok), G2=bool(g2), promoveret=bool(verdict)),
               gate_krav_pp=round(g_req, 2), **res)
    (HERE / "ablation3_resultat.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print("ablation3_resultat.json skrevet.")

    if verdict and "--promote" in sys.argv:
        promote(snap, meta, res)

def promote(snap, meta, res):
    usrec = A2.load_usrec(snap)
    eps = A2.episodes_from_usrec(usrec)
    Dq = A2.build_dataset(snap)
    Dm = build_monthly_dataset(snap, Dq)
    n = len(Dm["midx"])
    Y, in_rec = np.zeros(n), np.zeros(n, bool)
    for j in range(n):
        w_lo, w_hi = Dm["midx"][j] + 1, Dm["midx"][j] + 12
        Y[j] = 1.0 if any(w_lo <= o <= w_hi for o, _ in eps) else 0.0
        in_rec[j] = usrec.get(int(Dm["midx"][j]), 0) == 1
    fit = ~in_rec
    X, y = Dm["F"][fit], Y[fit]
    mu, sd = X.mean(0), X.std(0, ddof=1)
    sd[sd == 0] = 1
    w = C.fit((X - mu) / sd, y)
    onsets = sorted({f"{o//12}-{o%12+1:02d}" for o, _ in eps
                     if Dm["midx"][0] <= o <= Dm["midx"][-1] + 12})
    old = HERE / "weights.json"
    if old.exists():
        (HERE / "weights_trin2_kvartal.json").write_text(old.read_text(encoding="utf-8"), encoding="utf-8")
    out = dict(protocol_version=PROTOCOL,
               created_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
               snapshot=snap.name, snapshot_sha256=meta["snapshot_sha256"],
               label="nber-onset", label_tekst="NBER-onset inden 12 maaneder",
               frekvens="maanedlig",
               n_obs=int(fit.sum()), n_episoder=len(onsets),
               base_rate=round(float(y.mean()), 4),
               features=C.F5,
               mu={f: round(float(m), 4) for f, m in zip(C.F5, mu)},
               sd={f: round(float(s), 4) for f, s in zip(C.F5, sd)},
               w=[round(float(x), 4) for x in w],
               wf_improvement=res["maanedlig_tyndet"]["improvement"],
               wf_brier=res["maanedlig_tyndet"]["brier"],
               wf_note="gate-metrik = kvartals-tyndet maanedlig wf; fuld maanedlig og MDE i ablation3_resultat.json")
    old.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print("PROMOVERET: weights.json er nu maanedlig-12m (kvartal gemt som weights_trin2_kvartal.json).")

if __name__ == "__main__":
    main()
