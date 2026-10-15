#!/usr/bin/env python3
"""
replay2027.py — RAADETS_2027 §6.2: den konfigurationsspecifikke hovedbogs-replay for regimet
september + hash + NBER-indholdstrigger (forseglet spec: spec2027/3_indholdstrigger_replay.md §3).

Konstruktionen er E5's (analyser/hovedbog_reference.py, noeglens regler) med een aendring: kalibreringsplanen.
  - Een raekke pr. logningsmaaned; origin m = maaneden foer; input = GS10 - TB3MS for m; vindue = logningsmaaneden
    + 11 mdr; Y = 1 hvis en USREC-onset (endelig kronologi) ligger i vinduet; kun modne raekker (m + 30 <= R_score).
  - P = kalibreringen i kraft ved logningen (finalize6.p_af paa afrundede manifestvaegte), logget med 1 decimal;
    basisrate = kalibreringens fit-basisrate; skill = 1 - LL(P)/LL(basisrate), Brier sekundaer, clip 1e-6.
  - Information ved logningsmaaned M: tabellens raekker annonceret senest logdag(M) (dag-praecist).
  - Refit i M ved september, hash (en tabel-raekke bliver synlig i M) eller indholdstrigger (protokol2027,
    evalueret mod kalibreringen i kraft); hoejst een refit pr. maaned; >= 60 origins og >= 6 positive.
  - Tre censurvarianter, altid alle tre og i denne raekkefoelge: realtid (motorens aabne-episode-regel), realtid
    uden USREC-vintage-antagelsen (dag-praecis top, endelig bund), orakel.

Beskrivelse, ikke en test; vedtagelsen er ikke betinget af tallene. September-alene-tallene (E5) er ikke dette
regimes skill og printes ikke. Koeres ved september-refitten 2027 efter finalize6.py og diagnostik.py:

  python replay2027.py [--snapshot data/raw/YYYY-MM-DD]     (default: kalibreringens snapshot og refit-maaned)

Ved refitten re-afleder den ogsaa styrkeklausulen (RAADETS_2027 §1.2, spec2027/6_skill_saetning_refit.md §3) af
realtidsraekkerne med analyser/styrke_simulation.py's maskineri. Skriver replay2027_resultat.json. Kun stdlib + numpy.
"""
import json, sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import numpy as np

import calibrate as C
import ablation2_nber as A2
import finalize6 as F6
import protokol2027 as P27

HERE = Path(__file__).parent
L = A2.L_EMBARGO
MIN_N, MIN_POS = 60, 6
CLIP = 1e-6
REGIME = ("september", "hash", "indhold")
OVERSKRIFT = ("Konfigurationsspecifik replay (september + hash + indholdstrigger) — hovedbogs-supplement for dette "
              "regime (RAADETS_2027 §6.2). Beskrivelse, ikke en test; vedtagelsen er ikke betinget af tallene.")
VARIANTER = (("realtid_aaben_episode", "realtid (motorens aabne-episode-regel)"),
             ("realtid_uden_vintage", "realtid uden USREC-vintage-antagelsen (dag-praecis top, endelig bund)"),
             ("orakel", "orakel (endelig kronologi)"))
ym = P27.ym


def logdag(M):
    """Foerste hverdag fra og med den 10. i maaned M (noeglen (i); helligdage ignoreres)."""
    d = date(M // 12, M % 12 + 1, 10)
    while d.weekday() >= 5:
        d += timedelta(days=1)
    return d


def annoncerings_datoer(eps, rows):
    """Dag-praecise datoer, hvor top og bund er kendt, pr. episode-onset. Pre-1979: den 1. i maaned trough + 18 for
    begge (konventionen). Ingen raekke (fx en aaben episode): aldrig kendt (date.max)."""
    peak_d, trough_d = {}, {}
    for r in rows:
        t = P27._md(r["cycle_month"])
        d = date.fromisoformat(r["announcement_date"][:10])
        if r["event"].startswith("peak"):
            best = min(eps, key=lambda e: abs(e[0] - t))
            if abs(best[0] - t) <= 2:
                peak_d[best[0]] = d
        elif r["event"].startswith("trough"):
            best = min(eps, key=lambda e: abs(e[1] - t))
            if abs(best[1] - t) <= 2:
                trough_d[best[0]] = d
    for O, T in eps:
        if O < A2.POST1979:
            k = T + A2.PRE1979_TROUGH_LAG
            peak_d.setdefault(O, date(k // 12, k % 12 + 1, 1))
            trough_d.setdefault(O, date(k // 12, k % 12 + 1, 1))
        peak_d.setdefault(O, date.max)
        trough_d.setdefault(O, date.max)
    return peak_d, trough_d


def avail_ved(avail, peak_d, d):
    """Informationssaettet ved dato d: en post-1979-top er kun kendt, hvis dens raekke er annonceret senest d."""
    return {o: (a if o < A2.POST1979 or peak_d.get(o, date.max) <= d else P27.INF) for o, a in avail.items()}


def kalibrering(D, eps, aM, usrec, M):
    """finalize6.fit_model ved refit-maaned M med informationssaettet aM, eller None under minimumskravet."""
    elig, yR = A2.eligible_fit(D, eps, aM, usrec, M)
    if elig.sum() < MIN_N or yR[elig].sum() < MIN_POS:
        return None
    m = F6.fit_model(D, eps, aM, usrec, M)
    return dict(R=int(M), model={k: m[k] for k in ("features", "mu", "sd", "w", "base_rate", "n_obs", "n_pos")},
                origins=m["_origins"])


def plan(D, eps, avail, usrec, rows, R_score, regel=REGIME):
    """Kalibreringsplanen {M: kalibrering} og refit-listen for regimet `regel` (spec 3 §3.2)."""
    peak_d, _ = annoncerings_datoer(eps, rows)
    datoer = sorted((date.fromisoformat(r["announcement_date"][:10]), r["event"]) for r in rows)
    M0 = None
    for y in range(1955, R_score // 12 + 1):
        M = A2.midx(y, 9)
        if M > R_score:
            break
        k = kalibrering(D, eps, avail_ved(avail, peak_d, logdag(M)), usrec, M)
        if k:
            M0, kal = M, k
            break
    if M0 is None:
        return {}, []
    kalibreringer = {M0: kal}
    refits = [dict(R=ym(M0), grunde=["september (foerste kalibrering)"], n_obs=kal["model"]["n_obs"],
                   n_pos=kal["model"]["n_pos"], w=kal["model"]["w"])]
    for M in range(M0 + 1, R_score + 1):
        d0, d = logdag(M - 1), logdag(M)
        aM = avail_ved(avail, peak_d, d)
        grunde = []
        if "september" in regel and M % 12 == 8:
            grunde.append("september")
        if "hash" in regel:
            nye = [ev for dt, ev in datoer if d0 < dt <= d]
            if nye:
                grunde.append("hash: " + ", ".join(nye))
        if "indhold" in regel:
            it = P27.indholdstrigger(D, eps, aM, usrec, M, kal["origins"], kal["R"])
            if it["udloest"]:
                grunde.append("indhold: " + "; ".join([f"ny onset {o} ({', '.join(v)})" for o, v in sorted(it["nye_onsets"].items())]
                                                      + [f"omlabeling {x}" for x in it["omlabelinger"]]))
        if not grunde:
            continue
        k = kalibrering(D, eps, aM, usrec, M)
        if k is None:
            continue
        kal = kalibreringer[M] = k
        refits.append(dict(R=ym(M), grunde=grunde, n_obs=k["model"]["n_obs"], n_pos=k["model"]["n_pos"], w=k["model"]["w"]))
    return kalibreringer, refits


def raekker(curve_m, kalibreringer, eps, usrec, peak_d, trough_d, R_score):
    """Een hovedbogsraekke pr. logningsmaaned (spec 3 §3.1) med de tre censurflag (§3.3)."""
    Rs = sorted(kalibreringer)
    ud = []
    for m in sorted(curve_m):
        m_log = m + 1
        if m + 12 + L > R_score:
            continue
        R = max((r for r in Rs if r <= m_log), default=None)
        if R is None:
            continue
        mod = kalibreringer[R]["model"]
        p = F6.p_af(mod, {"curve": curve_m[m]})
        d = logdag(m_log)
        ep = A2.episode_of(m, eps)
        aaben = False
        for O, T in eps:
            if peak_d[O] > d:
                continue
            if O <= m and (m <= T or trough_d[O] > d):
                aaben = True
                break
        ud.append(dict(m=int(m), origin=ym(m), logget=ym(m_log), R=int(R), p=float(p), p_logget=round(p * 100, 1) / 100,
                       b=float(mod["base_rate"]), Y=1.0 if any(m + 1 <= o <= m + 12 for o, _ in eps) else 0.0,
                       realtid_aaben_episode=aaben,
                       realtid_uden_vintage=bool(ep and peak_d[ep[0]] <= d),
                       orakel=usrec.get(m, 0) == 1))
    return ud


def score(rs):
    """Noeglens metrik mod raekkens loggede basisrate (som E5)."""
    if not rs:
        return dict(n=0, n_pos=0, skill_LL=None, skill_brier=None)
    p = np.clip(np.array([r["p_logget"] for r in rs]), CLIP, 1 - CLIP)
    y = np.array([r["Y"] for r in rs])
    b = np.clip(np.array([r["b"] for r in rs]), CLIP, 1 - CLIP)
    Lm = -(y * np.log(p) + (1 - y) * np.log(1 - p))
    L0 = -(y * np.log(b) + (1 - y) * np.log(1 - b))
    return dict(n=len(rs), n_pos=int(y.sum()), skill_LL=round(float((1 - Lm.mean() / L0.mean()) * 100), 2),
                skill_brier=round(float((1 - ((p - y) ** 2).mean() / ((b - y) ** 2).mean()) * 100), 2))


def blokke_fra_replay(rs, eps):
    """Spec 6 §3: bund-til-bund-blokke i kalendermaaneder over replayens origin-maaneder; scorede raekker (censurvariant
    1, realtid) giver (L0, Lm) med L0 mod den LOGGEDE basisrate; censurerede maaneder er tomme pladser (None)."""
    md = {}
    for r in rs:
        if r["realtid_aaben_episode"]:
            continue
        p = min(max(r["p_logget"], CLIP), 1 - CLIP)
        b = min(max(r["b"], CLIP), 1 - CLIP)
        y = r["Y"]
        md[r["m"]] = (float(-(y * np.log(b) + (1 - y) * np.log(1 - b))), float(-(y * np.log(p) + (1 - y) * np.log(1 - p))), y)
    start, slut = min(r["m"] for r in rs), max(r["m"] for r in rs)
    gr = [start - 1] + [t for _, t in sorted(eps, key=lambda e: e[1]) if start <= t <= slut] + [slut]
    ud = []
    for a, b in zip(gr[:-1], gr[1:]):
        ons = [o - (a + 1) for o, _ in sorted(eps) if a < o <= b]
        pm = [md[mm][:2] if mm in md else None for mm in range(a + 1, b + 1)]
        v = [x for x in pm if x is not None]
        ud.append(dict(fra=a + 1, til=b, kal=b - a, n=len(v), ons=ons[0] if ons else None, pm=pm,
                       s0=float(sum(x[0] for x in v)), s1=float(sum(x[1] for x in v)),
                       sum_d=float(sum(x[0] - x[1] for x in v)), pos=int(sum(md[mm][2] for mm in range(a + 1, b + 1) if mm in md))))
    return ud


def styrke(rs, eps, nsim=None, nboot=None, seed=None):
    """Spec 6 §3: styrkeklausulen re-afledt af replayens realtidsraekker med styrkesimulationens maskineri (uaendret)."""
    sys.path.insert(0, str(HERE / "analyser"))
    import styrke_simulation as SS
    nsim, nboot, seed = nsim or SS.NSIM, nboot or SS.NBOOT, seed or SS.SEED
    pulje = blokke_fra_replay(rs, eps)
    n = sum(b["n"] for b in pulje)
    middel_d = sum(b["sum_d"] for b in pulje) / n
    tabel = []
    for T in SS.T_GRID:
        h1 = SS.koer(T, pulje, 0.0, nsim=nsim, nboot=nboot, seed=seed)
        h0 = SS.koer(T, pulje, middel_d, nsim=nsim, nboot=nboot, seed=seed)
        tabel.append(SS.opsummer(T, h1, h0))
    aar = SS.aar_til_80(tabel, "styrke")
    p3 = P27.p_hele_komplette(20, pulje, nsim=nsim, seed=seed)
    fp = [r["falsk_positiv_H0"][k] for r in tabel if r["T_aar"] in (5, 10, 20) for k in ("naiv", "boot44")]
    lo, hi = int(round(min(fp) * 100)), int(round(max(fp) * 100))
    return dict(protokol="RAADETS_2027 §1.2", spec_sha256=P27.kraev_forseglet("6_skill_saetning_refit.md"),
                n_blokke=len(pulje), n_komplette=sum(b["ons"] is not None for b in pulje), n_scorede=n,
                middel_d=round(middel_d, 4), n_sim=nsim, n_boot=nboot, seed=seed,
                blokke=[dict(fra=ym(b["fra"]), til=ym(b["til"]), kal_mdr=b["kal"], scorede=b["n"], positive=b["pos"],
                             komplet=b["ons"] is not None, sum_d=round(b["sum_d"], 4)) for b in pulje],
                aar_til_80=aar, p_3_komplette_20_aar=round(p3, 4), naive_falsk_positiv_5_20_aar=[lo, hi],
                tabel=tabel, klausul=P27.klausul(aar["interpoleret_aar"], p3, lo, hi))


def replay(snap, R_score, regel=REGIME, ann=None, med_styrke=False, **styrke_kw):
    """Hele replayen for et snapshot og en scoringsmaaned. -> resultat-dict (varianterne i spec'ens raekkefoelge)."""
    h = P27.kraev_forseglet("3_indholdstrigger_replay.md")
    rows = A2.laes_annonceringer(ann)
    usrec = A2.load_usrec(snap)
    eps = A2.episodes_from_usrec(usrec)
    avail = A2.load_announcements(eps, f=ann, usrec=usrec)
    peak_d, trough_d = annoncerings_datoer(eps, rows)
    D = A2.build_dataset(snap, ["curve"])
    gs10, tb3 = C.read_fred(snap, "GS10"), C.read_fred(snap, "TB3MS")
    curve_m = {A2.midx(y, mo): gs10[(y, mo)] - tb3[(y, mo)] for (y, mo) in gs10 if (y, mo) in tb3}
    kal, refits = plan(D, eps, avail, usrec, rows, R_score, regel)
    rs = raekker(curve_m, kal, eps, usrec, peak_d, trough_d, R_score)
    typer = {}
    for r in refits:
        for g in r["grunde"]:
            typer[g.split(":")[0].split(" (")[0]] = typer.get(g.split(":")[0].split(" (")[0], 0) + 1
    indhold = [dict(R=r["R"], grund=g) for r in refits for g in r["grunde"] if g.startswith("indhold")]
    ekstra = dict(styrke=styrke(rs, eps, **styrke_kw)) if med_styrke else {}
    return ekstra | dict(overskrift=OVERSKRIFT, protokol="RAADETS_2027 §6.2", spec_sha256=h, regel=list(regel),
                snapshot=snap.name, R_score=ym(R_score), L_embargo=L,
                varianter=[dict(navn=n, beskrivelse=b, **score([r for r in rs if not r[n]])) for n, b in VARIANTER],
                n_raekker=len(rs), foerste_logget=rs[0]["logget"] if rs else None, sidste_logget=rs[-1]["logget"] if rs else None,
                n_refits=len(refits), refits_pr_type=typer, indholdsudloeste_refits=indhold, refits=refits,
                note="September-alene-tallene (E5) er ikke dette regimes skill og printes ikke her (RAADETS_2027 §6.2).")


def linjer(res):
    ud = [res["overskrift"], f"   snapshot {res['snapshot']}, R_score {res['R_score']}, {res['n_raekker']} raekker "
                             f"({res['foerste_logget']}..{res['sidste_logget']}), {res['n_refits']} refits {res['refits_pr_type']}"]
    for v in res["varianter"]:
        ud.append(f"   {v['beskrivelse']:<72} n {v['n']:>4}  positive {v['n_pos']:>3}  skill {v['skill_LL']:+.2f}%  "
                  f"Brier {v['skill_brier']:+.2f}%")
    for r in res["indholdsudloeste_refits"]:
        ud.append(f"   indholdsudloest refit {r['R']}: {r['grund']}")
    ud.append(f"   {res['note']}")
    if res.get("styrke"):
        ud.append(f"   Styrkeklausul (RAADETS_2027 §1.2): {res['styrke']['klausul']}")
    return ud


def main():
    W = json.loads((HERE / "weights.json").read_text(encoding="utf-8"))
    if not P27.i_kraft_maaned(W.get("refit_maaned")):
        sys.exit(f"replay2027.py koeres ved september-refitten 2027 (spec2027/3_indholdstrigger_replay.md §3): "
                 f"kalibreringen i drift er fra {W.get('refit_maaned')}. Intet beregnet.")
    snap = C.find_snapshot(sys.argv) if "--snapshot" in sys.argv else C.RAW / W["snapshot"]
    R = A2.midx(int(W["refit_maaned"][:4]), int(W["refit_maaned"][5:7]))
    res = replay(snap, R, med_styrke=True)
    res.update(manifest_hash=W.get("manifest_hash"), created_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"))
    for ln in linjer(res):
        print(ln)
    (HERE / "replay2027_resultat.json").write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    print("replay2027_resultat.json skrevet.")


if __name__ == "__main__":
    main()
