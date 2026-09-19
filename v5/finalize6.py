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
    skriver et manifest (kalibreringer/manifest_<hash>.json) og en fortegnsbevidst origin-
    audit mod forrige manifest: n_ny = n_gl + tilfoejede - fjernede, ellers FEJL.
§3.5 Kun modne origins (vinduets slut + 18 mdr <= refit-maaned) fittes OG scores.
§7  Bro ved fast inputvektor: (i) legacy-rygrad, (ii) korrigerede kilder paa samme origins,
    (iii) udvidet panel. Raa koefficienter (beta = w1/s, alpha = w0 - w1*mu/s) ved siden af.

Koer:  python finalize6.py [--snapshot ...]          (rekalibrering paa spine.csv)
       python finalize6.py --legacy                  (v5.0-manifest fra shiller_yale_2023-09.csv;
                                                      roerer ikke weights.json; legacy-replay §1.5a)
Kun stdlib + numpy.
"""
import csv, hashlib, json, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

import calibrate as C
import ablation2_nber as A2

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
    gs10 = C.read_fred(snap, "GS10"); tb3 = C.read_fred(snap, "TB3MS")
    (_, y10), (_, tb3m) = sorted(gs10.items())[-1], sorted(tb3.items())[-1]
    return {"curve": float(y10 - tb3m)}


HASH_UDELUKKET = ("created_utc", "code_commit", "kaldt_som", "hash",
                  "delta_vs_forrige", "trigger")   # proveniens om aendringen, ikke kalibreringsindhold

def manifest_hash(m):
    """Hash af kalibreringens INDHOLD (snapshot, rygrad, annonceringstabel, R, origins, vaegte, gate, audit):
    identiske input giver identisk hash uanset commit-id og tidspunkt."""
    body = {k: v for k, v in m.items() if k not in HASH_UDELUKKET}
    return hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()[:8]


def forrige_manifest():
    """Nyeste manifest ifoelge kalibreringer/index.json (None hvis ingen)."""
    idx = kal() / "index.json"
    if not idx.exists():
        return None
    entries = json.loads(idx.read_text(encoding="utf-8"))
    if not entries:
        return None
    e = entries[-1]
    f = kal() / f"manifest_{e['hash']}.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else None


def skriv_manifest(m):
    kal().mkdir(exist_ok=True)
    h = manifest_hash(m)
    m["hash"] = h
    (kal() / f"manifest_{h}.json").write_text(json.dumps(m, indent=1, ensure_ascii=False), encoding="utf-8")
    idx = kal() / "index.json"
    entries = json.loads(idx.read_text(encoding="utf-8")) if idx.exists() else []
    entries = [e for e in entries if e["hash"] != h]
    entries.append(dict(hash=h, version=m["version"], snapshot=m["snapshot"], refit_maaned=m["refit_maaned"],
                        created_utc=m["created_utc"], n_obs=m["modeller"]["curve_only"]["n_obs"]))
    idx.write_text(json.dumps(entries, indent=1), encoding="utf-8")
    return h


def rekalibrer(snap, spine_file=None, R=None, version=VERSION, kaldt_som="rekalibrering"):
    """Hele beregningen for een rygrad. Returnerer (manifest-dict uden hash, ekstra-dict til weights)."""
    meta = json.loads((snap / "meta.json").read_text(encoding="utf-8"))
    usrec = A2.load_usrec(snap)
    eps = A2.episodes_from_usrec(usrec)
    avail = A2.load_announcements(eps)
    R = R if R is not None else A2.midx(int(snap.name[:4]), int(snap.name[5:7]))
    Dc = A2.build_dataset(snap, ["curve"], spine_file=spine_file)
    D5 = A2.build_dataset(snap, C.F5, spine_file=spine_file)

    # walk-forward: kun modne origins scores (§3.5) — R_score = refit-maaneden
    resc, _, _ = A2.wf_nber(Dc, eps, avail, usrec, A2L, R_score=R)
    _, _, impc, brc = C.metrics(resc)
    fac = vaerste_fejlalarm(resc)
    identiske = A2.samme_origins(Dc, D5)
    gate = dict(identiske_origins=identiske, curve_only_wf=round(impc, 2), curve_only_brier=round(brc, 2))
    if identiske:
        res5, _, _ = A2.wf_nber(D5, eps, avail, usrec, A2L, R_score=R)
        _, _, imp5, br5 = C.metrics(res5)
        fa5 = vaerste_fejlalarm(res5)
        f3 = HERE / "ablation3_resultat.json"
        mde = json.loads(f3.read_text(encoding="utf-8")).get("mde_pp") if f3.exists() else None
        gap = imp5 - impc
        gate.update(fuldmodel_wf=round(imp5, 2), fuldmodel_brier=round(br5, 2), forskel_pp=round(gap, 2), mde_pp=mde,
                    fuldmodel_slaar=bool(imp5 > impc),
                    raadsbeslutning_paakraevet=bool(mde is not None and gap > mde),
                    note=(f"LL-forskel {abs(gap):.1f}pp {'<' if mde is not None and abs(gap) < mde else '>='} "
                          f"stoejgulv {mde if mde is not None else '?'}pp (trin 3-MDE). Gaten er mekanisk og kan ikke "
                          "flytte den operationelle model (RAADETS_V501 §6)."))
    else:
        res5, imp5, br5, fa5 = [], None, None, None
        gate.update(note="comparison unavailable — fuldmodellens og curve-onlys origin-identiteter matcher ikke "
                         "(CAPE stale/manglende?). Curve-only koerer videre (§2).")

    mc = fit_model(Dc, eps, avail, usrec, R)
    m5 = fit_model(D5, eps, avail, usrec, R) if identiske else None
    W, B, ngrp, grp = boot_weights(mc["_Z"], mc["_y"], Dc["qend"][mc["_elig"]], eps, NDRAW)

    spine_navn = spine_file or next((n for n in C.SPINE_FILER if (snap / n).exists()), "?")
    ann = HERE / "nber_announcements.csv"
    manifest = dict(
        version=version, protocol_version=PROTOCOL,
        created_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        code_commit=git_commit(), kaldt_som=kaldt_som,
        snapshot=snap.name, snapshot_sha256=meta["snapshot_sha256"],
        announcement_table_sha256=sha256_file(ann) if ann.exists() else None,
        refit_maaned=f"{R // 12}-{R % 12 + 1:02d}",
        spine=dict(fil=spine_navn, sha256=sha256_file(snap / spine_navn) if (snap / spine_navn).exists() else None,
                   sidste=meta.get("spine", {}).get("sidste") if not spine_file else None),
        operationel="curve_only",
        modeller={"curve_only": {k: v for k, v in mc.items() if not k.startswith("_")}
                  | dict(wf_improvement=round(impc, 2), wf_brier=round(brc, 2), vaerste_fejlalarm=fac)},
        gate=gate,
        origins=mc["_origins"],
        bootstrap=dict(seed=SEED, n_draws=len(W), n_blokke=ngrp),
    )
    if m5 is not None:
        manifest["modeller"]["fuldmodel"] = ({k: v for k, v in m5.items() if not k.startswith("_")}
                                            | dict(wf_improvement=round(imp5, 2), wf_brier=round(br5, 2),
                                                   vaerste_fejlalarm=fa5))
    ekstra = dict(W=W, B=B, grp=grp, resc=resc, res5=res5, mc=mc, m5=m5, Dc=Dc, D5=D5, eps=eps, avail=avail, usrec=usrec)
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


def bestem_trigger(m_ny, m_gl):
    """Hvorfor koerte rekalibreringen (§3.2)? Bestemmes af det NYE manifest mod det forrige DISTINKTE
    manifest: NBER-datering (annonceringstabel aendret), september (aarlig), ellers manuel/reparation.
    Foerste manifest efter legacy (v5.0) er per definition reparationen."""
    if m_gl is None or m_gl.get("version") in (None, LEGACY_VERSION):
        return "manuel/reparation (foerste kalibrering efter v5.0)"
    if m_gl.get("announcement_table_sha256") != m_ny["announcement_table_sha256"]:
        return "nber-datering (annonceringstabellen aendret)"
    if int(m_ny["refit_maaned"][5:7]) == 9:
        return "september (aarlig)"
    return "manuel/reparation"


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
        m["audit"] = dict(note="legacy: ingen forrige manifest")
        h = skriv_manifest(m)
        mapping = dict(note="RAADETS_V501 §3.3: historiske hovedbogsraekker roeres aldrig; denne fil kobler dem til v5.0-manifestet.",
                       manifest_hash=h, version=LEGACY_VERSION, hovedbogsraekker=["2026-08-12", "2026-09-09"])
        (kal() / "legacy_mapping.json").write_text(json.dumps(mapping, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"v5.0-manifest skrevet: kalibreringer/manifest_{h}.json + legacy_mapping.json (weights.json uroert)")
        return

    m, ekstra = rekalibrer(snap)
    g = m["gate"]
    print(f"curve-only: +{g['curve_only_wf']:.1f}%/+{g['curve_only_brier']:.1f}%  "
          + (f"fuldmodel: +{g['fuldmodel_wf']:.1f}%/+{g['fuldmodel_brier']:.1f}%  (identiske origins)" if g["identiske_origins"]
             else "fuldmodel: comparison unavailable"))
    if g.get("raadsbeslutning_paakraevet"):
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

    # ---- origin-audit mod forrige manifest (§3.5) ----
    forrige = forrige_manifest()
    audit = A2.origin_audit(forrige["origins"] if forrige else None, m["origins"])
    audit["forrige_hash"] = forrige["hash"] if forrige else None
    audit["forrige_version"] = forrige["version"] if forrige else None
    m["audit"] = audit
    print(f"origin-audit: n {audit['n_forrige']} -> {audit['n_ny']} | tilfoejede {audit['tilfoejede']} | "
          f"fjernede {audit['fjernede']} | omlabelede {audit['omlabelede']} | identitet {'OK' if audit['identitet_ok'] else 'FEJL'}")
    if not audit["identitet_ok"]:
        sys.exit("FEJL: origin-audit — uforklaret aendring i det berettigede origin-saet (§3.5).")
    if forrige and not audit["tilfoejede"] and not audit["fjernede"] and not audit["omlabelede"]:
        print("ADVARSEL: ingen aendring i origin-saettet — rekalibreringen aendrer ingen vaegte (ventet mellem events).")

    mc = ekstra["mc"]
    x = live_x(snap)
    b = bro(snap, ekstra, x)
    for navn, t in b["trin"].items():
        print(f"bro {navn:<40} P={t['P']*100:5.1f}%  w={t['w']}  n={t['n_obs']}  beta={t['raa'].get('beta_curve_pr_pp')}")
    print(f'bro: "{BRO_SAETNING}"')

    # Idempotens: samme origins, labels og vaegte som forrige manifest = SAMME kalibrering.
    # Saa genbruges forrige hash (intet nyt manifest); kaeden holder, og en genkoersel uden
    # dataaendring (fx den aarlige september-koersel i et roligt aar) skaber ikke stoej.
    def _indhold(mod, origins):
        return (origins, mod["w"], mod["mu"], mod["sd"], mod["base_rate"])
    m["trigger"] = bestem_trigger(m, forrige)
    delta = None
    if forrige and _indhold(forrige["modeller"]["curve_only"], forrige["origins"]) == _indhold(m["modeller"]["curve_only"], m["origins"]):
        h = forrige["hash"]
        audit["forrige_hash"] = forrige["audit"].get("forrige_hash")
        audit["forrige_version"] = forrige["audit"].get("forrige_version")
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
    else:
        if forrige:
            delta = delta_vs_forrige(ekstra["Dc"], m["modeller"]["curve_only"], forrige["modeller"]["curve_only"])
        m["delta_vs_forrige"] = delta
        h = skriv_manifest(m)
        print(f"manifest: kalibreringer/manifest_{h}.json (v{VERSION}, refit {m['refit_maaned']}, n_obs {mc['n_obs']}, trigger: {m['trigger']})")
    if delta:
        print(f"delta vs forrige kalibrering over {delta['n_origins']} origins: max|dP| {delta['max_abs_dP']*100:.1f}pp ved "
              f"{delta['origin_max']} ({delta['dP_der']*100:+.1f}pp), middel|dP| {delta['mean_abs_dP']*100:.1f}pp, "
              f"andel >5pp {delta['andel_over_5pp']*100:.0f} %, max|dw| {delta['max_abs_dw']}, d_beta {delta['d_beta_pr_pp']}")

    # ---- weights.json (samme skema som foer + version/manifest/bro/raa) ----
    fm = m["modeller"].get("fuldmodel")
    band = dict(metode="episode-blok-bootstrap af vaegte, fast standardisering; resamplets basisrate pr. traek",
                fodnote="Not a predictive interval; reflects weight sensitivity to episode composition",
                daekning="central 80% bootstrap estimation-sensitivity band; coverage not established",
                seed=SEED, n_draws=len(ekstra["W"]), W=ekstra["W"], base=ekstra["B"])
    out = dict(protocol_version=PROTOCOL, version=VERSION, manifest_hash=h,
               forrige_manifest=audit["forrige_hash"],
               refit_maaned=m["refit_maaned"], announcement_table_sha256=m["announcement_table_sha256"],
               trigger=m["trigger"], delta_vs_forrige=delta,
               created_utc=m["created_utc"], snapshot=snap.name, snapshot_sha256=m["snapshot_sha256"],
               label="nber-onset", label_tekst="NBER-onset inden 4 kvartaler", frekvens="kvartal",
               n_obs=mc["n_obs"], n_episoder=len({o for wo in A2.nber_labels(ekstra["Dc"], ekstra["eps"], ekstra["usrec"])[1] for o in wo}),
               base_rate=mc["base_rate"], operationel="curve_only",
               op=dict(features=["curve"], mu=mc["mu"], sd=mc["sd"], w=mc["w"], raa=mc["raa"],
                       wf_improvement=g["curve_only_wf"], wf_brier=g["curve_only_brier"],
                       vaerste_fejlalarm=m["modeller"]["curve_only"]["vaerste_fejlalarm"],
                       estimering_slut=mc["estimering_slut"]),
               band=band,
               fuldmodel=(dict(features=C.F5, mu=fm["mu"], sd=fm["sd"], w=fm["w"],
                               wf_improvement=fm["wf_improvement"], wf_brier=fm["wf_brier"],
                               vaerste_fejlalarm=fm["vaerste_fejlalarm"],
                               status="testet, ikke bestaaet mod benchmark (trin 6; genkoert v5.0.1)" if not g["fuldmodel_slaar"]
                               else "slaar curve-only i wf — RAADSBESLUTNING PAAKRAEVET (v5.1), ikke operationel (§6)",
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
    (HERE / "weights.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"weights.json (v{VERSION}, manifest {h}) skrevet.")


if __name__ == "__main__":
    main()
