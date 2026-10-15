#!/usr/bin/env python3
"""
frekvensgate.py — analyse til raadets 2027-dagsorden: frekvensgaten (blueprint §2) laest paa BEGGE maader.

FORMAAL / HVILKET FUND
  Kode-review 2026-10-15, fund G1.3: ablation3_frekvens.py gatede den maanedlige model paa dens
  KVARTALS-TYNDEDE walk-forward-score (m%3==0), mens RAADETS_KONSENSUS.md §2 ordret gater paa den
  maanedlige models EGEN purgede expanding-origin walk-forward-skill:
    "monthly becomes primary iff its purged expanding-origin walk-forward log-loss skill is no worse
     than the quarterly baseline minus 1pp, with quarterly-thinned scores published beside monthly scores"
  De to laesninger vendte udfaldet i trin 3 (fuld 36,83 % bestaar kravet 32,23 %; tyndet 32,08 % fejler).
  Scriptet beregner begge laesninger paa det oprindelige v5.0-panel og paa v5.0.1-panelet, for baade
  fuldmodellen (F5, som ablation3 testede) og curve-only (den operationelle modelklasse), og viser
  hvad P ville vaere i dag under en maanedlig model mod den operationelle kvartalsmodel.

DESIGN (fakta — ingen beslutning, ingen anbefaling)
  Paneler:
    a_v50_ablation3  snapshot 2026-08-09, ren Yale-rygrad (shiller.csv), som ablation3 koerte det.
                     R_score = 2023Q2-slut + 12 + 18 mdr = 2025-12 (alle origins <= 2023Q2 er modne, saa
                     F5 skal reproducere ablation3_resultat.json: 33,23 / 36,83 / 32,08 / MDE 4,42).
    a_legacy_replay  snapshot 2026-09-19 + shiller_yale_2023-09.csv, R_score = 2025-12 (v5.0-manifestet
                     6baeade4: curve-only +34,32 %, F5 +33,23 %) — vintage-kontrol af panel a.
    b_v501           snapshot 2026-09-19 (weights.json), spine.csv, R_score = 2026-09 (manifest 72c3371d):
                     curve-only skal reproducere +27,05 % / Brier +24,15 % paa 198 origins; F5 +23,16 %.
  Pr. panel og model:
    kvartal direkte-4q          A2.wf_nber (purget, L=18, censur, >=60 raekker / >=6 positive, R_score-modning)
    maanedlig direkte-12m FULD  wf_maanedlig = ablation3.wf_monthly (refit hver maaned, purget, >=180 raekker /
                                >=18 positive) + samme R_score-modning som §3.5 (umoden label scores ikke)
    kvartals-tyndet             m%3 == 0 (ablation3's gate-metrik) samt de to andre faser (m%3 == 1, 2)
    parret forskel + MDE        ablation3.mde_bootstrap (tyndet minus kvartal paa identiske origins; episode-
                                blok-bootstrap, seed 42, 1000 traek; MDE = 1,96 x SD)
    blok-MDE for fuld maanedlig blok_mde: samme episodeblokke trukket med tilbagelaegning, skill for hvert
                                raekkesaet paa de trukne blokke (origin-maengderne er forskellige, saa ingen
                                origin-parring er mulig); identiske origins giver praecis ablation3's tal
    Laesning A (bogstavelig §2) maanedlig primaer iff FULD maanedlig skill >= kvartal - 1,0pp
    Laesning B (ablation3-kode) maanedlig primaer iff TYNDET (m%3==0) skill >= kvartal - 1,0pp
  P i dag: den operationelle kvartalsmodel (weights.json, frosne vaegte + baand) mod en kontrafaktisk
  maanedlig curve-only-model fittet paa v5.0.1-panelet ved R = 2026-09 med samme modningsregel som
  finalize6.fit_model (vinduets slut + 18 mdr <= R; annoncerede recessioner ude), baand = episode-blok-
  bootstrap af vaegte (finalize6.boot_weights, seed 42). Begge ved live-kurven (C.live_kurve paa nyeste
  komplette snapshot) og ved maanedstallet, plus P ved faste kurveniveauer.

AENDRER INTET I DRIFTEN. Scriptet laeser kun og skriver udelukkende analyser/frekvensgate_resultat.json.
Ingen vaegte, gates, hovedbog, dashboard eller resultatfiler roeres. Deterministisk: faste seeds; det
eneste vaegur-felt er created_utc.

Koer:  cd v5 && python analyser/frekvensgate.py
Kun stdlib + numpy.
"""
import json, sys, time
from datetime import datetime, timezone
from pathlib import Path

sys.dont_write_bytecode = True
import numpy as np

HERE = Path(__file__).resolve().parent
V5 = HERE.parent
sys.path.insert(0, str(V5))
import calibrate as C            # noqa: E402
import ablation2_nber as A2      # noqa: E402
import ablation3_frekvens as A3  # noqa: E402
import finalize6 as F6           # noqa: E402

L = A2.L_EMBARGO                 # 18
SEED = 42
NDRAW = 1000
GATE_MARGIN = A3.GATE_MARGIN     # 1.0 pp
MIN_TR_M, MIN_POS_M = 180, 18    # ablation3.wf_monthly: 60 kvartaler / 6 positive i maaneder

BLUEPRINT_S2 = ("monthly becomes primary iff its purged expanding-origin walk-forward log-loss skill is no "
                "worse than the quarterly baseline minus 1pp, with quarterly-thinned scores published beside "
                "monthly scores")
ABLATION3_REGEL = ("G2 maanedlig promoveres kun hvis dens KVARTALS-TYNDEDE walk-forward log-loss-forbedring "
                   ">= kvartals-baselinens forbedring - 1,0pp (fuld maanedlig score printes ved siden af men "
                   "indgaar ikke i gaten)")

PUBLICERET = dict(
    ablation3=dict(kvartal=33.23, fuld=36.83, tyndet=32.08, n_q=195, n_m=582, diff=-1.15, sd=2.26, mde=4.42),
    legacy_6baeade4=dict(curve_wf=34.32, curve_brier=32.85, f5_wf=33.23, f5_brier=33.6),
    v501_72c3371d=dict(curve_wf=27.05, curve_brier=24.15, n=198, f5_wf=23.16, f5_brier=23.69),
)


def mk(i):
    return f"{i // 12}-{i % 12 + 1:02d}"


# ------------------------------------------------------------------ maanedligt panel
def byg_maanedligt(snap, Dq, feats, spine_file=None):
    """Maanedligt univers for `feats`: alle features ikke-NaN OG maanedens kvartal ligger i det kvartalsvise
    univers Dq (identisk kalenderspaend) — ablation3.build_monthly_dataset for vilkaarlige features, med
    A2.build_dataset's rygrad-forlaengelse for curve-only (GS10/TB3MS-maaneder efter rygradens sidste)."""
    shiller = C.read_shiller(snap, spine_file)
    gs10 = C.read_fred(snap, "GS10")
    tb3ms = C.read_fred(snap, "TB3MS")
    if spine_file is None and list(feats) == ["curve"]:
        sidst = shiller[-1][0] if shiller else (0, 0)
        shiller = shiller + [(k, np.nan, np.nan, np.nan, np.nan) for k in sorted(set(gs10) & set(tb3ms)) if k > sidst]
    keys, M = C.build_monthly(shiller, gs10, tb3ms)
    F = np.stack([M[f] for f in feats], axis=1)
    ok_q = set(Dq["qk"])
    rows = [i for i, (y, m) in enumerate(keys)
            if not np.any(np.isnan(F[i])) and (y, (m - 1) // 3 + 1) in ok_q]
    return dict(F=F[rows], feats=list(feats),
                midx=np.array([A2.midx(*keys[i]) for i in rows]), ym=[keys[i] for i in rows])


def labels_maanedlig(Dm, eps, usrec):
    n = len(Dm["midx"])
    win_onsets, Y_final, in_rec = [], np.zeros(n), np.zeros(n, bool)
    for j in range(n):
        w_lo, w_hi = Dm["midx"][j] + 1, Dm["midx"][j] + 12
        wo = [o for o, _ in eps if w_lo <= o <= w_hi]
        win_onsets.append(wo)
        Y_final[j] = 1.0 if wo else 0.0
        in_rec[j] = usrec.get(int(Dm["midx"][j]), 0) == 1
    ep_onset = [A2.episode_of(int(Dm["midx"][j]), eps) for j in range(n)]
    ep_onset = [e[0] if e else None for e in ep_onset]
    return win_onsets, Y_final, in_rec, ep_onset


def wf_maanedlig(Dm, eps, avail, usrec, R_score=None, start=1960):
    """Purget expanding-origin walk-forward paa maanedsraekker — praecis ablation3.wf_monthly (refit hver
    maaned; traening = raekker hvis vindue + L <= R og ikke inde i en recession annonceret pr. R; labels pr.
    annonceringstabellen ved R; censurerede origins scores ikke), plus §3.5-modning: origins hvis label er
    umoden ved R_score (midx + 12 + L > R_score) scores ikke. R_score=None = ablation3's adfaerd.
    Returnerer [(aar, maaned, p, Y_final)] og en lille styrke-oversigt."""
    win_onsets, Y_final, in_rec, ep_onset = labels_maanedlig(Dm, eps, usrec)
    n = len(Dm["midx"])
    out, pos_tr = [], []
    for i in range(n):
        if Dm["ym"][i][0] < start:
            continue
        if R_score is not None and Dm["midx"][i] + 12 + L > R_score:
            continue
        R = int(Dm["midx"][i])
        tr = [j for j in range(i)
              if Dm["midx"][j] + 12 + L <= R and not (ep_onset[j] is not None and avail[ep_onset[j]] <= R)]
        if len(tr) < MIN_TR_M:
            continue
        yR = np.array([1.0 if any(avail[o] <= R for o in win_onsets[j]) else 0.0 for j in tr])
        if yR.sum() < MIN_POS_M:
            continue
        X = Dm["F"][tr]
        mu, sd = X.mean(0), X.std(0, ddof=1)
        sd[sd == 0] = 1
        w = C.fit((X - mu) / sd, yR)
        if in_rec[i]:
            continue
        p = float(C.predict(w, (Dm["F"][[i]] - mu) / sd)[0])
        y, m = Dm["ym"][i]
        out.append((int(y), int(m), p, float(Y_final[i])))
        pos_tr.append(int(yR.sum()))
    styrke = dict(median_pos_i_traening=int(np.median(pos_tr)) if pos_tr else None,
                  min_pos_i_traening=int(min(pos_tr)) if pos_tr else None)
    return out, styrke


def elig_maanedlig(Dm, eps, avail, usrec, R):
    """Traeningsberettigede maanedsraekker ved refit-maaned R — samme regel som A2.eligible_fit (§3.5):
    vinduets slut + L <= R og ikke inde i en recession annonceret pr. R. -> (maske, labels pr. R)."""
    win_onsets, _Y, _in, ep_onset = labels_maanedlig(Dm, eps, usrec)
    n = len(Dm["midx"])
    elig, yR = np.zeros(n, bool), np.zeros(n)
    for j in range(n):
        if Dm["midx"][j] + 12 + L > R:
            continue
        if ep_onset[j] is not None and avail[ep_onset[j]] <= R:
            continue
        elig[j] = True
        yR[j] = 1.0 if any(avail[o] <= R for o in win_onsets[j]) else 0.0
    return elig, yR


# ------------------------------------------------------------------ skill, MDE, gate
def skill(rows):
    if not rows:
        return dict(n=0)
    ll, bl, imp, br = C.metrics(rows)
    ys = np.array([r[3] for r in rows])
    neg = [r for r in rows if r[3] == 0.0]
    vaerst = max(neg, key=lambda r: r[2]) if neg else None
    return dict(n=len(rows), n_pos=int(ys.sum()), base_rate=round(float(ys.mean()), 4),
                logloss=round(float(ll), 4), baseline=round(float(bl), 4),
                improvement=round(float(imp), 2), brier=round(float(br), 2),
                foerste=f"{rows[0][0]}-{rows[0][1]:02d}", sidste=f"{rows[-1][0]}-{rows[-1][1]:02d}",
                vaerste_fejlalarm=dict(p=round(vaerst[2], 4), origin=f"{vaerst[0]}-{vaerst[1]:02d}") if vaerst else None)


def blok_mde(rows_a, rows_b, eps, ndraw=NDRAW):
    """Episode-blok-bootstrap af skill-forskellen (a minus b, pp). Begge raekkesaet grupperes med
    ablation3.episode_group (origin-aar -> naermeste efterfoelgende onset); et traek er blokke med
    tilbagelaegning, skill beregnes for hvert saet paa de trukne blokke. Identiske origins i a og b giver
    praecis ablation3.mde_bootstrap (selvtjek i run_panel)."""
    rng = np.random.default_rng(SEED)
    ga, gb = {}, {}
    for (y, _m, p, yy) in rows_a:
        ga.setdefault(A3.episode_group(y, eps), []).append((p, yy))
    for (y, _m, p, yy) in rows_b:
        gb.setdefault(A3.episode_group(y, eps), []).append((p, yy))
    gkeys = sorted(set(ga) | set(gb))

    def sk(groups, sample):
        p, yy = [], []
        for g in sample:
            for a, b in groups.get(g, []):
                p.append(a); yy.append(b)
        if not yy:
            return None
        p, yy = np.clip(np.array(p), 1e-6, 1 - 1e-6), np.array(yy)
        b = yy.mean()
        if b in (0.0, 1.0):
            return None
        bl = -np.mean(yy * np.log(b) + (1 - yy) * np.log(1 - b))
        lm = -np.mean(yy * np.log(p) + (1 - yy) * np.log(1 - p))
        return (1 - lm / bl) * 100

    def diff(sample):
        a, b = sk(ga, sample), sk(gb, sample)
        return None if a is None or b is None else a - b

    point = diff(gkeys)
    draws = []
    while len(draws) < ndraw:
        d = diff(list(rng.choice(gkeys, size=len(gkeys), replace=True)))
        if d is not None:
            draws.append(d)
    draws = np.array(draws)
    sd = float(draws.std(ddof=1))
    return dict(forskel_pp=round(float(point), 2), sd_pp=round(sd, 2),
                ci10=round(float(np.percentile(draws, 10)), 2), ci90=round(float(np.percentile(draws, 90)), 2),
                mde_pp=round(1.96 * sd, 2), n_blokke=len(gkeys), n_draws=ndraw, seed=SEED)


def gate(imp_q, imp_fuld, imp_t0):
    krav = imp_q - GATE_MARGIN
    A, B = imp_fuld >= krav, imp_t0 >= krav
    return dict(
        krav_pp=round(krav, 2),
        A_bogstavelig_s2=dict(metrik="fuld maanedlig purget wf-skill", vaerdi=round(imp_fuld, 2),
                              bestaaet=bool(A), primaer="maanedlig" if A else "kvartal"),
        B_ablation3_kode=dict(metrik="kvartals-tyndet maanedlig (m%3==0)", vaerdi=round(imp_t0, 2),
                              bestaaet=bool(B), primaer="maanedlig" if B else "kvartal"),
        laesningerne_er_uenige=bool(A != B))


# ------------------------------------------------------------------ et panel
def run_panel(navn, beskrivelse, snap, R_score, modeller):
    meta = json.loads((snap / "meta.json").read_text(encoding="utf-8"))
    usrec = A2.load_usrec(snap)
    eps = A2.episodes_from_usrec(usrec)
    avail = A2.load_announcements(eps, usrec=usrec)
    ud = dict(beskrivelse=beskrivelse, snapshot=snap.name, snapshot_sha256=meta.get("snapshot_sha256"),
              R_score=mk(R_score), modeller={})
    for mnavn, feats, spine_file in modeller:
        t0 = time.time()
        Dq = A2.build_dataset(snap, feats, spine_file=spine_file)
        res_q, power_q, _ = A2.wf_nber(Dq, eps, avail, usrec, L, R_score=R_score)
        Dm = byg_maanedligt(snap, Dq, feats, spine_file=spine_file)
        res_m, styrke_m = wf_maanedlig(Dm, eps, avail, usrec, R_score=R_score)
        faser = {ph: [r for r in res_m if r[1] % 3 == ph] for ph in (0, 1, 2)}
        q_by_key = {(y, q): (p, yy) for (y, q, p, yy) in res_q}
        paired, label_uenig = [], 0
        for (y, m, pm, yy) in faser[0]:
            k = (y, m // 3)
            if k in q_by_key:
                pq, yq = q_by_key[k]
                if yq == yy:
                    paired.append((y, m // 3, pm, pq, yy))
                else:
                    label_uenig += 1
        diff, sd, lo, hi = A3.mde_bootstrap(paired, eps)
        parret = dict(forskel_pp=round(float(diff), 2), sd_pp=round(sd, 2), ci10=round(lo, 2), ci90=round(hi, 2),
                      mde_pp=round(1.96 * sd, 2), n_parrede_origins=len(paired), labels_uenige=label_uenig,
                      metode="ablation3.mde_bootstrap: tyndet (m%3==0) minus kvartal paa identiske origins")
        chk = blok_mde([(y, q, pm, yy) for (y, q, pm, pq, yy) in paired],
                       [(y, q, pq, yy) for (y, q, pm, pq, yy) in paired], eps)
        selvtjek_ok = (chk["forskel_pp"] == parret["forskel_pp"] and chk["sd_pp"] == parret["sd_pp"])
        fuld = blok_mde(res_m, res_q, eps)
        fuld["metode"] = "blok_mde: fuld maanedlig minus kvartal paa samme episodeblokke (forskellige origin-maengder)"
        sq, sf = skill(res_q), skill(res_m)
        st = {f"m%3=={ph}": skill(faser[ph]) for ph in (0, 1, 2)}
        g = gate(sq["improvement"], sf["improvement"], st["m%3==0"]["improvement"])
        g["andre_tyndinger_under_B"] = {k: dict(vaerdi=v["improvement"], bestaaet=bool(v["improvement"] >= g["krav_pp"]))
                                        for k, v in st.items() if k != "m%3==0"}
        # er forskellene under stoejgulvet?
        g["under_stoejgulv"] = dict(
            tyndet_vs_kvartal=bool(abs(parret["forskel_pp"]) < parret["mde_pp"]),
            fuld_vs_kvartal=bool(abs(fuld["forskel_pp"]) < fuld["mde_pp"]))
        power = dict(median_pos_i_traening_kvartal=int(np.median([p for (_, p, _) in power_q])) if power_q else None,
                     min_pos_i_traening_kvartal=int(min(p for (_, p, _) in power_q)) if power_q else None,
                     **{k + "_maanedlig": v for k, v in styrke_m.items()})
        ud["modeller"][mnavn] = dict(
            features=list(feats), rygrad=spine_file or ("spine.csv" if (snap / "spine.csv").exists() else "shiller.csv"),
            kvartal_univers=dict(n=len(Dq["qk"]), foerste=f"{Dq['qk'][0][0]}Q{Dq['qk'][0][1]}", sidste=f"{Dq['qk'][-1][0]}Q{Dq['qk'][-1][1]}"),
            maanedligt_univers=dict(n=len(Dm["midx"]), foerste=f"{Dm['ym'][0][0]}-{Dm['ym'][0][1]:02d}", sidste=f"{Dm['ym'][-1][0]}-{Dm['ym'][-1][1]:02d}"),
            kvartal_4q=sq, maanedlig_12m_fuld=sf, maanedlig_tyndet=st,
            parret_tyndet_vs_kvartal=parret, blok_fuld_vs_kvartal=fuld, selvtjek_blok_mde_lig_ablation3=bool(selvtjek_ok),
            gate=g, styrke=power)
        print(f"  [{navn}/{mnavn}] kvartal {sq['improvement']:+.2f}% (n={sq['n']})  fuld {sf['improvement']:+.2f}% (n={sf['n']})  "
              f"tyndet0 {st['m%3==0']['improvement']:+.2f}%  krav {g['krav_pp']:.2f}  "
              f"A:{g['A_bogstavelig_s2']['primaer']}  B:{g['B_ablation3_kode']['primaer']}  "
              f"MDE tyndet {parret['mde_pp']:.2f} / fuld {fuld['mde_pp']:.2f}  ({time.time() - t0:.0f}s)")
    return ud


# ------------------------------------------------------------------ P i dag
def p_i_dag(snap_b, R, snap_ny):
    W = json.loads((V5 / "weights.json").read_text(encoding="utf-8"))
    LI = C.live_kurve(snap_ny)
    x_live = {"curve": float(LI["curve"])}
    x_m = {"curve": float(LI["maanedlig"]["curve"])}
    op = W["op"]
    band_op = np.array([F6.p_af(dict(op, w=wb), x_live) for wb in W["band"]["W"]])
    lo_op, hi_op = float(np.percentile(band_op, 10)), float(np.percentile(band_op, 90))
    operationel = dict(
        kilde="weights.json (frosne driftsvaegte)", version=W.get("version"), manifest=W.get("manifest_hash"),
        refit_maaned=W.get("refit_maaned"), snapshot=W.get("snapshot"), frekvens=W.get("frekvens"),
        mu=op["mu"], sd=op["sd"], w=op["w"], raa=op.get("raa"), n_obs=W.get("n_obs"), base_rate=W.get("base_rate"),
        P_live=round(F6.p_af(op, x_live), 4), P_maanedstal=round(F6.p_af(op, x_m), 4),
        baand_10_90_live=[round(lo_op, 4), round(hi_op, 4)],
        baand_indeholder_basisraten=bool(lo_op <= W["base_rate"] <= hi_op),
        n_draws_baand=len(W["band"]["W"]))

    usrec = A2.load_usrec(snap_b)
    eps = A2.episodes_from_usrec(usrec)
    avail = A2.load_announcements(eps, usrec=usrec)
    Dc = A2.build_dataset(snap_b, ["curve"])
    mq = F6.fit_model(Dc, eps, avail, usrec, R)
    genudledt = dict(mu=mq["mu"], sd=mq["sd"], w=mq["w"], raa=mq["raa"], n_obs=mq["n_obs"], n_pos=mq["n_pos"],
                     base_rate=mq["base_rate"], estimering_slut=mq["estimering_slut"],
                     identisk_med_weights_json=bool(mq["w"] == op["w"] and mq["mu"] == op["mu"] and mq["sd"] == op["sd"]))

    Dm = byg_maanedligt(snap_b, Dc, ["curve"])
    elig, yR = elig_maanedlig(Dm, eps, avail, usrec, R)
    X, y = Dm["F"][elig], yR[elig]
    mu, sd = X.mean(0), X.std(0, ddof=1)
    sd[sd == 0] = 1
    Z = (X - mu) / sd
    w = C.fit(Z, y)
    mm = dict(features=["curve"], mu={"curve": round(float(mu[0]), 4)}, sd={"curve": round(float(sd[0]), 4)},
              w=[round(float(v), 4) for v in w])
    Wb, Bb, n_blk, _grp = F6.boot_weights(Z, y, Dm["midx"][elig], eps, NDRAW)
    band_m = np.array([F6.p_af(dict(mm, w=wb), x_live) for wb in Wb])
    lo_m, hi_m = float(np.percentile(band_m, 10)), float(np.percentile(band_m, 90))
    sidste = int(Dm["midx"][elig][-1])
    maanedlig = dict(
        kilde="kontrafaktisk: maanedlig direkte-12m curve-only fittet paa v5.0.1-panelet ved R = " + mk(R),
        snapshot=snap_b.name, mu=mm["mu"], sd=mm["sd"], w=mm["w"],
        raa=dict(beta_curve_pr_pp=round(float(w[1] / sd[0]), 4), alpha=round(float(w[0] - w[1] * mu[0] / sd[0]), 4)),
        n_obs=int(elig.sum()), n_pos=int(y.sum()), base_rate=round(float(y.mean()), 4),
        estimering_slut=mk(sidste), univers_slut=f"{Dm['ym'][-1][0]}-{Dm['ym'][-1][1]:02d}",
        P_live=round(F6.p_af(mm, x_live), 4), P_maanedstal=round(F6.p_af(mm, x_m), 4),
        baand_10_90_live=[round(lo_m, 4), round(hi_m, 4)],
        baand_indeholder_basisraten=bool(lo_m <= float(y.mean()) <= hi_m),
        n_draws_baand=len(Wb), n_blokke_baand=int(n_blk), seed=SEED)

    grid = sorted({-1.0, -0.5, 0.0, 0.5, 1.0, round(x_live["curve"], 2), 1.5, 2.0, 3.0})
    tabel = [dict(kurve_pp=c, P_kvartal_op=round(F6.p_af(op, {"curve": c}), 4), P_maanedlig=round(F6.p_af(mm, {"curve": c}), 4))
             for c in grid]
    return dict(
        nyeste_snapshot=snap_ny.name,
        live_input=dict(curve_pp=round(x_live["curve"], 4), kilde=LI.get("kilde"), vindue=LI.get("vindue"), n_dage=LI.get("n_dage"),
                        y10=round(float(LI["y10"]), 4), tb3=round(float(LI["tb3"]), 4),
                        maanedstal=dict(curve_pp=round(x_m["curve"], 4), maaned=LI["maanedlig"]["maaned"])),
        kvartal_operationel=operationel, kvartal_genudledt_fra_panel_b=genudledt, maanedlig_kontrafaktisk=maanedlig,
        forskel_P_live_pp=round(100 * (maanedlig["P_live"] - operationel["P_live"]), 2),
        P_ved_faste_kurveniveauer=tabel,
        note="P under den maanedlige model er en kontrafaktisk beregning til raadet — ikke en aflaesning, ikke logfoert. "
             "Baandet er et estimation-sensitivity range (Not a predictive interval).")


# ------------------------------------------------------------------ main
def main():
    t0 = time.time()
    snap_a = C.RAW / "2026-08-09"
    snap_b = C.RAW / "2026-09-19"
    for s in (snap_a, snap_b):
        if not (s / "meta.json").exists():
            sys.exit(f"FEJL: snapshot {s} mangler")
    R_legacy = A2.midx(2023, 6) + 12 + L       # 2025-12: alle origins <= 2023Q2 modne (finalize6 --legacy)
    R_b = A2.midx(2026, 9)                     # weights.json refit_maaned
    snap_ny = C.find_snapshot([])
    print(f"=== frekvensgate (G1.3) — paneler a:{snap_a.name} a':{snap_b.name}+Yale b:{snap_b.name} — nyeste {snap_ny.name} ===")

    paneler = {}
    paneler["a_v50_ablation3"] = run_panel(
        "a", "v5.0-panelet som ablation3 koerte det: snapshot 2026-08-09, ren Yale-rygrad (shiller.csv); "
             "R_score 2025-12 = alle origins <= 2023Q2 (ablation3 scorede alle origins uden R_score — identisk maengde)",
        snap_a, R_legacy, [("F5_fuldmodel", C.F5, None), ("curve_only", ["curve"], "shiller.csv")])
    paneler["a_legacy_replay"] = run_panel(
        "a'", "legacy-replay (vintage-kontrol af a): snapshot 2026-09-19 + shiller_yale_2023-09.csv, R_score 2025-12 "
              "(v5.0-manifest 6baeade4)",
        snap_b, R_legacy, [("F5_fuldmodel", C.F5, F6.YALE), ("curve_only", ["curve"], F6.YALE)])
    paneler["b_v501"] = run_panel(
        "b", "v5.0.1-panelet: snapshot 2026-09-19 (weights.json), spine.csv, R_score 2026-09 (manifest 72c3371d)",
        snap_b, R_b, [("curve_only", ["curve"], None), ("F5_fuldmodel", C.F5, None)])

    # reproduktion af publicerede tal
    a5 = paneler["a_v50_ablation3"]["modeller"]["F5_fuldmodel"]
    ar = paneler["a_legacy_replay"]["modeller"]
    b = paneler["b_v501"]["modeller"]
    P = PUBLICERET
    repro = dict(
        ablation3_resultat_json=dict(
            kvartal=[P["ablation3"]["kvartal"], a5["kvartal_4q"]["improvement"]],
            maanedlig_fuld=[P["ablation3"]["fuld"], a5["maanedlig_12m_fuld"]["improvement"]],
            maanedlig_tyndet=[P["ablation3"]["tyndet"], a5["maanedlig_tyndet"]["m%3==0"]["improvement"]],
            n=[[P["ablation3"]["n_q"], P["ablation3"]["n_m"]], [a5["kvartal_4q"]["n"], a5["maanedlig_12m_fuld"]["n"]]],
            skill_diff_sd_mde=[[P["ablation3"]["diff"], P["ablation3"]["sd"], P["ablation3"]["mde"]],
                               [a5["parret_tyndet_vs_kvartal"]["forskel_pp"], a5["parret_tyndet_vs_kvartal"]["sd_pp"], a5["parret_tyndet_vs_kvartal"]["mde_pp"]]]),
        manifest_6baeade4=dict(curve_only_wf=[P["legacy_6baeade4"]["curve_wf"], ar["curve_only"]["kvartal_4q"]["improvement"]],
                               curve_only_brier=[P["legacy_6baeade4"]["curve_brier"], ar["curve_only"]["kvartal_4q"]["brier"]],
                               F5_wf=[P["legacy_6baeade4"]["f5_wf"], ar["F5_fuldmodel"]["kvartal_4q"]["improvement"]]),
        manifest_72c3371d=dict(curve_only_wf=[P["v501_72c3371d"]["curve_wf"], b["curve_only"]["kvartal_4q"]["improvement"]],
                               curve_only_brier=[P["v501_72c3371d"]["curve_brier"], b["curve_only"]["kvartal_4q"]["brier"]],
                               n=[P["v501_72c3371d"]["n"], b["curve_only"]["kvartal_4q"]["n"]],
                               F5_wf=[P["v501_72c3371d"]["f5_wf"], b["F5_fuldmodel"]["kvartal_4q"]["improvement"]],
                               F5_brier=[P["v501_72c3371d"]["f5_brier"], b["F5_fuldmodel"]["kvartal_4q"]["brier"]]))

    def flad(d):
        for v in d.values():
            if isinstance(v, dict):
                yield from flad(v)
            else:
                yield v
    alle_ok = all(json.dumps(pub) == json.dumps(got) for pub, got in flad(repro))
    repro["alle_publicerede_tal_reproduceret"] = bool(alle_ok)
    print("reproduktion af publicerede tal: " + ("OK" if alle_ok else "AFVIGELSE — se 'reproduktion'"))

    pid = p_i_dag(snap_b, R_b, snap_ny)
    print(f"P i dag ved live-kurve {pid['live_input']['curve_pp']:+.2f}pp: kvartal (drift) {pid['kvartal_operationel']['P_live']*100:.1f}% "
          f"[{pid['kvartal_operationel']['baand_10_90_live'][0]*100:.1f}-{pid['kvartal_operationel']['baand_10_90_live'][1]*100:.1f}]  "
          f"maanedlig (kontrafaktisk) {pid['maanedlig_kontrafaktisk']['P_live']*100:.1f}% "
          f"[{pid['maanedlig_kontrafaktisk']['baand_10_90_live'][0]*100:.1f}-{pid['maanedlig_kontrafaktisk']['baand_10_90_live'][1]*100:.1f}]")

    sammen = {}
    for pn, pv in paneler.items():
        for mn, mv in pv["modeller"].items():
            g = mv["gate"]
            sammen[f"{pn}/{mn}"] = dict(
                kvartal=mv["kvartal_4q"]["improvement"], fuld=mv["maanedlig_12m_fuld"]["improvement"],
                tyndet0=mv["maanedlig_tyndet"]["m%3==0"]["improvement"], krav=g["krav_pp"],
                A_bogstavelig=g["A_bogstavelig_s2"]["primaer"], B_kode=g["B_ablation3_kode"]["primaer"],
                mde_tyndet=mv["parret_tyndet_vs_kvartal"]["mde_pp"], mde_fuld=mv["blok_fuld_vs_kvartal"]["mde_pp"])

    ud = dict(
        analyse="frekvensgate", fund="G1.3 (kode-review 2026-10-15)",
        created_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        aendrer_drift=False,
        blueprint_s2_ordret=BLUEPRINT_S2, ablation3_regel=ABLATION3_REGEL,
        laesninger=dict(A="bogstavelig §2: fuld maanedlig purget wf-skill >= kvartal - 1pp",
                        B="ablation3-kode: kvartals-tyndet (m%3==0) maanedlig skill >= kvartal - 1pp"),
        konstanter=dict(gate_margin_pp=GATE_MARGIN, L_embargo=L, seed=SEED, n_draws=NDRAW, start_aar=1960,
                        min_traening_maanedlig=[MIN_TR_M, MIN_POS_M], min_traening_kvartal=[60, 6]),
        sammenfatning=sammen, paneler=paneler, reproduktion=repro, P_i_dag=pid,
        noter=[
            "Skill = log-loss-forbedring mod den POOLEDE basisrate over de scorede origins (C.metrics); fuld maanedlig og "
            "kvartal har forskellige origin-maengder og dermed hver sin basisrate — tallene er ikke origin-parrede.",
            "Tyndet m%3==0 er kvartalsslut-maanederne og er origin-identisk med kvartalsmodellen (parret, som ablation3).",
            "Grok R6 (RAADETS_KONSENSUS): taerskler maa aldrig lempes efter at resultater er set — begge udfald er nu kendt; "
            "scriptet rapporterer kun fakta.",
            "Et skifte til maanedlig frekvens er laast bag raadsbeslutning (RAADETS_V501 §6) og sker aldrig automatisk.",
        ])
    out = HERE / "frekvensgate_resultat.json"
    out.write_text(json.dumps(ud, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"{out.name} skrevet ({time.time() - t0:.1f} s)")


if __name__ == "__main__":
    main()
