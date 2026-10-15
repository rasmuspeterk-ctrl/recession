#!/usr/bin/env python3
"""
nested_robusthed.py — EKSPLORATIV analyse af den nested lambda- og modelselektion (til raadets 2027-dagsorden).

STATUS: EKSPLORATIV. Erstatter IKKE det praeregistrerede ablation9_nested.py (G1.1/G1.2), hvis design og tal
staar fast (curve-only nested +18,3 %, F5 nested +7,3 %, selektionssti +8,5 %, F5 valgt i 100 % af origins fra
2000). Dette script AENDRER INTET I DRIFTEN: hverken weights.json, P, den operationelle model eller nogen anden
fil i repoet. Det laeser snapshot 2026-09-19 og scorer ved R = 2026-09 (v5.0.1-panelet, 198 origins) og skriver
kun v5/analyser/nested_robusthed_resultat.json. Tallene er fakta til raadet, ikke beslutninger.

Formaal (kode-review 2026-10-15, G1.1 'L2-straffen vaelges aldrig inde i traeningsvinduet' og G1.2 '+27,1 % er en
max over to modeller paa den fulde sti'; ablation9's resultat rejste spoergsmaalet: hvorfor foretraekker den indre
CV fuldmodellen F5 i alle origins fra 2000, naar F5 derefter klarer sig langt daarligere out of sample?):

  (1) ROBUSTHED af det nested-lambda curve-only-tal paa tvaers af indre-CV-designs: leave-one-episode-blok-out som
      ablation9 (reproduceres bit-identisk som kontrol), samme med 12-maaneders purge og fold-standardisering,
      expanding tidsserie-CV inde i vinduet (sidste 40 %/60 % scores fremad, purget), blokket k-fold (5/10
      sammenhaengende folds, purget) og alternative lambda-grids (fint, loft 10, loft 300). Intervallet rapporteres.
  (2) DIAGNOSE af hvorfor den indre CV foretraekker F5: pr. origin sammenlignes den indre CV-log-loss (curve mod F5)
      med den realiserede log-loss ved samme origin (naeste-origin-tab) og over de naeste 8 origins; korrelation og
      fortegnsenighed; aera-/blok-effekter; dekomponering af selektionsstiens tab pr. aera; 2022-24-fejlalarmen med
      F5's logit-bidrag pr. feature; cape_pct's trend og vaegt-sti; hvilke historiske blokke der baerer F5's indre
      CV-fordel ved udvalgte origins.
  (3) ALTERNATIVE SELEKTORER (hvad de ville have valgt og scoret): one-standard-error-regel for lambda (stoerste
      lambda inden for 1 SE af minimum, SE over episodeblokke), one-SE-regel for modelvalget (F5 kun hvis dens
      indre CV-tab er mere end 1 SE under curve-onlys; default curve-only), fast default curve-only medmindre F5
      slaar den med mere end gate-MDE (4,42 pp, trin 3-MDE fra ablation3_resultat.json) i indre CV-skill, en
      taerskel-sweep, samt en selektor paa realiseret, moden out-of-sample-historik (reviewets bp_modelsel).
      For hver regel: stiens skill, andel F5 valgt (samlet og fra 2000), antal skift og valget 'i dag' paa hele det
      modne panel ved R = 2026-09.

Design (fastlaast i koden, alle deterministiske; eneste tilfaeldighed er en episode-blok-bootstrap med SEED = 42):
  ydre sti   = ablation9's walk-forward (A2.wf_nber-reglerne: gulv L = 18, censurering af annoncerede recessioner,
               >= 60 traeningsraekker, >= 6 positive, censurerede origins scores ikke), identiske origins for
               curve-only og F5. Standardisering fra hele traeningsvinduet (som ablation9) medmindre designet siger
               'fold'. Lambda = argmin af det poolede middel-log-loss over de udeladte raekker; uafgjort -> stoerre
               lambda. Modelvalg (reference) = laveste indre CV-tab ved egen lambda; uafgjort -> curve-only.
  metrik     = C.metrics (log-loss-forbedring og Brier-skill mod den poolede basisrate over de scorede origins).
  aera-bidrag = (basis-tab - model-tab) summeret over aeraens origins, i pp af den poolede basislinjes samlede tab.

Koer:  cd v5 && python analyser/nested_robusthed.py        (kun stdlib + numpy; ~3-6 minutter)
Output: v5/analyser/nested_robusthed_resultat.json (eneste fil der skrives).
"""
import json, sys, time
from datetime import datetime, timezone
from pathlib import Path

sys.dont_write_bytecode = True                      # roer ikke v5/__pycache__
HERE = Path(__file__).resolve().parent
V5 = HERE.parent
sys.path.insert(0, str(V5))

import numpy as np
import calibrate as C
import ablation2_nber as A2
import ablation9_nested as A9

SNAPSHOT = "2026-09-19"
R_SCORE = (2026, 9)
SEED = 42
L = A2.L_EMBARGO
MDE_FALLBACK = 4.42
GRID_A9 = list(A9.GRID)                                            # [0.1, 0.3, 1, 3, 10, 30, 100]
GRID_FIN = [0.1, 0.2, 0.3, 0.5, 1.0, 2.0, 3.0, 5.0, 10.0, 20.0, 30.0, 50.0, 100.0]
GRID_LAV = [0.1, 0.3, 1.0, 3.0, 10.0]
GRID_HOEJ = [1.0, 3.0, 10.0, 30.0, 100.0, 300.0]
LAMBDA_FAST = 1.0
TAERSKLER_PP = [0.0, 1.0, 2.0, 3.0, 4.42, 6.0, 8.0, 10.0]
FEJLALARM = ((2021, 4), (2024, 1))                                 # 2022-24-fejlalarmens origins (reviewets blok)

# Indre-CV-designs: folds = blok (leave-one-episode-blok-out) | blok_purge | expanding | kfold;
# std = vindue (mu/sd fra hele traeningsvinduet, som ablation9) | fold (mu/sd fra foldens traeningsdel).
DESIGNS = {
    "a9_blok":            dict(folds="blok", std="vindue", grid=GRID_A9,
                               tekst="ablation9's design: leave-one-episode-blok-out, ingen purge, vindue-std (kontrol)"),
    "blok_foldstd":       dict(folds="blok", std="fold", grid=GRID_A9,
                               tekst="som a9_blok, men standardisering fra foldens traeningsdel"),
    "blok_purge":         dict(folds="blok_purge", std="fold", grid=GRID_A9,
                               tekst="leave-one-episode-blok-out med 12 mdr purge omkring blokken, fold-std (reviewets bp_nested 'blok')"),
    "expanding40":        dict(folds="expanding", andel=0.4, std="fold", grid=GRID_A9,
                               tekst="expanding tidsserie-CV: de sidste 40 % af vinduet scores fremad, purget (reviewets 'sidst')"),
    "expanding60":        dict(folds="expanding", andel=0.6, std="fold", grid=GRID_A9,
                               tekst="expanding tidsserie-CV: de sidste 60 % af vinduet scores fremad, purget"),
    "kfold5_purge":       dict(folds="kfold", k=5, std="fold", grid=GRID_A9,
                               tekst="blokket 5-fold (sammenhaengende tidsblokke) med 12 mdr purge, fold-std"),
    "kfold10_purge":      dict(folds="kfold", k=10, std="fold", grid=GRID_A9,
                               tekst="blokket 10-fold (sammenhaengende tidsblokke) med 12 mdr purge, fold-std"),
    "a9_blok_grid_fin":   dict(folds="blok", std="vindue", grid=GRID_FIN,
                               tekst="a9_blok med fint grid (13 punkter 0,1-100)"),
    "a9_blok_grid_lav":   dict(folds="blok", std="vindue", grid=GRID_LAV,
                               tekst="a9_blok med grid-loft 10 (reviewets g10-variant)"),
    "a9_blok_grid_hoej":  dict(folds="blok", std="vindue", grid=GRID_HOEJ,
                               tekst="a9_blok med grid 1-300 (intet lille lambda, loft 300)"),
    "blok_purge_grid_fin": dict(folds="blok_purge", std="fold", grid=GRID_FIN,
                                tekst="blok_purge med fint grid"),
}
REFERENCE_DESIGN = "a9_blok"


# ------------------------------------------------------------------ hjaelpere
def ll_rows(p, y):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return -(y * np.log(p) + (1 - y) * np.log(1 - p))


def ll1(p, y):
    return float(ll_rows(np.array([p]), np.array([y]))[0])


def blokke(qend, eps):
    """Raekke -> episodeblok (forrige onset frem til onset k), som ablation9/finalize6.boot_weights."""
    return A9.blokke(qend, eps)


def std_af(X):
    mu, sd = X.mean(0), X.std(0, ddof=1)
    sd = np.where(sd == 0, 1.0, sd)
    return mu, sd


def rund(x, n=4):
    if x is None:
        return None
    x = float(x)
    return None if np.isnan(x) else round(x, n)


def skill_af(rows):
    """rows = [(y, q, p, Y)] -> C.metrics som dict."""
    if not rows:
        return dict(n=0)
    ll, bl, imp, br = C.metrics(rows)
    return dict(n=len(rows), improvement=rund(imp, 2), brier=rund(br, 2), logloss=rund(ll), baseline=rund(bl))


def valg_oversigt(valg, aar):
    """Andel F5 valgt (samlet, fra 2000) og antal skift langs stien."""
    valg = list(valg)
    f5 = [v == "F5" for v in valg]
    fra = [v == "F5" for v, y in zip(valg, aar) if y >= 2000]
    skift = sum(1 for a, b in zip(valg[:-1], valg[1:]) if a != b)
    return dict(andel_F5=rund(np.mean(f5), 3), andel_F5_fra_2000=rund(np.mean(fra), 3) if fra else None,
                n_F5=int(sum(f5)), skift=skift)


# -------------------------------------------------------------- ydre sti
def traeningssaet(D, eps, avail, usrec, R_score):
    """ablation9's origins med traeningsraekker og realtidslabels (kun afhaengig af qend/labels, ens for begge modeller)."""
    Y_final, win_onsets, in_rec_final = A2.nber_labels(D, eps, usrec)
    ud = []
    for i in range(len(D["qend"])):
        if D["year"][i] < 1960 or D["qend"][i] + 12 + L > R_score:
            continue
        R = D["qend"][i]
        tr = []
        for j in range(i):
            if D["qend"][j] + 12 + L > R:
                continue
            ep = A2.episode_of(int(D["qend"][j]), eps)
            if ep and avail[ep[0]] <= R:
                continue
            tr.append(j)
        if len(tr) < 60:
            continue
        yR = np.array([1.0 if any(avail[o] <= R for o in win_onsets[j]) else 0.0 for j in tr])
        if yR.sum() < 6 or in_rec_final[i]:
            continue
        ud.append(dict(i=i, tr=np.array(tr), y=yR, aar=int(D["year"][i]), q=int(D["qk"][i][1]), Y=float(Y_final[i]),
                       qend=D["qend"][tr], blok=blokke(D["qend"][tr], eps)))
    return ud


# -------------------------------------------------------------- indre CV
def folds_af(design, y, qend, blok):
    """Liste af (traen-maske, test-maske) for designet. Folds afhaenger kun af tid/labels, ikke af features."""
    n = len(y)
    ud = []
    f = design["folds"]
    if f in ("blok", "blok_purge"):
        for g in np.unique(blok):
            te = blok == g
            if f == "blok":
                trn = ~te
                if y[trn].sum() < 3 or te.sum() == 0:
                    continue
            else:
                lo, hi = qend[te].min(), qend[te].max()
                trn = (~te) & ((qend + 12 <= lo) | (qend > hi + 12))
                if y[trn].sum() < 3 or trn.sum() < 30:
                    continue
            ud.append((trn, te))
    elif f == "expanding":
        start = int(round((1 - design["andel"]) * n))
        for t in range(start, n):
            trn = qend + 12 <= qend[t]
            if trn.sum() < 30 or y[trn].sum() < 3:
                continue
            te = np.zeros(n, bool); te[t] = True
            ud.append((trn, te))
    elif f == "kfold":
        k = design["k"]
        graenser = np.linspace(0, n, k + 1).astype(int)
        for a, b in zip(graenser[:-1], graenser[1:]):
            if b <= a:
                continue
            te = np.zeros(n, bool); te[a:b] = True
            lo, hi = qend[te].min(), qend[te].max()
            trn = (~te) & ((qend + 12 <= lo) | (qend > hi + 12))
            if y[trn].sum() < 3 or trn.sum() < 30:
                continue
            ud.append((trn, te))
    return ud


def indre_cv(design, X, y, qend, blok, mu_v, sd_v):
    """Per-raekke log-loss for hvert lambda paa de udeladte raekker.
    -> dict(grid, tab (n_grid x n_rows), rows_y, rows_blok, n_folds) eller None hvis ingen fold er brugbar."""
    grid = design["grid"]
    folds = folds_af(design, y, qend, blok)
    if not folds:
        return None
    Zv = (X - mu_v) / sd_v
    tab, ry, rb = [[] for _ in grid], [], []
    for trn, te in folds:
        if design["std"] == "fold":
            mu, sd = std_af(X[trn])
            Ztr, Zte = (X[trn] - mu) / sd, (X[te] - mu) / sd
        else:
            Ztr, Zte = Zv[trn], Zv[te]
        for k, lam in enumerate(grid):
            w = C.fit(Ztr, y[trn], l2=lam)
            tab[k].extend(ll_rows(C.predict(w, Zte), y[te]).tolist())
        ry.extend(y[te].tolist()); rb.extend(blok[te].tolist())
    return dict(grid=grid, tab=np.array(tab), rows_y=np.array(ry), rows_blok=np.array(rb), n_folds=len(folds))


def cv_stat(cv, base_rate):
    """Lambda-valg (pooled argmin, uafgjort -> stoerre lambda), 1-SE-lambda (blokmiddel), blokmiddel-tab ved
    valgt lambda, indre basis-tab (vinduets basisrate paa de udeladte raekker) og indre CV-skill."""
    grid, tab = cv["grid"], cv["tab"]
    pooled = tab.mean(1)
    k_min = max(range(len(grid)), key=lambda k: (-pooled[k], grid[k]))
    bl = np.unique(cv["rows_blok"])
    blokmid = np.array([[tab[k][cv["rows_blok"] == b].mean() for b in bl] for k in range(len(grid))])  # grid x blok
    fm = blokmid.mean(1)
    k_fm = max(range(len(grid)), key=lambda k: (-fm[k], grid[k]))
    se = float(blokmid[k_fm].std(ddof=1) / np.sqrt(len(bl))) if len(bl) > 1 else 0.0
    k_1se = max(k for k in range(len(grid)) if fm[k] <= fm[k_fm] + se)       # stoerste lambda inden for 1 SE
    base_tab = ll_rows(np.full(len(cv["rows_y"]), base_rate), cv["rows_y"])
    cv_base = float(base_tab.mean())
    base_blok = np.array([base_tab[cv["rows_blok"] == b].mean() for b in bl])
    return dict(lam=grid[k_min], cv=float(pooled[k_min]), lam_1se=grid[k_1se], cv_1se=float(pooled[k_1se]),
                se_1se=se, blokmid=blokmid[k_min], blokmid_1se=blokmid[k_1se], blok_ids=bl, base_blok=base_blok,
                blok_n=np.array([int((cv["rows_blok"] == b).sum()) for b in bl]),
                cv_base=cv_base, skill_cv=(1 - pooled[k_min] / cv_base) * 100,
                skill_cv_1se=(1 - pooled[k_1se] / cv_base) * 100,
                pooled=pooled.tolist(), n_folds=cv["n_folds"], n_rows=int(tab.shape[1]))


def koer_design(navn, design, saet, D_by, gem_vaegte=False):
    """Walk-forward under eet indre-CV-design for alle modeller. -> liste af per-origin-poster."""
    recs = []
    for s in saet:
        rec = dict(aar=s["aar"], q=s["q"], Y=s["Y"], base_tr=float(s["y"].mean()), n_tr=int(len(s["y"])),
                   n_blok=int(len(np.unique(s["blok"]))))
        for m, D in D_by.items():
            X = D["F"][s["tr"]]
            mu, sd = std_af(X)
            Z, x = (X - mu) / sd, (D["F"][[s["i"]]] - mu) / sd
            rec[f"{m}_fast"] = float(C.predict(C.fit(Z, s["y"], l2=LAMBDA_FAST), x)[0])
            cv = indre_cv(design, X, s["y"], s["qend"], s["blok"], mu, sd)
            if cv is None:                                        # ingen brugbar fold: fald tilbage til lambda = 1
                st = dict(lam=LAMBDA_FAST, cv=float("nan"), lam_1se=LAMBDA_FAST, cv_1se=float("nan"), se_1se=0.0,
                          blokmid=None, blokmid_1se=None, blok_ids=None, base_blok=None, blok_n=None, cv_base=float("nan"),
                          skill_cv=float("nan"), skill_cv_1se=float("nan"), pooled=None, n_folds=0, n_rows=0)
                rec[f"{m}_fallback"] = True
            else:
                st = cv_stat(cv, float(s["y"].mean()))
            w = C.fit(Z, s["y"], l2=st["lam"])
            rec[f"{m}_nested"] = float(C.predict(w, x)[0])
            rec[f"{m}_1se"] = float(C.predict(C.fit(Z, s["y"], l2=st["lam_1se"]), x)[0])
            rec[f"{m}_st"] = st
            if gem_vaegte:
                rec[f"{m}_w"] = w.tolist(); rec[f"{m}_z"] = x[0].tolist()
        rec["valgt"] = "curve" if rec["curve_st"]["cv"] <= rec["F5_st"]["cv"] else "F5"
        rec["sel"] = rec[f"{rec['valgt']}_nested"]
        recs.append(rec)
    return recs


# --------------------------------------------------------- aggregater
def sti(recs, k):
    return [(r["aar"], r["q"], r[k], r["Y"]) for r in recs]


def lambda_fordeling(recs, m, grid, key="lam"):
    return {str(l): int(sum(1 for r in recs if r[f"{m}_st"][key] == l)) for l in grid}


def aera_af(r):
    if (r["aar"], r["q"]) >= FEJLALARM[0]:
        return "2021Q4-2024Q1"
    if r["aar"] >= 2020:
        return "2020Q2-2021Q3"
    return f"{r['aar'] // 10 * 10}s"


AERAER = ["1960s", "1970s", "1980s", "1990s", "2000s", "2010s", "2020Q2-2021Q3", "2021Q4-2024Q1"]


def aera_bidrag(recs, keys):
    """Skill-bidrag pr. aera i pp af den poolede basislinjes samlede tab (summerer til stiens improvement)."""
    ys = np.array([r["Y"] for r in recs]); b = ys.mean()
    L0 = float(ll_rows(np.full(len(ys), b), ys).sum())
    ud = {}
    for a in AERAER:
        rs = [r for r in recs if aera_af(r) == a]
        if not rs:
            continue
        b0 = sum(ll1(b, r["Y"]) for r in rs)
        row = dict(n=len(rs), n_pos=int(sum(r["Y"] for r in rs)))
        for k in keys:
            row[k] = rund(100 * (b0 - sum(ll1(r[k], r["Y"]) for r in rs)) / L0, 2)
        ud[a] = row
    return ud


def mde_parret(recs, k1, k2, eps, ndraw=1000):
    """Episode-blok-bootstrap af den parrede skill-forskel (k2 minus k1), som ablation3.mde_bootstrap (SEED = 42).
    Blok = origin -> naermeste efterfoelgende onset. -> (punkt, sd, ci10, ci90, 1,96 x sd)."""
    rng = np.random.default_rng(SEED)
    grp = {}
    for r in recs:
        g = next((k for k, (o, _) in enumerate(eps) if o >= A2.midx(r["aar"], 6)), len(eps))
        grp.setdefault(g, []).append((r[k1], r[k2], r["Y"]))
    gk = sorted(grp)

    def diff(gs):
        p1, p2, yy = [], [], []
        for g in gs:
            for a, b, c in grp[g]:
                p1.append(a); p2.append(b); yy.append(c)
        p1, p2, yy = np.array(p1), np.array(p2), np.array(yy)
        bb = yy.mean()
        if bb in (0.0, 1.0):
            return None
        bl = ll_rows(np.full(len(yy), bb), yy).mean()
        return ((1 - ll_rows(p2, yy).mean() / bl) - (1 - ll_rows(p1, yy).mean() / bl)) * 100

    punkt = diff(gk)
    draws = []
    while len(draws) < ndraw:
        d = diff(list(rng.choice(gk, size=len(gk), replace=True)))
        if d is not None:
            draws.append(d)
    draws = np.array(draws)
    sd = float(draws.std(ddof=1))
    return dict(punkt_pp=rund(punkt, 2), sd_pp=rund(sd, 2), ci10=rund(np.percentile(draws, 10), 2),
                ci90=rund(np.percentile(draws, 90), 2), mde_1_96_sd_pp=rund(1.96 * sd, 2), n_blokke=len(gk))


# ------------------------------------------------------------ del 3: selektorer
def selektor_sti(recs, regel, mde=MDE_FALLBACK, taerskel=None):
    """Anvender en selektionsregel pr. origin paa et designs poster. -> (rows, valg)."""
    rows, valg = [], []
    for r in recs:
        c, f = r["curve_st"], r["F5_st"]
        if regel == "argmin":                                   # ablation9's reference
            v = "curve" if c["cv"] <= f["cv"] else "F5"
            p = r[f"{v}_nested"]
        elif regel == "mde":                                    # default curve-only; F5 kun hvis indre CV-skill-forskel > taerskel
            t = mde if taerskel is None else taerskel
            d = f["skill_cv"] - c["skill_cv"]
            v = "F5" if (not np.isnan(d) and d > t) else "curve"
            p = r[f"{v}_nested"]
        elif regel == "1se_model":                              # default curve-only; F5 kun hvis > 1 SE (parret over blokke) bedre
            v = "curve"
            if c["blokmid"] is not None and f["blokmid"] is not None:
                d = c["blokmid"] - f["blokmid"]                 # positiv = F5 bedre i blokken
                se = float(d.std(ddof=1) / np.sqrt(len(d))) if len(d) > 1 else float("inf")
                v = "F5" if d.mean() > se else "curve"
            p = r[f"{v}_nested"]
        elif regel == "1se_lambda_argmin":                      # begge modeller ved 1-SE-lambda; argmin paa cv_1se
            v = "curve" if c["cv_1se"] <= f["cv_1se"] else "F5"
            p = r[f"{v}_1se"]
        elif regel == "1se_lambda_mde":                         # 1-SE-lambda + MDE-gated modelvalg
            d = f["skill_cv_1se"] - c["skill_cv_1se"]
            v = "F5" if (not np.isnan(d) and d > mde) else "curve"
            p = r[f"{v}_1se"]
        else:
            raise ValueError(regel)
        rows.append((r["aar"], r["q"], p, r["Y"])); valg.append(v)
    return rows, valg


def realiseret_historik(recs, eps, avail, default, min_hist, key="nested"):
    """Reviewets bp_modelsel/sk_g12: vaelg den model med lavest kumuleret realiseret out-of-sample-log-loss paa
    origins hvis label var moden (vinduets slut + 18 mdr <= origin) og som annonceret pr. origin."""
    def qend(r): return A2.qend_idx(r["aar"], r["q"])
    def win(r): return [o for o, _ in eps if qend(r) + 1 <= o <= qend(r) + 12]
    rows, valg = [], []
    for r in recs:
        Rk = qend(r)
        hist = [h for h in recs if qend(h) + 12 + L <= Rk]
        lc = l5 = 0.0; npos = 0
        for h in hist:
            yk = 1.0 if any(avail[o] <= Rk for o in win(h)) else 0.0
            npos += yk; lc += ll1(h[f"curve_{key}"], yk); l5 += ll1(h[f"F5_{key}"], yk)
        v = default if (len(hist) < min_hist or npos == 0) else ("curve" if lc <= l5 else "F5")
        rows.append((r["aar"], r["q"], r[f"{v}_{key}"], r["Y"])); valg.append(v)
    return rows, valg


# ------------------------------------------------------------ del 2: diagnose
def redningsblok(recs, eps, mde):
    """Hvilken historisk blok baerer F5's indre CV-fordel? Pr. origin: blokbidrag = (curve - F5 blokmiddel) x antal
    raekker i blokken (summen / n = den poolede indre forskel). Stoerste positive bidragyder, og om F5 stadig ville
    vinde den indre CV uden den — blueprintets 'no single rescuing episode' (§4) brugt som diagnostik paa selektoren.
    Fordelen omregnes ogsaa til indre CV-skill-point (pp af vinduets basis-tab) og holdes mod gate-MDE."""
    from collections import Counter

    def navn(g):
        return f"{eps[int(g)][0] // 12}-{eps[int(g)][0] % 12 + 1:02d}" if int(g) < len(eps) else "hale"

    rows = []
    for r in recs:
        c, f = r["curve_st"], r["F5_st"]
        if c["blokmid"] is None or f["blokmid"] is None:
            continue
        bidrag = (c["blokmid"] - f["blokmid"]) * c["blok_n"]
        total = float(bidrag.sum()); k = int(np.argmax(bidrag))
        skala = 100 / (c["n_rows"] * c["cv_base"])                     # nats -> pp af vinduets basis-tab
        rows.append(dict(aar=r["aar"], q=r["q"], valgt=r["valgt"], total=total, stoerste=navn(c["blok_ids"][k]),
                         stoerste_nats=float(bidrag[k]), uden=total - float(bidrag[k]),
                         total_pp=total * skala, uden_pp=(total - float(bidrag[k])) * skala,
                         andel=float(bidrag[k] / total) if total > 0 else None))
    f5 = [x for x in rows if x["valgt"] == "F5"]
    f5_2000 = [x for x in f5 if x["aar"] >= 2000]
    return dict(
        definition="blokbidrag til F5's indre fordel = (curve_blokmiddel - F5_blokmiddel) x antal raekker i blokken (nats); "
                   "summen over blokke / n_raekker = den poolede indre forskel curve_cv - F5_cv; "
                   "_pp = samme i indre CV-skill-point (100 x nats / (n_raekker x basis-tab)), sammenlignelig med gate-MDE",
        mde_pp=mde,
        n_origins_F5_valgt=len(f5), n_origins_F5_valgt_fra_2000=len(f5_2000),
        middel_indre_skill_fordel_F5_fra_2000_pp=rund(np.mean([x["total_pp"] for x in f5_2000]), 2) if f5_2000 else None,
        middel_indre_skill_fordel_F5_uden_stoerste_blok_fra_2000_pp=rund(np.mean([x["uden_pp"] for x in f5_2000]), 2) if f5_2000 else None,
        andel_fra_2000_hvor_F5_fordel_over_mde=rund(np.mean([x["total_pp"] > mde for x in f5_2000]), 3) if f5_2000 else None,
        andel_fra_2000_hvor_F5_fordel_uden_stoerste_blok_over_mde=rund(np.mean([x["uden_pp"] > mde for x in f5_2000]), 3) if f5_2000 else None,
        stoerste_bidragyder_blandt_F5_valgte=dict(Counter(x["stoerste"] for x in f5).most_common()),
        stoerste_bidragyder_fra_2000=dict(Counter(x["stoerste"] for x in f5_2000).most_common()),
        andel_F5_valgte_hvor_curve_vinder_uden_stoerste_blok=rund(np.mean([x["uden"] <= 0 for x in f5]), 3) if f5 else None,
        andel_fra_2000_hvor_curve_vinder_uden_stoerste_blok=rund(np.mean([x["uden"] <= 0 for x in f5_2000]), 3) if f5_2000 else None,
        middel_andel_af_F5_fordel_fra_stoerste_blok_fra_2000=rund(np.mean([x["andel"] for x in f5_2000 if x["andel"] is not None]), 3) if f5_2000 else None,
        per_origin_fra_2000=[dict(o=f"{x['aar']}Q{x['q']}", total_nats=rund(x["total"], 3), stoerste=x["stoerste"],
                                  stoerste_nats=rund(x["stoerste_nats"], 3), uden_stoerste_nats=rund(x["uden"], 3),
                                  total_pp=rund(x["total_pp"], 2), uden_stoerste_pp=rund(x["uden_pp"], 2)) for x in f5_2000])


def diagnose(recs, eps, D5, feats, mde):
    aar = np.array([r["aar"] for r in recs])
    qk_idx = {qk: i for i, qk in enumerate(D5["qk"])}
    cv_c = np.array([r["curve_st"]["cv"] for r in recs]); cv_5 = np.array([r["F5_st"]["cv"] for r in recs])
    ll_c = np.array([ll1(r["curve_nested"], r["Y"]) for r in recs]); ll_5 = np.array([ll1(r["F5_nested"], r["Y"]) for r in recs])
    indre = cv_c - cv_5                 # positiv = F5 bedre i indre CV (nats/raekke)
    real = ll_c - ll_5                  # positiv = F5 bedre realiseret ved origin (nats)
    ok = ~np.isnan(indre)
    # realiseret over de naeste 8 origins (2 aar) fra og med origin
    real8 = np.array([np.mean(real[i:i + 8]) for i in range(len(real))])

    def korr(a, b):
        a, b = np.asarray(a, float), np.asarray(b, float)
        if len(a) < 3 or a.std() == 0 or b.std() == 0:
            return dict(pearson=None, spearman=None, n=int(len(a)))
        ra, rb = a.argsort().argsort(), b.argsort().argsort()
        return dict(pearson=rund(np.corrcoef(a, b)[0, 1], 3), spearman=rund(np.corrcoef(ra, rb)[0, 1], 3), n=int(len(a)))

    per_aera = {}
    for a in AERAER:
        m = np.array([aera_af(r) == a for r in recs]) & ok
        if not m.any():
            continue
        rs = [r for r, mm in zip(recs, m) if mm]
        per_aera[a] = dict(
            n=int(m.sum()), n_pos=int(sum(r["Y"] for r in rs)),
            indre_fordel_F5_nats=rund(indre[m].mean()), realiseret_fordel_F5_nats=rund(real[m].mean()),
            andel_indre_F5=rund(np.mean(indre[m] > 0), 3), andel_realiseret_F5=rund(np.mean(real[m] > 0), 3),
            fortegnsenighed=rund(np.mean((indre[m] > 0) == (real[m] > 0)), 3),
            andel_F5_valgt=rund(np.mean([r["valgt"] == "F5" for r in rs]), 3),
            indre_skill_curve_pct=rund(np.mean([r["curve_st"]["skill_cv"] for r in rs]), 2),
            indre_skill_F5_pct=rund(np.mean([r["F5_st"]["skill_cv"] for r in rs]), 2),
            lambda_curve=dict(zip(*[x.tolist() for x in np.unique([r["curve_st"]["lam"] for r in rs], return_counts=True)])),
            lambda_F5=dict(zip(*[x.tolist() for x in np.unique([r["F5_st"]["lam"] for r in rs], return_counts=True)])),
            middel_p_curve_nested=rund(np.mean([r["curve_nested"] for r in rs]), 3),
            middel_p_F5_nested=rund(np.mean([r["F5_nested"] for r in rs]), 3),
            z_cape_middel=rund(np.mean([r["F5_z"][feats.index("cape_pct")] for r in rs]), 3) if "F5_z" in rs[0] else None,
            cape_pct_raa_middel=rund(np.mean([D5["F"][qk_idx[(r["aar"], r["q"])], feats.index("cape_pct")] for r in rs]), 3))

    # blokniveau: origin -> episodeblok (naeste onset)
    blok_id = np.array([next((k for k, (o, _) in enumerate(eps) if o >= A2.midx(r["aar"], 6)), len(eps)) for r in recs])
    blok_tab = []
    for g in np.unique(blok_id):
        m = (blok_id == g) & ok
        if not m.any():
            continue
        rs = [r for r, mm in zip(recs, m) if mm]
        navn = (f"{eps[g][0] // 12}-{eps[g][0] % 12 + 1:02d}" if g < len(eps) else "hale")
        blok_tab.append(dict(blok_onset=navn, origins=f"{rs[0]['aar']}Q{rs[0]['q']}-{rs[-1]['aar']}Q{rs[-1]['q']}", n=int(m.sum()),
                             indre_fordel_F5_nats=rund(indre[m].mean()), realiseret_fordel_F5_nats=rund(real[m].mean()),
                             andel_F5_valgt=rund(np.mean([r["valgt"] == "F5" for r in rs]), 3)))
    blok_indre = np.array([b["indre_fordel_F5_nats"] for b in blok_tab]); blok_real = np.array([b["realiseret_fordel_F5_nats"] for b in blok_tab])

    # 2022-24-fejlalarmen: F5's logit-bidrag pr. feature (nested lambda), kontrafaktisk uden cape-bidrag
    ic = feats.index("cape_pct")
    falsk = []
    for r in recs:
        if FEJLALARM[0] <= (r["aar"], r["q"]) <= FEJLALARM[1]:
            w, z = np.array(r["F5_w"]), np.array(r["F5_z"])
            wc, zc = np.array(r["curve_w"]), np.array(r["curve_z"])
            bidrag = (w[1:] * z).tolist()
            logit = float(w[0] + sum(bidrag))
            p_uden_cape = float(1 / (1 + np.exp(-(logit - bidrag[ic]))))
            raa = {f: rund(D5["F"][next(i for i in range(len(D5["qk"])) if D5["qk"][i] == (r["aar"], r["q"]))][k], 3)
                   for k, f in enumerate(feats)}
            falsk.append(dict(origin=f"{r['aar']}Q{r['q']}", Y=r["Y"], curve_fast=rund(r["curve_fast"]), curve_nested=rund(r["curve_nested"]),
                              F5_fast=rund(r["F5_fast"]), F5_nested=rund(r["F5_nested"]), valgt=r["valgt"],
                              lambda_curve=r["curve_st"]["lam"], lambda_F5=r["F5_st"]["lam"],
                              indre_cv_curve=rund(r["curve_st"]["cv"]), indre_cv_F5=rund(r["F5_st"]["cv"]),
                              F5_intercept=rund(w[0]), F5_logit_bidrag={f: rund(b) for f, b in zip(feats, bidrag)},
                              F5_logit=rund(logit), F5_p_uden_cape_bidrag=rund(p_uden_cape),
                              curve_only_w=[rund(wc[0]), rund(wc[1])], curve_only_z=rund(zc[0]),
                              curve_only_logit=rund(wc[0] + wc[1] * zc[0]), raa_features=raa))
    fa = [r for r in recs if FEJLALARM[0] <= (r["aar"], r["q"]) <= FEJLALARM[1]]
    # cape-trend: dekade-middel af cape_pct (raa), F5's standardiserede cape-vaegt og cape-bidrag til logit
    cape_raa = D5["F"][:, ic]
    cape_trend = {}
    for dek in range(1950, 2030, 10):
        m = (D5["year"] >= dek) & (D5["year"] < dek + 10)
        rs = [r for r in recs if dek <= r["aar"] < dek + 10]
        cape_trend[f"{dek}s"] = dict(
            cape_pct_middel=rund(np.nanmean(cape_raa[m]), 3) if m.any() else None,
            cape_pct_min=rund(np.nanmin(cape_raa[m]), 3) if m.any() else None,
            cape_pct_max=rund(np.nanmax(cape_raa[m]), 3) if m.any() else None,
            n_origins=len(rs),
            F5_w_cape_middel=rund(np.mean([r["F5_w"][1 + ic] for r in rs]), 3) if rs else None,
            F5_w_curve_middel=rund(np.mean([r["F5_w"][1 + feats.index("curve")] for r in rs]), 3) if rs else None,
            curve_only_w_curve_middel=rund(np.mean([r["curve_w"][1] for r in rs]), 3) if rs else None,
            F5_cape_bidrag_middel=rund(np.mean([r["F5_w"][1 + ic] * r["F5_z"][ic] for r in rs]), 3) if rs else None,
            F5_curve_bidrag_middel=rund(np.mean([r["F5_w"][1 + feats.index("curve")] * r["F5_z"][feats.index("curve")] for r in rs]), 3) if rs else None,
            andel_z_cape_over_1=rund(np.mean([r["F5_z"][ic] > 1 for r in rs]), 3) if rs else None)

    # hvilke historiske blokke baerer F5's indre CV-fordel ved udvalgte origins (blokmiddel curve - F5 ved egen lambda)
    repr_origins = {}
    for (ya, qa) in [(1980, 1), (1990, 1), (2000, 1), (2010, 1), (2019, 4), (2024, 1)]:
        r = next((r for r in recs if (r["aar"], r["q"]) == (ya, qa)), None)
        if r is None or r["curve_st"]["blokmid"] is None:
            continue
        c, f = r["curve_st"], r["F5_st"]
        ids = c["blok_ids"]
        rows = []
        for k, g in enumerate(ids):
            navn = f"{eps[int(g)][0] // 12}-{eps[int(g)][0] % 12 + 1:02d}" if int(g) < len(eps) else "hale"
            rows.append(dict(blok_onset=navn, n_raekker=int(c["blok_n"][k]), curve_cv=rund(c["blokmid"][k]), F5_cv=rund(f["blokmid"][k]),
                             basis_cv=rund(c["base_blok"][k]), fordel_F5=rund(c["blokmid"][k] - f["blokmid"][k]),
                             bidrag_nats=rund((c["blokmid"][k] - f["blokmid"][k]) * c["blok_n"][k], 3)))
        repr_origins[f"{ya}Q{qa}"] = dict(lambda_curve=c["lam"], lambda_F5=f["lam"], indre_cv_curve=rund(c["cv"]), indre_cv_F5=rund(f["cv"]),
                                          indre_basis=rund(c["cv_base"]), valgt=r["valgt"], blokke=rows)

    ys = np.array([r["Y"] for r in recs]); b = ys.mean(); L0 = float(ll_rows(np.full(len(ys), b), ys).sum())
    sel_tab = aera_bidrag(recs, ["curve_nested", "sel"])
    return dict(
        definitioner=dict(indre_fordel_F5="indre CV-log-loss curve minus F5 (nats/raekke), hver ved egen valgt lambda; positiv = F5 bedre",
                          realiseret_fordel_F5="realiseret log-loss ved origin curve_nested minus F5_nested (nats); positiv = F5 bedre",
                          real8="middel af realiseret fordel over origin og de 7 foelgende origins"),
        korrelation=dict(origin=korr(indre[ok], real[ok]), origin_naeste_8=korr(indre[ok], real8[ok]),
                         blok=korr(blok_indre, blok_real),
                         fortegnsenighed_origin=rund(np.mean((indre[ok] > 0) == (real[ok] > 0)), 3),
                         andel_origins_indre_F5=rund(np.mean(indre[ok] > 0), 3), andel_origins_realiseret_F5=rund(np.mean(real[ok] > 0), 3),
                         middel_indre_fordel_F5_nats=rund(indre[ok].mean()), middel_realiseret_fordel_F5_nats=rund(real[ok].mean())),
        per_aera=per_aera, per_blok=blok_tab,
        selektionstab_per_aera_pp=sel_tab,
        selektionstab_i_alt_pp=rund(sum(v["sel"] - v["curve_nested"] for v in sel_tab.values()), 2),
        selektionstab_2021Q4_2024Q1_pp=rund(sel_tab.get("2021Q4-2024Q1", {}).get("sel", 0) - sel_tab.get("2021Q4-2024Q1", {}).get("curve_nested", 0), 2),
        skill_uden_fejlalarm=dict(
            note="skill (C.metrics) paa origins foer 2021Q4 alene (reviewets sammenligning: F5 +4,51 pp over curve-only ved fast lambda)",
            **{k: skill_af([(r["aar"], r["q"], r[k], r["Y"]) for r in recs if (r["aar"], r["q"]) < FEJLALARM[0]])
               for k in ("curve_fast", "F5_fast", "curve_nested", "F5_nested", "sel")}),
        skill_kun_fejlalarm_blok=dict(
            note="log-loss-sum (nats) paa origins 2021Q4-2024Q1 (alle Y = 0; skill mod basisrate udefineret)",
            **{k: rund(sum(ll1(r[k], r["Y"]) for r in fa), 3) for k in ("curve_fast", "F5_fast", "curve_nested", "F5_nested", "sel")},
            basis_poolet=rund(sum(ll1(b, r["Y"]) for r in fa), 3)),
        fejlalarm_2022_24=falsk, cape_trend=cape_trend, repraesentative_origins=repr_origins,
        redningsblok=redningsblok(recs, eps, mde))


# ------------------------------------------------------------ 'i dag'
def valg_i_dag(D_by, eps, avail, usrec, R, design, mde):
    """Indre CV paa hele det modne, ikke-censurerede panel ved R (A2.eligible_fit) under designet; valg under hver regel."""
    Dc = D_by["curve"]
    elig, yR = A2.eligible_fit(Dc, eps, avail, usrec, R)
    y = yR[elig]; qend = Dc["qend"][elig]; blok = blokke(qend, eps)
    ud = dict(n_obs=int(elig.sum()), n_pos=int(y.sum()), base_rate=rund(y.mean()))
    st = {}
    for m, D in D_by.items():
        X = D["F"][elig]
        mu, sd = std_af(X)
        cv = indre_cv(design, X, y, qend, blok, mu, sd)
        s = cv_stat(cv, float(y.mean()))
        st[m] = s
        ud[m] = dict(lambda_argmin=s["lam"], lambda_1se=s["lam_1se"], indre_cv=rund(s["cv"]), indre_cv_1se=rund(s["cv_1se"]),
                     indre_basis=rund(s["cv_base"]), indre_skill_pct=rund(s["skill_cv"], 2), indre_skill_1se_pct=rund(s["skill_cv_1se"], 2),
                     cv_pr_lambda={str(l): rund(v) for l, v in zip(design["grid"], s["pooled"])}, n_folds=s["n_folds"])
        if m == "curve":
            Z = (X - mu) / sd
            for navn, lam in (("argmin", s["lam"]), ("1se", s["lam_1se"]), ("fast", LAMBDA_FAST)):
                w = C.fit(Z, y, l2=lam)
                ud[m][f"p_ved_kurve_111_lambda_{navn}"] = rund(C.predict(w, (np.array([[1.11]]) - mu) / sd)[0])
    d_skill = st["F5"]["skill_cv"] - st["curve"]["skill_cv"]
    d_blok = st["curve"]["blokmid"] - st["F5"]["blokmid"]
    se = float(d_blok.std(ddof=1) / np.sqrt(len(d_blok)))
    ud["F5_minus_curve_indre_skill_pp"] = rund(d_skill, 2)
    ud["F5_minus_curve_blokmiddel_nats"] = rund(d_blok.mean()); ud["se_parret_nats"] = rund(se)
    ud["valg"] = dict(argmin="curve" if st["curve"]["cv"] <= st["F5"]["cv"] else "F5",
                      mde=("F5" if d_skill > mde else "curve"), **{f"taerskel_{t}": ("F5" if d_skill > t else "curve") for t in TAERSKLER_PP},
                      en_se_model=("F5" if d_blok.mean() > se else "curve"),
                      en_se_lambda_argmin=("curve" if st["curve"]["cv_1se"] <= st["F5"]["cv_1se"] else "F5"))
    return ud


# ------------------------------------------------------------------ main
def main():
    t0 = time.time()
    snap = C.RAW / SNAPSHOT
    R = A2.midx(*R_SCORE)
    W = json.loads((V5 / "weights.json").read_text(encoding="utf-8"))
    a9 = json.loads((V5 / "ablation9_resultat.json").read_text(encoding="utf-8")) if (V5 / "ablation9_resultat.json").exists() else {}
    f3 = V5 / "ablation3_resultat.json"
    mde = float(json.loads(f3.read_text(encoding="utf-8")).get("mde_pp", MDE_FALLBACK)) if f3.exists() else MDE_FALLBACK
    usrec = A2.load_usrec(snap); eps = A2.episodes_from_usrec(usrec)
    avail = A2.load_announcements(eps, usrec=usrec)
    Dc = A2.build_dataset(snap, ["curve"]); D5 = A2.build_dataset(snap, C.F5)
    if not A2.samme_origins(Dc, D5):
        sys.exit("FEJL: curve-only og F5 har ikke identiske origins paa dette panel.")
    D_by = {"curve": Dc, "F5": D5}
    saet = traeningssaet(Dc, eps, avail, usrec, R)
    print(f"snapshot {SNAPSHOT}  R_score {R_SCORE[0]}-{R_SCORE[1]:02d}  origins {len(saet)}  MDE {mde} pp", flush=True)

    # ---- del 1: designs
    del1, recs_by = {}, {}
    for navn, design in DESIGNS.items():
        t = time.time()
        recs = koer_design(navn, design, saet, D_by, gem_vaegte=(navn == REFERENCE_DESIGN))
        recs_by[navn] = recs
        aar = [r["aar"] for r in recs]
        d = dict(beskrivelse=design["tekst"], folds=design["folds"], std=design["std"], grid=design["grid"],
                 curve_nested=skill_af(sti(recs, "curve_nested")), F5_nested=skill_af(sti(recs, "F5_nested")),
                 sel_argmin=skill_af(sti(recs, "sel")),
                 curve_1se_lambda=skill_af(sti(recs, "curve_1se")), F5_1se_lambda=skill_af(sti(recs, "F5_1se")),
                 lambda_curve=lambda_fordeling(recs, "curve", design["grid"]), lambda_F5=lambda_fordeling(recs, "F5", design["grid"]),
                 lambda_curve_1se=lambda_fordeling(recs, "curve", design["grid"], "lam_1se"),
                 lambda_F5_1se=lambda_fordeling(recs, "F5", design["grid"], "lam_1se"),
                 valg_argmin=valg_oversigt([r["valgt"] for r in recs], aar),
                 fallback_origins=int(sum(1 for r in recs if r.get("curve_fallback") or r.get("F5_fallback"))),
                 andel_1se_lambda_ved_gridloft=dict(curve=rund(np.mean([r["curve_st"]["lam_1se"] == max(design["grid"]) for r in recs]), 3),
                                                    F5=rund(np.mean([r["F5_st"]["lam_1se"] == max(design["grid"]) for r in recs]), 3)),
                 middel_folds=rund(np.mean([r["curve_st"]["n_folds"] for r in recs]), 1),
                 aera_bidrag_pp=aera_bidrag(recs, ["curve_fast", "curve_nested", "F5_fast", "F5_nested", "sel"]))
        del1[navn] = d
        print(f"  {navn:<22} curve_nested {d['curve_nested']['improvement']:6.2f}/{d['curve_nested']['brier']:6.2f}  "
              f"F5_nested {d['F5_nested']['improvement']:6.2f}/{d['F5_nested']['brier']:6.2f}  sel {d['sel_argmin']['improvement']:6.2f}  "
              f"F5 valgt {d['valg_argmin']['andel_F5']:.3f} (fra 2000 {d['valg_argmin']['andel_F5_fra_2000']})  [{time.time() - t:.1f}s]", flush=True)
    ref = recs_by[REFERENCE_DESIGN]
    fast = dict(curve_fast=skill_af(sti(ref, "curve_fast")), F5_fast=skill_af(sti(ref, "F5_fast")))
    repro = dict(curve_fast=fast["curve_fast"]["improvement"], F5_fast=fast["F5_fast"]["improvement"],
                 curve_nested=del1[REFERENCE_DESIGN]["curve_nested"]["improvement"], F5_nested=del1[REFERENCE_DESIGN]["F5_nested"]["improvement"],
                 sel=del1[REFERENCE_DESIGN]["sel_argmin"]["improvement"],
                 andel_valgt_curve=rund(1 - del1[REFERENCE_DESIGN]["valg_argmin"]["andel_F5"], 3),
                 lambda_curve=del1[REFERENCE_DESIGN]["lambda_curve"], lambda_F5=del1[REFERENCE_DESIGN]["lambda_F5"])
    a9s = a9.get("skill", {})
    repro["ok_mod_ablation9_resultat"] = bool(a9s) and all(
        abs(repro[k] - a9s[k]["improvement"]) < 0.005 for k in ("curve_fast", "F5_fast", "curve_nested", "F5_nested", "sel")) \
        and repro["lambda_curve"] == {k: v for k, v in a9.get("lambda_fordeling", {}).get("curve", {}).items()} \
        and repro["lambda_F5"] == {k: v for k, v in a9.get("lambda_fordeling", {}).get("F5", {}).items()}
    repro["ok_mod_weights_json"] = bool(abs(repro["curve_fast"] - W["op"]["wf_improvement"]) < 0.005)

    # fast-lambda-sweep (reference: max over stien er IKKE walk-forward-skill; kun til at vise kurvens form)
    sweep = {}
    for lam in GRID_FIN:
        rows = {m: [] for m in D_by}
        for s in saet:
            for m, D in D_by.items():
                X = D["F"][s["tr"]]; mu, sd = std_af(X)
                p = float(C.predict(C.fit((X - mu) / sd, s["y"], l2=lam), (D["F"][[s["i"]]] - mu) / sd)[0])
                rows[m].append((s["aar"], s["q"], p, s["Y"]))
        sweep[str(lam)] = {m: skill_af(rows[m]) for m in D_by}
        sweep[str(lam)]["F5_minus_curve_pp"] = rund(sweep[str(lam)]["F5"]["improvement"] - sweep[str(lam)]["curve"]["improvement"], 2)
    cn = [del1[n]["curve_nested"]["improvement"] for n in DESIGNS]
    fn = [del1[n]["F5_nested"]["improvement"] for n in DESIGNS]
    sn = [del1[n]["sel_argmin"]["improvement"] for n in DESIGNS]
    del1_sammenfatning = dict(
        n_designs=len(DESIGNS),
        curve_nested_interval=dict(min=min(cn), max=max(cn), median=rund(np.median(cn), 2), fast_lambda_1=fast["curve_fast"]["improvement"]),
        F5_nested_interval=dict(min=min(fn), max=max(fn), median=rund(np.median(fn), 2), fast_lambda_1=fast["F5_fast"]["improvement"]),
        sel_argmin_interval=dict(min=min(sn), max=max(sn), median=rund(np.median(sn), 2)),
        curve_vinder_nested_i_alle_designs=bool(all(c > f for c, f in zip(cn, fn))),
        F5_minus_curve_nested_pp={n: rund(del1[n]["F5_nested"]["improvement"] - del1[n]["curve_nested"]["improvement"], 2) for n in DESIGNS},
        bootstrap_parret_a9=dict(
            F5_nested_minus_curve_nested=mde_parret(ref, "curve_nested", "F5_nested", eps),
            curve_nested_minus_curve_fast=mde_parret(ref, "curve_fast", "curve_nested", eps),
            sel_minus_curve_nested=mde_parret(ref, "curve_nested", "sel", eps),
            note="episode-blok-bootstrap (SEED 42, 1000 traek) af den parrede skill-forskel, som ablation3.mde_bootstrap; "
                 "sensitivitet, ikke walk-forward"),
        fast_lambda_sweep=sweep,
        note="Fast lambda-sweep = max over hele stien (ikke walk-forward-skill, §6); vist for at se hvor nested-valgene ligger "
             "paa kurven. Nested-tallene er walk-forward i §6's forstand.")

    # ---- del 2: diagnose (referencedesign)
    del2 = diagnose(ref, eps, D5, C.F5, mde)
    del2["per_origin"] = [dict(o=f"{r['aar']}Q{r['q']}", Y=r["Y"], cv_c=rund(r["curve_st"]["cv"]), cv_5=rund(r["F5_st"]["cv"]),
                               cv_basis=rund(r["curve_st"]["cv_base"]), lam_c=r["curve_st"]["lam"], lam_5=r["F5_st"]["lam"],
                               p_c=rund(r["curve_nested"]), p_5=rund(r["F5_nested"]), p_c_fast=rund(r["curve_fast"]), p_5_fast=rund(r["F5_fast"]),
                               ll_c=rund(ll1(r["curve_nested"], r["Y"])), ll_5=rund(ll1(r["F5_nested"], r["Y"])), valgt=r["valgt"])
                          for r in ref]

    # ---- del 3: selektorer (alle designs; referencedesign fremhaeves)
    del3 = {}
    for navn, recs in recs_by.items():
        aar = [r["aar"] for r in recs]
        regler = {}
        for regel, tekst in (("argmin", "ablation9's reference: laveste indre CV-tab ved egen lambda; uafgjort -> curve-only"),
                             ("mde", f"default curve-only; F5 kun hvis indre CV-skill (F5 - curve) > gate-MDE {mde} pp"),
                             ("1se_model", "default curve-only; F5 kun hvis blokmiddel-tab er > 1 SE (parret over episodeblokke) lavere"),
                             ("1se_lambda_argmin", "begge modeller ved 1-SE-lambda (stoerste lambda inden for 1 SE af minimum); argmin-valg"),
                             ("1se_lambda_mde", f"1-SE-lambda for begge + MDE-gated valg (> {mde} pp), default curve-only")):
            rows, valg = selektor_sti(recs, regel, mde=mde)
            regler[regel] = dict(beskrivelse=tekst, skill=skill_af(rows), **valg_oversigt(valg, aar))
        taerskler = {}
        for t in TAERSKLER_PP:
            rows, valg = selektor_sti(recs, "mde", taerskel=t)
            taerskler[str(t)] = dict(skill=skill_af(rows), **valg_oversigt(valg, aar))
        hist = {}
        for key in ("nested", "fast"):
            for default in ("curve", "F5"):
                for mh in (8, 20, 40):
                    rows, valg = realiseret_historik(recs, eps, avail, default, mh, key=key)
                    hist[f"{key}_default_{default}_min_hist_{mh}"] = dict(skill=skill_af(rows), **valg_oversigt(valg, aar))
        del3[navn] = dict(regler=regler, taerskel_sweep_mde=taerskler, realiseret_historik=hist,
                          reference=dict(curve_nested=del1[navn]["curve_nested"], F5_nested=del1[navn]["F5_nested"]))
    idag = {navn: valg_i_dag(D_by, eps, avail, usrec, R, DESIGNS[navn], mde) for navn in (REFERENCE_DESIGN, "blok_purge", "expanding40")}

    r3 = del3[REFERENCE_DESIGN]
    del3_sammenfatning = dict(
        design=REFERENCE_DESIGN,
        skill_pr_regel={k: v["skill"]["improvement"] for k, v in r3["regler"].items()},
        andel_F5_pr_regel={k: v["andel_F5"] for k, v in r3["regler"].items()},
        andel_F5_fra_2000_pr_regel={k: v["andel_F5_fra_2000"] for k, v in r3["regler"].items()},
        taerskel_sweep={k: dict(skill=v["skill"]["improvement"], andel_F5=v["andel_F5"]) for k, v in r3["taerskel_sweep_mde"].items()},
        realiseret_historik={k: dict(skill=v["skill"]["improvement"], andel_F5=v["andel_F5"]) for k, v in r3["realiseret_historik"].items()},
        paa_tvaers_af_designs={regel: dict(min=min(del3[n]["regler"][regel]["skill"]["improvement"] for n in DESIGNS),
                                            max=max(del3[n]["regler"][regel]["skill"]["improvement"] for n in DESIGNS))
                               for regel in r3["regler"]},
        valg_i_dag=idag)

    ab = del1[REFERENCE_DESIGN]["aera_bidrag_pp"]
    fa_rows = del2["fejlalarm_2022_24"]
    fra2000 = [r for r in ref if r["aar"] >= 2000 and not np.isnan(r["curve_st"]["skill_cv"])]
    hovedtal = dict(
        publiceret_fast_lambda_1=dict(curve=fast["curve_fast"]["improvement"], F5=fast["F5_fast"]["improvement"]),
        ablation9_reproduceret=dict(curve_nested=repro["curve_nested"], F5_nested=repro["F5_nested"], sel=repro["sel"], ok=repro["ok_mod_ablation9_resultat"]),
        del1_curve_nested_interval_pp=[min(cn), max(cn)], del1_curve_nested_median_pp=rund(np.median(cn), 2),
        del1_F5_nested_interval_pp=[min(fn), max(fn)], del1_sel_argmin_interval_pp=[min(sn), max(sn)],
        del1_curve_vinder_nested_i_alle_designs=bool(all(c > f for c, f in zip(cn, fn))),
        del1_nested_tab_curve_1970s_1980s_pp=rund((ab["1970s"]["curve_nested"] + ab["1980s"]["curve_nested"]) - (ab["1970s"]["curve_fast"] + ab["1980s"]["curve_fast"]), 2),
        del1_nested_gevinst_curve_2021Q4_2024Q1_pp=rund(ab["2021Q4-2024Q1"]["curve_nested"] - ab["2021Q4-2024Q1"]["curve_fast"], 2),
        del1_bootstrap_curve_nested_minus_fast=del1_sammenfatning["bootstrap_parret_a9"]["curve_nested_minus_curve_fast"],
        del1_andel_origins_lambda_ge_30_curve_a9=rund(np.mean([r["curve_st"]["lam"] >= 30 for r in ref]), 3),
        del2_korrelation_indre_vs_realiseret=del2["korrelation"],
        del2_selektionstab_i_alt_pp=del2["selektionstab_i_alt_pp"], del2_selektionstab_2021Q4_2024Q1_pp=del2["selektionstab_2021Q4_2024Q1_pp"],
        del2_indre_skill_fordel_F5_fra_2000_pp=rund(np.mean([r["F5_st"]["skill_cv"] - r["curve_st"]["skill_cv"] for r in fra2000]), 2),
        del2_indre_skill_fordel_F5_fra_2000_min_pp=rund(min(r["F5_st"]["skill_cv"] - r["curve_st"]["skill_cv"] for r in fra2000), 2),
        del2_redningsblok=dict(stoerste_fra_2000=del2["redningsblok"]["stoerste_bidragyder_fra_2000"],
                               andel_fra_2000_hvor_curve_vinder_uden=del2["redningsblok"]["andel_fra_2000_hvor_curve_vinder_uden_stoerste_blok"],
                               middel_andel_af_fordel=del2["redningsblok"]["middel_andel_af_F5_fordel_fra_stoerste_blok_fra_2000"],
                               F5_fordel_fra_2000_pp=del2["redningsblok"]["middel_indre_skill_fordel_F5_fra_2000_pp"],
                               F5_fordel_uden_stoerste_blok_fra_2000_pp=del2["redningsblok"]["middel_indre_skill_fordel_F5_uden_stoerste_blok_fra_2000_pp"],
                               andel_over_mde=del2["redningsblok"]["andel_fra_2000_hvor_F5_fordel_over_mde"],
                               andel_uden_stoerste_blok_over_mde=del2["redningsblok"]["andel_fra_2000_hvor_F5_fordel_uden_stoerste_blok_over_mde"]),
        del2_fejlalarm_F5_cape_bidrag_middel=rund(np.mean([f["F5_logit_bidrag"]["cape_pct"] for f in fa_rows]), 3),
        del2_fejlalarm_F5_curve_bidrag_middel=rund(np.mean([f["F5_logit_bidrag"]["curve"] for f in fa_rows]), 3),
        del2_fejlalarm_F5_logit_middel=rund(np.mean([f["F5_logit"] for f in fa_rows]), 3),
        del2_fejlalarm_curve_only_logit_middel=rund(np.mean([f["curve_only_logit"] for f in fa_rows]), 3),
        del2_cape_pct_raa_1970s_1980s=[del2["cape_trend"]["1970s"]["cape_pct_middel"], del2["cape_trend"]["1980s"]["cape_pct_middel"]],
        del2_cape_pct_raa_1990s_2020s=[del2["cape_trend"][d]["cape_pct_middel"] for d in ("1990s", "2000s", "2010s", "2020s")],
        del2_F5_w_cape_2000s_2020s=[del2["cape_trend"][d]["F5_w_cape_middel"] for d in ("2000s", "2010s", "2020s")],
        del3_skill_pr_regel=del3_sammenfatning["skill_pr_regel"], del3_andel_F5_pr_regel=del3_sammenfatning["andel_F5_pr_regel"],
        del3_taerskel_sweep=del3_sammenfatning["taerskel_sweep"],
        del3_1se_lambda_ved_gridloft_andel=del1[REFERENCE_DESIGN]["andel_1se_lambda_ved_gridloft"],
        del3_realiseret_historik=del3_sammenfatning["realiseret_historik"],
        del3_paa_tvaers_af_designs=del3_sammenfatning["paa_tvaers_af_designs"],
        valg_i_dag=dict(regler=idag[REFERENCE_DESIGN]["valg"], F5_minus_curve_indre_skill_pp=idag[REFERENCE_DESIGN]["F5_minus_curve_indre_skill_pp"],
                        lambda_curve=idag[REFERENCE_DESIGN]["curve"]["lambda_argmin"], lambda_F5=idag[REFERENCE_DESIGN]["F5"]["lambda_argmin"],
                        p_ved_kurve_111=dict(fast=idag[REFERENCE_DESIGN]["curve"]["p_ved_kurve_111_lambda_fast"],
                                             argmin=idag[REFERENCE_DESIGN]["curve"]["p_ved_kurve_111_lambda_argmin"],
                                             en_se=idag[REFERENCE_DESIGN]["curve"]["p_ved_kurve_111_lambda_1se"])))
    ud = dict(
        protocol="5.0-analyse-nested_robusthed (EKSPLORATIV — erstatter ikke ablation9, praeregistreret G1.1/G1.2)",
        status="eksplorativ; aendrer intet i driften (weights.json, P, operationel model uroert)",
        svarer_paa="kode-review 2026-10-15 G1.1 (nested lambda) og G1.2 (nested modelselektion); ablation9_resultat.json",
        created_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        snapshot=SNAPSHOT, R_score=f"{R_SCORE[0]}-{R_SCORE[1]:02d}", n_origins=len(saet), mde_pp=mde, seed=SEED,
        weights_json=dict(snapshot=W.get("snapshot"), refit_maaned=W.get("refit_maaned"), manifest=W.get("manifest_hash"),
                          wf_improvement=W["op"]["wf_improvement"]),
        reproduktion_ablation9=repro, fast_lambda_1=fast, hovedtal=hovedtal,
        del1_robusthed=dict(sammenfatning=del1_sammenfatning, designs=del1),
        del2_diagnose=del2,
        del3_selektorer=dict(sammenfatning=del3_sammenfatning, designs=del3),
        noter=[
            "Eksplorativ analyse: designs og regler er valgt efter at ablation9's resultat var set; intet her er praeregistreret.",
            "Alle tal er paa v5.0.1-panelet (snapshot 2026-09-19, R = 2026-09, 198 origins, identiske origins for curve-only og F5).",
            "Nested-tal er walk-forward i blueprintets §6-forstand; fast-lambda-sweep og 'skill_uden_fejlalarm' er fuld-sti-udsnit og ikke walk-forward.",
            "Skill-bidrag pr. aera summerer til stiens improvement (pp af den poolede basislinjes samlede log-loss).",
            "Ingen fil i repoet ud over analyser/nested_robusthed_resultat.json er skrevet; __pycache__ er ikke skrevet.",
        ])
    out = HERE / "nested_robusthed_resultat.json"
    out.write_text(json.dumps(ud, indent=1, ensure_ascii=False, default=float), encoding="utf-8")
    print(f"\nreproduktion ablation9: {repro['ok_mod_ablation9_resultat']}  weights.json: {repro['ok_mod_weights_json']}")
    print("del1 curve_nested interval:", del1_sammenfatning["curve_nested_interval"])
    print("del1 F5_nested interval:   ", del1_sammenfatning["F5_nested_interval"])
    print("del2 korrelation:", json.dumps(del2["korrelation"]))
    print("del2 selektionstab i alt / 2021Q4-2024Q1:", del2["selektionstab_i_alt_pp"], "/", del2["selektionstab_2021Q4_2024Q1_pp"])
    print("del3 skill pr regel:", json.dumps(del3_sammenfatning["skill_pr_regel"]))
    print("del3 andel F5 pr regel:", json.dumps(del3_sammenfatning["andel_F5_pr_regel"]))
    print("del3 taerskel-sweep:", json.dumps(del3_sammenfatning["taerskel_sweep"]))
    print("i dag (a9_blok):", json.dumps({k: v for k, v in idag[REFERENCE_DESIGN].items() if k in ("valg", "F5_minus_curve_indre_skill_pp")}))
    print(f"\n{out.name} skrevet ({time.time() - t0:.1f}s; koeretid staar ikke i filen).")


if __name__ == "__main__":
    main()
