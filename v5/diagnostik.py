#!/usr/bin/env python3
"""
diagnostik.py — RAADETS_V501 §4 (+ §3.6-erklaering, §7.3): diagnostik der printes ved siden af
laesningen og ALDRIG aendrer gate, vaegte eller dom.

  4.1 Episode-tabel: 12 onset-raekker + een raekke med alle negative origins; additivt bidrag
      100*sum(L0-Lm)/sum(L0) der summerer eksakt til den poolede forbedring; negative ogsaa pr.
      kronologisk bootstrap-blok (blokgraenser publiceres, aendres aldrig).
  4.2 LOEO: walk-forward hvor blok k er udelukket fra traeningen naar blok k scores (ingen
      fremtidsdata, eksplicit udelukkelse) — sensitivitet, aldrig co-primaer.
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


def main():
    warnings.filterwarnings("ignore", category=RuntimeWarning)   # udefinerede blokke haandteres eksplicit i skill()
    t0 = time.time()
    hurtig = "--hurtig" in sys.argv
    snap = C.find_snapshot(sys.argv)
    W = json.loads((HERE / "weights.json").read_text(encoding="utf-8"))
    print(f"=== diagnostik — v{W.get('version', '?')} manifest {W.get('manifest_hash', '?')} — snapshot {snap.name} ===")
    usrec = A2.load_usrec(snap); eps = A2.episodes_from_usrec(usrec); avail = A2.load_announcements(eps)
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
    d = np.array([loss(base, r["Y"]) - loss(r["p"], r["Y"]) for r in recs])
    bl = np.array([blok_af(A2.qend_idx(r["y"], r["q"]), eps) for r in recs])
    rng = np.random.default_rng(SEED)
    keys = np.unique(bl); means = []
    for _ in range(10000):
        rows = np.concatenate([np.where(bl == g)[0] for g in rng.choice(keys, size=len(keys), replace=True)])
        means.append(d[rows].mean())
    means = np.array(means)
    hist = dict(middel_pp=round(float(d.mean()), 4), interval_90=[round(float(np.percentile(means, 5)), 4), round(float(np.percentile(means, 95)), 4)],
                andel_ikke_positiv=round(float(np.mean(means <= 0)), 4), n_blokke=int(len(keys)), n_draws=10000)
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
    print(f"4.3 domsregler backtestet: {len(rb)} origins x {nb} traek — baand skelnelig {a_sk}, parret {b_sk}, uenige {len(uenige)} ({bt['uenighedsrate']*100:.1f} %)")

    # 4.5 oracle-fri supplement (to gange)
    rt = wf(Dc, eps, avail, usrec, R, censur="realtid")
    ekstra = [r for r in rt if r["in_rec_final"]]                  # additional live-publishable origins
    uden = [r for r in rt if not r["in_rec_final"]]
    s_alle, s_uden = skill(rt), skill(uden)
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

    ud = dict(version=W.get("version"), manifest_hash=W.get("manifest_hash"), snapshot=snap.name,
              created_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
              primaer=S | ex36, base_rate_poolet=round(float(base), 4),
              episode_tabel=dict(raekker=tab, sum_bidrag_pp=total, negative_pr_blok=neg_blok,
                                 blokdefinition="blok k = origins fra forrige onset frem til onset k (finalize6.boot_weights); blok 12 = efter sidste onset"),
              loeo=dict(blokke=loeo, median=round(float(np.median(imps)), 2), min=round(float(min(imps)), 2),
                        udefinerede=udef, status="sensitivitet, aldrig co-primaer"),
              parret_loss_bootstrap=hist, domsregler_backtest=bt, oracle_fri=oracle, skill_73=s73,
              erklaering_36="Publiceret baseline = poolet basisrate over scorede origins (C.metrics). Konsensustekstens 'expanding intercept' var sekretaerens fejl; expanding printes som ekstra kolonne, gaten aendres ikke.")
    (HERE / "diagnostik.json").write_text(json.dumps(ud, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"diagnostik.json skrevet ({time.time() - t0:.0f} s)")


if __name__ == "__main__":
    main()
