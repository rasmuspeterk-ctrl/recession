#!/usr/bin/env python3
"""
ablation9_nested.py — PRAEREGISTRERET nested lambda- og modelselektion (kode-review 2026-10-15, G1.1/G1.2).

PRAEREGISTRERING (committet og pushet FOER foerste koersel; scriptet naegter at koere ellers)
==========================================================================================
Hvorfor. Blueprintet (RAADETS_KONSENSUS §3/§6) kraever, at L2-straffen vaelges INDE i hvert
traeningsvindue, og at kun den nested sti kaldes walk-forward-skill. Koden har brugt en fast
lambda = 1 (arvet fra v4), og +27,1 %/+34,3 % er en max over to modeller paa den fulde sti.
Testen her er den nested sti, publiceret VED SIDEN AF. Den aendrer intet: hverken vaegte, P eller
den operationelle model. Et skift kraever en raadsbeslutning (§6) ved september-refit 2027.

Kontaminering, deklareret. Kode-reviewets eksplorative scratch-koersler (4 nested varianter) er
SET: curve-onlys skill faldt til 17-23 %, og curve-only vandt i alle varianter. Designet nedenfor
er EET af dem, fastlaast her, saa resultatet ikke kan vaelges efter udfald.

Design (fastlaast):
  panel     v5.0.1: snapshot = weights.json['snapshot'] (2026-09-19), R_score = refit_maaned (2026-09),
            samme origins som den publicerede walk-forward (A2.wf_nber-reglerne: gulv L = 18,
            censurering af annoncerede recessioner i traeningen, censurerede origins scores ikke,
            >= 60 traeningsraekker og >= 6 positive).
  modeller  curve-only (feature 'curve') og fuldmodellen (C.F5) paa identiske origins.
  lambda    grid {0.1, 0.3, 1, 3, 10, 30, 100} (L2 paa summen, som C.fit; intercept upenaliseret).
  indre CV  pr. origin: leave-one-episode-blok-out paa traeningssaettet (blok = forrige onset
            frem til onset k, som finalize6.boot_weights); standardisering fra hele traenings-
            vinduet; foldens log-loss paa de udeladte raekker; folds hvor traeningsdelen har < 3
            positive springes over. Lambda = argmin af middel-log-loss over folds; uafgjort -> stoerre lambda.
  selektion pr. origin vaelges den model (curve-only vs F5) med lavest indre-CV-log-loss ved dens egen
            valgte lambda; uafgjort -> curve-only.
  metrik    som C.metrics: log-loss-forbedring og Brier-skill mod den poolede basisrate over de
            scorede origins.
  output    ablation9_resultat.json: fast lambda=1 (skal reproducere +27,05 % / F5 +23,16 %), nested-
            lambda curve-only, nested-lambda F5, nested selektionssti, andel origins der vaelger hver
            model (samlet og fra 2000), lambda-fordeling, og P ved kurve +1,11 under en endelig
            CV-valgt lambda paa hele det modne panel (kun til raadet — ikke operationel).

Forventning (skrevet foer koersel): nested-lambda curve-only mellem +17 % og +25 %; selektionsstiens
skill hoejst lig nested curve-only; curve-only vaelges i flertallet af origins fra 2000. Udfaldet
publiceres uanset hvad. Intet i driften aendres af resultatet.

Koer:  python ablation9_nested.py      (kraever at denne fil er committet uaendret og pushet til origin)
Kun stdlib + numpy.
"""
import json, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

import calibrate as C
import ablation2_nber as A2
import finalize6 as F6

HERE = Path(__file__).parent
L = A2.L_EMBARGO
GRID = [0.1, 0.3, 1.0, 3.0, 10.0, 30.0, 100.0]


def praeregistreret():
    """Haandhaev praeregistreringen: filen skal vaere committet uaendret og commit'en pushet."""
    def git(*a):
        return subprocess.run(["git", *a], cwd=HERE, capture_output=True, text=True).stdout.strip()
    if git("status", "--porcelain", "--", "ablation9_nested.py"):
        return False, "ablation9_nested.py har ucommittede aendringer"
    c = git("log", "-1", "--format=%H", "--", "ablation9_nested.py")
    if not c:
        return False, "ablation9_nested.py er ikke committet"
    if "origin/main" not in git("branch", "-r", "--contains", c):
        return False, f"praeregistrerings-commit {c[:10]} er ikke pushet til origin/main"
    return True, c[:10]


def ll(p, y):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return -(y * np.log(p) + (1 - y) * np.log(1 - p))


def blokke(qend, eps):
    return np.array([next((k for k, (o, _) in enumerate(eps) if o >= q), len(eps)) for q in qend])


def indre_cv(Z, y, grp, lam):
    tab = []
    for g in np.unique(grp):
        tr, te = grp != g, grp == g
        if y[tr].sum() < 3 or te.sum() == 0:
            continue
        w = C.fit(Z[tr], y[tr], l2=lam)
        tab.extend(ll(C.predict(w, Z[te]), y[te]))
    return float(np.mean(tab)) if tab else float("inf")


def vaelg_lambda(Z, y, grp):
    scores = [(indre_cv(Z, y, grp, lam), -lam, lam) for lam in GRID]
    best = min(scores)
    return best[2], best[0]


def wf(D_by, eps, avail, usrec, R_score):
    """Walk-forward over de publicerede origins; returnerer pr. origin P under alle varianter."""
    Dc = D_by["curve"]
    Y_final, win_onsets, in_rec_final = A2.nber_labels(Dc, eps, usrec)
    out = []
    for i in range(len(Dc["qend"])):
        if Dc["year"][i] < 1960 or Dc["qend"][i] + 12 + L > R_score:
            continue
        R = Dc["qend"][i]
        tr = []
        for j in range(i):
            if Dc["qend"][j] + 12 + L > R:
                continue
            ep = A2.episode_of(int(Dc["qend"][j]), eps)
            if ep and avail[ep[0]] <= R:
                continue
            tr.append(j)
        if len(tr) < 60:
            continue
        yR = np.array([1.0 if any(avail[o] <= R for o in win_onsets[j]) else 0.0 for j in tr])
        if yR.sum() < 6 or in_rec_final[i]:
            continue
        grp = blokke(Dc["qend"][tr], eps)
        rec = dict(y=int(Dc["year"][i]), q=int(Dc["qk"][i][1]), Y=float(Y_final[i]))
        for navn, D in D_by.items():
            X = D["F"][tr]
            mu, sd = X.mean(0), X.std(0, ddof=1); sd[sd == 0] = 1
            Z = (X - mu) / sd
            x = (D["F"][[i]] - mu) / sd
            rec[f"{navn}_fast"] = float(C.predict(C.fit(Z, yR, l2=1.0), x)[0])
            lam, cv = vaelg_lambda(Z, yR, grp)
            rec[f"{navn}_nested"] = float(C.predict(C.fit(Z, yR, l2=lam), x)[0])
            rec[f"{navn}_lambda"] = lam
            rec[f"{navn}_cv"] = cv
        rec["valgt"] = "curve" if rec["curve_cv"] <= rec["F5_cv"] else "F5"
        rec["sel"] = rec[f"{rec['valgt']}_nested"]
        out.append(rec)
    return out


def skill(recs, k):
    rows = [(r["y"], r["q"], r[k], r["Y"]) for r in recs]
    _, _, imp, br = C.metrics(rows)
    return dict(improvement=round(float(imp), 2), brier=round(float(br), 2))


def main():
    ok, ref = praeregistreret()
    if not ok and "--tving" not in sys.argv:
        sys.exit(f"FEJL: praeregistreringen er ikke haandhaevet ({ref}). Commit og push filen foer koersel.")
    W = json.loads((HERE / "weights.json").read_text(encoding="utf-8"))
    snap = C.RAW / W["snapshot"]
    R = A2.midx(int(W["refit_maaned"][:4]), int(W["refit_maaned"][5:7]))
    usrec = A2.load_usrec(snap); eps = A2.episodes_from_usrec(usrec)
    avail = A2.load_announcements(eps, usrec=usrec)
    Dc = A2.build_dataset(snap, ["curve"]); D5 = A2.build_dataset(snap, C.F5)
    if not A2.samme_origins(Dc, D5):
        sys.exit("FEJL: curve-only og F5 har ikke identiske origins paa dette panel — designet forudsaetter det.")
    recs = wf({"curve": Dc, "F5": D5}, eps, avail, usrec, R)
    res = {k: skill(recs, k) for k in ("curve_fast", "F5_fast", "curve_nested", "F5_nested", "sel")}
    fra2000 = [r for r in recs if r["y"] >= 2000]
    lam_fordeling = {m: {str(l): sum(1 for r in recs if r[f"{m}_lambda"] == l) for l in GRID} for m in ("curve", "F5")}
    # endelig CV-valgt lambda paa hele det modne panel (kun til raadet)
    elig, yR = A2.eligible_fit(Dc, eps, avail, usrec, R)
    X = Dc["F"][elig]; mu, sd = X.mean(0), X.std(0, ddof=1)
    Z = (X - mu) / sd; y = yR[elig]
    lam_slut, _ = vaelg_lambda(Z, y, blokke(Dc["qend"][elig], eps))
    w = C.fit(Z, y, l2=lam_slut)
    p111 = float(C.predict(w, (np.array([[1.11]]) - mu) / sd)[0])
    ud = dict(protocol="5.0-ablation9-nested (praeregistreret G1.1/G1.2)", praeregistrering=ref,
              created_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
              snapshot=snap.name, R_score=W["refit_maaned"], n_origins=len(recs), grid=GRID,
              skill=res,
              reproduktion_ok=bool(abs(res["curve_fast"]["improvement"] - W["op"]["wf_improvement"]) < 0.01),
              andel_valgt_curve=round(np.mean([r["valgt"] == "curve" for r in recs]), 3),
              andel_valgt_curve_fra_2000=round(np.mean([r["valgt"] == "curve" for r in fra2000]), 3),
              lambda_fordeling=lam_fordeling,
              endelig_cv_lambda=lam_slut, p_ved_kurve_111_endelig_lambda=round(p111, 4),
              p_ved_kurve_111_drift=round(F6.p_af(dict(features=["curve"], mu=W["op"]["mu"], sd=W["op"]["sd"], w=W["op"]["w"]), {"curve": 1.11}), 4),
              note="Publiceres ved siden af den faste lambda=1-sti. Aendrer hverken vaegte, P eller den operationelle model; til raadet foer september 2027.")
    (HERE / "ablation9_resultat.json").write_text(json.dumps(ud, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: v for k, v in ud.items() if k not in ("lambda_fordeling",)}, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
