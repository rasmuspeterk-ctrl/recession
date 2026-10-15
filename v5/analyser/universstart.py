#!/usr/bin/env python3
"""
analyser/universstart.py — raekkeuniversets start: 1947Q2 (protokol) mod 1953Q2 og 1960Q1.

FORMAAL
  Kode-review 2026-10-15, fund F34: raekkeuniverset starter 1947Q2 (protokolkonstant C.START_QK,
  RAADETS_V501 §2), inkl. 24 kvartaler (1947Q2..1953Q1) hvor den lange rente er Shillers LTR i stedet for
  GS10 (GS10 findes foerst fra 1953-04), og dommens basisrate (18,0 %) er FIT-samplets rate, ikke
  walk-forwardens poolede rate (~16,2 %). Spoergsmaalet: aendrer universets start gaten, baandet og dommen?

HVAD BEREGNES (paa v5.0.1-panelet: snapshot data/raw/2026-09-19, R = 2026-09, samme som manifest 72c3371d)
  For hver start i {1947Q2, 1953Q2, 1960Q1}, curve-only (og fuldmodel F5 til gaten):
    - endeligt fit (finalize6.fit_model, §3.5-regler): vaegte w, mu/sd, raa beta/alpha, n_obs, n_pos, basisrate,
      antal LTR-kvartaler i fittet, andel foer 1960
    - P ved broens faste input (+0,96 pp = maanedstal 2026-08 i snapshottet), ved dagens live-kurve (trailing
      maaned af DGS10-DTB3 i snapshot 2026-10-15, pinnet) og ved maanedstallet 2026-09
    - estimation-sensitivity-baandet (finalize6.boot_weights, seed 42, 1000 traek) og motorens to domsregler
      (baandet udelukker basisraten / parret Delta-regel §4.3) ved begge input -> dom-ord som i hovedbogen
    - walk-forward (ablation2.wf_nber, L=18, R_score=R): n, poolet basisrate, log-loss- og Brier-forbedring
      mod (a) poolet rate (publiceret definition), (b) den frosne fit-basisrate, (c) expanding intercept (§3.6);
      desuden skill paa de origins alle tre starter har til faelles ("samme origins")
    - oracle-fri supplement (diagnostik §4.5, censur='realtid')
    - gaten (V501 §6): fuldmodel mod curve-only paa identiske origins, forskel i pp mod MDE 4,42 pp (trin 3)
      og gatens egen MDE (1,96 x episode-blok-bootstrap-SD, F8)
  Plus: walk-forwardens poolede basisrate mod fit-basisraten, pr. start.

DESIGN
  Rent laesende: genbruger kaedens egne funktioner (calibrate, ablation2_nber, finalize6, ablation3_frekvens,
  diagnostik) uden at kalde noget, der skriver. Universet skaeres ved at fjerne raekker foer startkvartalet
  fra build_dataset-outputtet (samme metode som review/univers.py, f34_skeptic.py og
  diagnostik.start_sensitivitet). Deterministisk: faste seeds (finalize6.SEED/ablation3.SEED), ingen
  vaegur i resultatet ud over created_utc. Kun stdlib + numpy.

AENDRER INTET I DRIFT: skriver kun analyser/universstart_resultat.json. Roerer hverken weights.json,
  manifester, hovedbog, diagnostik.json eller protokolkonstanten. Fakta og tal til raadets dagsorden 2027,
  ingen beslutning.

Koer:  cd v5 && python analyser/universstart.py
"""
import hashlib, json, sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent          # v5/analyser
V5 = HERE.parent                                # v5
sys.path.insert(0, str(V5))

import calibrate as C            # noqa: E402
import ablation2_nber as A2      # noqa: E402
import ablation3_frekvens as A3  # noqa: E402
import finalize6 as F6           # noqa: E402
import diagnostik as DG          # noqa: E402

SNAPSHOT = "2026-09-19"          # kalibreringen i drift (manifest 72c3371d, refit_maaned 2026-09)
R = A2.midx(2026, 9)
LIVE_SNAPSHOT = "2026-10-15"     # nyeste komplette snapshot ved analysens tilblivelse (pinnet for determinisme)
STARTER = [("1947Q2", (1947, 2)), ("1953Q2", (1953, 2)), ("1960Q1", (1960, 1))]
L = A2.L_EMBARGO
WF_START = 1960
MDE_FIL = V5 / "ablation3_resultat.json"
UD = HERE / "universstart_resultat.json"


def qs(qk):
    return f"{qk[0]}Q{qk[1]}"


def sub(D, fra):
    """Raekkeuniverset fra og med kvartal `fra` (samme snit som diagnostik.start_sensitivitet)."""
    keep = [i for i, qk in enumerate(D["qk"]) if qk >= fra]
    return dict(F=D["F"][keep], feats=D["feats"], Y_tek=D["Y_tek"][keep], qk=[D["qk"][i] for i in keep],
                qend=D["qend"][keep], year=D["year"][keep])


def metrics_mod_base(rows, b):
    """Log-loss- og Brier-forbedring mod en FAST basisrate b (ikke den poolede)."""
    p = np.clip(np.array([r[2] for r in rows]), 1e-6, 1 - 1e-6)
    y = np.array([r[3] for r in rows])
    ll = -np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))
    bl = -np.mean(y * np.log(b) + (1 - y) * np.log(1 - b))
    brier = (1 - np.mean((p - y) ** 2) / np.mean((b - y) ** 2)) * 100
    return round(float((1 - ll / bl) * 100), 2), round(float(brier), 2), round(float(bl), 4)


def wf_blok(rows):
    ll, bl, imp, br = C.metrics(rows)
    ys = [r[3] for r in rows]
    return dict(n=len(rows), n_pos=int(sum(ys)), foerste=f"{rows[0][0]}Q{rows[0][1]}", sidste=f"{rows[-1][0]}Q{rows[-1][1]}",
                base_rate_poolet=round(float(np.mean(ys)), 4), logloss=round(float(ll), 4),
                baseline_poolet=round(float(bl), 4), improvement=round(float(imp), 2), brier=round(float(br), 2))


def dom_ord(p, lo, hi, base):
    """Motorens domsord (motor.py, sektion 6): baandreglen."""
    udelukker = (base < lo) or (base > hi)
    if not udelukker:
        return "ikke skelnelig"
    return "under basisraten" if p < base else "over basisraten"


def baand_ved(model, W, B, x):
    """Motorens baand- og domslogik ved inputvektor x: 10-90 %-baand af P over bootstrap-vaegtene,
    baandreglen (Section 6) og den parrede Delta-regel (§4.3)."""
    ps = np.array([F6.p_af(dict(model, w=wb), x) for wb in W])
    lo, hi = float(np.percentile(ps, 10)), float(np.percentile(ps, 90))
    p = F6.p_af(model, x)
    base = model["base_rate"]
    dlt = ps - np.array(B)
    dlo, dhi = float(np.percentile(dlt, 10)), float(np.percentile(dlt, 90))
    skelnelig = bool((dlo > 0) or (dhi < 0))
    udelukker = bool((base < lo) or (base > hi))
    return dict(P=round(p, 4), P_minus_basisrate_pp=round((p - base) * 100, 2), baand=[round(lo, 4), round(hi, 4)],
                basisrate=base, baand_udelukker_basisrate=udelukker, ratio=round(p / base, 4) if udelukker else None,
                dom_ord=dom_ord(p, lo, hi, base),
                parret=dict(baand_pp=[round(dlo * 100, 2), round(dhi * 100, 2)], skelnelig=skelnelig,
                            enig_med_baandregel=skelnelig == udelukker))


def main():
    snap = V5 / "data" / "raw" / SNAPSHOT
    if not snap.exists():
        sys.exit(f"FEJL: snapshot {snap} mangler")
    meta = json.loads((snap / "meta.json").read_text(encoding="utf-8"))
    live_snap = V5 / "data" / "raw" / LIVE_SNAPSHOT
    live_note = "pinnet"
    if not live_snap.exists():
        live_snap = C.find_snapshot([])
        live_note = f"pinnet snapshot {LIVE_SNAPSHOT} mangler — nyeste komplette ({live_snap.name}) brugt"
    LI = C.live_kurve(live_snap)

    usrec = A2.load_usrec(snap)
    eps = A2.episodes_from_usrec(usrec)
    avail = A2.load_announcements(eps, usrec=usrec)      # F7-krydstjek som i finalize6
    D0c = A2.build_dataset(snap, ["curve"])
    D05 = A2.build_dataset(snap, C.F5)

    # Input-punkter: broens faste input (maanedstal i kalibreringssnapshottet), dagens live-kurve, maanedstal nu
    x_bro = F6.live_x(snap)                                    # = {'curve': 0.96} (maanedstal 2026-08; ingen daglige serier)
    x_live = {"curve": float(LI["curve"])}
    x_mdl = {"curve": float(LI["maanedlig"]["curve"])}
    INPUT = {"bro": x_bro, "live_i_dag": x_live, "maanedlig_nu": x_mdl}

    # LTR-kvartaler: kvartalets sidste maaned uden GS10 -> curve = Shiller LTR - TB3MS (to_quarterly tager sidste maaned)
    gs10 = C.read_fred(snap, "GS10")
    gs10_foerste = min(gs10)
    ltr_univers = [qk for qk in D0c["qk"] if (qk[0], qk[1] * 3) not in gs10]

    W_drift = json.loads((V5 / "weights.json").read_text(encoding="utf-8"))
    manifest = json.loads((V5 / "kalibreringer" / f"manifest_{W_drift['manifest_hash']}.json").read_text(encoding="utf-8"))
    mde_trin3 = json.loads(MDE_FIL.read_text(encoding="utf-8")).get("mde_pp") if MDE_FIL.exists() else None

    starter, wf_rows, wf5_rows = {}, {}, {}
    for navn, st in STARTER:
        Dc, D5 = sub(D0c, st), sub(D05, st)

        # ---- endeligt fit (curve-only) ----
        mc = F6.fit_model(Dc, eps, avail, usrec, R)
        orig = mc["_origins"]
        foer60 = [l for y, q, l in orig if y < 1960]
        ltr_fit = [(y, q) for y, q, _ in orig if (y, q * 3) not in gs10]
        fit = dict(n_obs=mc["n_obs"], n_pos=mc["n_pos"], base_rate=mc["base_rate"], w=mc["w"], mu=mc["mu"], sd=mc["sd"],
                   raa=dict(beta_curve_pr_pp=mc["raa"]["beta_curve_pr_pp"], alpha=mc["raa"]["alpha"]),
                   foerste_origin=f"{orig[0][0]}Q{orig[0][1]}", estimering_slut=mc["estimering_slut"],
                   ltr_kvartaler_i_fit=len(ltr_fit),
                   foer_1960=dict(n=len(foer60), n_pos=int(sum(foer60)),
                                  rate=round(sum(foer60) / len(foer60), 4) if foer60 else None),
                   fra_1960=dict(n=len(orig) - len(foer60), n_pos=mc["n_pos"] - int(sum(foer60)),
                                 rate=round((mc["n_pos"] - sum(foer60)) / (len(orig) - len(foer60)), 4)))
        model = dict(features=mc["features"], mu=mc["mu"], sd=mc["sd"], w=mc["w"], base_rate=mc["base_rate"])
        P = {k: round(F6.p_af(model, x), 4) for k, x in INPUT.items()}

        # ---- baand + dom (motorens regler) ----
        W, B, ngrp, _grp = F6.boot_weights(mc["_Z"], mc["_y"], Dc["qend"][mc["_elig"]], eps, F6.NDRAW)
        band_sha = hashlib.sha256(json.dumps([W, B]).encode("utf-8")).hexdigest()[:16]
        baand = {k: baand_ved(model, W, B, x) for k, x in INPUT.items()}
        boot = dict(seed=F6.SEED, n_draws=len(W), n_blokke=ngrp, band_sha256=band_sha,
                    W_10_90=[round(float(np.percentile([w[1] for w in W], 10)), 4), round(float(np.percentile([w[1] for w in W], 90)), 4)],
                    base_10_90=[round(float(np.percentile(B, 10)), 4), round(float(np.percentile(B, 90)), 4)])

        # ---- walk-forward (protokol: wf_nber, L=18, R_score=R) ----
        rows, power, _ = A2.wf_nber(Dc, eps, avail, usrec, L, start=WF_START, R_score=R)
        wf_rows[navn] = rows
        wf = wf_blok(rows)
        imp_f, br_f, bl_f = metrics_mod_base(rows, mc["base_rate"])
        wf["mod_fit_basisrate"] = dict(basisrate=mc["base_rate"], baseline=bl_f, improvement=imp_f, brier=br_f)
        recs = DG.wf(Dc, eps, avail, usrec, R, start=WF_START, censur="endelig")
        wf["mod_expanding_intercept"] = DG.skill_expanding(recs)
        wf["poolet_minus_fit_basisrate_pp"] = round((wf["base_rate_poolet"] - mc["base_rate"]) * 100, 2)
        wf["power_min_pos_i_traening"] = int(min(p for (_, p, _) in power))
        wf["power_median_pos_i_traening"] = int(np.median([p for (_, p, _) in power]))

        # ---- oracle-fri supplement (diagnostik §4.5) ----
        rt = DG.wf(Dc, eps, avail, usrec, R, start=WF_START, censur="realtid")
        oracle = DG.skill(rt)

        # ---- gaten (V501 §6) ----
        identiske = A2.samme_origins(Dc, D5)
        gate = dict(identiske_origins=bool(identiske), curve_only_wf=wf["improvement"], curve_only_brier=wf["brier"])
        fm = None
        if identiske:
            r5, _, _ = A2.wf_nber(D5, eps, avail, usrec, L, start=WF_START, R_score=R)
            _, _, imp5, br5 = C.metrics(r5)
            gap = float(imp5 - wf["improvement"])
            paired = [(y, q, p5, pc, yy) for (y, q, p5, yy), (_, _, pc, _) in zip(r5, rows)]
            assert [(a[0], a[1]) for a in r5] == [(a[0], a[1]) for a in rows]
            _md, sd_g, _lo, _hi = A3.mde_bootstrap(paired, eps)
            mde_gate = round(1.96 * sd_g, 2) if sd_g is not None else None
            wf5_rows[navn] = r5
            gate.update(fuldmodel_wf=round(float(imp5), 2), fuldmodel_brier=round(float(br5), 2), n_origins=len(r5),
                        foerste_origin=f"{r5[0][0]}Q{r5[0][1]}",
                        fuldmodel_vaerste_fejlalarm=F6.vaerste_fejlalarm(r5), curve_only_vaerste_fejlalarm=F6.vaerste_fejlalarm(rows),
                        fuldmodel_vaerste_origins=[dict(origin=f"{yy}Q{q}", p=round(p, 4), Y=int(y))
                                                   for yy, q, p, y in sorted(r5, key=lambda r: -DG.loss(r[2], r[3]))[:5]],
                        forskel_pp=round(gap, 2), mde_pp=mde_trin3, mde_gate_pp=mde_gate,
                        fuldmodel_slaar=bool(imp5 > wf["improvement"]),
                        raadsbeslutning_paakraevet=bool(mde_trin3 is not None and gap > mde_trin3),
                        status=F6.fuldmodel_status(dict(fuldmodel_slaar=bool(imp5 > wf["improvement"]),
                                                        raadsbeslutning_paakraevet=bool(mde_trin3 is not None and gap > mde_trin3))))
            m5 = F6.fit_model(D5, eps, avail, usrec, R)
            fm = dict(n_obs=m5["n_obs"], n_pos=m5["n_pos"], base_rate=m5["base_rate"], w=m5["w"],
                      P={k: round(F6.p_af(dict(features=m5["features"], mu=m5["mu"], sd=m5["sd"], w=m5["w"]),
                                          dict(manifest["modeller"]["fuldmodel"]["mu"], **x)), 4) for k, x in INPUT.items()},
                      P_note="fuldmodellens oevrige features sat til deres mu i manifest 72c3371d (kun kurven varieres) — "
                             "illustrativt, ikke motorens live-vektor")
        else:
            gate["note"] = "comparison unavailable — origin-identiteterne matcher ikke"

        starter[navn] = dict(start=qs(st), univers=dict(n_raekker=len(Dc["qk"]), foerste=qs(Dc["qk"][0]), sidste=qs(Dc["qk"][-1])),
                             fit=fit, P=P, baand=baand, bootstrap=boot, wf=wf, oracle_fri_4_5=oracle, gate=gate, fuldmodel_fit=fm)

    # ---- samme origins: faellesmaengden af de tre starters scorede origins ----
    keys = [set((y, q) for y, q, _, _ in wf_rows[n]) for n, _ in STARTER]
    faelles = sorted(set.intersection(*keys))
    faelles_blok = dict(n=len(faelles), foerste=qs(faelles[0]), sidste=qs(faelles[-1]), pr_start={})
    for navn, _ in STARTER:
        sel = [r for r in wf_rows[navn] if (r[0], r[1]) in set(faelles)]
        b = wf_blok(sel)
        faelles_blok["pr_start"][navn] = dict(n=b["n"], n_pos=b["n_pos"], base_rate_poolet=b["base_rate_poolet"],
                                              improvement=b["improvement"], brier=b["brier"], logloss=b["logloss"])
        if navn in wf5_rows:                      # gaten paa de samme origins: fuldmodellen scoret paa faellesmaengden
            b5 = wf_blok([r for r in wf5_rows[navn] if (r[0], r[1]) in set(faelles)])
            faelles_blok["pr_start"][navn].update(fuldmodel_improvement=b5["improvement"], fuldmodel_brier=b5["brier"],
                                                  gate_forskel_pp=round(b5["improvement"] - b["improvement"], 2))
        starter[navn]["wf_samme_origins"] = faelles_blok["pr_start"][navn]
    # ekstra: protokolmodellen (1947Q2) scoret paa hver anden starts EGET origin-saet
    for navn, _ in STARTER[1:]:
        egne = set((y, q) for y, q, _, _ in wf_rows[navn])
        sel = [r for r in wf_rows["1947Q2"] if (r[0], r[1]) in egne]
        b = wf_blok(sel)
        starter[navn]["wf_protokol_paa_disse_origins"] = dict(n=b["n"], improvement=b["improvement"], brier=b["brier"],
                                                               note="1947Q2-walk-forwardens P'er scoret paa praecis denne starts scorede origins")

    # ---- selvtjek mod kalibreringen i drift (1947Q2 skal reproducere manifest 72c3371d) ----
    s47 = starter["1947Q2"]
    ref = dict(w=W_drift["op"]["w"], base_rate=W_drift["base_rate"], n_obs=W_drift["n_obs"],
               wf_improvement=W_drift["op"]["wf_improvement"], wf_brier=W_drift["op"]["wf_brier"],
               fuldmodel_wf=W_drift["gate"].get("fuldmodel_wf"), forskel_pp=W_drift["gate"].get("forskel_pp"),
               bro_P_iii=W_drift["bro"]["trin"]["iii_udvidet_panel"]["P"], bro_input=W_drift["bro"]["input_vektor"]["curve"],
               # manifest 72c3371d er fra foer F54 (ingen bootstrap.band_sha256): samme fallback som finalize6 — weights.json's baand
               band_sha256=((manifest.get("bootstrap") or {}).get("band_sha256")
                            or hashlib.sha256(json.dumps([W_drift["band"]["W"], W_drift["band"]["base"]]).encode("utf-8")).hexdigest()[:16]),
               diagnostik_oracle_fri=None)
    dj = V5 / "diagnostik.json"
    if dj.exists():
        d = json.loads(dj.read_text(encoding="utf-8"))
        o = (d.get("oracle_fri") or {}).get("alle_live_publicerbare") or {}
        ref["diagnostik_oracle_fri"] = dict(n=o.get("n"), improvement=o.get("improvement"))
        ref["diagnostik_base_rate_poolet"] = d.get("base_rate_poolet")
    selvtjek = dict(
        w=s47["fit"]["w"] == ref["w"], base_rate=s47["fit"]["base_rate"] == ref["base_rate"], n_obs=s47["fit"]["n_obs"] == ref["n_obs"],
        wf_improvement=s47["wf"]["improvement"] == ref["wf_improvement"], wf_brier=s47["wf"]["brier"] == ref["wf_brier"],
        fuldmodel_wf=s47["gate"].get("fuldmodel_wf") == ref["fuldmodel_wf"],
        bro_P=s47["P"]["bro"] == ref["bro_P_iii"] and abs(x_bro["curve"] - ref["bro_input"]) < 1e-9,
        band_sha256=s47["bootstrap"]["band_sha256"] == ref["band_sha256"],
        oracle_fri=(ref["diagnostik_oracle_fri"] is None or
                    (s47["oracle_fri_4_5"].get("n") == ref["diagnostik_oracle_fri"]["n"]
                     and s47["oracle_fri_4_5"].get("improvement") == ref["diagnostik_oracle_fri"]["improvement"])))
    selvtjek = {k: bool(v) for k, v in selvtjek.items()}       # np.float64 == float giver np.bool_ (ikke JSON)
    selvtjek["alle_ok"] = all(selvtjek.values())

    # ---- sammenligningstabel ----
    tabel = []
    for navn, _ in STARTER:
        s = starter[navn]
        tabel.append(dict(start=navn, n_obs=s["fit"]["n_obs"], n_pos=s["fit"]["n_pos"], basisrate_fit=s["fit"]["base_rate"],
                          basisrate_wf_poolet=s["wf"]["base_rate_poolet"], w=s["fit"]["w"],
                          beta_pr_pp=s["fit"]["raa"]["beta_curve_pr_pp"], alpha=s["fit"]["raa"]["alpha"],
                          P_bro=s["P"]["bro"], P_live=s["P"]["live_i_dag"],
                          baand_bro=s["baand"]["bro"]["baand"], dom_bro=s["baand"]["bro"]["dom_ord"],
                          baand_live=s["baand"]["live_i_dag"]["baand"], dom_live=s["baand"]["live_i_dag"]["dom_ord"],
                          parret_skelnelig_bro=s["baand"]["bro"]["parret"]["skelnelig"],
                          parret_skelnelig_live=s["baand"]["live_i_dag"]["parret"]["skelnelig"],
                          wf_n=s["wf"]["n"], wf_improvement=s["wf"]["improvement"], wf_brier=s["wf"]["brier"],
                          wf_samme_origins_improvement=s["wf_samme_origins"]["improvement"],
                          oracle_fri_improvement=s["oracle_fri_4_5"].get("improvement"),
                          gate_fuldmodel_wf=s["gate"].get("fuldmodel_wf"), gate_forskel_pp=s["gate"].get("forskel_pp"),
                          gate_mde_gate_pp=s["gate"].get("mde_gate_pp"),
                          gate_raadsbeslutning=s["gate"].get("raadsbeslutning_paakraevet")))

    out = dict(
        analyse="universstart", svarer_paa="F34 (kode-review 2026-10-15)", aendrer_intet_i_drift=True,
        created_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        snapshot=SNAPSHOT, snapshot_sha256=meta["snapshot_sha256"], refit_maaned=f"{R // 12}-{R % 12 + 1:02d}",
        kalibrering_i_drift=dict(manifest_hash=W_drift["manifest_hash"], version=W_drift["version"]),
        live=dict(snapshot=live_snap.name, note=live_note, kilde=LI.get("kilde"), vindue=LI.get("vindue"), n_dage=LI.get("n_dage"),
                  curve=round(x_live["curve"], 4), maanedlig=LI["maanedlig"]),
        input_punkter={k: round(v["curve"], 4) for k, v in INPUT.items()},
        protokol=dict(START_QK=qs(C.START_QK), L_embargo=L, wf_start=WF_START, seed=F6.SEED, n_draws=F6.NDRAW, mde_trin3_pp=mde_trin3),
        ltr=dict(gs10_foerste_maaned=f"{gs10_foerste[0]}-{gs10_foerste[1]:02d}", kvartaler_i_universet=len(ltr_univers),
                 foerste=qs(ltr_univers[0]), sidste=qs(ltr_univers[-1]),
                 note="kvartalets curve = sidste maaneds GS10 - TB3MS; uden GS10 bruges Shillers LTR (calibrate.build_monthly)"),
        reference_drift=ref, selvtjek_1947Q2_mod_drift=selvtjek,
        starter=starter, samme_origins=faelles_blok, tabel=tabel,
        noter=[
            "Fit-basisraten er den frosne kalibreringsparameter i dommen (V501 §3.6); walk-forward-skillen maales mod den "
            "poolede rate over de scorede origins (C.metrics). Begge rapporteres pr. start, plus skill mod fit-raten og "
            "mod expanding intercept.",
            "Walk-forwardens scorede origin-saet afhaenger af starten (60 raekker/6 positive i traening), saa 'samme origins' "
            "= faellesmaengden; hver starts egen skill staar ved siden af.",
            "Baand og dom foelger motor.py's regler (10-90 %-baand af P over 1000 episode-blok-bootstrap-vaegte; "
            "parret Delta-regel §4.3). Coverage not established — som i drift.",
            "Universets start er en protokolkonstant (V501 §2). Intet her aendrer P, vaegte, gate eller dom i drift.",
        ])
    def _np(o):                                   # numpy-skalarer -> Python (bool_/int64/float64)
        return o.item() if hasattr(o, "item") else str(o)
    UD.write_text(json.dumps(out, indent=1, ensure_ascii=False, default=_np), encoding="utf-8")

    # ---- print ----
    print(f"=== universstart (F34) — snapshot {SNAPSHOT}, R={out['refit_maaned']}, live {live_snap.name}: kurve {x_live['curve']:+.4f} "
          f"(bro {x_bro['curve']:+.2f}, maanedlig {x_mdl['curve']:+.2f}) ===")
    print(f"LTR-kvartaler i universet: {len(ltr_univers)} ({qs(ltr_univers[0])}..{qs(ltr_univers[-1])}); GS10 fra {out['ltr']['gs10_foerste_maaned']}")
    print(f"selvtjek 1947Q2 mod drift (manifest {W_drift['manifest_hash']}): {'OK' if selvtjek['alle_ok'] else 'AFVIGER ' + str(selvtjek)}")
    print(f"\n{'start':<8}{'n_obs':>6}{'pos':>5}{'base_fit':>9}{'base_wf':>8}{'w0':>9}{'w1':>9}{'beta/pp':>9}{'alpha':>8}"
          f"{'P_bro':>7}{'P_live':>7}{'baand_live':>14}{'dom_live':>18}{'wf_n':>5}{'wf_LL':>7}{'wf_Br':>7}{'faelles':>8}{'4.5':>7}{'F5_wf':>7}{'gap':>6}")
    for t in tabel:
        print(f"{t['start']:<8}{t['n_obs']:>6}{t['n_pos']:>5}{t['basisrate_fit']*100:>8.1f}%{t['basisrate_wf_poolet']*100:>7.1f}%"
              f"{t['w'][0]:>9.4f}{t['w'][1]:>9.4f}{t['beta_pr_pp']:>9.4f}{t['alpha']:>8.4f}"
              f"{t['P_bro']*100:>6.1f}%{t['P_live']*100:>6.1f}%  {t['baand_live'][0]*100:>4.1f}-{t['baand_live'][1]*100:<5.1f}%"
              f"{t['dom_live']:>18}{t['wf_n']:>5}{t['wf_improvement']:>6.1f}%{t['wf_brier']:>6.1f}%"
              f"{t['wf_samme_origins_improvement']:>7.1f}%{(t['oracle_fri_improvement'] or float('nan')):>6.1f}%"
              f"{(t['gate_fuldmodel_wf'] if t['gate_fuldmodel_wf'] is not None else float('nan')):>6.1f}%{(t['gate_forskel_pp'] if t['gate_forskel_pp'] is not None else float('nan')):>+6.1f}")
    print(f"\nsamme origins (faellesmaengde): n={faelles_blok['n']} ({faelles_blok['foerste']}..{faelles_blok['sidste']})")
    for navn, _ in STARTER:
        s = starter[navn]
        print(f"  {navn}: dom bro '{s['baand']['bro']['dom_ord']}' (baand {s['baand']['bro']['baand']}, parret {s['baand']['bro']['parret']['baand_pp']}pp), "
              f"dom live '{s['baand']['live_i_dag']['dom_ord']}' (parret {s['baand']['live_i_dag']['parret']['baand_pp']}pp); "
              f"wf poolet-fit {s['wf']['poolet_minus_fit_basisrate_pp']:+.2f}pp; skill mod fit-rate +{s['wf']['mod_fit_basisrate']['improvement']}%, "
              f"mod expanding +{s['wf']['mod_expanding_intercept']['improvement_expanding']}%; gate: {s['gate'].get('status', s['gate'].get('note'))}")
    print(f"\n{UD.relative_to(V5)} skrevet.")


if __name__ == "__main__":
    main()
