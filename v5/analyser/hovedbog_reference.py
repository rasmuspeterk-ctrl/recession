#!/usr/bin/env python3
"""
analyser/hovedbog_reference.py — hovedbogens forventede referencetal, beregnet med NOEGLENS EGNE regler.

FORMAAL
  Kode-review 2026-10-15, fund G3.5, og BEDOEMMELSESNOEGLE.md §3: den publicerede walk-forward-skill (+27,05 %)
  bygger paa orakel-censurering (endelig kronologi) og en poolet, ex post realiseret basisrate — to ting
  hovedbogen ikke kan efterligne. Noeglen siger, at hovedbogens referencetal skal beregnes med noeglens egne
  regler. Reviewets eget skoen (pw_keys.py) var ca. +25 % (realtid) / ca. +30 % (orakel), men det skoen brugte
  (i) kvartalsvise refits og (ii) en FAST basisrate paa 18,0 % (dagens) for alle historiske raekker — ikke den
  basisrate, der var i kraft paa logningstidspunktet. Her reproduceres skoennet foerst og korrigeres derefter
  trin for trin til noeglens konstruktion.

HVAD BEREGNES (snapshot data/raw/2026-09-19, R_score = 2026-09, L = 18 — samme som manifest 72c3371d)
  En maanedlig walk-forward-replay af, hvad hovedbogen ville have vist historisk:
    - Raekker: een pr. logningsmaaned. Origin = maaneden foer logningsmaaneden; input = maanedstallet
      GS10 - TB3MS for origin-maaneden (som raekke 1-3 og kolonnen P_maanedlig); vindue = logningsmaaneden
      + 11 maaneder (noeglen (b)); Y = 1 hvis en NBER-onset (foerste USREC=1-maaned) ligger i vinduet (c).
    - Kalibreringer: ekspanderende refits HVER SEPTEMBER (RAADETS_V501 §3.2a) med finalize6.fit_model
      (§3.5: kun modne origins, vinduets slut + 18 mdr <= R; origins i annonceret recession ude; labels pr. R),
      frosne vaegte, standardisering og basisrate til naeste september; P beregnes som motor gaar (p_af paa de
      afrundede manifestvaegte). Foerste kalibrering = foerste september med >= 60 origins og >= 6 positive
      (walk-forwardens egne minimumskrav). Refitten i 2026-09 skal reproducere weights.json (selvtjek).
    - Loggede basisrate: kalibreringens fit-basisrate, som den stod i kraft, da raekken blev logget (a).
    - Skill = 1 - LL(model)/LL(logget basisrate); Brier-skill mod samme basisrate (sekundaer); P som logget
      med 1 decimal (a); raa P som variant.
    - Censurering i tandem (d): REALTID — raekken scores ikke, hvis den er logget inde i en recession, hvis top
      var annonceret pr. logdagen (foerste hverdag fra den 10.; annonceringsdatoer dag-praecist fra
      nber_announcements.csv), og recessionen pr. den dags USREC-vintage stadig daekker maaneden (dvs. indtil
      bunden er annonceret — motorens i_annonceret_recession/aaben_episode-regel). ORAKEL — raekken scores
      ikke, hvis origin-maaneden ligger i en recession efter den endelige kronologi (som den publicerede wf).
      Pre-1979-onsets: konventionen trough + 18 mdr (ablation2.PRE1979_TROUGH_LAG) — de er derfor aldrig
      realtids-censurerede (samme behandling som diagnostik 4.5).
    - Pr. cyklusblok (bund til bund, noeglen (g)): n, positive, skill, middel log-loss-gevinst, max P;
      cluster-robust t paa blokkene (deskriptivt — noeglen (h) forbyder en dom foer 3 komplette blokke).
    - Historiske 5-, 10- og 20-aars hovedboeger (start hvert aar): fordeling af skill under noeglen.
    - Afstemning med reviewet: pw_keys-konstruktionen reproduceres eksakt, og hvert trin til noeglens
      konstruktion (september-refits, logget basisrate, P med 1 decimal, motorens realtidsregel) vises.
    - Varianter: censur paa logningsmaaneden i stedet for origin-maaneden; fast 18,0 %; poolet basisrate;
      §3.2b-udloeste refits (naeste logning efter hver annoncering) oven i september.

DESIGN
  Rent laesende: genbruger kaedens egne funktioner (calibrate.read_fred, ablation2_nber.build_dataset/
  eligible_fit/load_announcements/laes_annonceringer, finalize6.fit_model/p_af) uden at kalde noget, der
  skriver. Ingen stokastik (ingen bootstrap); np.random.seed(42) saettes kun for form. Ingen vaegur i
  resultatet ud over created_utc. Kun stdlib + numpy. `--check` koerer beregningen to gange og sammenligner.

AENDRER INTET I DRIFT: skriver kun analyser/hovedbog_reference_resultat.json. Roerer hverken weights.json,
  manifester, hovedbog, diagnostik.json, noeglen eller nogen protokolkonstant. Fakta og tal til raadets
  dagsorden 2027 — ingen beslutning, ingen dom.

Koer:  cd v5 && python analyser/hovedbog_reference.py [--check]
"""
import json, sys
from datetime import date, datetime, timezone, timedelta
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent          # v5/analyser
V5 = HERE.parent                                # v5
sys.path.insert(0, str(V5))

import numpy as np                              # noqa: E402
import calibrate as C                           # noqa: E402
import ablation2_nber as A2                     # noqa: E402
import finalize6 as F6                          # noqa: E402

SNAPSHOT = "2026-09-19"          # kalibreringen i drift (manifest 72c3371d, refit_maaned 2026-09)
SNAP = V5 / "data" / "raw" / SNAPSHOT
R_SCORE = A2.midx(2026, 9)
L = A2.L_EMBARGO
MIN_N, MIN_POS = 60, 6           # walk-forwardens minimumskrav (ablation2.wf_nber)
CLIP = 1e-6                      # som calibrate.metrics
B_FAST = 0.1798                  # weights.json base_rate (reviewets "logget18" brugte 0.18)
VINDUER_AAR = (5, 10, 20)
UD = HERE / "hovedbog_reference_resultat.json"
PUBLICERET = dict(wf_curve_only=27.05, wf_brier=24.15, n=198, diag45_alle=20.37, diag45_brier=16.19, diag45_n=219,
                  review_realtid=25.0, review_orakel=30.2)


def ym(m):
    return f"{m // 12}-{m % 12 + 1:02d}"


def logdag(m_log):
    """Logdagen i maaned m_log: foerste hverdag fra og med den 10. (noeglen (i); helligdage ignoreres)."""
    d = date(m_log // 12, m_log % 12 + 1, 10)
    while d.weekday() >= 5:
        d += timedelta(days=1)
    return d


def annoncerings_datoer(eps):
    """Dag-praecise annonceringsdatoer pr. episode: peak_d[onset], trough_d[onset] (date). Pre-1979: konventionen
    trough + PRE1979_TROUGH_LAG (den 1. i maaneden) for baade top og bund — hele episoden bliver kendt paa een gang."""
    peak_d, trough_d = {}, {}
    for r in A2.laes_annonceringer():
        cy, cm = map(int, r["cycle_month"].split("-"))
        t = A2.midx(cy, cm)
        ad = date.fromisoformat(r["announcement_date"][:10])
        if r["event"].startswith("peak"):
            best = min(eps, key=lambda e: abs(e[0] - t))
            assert abs(best[0] - t) <= 2, r
            peak_d[best[0]] = ad
        elif r["event"].startswith("trough"):
            best = min(eps, key=lambda e: abs(e[1] - t))
            assert abs(best[1] - t) <= 2, r
            trough_d[best[0]] = ad
    for onset, trough in eps:
        if onset not in peak_d:
            assert onset < A2.POST1979, ym(onset)
            k = trough + A2.PRE1979_TROUGH_LAG
            peak_d[onset] = trough_d[onset] = date(k // 12, k % 12 + 1, 1)
        assert onset in trough_d, ym(onset)
    return peak_d, trough_d


def realtid_i_recession(m, d, eps, peak_d, trough_d):
    """Ligger maaned m i en recession efter USREC-vintagen pr. dato d? En episode er kendt, naar toppen er annonceret
    <= d; den daekker [onset, trough] hvis bunden er annonceret <= d, ellers [onset, aaben) (motorens aaben_episode)."""
    for onset, trough in eps:
        if peak_d[onset] > d:
            continue
        if onset <= m and (m <= trough or trough_d[onset] > d):
            return True
    return False


def kalibrering(D, eps, avail, usrec, R):
    """finalize6.fit_model ved refit-maaned R (§3.5), eller None hvis walk-forwardens minimumskrav ikke er opfyldt."""
    elig, yR = A2.eligible_fit(D, eps, avail, usrec, R)
    if elig.sum() < MIN_N or yR[elig].sum() < MIN_POS:
        return None
    m = F6.fit_model(D, eps, avail, usrec, R)
    return dict(R=int(R), refit=ym(R), n_obs=m["n_obs"], n_pos=m["n_pos"], base_rate=m["base_rate"],
                estimering_slut=m["estimering_slut"], w=m["w"], mu=m["mu"], sd=m["sd"],
                beta_pr_pp=m["raa"]["beta_curve_pr_pp"], alpha=m["raa"]["alpha"], features=m["features"])


def byg_raekker(curve_m, kal, eps, usrec, avail, peak_d, trough_d):
    """Een hovedbogsraekke pr. logningsmaaned under kalibreringsplanen `kal` ({R: model}); kun modne labels."""
    Rs = sorted(kal)
    rows = []
    for m in sorted(curve_m):
        m_log = m + 1
        if m + 12 + L > R_SCORE:
            continue                                   # umoden label: ingen score (§3.5)
        R = max((r for r in Rs if r <= m_log), default=None)
        if R is None:
            continue
        mod = kal[R]
        p = F6.p_af(mod, {"curve": curve_m[m]})
        onsets = [o for o, _ in eps if m + 1 <= o <= m + 12]
        d = logdag(m_log)
        ep = A2.episode_of(m, eps)
        rows.append(dict(
            m=int(m), origin=ym(m), logget=ym(m_log), R=int(R), kurve=round(float(curve_m[m]), 4),
            p=float(p), p_logget=round(p * 100, 1) / 100, b=float(mod["base_rate"]),
            Y=1.0 if onsets else 0.0, onset=ym(onsets[0]) if onsets else None,
            orakel_origin=usrec.get(m, 0) == 1, orakel_log=usrec.get(m_log, 0) == 1,
            realtid_origin=realtid_i_recession(m, d, eps, peak_d, trough_d),
            realtid_log=realtid_i_recession(m_log, d, eps, peak_d, trough_d),
            realtid_45=bool(usrec.get(m, 0) == 1 and ep and avail[ep[0]] <= m),   # diagnostik 4.5's regel (maanedsgranulaer, endelig bund)
            # noeglen (c): ville et provisorisk 0 vaere afgjort FOER annonceringen af onset i vinduet?
            afgjort_0_foer_annoncering=bool(onsets and peak_d[onsets[0]] > logdag(m + 12 + L + 1)),
        ))
    return rows


def score(rows, p_key="p_logget", basis="logget", b_fast=B_FAST):
    """Noeglens metrik: LL-skill og Brier-skill mod raekkens loggede basisrate (eller fast/poolet som variant)."""
    if not rows:
        return dict(n=0, n_pos=0, skill_LL=None, skill_brier=None)
    p = np.clip(np.array([r[p_key] for r in rows], float), CLIP, 1 - CLIP)
    y = np.array([r["Y"] for r in rows], float)
    if basis == "logget":
        b = np.array([r["b"] for r in rows], float)
    elif basis == "fast":
        b = np.full(len(rows), b_fast)
    else:                                              # poolet, ex post (publiceret definition)
        if y.mean() in (0.0, 1.0):
            return dict(n=len(rows), n_pos=int(y.sum()), skill_LL=None, skill_brier=None,
                        note="udefineret: poolet basisrate 0/1")
        b = np.full(len(rows), y.mean())
    b = np.clip(b, CLIP, 1 - CLIP)
    Lm = -(y * np.log(p) + (1 - y) * np.log(1 - p))
    L0 = -(y * np.log(b) + (1 - y) * np.log(1 - b))
    bm, b0 = (p - y) ** 2, (b - y) ** 2
    return dict(n=len(rows), n_pos=int(y.sum()), LL_model=round(float(Lm.mean()), 4), LL_basis=round(float(L0.mean()), 4),
                skill_LL=round(float((1 - Lm.mean() / L0.mean()) * 100), 2),
                skill_brier=round(float((1 - bm.mean() / b0.mean()) * 100), 2),
                middel_d=round(float((L0 - Lm).mean()), 4), sum_L0=round(float(L0.sum()), 3), sum_Lm=round(float(Lm.sum()), 3),
                max_p=round(float(max(r[p_key] for r in rows)), 3))


def tab_pr_raekke(r, p_key="p_logget"):
    p = min(max(r[p_key], CLIP), 1 - CLIP)
    b = min(max(r["b"], CLIP), 1 - CLIP)
    y = r["Y"]
    return (-(y * np.log(b) + (1 - y) * np.log(1 - b)), -(y * np.log(p) + (1 - y) * np.log(1 - p)))


def tandem(rows, cens_realtid="realtid_origin", cens_orakel="orakel_origin", **kw):
    """De to noegle-varianter, tolket i tandem (noeglen (d), V501 §4.5)."""
    rt = [r for r in rows if not r[cens_realtid]]
    ok = [r for r in rows if not r[cens_orakel]]
    return dict(realtid=score(rt, **kw), orakel=score(ok, **kw))


def blokke_bund_til_bund(rows, eps, p_key="p_logget"):
    """Cyklusblokke bund til bund (noeglen (g)) paa origin-maaneden; realtid og orakel pr. blok."""
    troughs = sorted(t for _, t in eps)
    m0, m1 = rows[0]["m"], rows[-1]["m"]
    graenser = [t for t in troughs if m0 <= t <= m1]
    kanter = [m0 - 1] + graenser + [m1]
    ud = []
    for k, (a, b) in enumerate(zip(kanter[:-1], kanter[1:])):
        if b <= a:
            continue
        rs = [r for r in rows if a < r["m"] <= b]
        if not rs:
            continue
        ons = [o for o, t in eps if a < o <= b]
        foregaaende_bund = max((t for t in troughs if t <= a), default=None)
        status = ("aaben (ingen onset endnu)" if not ons else
                  "delvis (starter efter forrige bund)" if (foregaaende_bund is None or a != foregaaende_bund) else "komplet")
        rt = [r for r in rs if not r["realtid_origin"]]
        ok = [r for r in rs if not r["orakel_origin"]]
        sidste_foer = None
        if ons:
            foer = [r for r in rt if r["m"] < ons[0]]
            if foer:
                sidste_foer = dict(origin=foer[-1]["origin"], p=round(foer[-1][p_key], 3))
        ud.append(dict(blok=k, maaneder=f"{ym(a + 1)}..{ym(b)}", onset=ym(ons[0]) if ons else None, status=status,
                       n_raekker=len(rs), realtid=score(rt, p_key=p_key), orakel=score(ok, p_key=p_key),
                       sidste_raekke_foer_onset=sidste_foer))
    return ud


def cluster_t(rows, eps, cens_key, p_key="p_logget", kun_komplette=None):
    """Cluster-robust t for middel(L0 - Lm) paa bund-til-bund-blokke (noeglen (g)); df = K - 1. Deskriptivt."""
    troughs = sorted(t for _, t in eps)
    rs = [r for r in rows if not r[cens_key]]
    if kun_komplette:
        rs = [r for r in rs if any(a < r["m"] <= b for a, b in kun_komplette)]
    if not rs:
        return dict(n=0)
    d = np.array([l0 - lm for l0, lm in (tab_pr_raekke(r, p_key) for r in rs)])
    g = np.array([sum(1 for t in troughs if t < r["m"]) for r in rs])
    keys = np.unique(g)
    K = len(keys)
    dbar = float(d.mean())
    S = np.array([d[g == k].sum() - (g == k).sum() * dbar for k in keys])
    se = float(np.sqrt((S ** 2).sum() * (K / (K - 1) if K > 1 else 1.0)) / len(d))
    return dict(n=len(rs), K_blokke=int(K), middel_d=round(dbar, 4), se_cluster=round(se, 4),
                t=round(dbar / se, 2) if se > 0 else None, df=int(K - 1))


def vinduer(rows, W, cens_key, p_key="p_logget"):
    """Historiske W-aars hovedboeger (start hvert aar, paa logningsmaaneden): skill under noeglen."""
    ms = sorted(r["m"] + 1 for r in rows)
    ud = []
    s = ms[0]
    while s + 12 * W - 1 <= ms[-1]:
        rs = [r for r in rows if s <= r["m"] + 1 < s + 12 * W and not r[cens_key]]
        sc = score(rs, p_key=p_key)
        ud.append(dict(start=ym(s), n=sc["n"], n_pos=sc["n_pos"], skill_LL=sc["skill_LL"], skill_brier=sc.get("skill_brier")))
        s += 12
    sk = np.array([v["skill_LL"] for v in ud if v["skill_LL"] is not None], float)
    return dict(n_vinduer=len(ud), kvantiler_10_50_90=[round(float(x), 1) for x in np.percentile(sk, [10, 50, 90])],
                min=round(float(sk.min()), 1), max=round(float(sk.max()), 1),
                andel_ikke_positiv=round(float(np.mean(sk <= 0)), 3),
                andel_uden_onset=round(float(np.mean([v["n_pos"] == 0 for v in ud])), 3), vinduer=ud)


def review_konstruktion(D, eps, avail, usrec, curve_m):
    """pw_keys.py's konstruktion, eksakt: kvartalsvise refits (C.fit, uafrundede vaegte) paa wf_nber's regler, raekker
    R, R+1, R+2, raa P, fast basisrate 0,18, realtid = origin i recession OG top annonceret pr. origin-MAANEDEN
    (endelig bund), orakel = origin i recession (endelig kronologi)."""
    _, win_onsets, _ = A2.nber_labels(D, eps, usrec)
    rows = []
    for i in range(len(D["qend"])):
        if D["year"][i] < 1960:
            continue
        R = int(D["qend"][i])
        tr = []
        for j in range(i):
            if D["qend"][j] + 12 + L > R:
                continue
            ep = A2.episode_of(int(D["qend"][j]), eps)
            if ep and avail[ep[0]] <= R:
                continue
            tr.append(j)
        if len(tr) < MIN_N:
            continue
        yR = np.array([1.0 if any(avail[o] <= R for o in win_onsets[j]) else 0.0 for j in tr])
        if yR.sum() < MIN_POS:
            continue
        X = D["F"][tr]
        mu, sd = X.mean(0), X.std(0, ddof=1)
        sd[sd == 0] = 1
        w = C.fit((X - mu) / sd, yR)
        for m in (R, R + 1, R + 2):
            if m + 12 + L > R_SCORE or m not in curve_m:
                continue
            p = float(C.predict(w, (np.array([[curve_m[m]]]) - mu) / sd)[0])
            y = 1.0 if any(m + 1 <= o <= m + 12 for o, _ in eps) else 0.0
            ep = A2.episode_of(m, eps)
            inr = usrec.get(m, 0) == 1
            rows.append(dict(m=m, p=p, p_logget=round(p * 100, 1) / 100, Y=y, b=float(yR.mean()),
                             orakel_origin=inr, realtid_45=bool(inr and ep and avail[ep[0]] <= m)))
    return rows


def beregn():
    np.random.seed(42)                                 # kun for form: ingen stokastik i analysen
    usrec = A2.load_usrec(SNAP)
    eps = A2.episodes_from_usrec(usrec)
    avail = A2.load_announcements(eps, usrec=usrec)
    peak_d, trough_d = annoncerings_datoer(eps)
    D = A2.build_dataset(SNAP, ["curve"])
    W = json.loads((V5 / "weights.json").read_text(encoding="utf-8"))

    # maanedlig kurve: GS10 - TB3MS pr. maaned (samme kilde som kvartalspanelets feature i kvartalets sidste maaned)
    gs10, tb3 = C.read_fred(SNAP, "GS10"), C.read_fred(SNAP, "TB3MS")
    curve_m = {A2.midx(y, mo): gs10[(y, mo)] - tb3[(y, mo)] for (y, mo) in gs10 if (y, mo) in tb3}
    diffs = [abs(float(D["F"][j, 0]) - curve_m[int(D["qend"][j])]) for j in range(len(D["qend"]))
             if D["year"][j] >= 1960 and int(D["qend"][j]) in curve_m]
    assert max(diffs) < 1e-9, max(diffs)
    selvtjek = dict(max_abs_diff_kvartal_vs_maaned=float(max(diffs)))

    # selvtjek: den publicerede kvartalsvise walk-forward
    ref, _, _ = A2.wf_nber(D, eps, avail, usrec, L, R_score=R_SCORE)
    ll, bl, imp, br = C.metrics(ref)
    selvtjek["wf_kvartal"] = dict(n=len(ref), skill_LL=round(imp, 2), skill_brier=round(br, 2))
    assert abs(imp - PUBLICERET["wf_curve_only"]) < 0.01, imp

    # kalibreringsplan A: hver september (§3.2a)
    kal_sep = {}
    for y in range(1955, 2027):
        k = kalibrering(D, eps, avail, usrec, A2.midx(y, 9))
        if k:
            kal_sep[k["R"]] = k
    k26 = kal_sep[A2.midx(2026, 9)]
    assert k26["w"] == W["op"]["w"] and k26["n_obs"] == W["n_obs"] and abs(k26["base_rate"] - W["base_rate"]) < 1e-9, k26
    selvtjek["refit_2026_09_reproducerer_weights_json"] = True
    selvtjek["weights_json"] = dict(manifest=W.get("manifest_hash"), w=W["op"]["w"], n_obs=W["n_obs"], base_rate=W["base_rate"])

    # kalibreringsplan B: september + §3.2b-udloeste refits ved naeste logning efter hver annoncering (top og bund)
    trig = set()
    for onset, _ in eps:
        for ad in (peak_d[onset], trough_d[onset]):
            m_log = A2.midx(ad.year, ad.month)
            if ad > logdag(m_log):
                m_log += 1
            trig.add(m_log)
    kal_trig = dict(kal_sep)
    for R in sorted(trig):
        if R in kal_trig or R > R_SCORE:
            continue
        k = kalibrering(D, eps, avail, usrec, R)
        if k:
            kal_trig[R] = k

    rows = byg_raekker(curve_m, kal_sep, eps, usrec, avail, peak_d, trough_d)
    rows_trig = byg_raekker(curve_m, kal_trig, eps, usrec, avail, peak_d, trough_d)
    for k in kal_sep.values():
        gov = [r for r in rows if r["R"] == k["R"]]
        k["raekker_logget"] = f"{gov[0]['logget']}..{gov[-1]['logget']}" if gov else None
        k["n_raekker"] = len(gov)

    # ---- referencetallet (noeglens konstruktion, primaer) ----
    primaer = tandem(rows)
    for navn, cens in (("realtid", "realtid_origin"), ("orakel", "orakel_origin")):
        primaer[navn]["cluster_t_alle_blokke"] = cluster_t(rows, eps, cens)
    blokke = blokke_bund_til_bund(rows, eps)
    komplette = []
    troughs = sorted(t for _, t in eps)
    for b in blokke:
        if b["status"] == "komplet":
            a0 = A2.midx(*map(int, b["maaneder"][:7].split("-"))) - 1
            b1 = A2.midx(*map(int, b["maaneder"][9:16].split("-")))
            komplette.append((a0, b1))
    for navn, cens in (("realtid", "realtid_origin"), ("orakel", "orakel_origin")):
        primaer[navn]["cluster_t_komplette_blokke"] = cluster_t(rows, eps, cens, kun_komplette=komplette)
    primaer["note"] = ("Tolkes i tandem og citeres aldrig hver for sig (V501 §4.5, noeglen (d)). Skill mod raekkens loggede "
                       "basisrate (kalibreringen i kraft), P som logget med 1 decimal, maanedsraekker, september-refits.")

    # ---- varianter ----
    varianter = dict(
        P_raa=tandem(rows, p_key="p"),
        censur_paa_logningsmaaneden=tandem(rows, cens_realtid="realtid_log", cens_orakel="orakel_log"),
        realtid_uden_aaben_episode_regel=dict(realtid=score([r for r in rows if not r["realtid_45"]]),
                                              note="diagnostik 4.5's regel paa maanedsraekker: top annonceret pr. origin-maaneden, endelig bund"),
        basisrate_fast_18=tandem(rows, basis="fast"),
        basisrate_poolet_ex_post=tandem(rows, basis="poolet"),
        refits_september_plus_annoncering=tandem(rows_trig) | dict(n_refits=len(kal_trig), n_refits_september=len(kal_sep),
                                                                  udloeste_refits=[ym(R) for R in sorted(kal_trig) if R not in kal_sep]),
    )

    # ---- afstemning med reviewet (pw_keys.py) ----
    rv = review_konstruktion(D, eps, avail, usrec, curve_m)
    rv_rt = [r for r in rv if not (r["orakel_origin"] and r["realtid_45"])]
    rv_ok = [r for r in rv if not r["orakel_origin"]]
    trin = []
    trin.append(dict(trin=0, konstruktion="reviewet (pw_keys): kvartalsrefits, raa P, fast 0,18, realtid = 4.5-regel pr. origin-maaned",
                     realtid=score(rv_rt, p_key="p", basis="fast", b_fast=0.18), orakel=score(rv_ok, p_key="p", basis="fast", b_fast=0.18)))
    trin.append(dict(trin=1, konstruktion="+ september-refits, frosne vaegte (afrundede manifestvaegte som motor)",
                     realtid=score([r for r in rows if not r["realtid_45"]], p_key="p", basis="fast", b_fast=0.18),
                     orakel=score([r for r in rows if not r["orakel_origin"]], p_key="p", basis="fast", b_fast=0.18)))
    trin.append(dict(trin=2, konstruktion="+ logget basisrate (kalibreringen i kraft) i stedet for fast 0,18",
                     realtid=score([r for r in rows if not r["realtid_45"]], p_key="p"),
                     orakel=score([r for r in rows if not r["orakel_origin"]], p_key="p")))
    trin.append(dict(trin=3, konstruktion="+ P som logget med 1 decimal",
                     realtid=score([r for r in rows if not r["realtid_45"]]),
                     orakel=score([r for r in rows if not r["orakel_origin"]])))
    trin.append(dict(trin=4, konstruktion="+ motorens realtidsregel (dag-praecis annoncering pr. logdag, aaben episode indtil bunden er annonceret) = noeglen",
                     realtid=primaer["realtid"] | {}, orakel=primaer["orakel"] | {}))
    for t in trin:
        for k in ("realtid", "orakel"):
            t[k] = {kk: vv for kk, vv in t[k].items() if kk in ("n", "n_pos", "skill_LL", "skill_brier")}
    review_repro = dict(realtid_LL=trin[0]["realtid"]["skill_LL"], orakel_LL=trin[0]["orakel"]["skill_LL"],
                        review_oplyste=dict(realtid=PUBLICERET["review_realtid"], orakel=PUBLICERET["review_orakel"]),
                        reproduceret=(abs(trin[0]["realtid"]["skill_LL"] - PUBLICERET["review_realtid"]) < 0.1
                                      and abs(trin[0]["orakel"]["skill_LL"] - PUBLICERET["review_orakel"]) < 0.1))

    # ---- de maaneder, der skiller de to varianter ----
    ekstra = [r for r in rows if not r["realtid_origin"] and r["orakel_origin"]]       # scoret i realtid, censureret af oraklet
    aabne = [r for r in rows if r["realtid_origin"] and not r["orakel_origin"]]        # censureret live (bund endnu ikke annonceret), scoret af oraklet
    def liste(rs):
        ud = []
        for r in rs:
            l0, lm = tab_pr_raekke(r)
            ud.append(dict(origin=r["origin"], logget=r["logget"], p=round(r["p_logget"], 3), Y=r["Y"], b=r["b"],
                           L0=round(float(l0), 3), Lm=round(float(lm), 3)))
        return ud
    def pr_episode(rs):
        ud = {}
        for r in rs:
            ep = A2.episode_of(r["m"], eps) or next(((o, t) for o, t in eps if t < r["m"] and not any(o2 <= r["m"] <= t2 for o2, t2 in eps)), None)
            key = ym(ep[0]) if ep else "?"
            ud.setdefault(key, []).append(r)
        return {k: dict(n=len(v), n_pos=int(sum(r["Y"] for r in v)), max_p=round(max(r["p_logget"] for r in v), 3),
                        sum_L0=round(float(sum(tab_pr_raekke(r)[0] for r in v)), 3), sum_Lm=round(float(sum(tab_pr_raekke(r)[1] for r in v)), 3),
                        maaneder=f"{v[0]['origin']}..{v[-1]['origin']}") for k, v in ud.items()}
    # aabne-episode-raekker: tilhoerer episoden hvis bund netop er passeret
    def episode_for_aaben(r):
        return ym(max((o for o, t in eps if t < r["m"]), key=lambda o: o))
    aabne_pr_ep = {}
    for r in aabne:
        aabne_pr_ep.setdefault(episode_for_aaben(r), []).append(r)
    aabne_tabel = {k: dict(n=len(v), n_pos=int(sum(r["Y"] for r in v)), max_p=round(max(r["p_logget"] for r in v), 3),
                           sum_L0=round(float(sum(tab_pr_raekke(r)[0] for r in v)), 3), sum_Lm=round(float(sum(tab_pr_raekke(r)[1] for r in v)), 3),
                           maaneder=f"{v[0]['origin']}..{v[-1]['origin']}") for k, v in aabne_pr_ep.items()}
    skillelinjer = dict(
        additional_live_publishable_maaneder=dict(
            n=len(ekstra), n_pos=int(sum(r["Y"] for r in ekstra)), max_p=round(max(r["p_logget"] for r in ekstra), 3),
            sum_L0=round(float(sum(tab_pr_raekke(r)[0] for r in ekstra)), 3), sum_Lm=round(float(sum(tab_pr_raekke(r)[1] for r in ekstra)), 3),
            pr_episode=pr_episode(ekstra), raekker=liste(ekstra),
            note="raekker logget i en recession, der endnu ikke var annonceret: scores i realtid (typisk Y=0), censureres af oraklet — maanedsanalogen til 4.5's 21 origins"),
        aaben_episode_censur=dict(
            n=len(aabne), n_pos=int(sum(r["Y"] for r in aabne)), max_p=round(max(r["p_logget"] for r in aabne), 3) if aabne else None,
            pr_episode=aabne_tabel, raekker=liste(aabne), skill_hvis_scoret=score(aabne),
            note="raekker efter den endelige bund men foer bundens annoncering: motorens dom 'censureret' (USREC-vintagen viser stadig recession), "
                 "men oraklet (og diagnostik 4.5) scorer dem. Heri de 12 positive origins foer 1981-08-onset (bunden 1980-07 annonceret 1981-07-08)."),
        noeglen_c_provisorisk_0_foer_annoncering=dict(
            n=sum(r["afgjort_0_foer_annoncering"] for r in rows),
            raekker=[r["origin"] for r in rows if r["afgjort_0_foer_annoncering"]],
            note="raekker med onset i vinduet, hvor noeglens (c) ville have afgjort Y=0 (vinduets slut + 18 passeret), FOER 'annonceringen' — "
                 "kun pre-1979-onsets under trough+18-konventionen. Replayet bruger den endelige label (noeglens hensigt)."),
    )

    # ---- vinduer ----
    vin = {f"{W_}_aar": dict(realtid=vinduer(rows, W_, "realtid_origin"), orakel=vinduer(rows, W_, "orakel_origin")) for W_ in VINDUER_AAR}

    # ---- P-fordeling og raekkeoversigt ----
    P = np.array([r["p_logget"] for r in rows])
    oversigt = dict(n_raekker=len(rows), foerste_logget=rows[0]["logget"], sidste_logget=rows[-1]["logget"],
                    foerste_origin=rows[0]["origin"], sidste_origin=rows[-1]["origin"],
                    n_pos=int(sum(r["Y"] for r in rows)), n_censureret_realtid=int(sum(r["realtid_origin"] for r in rows)),
                    n_censureret_orakel=int(sum(r["orakel_origin"] for r in rows)),
                    onsets_i_vinduer=sorted({r["onset"] for r in rows if r["onset"]}),
                    P_kvantiler_10_25_50_75_90=[round(float(x), 3) for x in np.percentile(P, [10, 25, 50, 75, 90])],
                    logget_basisrate_spaend=[min(r["b"] for r in rows), max(r["b"] for r in rows)],
                    n_kalibreringer_med_raekker=sum(1 for k in kal_sep.values() if k["n_raekker"]),
                    modenhed="m + 12 + 18 <= 2026-09 (som wf_nber/4.5); sidste origin 2024-03")

    return dict(
        navn="hovedbog_reference", fund="G3.5 (kode-review 2026-10-15) + BEDOEMMELSESNOEGLE.md §3",
        aendrer_intet_i_drift=True, snapshot=SNAPSHOT, R_score=ym(R_SCORE), L_embargo=L, min_n=MIN_N, min_pos=MIN_POS,
        konstruktion=dict(
            raekke="een pr. logningsmaaned; origin = maaneden foer; input = GS10 - TB3MS (maanedstal) for origin; vindue = logningsmaaned + 11; Y = onset i vinduet (endelig kronologi)",
            kalibrering="finalize6.fit_model hver september (R = sep), §3.5-regler, frosne afrundede vaegte til naeste september, gaelder fra septembers egen logning (--log blokeres til refitten er koert)",
            basisrate="kalibreringens fit-basisrate i kraft paa logningstidspunktet (hovedbogens kolonne)",
            metrik="skill = 1 - LL(P som logget, 1 decimal)/LL(logget basisrate); Brier-skill sekundaer; clip 1e-6",
            realtid="censureret hvis origin-maaneden ligger i en recession efter USREC-vintagen pr. logdagen (top annonceret <= logdag; episoden aaben indtil bunden er annonceret <= logdag); pre-1979: trough+18-konvention, aldrig realtids-censureret",
            orakel="censureret hvis origin-maaneden er i recession efter den endelige kronologi (som den publicerede wf)",
            logdag="foerste hverdag fra og med den 10. (helligdage ignoreres)",
            blokke="bund til bund (noeglen (g)); foerste blok er delvis (ledgeren starter 1968, ikke ved bunden 1961-02), sidste er aaben",
        ),
        selvtjek=selvtjek,
        sammenligning=dict(publiceret_wf=PUBLICERET["wf_curve_only"], publiceret_brier=PUBLICERET["wf_brier"], publiceret_n=PUBLICERET["n"],
                           diagnostik_45_alle_live=PUBLICERET["diag45_alle"], diagnostik_45_brier=PUBLICERET["diag45_brier"], diagnostik_45_n=PUBLICERET["diag45_n"],
                           review_pw_keys=dict(realtid=PUBLICERET["review_realtid"], orakel=PUBLICERET["review_orakel"],
                                               note="kvartalsrefits + fast 0,18 for alle raekker — ikke noeglens 'loggede basisrate'")),
        oversigt=oversigt, referencetal=primaer, varianter=varianter,
        afstemning_med_review=dict(review_reproduceret=review_repro, trin=trin),
        blokke=blokke, vinduer=vin, skillelinjer=skillelinjer,
        kalibreringer=[{k: v for k, v in kal.items()} for kal in kal_sep.values()],
    )


def main():
    res = beregn()
    if "--check" in sys.argv:
        res2 = beregn()
        assert json.dumps(res, sort_keys=True) == json.dumps(res2, sort_keys=True), "IKKE deterministisk"
        print("DETERMINISME: OK — to beregninger identiske")
    r = res["referencetal"]
    o = res["oversigt"]
    print(f"=== hovedbog_reference — snapshot {SNAPSHOT}, R_score {res['R_score']}, L={L} — aendrer intet i drift ===")
    print(f"selvtjek: kvartal-wf +{res['selvtjek']['wf_kvartal']['skill_LL']}% ({res['selvtjek']['wf_kvartal']['n']}); refit 2026-09 == weights.json: "
          f"{res['selvtjek']['refit_2026_09_reproducerer_weights_json']}; max|kvartal-maaned| {res['selvtjek']['max_abs_diff_kvartal_vs_maaned']:.1e}")
    print(f"raekker: {o['n_raekker']} logget {o['foerste_logget']}..{o['sidste_logget']} (origins {o['foerste_origin']}..{o['sidste_origin']}), "
          f"{o['n_pos']} positive, {len(o['onsets_i_vinduer'])} onsets; censureret realtid {o['n_censureret_realtid']} / orakel {o['n_censureret_orakel']}; "
          f"{o['n_kalibreringer_med_raekker']} september-kalibreringer; logget basisrate {o['logget_basisrate_spaend'][0]*100:.1f}-{o['logget_basisrate_spaend'][1]*100:.1f}%")
    print("\nREFERENCETAL (noeglens egne regler, tolkes i tandem):")
    for k in ("realtid", "orakel"):
        s = r[k]
        ct, ck = s["cluster_t_alle_blokke"], s["cluster_t_komplette_blokke"]
        print(f"  {k:<8} n={s['n']:>4} pos={s['n_pos']:>3}  LL-skill {s['skill_LL']:+6.2f}%  Brier-skill {s['skill_brier']:+6.2f}%  "
              f"middel d={s['middel_d']:.4f}  cluster-t {ct['t']} (K={ct['K_blokke']}) / komplette blokke {ck['t']} (K={ck['K_blokke']})")
    print(f"  (publiceret wf +{PUBLICERET['wf_curve_only']}% | diagnostik 4.5 +{PUBLICERET['diag45_alle']}% | review +{PUBLICERET['review_realtid']}/+{PUBLICERET['review_orakel']}%)")
    print("\nAFSTEMNING MED REVIEWET (LL-skill realtid / orakel):")
    for t in res["afstemning_med_review"]["trin"]:
        print(f"  trin {t['trin']}: {t['realtid']['skill_LL']:+6.2f}% / {t['orakel']['skill_LL']:+6.2f}%  (n {t['realtid']['n']}/{t['orakel']['n']})  {t['konstruktion']}")
    print(f"  reviewets tal reproduceret: {res['afstemning_med_review']['review_reproduceret']['reproduceret']}")
    print("\nVARIANTER (LL realtid / orakel):")
    for k, v in res["varianter"].items():
        rt = v.get("realtid", {}).get("skill_LL"); ok = v.get("orakel", {}).get("skill_LL")
        srt = "-" if rt is None else f"{rt:+.2f}%"; sok = "-" if ok is None else f"{ok:+.2f}%"
        print(f"  {k:<36} {srt:>8} / {sok:>8}")
    print("\nCYKLUSBLOKKE (bund til bund; LL-skill realtid / orakel, n, max P):")
    for b in res["blokke"]:
        rt, ok = b["realtid"], b["orakel"]
        print(f"  {b['maaneder']}  onset {b['onset'] or '-':<8} {b['status']:<36} {rt.get('skill_LL')!s:>7} / {ok.get('skill_LL')!s:>7}  "
              f"n {rt['n']}/{ok['n']}  maxP {rt.get('max_p')}")
    print("\nHISTORISKE HOVEDBOEGER (LL-skill, kvantiler 10/50/90, andel <= 0, andel uden onset):")
    for W_, v in res["vinduer"].items():
        for k in ("realtid", "orakel"):
            x = v[k]
            print(f"  {W_:<7} {k:<8} {x['n_vinduer']:>3} vinduer  {x['kvantiler_10_50_90']}  min {x['min']}  <=0: {x['andel_ikke_positiv']}  uden onset: {x['andel_uden_onset']}")
    sk = res["skillelinjer"]
    print(f"\nskillelinjer: additional live-publishable maaneder {sk['additional_live_publishable_maaneder']['n']} (pos {sk['additional_live_publishable_maaneder']['n_pos']}, "
          f"max P {sk['additional_live_publishable_maaneder']['max_p']}); aaben-episode-censur {sk['aaben_episode_censur']['n']} maaneder "
          f"(pos {sk['aaben_episode_censur']['n_pos']}); noeglen (c) provisorisk 0 foer annoncering: {sk['noeglen_c_provisorisk_0_foer_annoncering']['n']} (kun pre-1979)")
    ud = dict(created_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"), **res)
    UD.write_text(json.dumps(ud, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"\n{UD.relative_to(V5)} skrevet.")


if __name__ == "__main__":
    main()
