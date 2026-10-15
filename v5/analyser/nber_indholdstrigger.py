#!/usr/bin/env python3
"""
nber_indholdstrigger.py - analyse til raadets 2027-dagsorden: hvornaar faar en NBER-datering betydning
for kalibreringen, og hvad ville en INDHOLDSTRIGGER aendre? (kode-review 2026-10-15, fund G4.1)

FORMAAL / FUNDET DER BESVARES
  G4.1: en ny top-raekke i nber_announcements.csv er en hash-trigger for rekalibrering (motor.py, §3.2b), men
  under 18-maaneders-gulvet (eligible_fit: kvartalsslut + 12 + 18 <= R) aendrer den hverken origins, labels
  eller vaegte i den refit, den udloeser. Det foerste positive label for en ny onset kan tidligst komme ind
  ved R >= (foerste kvartalsslut >= onset - 12) + 30, dvs. ca. onset + 18, og rammes i drift kun af den
  aarlige september-refit eller en tilfaeldigt senere bund-trigger. Scriptet goer det til tal:

  1. Alle post-1979-onsets (1980, 1981, 1990, 2001, 2008, 2020) med den RIGTIGE annonceringstabel:
     top- og bund-annonceringsdato, foerste R med et berettiget positivt origin (analytisk OG mekanisk via
     A2.eligible_fit), og hvad en indholdstrigger ville have gjort ved refit-tidspunkt og P, sammenlignet
     med den nuvaerende regel (september + hash). Desuden et mekanisk bevis for, at bund-raekken aldrig
     laeses af load_announcements (avail er identisk uden bund-raekker).
  2. Fremskrivning af den nuvaerende situation: NBER daterer en top i 2027-01 (USREC-onset 2027-02),
     annonceret 2027-09-15 - hvornaar aendres kalibreringen foerst, og hvor meget? Plus et sweep over
     top-maaneder 2026-09..2027-05 og et rent aritmetisk timing-grid (top-maaned x annonceringslag).

DESIGN
  - Snapshot 2026-09-19, R_drift = 2026-09 (manifest 72c3371d). finalize6.fit_model ved R_drift SKAL
    reproducere weights.json's op-vaegte, foer noget andet regnes (assertion; ellers stopper scriptet).
  - Regler, simuleret som maanedlige koersler (R = koerselsmaaned), alle med refit = finalize6.fit_model
    (praecis driftens fit: kun modne, ikke-censurerede origins, labels pr. R):
      A 'drift'         : refit hver september + ved hash-aendring af tabellen. Ritualet ligger omkring den
                          10.: en annoncering d. <= 10 rammer samme maaneds koersel, ellers naeste maaneds.
      B 'drift+indhold' : A + indholdstrigger - refit naar eligible_fit ved dagens R har et positivt label
                          eller en omlabeling 0->1, som manifestet i drift ikke har (nymodnede NEGATIVE
                          origins udloeser ikke; de venter paa september som i dag).
      C 'indhold'       : september + indholdstrigger (hash-triggeren ERSTATTET).
    Omlabelinger og nyankomne positive registreres for ALLE regler (de udloeser kun i B og C).
  - P pr. maaned: operationelle vaegte x den publicerede maanedskurve GS10 - TB3MS for maaneden foer
    koerselsmaaneden (det maanedstal motor.py's 'P paa maanedstal' viser den 10.). Forskelle maales som
    dP = P_B - P_A pr. maaned (max, middel, maaneder med afvigelse) og som max|dP| over ALLE origins i
    raekkeuniverset (finalize6.delta_vs_forrige, samme maal som manifestets delta).
  - Fremskrivning: USREC forlaenges syntetisk (USREC = 1 fra onset i 8 mdr, medianvarigheden post-1979),
    avail[onset] = annonceringsmaaneden; tabellen paa disk roeres ikke (avail bygges i hukommelsen).
    Curve-only-panelet forlaenges med 2026Q2 (komplet kvartal i snapshottet, kurven for juni 2026) ud over
    det tekniske labels univers (slutter 2026Q1): i en virkelig koersel i 2028 ville 2026Q2 vaere i
    universet med praecis den kurve. Kvartaler efter 2026Q2 er ukendte (snapshottet slutter 2026-08), saa
    refits fra 2029-03 og frem MANGLER de origins, der ville modne da - markeret i resultatet.
    Dateringens ISOLEREDE effekt = P(med onset) - P(uden onset) ved samme R og samme origins (kontrafaktisk
    koersel uden den syntetiske onset); bro-effekten = P(ny kalibrering) - P(forrige kalibrering).
  - Deterministisk: ingen stokastik (intet bootstrap-baand), ingen vaegur ud over created_utc.

AENDRER INTET I DRIFTEN: scriptet laeser snapshot, tabel og weights.json og skriver KUN
analyser/nber_indholdstrigger_resultat.json. Ingen vaegte, manifester, hovedbog eller dashboard roeres,
og intet i resultatet er en beslutning - kun tal til raadet.

Koer fra v5:  python analyser/nber_indholdstrigger.py [--snapshot data/raw/2026-09-19]
"""
import json, sys
sys.dont_write_bytecode = True
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent          # v5/analyser
V5 = HERE.parent
sys.path.insert(0, str(V5))
import calibrate as C            # noqa: E402
import ablation2_nber as A2      # noqa: E402
import finalize6 as F6           # noqa: E402

SNAPSHOT = "2026-09-19"                 # kalibreringen i drift (72c3371d) er fittet paa dette snapshot
R_DRIFT = A2.midx(2026, 9)
L = A2.L_EMBARGO                        # 18
RITUAL_DAG = 10                         # annonceret d. <= 10 -> samme maaneds koersel, ellers naeste
SIM_START = A2.midx(1977, 9)            # efter 1973-75-episodens pre-1979-konvention er faldet til ro
FREM_SLUT = A2.midx(2029, 12)
UFULDSTAENDIG_FRA = A2.midx(2029, 3)    # 2026Q3 (kurve sep 2026, ukendt) ville modne her
SCENARIE = dict(peak="2027-01", annonceret="2027-09-15", varighed_mdr=8, bund_annonceret="2028-12-15")
SWEEP_PEAKS = [A2.midx(2026, 9) + k for k in range(9)]        # 2026-09 .. 2027-05 (foerste positive origin kendt)
SWEEP_LAG = 8                                                  # mdr fra top til annoncering (historisk 4-12, median 7)
GRID_PEAKS = [A2.midx(2026, 9) + k for k in range(16)]        # 2026-09 .. 2027-12 (kun aritmetik)
GRID_LAGS = [4, 8, 12, 20]
KURVE_GRID = [-1.0, -0.5, 0.0, 0.5, 1.0, 1.5, 2.0]
UD = HERE / "nber_indholdstrigger_resultat.json"
REGLER = {"A_drift": {"september", "hash"},
          "B_drift_plus_indhold": {"september", "hash", "indhold"},
          "C_indhold_erstatter_hash": {"september", "indhold"}}


def fmt(i):
    return f"{i // 12}-{i % 12 + 1:02d}"


def qn(k):
    return f"{k[0]}Q{k[1]}"


def mid(s):
    """'YYYY-MM...' -> midx."""
    return A2.midx(int(s[:4]), int(s[5:7]))


def ren(o):
    """JSON-ren: numpy-typer -> Python, tupler -> lister, floats afrundet til 6 decimaler."""
    if isinstance(o, dict):
        return {str(k): ren(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [ren(v) for v in o]
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.floating):
        return round(float(o), 6)
    if isinstance(o, np.bool_):
        return bool(o)
    if isinstance(o, float):
        return round(o, 6)
    return o


def foerste_kvartalsslut(i):
    while (i % 12 + 1) % 3 != 0:
        i += 1
    return i


def naeste_september(i):
    return i if i % 12 == 8 else (i // 12 + (1 if i % 12 > 8 else 0)) * 12 + 8


def hash_triggere(rows):
    """{R: [raekketekst ...]} - koerselsmaaneden hvor en annoncering rammer ritualet (RITUAL_DAG)."""
    ud = {}
    for r in rows:
        a = r["announcement_date"]
        R = mid(a) + (0 if int(a[8:10]) <= RITUAL_DAG else 1)
        ud.setdefault(R, []).append(f"{r['event']} (annonceret {a})")
    return ud


def maanedskurve(snap):
    gs10, tb3 = C.read_fred(snap, "GS10"), C.read_fred(snap, "TB3MS")
    return {A2.midx(y, m): gs10[(y, m)] - tb3[(y, m)] for (y, m) in set(gs10) & set(tb3)}


def positive_ved(D, eps, avail, usrec, R, win):
    """{(aar, kvt): [annoncerede onsets i vinduet]} for de berettigede origins med label 1 ved R -
    praecis A2.eligible_fit's svar (samme funktion som finalize6.fit_model bruger)."""
    elig, yR = A2.eligible_fit(D, eps, avail, usrec, R)
    return {(int(D["qk"][j][0]), int(D["qk"][j][1])): [o for o in win[j] if avail[o] <= R]
            for j in np.where(elig & (yR == 1))[0]}


def manifest_ved(D, eps, avail, usrec, R, win):
    """Kalibreringen en refit ved R ville give (finalize6.fit_model) + positive origins pr. onset."""
    m = F6.fit_model(D, eps, avail, usrec, R)
    origins = {(y, q): l for y, q, l in m["_origins"]}
    pos_pr_onset = {}
    for k, j in enumerate(np.where(m["_elig"])[0]):
        if m["_y"][k] == 1:
            for o in win[j]:
                if avail[o] <= R:
                    pos_pr_onset[o] = pos_pr_onset.get(o, 0) + 1
    model = {k: m[k] for k in ("features", "mu", "sd", "w", "raa", "n_obs", "n_pos", "base_rate", "estimering_slut")}
    return dict(R=R, origins=origins, model=model, pos_pr_onset=pos_pr_onset)


def simuler(regel, D, eps, avail, usrec, win, hashR, pos_pr_R, man0, R0, R1, kurve):
    """Maanedlige koersler R0..R1 under en regel. Returnerer refits, P pr. maaned og manifestet i drift pr. maaned."""
    man = man0
    refits, P, man_md = [], {}, {}
    for R in range(R0, R1 + 1):
        grunde = []
        if "september" in regel and R % 12 == 8:
            grunde.append("september")
        if "hash" in regel and R in hashR:
            grunde.append("nber-hash: " + "; ".join(hashR[R]))
        pos = pos_pr_R[R]
        nye = sorted(k for k in pos if k not in man["origins"])
        omlab = sorted(k for k in pos if man["origins"].get(k) == 0)
        if "indhold" in regel and (nye or omlab):
            grunde.append("indhold: " + ", ".join([qn(k) for k in nye] + [qn(k) + " 0->1" for k in omlab]))
        if grunde:
            ny = manifest_ved(D, eps, avail, usrec, R, win)
            aendret = ny["origins"] != man["origins"] or ny["model"]["w"] != man["model"]["w"]
            refits.append(dict(R=fmt(R), trigger=grunde, kalibrering_aendret=aendret,
                               n_obs=ny["model"]["n_obs"], n_pos=ny["model"]["n_pos"], w=ny["model"]["w"],
                               positive_der_kom_ind=[qn(k) for k in nye], omlabelede_0_til_1=[qn(k) for k in omlab],
                               positive_pr_onset_post1979={fmt(o): n for o, n in sorted(ny["pos_pr_onset"].items())
                                                           if o >= A2.POST1979},
                               ufuldstaendigt_panel=bool(R >= UFULDSTAENDIG_FRA and R > R_DRIFT)))
            if aendret:
                man = ny
        man_md[R] = man
        if R - 1 in kurve:
            P[R] = F6.p_af(man["model"], {"curve": kurve[R - 1]})
    return dict(refits=refits, P=P, man=man_md)


def foerste_R_med(man_md, key, R0, R1):
    """Foerste koerselsmaaned hvor manifestet i drift har origin `key` med label 1 (None: aldrig)."""
    for R in range(R0, R1 + 1):
        if man_md[R]["origins"].get(key) == 1:
            return R
    return None


def afvigelse(sA, sB, D, R0, R1, kurve):
    """Maanedlige P-forskelle sB - sA i [R0, R1] (ved den faktiske maanedskurve) + universets max|dP| ved
    den foerste afvigende maaned. NB: en indholdsudloest refit er en FULD refit (den optager ogsaa de
    negative origins, der er modnet siden sidste refit), saa dP er refit-effekten, ikke labelen alene."""
    md = [R for R in range(R0, R1 + 1) if R in sA["P"] and R in sB["P"] and sA["man"][R]["model"]["w"] != sB["man"][R]["model"]["w"]]
    if not md:
        return dict(maaneder_med_afvigelse=0, vindue=[fmt(R0), fmt(R1)])
    dP = {R: sB["P"][R] - sA["P"][R] for R in md}
    Rm = max(md, key=lambda R: abs(dP[R]))
    R0a = md[0]
    u = F6.delta_vs_forrige(D, sB["man"][R0a]["model"], sA["man"][R0a]["model"])
    return dict(maaneder_med_afvigelse=len(md), vindue=[fmt(R0), fmt(R1)], foerste=fmt(md[0]), sidste=fmt(md[-1]),
                dP_foerste_pp=100 * dP[R0a], P_A_foerste=sA["P"][R0a], P_B_foerste=sB["P"][R0a], kurve_foerste=kurve[R0a - 1],
                max_abs_dP_pp=100 * abs(dP[Rm]), maaned_max=fmt(Rm), P_A_max=sA["P"][Rm], P_B_max=sB["P"][Rm], kurve_max=kurve[Rm - 1],
                middel_abs_dP_pp=100 * float(np.mean([abs(v) for v in dP.values()])),
                maaneder_over_0_5pp=sum(1 for v in dP.values() if abs(v) > 0.005),
                maaneder_over_1pp=sum(1 for v in dP.values() if abs(v) > 0.01),
                univers_ved_foerste=dict(max_abs_dP_pp=100 * u["max_abs_dP"], origin_max=u["origin_max"],
                                         mean_abs_dP_pp=100 * u["mean_abs_dP"], dw=u["dw_std"],
                                         d_beta_pr_pp=u["d_beta_pr_pp"], d_alpha=u["d_alpha"]),
                dP_pr_maaned_pp={fmt(R): 100 * v for R, v in dP.items()})


def isoleret(D, eps, avail, usrec, R, win, onset, kurve_x):
    """Dateringens ISOLEREDE effekt ved R: fit med onset annonceret (avail) mod samme R med onset IKKE annonceret
    (avail[onset] = aldrig; samme origins, de positive labels er provisoriske nuller). dP ved kurve_x og over universet."""
    a0 = dict(avail); a0[onset] = 10 ** 9
    ny = manifest_ved(D, eps, avail, usrec, R, win)["model"]
    kf = manifest_ved(D, eps, a0, usrec, R, win)["model"]
    u = F6.delta_vs_forrige(D, ny, kf)
    return dict(R=fmt(R), n_obs=ny["n_obs"], n_pos=ny["n_pos"], n_pos_uden_datering=kf["n_pos"], w=ny["w"], w_uden_datering=kf["w"],
                kurve=kurve_x, dP_pp=100 * (F6.p_af(ny, {"curve": kurve_x}) - F6.p_af(kf, {"curve": kurve_x})),
                P_med=F6.p_af(ny, {"curve": kurve_x}), P_uden=F6.p_af(kf, {"curve": kurve_x}),
                dP_pp_pr_kurve={f"{c:+.1f}": 100 * (F6.p_af(ny, {"curve": c}) - F6.p_af(kf, {"curve": c})) for c in KURVE_GRID},
                univers_max_abs_dP_pp=100 * u["max_abs_dP"], univers_origin_max=u["origin_max"], d_beta_pr_pp=u["d_beta_pr_pp"], d_alpha=u["d_alpha"])


def udvid_panel(snap, D):
    """Curve-only-panelet + de KOMPLETTE kvartaler efter det tekniske labels univers (samme maanedsbyggeri som
    A2.build_dataset(curve-only); kvartalet kraever sin sidste maaned i GS10 og TB3MS). Overlappet assertes identisk."""
    shiller = C.read_shiller(snap)
    gs10, tb3 = C.read_fred(snap, "GS10"), C.read_fred(snap, "TB3MS")
    faelles = sorted(set(gs10) & set(tb3))
    sidst = shiller[-1][0] if shiller else (0, 0)
    shiller = shiller + [(k, np.nan, np.nan, np.nan, np.nan) for k in faelles if k > sidst]
    keys, M = C.build_monthly(shiller, gs10, tb3)
    qkeys, cols = C.to_quarterly(keys, M, C.read_fred(snap, "A191RL1Q225SBEA"))
    idx = {qk: i for i, qk in enumerate(qkeys)}
    for j, qk in enumerate(D["qk"]):
        assert abs(cols["curve"][idx[qk]] - D["F"][j, 0]) < 1e-12, f"panel-overlap afviger ved {qk}"
    fset = set(faelles)
    ekstra = [(i, qk) for i, qk in enumerate(qkeys)
              if qk > D["qk"][-1] and (qk[0], qk[1] * 3) in fset and not np.isnan(cols["curve"][i])]
    D2 = dict(F=np.vstack([D["F"]] + [np.array([[cols["curve"][i]]]) for i, _ in ekstra]) if ekstra else D["F"].copy(),
              feats=list(D["feats"]), Y_tek=np.concatenate([D["Y_tek"], np.full(len(ekstra), np.nan)]),
              qk=list(D["qk"]) + [qk for _, qk in ekstra])
    D2["qend"] = np.array([A2.qend_idx(y, q) for (y, q) in D2["qk"]])
    D2["year"] = np.array([y for (y, _) in D2["qk"]])
    return D2, [dict(origin=qn(qk), kurve=float(cols["curve"][i]), modner=fmt(A2.qend_idx(*qk) + 12 + L)) for i, qk in ekstra]


def syntetisk(usrec, eps, avail, onset, varighed, ann_midx, horisont):
    """USREC/episoder/avail med en syntetisk onset (USREC = 1 i `varighed` mdr), 0 ellers frem til horisonten."""
    u = dict(usrec)
    for i in range(max(usrec) + 1, horisont + 1):
        u[i] = 1 if onset <= i < onset + varighed else 0
    e = A2.episodes_from_usrec(u)
    a = dict(avail)
    a[onset] = ann_midx
    assert (onset, onset + varighed - 1) in e, "syntetisk episode ikke fundet"
    return u, e, a


def timing_grid():
    """Ren aritmetik: for top-maaned x annonceringslag, hvornaar modner hvert positivt origin, hvornaar kommer
    det ind under A (september + top-hash) og under en indholdstrigger. Annoncering antages efter d. 10
    (koerslen ser den maaneden efter). Bund-trigger indgaar ikke (ukendt dato)."""
    ud = []
    for peak in GRID_PEAKS:
        onset = peak + 1
        qe = foerste_kvartalsslut(onset - 12)
        pos = [q for q in range(qe, onset, 3)]
        for lag in GRID_LAGS:
            synlig = peak + lag + 1                      # foerste koersel der ser raekken
            rk = []
            for q in pos:
                R_mod = q + 12 + L
                R_first = max(R_mod, synlig)
                R_A = min(naeste_september(R_first), synlig if synlig >= R_first else 10 ** 9)
                rk.append(dict(origin=qn((q // 12, (q % 12 + 1) // 3)), modner=fmt(R_mod), synlig_for_koerslen=fmt(R_first),
                               omlabeling=bool(synlig > R_mod), ind_under_A=fmt(R_A), ind_under_indhold=fmt(R_first),
                               forsinkelse_A_mdr=R_A - R_first, A_via=("top-hash" if R_A == synlig else "september")))
            ud.append(dict(peak=fmt(peak), onset=fmt(onset), lag_mdr=lag, annonceret=fmt(peak + lag),
                           foerste_positive_origin=rk[0]["origin"], foerste_modning=rk[0]["modner"],
                           forsinkelse_foerste_mdr=rk[0]["forsinkelse_A_mdr"],
                           origin_maaneder_forsinket_i_alt=sum(r["forsinkelse_A_mdr"] for r in rk),
                           n_septembre_under_A=len({r["ind_under_A"] for r in rk if r["A_via"] == "september"}),
                           origins=rk))
    return ud


def main():
    argv = sys.argv
    snap = Path(argv[argv.index("--snapshot") + 1]) if "--snapshot" in argv else V5 / "data" / "raw" / SNAPSHOT
    snap = snap if snap.is_absolute() else V5 / snap
    meta = json.loads((snap / "meta.json").read_text(encoding="utf-8"))
    W = json.loads((V5 / "weights.json").read_text(encoding="utf-8"))
    print(f"=== nber_indholdstrigger (G4.1) - snapshot {snap.name} - R_drift {fmt(R_DRIFT)} - manifest i drift {W.get('manifest_hash')} ===")

    usrec = A2.load_usrec(snap)
    eps = A2.episodes_from_usrec(usrec)
    rows = A2.laes_annonceringer()
    avail = A2.load_announcements(eps, usrec=usrec)           # F7-krydstjek mod USREC som i driften
    D = A2.build_dataset(snap, ["curve"])
    _, win, _ = A2.nber_labels(D, eps, usrec)
    kurve = maanedskurve(snap)
    live = float(C.live_kurve(snap)["curve"])

    # ---- 0. reproduktion af kalibreringen i drift (assertion) ----
    m0 = manifest_ved(D, eps, avail, usrec, R_DRIFT, win)
    repro = dict(n_obs=m0["model"]["n_obs"], n_pos=m0["model"]["n_pos"], w=m0["model"]["w"], mu=m0["model"]["mu"], sd=m0["model"]["sd"],
                 weights_json=dict(n_obs=W["n_obs"], w=W["op"]["w"], mu=W["op"]["mu"], sd=W["op"]["sd"], manifest=W.get("manifest_hash")))
    repro["identisk"] = (m0["model"]["w"] == W["op"]["w"] and m0["model"]["mu"] == W["op"]["mu"]
                         and m0["model"]["sd"] == W["op"]["sd"] and m0["model"]["n_obs"] == W["n_obs"])
    print(f"reproduktion R={fmt(R_DRIFT)}: n_obs {repro['n_obs']} n_pos {repro['n_pos']} w {repro['w']} -> "
          f"{'IDENTISK med weights.json' if repro['identisk'] else 'AFVIGER fra weights.json'}")
    if not repro["identisk"]:
        sys.exit("FEJL: fit_model reproducerer ikke kalibreringen i drift - forkert snapshot?")

    # ---- 1. tabellen: bund-raekken laeses ikke (mekanisk) ----
    orig = A2.laes_annonceringer
    try:
        A2.laes_annonceringer = lambda f=None: [r for r in rows if r["event"].startswith("peak")]
        avail_uden_bund = A2.load_announcements(eps)
    finally:
        A2.laes_annonceringer = orig
    bund_laeses = avail_uden_bund != avail
    print(f"avail uden bund-raekker identisk med avail: {not bund_laeses} (bund-raekken er kun hash-trigger)")

    hashR = hash_triggere(rows)
    post = [(o, t) for o, t in eps if o >= A2.POST1979]

    # ---- 2. historisk simulation af reglerne ----
    print(f"\nberegner berettigede positive pr. maaned {fmt(SIM_START)}..{fmt(R_DRIFT)} ...", flush=True)
    pos_pr_R = {R: positive_ved(D, eps, avail, usrec, R, win) for R in range(SIM_START, R_DRIFT + 1)}
    man_start = manifest_ved(D, eps, avail, usrec, SIM_START, win)
    sims = {}
    for navn, regel in REGLER.items():
        sims[navn] = simuler(regel, D, eps, avail, usrec, win, hashR, pos_pr_R, man_start, SIM_START + 1, R_DRIFT, kurve)
        s = sims[navn]
        print(f"  {navn:<26} refits {len(s['refits']):>3}  heraf aendrede {sum(r['kalibrering_aendret'] for r in s['refits']):>3}  "
              f"indholdsudloeste {sum(1 for r in s['refits'] if any(g.startswith('indhold') for g in r['trigger'])):>2}  "
              f"omlabelinger {sum(len(r['omlabelede_0_til_1']) for r in s['refits']):>2}")
    # slutkalibreringen SKAL vaere den i drift under alle regler (september 2026 fanger alt)
    for navn, s in sims.items():
        assert s["man"][R_DRIFT]["model"]["w"] == W["op"]["w"], f"{navn}: slutkalibrering != drift"

    onsets = []
    for n_, (o, t) in enumerate(post):
        peak_row = min((r for r in rows if r["event"].startswith("peak")), key=lambda r: abs(mid(r["cycle_month"]) - o))
        trough_row = min((r for r in rows if r["event"].startswith("trough")), key=lambda r: abs(mid(r["cycle_month"]) - t))
        ann = avail[o]
        pos_j = [j for j in range(len(D["qend"])) if o in win[j]]
        rec_j = [j for j in range(len(D["qend"])) if o <= D["qend"][j] <= t]
        qe_first = int(min(D["qend"][j] for j in pos_j))
        R_an = max(ann, qe_first + 12 + L)
        R_mek = min(R for R in sorted(pos_pr_R) if any(o in v for v in pos_pr_R[R].values()))
        ind = {}
        for navn, s in sims.items():
            ind[navn] = {}
            for j in pos_j:
                k = (int(D["qk"][j][0]), int(D["qk"][j][1]))
                Rk = foerste_R_med(s["man"], k, SIM_START + 1, R_DRIFT)
                ind[navn][qn(k)] = fmt(Rk) if Rk else None
        R_A = min(mid(v) for v in ind["A_drift"].values() if v)
        R_B = min(mid(v) for v in ind["B_drift_plus_indhold"].values() if v)
        R_C = min(mid(v) for v in ind["C_indhold_erstatter_hash"].values() if v)
        R_A_sidst = max(mid(v) for v in ind["A_drift"].values() if v)
        # analysevindue: fra foerste modning til A har indhentet B helt (samme vaegte igen efter A's sidste indtraeden)
        R_konv = next((R for R in range(R_A_sidst, R_DRIFT + 1)
                       if sims["A_drift"]["man"][R]["model"]["w"] == sims["B_drift_plus_indhold"]["man"][R]["model"]["w"]), R_DRIFT)
        refA = next(r for r in sims["A_drift"]["refits"] if mid(r["R"]) == R_A)
        R_top = min(R for R, v in hashR.items() if any(peak_row["event"] in x for x in v))
        ref_top = next((r for r in sims["A_drift"]["refits"] if mid(r["R"]) == R_top), None)
        qe_sidst = int(max(D["qend"][j] for j in pos_j))
        R_alle = max(ann, qe_sidst + 12 + L)                      # alle fire positive origins modne
        onsets.append(dict(
            onset_usrec=fmt(o), trough_usrec=fmt(t), varighed_mdr=t - o + 1,
            top_raekke=dict(event=peak_row["event"], cycle_month=peak_row["cycle_month"], annonceret=peak_row["announcement_date"],
                            lag_mdr=mid(peak_row["announcement_date"]) - mid(peak_row["cycle_month"]), koersel=fmt(min(R for R, v in hashR.items() if any(peak_row["event"] in x for x in v)))),
            bund_raekke=dict(event=trough_row["event"], cycle_month=trough_row["cycle_month"], annonceret=trough_row["announcement_date"],
                             lag_mdr=mid(trough_row["announcement_date"]) - mid(trough_row["cycle_month"]), koersel=fmt(min(R for R, v in hashR.items() if any(trough_row["event"] in x for x in v)))),
            positive_origins=[dict(origin=qn(D["qk"][j]), kvartalsslut=fmt(int(D["qend"][j])), modner=fmt(int(D["qend"][j]) + 12 + L),
                                   kurve=float(D["F"][j, 0])) for j in pos_j],
            foerste_R_positiv=dict(analytisk=fmt(R_an), mekanisk=fmt(R_mek), enig=R_an == R_mek,
                                   mdr_efter_onset=R_mek - o, mdr_efter_top_annoncering=R_mek - ann,
                                   mdr_efter_bund_annoncering=R_mek - mid(trough_row["announcement_date"])),
            top_hash_koersel_aendrer=dict(
                # hvad hash-koerslen efter toppen faktisk aendrede (A): nye positive for DENNE onset = 0 under gulvet
                R=fmt(R_top), positive_for_onset=ref_top["positive_pr_onset_post1979"].get(fmt(o), 0) if ref_top else None,
                kalibrering_aendret=ref_top["kalibrering_aendret"] if ref_top else None,
                positive_der_kom_ind=ref_top["positive_der_kom_ind"] if ref_top else None,
                n_obs=ref_top["n_obs"] if ref_top else None),
            in_recession_origins=[qn(D["qk"][j]) for j in rec_j],
            in_recession_frigivet_foer_annoncering=[qn(D["qk"][j]) for j in rec_j if int(D["qend"][j]) + 12 + L < ann],
            indtraeden_pr_regel=ind,
            foerste_indtraeden=dict(A_drift=fmt(R_A), A_via=refA["trigger"], B=fmt(R_B), C=fmt(R_C),
                                    forsinkelse_A_mdr=R_A - R_mek, forsinkelse_B_mdr=R_B - R_mek, forsinkelse_C_mdr=R_C - R_mek),
            sidste_indtraeden_A=fmt(R_A_sidst), konvergens_A_B=fmt(R_konv),
            origin_maaneder_forsinket_A=sum(mid(ind["A_drift"][k]) - mid(ind["B_drift_plus_indhold"][k]) for k in ind["A_drift"] if ind["A_drift"][k]),
            indholdsrefits_B=[r["R"] for r in sims["B_drift_plus_indhold"]["refits"]
                              if R_mek <= mid(r["R"]) <= R_konv and any(g.startswith("indhold") for g in r["trigger"])],
            P_afvigelse_B_minus_A=afvigelse(sims["A_drift"], sims["B_drift_plus_indhold"], D, R_mek, R_konv, kurve),
            P_afvigelse_C_minus_A=afvigelse(sims["A_drift"], sims["C_indhold_erstatter_hash"], D, R_mek, R_konv, kurve),
            # dateringens isolerede effekt (annonceret vs ikke annonceret ved samme R) ved foerste modning og naar alle fire er modne
            isoleret_dateringseffekt=dict(ved_foerste_positive=isoleret(D, eps, avail, usrec, R_mek, win, o, kurve[R_mek - 1]),
                                          ved_alle_positive=isoleret(D, eps, avail, usrec, R_alle, win, o, kurve[R_alle - 1])),
        ))
        x = onsets[-1]
        print(f"\nonset {x['onset_usrec']} (top {peak_row['cycle_month']} ann. {peak_row['announcement_date']}, bund {trough_row['cycle_month']} ann. {trough_row['announcement_date']}):"
              f" foerste positive origin {x['positive_origins'][0]['origin']} modner {x['foerste_R_positiv']['mekanisk']}"
              f" ({x['foerste_R_positiv']['mdr_efter_onset']} mdr efter onset, {x['foerste_R_positiv']['mdr_efter_top_annoncering']} efter top-ann.)")
        print(f"   ind i fittet: A {x['foerste_indtraeden']['A_drift']} via {x['foerste_indtraeden']['A_via']} (forsinkelse {x['foerste_indtraeden']['forsinkelse_A_mdr']} mdr)"
              f" | B {x['foerste_indtraeden']['B']} | C {x['foerste_indtraeden']['C']} | origin-maaneder forsinket under A i alt: {x['origin_maaneder_forsinket_A']}")
        th = x["top_hash_koersel_aendrer"]
        print(f"   top-hash-koerslen {th['R']}: kalibrering aendret {th['kalibrering_aendret']}, positive for onset {th['positive_for_onset']}, "
              f"positive der kom ind {th['positive_der_kom_ind']}")
        pa = x["P_afvigelse_B_minus_A"]
        if pa["maaneder_med_afvigelse"]:
            print(f"   P(B)-P(A) i {pa['vindue'][0]}..{pa['vindue'][1]}: {pa['maaneder_med_afvigelse']} mdr afviger, foerste {pa['foerste']} {pa['dP_foerste_pp']:+.2f}pp "
                  f"(P {pa['P_A_foerste']*100:.1f}% -> {pa['P_B_foerste']*100:.1f}% ved kurve {pa['kurve_foerste']:+.2f}), "
                  f"max|dP| {pa['max_abs_dP_pp']:.2f}pp i {pa['maaned_max']} (kurve {pa['kurve_max']:+.2f}); univers max|dP| {pa['univers_ved_foerste']['max_abs_dP_pp']:.2f}pp")
        else:
            print(f"   P(B)-P(A) i {pa['vindue'][0]}..{pa['vindue'][1]}: ingen afvigelse")
        i1, i4 = x["isoleret_dateringseffekt"]["ved_foerste_positive"], x["isoleret_dateringseffekt"]["ved_alle_positive"]
        print(f"   isoleret dateringseffekt: ved {i1['R']} (1 positiv) {i1['dP_pp']:+.2f}pp ved kurve {i1['kurve']:+.2f} (univers max {i1['univers_max_abs_dP_pp']:.2f}pp); "
              f"ved {i4['R']} ({i4['n_pos'] - i4['n_pos_uden_datering']} positive) {i4['dP_pp']:+.2f}pp ved kurve {i4['kurve']:+.2f} (univers max {i4['univers_max_abs_dP_pp']:.2f}pp)")

    # samlet A vs B / A vs C over hele simulationen
    def samlet(a, b):
        md = [R for R in a["P"] if R in b["P"] and a["man"][R]["model"]["w"] != b["man"][R]["model"]["w"]]
        d = [b["P"][R] - a["P"][R] for R in md]
        return dict(maaneder_i_alt=len(a["P"]), maaneder_med_afvigelse=len(md),
                    max_abs_dP_pp=100 * max((abs(v) for v in d), default=0.0),
                    maaned_max=fmt(md[int(np.argmax([abs(v) for v in d]))]) if d else None,
                    middel_abs_dP_pp=100 * float(np.mean([abs(v) for v in d])) if d else 0.0,
                    maaneder_over_1pp=sum(1 for v in d if abs(v) > 0.01))
    hist = dict(start=fmt(SIM_START), slut=fmt(R_DRIFT), kurve_input="GS10 - TB3MS for maaneden foer koerselsmaaneden",
                hash_koersler={fmt(R): v for R, v in sorted(hashR.items())},
                refits={navn: s["refits"] for navn, s in sims.items()},
                samlet=dict(B_minus_A=samlet(sims["A_drift"], sims["B_drift_plus_indhold"]),
                            C_minus_A=samlet(sims["A_drift"], sims["C_indhold_erstatter_hash"])),
                omlabelinger_post1979={navn: sum(len(r["omlabelede_0_til_1"]) for r in s["refits"] if mid(r["R"]) >= A2.POST1979)
                                       for navn, s in sims.items()})

    # ---- 3. fremskrivning ----
    print("\n--- fremskrivning: top 2027-01, onset 2027-02, annonceret 2027-09-15 ---")
    D2, ekstra = udvid_panel(snap, D)
    print(f"panel forlaenget med {[e['origin'] for e in ekstra]} (kurve {[round(e['kurve'], 2) for e in ekstra]})")
    _, win2, _ = A2.nber_labels(D2, eps, usrec)
    m_drift2 = manifest_ved(D2, eps, avail, usrec, R_DRIFT, win2)
    assert m_drift2["model"]["w"] == W["op"]["w"] and m_drift2["model"]["n_obs"] == W["n_obs"], "udvidet panel aendrer driftens fit"

    def frem(peak, ann_dato, varighed, bund_ann=None, lag_note=None):
        onset = peak + 1
        ann = mid(ann_dato)
        u, e, a = syntetisk(usrec, eps, avail, onset, varighed, ann, FREM_SLUT + 1)
        _, w2, _ = A2.nber_labels(D2, e, u)
        hR = {ann + (0 if int(ann_dato[8:10]) <= RITUAL_DAG else 1): [f"peak_{peak // 12} ({fmt(peak)}, annonceret {ann_dato})"]}
        hRb = dict(hR)
        if bund_ann:
            hRb.setdefault(mid(bund_ann) + (0 if int(bund_ann[8:10]) <= RITUAL_DAG else 1), []).append(
                f"trough ({fmt(onset + varighed - 1)}, annonceret {bund_ann})")
        pos2 = {R: positive_ved(D2, e, a, u, R, w2) for R in range(R_DRIFT, FREM_SLUT + 1)}
        pos0 = {R: positive_ved(D2, eps, avail, usrec, R, win2) for R in range(R_DRIFT, FREM_SLUT + 1)}
        man0 = manifest_ved(D2, e, a, u, R_DRIFT, w2)
        assert man0["model"]["w"] == W["op"]["w"]
        kurve_frem = {R: live for R in range(R_DRIFT - 1, FREM_SLUT + 1)}     # kurven holdes paa live-input (ukendt fremtid)
        kurve_frem.update({R: v for R, v in kurve.items() if R < R_DRIFT})
        S = {"A_drift": simuler(REGLER["A_drift"], D2, e, a, u, w2, hR, pos2, man0, R_DRIFT + 1, FREM_SLUT, kurve_frem),
             "A_drift_med_bundtrigger": simuler(REGLER["A_drift"], D2, e, a, u, w2, hRb, pos2, man0, R_DRIFT + 1, FREM_SLUT, kurve_frem),
             "B_drift_plus_indhold": simuler(REGLER["B_drift_plus_indhold"], D2, e, a, u, w2, hR, pos2, man0, R_DRIFT + 1, FREM_SLUT, kurve_frem),
             "C_indhold_erstatter_hash": simuler(REGLER["C_indhold_erstatter_hash"], D2, e, a, u, w2, {}, pos2, man0, R_DRIFT + 1, FREM_SLUT, kurve_frem),
             "kontrafaktisk_ingen_onset": simuler(REGLER["A_drift"], D2, eps, avail, usrec, win2, {}, pos0, m_drift2, R_DRIFT + 1, FREM_SLUT, kurve_frem)}
        pos_known = [qn(D2["qk"][j]) for j in range(len(D2["qend"])) if onset in w2[j]]
        pos_all = [qn((q // 12, (q % 12 + 1) // 3)) for q in range(foerste_kvartalsslut(onset - 12), onset, 3)]
        rt = next((r for r in S["A_drift"]["refits"] if mid(r["R"]) == min(hR)), None)
        ud = dict(peak=fmt(peak), onset=fmt(onset), annonceret=ann_dato, hash_koersel=fmt(min(hR)), usrec_1_til=fmt(onset + varighed - 1),
                  bund_annonceret=bund_ann, positive_origins_i_alt=pos_all, positive_origins_i_panelet=pos_known,
                  ukendte_positive_origins=[q for q in pos_all if q not in pos_known],
                  top_hash_koersel_aendrer=dict(R=rt["R"], kalibrering_aendret=rt["kalibrering_aendret"], n_obs=rt["n_obs"], n_pos=rt["n_pos"],
                                                positive_for_onset=rt["positive_pr_onset_post1979"].get(fmt(onset), 0),
                                                positive_der_kom_ind=rt["positive_der_kom_ind"]) if rt else None,
                  regler={})
        for navn, s in S.items():
            if navn == "kontrafaktisk_ingen_onset":
                continue
            Rf = next((mid(r["R"]) for r in s["refits"] if r["positive_pr_onset_post1979"].get(fmt(onset), 0) > 0 and r["kalibrering_aendret"]), None)
            Rc = next((mid(r["R"]) for r in s["refits"] if r["kalibrering_aendret"]), None)
            rf = next((r for r in s["refits"] if mid(r["R"]) == Rf), None) if Rf else None
            rec = dict(foerste_aendrede_kalibrering=fmt(Rc) if Rc else None,
                       foerste_refit_med_positivt_label=fmt(Rf) if Rf else None,
                       refits=s["refits"])
            if Rf:
                gl = s["man"][Rf - 1]["model"]; ny = s["man"][Rf]["model"]; kf = S["kontrafaktisk_ingen_onset"]["man"][Rf]["model"]
                rec["ved_foerste_positive"] = dict(
                    R=fmt(Rf), trigger=rf["trigger"], n_obs=ny["n_obs"], n_pos=ny["n_pos"], w=ny["w"], w_forrige=gl["w"], w_kontrafaktisk=kf["w"],
                    bro_dP_pp_ved_live_kurve=100 * (F6.p_af(ny, {"curve": live}) - F6.p_af(gl, {"curve": live})),
                    isoleret_dP_pp_ved_live_kurve=100 * (F6.p_af(ny, {"curve": live}) - F6.p_af(kf, {"curve": live})),
                    P_ny_ved_live=F6.p_af(ny, {"curve": live}), P_forrige_ved_live=F6.p_af(gl, {"curve": live}), P_kontrafaktisk_ved_live=F6.p_af(kf, {"curve": live}),
                    isoleret_dP_pp_pr_kurve={f"{c:+.1f}": 100 * (F6.p_af(ny, {"curve": c}) - F6.p_af(kf, {"curve": c})) for c in KURVE_GRID},
                    bro_univers=F6.delta_vs_forrige(D2, ny, gl), isoleret_univers=F6.delta_vs_forrige(D2, ny, kf))
            # alle positive origins i panelet: hvornaar kom de ind
            rec["indtraeden"] = {q: (fmt(foerste_R_med(s["man"], (int(q[:4]), int(q[-1])), R_DRIFT + 1, FREM_SLUT)) if foerste_R_med(s["man"], (int(q[:4]), int(q[-1])), R_DRIFT + 1, FREM_SLUT) else None)
                                 for q in pos_known}
            ud["regler"][navn] = rec
        # A vs B over horisonten (kurve = live-input)
        ud["P_afvigelse_B_minus_A_ved_live_kurve"] = afvigelse(S["A_drift"], S["B_drift_plus_indhold"], D2, R_DRIFT + 1, FREM_SLUT, kurve_frem)
        ud["P_afvigelse_Abund_minus_A_ved_live_kurve"] = afvigelse(S["A_drift"], S["A_drift_med_bundtrigger"], D2, R_DRIFT + 1, FREM_SLUT, kurve_frem)
        # isoleret dateringseffekt pr. refit under A (alle origins i panelet, kurve-grid)
        iso = []
        for r in S["A_drift"]["refits"]:
            R = mid(r["R"])
            if not r["kalibrering_aendret"]:
                continue
            ny, kf = S["A_drift"]["man"][R]["model"], S["kontrafaktisk_ingen_onset"]["man"][R]["model"]
            iso.append(dict(R=r["R"], n_pos_onset=r["positive_pr_onset_post1979"].get(fmt(onset), 0), w=ny["w"], w_kontrafaktisk=kf["w"],
                            isoleret_dP_pp_ved_live=100 * (F6.p_af(ny, {"curve": live}) - F6.p_af(kf, {"curve": live})),
                            isoleret_dP_pp_pr_kurve={f"{c:+.1f}": 100 * (F6.p_af(ny, {"curve": c}) - F6.p_af(kf, {"curve": c})) for c in KURVE_GRID},
                            ufuldstaendigt_panel=r["ufuldstaendigt_panel"]))
        ud["isoleret_dateringseffekt_pr_refit_A"] = iso
        return ud

    hoved = frem(mid(SCENARIE["peak"]), SCENARIE["annonceret"], SCENARIE["varighed_mdr"], SCENARIE["bund_annonceret"])
    th = hoved["top_hash_koersel_aendrer"]
    print(f"  top-hash-koerslen {th['R']}: kalibrering aendret {th['kalibrering_aendret']} (n_obs {th['n_obs']}, n_pos {th['n_pos']}), "
          f"positive for onset {th['positive_for_onset']}")
    for navn, rec in hoved["regler"].items():
        v = rec.get("ved_foerste_positive")
        print(f"  {navn:<26} foerste aendrede kalibrering {rec['foerste_aendrede_kalibrering']}, foerste positive label {rec['foerste_refit_med_positivt_label']}"
              + (f": n_obs {v['n_obs']} n_pos {v['n_pos']} w {v['w']}; bro dP {v['bro_dP_pp_ved_live_kurve']:+.2f}pp, isoleret {v['isoleret_dP_pp_ved_live_kurve']:+.2f}pp ved kurve {live:+.2f}" if v else "")
              + f"; indtraeden {rec['indtraeden']}")
    pa = hoved["P_afvigelse_B_minus_A_ved_live_kurve"]
    if pa["maaneder_med_afvigelse"]:
        print(f"  P(B)-P(A) ved live-kurve: {pa['maaneder_med_afvigelse']} mdr afviger ({pa['foerste']}..{pa['sidste']}), max|dP| {pa['max_abs_dP_pp']:.2f}pp")
    for r in hoved["isoleret_dateringseffekt_pr_refit_A"]:
        print(f"  isoleret dateringseffekt ved A-refit {r['R']}: {r['n_pos_onset']} positive for onset, dP {r['isoleret_dP_pp_ved_live']:+.2f}pp ved live-kurve"
              f"{' [panel ufuldstaendigt]' if r['ufuldstaendigt_panel'] else ''}")

    sweep = []
    for peak in SWEEP_PEAKS:
        ann = peak + SWEEP_LAG
        sc = frem(peak, f"{fmt(ann)}-15", SCENARIE["varighed_mdr"])
        a, b = sc["regler"]["A_drift"], sc["regler"]["B_drift_plus_indhold"]
        va = a.get("ved_foerste_positive"); vb = b.get("ved_foerste_positive")
        sweep.append(dict(peak=sc["peak"], onset=sc["onset"], annonceret=sc["annonceret"], hash_koersel=sc["hash_koersel"],
                          positive_i_panelet=sc["positive_origins_i_panelet"], ukendte=sc["ukendte_positive_origins"],
                          A_foerste_positiv=a["foerste_refit_med_positivt_label"], B_foerste_positiv=b["foerste_refit_med_positivt_label"],
                          forsinkelse_A_mdr=(mid(a["foerste_refit_med_positivt_label"]) - mid(b["foerste_refit_med_positivt_label"])) if a["foerste_refit_med_positivt_label"] and b["foerste_refit_med_positivt_label"] else None,
                          indtraeden_A=a["indtraeden"], indtraeden_B=b["indtraeden"],
                          isoleret_dP_pp_ved_live_B_foerste=vb["isoleret_dP_pp_ved_live_kurve"] if vb else None,
                          isoleret_dP_pp_ved_live_A_foerste=va["isoleret_dP_pp_ved_live_kurve"] if va else None,
                          n_pos_onset_A_foerste=next((r["positive_pr_onset_post1979"].get(sc["onset"], 0) for r in a["refits"] if r["R"] == a["foerste_refit_med_positivt_label"]), None),
                          P_afvigelse_B_minus_A=sc["P_afvigelse_B_minus_A_ved_live_kurve"]))
        s_ = sweep[-1]
        pb = s_["P_afvigelse_B_minus_A"]
        print(f"  sweep top {s_['peak']} onset {s_['onset']}: positive i panel {s_['positive_i_panelet']} ukendte {len(s_['ukendte'])}; "
              f"A {s_['A_foerste_positiv']} B {s_['B_foerste_positiv']} forsinkelse {s_['forsinkelse_A_mdr']} mdr; "
              f"isoleret dP ved B's foerste {s_['isoleret_dP_pp_ved_live_B_foerste']:+.2f}pp; "
              f"P(B)-P(A) max|dP| {pb.get('max_abs_dP_pp', 0.0):.2f}pp over {pb['maaneder_med_afvigelse']} mdr")

    grid = timing_grid()
    fors = {}
    for g in grid:
        fors.setdefault(g["onset"], {})[str(g["lag_mdr"])] = g["forsinkelse_foerste_mdr"]
    print("  timing-grid, forsinkelse (mdr) af foerste positive label under A pr. onset-maaned {lag: forsinkelse}: "
          + "; ".join(f"{k} {v}" for k, v in fors.items()))

    ud = dict(
        script="analyser/nber_indholdstrigger.py", fund="G4.1 (kode-review 2026-10-15)", aendrer_driften=False,
        created_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        snapshot=snap.name, snapshot_sha256=meta.get("snapshot_sha256"), R_drift=fmt(R_DRIFT), manifest_i_drift=W.get("manifest_hash"),
        annonceringstabel_kanonisk=A2.tabel_hash(),
        konventioner=dict(L_embargo=L, ritual_dag=RITUAL_DAG, sim_start=fmt(SIM_START), frem_slut=fmt(FREM_SLUT),
                          ufuldstaendigt_panel_fra=fmt(UFULDSTAENDIG_FRA), live_kurve=live, kurve_grid=KURVE_GRID,
                          regler={k: sorted(v) for k, v in REGLER.items()},
                          indholdstrigger="refit naar eligible_fit ved dagens R har et berettiget positivt label eller en omlabeling 0->1, som manifestet i drift ikke har",
                          P_input_historisk="GS10 - TB3MS for maaneden foer koerselsmaaneden",
                          P_input_frem=f"kurven holdt paa snapshottets live-input {live:+.2f}pp (ukendt fremtid); isoleret effekt ogsaa paa kurve-grid"),
        reproduktion_drift=repro,
        tabel=dict(raekker=[dict(event=r["event"], cycle_month=r["cycle_month"], annonceret=r["announcement_date"]) for r in rows],
                   bund_raekke_laeses_af_load_announcements=bund_laeses,
                   hash_koersler={fmt(R): v for R, v in sorted(hashR.items())},
                   top_lag_mdr={r["event"]: mid(r["announcement_date"]) - mid(r["cycle_month"]) for r in rows if r["event"].startswith("peak")},
                   bund_lag_mdr={r["event"]: mid(r["announcement_date"]) - mid(r["cycle_month"]) for r in rows if r["event"].startswith("trough")}),
        onsets=onsets,
        simulation_historisk=hist,
        fremskrivning=dict(scenarie=SCENARIE, panel_udvidelse=ekstra, hoved=hoved, sweep=dict(lag_mdr=SWEEP_LAG, varighed_mdr=SCENARIE["varighed_mdr"], scenarier=sweep),
                           timing_grid=dict(antagelser="annoncering efter d. 10 -> koerslen ser raekken maaneden efter; ingen bund-trigger; kun aritmetik",
                                            forsinkelse_pr_onset_maaned_og_lag=fors, raekker=grid)),
    )
    UD.write_text(json.dumps(ren(ud), indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"\n{UD.relative_to(V5)} skrevet.")


if __name__ == "__main__":
    main()
