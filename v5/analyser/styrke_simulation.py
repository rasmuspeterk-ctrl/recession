#!/usr/bin/env python3
"""
styrke_simulation.py — styrkesimulation for hovedbogen som eksamen (kode-review 2026-10-15, G3.2).

Formaal
-------
Hvor mange aars hovedbogsraekker kraeves, foer en ensidet 5 %-test med cluster-robust t paa
cyklusblokke har 80 % styrke til at skelne modellen fra hovedbogens loggede basisrate (18,0 %)?
diagnostik.json's parametriske svar (afsnit `styrke`) er ca. 26 blokke ~ 168 aar. Dette script
giver det simulerede svar, som reviewet (scratchpad/review/pw_power3.py) naaede frem til, men
genskabt fra repoets egen kode og udvidet med stoerrelseskontrol (Type I) af testene.

Besvarer: G3.2 "Hovedbogen mangler styrke til at skelne +27 % fra basisraten de naeste aartier"
(plus skeptikerens korrektion: cluster-t holder ikke sit nominelle niveau ved faa blokke).

Design (fastlagt foer koersel)
------------------------------
  panel      v5.0.1: snapshot data/raw/2026-09-19, R_score = 2026-09 (A2.wf_nber-reglerne, L = 18).
             Kontrol: den kvartalsvise walk-forward skal give de publicerede tal (198 origins,
             +27,05 % / Brier +24,15 %).
  hovedbog   MAANEDLIG walk-forward (som reviewets pw_monthly_wf.py): vaegtene fra seneste
             kvartals-refit (samme traeningsregler som wf_nber) anvendes paa maanedskurven i refit-
             maaneden og de to foelgende maaneder; label = NBER-onset inden 12 maaneder (endelig
             kronologi); origins inde i en recession censureres (orakel, som primaermetrikken);
             kun modne origins (m + 12 + L <= R_score). Tab pr. raekke: log-loss for modellen (Lm)
             og for den faste loggede basisrate 18,0 % (L0); d = L0 - Lm.
  blokke     bund til bund (trough -> trough) i kalendermaaneder, inkl. censurerede maaneder.
             Variant A: alle 9 blokke 1967-12..2024-03 (inkl. 2020-05..2024-03 med fejlalarmen).
             Variant B: kun de 8 komplette cyklusser (gunstigst for modellen).
  hovedbog   T = 5, 10, 20, 50, 100, 150, 200 aar SCOREDE kalendermaaneder (laeg ca. 2,5 aars
  simuleret  modning til: 12 mdr vindue + 18 mdr gulv). Start et TILFAELDIGT sted i cyklussen:
             foerste blok traekkes laengdevaegtet, startmaaned uniform i blokken; derefter blokke
             uniformt med tilbagelaegning; sidste blok afskaeres. 3000 hovedboeger pr. T, seed 11.
  tests      ensidet 5 %, H0 "ingen log-loss-gevinst mod 18,0 %":
             cluster-t  cluster-robust t paa blokstykker, df = K-1 (K >= 2 kraeves)
             boot44     diagnostik 4.4's form: blok-bootstrap (600 traek) af middel(d); forkast hvis
                        andel <= 0 er < 5 %
             naiv       iid-t paa maanedsraekkerne (ignorerer overlap og cyklus)
             wild       TILFOEJET (skeptikerens korrektion: cluster-t holder ikke niveauet): restrik-
                        tiv wild-cluster-bootstrap (Rademacher-fortegn paa de centrerede blokstykke-
                        summer, 600 traek, egen RNG-stroem); forkast hvis P(t* >= t) < 5 %. Ved K <= 3
                        blokstykker er fortegnsfordelingen degenereret (K = 2: t* i {0, +-n/|N1-N2|}, saa
                        p er 0 eller >= 0,25); testens reelle niveau ses i H0-tabellen og pr. K.
  H1         d som historisk (styrke). H0: d centreret (d - middel over puljens raekker), blok-
             strukturen bevaret (stoerrelse / falsk-positiv-rate). Stoerrelsesjusteret styrke =
             andel H1-hovedboeger hvis statistik overstiger H0's empiriske 95 %-fraktil.
             NB: i variant A er det centrerede H0 en blanding: hovedboeger UDEN fejlalarm-blokken
             har positiv drift (+0,075 pr. raekke), hovedboeger MED den negativ. Raterne rapporteres
             derfor ogsaa betinget paa, om fejlalarm-blokken indgaar.
  parametrisk diagnostik.json `styrke` (26 blokke / 168 aar) gengives; samme formel paa
             4.4-intervallet og paa de 9 maanedlige bloksummer her.

Output: analyser/styrke_simulation_resultat.json. Kun fakta og tal til raadets 2027-dagsorden.
Scriptet AENDRER INTET I DRIFTEN: ingen vaegte, ingen P, ingen hovedbogsraekke, ingen anden fil.
Deterministisk (faste seeds); eneste vaegur-felt er created_utc.

Koer:  cd v5 && python analyser/styrke_simulation.py        (kun stdlib + numpy)
"""
import json, sys
from datetime import datetime, timezone
from math import sqrt
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent          # v5/analyser
V5 = HERE.parent
sys.path.insert(0, str(V5))
import numpy as np
import calibrate as C
import ablation2_nber as A2

OUT = HERE / "styrke_simulation_resultat.json"
SNAP = V5 / "data" / "raw" / "2026-09-19"
R_SCORE = A2.midx(2026, 9)
L = A2.L_EMBARGO
B0 = 0.18                                        # hovedbogens loggede basisrate (weights.json: 0,1798 -> 18,0 %)
T_GRID = (5, 10, 20, 50, 100, 150, 200)
NSIM, NBOOT, SEED = 3000, 600, 11
Z95, Z80 = 1.6449, 0.8416
# ensidet 95 %-fraktil af t-fordelingen (tabel; naermeste df opad)
TCRIT = {1: 6.314, 2: 2.920, 3: 2.353, 4: 2.132, 5: 2.015, 6: 1.943, 7: 1.895, 8: 1.860, 9: 1.833, 10: 1.812,
         12: 1.782, 15: 1.753, 20: 1.725, 25: 1.708, 30: 1.697, 40: 1.684, 60: 1.671, 120: 1.658}


def tcrit(df):
    for k in sorted(TCRIT):
        if k >= df:
            return TCRIT[k]
    return Z95


def ym(m):
    return f"{m // 12}-{m % 12 + 1:02d}"


def r4(x):
    return None if x is None else round(float(x), 4)


# ------------------------------------------------------------------ 1. panel og kontrol
def byg_panel():
    usrec = A2.load_usrec(SNAP)
    eps = A2.episodes_from_usrec(usrec)
    avail = A2.load_announcements(eps, usrec=usrec)
    Dc = A2.build_dataset(SNAP, ["curve"])
    ref, _, _ = A2.wf_nber(Dc, eps, avail, usrec, L, R_score=R_SCORE)
    ll, bl, imp, br = C.metrics(ref)
    kontrol = dict(n_origins=len(ref), n_pos=int(sum(r[3] for r in ref)), log_loss=r4(ll), base_log_loss=r4(bl),
                   skill_pct=r4(imp), brier_skill_pct=r4(br), publiceret=dict(n_origins=198, skill_pct=27.05, brier_skill_pct=24.15))
    return usrec, eps, avail, Dc, kontrol


def maanedlig_hovedbog(usrec, eps, avail, Dc):
    """Maanedlige hovedbogsraekker (m, p, y, traeningsbasisrate) — reviewets pw_monthly_wf.py-regler."""
    shiller = C.read_shiller(SNAP)
    gs10 = C.read_fred(SNAP, "GS10"); tb3ms = C.read_fred(SNAP, "TB3MS")
    keys, M = C.build_monthly(shiller, gs10, tb3ms)
    curve_m = {A2.midx(y, m): float(v) for (y, m), v in zip(keys, M["curve"]) if not np.isnan(v)}
    maxdiff = max(abs(Dc["F"][j, 0] - curve_m[int(Dc["qend"][j])]) for j in range(len(Dc["qend"]))
                  if int(Dc["qend"][j]) in curve_m)
    onsets = [o for o, _ in eps]
    _, win_onsets, _ = A2.nber_labels(Dc, eps, usrec)
    rows = []
    n = len(Dc["qend"])
    for i in range(n):
        if Dc["year"][i] < 1960:
            continue
        R = int(Dc["qend"][i])
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
        if yR.sum() < 6:
            continue
        X = Dc["F"][tr]; mu, sd = X.mean(0), X.std(0, ddof=1); sd[sd == 0] = 1
        w = C.fit((X - mu) / sd, yR)
        for m in (R, R + 1, R + 2):
            if m + 12 + L > R_SCORE or m not in curve_m:
                continue
            if usrec.get(m, 0) == 1:
                continue                          # orakel-censurering som primaermetrikken
            p = float(C.predict(w, (np.array([[curve_m[m]]]) - mu) / sd)[0])
            y = 1.0 if any(m + 1 <= o <= m + 12 for o in onsets) else 0.0
            rows.append((m, p, y, float(yR.mean())))
    return rows, onsets, [t for _, t in eps], float(maxdiff)


# ------------------------------------------------------------------ 2. blokke
def byg_blokke(rows, onsets, troughs):
    m_arr = np.array([r[0] for r in rows])
    P = np.clip(np.array([r[1] for r in rows]), 1e-6, 1 - 1e-6)
    Y = np.array([r[2] for r in rows])
    Lm = -(Y * np.log(P) + (1 - Y) * np.log(1 - P))
    L0 = -(Y * np.log(B0) + (1 - Y) * np.log(1 - B0))
    start, slut = int(m_arr.min()), int(m_arr.max())
    gr = [start - 1] + [t for t in sorted(troughs) if start <= t <= slut] + [slut]
    blokke = []
    for a, b in zip(gr[:-1], gr[1:]):
        idx = np.where((m_arr > a) & (m_arr <= b))[0]
        md = {int(m_arr[i]): (float(L0[i]), float(Lm[i])) for i in idx}
        ons = [o - (a + 1) for o in sorted(onsets) if a < o <= b]
        s0, s1 = float(L0[idx].sum()), float(Lm[idx].sum())
        blokke.append(dict(fra=a + 1, til=b, kal=b - a, n=len(idx), ons=ons[0] if ons else None,
                           onset_maaned=ym(ons[0] + a + 1) if ons else None,
                           pm=[md.get(mm) for mm in range(a + 1, b + 1)], s0=s0, s1=s1,
                           sum_d=s0 - s1, pos=int(Y[idx].sum())))
    return blokke, L0, Lm, Y, P


def blok_tabel(blokke):
    return [dict(fra=ym(b["fra"]), til=ym(b["til"]), kal_mdr=b["kal"], scorede=b["n"], positive=b["pos"],
                 onset=b["onset_maaned"], komplet=b["ons"] is not None, sum_d=r4(b["sum_d"]),
                 middel_d=r4(b["sum_d"] / b["n"]), skill_pct=r4((1 - b["s1"] / b["s0"]) * 100)) for b in blokke]


# ------------------------------------------------------------------ 3. simulation
def hovedbog(T, pulje, rng):
    """En simuleret hovedbog: start tilfaeldigt i cyklussen, blokke med tilbagelaegning, afskaaret ved T*12."""
    lw = np.array([b["kal"] for b in pulje], float)
    b = pulje[rng.choice(len(pulje), p=lw / lw.sum())]
    off = int(rng.integers(b["kal"]))
    tot, cl, alle, nons, hele, nfa = 0, [], [], 0, 0, 0
    while tot < T * 12:
        take = min(b["kal"] - off, T * 12 - tot)
        seg = b["pm"][off:off + take]
        if b["ons"] is not None and off <= b["ons"] < off + take:
            nons += 1
        if off == 0 and take == b["kal"]:
            hele += 1
        if b["ons"] is None:
            nfa += 1                              # stykke af den ukomplette fejlalarm-blok (2020-05..2024-03)
        v = [x for x in seg if x is not None]
        if v:
            a = np.array(v)
            cl.append((a[:, 0].sum(), a[:, 1].sum(), len(a)))
            alle.append(a[:, 0] - a[:, 1])
        tot += take; off = 0
        b = pulje[rng.integers(len(pulje))]
    return np.array(cl), np.concatenate(alle), nons, hele, nfa


def koer(T, pulje, shift=0.0, nsim=NSIM, nboot=NBOOT, seed=SEED):
    """shift = 0: H1 (historisk d). shift = middel d i puljen: H0 (centreret d, blokstruktur bevaret).
    Returnerer pr. hovedbog: statistikker og flag (ingen beslutning traeffes her)."""
    rng = np.random.default_rng(seed)
    rng_w = np.random.default_rng(seed + 1000)    # egen stroem til wild-cluster: roerer ikke de oevrige traek
    rec = dict(t_cl=np.full(nsim, -np.inf), t_naiv=np.zeros(nsim), p_boot=np.zeros(nsim), p_wild=np.ones(nsim),
               rej_cl=np.zeros(nsim, bool), rej_boot=np.zeros(nsim, bool), rej_naiv=np.zeros(nsim, bool),
               rej_wild=np.zeros(nsim, bool),
               dbar=np.zeros(nsim), skill=np.zeros(nsim), K=np.zeros(nsim, int), nons=np.zeros(nsim, int),
               hele=np.zeros(nsim, int), nfa=np.zeros(nsim, int))
    for s in range(nsim):
        cl, dd, nons, hele, nfa = hovedbog(T, pulje, rng)
        S0, S1, N = cl[:, 0], cl[:, 1], cl[:, 2]
        Dk = S0 - S1 - shift * N                  # blokstykkets sum af d (centreret under H0)
        n = N.sum(); dbar = Dk.sum() / n
        K = len(cl)
        rec["dbar"][s] = dbar; rec["skill"][s] = (1 - S1.sum() / S0.sum()) * 100
        rec["K"][s] = K; rec["nons"][s] = nons; rec["hele"][s] = hele; rec["nfa"][s] = nfa
        if K >= 2:
            sk = Dk - dbar * N
            se = sqrt((sk ** 2).sum() * K / (K - 1)) / n
            if se > 0:
                t_obs = dbar / se
                rec["t_cl"][s] = t_obs
                rec["rej_cl"][s] = t_obs > tcrit(K - 1)
                # restriktiv wild-cluster-bootstrap: nul paalagt (centrerede stykkesummer), Rademacher-fortegn
                sg = rng_w.choice(np.array([-1.0, 1.0]), size=(nboot, K))
                Dw = sg * sk
                dbw = Dw.sum(1) / n
                sw = Dw - dbw[:, None] * N
                sew = np.sqrt((sw ** 2).sum(1) * K / (K - 1)) / n
                with np.errstate(divide="ignore", invalid="ignore"):
                    tw = np.where(sew > 0, dbw / sew, 0.0)
                rec["p_wild"][s] = np.mean(tw >= t_obs)
                rec["rej_wild"][s] = rec["p_wild"][s] < 0.05
        idx = rng.integers(K, size=(nboot, K))
        bd = Dk[idx].sum(1) / N[idx].sum(1)
        rec["p_boot"][s] = np.mean(bd <= 0)
        rec["rej_boot"][s] = rec["p_boot"][s] < 0.05
        dd = dd - shift
        rec["t_naiv"][s] = dbar / (dd.std(ddof=1) / sqrt(len(dd)))
        rec["rej_naiv"][s] = rec["t_naiv"][s] > Z95
    return rec


def opsummer(T, h1, h0):
    """Een raekke i styrketabellen: styrke (H1), falsk-positiv-rate (H0) og stoerrelsesjusteret styrke."""
    n = len(h1["skill"])
    q_cl = float(np.quantile(h0["t_cl"], 0.95))
    q_nv = float(np.quantile(h0["t_naiv"], 0.95))
    q_bt = float(np.quantile(h0["p_boot"], 0.05))
    nul = h1["nons"] == 0
    q10, q50, q90 = np.percentile(h1["skill"], [10, 50, 90])

    def betinget(h, flag, m):
        return r4(h[flag][m].mean()) if m.any() else None

    fa1, fa0 = h1["nfa"] > 0, h0["nfa"] > 0
    return dict(
        T_aar=T,
        styrke=dict(cluster_t=r4(h1["rej_cl"].mean()), boot44=r4(h1["rej_boot"].mean()), naiv=r4(h1["rej_naiv"].mean()),
                    wild_cluster=r4(h1["rej_wild"].mean())),
        falsk_positiv_H0=dict(cluster_t=r4(h0["rej_cl"].mean()), boot44=r4(h0["rej_boot"].mean()), naiv=r4(h0["rej_naiv"].mean()),
                              wild_cluster=r4(h0["rej_wild"].mean())),
        fejlalarm_blok=dict(P_indgaar=r4(fa1.mean()),
                            styrke_cluster_t_med=betinget(h1, "rej_cl", fa1), styrke_cluster_t_uden=betinget(h1, "rej_cl", ~fa1),
                            falsk_positiv_cluster_t_H0_med=betinget(h0, "rej_cl", fa0),
                            falsk_positiv_cluster_t_H0_uden=betinget(h0, "rej_cl", ~fa0)),
        styrke_stoerrelsesjusteret=dict(cluster_t=r4(np.mean(h1["t_cl"] > q_cl)), naiv=r4(np.mean(h1["t_naiv"] > q_nv)),
                                        boot44=r4(np.mean(h1["p_boot"] < q_bt))),
        kritisk_vaerdi_empirisk_H0=dict(t_cluster_95=r4(q_cl), t_naiv_95=r4(q_nv), p_boot44_05=r4(q_bt)),
        P_0_onsets=r4(nul.mean()), middel_onsets=r4(h1["nons"].mean()),
        naiv_forkaster_givet_0_onsets=r4(h1["rej_naiv"][nul].mean()) if nul.any() else None,
        P_d_ikke_positiv=r4(np.mean(h1["dbar"] <= 0)),
        skill_pct_kvantiler_10_50_90=[r4(q10), r4(q50), r4(q90)],
        blokstykker_K=dict(middel=r4(h1["K"].mean()), P_K_under_2=r4(np.mean(h1["K"] < 2)), P_K_under_5=r4(np.mean(h1["K"] < 5))),
        hele_cyklusblokke=dict(middel=r4(h1["hele"].mean()), P_mindst_3=r4(np.mean(h1["hele"] >= 3))),
        n_sim=n)


def aar_til_80(tabel, noegle):
    """Foerste T i gitteret med styrke >= 0,80 og lineaer interpolation mellem nabopunkterne (groft gitter)."""
    pw = [(r["T_aar"], r[noegle]["cluster_t"]) for r in tabel]
    for i, (T, p) in enumerate(pw):
        if p >= 0.80:
            if i == 0:
                return dict(foerste_T_i_gitter=T, interpoleret_aar=None, note="naaet allerede ved mindste T")
            T0, p0 = pw[i - 1]
            interp = T0 + (0.80 - p0) / (p - p0) * (T - T0) if p > p0 else T
            return dict(foerste_T_i_gitter=T, interpoleret_aar=round(interp, 1), note="lineaer interpolation paa groft gitter")
    return dict(foerste_T_i_gitter=None, interpoleret_aar=None, note=f"ikke naaet inden {pw[-1][0]} aar (max {pw[-1][1]:.3f})")


def falsk_positiv_pr_K(h0_liste):
    """Falsk-positiv-rate under H0 fordelt paa antal blokstykker K (puljet over T-gitteret)."""
    K = np.concatenate([h["K"] for h in h0_liste])
    out = {}
    for navn, lo, hi in (("K=1", 1, 1), ("K=2", 2, 2), ("K=3", 3, 3), ("K=4", 4, 4), ("K=5-9", 5, 9), ("K>=10", 10, 10 ** 9)):
        m = (K >= lo) & (K <= hi)
        if m.sum() == 0:
            continue
        out[navn] = dict(n=int(m.sum()),
                         cluster_t=r4(np.concatenate([h["rej_cl"] for h in h0_liste])[m].mean()),
                         boot44=r4(np.concatenate([h["rej_boot"] for h in h0_liste])[m].mean()),
                         naiv=r4(np.concatenate([h["rej_naiv"] for h in h0_liste])[m].mean()),
                         wild_cluster=r4(np.concatenate([h["rej_wild"] for h in h0_liste])[m].mean()))
    return out


# ------------------------------------------------------------------ 4. parametrisk krydstjek
def parametrisk(blokke, D_mean):
    ud = {}
    dj = json.load((V5 / "diagnostik.json").open(encoding="utf-8"))
    ud["diagnostik_styrke"] = {k: dj["styrke"].get(k) for k in ("middel_d", "se_cluster_historisk", "n_blokke_historisk",
                                                                  "aar_pr_blok", "blokke_80pct", "aar_80pct")}
    plb = dj["parret_loss_bootstrap"]
    mu, (lo, hi), K9 = plb["middel_pp"], plb["interval_90"], plb["n_blokke"]
    span_aar = (blokke[-1]["til"] - blokke[0]["fra"] + 1) / 12
    se9 = (hi - lo) / (2 * Z95)
    need = ((Z95 + Z80) * se9 / mu) ** 2 * K9
    ud["fra_44_interval"] = dict(middel_d=mu, interval_90=[lo, hi], se_ved_9_blokke=r4(se9), blokke_80pct=round(need, 1),
                                 aar_80pct=round(need * span_aar / K9, 1), formel="K = ((z95+z80)*SE9/middel)^2 * 9; normal-approx")
    # samme formel paa de 9 maanedlige bloksummer her (cluster-SE ved K=9, raekkevaegtet middel)
    Dk = np.array([b["sum_d"] for b in blokke]); N = np.array([b["n"] for b in blokke], float)
    K = len(blokke); n = N.sum(); dbar = Dk.sum() / n
    sk = Dk - dbar * N; se = sqrt((sk ** 2).sum() * K / (K - 1)) / n
    need_m = ((Z95 + Z80) * se / dbar) ** 2 * K
    ud["fra_maanedlige_blokke_her"] = dict(middel_d=r4(dbar), se_cluster_K9=r4(se), t_historisk=r4(dbar / se),
                                           t_krit_df8=tcrit(8), blokke_80pct=round(need_m, 1),
                                           aar_80pct=round(need_m * span_aar / K, 1), span_aar=r4(span_aar))
    return ud


# ------------------------------------------------------------------ 5. main
def main():
    usrec, eps, avail, Dc, kontrol = byg_panel()
    print(f"kvartal-wf kontrol: n={kontrol['n_origins']} skill={kontrol['skill_pct']:.2f}% brier={kontrol['brier_skill_pct']:.2f}%")
    rows, onsets, troughs, maxdiff = maanedlig_hovedbog(usrec, eps, avail, Dc)
    blokke, L0, Lm, Y, P = byg_blokke(rows, onsets, troughs)
    D = L0 - Lm
    B = np.array([r[3] for r in rows])
    L0tr = -(Y * np.log(B) + (1 - Y) * np.log(1 - B))
    mm = [(m // 12, m % 12 + 1, p, y) for m, p, y, _ in rows]
    ll, bl, imp, br = C.metrics(mm)
    hb = dict(n_raekker=len(rows), n_pos=int(Y.sum()), foerste=ym(rows[0][0]), sidste=ym(rows[-1][0]),
              max_abs_kvartal_minus_maanedskurve=r4(maxdiff),
              skill_pct_mod_fast_18=r4((1 - Lm.mean() / L0.mean()) * 100), middel_d_mod_fast_18=r4(D.mean()),
              skill_pct_mod_poolet_basisrate=r4(imp), brier_skill_pct_mod_poolet=r4(br),
              skill_pct_mod_traeningsbasisrate=r4((1 - Lm.mean() / L0tr.mean()) * 100),
              basisrate_H0=B0, weights_base_rate=json.load((V5 / "weights.json").open(encoding="utf-8")).get("base_rate"),
              onsets_i_perioden=[ym(o) for o in onsets if rows[0][0] < o <= rows[-1][0] + 12])
    print(f"maaned-wf: n={len(rows)} pos={int(Y.sum())} skill mod 18%={hb['skill_pct_mod_fast_18']:.2f}% middel d={D.mean():.4f}")
    kom = [b for b in blokke if b["ons"] is not None]
    print("blokke:", [(ym(b['fra']), ym(b['til']), round(b['sum_d'], 2)) for b in blokke])

    varianter = {}
    h0_alle = []
    for navn, pulje in (("A_alle_9_blokke", blokke), ("B_8_komplette_cyklusser", kom)):
        d_pool = sum(b["sum_d"] for b in pulje) / sum(b["n"] for b in pulje)
        tabel = []
        print(f"\n{navn}: {len(pulje)} blokke, middel d i puljen {d_pool:.4f} (H0 = d - {d_pool:.4f})")
        print(f"  {'T':>4} {'styrke-clt':>10} {'adj':>6} {'boot44':>7} {'naiv':>6} {'wild':>6} | H0: {'clt':>5} {'boot44':>6} {'naiv':>5} {'wild':>5} | "
              f"{'P(0ons)':>7} {'P(d<=0)':>7}  skill 10/50/90")
        for T in T_GRID:
            h1 = koer(T, pulje, shift=0.0)
            h0 = koer(T, pulje, shift=d_pool)
            h0_alle.append(h0)
            r = opsummer(T, h1, h0); tabel.append(r)
            q = r["skill_pct_kvantiler_10_50_90"]
            print(f"  {T:>4} {r['styrke']['cluster_t']:>10.3f} {r['styrke_stoerrelsesjusteret']['cluster_t']:>6.3f} "
                  f"{r['styrke']['boot44']:>7.3f} {r['styrke']['naiv']:>6.3f} {r['styrke']['wild_cluster']:>6.3f} | "
                  f"{r['falsk_positiv_H0']['cluster_t']:>9.3f} {r['falsk_positiv_H0']['boot44']:>6.3f} {r['falsk_positiv_H0']['naiv']:>5.3f} "
                  f"{r['falsk_positiv_H0']['wild_cluster']:>5.3f} | "
                  f"{r['P_0_onsets']:>7.3f} {r['P_d_ikke_positiv']:>7.3f}  {q[0]:+6.1f}/{q[1]:+5.1f}/{q[2]:+5.1f}")
        varianter[navn] = dict(n_blokke=len(pulje), middel_d_pulje=r4(d_pool), H0_shift=r4(d_pool), tabel=tabel,
                               aar_til_80pct_styrke=dict(nominel_cluster_t=aar_til_80(tabel, "styrke"),
                                                         stoerrelsesjusteret_cluster_t=aar_til_80(tabel, "styrke_stoerrelsesjusteret")))
        print("  80 %:", varianter[navn]["aar_til_80pct_styrke"])

    res = dict(
        navn="styrke_simulation", besvarer="G3.2 (kode-review 2026-10-15)", version_kontekst="v5.0.1",
        created_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        aendrer_intet_i_driften=True,
        snapshot=SNAP.name, R_score=ym(R_SCORE), L_embargo=L, seed=SEED, n_sim=NSIM, n_boot=NBOOT, T_gitter=list(T_GRID),
        design=dict(hovedbog="maanedlig walk-forward, kvartalsvaegte paa maanedskurven, orakel-censurering, modne origins",
                    blok="bund til bund (trough -> trough), kalendermaaneder inkl. censurerede",
                    start="tilfaeldigt sted i cyklussen (foerste blok laengdevaegtet, offset uniform), derefter uniform m. tilbagelaegning",
                    H0="d centreret med puljens raekkevaegtede middel; blokstruktur bevaret",
                    tests="ensidet 5 %: cluster-t (df=K-1), boot44 (600 blok-bootstrap-traek, forkast hvis andel<=0 < 5 %), naiv iid-t, "
                          "wild-cluster (restriktiv Rademacher-bootstrap paa centrerede blokstykkesummer, 600 traek, egen RNG seed+1000)",
                    stoerrelsesjusteret="H1-statistik > H0's empiriske 95 %-fraktil (boot44: p < H0's 5 %-fraktil)",
                    T="aar SCOREDE kalendermaaneder; laeg ca. 2,5 aars modning til (12 mdr vindue + 18 mdr gulv)"),
        kvartal_wf_kontrol=kontrol, maanedlig_hovedbog=hb, blokke=blok_tabel(blokke),
        parametrisk=parametrisk(blokke, D.mean()),
        simulation=varianter,
        falsk_positiv_H0_pr_antal_blokstykker=falsk_positiv_pr_K(h0_alle),
        forbehold=[
            "Simulationen antager, at fremtidige cykler er resamples af de 9 (hhv. 8) historiske blokke 1967-12..2024-03.",
            "Hovedbogen er en rekonstrueret MAANEDLIG walk-forward (kvartalsvaegte paa maanedskurven), ikke den publicerede kvartals-wf; "
            "basisraten er fast 18,0 % (den loggede), ikke den poolede.",
            "Censureringen er orakel (endelig kronologi) som primaermetrikken; den levende hovedbog censurerer kun annoncerede recessioner "
            "(BEDOEMMELSESNOEGLE (d)), saa dens forventede skill er lavere (diagnostik 4.5: +20,4 %).",
            "T-gitteret er groft (5/10/20/50/100/150/200); 'aar til 80 %' er lineaer interpolation og en stoerrelsesorden, ikke et punktestimat.",
            "cluster-t's styrkekurve er ikke monoton i variant A: den afhaenger af om fejlalarm-blokken 2020-05..2024-03 traekkes, og af "
            "t-kritiske vaerdier ved smaa K; under H0 holder den ikke sit nominelle niveau ved faa blokke.",
            "H0 er 'centreret d' (samme spredning som historikken); andre nulhypoteser (fx P = 18 % overalt) er ikke simuleret. "
            "I variant A er det en blanding: hovedboeger uden fejlalarm-blokken har positiv drift, med den negativ; se 'fejlalarm_blok'.",
            "Wild-cluster-testen er tilfoejet ud over reviewets tre tests (skeptikerens korrektion). Den er en restriktiv bootstrap: den "
            "observerede t er ikke blandt de 2^K fortegnsudfald, og ved K <= 3 blokstykker er t*-fordelingen degenereret (K = 2: "
            "t* i {0, +-n/|N1-N2|}), saa p kan vaere 0. Dens reelle niveau staar i 'falsk_positiv_H0' og pr. K; den er IKKE "
            "stoerrelseskontrolleret ved faa blokke.",
        ])
    OUT.write_text(json.dumps(res, ensure_ascii=True, indent=1), encoding="utf-8")
    print("\nskrevet", OUT)


if __name__ == "__main__":
    main()
