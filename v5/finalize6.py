#!/usr/bin/env python3
"""
finalize6.py — trin 6 + rekalibrering (v5.0.1, RAADETS_V501.md): vaegte, baand, benchmarks,
kalibreringsmanifest, origin-audit og bro ind i weights.json.

BLUEPRINT-KRAVET (Section 8) BED i august: paa NBER-onset-labelen slog curve-only (+34,3 %)
fuldmodellen (+33,2 %), og den forhaandsforpligtede fallback gjorde curve-only operationel.
v5.0.1 (§6): gaten genkoeres og publiceres ved hver rekalibrering, men dens udfald KAN IKKE
flytte den operationelle model — slaar fuldmodellen curve-only med mere end MDE, udloeser
det en raadsbeslutning om en v5.1-protokol, aldrig et automatisk skift.

§2  Hver model estimeres paa sit eget raekkeunivers (fast start 1947Q2, egne features);
    gaten printes kun naar origin-identiteterne matcher — ellers "comparison unavailable".
§3  Vaegte, standardisering og basisrate fryses mellem rekalibreringer. Hver rekalibrering
    skriver et manifest (kalibreringer/manifest_<hash>.json) og en origin-audit mod forrige
    manifest med FORKLAREDE aendringer (modnet / censureret / omlabelet ved ny annoncering i
    (R_gl, R]); en uforklaret aendring er FEJL (kode-review 2026-10-15, F6).
§3.2 Koerslen kraever en deterministisk trigger: september-snapshot eller aendret annonceringstabel.
    Uden trigger kraeves `--reparation "<begrundelse>"`, som skrives i manifestet (F4). Rygraden
    skal vaere refit-klar (meta.spine.refit_klar, F5); annonceringstabellen skal vaere i synk med
    USREC (F7).
§3.5 Kun modne origins (vinduets slut + 18 mdr <= refit-maaned) fittes OG scores.
RAADETS_2027 (refit-maaned >= 2027-09; protokol2027.py, forseglede specs i spec2027/): §2.3 gaten er ensidet mod
    sin egen kritiske vaerdi 1,96 x SD_block og udloeser kun et obligatorisk dagsordenspunkt (den laante 4,42 er ude);
    §9 L_R-auditten (max(18, top-lag, bund-lag - 12); eligibility med info ved R; finalitet) stopper refitten ved brud.
    §6 NBER-indholdstriggeren (een refit pr. ny onset + omlabelinger) er en deterministisk trigger, naar kalibreringen
    i drift er fra 2027-refitten; trigger-maaneden skrives i manifestet. Replayen ligger i replay2027.py.
    §3.3/§4 maanedligt curve-only-fit (lambda_m = N_m/N_q) og fits ved start 1953Q2/1960Q1 -> 'uscorede' (aldrig i P).
§7  Bro ved fast inputvektor: (i) legacy-rygrad, (ii) korrigerede kilder paa samme origins,
    (iii) udvidet panel. Raa koefficienter (beta = w1/s, alpha = w0 - w1*mu/s) ved siden af.

Koer:  python finalize6.py [--snapshot ...] [--reparation "<begrundelse>"]   (rekalibrering paa spine.csv)
       python finalize6.py --legacy                  (v5.0-manifest fra shiller_yale_2023-09.csv;
                                                      roerer ikke weights.json; legacy-replay §1.5a)
Kun stdlib + numpy.
"""
import csv, hashlib, json, platform, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

import calibrate as C
import ablation2_nber as A2
import ablation3_frekvens as A3
import protokol2027 as P27

HERE = Path(__file__).parent
def kal():
    return HERE / "kalibreringer"       # evalueres ved kald: tests patcher HERE

PROTOCOL = "5.0-final"
VERSION = "5.0.1"
LEGACY_VERSION = "5.0"
YALE = "shiller_yale_2023-09.csv"
SEED = 42
NDRAW = 1000
LEGACY_W = [-2.1755, -1.6907]      # v5.0's publicerede curve-only-vaegte (legacy-replay-assertion)
LEGACY_NOBS = 264
BRO_SAETNING = "A lower or higher recalibrated probability is changed estimation, not changed economic risk."

PERMANENTE = [
    ("curve_cape", "ablation7_resultat.json", "curvecape", "promoveret", "testet, ikke bestaaet (data-foreslaaet)"),
    ("curve_awh",  "ablation8_resultat.json", "curve_awh", "OPTAGET",    "testet, ikke bestaaet (sidste skud; soegning lukket)"),
]


def permanente_linjer():
    lines = {}
    for key, fname, rkey, gate, status_nej in PERMANENTE:
        f = HERE / fname
        if not f.exists():
            print(f"ADVARSEL: {fname} mangler — benchmark-linjen '{key}' udelades af weights.json.")
            continue
        r = json.loads(f.read_text(encoding="utf-8"))
        blok = r.get(rkey)
        if not isinstance(blok, dict) or "improvement" not in blok or "brier" not in blok:
            print(f"ADVARSEL: {fname} har ingen '{rkey}'-blok med improvement/brier — linjen '{key}' udelades.")
            continue
        gates = r.get("gates", {})
        if gate not in gates:
            print(f"ADVARSEL: {fname} har ingen gate '{gate}' — status for '{key}' saettes til ukendt.")
            status = f"gate-status ukendt (se {fname})"
        else:
            status = "bestaaet (se resultatfil)" if bool(gates[gate]) else status_nej
        lines[key] = dict(wf_improvement=blok["improvement"], wf_brier=blok["brier"],
                          status=status + " [panel t.o.m. 2023Q2]", kilde=f"{fname} (snapshot {r.get('snapshot', '?')})")
    return lines


def vaerste_fejlalarm(res):
    y, q, p, _ = max((r for r in res if r[3] == 0.0), key=lambda r: r[2])
    return dict(p=round(p, 4), origin=f"{y}Q{q}")


def boot_weights(Z, y, qend_fit, eps, ndraw):
    """Episode-blok-bootstrap af vaegte. v5.0.1: resamplets basisrate gemmes pr. traek (§4.3, parret regel)."""
    rng = np.random.default_rng(SEED)
    grp = np.array([next((k for k, (o, _) in enumerate(eps) if o >= qe), len(eps)) for qe in qend_fit])
    gkeys = np.unique(grp)
    W, B = [], []
    while len(W) < ndraw:
        rows = np.concatenate([np.where(grp == g)[0] for g in rng.choice(gkeys, size=len(gkeys), replace=True)])
        yb = y[rows]
        if yb.sum() < 5 or yb.sum() > len(yb) - 5:
            continue
        W.append(np.round(C.fit(Z[rows], yb), 4).tolist())
        B.append(round(float(yb.mean()), 4))
    return W, B, len(gkeys), [int(g) for g in grp]


def sha256_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def git_commit():
    try:
        return subprocess.run(["git", "rev-parse", "--short=10", "HEAD"], cwd=HERE, capture_output=True,
                              text=True, timeout=10).stdout.strip() or "ukendt"
    except Exception:
        return "ukendt"


def fit_model(D, eps, avail, usrec, R):
    """Endeligt fit paa modne, ikke-censurerede origins (§3.5). -> dict med vaegte, standardisering,
    raa koefficienter, origin-liste og fit-maske."""
    elig, yR = A2.eligible_fit(D, eps, avail, usrec, R)
    X, y = D["F"][elig], yR[elig]
    mu, sd = X.mean(0), X.std(0, ddof=1); sd[sd == 0] = 1
    Z = (X - mu) / sd
    w = C.fit(Z, y)
    feats = D["feats"]
    raa = {}
    if len(feats) == 1:
        beta = float(w[1] / sd[0]); alpha = float(w[0] - w[1] * mu[0] / sd[0])
        raa = dict(beta_curve_pr_pp=round(beta, 4), alpha=round(alpha, 4),
                   note="P = logit^-1(alpha + beta * kurve_i_pp); samme model som de standardiserede vaegte")
    origins = A2.origins_liste(D, elig, yR)
    return dict(features=feats, n_obs=int(elig.sum()), n_pos=int(y.sum()),
                estimering_slut=f"{origins[-1][0]}Q{origins[-1][1]}", univers_slut=f"{D['qk'][-1][0]}Q{D['qk'][-1][1]}",
                mu={f: round(float(m), 4) for f, m in zip(feats, mu)},
                sd={f: round(float(s), 4) for f, s in zip(feats, sd)},
                w=[round(float(v), 4) for v in w], raa=raa, base_rate=round(float(y.mean()), 4),
                _elig=elig, _y=y, _Z=Z, _origins=origins)


def p_af(model, x):
    """P for een inputvektor {feature: vaerdi} under et model-dict (mu/sd/w)."""
    z = np.array([(x[f] - model["mu"][f]) / model["sd"][f] for f in model["features"]])
    return float(1 / (1 + np.exp(-np.clip(model["w"][0] + np.dot(model["w"][1:], z), -30, 30))))


def live_x(snap):
    """Broens faste inputvektor = motorens live-input (trailing maaned af daglige DGS10 - DTB3)."""
    return {"curve": float(C.live_kurve(snap)["curve"])}


HASH_UDELUKKET = ("created_utc", "code_commit", "kaldt_som", "hash",
                  "delta_vs_forrige", "trigger", "miljoe", "reparation", "nber_effekt",
                  "L_R_audit", "announcement_table_kanonisk", "indholdstrigger",
                  "uscorede")   # proveniens om aendringen/koerslen (og RAADETS_2027's uscorede fit), ikke
# kalibreringsindhold (den kanoniske tabelhash er afledt af samme fil som announcement_table_sha256)

def manifest_hash(m):
    """Hash af kalibreringens INDHOLD (snapshot, rygrad, annonceringstabel, R, origins, vaegte, gate, audit):
    identiske input giver identisk hash uanset commit-id og tidspunkt."""
    body = {k: v for k, v in m.items() if k not in HASH_UDELUKKET}
    return hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()[:8]


def forrige_manifest():
    """Den kalibrering der er I DRIFT = weights.json's manifest_hash — ikke blot sidste post i
    index.json: en legacy-replay eller en afbrudt koersel maa aldrig kunne goere sig selv til
    'forrige'. Uden manifest_hash i weights.json (foer v5.0.1) bruges sidste index-post."""
    h = None
    wf = HERE / "weights.json"
    if wf.exists():
        try:
            h = json.loads(wf.read_text(encoding="utf-8")).get("manifest_hash")
        except ValueError:
            h = None
    if h is None:
        idx = kal() / "index.json"
        entries = json.loads(idx.read_text(encoding="utf-8")) if idx.exists() else []
        h = entries[-1]["hash"] if entries else None
    if h is None:
        return None
    f = kal() / f"manifest_{h}.json"
    if not f.exists():
        # F6: weights.json peger paa et manifest der ikke findes -> auditten ville stille blive tom
        sys.exit(f"FEJL: weights.json har manifest_hash {h}, men kalibreringer/manifest_{h}.json mangler — "
                 "gendan filen (git checkout) foer rekalibrering.")
    return json.loads(f.read_text(encoding="utf-8"))


def ann_fil():
    """Annonceringstabellen ved siden af koden (HERE; tests patcher HERE — falder da tilbage til A2's)."""
    f = HERE / "nber_announcements.csv"
    return f if f.exists() else A2.HERE / "nber_announcements.csv"


def indholdstrigger_ved(snap, forrige):
    """RAADETS_2027 §6 (spec2027/3_indholdstrigger_replay.md §2): den foerste maaned i (forrige refit, snapshottets
    maaned], hvor NBER-indholdstriggeren er udloest mod manifestet i drift -> manifestets felt, eller None."""
    usrec = A2.load_usrec(snap)
    eps = A2.episodes_from_usrec(usrec)
    avail = A2.load_announcements(eps, f=ann_fil(), usrec=usrec)
    D = A2.build_dataset(snap, ["curve"])
    R = A2.midx(int(snap.name[:4]), int(snap.name[5:7]))
    R_M = A2.midx(int(forrige["refit_maaned"][:4]), int(forrige["refit_maaned"][5:7]))
    return P27.foerste_trigger(D, eps, avail, usrec, R, forrige["origins"], R_M)


def miljoe():
    """F54: miljoeet der kalibrerede (proveniens, uden for hashen)."""
    return dict(python=platform.python_version(), numpy=np.__version__, platform=platform.platform(terse=True))


def L_R_audit():
    """F51 (blueprint §1): L_R = max(18, stoerste observerede top-annonceringslag). Stiger den over 18,
    skal embargogulvet og protokolversionen op — det printes hoejlydt, aendres ikke automatisk."""
    lags = []
    for r in A2.laes_annonceringer(ann_fil()):
        if r["event"].startswith("peak"):
            cy, cm = map(int, r["cycle_month"].split("-"))
            ay, am = int(r["announcement_date"][:4]), int(r["announcement_date"][5:7])
            lags.append((A2.midx(ay, am) - A2.midx(cy, cm), r["event"]))
    mx = max(lags) if lags else (0, "-")
    L_R = max(A2.L_EMBARGO, mx[0])
    return dict(L_embargo=A2.L_EMBARGO, stoerste_top_lag=mx[0], fra=mx[1], L_R=L_R, ok=L_R == A2.L_EMBARGO)


def rygrad_klar(snap, meta):
    """F5: et snapshot hvis rygrad er skaaret af (multpl/SP500-udfald) eller stale maa aldrig
    rekalibreres — det ville stille rulle v5.0.1-reparationen tilbage. Aeldre snapshots uden
    meta.spine.refit_klar vurderes efter de samme regler."""
    sp = meta.get("spine", {})
    if "refit_klar" in sp:
        return sp["refit_klar"], sp.get("refit_blokeret", [])
    grunde = []
    if "fejl" in sp.get("multpl", {"fejl": "multpl-blok mangler"}):
        grunde.append("multpl fejlede/mangler")
    if "SP500" in meta.get("reserve_fejlede", []):
        grunde.append("SP500 fejlede")
    if "spine" in meta.get("stale", {}):
        grunde.append("rygraden er stale")
    if not (snap / "spine.csv").exists():
        grunde.append("spine.csv mangler")
    return not grunde, grunde


def skriv_manifest(m):
    """Nyt manifest + post SIDST i index.json (kronologisk kaede). Findes kalibreringen allerede
    (samme indholds-hash), roeres hverken fil eller index: den oprindelige proveniens (created_utc,
    code_commit) og kaedens raekkefoelge bevares. Returnerer (hash, nyt_skrevet)."""
    kal().mkdir(exist_ok=True)
    h = manifest_hash(m)
    m["hash"] = h
    f = kal() / f"manifest_{h}.json"
    idx = kal() / "index.json"
    entries = json.loads(idx.read_text(encoding="utf-8")) if idx.exists() else []
    if f.exists() and any(e["hash"] == h for e in entries):
        return h, False
    f.write_text(json.dumps(m, indent=1, ensure_ascii=False), encoding="utf-8")
    entries = [e for e in entries if e["hash"] != h]
    entries.append(dict(hash=h, version=m["version"], snapshot=m["snapshot"], refit_maaned=m["refit_maaned"],
                        created_utc=m["created_utc"], n_obs=m["modeller"]["curve_only"]["n_obs"]))
    idx.write_text(json.dumps(entries, indent=1), encoding="utf-8")
    return h, True


def rekalibrer(snap, spine_file=None, R=None, version=VERSION, kaldt_som="rekalibrering"):
    """Hele beregningen for een rygrad. Returnerer (manifest-dict uden hash, ekstra-dict til weights)."""
    meta = json.loads((snap / "meta.json").read_text(encoding="utf-8"))
    usrec = A2.load_usrec(snap)
    eps = A2.episodes_from_usrec(usrec)
    avail = A2.load_announcements(eps, f=ann_fil(), usrec=usrec)      # F7: haard fejl hvis tabellen er ude af synk med USREC
    R = R if R is not None else A2.midx(int(snap.name[:4]), int(snap.name[5:7]))
    Dc = A2.build_dataset(snap, ["curve"], spine_file=spine_file)
    D5 = A2.build_dataset(snap, C.F5, spine_file=spine_file)

    # walk-forward: kun modne origins scores (§3.5) — R_score = refit-maaneden
    resc, _, _ = A2.wf_nber(Dc, eps, avail, usrec, A2L, R_score=R)
    _, _, impc, brc = C.metrics(resc)
    fac = vaerste_fejlalarm(resc)
    identiske = A2.samme_origins(Dc, D5)
    gate = dict(identiske_origins=identiske, curve_only_wf=round(impc, 2), curve_only_brier=round(brc, 2))
    if P27.i_kraft(R):
        # RAADETS_2027 §2.3 (spec2027/1_gate.md): ensidet gate mod egen kritisk vaerdi -> dagsordenspunkt; 4,42 er ude
        gate, res5 = P27.gate(Dc, D5, eps, avail, usrec, R, resc)
        if res5:
            _, _, imp5, br5 = C.metrics(res5)
            fa5 = vaerste_fejlalarm(res5)
        else:
            imp5, br5, fa5 = None, None, None
    elif identiske:
        res5, _, _ = A2.wf_nber(D5, eps, avail, usrec, A2L, R_score=R)
        _, _, imp5, br5 = C.metrics(res5)
        fa5 = vaerste_fejlalarm(res5)
        f3 = HERE / "ablation3_resultat.json"
        mde = json.loads(f3.read_text(encoding="utf-8")).get("mde_pp") if f3.exists() else None
        gap = imp5 - impc
        # F8: gatens EGEN MDE (1,96 x episode-blok-bootstrap-SD af den parrede skill-forskel F5 - curve-only).
        # Beslutningsreglen bruger fortsat den ratificerede trin 3-MDE (en taerskel aendres ikke efter at
        # resultatet er set); den gate-specifikke printes ved siden af, til raadet foer sept. 2027.
        paired = [(y, q, p5, pc, yy) for (y, q, p5, yy), (_, _, pc, _) in zip(res5, resc)]
        _md, sd_g, _lo, _hi = A3.mde_bootstrap(paired, eps)
        mde_gate = round(1.96 * sd_g, 2) if sd_g is not None else None
        gate.update(fuldmodel_wf=round(imp5, 2), fuldmodel_brier=round(br5, 2), forskel_pp=round(gap, 2), mde_pp=mde,
                    mde_gate_pp=mde_gate,
                    fuldmodel_slaar=bool(imp5 > impc),
                    raadsbeslutning_paakraevet=bool(mde is not None and gap > mde),
                    note=(f"LL-forskel {abs(gap):.1f}pp {'<' if mde is not None and abs(gap) < mde else '>='} "
                          f"stoejgulv {mde if mde is not None else '?'}pp (trin 3-MDE, laant fra frekvenstesten; "
                          f"gatens egen MDE {mde_gate}pp). Gaten er mekanisk og kan ikke "
                          "flytte den operationelle model (RAADETS_V501 §6)."))
    else:
        res5, imp5, br5, fa5 = [], None, None, None
        gate.update(note="comparison unavailable — fuldmodellens og curve-onlys origin-identiteter matcher ikke "
                         "(CAPE stale/manglende?). Curve-only koerer videre (§2).")

    mc = fit_model(Dc, eps, avail, usrec, R)
    m5 = fit_model(D5, eps, avail, usrec, R) if identiske else None
    W, B, ngrp, grp = boot_weights(mc["_Z"], mc["_y"], Dc["qend"][mc["_elig"]], eps, NDRAW)

    spine_navn = spine_file or next((n for n in C.SPINE_FILER if (snap / n).exists()), "?")
    ann = ann_fil()
    # G4.1: dateringens faktiske effekt — n_episoder taeller kun onsets med mindst eet BERETTIGET positivt origin
    _yf, win_on, _ = A2.nber_labels(Dc, eps, usrec)
    onsets_i_fit = set()
    for k, j in enumerate(np.where(mc["_elig"])[0]):
        if mc["_y"][k] == 1:
            onsets_i_fit |= {o for o in win_on[j] if avail.get(o, 10 ** 9) <= R}
    onsets_i_fit = sorted(onsets_i_fit)
    manifest = dict(
        version=version, protocol_version=PROTOCOL,
        created_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        code_commit=git_commit(), kaldt_som=kaldt_som,
        snapshot=snap.name, snapshot_sha256=meta["snapshot_sha256"],
        announcement_table_sha256=C.ann_sha256(ann) if ann.exists() else None,
        announcement_table_kanonisk=A2.tabel_hash(ann) if ann.exists() else None,   # F15: bestem_trigger/koersel kanonisk
        refit_maaned=f"{R // 12}-{R % 12 + 1:02d}",
        spine=dict(fil=spine_navn, sha256=sha256_file(snap / spine_navn) if (snap / spine_navn).exists() else None,
                   sidste=meta.get("spine", {}).get("sidste") if not spine_file else None),
        operationel="curve_only",
        modeller={"curve_only": {k: v for k, v in mc.items() if not k.startswith("_")}
                  | dict(wf_improvement=round(impc, 2), wf_brier=round(brc, 2), vaerste_fejlalarm=fac)},
        gate=gate,
        origins=mc["_origins"],
        bootstrap=dict(seed=SEED, n_draws=len(W), n_blokke=ngrp,
                       band_sha256=hashlib.sha256(json.dumps([W, B]).encode("utf-8")).hexdigest()[:16]),
        miljoe=miljoe(),
        nber_effekt=dict(onsets_med_berettiget_positivt_origin=[f"{o // 12}-{o % 12 + 1:02d}" for o in onsets_i_fit],
                         n_pos=mc["n_pos"]),
    )
    if m5 is not None:
        manifest["modeller"]["fuldmodel"] = ({k: v for k, v in m5.items() if not k.startswith("_")}
                                            | dict(wf_improvement=round(imp5, 2), wf_brier=round(br5, 2),
                                                   vaerste_fejlalarm=fa5))
    ekstra = dict(W=W, B=B, grp=grp, resc=resc, res5=res5, mc=mc, m5=m5, Dc=Dc, D5=D5, eps=eps, avail=avail, usrec=usrec,
                  R=R, onsets_i_fit=onsets_i_fit)
    return manifest, ekstra


A2L = A2.L_EMBARGO


def bro(snap, ekstra_ny, x):
    """§7.2: trinvis bro ved fast inputvektor x. (i) legacy-rygrad (R = 2025-12: praecis det gamle univers),
    (ii) korrigerede kilder paa de samme origins (spine.csv, R = 2025-12), (iii) udvidet panel (R = nu)."""
    R_gl = A2.midx(2023, 6) + 12 + A2L                # vinduets slut 2023Q2 + gulv -> det gamle origin-saet
    trin = {}
    if (snap / YALE).exists():
        m_i, _ = rekalibrer(snap, spine_file=YALE, R=R_gl, version=LEGACY_VERSION, kaldt_som="bro-i")
        trin["i_legacy_rygrad"] = dict(P=round(p_af(m_i["modeller"]["curve_only"], x), 4),
                                       **{k: m_i["modeller"]["curve_only"][k] for k in ("w", "mu", "sd", "raa", "n_obs", "base_rate")})
    m_ii, _ = rekalibrer(snap, R=R_gl, version=VERSION, kaldt_som="bro-ii")
    trin["ii_korrigerede_kilder_samme_origins"] = dict(P=round(p_af(m_ii["modeller"]["curve_only"], x), 4),
                                                       **{k: m_ii["modeller"]["curve_only"][k] for k in ("w", "mu", "sd", "raa", "n_obs", "base_rate")})
    mc = ekstra_ny["mc"]
    trin["iii_udvidet_panel"] = dict(P=round(p_af(mc, x), 4), **{k: mc[k] for k in ("w", "mu", "sd", "raa", "n_obs", "base_rate")})
    return dict(input_vektor={k: round(v, 4) for k, v in x.items()}, snapshot=snap.name, trin=trin,
                note="attributionen er raekkefoelge-afhaengig (Astra R3)", saetning=BRO_SAETNING)


def delta_vs_forrige(Dc, ny, gl):
    """Kimi R5 #2: ikke kun eet inputpunkt — max|dP| og max|dw| over ALLE origins i raekkeuniverset
    mellem to kalibreringer. Goer Geminis bekymring (kompression efter en ny bund) til et tal."""
    xs = [{"curve": float(v)} for v in Dc["F"][:, 0]]
    dP = np.array([p_af(ny, x) - p_af(gl, x) for x in xs])
    k = int(np.argmax(np.abs(dP)))
    dw = [round(a - b, 4) for a, b in zip(ny["w"], gl["w"])]
    return dict(n_origins=len(xs), max_abs_dP=round(float(np.abs(dP).max()), 4),
                origin_max=f"{Dc['qk'][k][0]}Q{Dc['qk'][k][1]}", dP_der=round(float(dP[k]), 4),
                mean_abs_dP=round(float(np.abs(dP).mean()), 4),
                andel_over_5pp=round(float(np.mean(np.abs(dP) > 0.05)), 3),
                dw_std=dw, max_abs_dw=round(max(abs(v) for v in dw), 4),
                d_beta_pr_pp=round(ny["raa"]["beta_curve_pr_pp"] - gl["raa"]["beta_curve_pr_pp"], 4) if ny.get("raa") and gl.get("raa") else None,
                d_alpha=round(ny["raa"]["alpha"] - gl["raa"]["alpha"], 4) if ny.get("raa") and gl.get("raa") else None)


def kraev_ny_version(forrige):
    """§3.3: hver ny kalibrering er en ny v5.0.x. Stopper FOER noget skrives: et manifest med samme version
    som kalibreringen i drift ville ellers blive genbrugt uaendret ved naeste koersel (indholdet er det samme),
    saa fejlen ikke kunne rettes ved blot at bumpe VERSION bagefter. Fanger ogsaa en finalize6-koersel uden
    for en rekalibrering, som ellers ville loesne de frosne vaegte."""
    if forrige and forrige.get("version") == VERSION:
        sys.exit(f"FEJL (§3.3): dataene giver en ny kalibrering, men VERSION er stadig v{VERSION} som kalibreringen i "
                 f"drift ({forrige.get('hash')}). Er det en rekalibrering (§3.2): bump VERSION i finalize6.py og koer "
                 "igen. Ellers: stop — vaegtene er frosne mellem rekalibreringer; driftsvaegtene gendannes med "
                 "'git checkout v5/weights.json'. "
                 "Intet er skrevet.")


def bestem_trigger(m_ny, m_gl, ref=None):
    """Hvorfor koerte rekalibreringen (§3.2)? Bestemmes af det NYE manifest mod det forrige DISTINKTE
    manifest: NBER-datering (annonceringstabel aendret), september (aarlig), ellers manuel/reparation.
    Foerste manifest efter legacy (v5.0) er per definition reparationen."""
    if m_gl is None or m_gl.get("version") in (None, LEGACY_VERSION):
        return "manuel/reparation (foerste kalibrering efter v5.0)"
    ref = ref or m_gl              # tabeltilstanden en genbrugende NBER-koersel allerede har registreret (weights.json)
    k_gl, k_ny = A2.kanonisk_af(ref), A2.kanonisk_af(m_ny) or A2.tabel_hash(ann_fil())
    it = m_ny.get("indholdstrigger")                  # RAADETS_2027 §6 (spec 3 §2): efter hash-triggeren, foer september
    if (k_gl != k_ny) if k_gl else (ref.get("announcement_table_sha256") != m_ny["announcement_table_sha256"]):
        return "nber-datering (annonceringstabellen aendret)" + (f" + {P27.trigger_tekst(it)}" if it else "")
    if it:
        return P27.trigger_tekst(it)
    if int(m_ny["refit_maaned"][5:7]) == 9:
        return "september (aarlig)"
    return "manuel/reparation"


def kalibrerings_indhold(mod, origins):
    """Det der ER en kalibrering: origin-saet med labels, vaegte, standardisering, basisrate.
    Snapshot-navn/-hash er proveniens: samme kalibrering verificeret paa et nyere snapshot er
    stadig samme kalibrering."""
    return (origins, mod["w"], mod["mu"], mod["sd"], mod["base_rate"])


def legacy_manifest():
    """Det eksisterende v5.0-manifest (via legacy_mapping.json, ellers index-post med version 5.0)."""
    lm = kal() / "legacy_mapping.json"
    h = None
    if lm.exists():
        try:
            h = json.loads(lm.read_text(encoding="utf-8")).get("manifest_hash")
        except ValueError:
            h = None
    if h is None and (kal() / "index.json").exists():
        h = next((e["hash"] for e in json.loads((kal() / "index.json").read_text(encoding="utf-8"))
                  if e.get("version") == LEGACY_VERSION), None)
    f = kal() / f"manifest_{h}.json" if h else None
    return json.loads(f.read_text(encoding="utf-8")) if f and f.exists() else None


def fuldmodel_status(g):
    """G1.7 (V501 §6): statusteksten foelger gatens beslutning, ikke en vilkaarlig lille foering."""
    if P27.er_2027_gate(g):
        return P27.fuldmodel_status(g)
    if g.get("raadsbeslutning_paakraevet"):
        return "slaar curve-only med mere end MDE — RAADSBESLUTNING PAAKRAEVET (v5.1), ikke operationel (§6)"
    if g.get("fuldmodel_slaar"):
        return "slaar curve-only under MDE — ingen raadsbeslutning (§6)"
    return "testet, ikke bestaaet mod benchmark (trin 6; genkoert v5.0.1)"


def raadsbeslutning():
    """§6: den operationelle model skiftes KUN ved en raadsbeslutning, nedskrevet i
    kalibreringer/raadsbeslutning.json ({"operationel": ..., "reference": ..., "dato": ...}).
    Findes filen ikke, er den operationelle model curve_only. En tidligere weights.json-vaerdi
    (fx en one-shot-promotion) taeller ikke: den var gate-udfald, ikke raadsbeslutning."""
    f = kal() / "raadsbeslutning.json"
    if not f.exists():
        return "curve_only", None
    d = json.loads(f.read_text(encoding="utf-8"))
    return d.get("operationel", "curve_only"), d


def main():
    legacy = "--legacy" in sys.argv
    snap = C.find_snapshot(sys.argv)
    print(f"=== finalize6 — {PROTOCOL} / v{LEGACY_VERSION if legacy else VERSION} — snapshot {snap.name}"
          f"{' — LEGACY-REPLAY (' + YALE + ')' if legacy else ''} ===")

    if legacy:
        R_gl = A2.midx(2023, 6) + 12 + A2L
        m, ekstra = rekalibrer(snap, spine_file=YALE, R=R_gl, version=LEGACY_VERSION, kaldt_som="legacy-replay")
        mc = m["modeller"]["curve_only"]
        ok = mc["w"] == LEGACY_W and mc["n_obs"] == LEGACY_NOBS
        print(f"legacy-replay (§1.5a): w={mc['w']} n_obs={mc['n_obs']} wf=+{mc['wf_improvement']}% -> "
              f"{'EKSAKT' if ok else 'AFVIGER'} fra v5.0 ({LEGACY_W}, {LEGACY_NOBS})")
        if not ok:
            sys.exit("FEJL: legacy-replay reproducerer ikke v5.0 — stitchen er brudt (§1.5a).")
        eks = legacy_manifest()
        if eks is not None:
            # Ren verifikation: samme kalibrering som det arkiverede v5.0-manifest -> intet skrives.
            if kalibrerings_indhold(eks["modeller"]["curve_only"], eks["origins"]) != kalibrerings_indhold(mc, m["origins"]):
                sys.exit(f"FEJL: legacy-replay paa {snap.name} giver en ANDEN kalibrering end det arkiverede "
                         f"v5.0-manifest {eks['hash']} (snapshot {eks['snapshot']}) — historikken er aendret under os.")
            print(f"legacy-replay verificeret mod arkiveret v5.0-manifest {eks['hash']} (oprindeligt snapshot "
                  f"{eks['snapshot']}, verificeret paa {snap.name}) — samme origins, labels og vaegte; intet skrevet.")
            return
        m["audit"] = dict(note="legacy: ingen forrige manifest")
        h, nyt = skriv_manifest(m)
        mapping = dict(note="RAADETS_V501 §3.3: historiske hovedbogsraekker roeres aldrig; denne fil kobler dem til v5.0-manifestet.",
                       manifest_hash=h, version=LEGACY_VERSION, hovedbogsraekker=["2026-08-12", "2026-09-09"])
        (kal() / "legacy_mapping.json").write_text(json.dumps(mapping, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"v5.0-manifest {'skrevet' if nyt else 'findes allerede og er uroert'}: kalibreringer/manifest_{h}.json"
              " + legacy_mapping.json (weights.json og index-raekkefoelgen uroert)")
        return

    meta = json.loads((snap / "meta.json").read_text(encoding="utf-8"))
    klar, grunde = rygrad_klar(snap, meta)
    if not klar:
        # F5 + PR #1: curve-only er uafhaengig af rygraden (A2.build_dataset forlaenger maanedsindekset), saa en
        # trunkeret rygrad ruller ikke reparationen tilbage; den koster kun fuldmodellens gate ("comparison
        # unavailable", V501 §2). En vagt der STOPPEDE her, ville blokere hovedbogen i hver refit-maaned.
        print(f"ADVARSEL (F5): rygraden i {snap.name} er ikke komplet ({'; '.join(grunde)}) — curve-only kalibreres "
              "uafhaengigt af den; fuldmodellens gate kan blive 'comparison unavailable'. Koer helst fetch.py igen.")
    forrige = forrige_manifest()
    reparation = None
    if "--reparation" in sys.argv:
        k = sys.argv.index("--reparation")
        reparation = sys.argv[k + 1] if len(sys.argv) > k + 1 and not sys.argv[k + 1].startswith("-") else ""
        if not reparation.strip():
            sys.exit('FEJL: --reparation kraever en begrundelse: --reparation "<hvad og hvorfor>"')
    ref = None
    indhold_gaelder, indhold = False, None
    if forrige and forrige.get("version") not in (None, LEGACY_VERSION):
        sep = int(snap.name[5:7]) == 9
        W_ = {}
        if (HERE / "weights.json").exists():
            try:
                W_ = json.loads((HERE / "weights.json").read_text(encoding="utf-8"))
            except ValueError:
                W_ = {}
        ref = W_ if W_.get("manifest_hash") == forrige.get("hash") and W_.get("announcement_table_sha256") else forrige
        ny_tabel = A2.tabel_aendret(ref.get("announcement_table_sha256"), A2.kanonisk_af(ref), f=ann_fil())
        # RAADETS_2027 §6: indholdstriggeren gaelder, naar kalibreringen i drift er fra 2027-refitten eller senere
        indhold_gaelder = P27.i_kraft_maaned(forrige.get("refit_maaned"))
        indhold = indholdstrigger_ved(snap, forrige) if indhold_gaelder else None
        # en ren reproduktion paa kalibreringens EGET snapshot er tilladt (gendanner driftsvaegtene bit-identisk;
        # kraev_ny_version stopper den, hvis den mod forventning giver en anden kalibrering)
        if not sep and not ny_tabel and not indhold and reparation is None and snap.name != forrige.get("snapshot"):
            sys.exit(f"FEJL (§3.2, F4): ingen deterministisk trigger — snapshot {snap.name} er ikke et september-snapshot, "
                     "og annonceringstabellen er uaendret siden manifest "
                     f"{forrige.get('hash')}"
                     + (" (og NBER-indholdstriggeren, RAADETS_2027 §6, er ikke udloest)" if indhold_gaelder else "")
                     + ". Vaegtene er frosne. En reparation kraever "
                     '--reparation "<begrundelse>" (skrives i manifestet).')
    lr = None
    if not P27.i_kraft(A2.midx(int(snap.name[:4]), int(snap.name[5:7]))):
        lr = L_R_audit()
        print(f"L_R-audit (blueprint §1): stoerste top-annonceringslag {lr['stoerste_top_lag']} mdr ({lr['fra']}) -> "
              f"L_R = {lr['L_R']} {'= gulvet 18 (OK)' if lr['ok'] else '> 18: EMBARGOGULV OG PROTOKOLVERSION SKAL OP (raadet)'}")
    m, ekstra = rekalibrer(snap)
    if P27.i_kraft(ekstra["R"]):
        # RAADETS_2027 §9 (spec2027/2_L_R_audit.md): begge uligheder + eligibility med info ved R; stop ved brud
        lr = P27.L_R_audit(ekstra["Dc"], ekstra["eps"], ekstra["avail"], ekstra["usrec"], ekstra["R"],
                           rows=A2.laes_annonceringer(ann_fil()))
        for ln in P27.L_R_linjer(lr):
            print(ln)
        P27.stop_ved_brud(lr)
    m["L_R_audit"] = lr
    if P27.i_kraft(ekstra["R"]):
        # RAADETS_2027 §3.3/§4 (spec2027/4_maanedligt_fit_uscorede.md): maanedligt fit (lambda_m = N_m/N_q) og fits ved
        # universstart 1953Q2/1960Q1 — uscorede, uden for indholds-hashen, aldrig i P/baand/dom
        m["uscorede"] = P27.uscorede(snap, ekstra["Dc"], ekstra["eps"], ekstra["avail"], ekstra["usrec"], ekstra["R"])
        mf_ = m["uscorede"]["maanedligt_fit"]
        print(f"uscoret (RAADETS_2027 §3.3): maanedligt fit N_m {mf_['N_m']} / N_q {mf_['N_q']} -> lambda_m {mf_['l2']:.3f}, "
              f"w {mf_['w']}; starter 1953Q2 n {m['uscorede']['start_1953Q2']['n_obs']}, 1960Q1 n {m['uscorede']['start_1960Q1']['n_obs']}")
    if indhold_gaelder:
        m["indholdstrigger"] = indhold               # spec 3 §2: trigger-maaneden i manifestet (null: ikke udloest)
        if indhold:
            print(f"NBER-indholdstrigger (RAADETS_2027 §6): trigger-maaned {indhold['trigger_maaned']}; nye onsets "
                  f"{indhold['nye_onsets'] or '-'}; omlabelinger {indhold['omlabelinger'] or '-'}")
    if reparation is not None:
        m["reparation"] = reparation
    g = m["gate"]
    print(f"curve-only: +{g['curve_only_wf']:.1f}%/+{g['curve_only_brier']:.1f}%  "
          + (f"fuldmodel: +{g['fuldmodel_wf']:.1f}%/+{g['fuldmodel_brier']:.1f}%  (identiske origins)" if g["identiske_origins"]
             else "fuldmodel: comparison unavailable"))
    if P27.er_2027_gate(g):
        for ln in P27.gate_linjer(g):
            print(ln)
        print("Operationel model: curve_only (laast, RAADETS_V501 §6; ingen selektor, RAADETS_2027 §2.1).")
    elif g.get("raadsbeslutning_paakraevet"):
        print("!!! Fuldmodellen slaar curve-only med mere end MDE: RAADSBESLUTNING PAAKRAEVET (v5.1) — intet skiftes automatisk (§6).")
    else:
        print("Operationel model: curve_only (laast, §6). " + g.get("note", ""))
    operationel, beslutning = raadsbeslutning()
    prev_op = None
    if (HERE / "weights.json").exists():
        try:
            prev_op = json.loads((HERE / "weights.json").read_text(encoding="utf-8")).get("operationel")
        except ValueError:
            prev_op = None
    if prev_op not in (None, "curve_only", operationel):
        print(f"ADVARSEL (§6): forrige weights.json havde operationel='{prev_op}' — ignoreres. Et skift af den "
              "operationelle model kraever kalibreringer/raadsbeslutning.json, ikke et gate-udfald.")
    if operationel != "curve_only":
        print(f"RAADSBESLUTNING: operationel model = {operationel} ({beslutning.get('reference', '?')}, {beslutning.get('dato', '?')}). "
              "v5.0.1-koden estimerer kun curve_only; koer det ratificerede protokol-script for den valgte model.")
        sys.exit("FEJL: en anden operationel model end curve_only kraever sin egen rekalibreringskode (v5.1).")
    m["raadsbeslutning"] = beslutning

    # ---- origin-audit mod forrige manifest (§3.5): kun FORKLAREDE aendringer (F6) ----
    R_gl = None
    if forrige and forrige.get("refit_maaned"):
        R_gl = A2.midx(int(forrige["refit_maaned"][:4]), int(forrige["refit_maaned"][5:7]))
    audit = A2.origin_audit(forrige["origins"] if forrige else None, m["origins"], R_gl=R_gl, R=ekstra["R"],
                            eps=ekstra["eps"], avail=ekstra["avail"])
    audit["forrige_hash"] = forrige["hash"] if forrige else None
    audit["forrige_version"] = forrige["version"] if forrige else None
    m["audit"] = audit
    print(f"origin-audit: n {audit['n_forrige']} -> {audit['n_ny']} | tilfoejede {audit['tilfoejede']} | "
          f"fjernede {audit['fjernede']} | omlabelede {audit['omlabelede']} | "
          f"{'FORKLARET' if audit['forklaret_ok'] and not audit['kun_listet'] else 'kun listet (legacy)' if audit['kun_listet'] else 'UFORKLARET'}")
    for u in audit["uforklarede"]:
        print(f"   uforklaret: {u}")
    if not audit["forklaret_ok"]:
        sys.exit("FEJL: origin-audit — uforklaret aendring i det berettigede origin-saet (§3.5, F6).")
    if forrige and not audit["tilfoejede"] and not audit["fjernede"] and not audit["omlabelede"]:
        print("Bemaerk: ingen aendring i origin-saettet — kalibreringen er uaendret (en top-annoncering modner/censurerer "
              "foerst origins ved en senere refit under 18-mdr-gulvet; G4.1).")

    mc = ekstra["mc"]
    x = live_x(snap)
    b = bro(snap, ekstra, x)
    for navn, t in b["trin"].items():
        print(f"bro {navn:<40} P={t['P']*100:5.1f}%  w={t['w']}  n={t['n_obs']}  beta={t['raa'].get('beta_curve_pr_pp')}")
    print(f'bro: "{BRO_SAETNING}"')

    # Idempotens: samme origins, labels og vaegte som forrige manifest = SAMME kalibrering.
    # Saa genbruges forrige hash (intet nyt manifest); kaeden holder, og en genkoersel uden
    # dataaendring (fx den aarlige september-koersel i et roligt aar) skaber ikke stoej.
    _indhold = kalibrerings_indhold
    m["trigger"] = bestem_trigger(m, forrige, ref)
    if reparation is not None:
        m["trigger"] = (f"manuel/reparation: {reparation}" if m["trigger"].startswith("manuel/reparation")
                        and not m["trigger"].startswith("manuel/reparation (foerste")
                        else f"{m['trigger']} (+ reparation: {reparation})")
    delta = None
    genbrugt = False
    koersel_trigger = m["trigger"]
    koersel_utc = m["created_utc"]
    if forrige and _indhold(forrige["modeller"]["curve_only"], forrige["origins"]) == _indhold(m["modeller"]["curve_only"], m["origins"]):
        genbrugt = True
        h = forrige["hash"]
        audit = dict(forrige["audit"])                      # F49: manifestets audit, ikke en blanding
        m["audit"] = audit
        m["refit_maaned"] = forrige["refit_maaned"]         # G4.2: manifestets refit-maaned, ikke denne koersels
        m["version"] = forrige["version"]
        koersel_gate = m["gate"]
        m["gate"] = dict(forrige["gate"])                   # #12: manifestets gate og fuldmodel, ikke denne koersels
        if "uscorede" in forrige:
            m["uscorede"] = forrige["uscorede"]             # spec 4 §2: et genbrugt manifest genbruger ogsaa sine uscorede fit
        if "fuldmodel" in forrige["modeller"]:
            m["modeller"]["fuldmodel"] = forrige["modeller"]["fuldmodel"]
        else:
            m["modeller"].pop("fuldmodel", None)
        g = m["gate"]
        if (koersel_gate.get("identiske_origins") != g.get("identiske_origins")
                or koersel_gate.get("fuldmodel_wf") != g.get("fuldmodel_wf")):
            print(f"ADVARSEL: denne koersels fuldmodel/gate afviger fra manifest {forrige['hash']} (fx ufuldstaendig rygrad) — "
                  "weights.json beholder manifestets fuldmodel og gate.")
        delta = forrige.get("delta_vs_forrige")
        print(f"kalibrering UAENDRET (samme origins, labels og vaegte): manifest {h} genbruges, intet nyt skrives.")
        # hash-udelukkede proveniensfelter skrives igennem hvis de mangler i det eksisterende manifest
        mf = kal() / f"manifest_{h}.json"
        if mf.exists() and (delta is None or "trigger" not in forrige):
            gl_h = audit["forrige_hash"]
            gl_f = kal() / f"manifest_{gl_h}.json" if gl_h else None
            if delta is None and gl_f and gl_f.exists():
                delta = delta_vs_forrige(ekstra["Dc"], m["modeller"]["curve_only"],
                                         json.loads(gl_f.read_text(encoding="utf-8"))["modeller"]["curve_only"])
            forrige["delta_vs_forrige"] = delta
            gl_m = json.loads(gl_f.read_text(encoding="utf-8")) if gl_f and gl_f.exists() else None
            forrige["trigger"] = bestem_trigger(forrige, gl_m)      # mod ITS forrige, ikke mod sig selv
            mf.write_text(json.dumps(forrige, indent=1, ensure_ascii=False), encoding="utf-8")
            print(f"manifest {h}: proveniensfelter (delta_vs_forrige, trigger) skrevet igennem — hashen er uaendret.")
        m["trigger"] = forrige.get("trigger", m["trigger"])          # denne koersel skabte ingen ny kalibrering
        koersel_trigger = f"{koersel_trigger} (kalibrering uaendret, manifest {h} genbrugt)"
    else:
        kraev_ny_version(forrige)
        if forrige:
            delta = delta_vs_forrige(ekstra["Dc"], m["modeller"]["curve_only"], forrige["modeller"]["curve_only"])
        m["delta_vs_forrige"] = delta
        h, _ = skriv_manifest(m)
        print(f"manifest: kalibreringer/manifest_{h}.json (v{m['version']}, refit {m['refit_maaned']}, n_obs {mc['n_obs']}, trigger: {m['trigger']})")
    if delta:
        print(f"delta vs forrige kalibrering over {delta['n_origins']} origins: max|dP| {delta['max_abs_dP']*100:.1f}pp ved "
              f"{delta['origin_max']} ({delta['dP_der']*100:+.1f}pp), middel|dP| {delta['mean_abs_dP']*100:.1f}pp, "
              f"andel >5pp {delta['andel_over_5pp']*100:.0f} %, max|dw| {delta['max_abs_dw']}, d_beta {delta['d_beta_pr_pp']}")

    # ---- F54: et genbrugt manifest maa ikke faa et andet baand (numpy-/platformsdrift i bootstrap-stroemmen) ----
    if genbrugt:
        bh = hashlib.sha256(json.dumps([ekstra["W"], ekstra["B"]]).encode("utf-8")).hexdigest()[:16]
        ref_bh = (forrige.get("bootstrap") or {}).get("band_sha256")
        if ref_bh is None and (HERE / "weights.json").exists():
            try:
                Wd = json.loads((HERE / "weights.json").read_text(encoding="utf-8"))
                if Wd.get("manifest_hash") == h and Wd.get("band"):
                    ref_bh = hashlib.sha256(json.dumps([Wd["band"]["W"], Wd["band"].get("base")]).encode("utf-8")).hexdigest()[:16]
            except ValueError:
                pass
        if ref_bh is None:
            sys.exit(f"FEJL (F54): manifest {h} genbruges, men bootstrap-baandet kan ikke verificeres: manifestet har ingen "
                     "bootstrap.band_sha256, og weights.json er ikke kalibreringens (mangler/overskrevet). Gendan "
                     "driftsvaegtene med 'git checkout v5/weights.json'. Intet er skrevet.")
        if ref_bh != bh:
            sys.exit(f"FEJL (F54): manifest {h} genbruges, men bootstrap-baandet afviger fra det i drift ({bh} != {ref_bh}) — "
                     f"numpy/platform har aendret stroemmen (miljoe nu: {miljoe()}). Intet er skrevet; laas numpy-versionen.")

    # ---- weights.json (samme skema som foer + version/manifest/bro/raa) ----
    fm = m["modeller"].get("fuldmodel")
    band = dict(metode="episode-blok-bootstrap af vaegte, fast standardisering; resamplets basisrate pr. traek",
                fodnote="Not a predictive interval; reflects weight sensitivity to episode composition",
                daekning="central 80% bootstrap estimation-sensitivity band; coverage not established",
                seed=SEED, n_draws=len(ekstra["W"]), W=ekstra["W"], base=ekstra["B"])
    out = dict(protocol_version=PROTOCOL, version=m["version"], manifest_hash=h,
               forrige_manifest=audit["forrige_hash"],
               refit_maaned=m["refit_maaned"], announcement_table_sha256=C.ann_sha256(ann_fil()),
               announcement_table_kanonisk=A2.tabel_hash(ann_fil()),          # F15: formatering/CRLF udloeser ikke en trigger
               trigger=m["trigger"], delta_vs_forrige=delta,
               # G4.2: en koersel der genbrugte manifestet registreres separat (refit-maaned og created_utc forbliver
               # kalibreringens). En ren reproduktion paa kalibreringens EGET snapshot er ingen koersel (koersel=None).
               koersel=(None if genbrugt and snap.name == forrige.get("snapshot")
                        and not A2.tabel_aendret(forrige.get("announcement_table_sha256"), A2.kanonisk_af(forrige), f=ann_fil()) else
                        dict(maaned=f"{ekstra['R'] // 12}-{ekstra['R'] % 12 + 1:02d}", utc=koersel_utc,
                             trigger=koersel_trigger, manifest_genbrugt=genbrugt)),
               created_utc=forrige["created_utc"] if genbrugt else m["created_utc"],
               snapshot=snap.name, snapshot_sha256=m["snapshot_sha256"],
               label="nber-onset", label_tekst="NBER-onset inden 4 kvartaler", frekvens="kvartal",
               n_obs=mc["n_obs"], n_episoder=len(ekstra["onsets_i_fit"]),     # G4.1: onsets med berettiget positivt origin
               base_rate=mc["base_rate"], operationel="curve_only",
               op=dict(features=["curve"], mu=mc["mu"], sd=mc["sd"], w=mc["w"], raa=mc["raa"],
                       wf_improvement=g["curve_only_wf"], wf_brier=g["curve_only_brier"],
                       vaerste_fejlalarm=m["modeller"]["curve_only"]["vaerste_fejlalarm"],
                       estimering_slut=mc["estimering_slut"]),
               band=band,
               fuldmodel=(dict(features=C.F5, mu=fm["mu"], sd=fm["sd"], w=fm["w"],
                               wf_improvement=fm["wf_improvement"], wf_brier=fm["wf_brier"],
                               vaerste_fejlalarm=fm["vaerste_fejlalarm"],
                               status=fuldmodel_status(g),
                               note=g["note"]) if fm else
                          dict(features=C.F5, status="unavailable — CAPE stale", note=g["note"])),
               benchmarks=dict(intercept=dict(wf_improvement=0.0),
                               curve_only=dict(wf_improvement=g["curve_only_wf"], wf_brier=g["curve_only_brier"],
                                               mu=mc["mu"]["curve"], sd=mc["sd"]["curve"], w=mc["w"],
                                               vaerste_fejlalarm=m["modeller"]["curve_only"]["vaerste_fejlalarm"]),
                               cp_serie="RECPROUSM156N"),
               gate=g, audit=audit, bro=b,
               fallback_note="Forhaandsforpligtet i RAADETS_KONSENSUS (Kimi R5/Sol R6) FOER foerste test; "
                             "v5.0.1 (§6): gaten kan ikke flytte den operationelle model.")
    out["benchmarks"].update(permanente_linjer())
    if m.get("uscorede"):
        out["uscorede"] = m["uscorede"]                     # RAADETS_2027 §3.3/§4: kun fra refit 2027-09
    (HERE / "weights.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"weights.json (v{m['version']}, manifest {h}) skrevet.")


if __name__ == "__main__":
    main()
