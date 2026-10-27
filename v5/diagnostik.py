#!/usr/bin/env python3
"""
diagnostik.py — RAADETS_V501 §4 (+ §3.6-erklaering, §7.3): diagnostik der printes ved siden af
laesningen og ALDRIG aendrer gate, vaegte eller dom.

  4.1 Episode-tabel: een raekke pr. onset MED scorede origins (8 — de 4 onsets 1948-1960 ligger
      foer foerste scorede origin 1960 og har ingen; erklaeret afvigelse fra §4.1's '12', F52) + een
      raekke med alle negative origins; additivt bidrag 100*sum(L0-Lm)/sum(L0) der summerer eksakt
      til den poolede forbedring; negative ogsaa pr. kronologisk bootstrap-blok.
  4.2 LOEO: walk-forward hvor blok k er udelukket fra traeningen naar blok k scores (ingen
      fremtidsdata, eksplicit udelukkelse) — sensitivitet, aldrig co-primaer. 7 blokke: 1970-blokken
      udgaar, fordi traeningen uden den har < 60 raekker eller < 6 positive; 1981-blokken har kun positive
      origins (udefineret skill), saa medianen er over 6 definerede blokke.
  4.3 Backtest af begge domsregler over hele walk-forward'en, samme origins, samme
      bootstrap-struktur (seed 42, episodeblokke): baandreglen (P-baand indeholder traenings-
      basisraten) vs den parrede regel (baand af P_b - base_b indeholder 0). Uenigheder listes.
  4.4 Historisk parret loss-bootstrap (Gemini): blok-bootstrap af middel(L0 - Lm) over blokkene.
  4.5 Oracle-fri supplement: censurering kun efter annonceringstabellen SOM AF origin-datoen,
      modellens egen label, kun modne labels, baseline paa samme daekning; printet TO gange
      (alle live-publicerbare origins / eksklusive de 'additional live-publishable origins').
  §3.6 Erklaeret fejl: publiceret baseline er den POOLEDE basisrate; expanding-intercept-
      versionen printes som ekstra kolonne.
  §7.3 Skill paa faelles origins (<= 2023Q2) og tilfoejede origins hver for sig + trunkeret panel.

Tilfoejet efter kode-review 2026-10-15 (alt diagnostik, aendrer intet):
  sti     P-stien foer hvert scoret onset (F11): P ved sidste origin, top, fald fra top, maaneder fra
          top til onset — tallene bag motorens sti-advarsel; 2007Q4-analogen med baand og dom.
  start   P og basisrate ved universstart 1953Q2 og 1960Q1 mod protokolkonstanten 1947Q2 (F34).
  flips   provisoriske nuller der senere blev et ved L = 12/18/24 (blueprint §1, G1.8) og Kimis R6:
          effektivt episodeantal pr. origin og skill med/uden nyeste episode.
  styrke  hovedbogens styrke (G3.2): cluster-t paa cyklusblokke, parametrisk skaleret fra 4.4.

R og snapshot tages fra kalibreringen i drift (weights.json: refit_maaned/snapshot), ikke fra
nyeste snapshot (F26). Et snapshot hvis rygrad ikke er refit-klar afvises (F5).
Skriver diagnostik.json (laeses af motor.py). Kun stdlib + numpy.
Koer:  python diagnostik.py [--snapshot ...] [--hurtig]   (--hurtig: 200 traek i 4.3)
"""
import json, sys, time, warnings
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

import calibrate as C
import ablation2_nber as A2
import finalize6 as F6
import protokol2027 as P27

HERE = Path(__file__).parent
L = A2.L_EMBARGO
SEED = 42


def loss(p, y):
    p = min(max(p, 1e-6), 1 - 1e-6)
    return -(y * np.log(p) + (1 - y) * np.log(1 - p))


def wf(D, eps, avail, usrec, R_score, start=1960, censur="endelig", exclude_rows=None, boot=0, rng=None):
    """Walk-forward som A2.wf_nber, men returnerer rige poster og understoetter varianter.
    censur='endelig': origin scores ikke hvis inde i recession (endelig kronologi) — som wf_nber.
    censur='realtid': origin scores ikke KUN hvis recessionen var annonceret pr. origin (§4.5).
    exclude_rows: raekker der aldrig indgaar i traening (LOEO). boot>0: episodeblok-bootstrap
    af traeningssaettet ved hvert origin (§4.3) -> P_b og base_b pr. traek."""
    Y_final, win_onsets, in_rec_final = A2.nber_labels(D, eps, usrec)
    n = len(D["qend"])
    ex = exclude_rows or set()
    out = []
    for i in range(n):
        if D["year"][i] < start or D["qend"][i] + 12 + L > R_score:
            continue
        R = D["qend"][i]
        tr = []
        for j in range(i):
            if j in ex or D["qend"][j] + 12 + L > R:
                continue
            ep = A2.episode_of(int(D["qend"][j]), eps)
            if ep and avail[ep[0]] <= R:
                continue
            tr.append(j)
        if len(tr) < 60:
            continue
        yR = np.array([1.0 if any(avail[o] <= R for o in win_onsets[j]) else 0.0 for j in tr])
        if yR.sum() < 6:
            continue
        ep_i = A2.episode_of(int(R), eps)
        annonceret = bool(ep_i and avail[ep_i[0]] <= R)
        if censur == "endelig" and in_rec_final[i]:
            continue
        if censur == "realtid" and annonceret:
            continue
        X = D["F"][tr]
        mu, sd = X.mean(0), X.std(0, ddof=1); sd[sd == 0] = 1
        Z = (X - mu) / sd
        w = C.fit(Z, yR)
        x = (D["F"][[i]] - mu) / sd
        p = float(C.predict(w, x)[0])
        rec = dict(y=int(D["year"][i]), q=int(D["qk"][i][1]), p=p, Y=float(Y_final[i]),
                   base_tr=float(yR.mean()), in_rec_final=bool(in_rec_final[i]), annonceret=annonceret,
                   onsets=[int(o) for o in win_onsets[i]])
        if boot:
            qe = D["qend"][tr]
            grp = np.array([next((k for k, (o, _) in enumerate(eps) if o >= q), len(eps)) for q in qe])
            gkeys = np.unique(grp)
            Pb, Bb, tries = [], [], 0
            while len(Pb) < boot and tries < boot * 20:
                tries += 1
                rows = np.concatenate([np.where(grp == g)[0] for g in rng.choice(gkeys, size=len(gkeys), replace=True)])
                yb = yR[rows]
                if yb.sum() < 5 or yb.sum() > len(yb) - 5:
                    continue
                wb = C.fit(Z[rows], yb)
                Pb.append(float(C.predict(wb, x)[0])); Bb.append(float(yb.mean()))
            rec["Pb"] = Pb; rec["Bb"] = Bb
        out.append(rec)
    return out


def blok_af(qend, eps):
    return int(next((k for k, (o, _) in enumerate(eps) if o >= qend), len(eps)))


def skill(recs, base=None):
    """Publiceret definition: poolet basisrate over de scorede origins (C.metrics)."""
    if not recs:
        return dict(n=0)
    n_pos = int(sum(r["Y"] for r in recs))
    if n_pos in (0, len(recs)):                  # basisrate 0/1: skill mod basisraten er udefineret
        lm = float(np.mean([loss(r["p"], r["Y"]) for r in recs]))
        return dict(n=len(recs), n_pos=n_pos, logloss=round(lm, 4), baseline=None, improvement=None, brier=None,
                    note="udefineret: blokken har kun " + ("positive" if n_pos else "negative") + " origins (basisrate 0/1)")
    rows = [(r["y"], r["q"], r["p"], r["Y"]) for r in recs]
    ll, bl, imp, br = C.metrics(rows)
    return dict(n=len(recs), n_pos=int(sum(r["Y"] for r in recs)), logloss=round(ll, 4), baseline=round(bl, 4),
                improvement=round(imp, 2), brier=round(br, 2))


def parret_loss_boot(recs, eps, base):
    """4.4: per-origin log-loss-forbedring mod den poolede basisrate; episode-blok-bootstrap over cykelblokkene,
    10.000 traek, seed 42, 5.-95. percentil. -> (resultat, d, blokke)."""
    d = np.array([loss(base, r["Y"]) - loss(r["p"], r["Y"]) for r in recs])
    bl = np.array([blok_af(A2.qend_idx(r["y"], r["q"]), eps) for r in recs])
    rng = np.random.default_rng(SEED)
    keys = np.unique(bl); means = []
    for _ in range(10000):
        rows = np.concatenate([np.where(bl == g)[0] for g in rng.choice(keys, size=len(keys), replace=True)])
        means.append(d[rows].mean())
    means = np.array(means)
    return (dict(middel_pp=round(float(d.mean()), 4), interval_90=[round(float(np.percentile(means, 5)), 4), round(float(np.percentile(means, 95)), 4)],
                 andel_ikke_positiv=round(float(np.mean(means <= 0)), 4), n_blokke=int(len(keys)), n_draws=10000), d, bl)


def skill_expanding(recs):
    """§3.6: expanding-intercept-baseline (intercept-modellens egen wf-prognose = traeningsbasisraten)."""
    lm = np.mean([loss(r["p"], r["Y"]) for r in recs]); l0 = np.mean([loss(r["base_tr"], r["Y"]) for r in recs])
    return dict(improvement_expanding=round((1 - lm / l0) * 100, 2), baseline_expanding=round(float(l0), 4))


def episode_tabel(recs, eps, base):
    l0 = {id(r): loss(base, r["Y"]) for r in recs}
    lm = {id(r): loss(r["p"], r["Y"]) for r in recs}
    tot0 = sum(l0.values())
    rows = []
    for k, (o, t) in enumerate(eps):
        rs = [r for r in recs if o in r["onsets"]]
        if not rs:
            continue
        rows.append(dict(episode=f"{o // 12}-{o % 12 + 1:02d}", n=len(rs), n_pos=int(sum(r["Y"] for r in rs)),
                         sum_L0=round(sum(l0[id(r)] for r in rs), 3), sum_Lm=round(sum(lm[id(r)] for r in rs), 3),
                         bidrag_pp=round(100 * sum(l0[id(r)] - lm[id(r)] for r in rs) / tot0, 2),
                         brier=round(float(np.mean([(r["p"] - r["Y"]) ** 2 for r in rs])), 4),
                         max_p=round(max(r["p"] for r in rs), 3)))
    neg = [r for r in recs if r["Y"] == 0.0]
    rows.append(dict(episode="alle negative origins", n=len(neg), n_pos=0,
                     sum_L0=round(sum(l0[id(r)] for r in neg), 3), sum_Lm=round(sum(lm[id(r)] for r in neg), 3),
                     bidrag_pp=round(100 * sum(l0[id(r)] - lm[id(r)] for r in neg) / tot0, 2),
                     brier=round(float(np.mean([(r["p"] - r["Y"]) ** 2 for r in neg])), 4),
                     max_p=round(max(r["p"] for r in neg), 3)))
    total = round(100 * sum(l0[id(r)] - lm[id(r)] for r in recs) / tot0, 2)
    # negative pr. kronologisk blok
    blokke = {}
    for r in neg:
        b = blok_af(A2.qend_idx(r["y"], r["q"]), eps)
        blokke.setdefault(b, []).append(r)
    def blok_navn(b):
        return f"->{eps[b][0] // 12}-{eps[b][0] % 12 + 1:02d}" if b < len(eps) else "efter sidste onset"
    neg_blok = [dict(blok=blok_navn(b), n=len(rs), bidrag_pp=round(100 * sum(l0[id(r)] - lm[id(r)] for r in rs) / tot0, 2),
                     max_p=round(max(r["p"] for r in rs), 3), origins=f"{rs[0]['y']}Q{rs[0]['q']}..{rs[-1]['y']}Q{rs[-1]['q']}")
                for b, rs in sorted(blokke.items())]
    return rows, total, neg_blok


def sti_foer_onsets(recs, eps, D):
    """F11: for hvert onset med scorede origins — P ved sidste scorede origin FOER onset, toppen af P
    blandt origins i samme blok (fra forrige onset), fald fra top og maaneder fra top til onset."""
    rows = []
    for k, (o, _t) in enumerate(eps):
        foer = [r for r in recs if A2.qend_idx(r["y"], r["q"]) < o and blok_af(A2.qend_idx(r["y"], r["q"]), eps) == k]
        if not foer:
            continue
        sidste = foer[-1]
        top = max(foer, key=lambda r: r["p"])
        rows.append(dict(onset=f"{o // 12}-{o % 12 + 1:02d}", sidste_origin=f"{sidste['y']}Q{sidste['q']}",
                         p_sidste=round(sidste["p"], 3), top_origin=f"{top['y']}Q{top['q']}", p_top=round(top["p"], 3),
                         fald_pp=round(100 * (top["p"] - sidste["p"]), 1),
                         mdr_top_til_onset=int(o - A2.qend_idx(top["y"], top["q"]))))
    under = [r for r in rows if r["fald_pp"] > 0]
    return dict(raekker=rows, n_onsets=len(rows), n_under_top=len(under),
                median_fald_pp=round(float(np.median([r["fald_pp"] for r in under])), 1) if under else None,
                median_mdr_top_til_onset=int(np.median([r["mdr_top_til_onset"] for r in under])) if under else None,
                note="beskrivende historik bag sti-advarslen; ingen fremskrivning og ingen indflydelse paa P")


def start_sensitivitet(snap, eps, avail, usrec, R):
    """F34: P og basisrate hvis raekkeuniverset startede 1953Q2 eller 1960Q1 (protokolkonstanten er
    1947Q2 inkl. 24 kvartaler med Shiller-LTR i stedet for 10Y). Samme fast input som broen."""
    D0 = A2.build_dataset(snap, ["curve"])
    x = F6.live_x(snap)
    ud = {}
    for navn, st in (("1947Q2 (protokol)", (1947, 2)), ("1953Q2", (1953, 2)), ("1960Q1", (1960, 1))):
        keep = [i for i, qk in enumerate(D0["qk"]) if qk >= st]
        Ds = dict(F=D0["F"][keep], feats=D0["feats"], Y_tek=D0["Y_tek"][keep], qk=[D0["qk"][i] for i in keep],
                  qend=D0["qend"][keep], year=D0["year"][keep])
        m = F6.fit_model(Ds, eps, avail, usrec, R)
        ud[navn] = dict(P=round(F6.p_af(m, x), 4), basisrate=m["base_rate"], n_obs=m["n_obs"], w=m["w"])
    ud["input"] = {k: round(v, 4) for k, v in x.items()}
    return ud


def kimi_r6(recs, eps, D, avail, usrec):
    """Kimis R6-krav (G1.8): effektivt episodeantal i traeningssaettet pr. scoret origin, og skill med
    og uden origins fra den nyeste episode-blok."""
    n_ep = []
    q0 = int(D["qend"][0])                 # kun onsets der kan ligge i et label-vindue i raekkeuniverset (efter 1947Q2)
    for r in recs:
        R0 = A2.qend_idx(r["y"], r["q"])
        n_ep.append(sum(1 for o, _ in eps if o > q0 and avail.get(o, 10 ** 9) <= R0 and o + L <= R0))
    sidste_blok = max(blok_af(A2.qend_idx(r["y"], r["q"]), eps) for r in recs if r["Y"] == 1.0)
    uden = [r for r in recs if blok_af(A2.qend_idx(r["y"], r["q"]), eps) != sidste_blok]
    return dict(median_episoder_i_traening=int(np.median(n_ep)), min_episoder_i_traening=int(min(n_ep)),
                max_episoder_i_traening=int(max(n_ep)),
                skill_uden_nyeste_episode=skill(uden), nyeste_blok=sidste_blok,
                note="episoder = onsets efter raekkeuniversets start (1947Q2) der er annonceret og modne (onset + L <= origin); "
                     "skill_uden_nyeste_episode udelader de SCOREDE origins i den nyeste blok med en onset (scoring, ikke traening)")


def styrke_tabel(d, bl, recs):
    """G3.2: hvor mange komplette cyklusblokke skal hovedbogen have, foer en ensidet 5 %-test (cluster-t
    paa blokke) har 80 % styrke mod H0 'ingen log-loss-gevinst'? Parametrisk skalering af 4.4: blokkenes
    middelbidrag og spredning fra den historiske walk-forward. Aar = blokke x historisk middel-bloklaengde."""
    from math import erf, sqrt
    keys = np.unique(bl)
    mu = float(d.mean())
    # cluster-robust SE af middel(d) paa de historiske blokke; skaleres som sqrt(K_hist / K)
    se_hist = float(np.sqrt(sum((d[bl == g].sum() - (bl == g).sum() * mu) ** 2 for g in keys)) / len(d))
    K0 = len(keys)
    aar_pr_blok = (max(r["y"] for r in recs) - min(r["y"] for r in recs) + 1) / K0
    phi = lambda z: 0.5 * (1 + erf(z / sqrt(2)))
    styrke = lambda K: 1 - phi(1.645 - mu / (se_hist * sqrt(K0 / K))) if se_hist > 0 else 1.0
    tabel, k80 = [], None
    for K in (1, 2, 3, 5, 8, 10, 15, 20, 30, 40):
        tabel.append(dict(blokke=K, aar=round(K * aar_pr_blok), styrke=round(styrke(K), 2)))
    for K in range(1, 400):
        if styrke(K) >= 0.8:
            k80 = K
            break
    return dict(middel_d=round(mu, 4), se_cluster_historisk=round(se_hist, 4), n_blokke_historisk=int(K0),
                aar_pr_blok=round(aar_pr_blok, 1), tabel=tabel, blokke_80pct=k80,
                aar_80pct=round(k80 * aar_pr_blok) if k80 else None,
                note="ensidet 5 %, cluster-t paa cyklusblokke; iid-tests paa overlappende maanedsraekker og 4.4-bootstrap "
                     "ved faa blokke er FORBUDT (falsk signifikans). Kun til bedoemmelsesnoeglen — aendrer intet.")


def main():
    warnings.filterwarnings("ignore", category=RuntimeWarning)   # udefinerede blokke haandteres eksplicit i skill()
    t0 = time.time()
    hurtig = "--hurtig" in sys.argv
    W = json.loads((HERE / "weights.json").read_text(encoding="utf-8"))
    # F26: diagnostikken beskriver kalibreringen I DRIFT — dens snapshot og refit-maaned
    if "--snapshot" in sys.argv or not W.get("snapshot") or not (C.RAW / W["snapshot"]).exists():
        snap = C.find_snapshot(sys.argv)
        if W.get("snapshot") and snap.name != W["snapshot"]:
            print(f"ADVARSEL: snapshot {snap.name} er ikke kalibreringens ({W['snapshot']}) — diagnostikken er da ikke kalibreringens egen.")
    else:
        snap = C.RAW / W["snapshot"]
    klar, grunde = F6.rygrad_klar(snap, json.loads((snap / "meta.json").read_text(encoding="utf-8")))
    if not klar:                       # curve-only er uafhaengig af rygraden (PR #1); kun fuldmodel-dele beroeres
        print(f"ADVARSEL (F5): rygraden i {snap.name} er ikke komplet: {'; '.join(grunde)}.")
    print(f"=== diagnostik — v{W.get('version', '?')} manifest {W.get('manifest_hash', '?')} — snapshot {snap.name} ===")
    usrec = A2.load_usrec(snap); eps = A2.episodes_from_usrec(usrec); avail = A2.load_announcements(eps, usrec=usrec)
    if W.get("refit_maaned"):
        R = A2.midx(int(W["refit_maaned"][:4]), int(W["refit_maaned"][5:7]))
    else:
        R = A2.midx(int(snap.name[:4]), int(snap.name[5:7]))
    Dc = A2.build_dataset(snap, ["curve"])

    # selvtjek: standardvarianten skal give praecis wf_nber's P'er
    ref, _, _ = A2.wf_nber(Dc, eps, avail, usrec, L, R_score=R)
    recs = wf(Dc, eps, avail, usrec, R)
    assert [(r["y"], r["q"], round(r["p"], 10)) for r in recs] == [(y, q, round(p, 10)) for (y, q, p, _) in ref], "wf-varianten afviger fra wf_nber"
    S = skill(recs); base = np.mean([r["Y"] for r in recs])
    print(f"walk-forward curve-only (udvidet panel): +{S['improvement']}% paa {S['n']} origins — selvtjek mod wf_nber OK")

    # 4.1 episode-tabel
    tab, total, neg_blok = episode_tabel(recs, eps, base)
    assert abs(total - S["improvement"]) < 0.05, (total, S["improvement"])
    print(f"4.1 episode-tabel: {len(tab)} raekker, bidrag summerer til {total}pp (poolet {S['improvement']}%)")

    # 4.2 LOEO
    grp_all = {i: blok_af(int(Dc["qend"][i]), eps) for i in range(len(Dc["qend"]))}
    loeo = []
    for k in range(len(eps)):
        ex = {i for i, b in grp_all.items() if b == k}
        rk = [r for r in wf(Dc, eps, avail, usrec, R, exclude_rows=ex) if blok_af(A2.qend_idx(r["y"], r["q"]), eps) == k]
        if not rk:
            continue
        s = skill(rk)
        loeo.append(dict(blok=k, onset=f"{eps[k][0] // 12}-{eps[k][0] % 12 + 1:02d}", n=s["n"], n_pos=s["n_pos"],
                         improvement=s["improvement"], brier=s["brier"], logloss=s["logloss"], note=s.get("note")))
    imps = [x["improvement"] for x in loeo if x["improvement"] is not None]
    udef = [x["onset"] for x in loeo if x["improvement"] is None]
    print(f"4.2 LOEO: {len(loeo)} blokke ({len(imps)} definerede), median {np.median(imps):+.1f}%, min {min(imps):+.1f}%, "
          f"positive {sum(i > 0 for i in imps)}/{len(imps)}" + (f"; udefineret: {udef}" if udef else ""))

    # 4.4 historisk parret loss-bootstrap (Gemini)
    hist, d, bl = parret_loss_boot(recs, eps, base)
    print(f"4.4 parret loss-bootstrap: middel {hist['middel_pp']}, 90 %-interval {hist['interval_90']}, P(<=0) = {hist['andel_ikke_positiv']}")

    # 4.3 backtest af begge domsregler
    nb = 200 if hurtig else 1000
    rng2 = np.random.default_rng(SEED)
    rb = wf(Dc, eps, avail, usrec, R, boot=nb, rng=rng2)
    uenige, a_sk, b_sk = [], 0, 0
    for r in rb:
        Pb, Bb = np.array(r["Pb"]), np.array(r["Bb"])
        lo, hi = np.percentile(Pb, 10), np.percentile(Pb, 90)
        A = not (lo <= r["base_tr"] <= hi)                     # baandreglen: skelnelig hvis baandet udelukker basisraten
        dd = Pb - Bb
        B = not (np.percentile(dd, 10) <= 0 <= np.percentile(dd, 90))
        a_sk += A; b_sk += B
        if A != B:
            uenige.append(dict(origin=f"{r['y']}Q{r['q']}", p=round(r["p"], 3), baand=A, parret=B))
    bt = dict(n_origins=len(rb), n_draws=nb, baand_skelnelig=a_sk, parret_skelnelig=b_sk,
              uenige=len(uenige), uenighedsrate=round(len(uenige) / len(rb), 4), uenige_origins=uenige)
    # pre-onset-analogerne med baand og dom (F11): de origins hvor kurven var re-steepened og onset fulgte
    analoger = []
    for r in rb:
        if (r["y"], r["q"]) in ((2007, 4), (1990, 1), (1990, 2), (2000, 4), (2019, 4)):
            Pb = np.array(r["Pb"]); lo, hi = np.percentile(Pb, 10), np.percentile(Pb, 90)
            analoger.append(dict(origin=f"{r['y']}Q{r['q']}", p=round(r["p"], 3), baand=[round(float(lo), 3), round(float(hi), 3)],
                                 basisrate_traening=round(r["base_tr"], 3), Y=r["Y"],
                                 dom="ikke skelnelig" if lo <= r["base_tr"] <= hi else ("over basisraten" if r["p"] > r["base_tr"] else "under basisraten")))
    print(f"4.3 domsregler backtestet: {len(rb)} origins x {nb} traek — baand skelnelig {a_sk}, parret {b_sk}, uenige {len(uenige)} ({bt['uenighedsrate']*100:.1f} %)")

    # 4.5 oracle-fri supplement (to gange)
    rt = wf(Dc, eps, avail, usrec, R, censur="realtid")
    ekstra = [r for r in rt if r["in_rec_final"]]                  # additional live-publishable origins
    uden = [r for r in rt if not r["in_rec_final"]]
    s_alle, s_uden = skill(rt), skill(uden)
    # RAADETS_SPEC7 §3.7: 4.4's procedure paa det oracle-fri saet, printet FOER det orakel-censurerede interval
    hist_of, _, _ = parret_loss_boot(rt, eps, float(np.mean([r["Y"] for r in rt])))
    hist_of.update(n_origins=len(rt), saet="oracle-fri, alle live-publicerbare (realtidscensurering)")
    print(f"4.4 oracle-fri ({len(rt)} origins): middel {hist_of['middel_pp']}, 90 %-interval {hist_of['interval_90']}, "
          f"andel traek <= 0: {hist_of['andel_ikke_positiv']}")
    l0e = sum(loss(np.mean([r["Y"] for r in rt]), r["Y"]) for r in ekstra); lme = sum(loss(r["p"], r["Y"]) for r in ekstra)
    konv = [f"{o // 12}-{o % 12 + 1:02d}" for o, _ in eps if o < A2.midx(1979, 1)]
    oracle = dict(alle_live_publicerbare=s_alle, ekskl_additional=s_uden,
                  additional_live_publishable=dict(n=len(ekstra), n_pos=int(sum(r["Y"] for r in ekstra)),
                                                   origins=[f"{r['y']}Q{r['q']}" for r in ekstra],
                                                   sum_L0=round(float(l0e), 3), sum_Lm=round(float(lme), 3),
                                                   max_p=round(max((r["p"] for r in ekstra), default=float("nan")), 3)),
                  primaer_til_sammenligning=S["improvement"],
                  rekonstruktion=dict(note="Annonceringsdatoer foer 1979 findes ikke; eligibility for onsets " +
                                      ", ".join(konv) + " er rekonstrueret med konventionen trough + 18 mdr (ablation2 PRE1979_TROUGH_LAG).",
                                      onsets_med_konvention=konv),
                  tolkning="De to varianter tolkes i tandem og citeres aldrig hver for sig (Gemini R5).")
    print(f"4.5 oracle-fri: alle live-publicerbare {s_alle['n']} origins -> +{s_alle['improvement']}%; "
          f"ekskl. {len(ekstra)} additional -> +{s_uden['improvement']}%  (primaer, censureret: +{S['improvement']}%)")

    # §3.6 + §7.3
    ex36 = skill_expanding(recs)
    faelles = [r for r in recs if (r["y"], r["q"]) <= (2023, 2)]
    tilf = [r for r in recs if (r["y"], r["q"]) > (2023, 2)]
    trunk = None
    if (snap / F6.YALE).exists():
        Dy = A2.build_dataset(snap, ["curve"], spine_file=F6.YALE)
        trunk = skill(wf(Dy, eps, avail, usrec, A2.midx(2023, 6) + 12 + L))
    s73 = dict(trunkeret_panel=trunk, udvidet_faelles_origins=skill(faelles), udvidet_tilfoejede_origins=skill(tilf) if tilf else dict(n=0),
               tilfoejede_origins=[dict(origin=f"{r['y']}Q{r['q']}", p=round(r["p"], 3), Y=r["Y"]) for r in tilf],
               note="faelles origins har identiske traeningssaet i begge paneler; forskellen er per konstruktion de tilfoejede origins")
    print(f"§7.3: trunkeret +{trunk['improvement'] if trunk else '?'}% | udvidet: faelles +{s73['udvidet_faelles_origins']['improvement']}% "
          f"({len(faelles)}), tilfoejede {[(t['origin'], t['p']) for t in s73['tilfoejede_origins']]}")
    print(f"§3.6: expanding-intercept-baseline giver +{ex36['improvement_expanding']}% (publiceret, poolet: +{S['improvement']}%)")

    gate_mde = None
    D5 = A2.build_dataset(snap, C.F5)
    # RAADETS_2027 §2.3 (spec2027/1_gate.md §5): en 2027-kalibrering har gaten i manifestet uden trin 3's 4,42
    if A2.samme_origins(Dc, D5) and not P27.i_kraft_maaned(W.get("refit_maaned")):
        r5, _, _ = A2.wf_nber(D5, eps, avail, usrec, L, R_score=R)
        paired = [(y, q, p5, pc, yy) for (y, q, p5, yy), (_, _, pc, _) in zip(r5, ref)]
        _md, sd_g, _lo, _hi = F6.A3.mde_bootstrap(paired, eps)
        f3 = HERE / "ablation3_resultat.json"
        gate_mde = dict(mde_gate_pp=round(1.96 * sd_g, 2), forskel_pp=round(float(_md), 2),
                        mde_trin3_pp=json.loads(f3.read_text(encoding="utf-8")).get("mde_pp") if f3.exists() else None,
                        note="1,96 x episode-blok-bootstrap-SD af den parrede skill-forskel F5 - curve-only (F8). "
                             "Beslutningsreglen bruger fortsat trin 3's MDE; et skift kraever raadet.")
        print(f"gate-MDE (F8): gatens egen MDE {gate_mde['mde_gate_pp']}pp (trin 3: {gate_mde['mde_trin3_pp']}pp)")
    sti = sti_foer_onsets(recs, eps, Dc)
    print(f"sti (F11): P under sin top ved sidste origin foer onset i {sti['n_under_top']}/{sti['n_onsets']} onsets; "
          f"median fald {sti['median_fald_pp']}pp, median {sti['median_mdr_top_til_onset']} mdr fra top til onset")
    start = start_sensitivitet(snap, eps, avail, usrec, R)
    print("start (F34): " + "; ".join(f"{k}: P={v['P']*100:.1f}% basisrate {v['basisrate']*100:.1f}% (n {v['n_obs']})" for k, v in start.items() if k != "input"))
    flips = {}
    for LL in (12, 18, 24):
        _r, _pw, fl = A2.wf_nber(Dc, eps, avail, usrec, LL, collect_flips=True, R_score=R)
        flips[f"L{LL}"] = dict(n=len(fl), origins=[f"{Dc['qk'][j][0]}Q{Dc['qk'][j][1]}" for j in fl])
    print("flips (G1.8): " + ", ".join(f"{k} {v['n']}" for k, v in flips.items()))
    r6 = kimi_r6(recs, eps, Dc, avail, usrec)
    print(f"Kimi R6: effektivt episodeantal pr. origin median {r6['median_episoder_i_traening']} (min {r6['min_episoder_i_traening']}); "
          f"skill uden nyeste episode +{r6['skill_uden_nyeste_episode']['improvement']}% (med: +{S['improvement']}%)")
    maanedlig_parret, nested_of = None, None
    if P27.i_kraft_maaned(W.get("refit_maaned")):
        # RAADETS_2027 §1.2 (spec2027/6_skill_saetning_refit.md §2): nested lambda scoret oracle-frit (foerste gang ved refitten)
        nested_of = P27.nested_oracle_fri(snap, eps, avail, usrec, R)
        print(f"§1.2 nested lambda, oracle-fri: +{nested_of['improvement']}% paa {nested_of['n']} origins "
              f"(kontrol: fast oracle-fri +{nested_of['fast_oracle_fri']['improvement']}%, orakel-nested "
              f"+{nested_of['nested_orakel']['improvement']}%)")
        # RAADETS_2027 §3.3 (spec2027/4_maanedligt_fit_uscorede.md §4): §3.2(b) genkoert paa refittens panel; identiteterne
        # (origins, labels, basisrate) asserteres og fejler hoejlydt; publiceres uanset udfald
        maanedlig_parret = P27.maanedlig_parret(snap, eps, avail, usrec, R)
        for ln in P27.parret_linjer(maanedlig_parret):
            print(ln.strip())
    styrke = styrke_tabel(d, bl, recs)
    print(f"styrke (G3.2): 80 % styrke kraever ca. {styrke['blokke_80pct']} cyklusblokke = ca. {styrke['aar_80pct']} aar scorede raekker")

    ud = dict(version=W.get("version"), manifest_hash=W.get("manifest_hash"), snapshot=snap.name,
              refit_maaned=W.get("refit_maaned"),
              created_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
              primaer=S | ex36, base_rate_poolet=round(float(base), 4),
              episode_tabel=dict(raekker=tab, sum_bidrag_pp=total, negative_pr_blok=neg_blok,
                                 blokdefinition="blok k = origins fra forrige onset frem til onset k (finalize6.boot_weights); k indekserer HELE USREC-episodelisten (1854-), saa sidste blok = efter sidste onset"),
              loeo=dict(blokke=loeo, median=round(float(np.median(imps)), 2), min=round(float(min(imps)), 2),
                        udefinerede=udef, status="sensitivitet, aldrig co-primaer"),
              parret_loss_bootstrap=hist, parret_loss_bootstrap_oraclefri=hist_of, domsregler_backtest=bt, oracle_fri=oracle, skill_73=s73,
              gate_mde=gate_mde, sti=sti, pre_onset_analoger=analoger, start_sensitivitet=start, flips=flips, kimi_r6=r6, styrke=styrke,
              **({"maanedlig_parret": maanedlig_parret} if maanedlig_parret else {}),
              **({"nested_oracle_fri": nested_of} if nested_of else {}),
              erklaering_36="Publiceret baseline = poolet basisrate over scorede origins (C.metrics). Konsensustekstens 'expanding intercept' var sekretaerens fejl; expanding printes som ekstra kolonne, gaten aendres ikke.")
    (HERE / "diagnostik.json").write_text(json.dumps(ud, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"diagnostik.json skrevet ({time.time() - t0:.0f} s)")


if __name__ == "__main__":
    main()
