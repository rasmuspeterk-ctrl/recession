#!/usr/bin/env python3
"""
demotion.py - analyse til raadets 2027-dagsorden: SYMMETRISK genforsvar af de fem incumbents.

FORMAAL
  Svarer paa kode-reviewets fund G1.4 (2026-10-15): trin 4 (ablation4_features.py) brugte en
  ASYMMETRISK regel. En udfordrer skulle levere dLL >= +2,0pp OG dBrier >= +2,0pp (A1), begge
  niveauer i >= 80 % af LOEO-folds og dLL > 0 i ALLE folds (A2) samt forventet fortegn i >= 80 %
  af LOEO-refits (A3). En incumbent blev derimod kun demoteret, hvis det at DROPPE den gav
  dLL >= +1,0pp OG dBrier >= +1,0pp OG dLL(drop) > 0 i >= 80 % af folds. Blueprintet
  (RAADETS_KONSENSUS.md section 4: "No grandfather immunity, explicitly including the curve")
  fastlaegger ingen demotionstaerskel; demotionsreglen var sekretaerens fortolkning.
  Denne analyse genkoerer incumbent-genforsvaret under en SYMMETRISK regel: hver incumbent
  behandles som en udfordrer mod de oevrige og skal klare PRAECIS udfordrernes bar (A1/A2/A3 +
  persistens printet, < 60 % flagges) for at beholde pladsen.

DESIGN
  Paneler:
    (a) trin4 : snapshot 2026-09-19 med den trunkerede Yale-rygrad (shiller_yale_2023-09.csv) og
                trin 4's egen build/walk-forward (ablation4_features.build + .wf). Erratum-koerslen
                (ablation4_erratum_resultat.json) viste, at dette panel giver trin 4's publicerede
                incumbent-tal bit for bit; her kontrolleres det igen, og desuden mod den nuvaerende
                mappe 2026-08-09 (hvis hash ikke laengere er trin 4's).
    (b) v501  : snapshot 2026-09-19, spine.csv, raekkeunivers efter RAADETS_V501 section 2
                (ablation2_nber.build_dataset med F5), refit-maaned R = 2026-09 og wf_nber med
                R_score = R (kun modne origins scores). Curve-only og fuldmodel kontrolleres mod
                manifest 72c3371d (+27,05 %/+24,15 % paa 198 origins; F5 +23,16 %).
  Test pr. incumbent f i et saet S (f i S): "add-effekt" = S mod S\\{f} paa identiske origins
  (samme funktioner som trin 4: paired_metrics, loeo_deltas, bootstrap_persist (1000 traek, seed 42),
  sign_stability). Add-effekten er praecis minus trin 4's drop-effekt, saa de publicerede tal
  genfindes med modsat fortegn.
    A1  dLL_add >= +2,0pp OG dBrier_add >= +2,0pp
    A2  >= 80 % af LOEO-folds holder A1 OG dLL_add > 0 i ALLE folds
    A3  fortegn stabilt i >= 80 % af LOEO-refits. Ingen oekonomisk retning er praeregistreret for
        incumbents (blueprintet naevner kun "expected sign" for udfordrere), saa A3 anvendes som
        STABILITET af fuld-fit-fortegnet (som ablation7's G4); v4's fortegn rapporteres ved siden af.
    persistens: andel af 1000 episode-blok-bootstrap-traek med dLL_add > 0; < 60 % flagges.
  Tre regler scores paa de SAMME tal:
    asymmetrisk_publiceret : demoter iff dLL_drop >= 1 OG dBrier_drop >= 1 OG dLL_drop > 0 i >= 80 % folds
    symmetrisk             : behold iff A1 OG A2 OG A3 (udfordrernes OPTAGET-bar), ellers demoter
    neutral_LL             : reviewerens hypotetiske regel: demoter iff dLL_drop > 0 OG i >= 80 % folds
  Procedurer:
    simultan   : alle fem testes mod F5\\{f}; de der fejler, fjernes paa een gang.
    sekventiel : baglaens eliminering til fikspunkt (spejl af trin 4's multi-optagelse "stoerste dLL
                 foerst, retest mod ny baseline"): den incumbent med laveste dLL_add blandt de
                 fejlende fjernes, alle tilbagevaerende retestes mod det nye saet, indtil alle bestaar.
  Slutmodellen under hver regel/procedure maales mod curve-only paa identiske origins med de gates
  der har vaeret i brug: v5.0 trin 6 (kun LL: imp > 0 og imp > curve-only), v5.0.1 (forskel mod
  trin 3-MDE 4,42pp + gatens egen MDE via ablation3.mde_bootstrap) og v5.1/ablation7 (G2-G6 inkl.
  aera-split 1990). De publicerede udfordrer-resultater (erratum) vedlaegges til sammenligning.

AENDRER INTET I DRIFTEN: scriptet laeser kun snapshots og resultatfiler og skriver udelukkende
  v5/analyser/demotion_resultat.json. weights.json, manifester, kalibreringer og alle trin-scripts
  er uroerte. Resultaterne er fakta til raadets 2027-dagsorden, ikke beslutninger; feature-
  soegningen er lukket (v5.0.1 section 6, ablation7).

Deterministisk: faste seeds (42), ingen vaeggeur ud over created_utc; indholds_hash daekker alt andet.
Koer fra v5-mappen:  cd v5 && python analyser/demotion.py
"""
import hashlib, json, sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent          # v5/analyser
V5 = HERE.parent
sys.path.insert(0, str(V5))
import calibrate as C                 # noqa: E402
import ablation2_nber as A2           # noqa: E402
import ablation3_frekvens as A3       # noqa: E402
import ablation4_features as A4       # noqa: E402

PROTOCOL = "analyse-demotion-G1.4"
SNAP = V5 / "data" / "raw" / "2026-09-19"
SNAP_TRIN4_MAPPE = V5 / "data" / "raw" / "2026-08-09"
LEGACY_SPINE = "shiller_yale_2023-09.csv"
R_V501 = A2.midx(2026, 9)
F5 = list(C.F5)
L = A2.L_EMBARGO
UDFIL = HERE / "demotion_resultat.json"

# ------------------------------------------------------------------ paneler
class Panel:
    """Et panel = datasaet i trin 4-form (D['X'][feature], qend, year, qk) + en walk-forward-motor.
    trin4: ablation4_features.wf (alle origins scores, som i trin 4).
    v501 : ablation2_nber.wf_nber med R_score = R (kun modne origins scores, som i finalize6)."""

    def __init__(self, navn, D, eps, avail, usrec, motor, R=None):
        self.navn, self.D, self.eps, self.avail, self.usrec, self.motor, self.R = navn, D, eps, avail, usrec, motor, R
        self._cache = {}

    def wf(self, feats):
        key = tuple(feats)
        if key not in self._cache:
            if self.motor == "trin4":
                self._cache[key] = A4.wf(self.D, list(feats), self.eps, self.avail, self.usrec)
            else:
                Ds = dict(F=np.stack([self.D["X"][f] for f in feats], axis=1),
                          qend=self.D["qend"], year=self.D["year"], qk=self.D["qk"])
                res, _, _ = A2.wf_nber(Ds, self.eps, self.avail, self.usrec, L, R_score=self.R)
                self._cache[key] = {(y, q): (p, yy) for (y, q, p, yy) in res}
        return self._cache[key]


def panel_trin4(snap, spine):
    """Trin 4's eget panel: A4.build (BASE10-maske) paa den angivne rygrad."""
    A4.SPINE_FILE = spine
    try:
        usrec = A2.load_usrec(snap)
        eps = A2.episodes_from_usrec(usrec)
        avail = A2.load_announcements(eps)
        D = A4.build(snap)
    finally:
        A4.SPINE_FILE = None
    return Panel("trin4", D, eps, avail, usrec, "trin4")


def panel_v501(snap, R):
    """v5.0.1-panelet: section 2-univers for F5; curve-only's univers kontrolleres identisk (finalize6-gate)."""
    usrec = A2.load_usrec(snap)
    eps = A2.episodes_from_usrec(usrec)
    avail = A2.load_announcements(eps, usrec=usrec)
    D5 = A2.build_dataset(snap, F5)
    Dc = A2.build_dataset(snap, ["curve"])
    identiske = A2.samme_origins(Dc, D5)
    D = dict(qk=list(D5["qk"]), qend=D5["qend"], year=D5["year"],
             X={f: D5["F"][:, i] for i, f in enumerate(F5)})
    P = Panel("v501", D, eps, avail, usrec, "v501", R=R)
    P.identiske_origins = bool(identiske)
    return P

# ------------------------------------------------------------- een incumbent
def test_incumbent(P, S, f):
    """Add-effekt af f i S: wf(S) mod wf(S uden f) paa identiske origins + alle gates/regler."""
    rest = [x for x in S if x != f]
    m_med, m_uden = P.wf(S), P.wf(rest)
    ia, ba, ib, bb, n, ks = A4.paired_metrics(m_med, m_uden)
    dll, dbr = ia - ib, ba - bb                         # add-effekt (= minus trin 4's drop-effekt)
    folds = A4.loeo_deltas(m_med, m_uden, ks, P.eps)
    nf = len(folds)
    lvl = sum(1 for (_, a, b) in folds if a >= 2.0 and b >= 2.0)
    pos = sum(1 for (_, a, _) in folds if a > 0)        # folds hvor f HJAELPER LL
    neg = sum(1 for (_, a, _) in folds if a < 0)        # folds hvor DROP hjaelper LL (trin 4's 'folds_pos')
    persist, mde = A4.bootstrap_persist(m_med, m_uden, ks, P.eps)
    fsign, _, _ = A4.sign_stability(P.D, list(S), f, P.eps, P.usrec, +1)
    fsign = int(np.sign(fsign))
    if fsign == 0:
        sstab, sfolds = 0.0, 0
    else:
        _, sstab, sfolds = A4.sign_stability(P.D, list(S), f, P.eps, P.usrec, fsign)
    v4_sign = int(np.sign(C.V4["W_12M"][F5.index(f) + 1]))
    A1 = bool(dll >= 2.0 and dbr >= 2.0)
    A2g = bool(nf > 0 and lvl / nf >= 0.8 and pos == nf)
    A3g = bool(sstab >= 80.0)
    sym = bool(A1 and A2g and A3g)
    asym_demote = bool((-dll) >= 1.0 and (-dbr) >= 1.0 and nf > 0 and neg / nf >= 0.8)
    neutral_demote = bool((-dll) > 0 and nf > 0 and neg / nf >= 0.8)
    return dict(
        saet=list(S), baseline=rest, n_parret=n,
        imp_med=round(ia, 2), imp_uden=round(ib, 2), brier_med=round(ba, 2), brier_uden=round(bb, 2),
        dLL_add=round(dll, 2), dBrier_add=round(dbr, 2),
        dLL_ved_drop=round(-dll, 2), dBrier_ved_drop=round(-dbr, 2),
        folds=nf, folds_niveau_pct=round(lvl / nf * 100, 0) if nf else 0.0,
        folds_add_pos_pct=round(pos / nf * 100, 0) if nf else 0.0,
        folds_drop_pos_pct=round(neg / nf * 100, 0) if nf else 0.0,
        alle_folds_positive=bool(nf > 0 and pos == nf),
        persistens_pct=round(persist, 1), mde_pp=round(mde, 2), persistens_flag=bool(persist < 60),
        fortegn_fuldfit=fsign, fortegn_stab_pct=round(sstab, 0), fortegn_folds=sfolds,
        fortegn_v4=v4_sign, fortegn_som_v4=bool(fsign == v4_sign),
        A1=A1, A2=A2g, A3=A3g,
        sym_BESTAAR=sym, sym_BESTAAR_inkl_persistens=bool(sym and persist >= 60),
        asym_DEMOTERET=asym_demote, neutral_LL_DEMOTERET=neutral_demote)


REGLER = {
    "asymmetrisk_publiceret": lambda t: t["asym_DEMOTERET"],
    "symmetrisk": lambda t: not t["sym_BESTAAR"],
    "neutral_LL": lambda t: t["neutral_LL_DEMOTERET"],
}


def eliminering(P, regel, cache):
    """Baglaens eliminering til fikspunkt: fjern den fejlende incumbent med laveste dLL_add, retest alle."""
    S = list(F5)
    sti = []
    while True:
        tests = {}
        for f in S:
            key = (tuple(S), f)
            if key not in cache:
                cache[key] = test_incumbent(P, S, f)
            tests[f] = cache[key]
        fejler = [f for f in S if REGLER[regel](tests[f])]
        runde = dict(runde=len(sti) + 1, saet=list(S),
                     tests={f: {k: tests[f][k] for k in ("dLL_add", "dBrier_add", "folds_niveau_pct",
                                                           "alle_folds_positive", "persistens_pct",
                                                           "fortegn_stab_pct", "A1", "A2", "A3",
                                                           "sym_BESTAAR", "asym_DEMOTERET", "neutral_LL_DEMOTERET")}
                            for f in S},
                     fejler=fejler)
        if not fejler:
            runde["fjernet"] = None
            sti.append(runde)
            break
        vaerst = min(fejler, key=lambda f: tests[f]["dLL_add"])
        runde["fjernet"] = vaerst
        sti.append(runde)
        S = [x for x in S if x != vaerst]
        if len(S) == 1:
            sti.append(dict(runde=len(sti) + 1, saet=list(S), tests={}, fejler=[], fjernet=None,
                            note="sidste feature testes ikke mod den tomme model"))
            break
    return S, sti

# ------------------------------------------------------ slutmodel mod curve-only
def mod_curve_only(P, S, mde_trin3):
    """S mod curve-only paa identiske origins med de gates der har vaeret i brug (v5.0 trin 6, v5.0.1, v5.1)."""
    mS, mc = P.wf(S), P.wf(["curve"])
    iS, bS, ic, bc, n, ks = A4.paired_metrics(mS, mc)
    out = dict(features=list(S), n_parret=n, wf_improvement=round(iS, 2), wf_brier=round(bS, 2),
               curve_only_wf=round(ic, 2), curve_only_brier=round(bc, 2))
    if list(S) == ["curve"]:
        out["identisk_med_curve_only"] = True
        return out
    dll, dbr = iS - ic, bS - bc
    folds = A4.loeo_deltas(mS, mc, ks, P.eps)
    nf = len(folds)
    lvl = sum(1 for (_, a, b) in folds if a >= 2.0 and b >= 2.0)
    pos_all = bool(nf > 0 and all(a > 0 for (_, a, _) in folds))
    persist, mde_pers = A4.bootstrap_persist(mS, mc, ks, P.eps)
    pre = [k for k in ks if k[0] < 1990]; post = [k for k in ks if k[0] >= 1990]

    def imp_on(keys, m):
        rows = [(y, q, m[(y, q)][0], m[(y, q)][1]) for (y, q) in keys]
        return C.metrics(rows)[2] if keys else float("nan")
    d_pre = imp_on(pre, mS) - imp_on(pre, mc)
    d_post = imp_on(post, mS) - imp_on(post, mc)
    paired = [(y, q, mS[(y, q)][0], mc[(y, q)][0], mS[(y, q)][1]) for (y, q) in ks]
    _pt, sd_g, _lo, _hi = A3.mde_bootstrap(paired, P.eps)
    mde_gate = round(1.96 * sd_g, 2)
    out.update(
        identisk_med_curve_only=False,
        dLL=round(dll, 2), dBrier=round(dbr, 2),
        folds=nf, folds_niveau_pct=round(lvl / nf * 100, 0) if nf else 0.0, alle_folds_positive=pos_all,
        persistens_pct=round(persist, 1), mde_persistens_pp=round(mde_pers, 2),
        aera_pre1990_dLL=round(d_pre, 2), aera_post1990_dLL=round(d_post, 2), n_pre=len(pre), n_post=len(post),
        gate_v50_trin6_kun_LL=dict(regel="imp > 0 og imp > curve-only (git 3e71be9)", slaar=bool(iS > 0 and iS > ic)),
        gate_v501=dict(regel="forskel_pp mod trin 3-MDE; gaten kan ikke flytte den operationelle model (V501 section 6)",
                       forskel_pp=round(dll, 2), mde_trin3_pp=mde_trin3, mde_gate_pp=mde_gate,
                       slaar=bool(iS > ic), raadsbeslutning_paakraevet=bool(mde_trin3 is not None and dll > mde_trin3)),
        gate_v51_ablation7=dict(G2_dLL2_dBrier2=bool(dll >= 2.0 and dbr >= 2.0),
                                G3_LOEO=bool(nf > 0 and lvl / nf >= 0.8 and pos_all),
                                G5_aera_split=bool(d_pre > 0 and d_post > 0),
                                G6_persistens60=bool(persist >= 60),
                                alle=bool(dll >= 2.0 and dbr >= 2.0 and nf > 0 and lvl / nf >= 0.8 and pos_all
                                          and d_pre > 0 and d_post > 0 and persist >= 60)))
    return out

# ------------------------------------------------------------------ koersel
def koer_panel(P, mde_trin3):
    cache = {}
    res = dict(n_raekker=len(P.D["qend"]), univers=f"{P.D['qk'][0][0]}Q{P.D['qk'][0][1]}-{P.D['qk'][-1][0]}Q{P.D['qk'][-1][1]}",
               n_scorede_F5=len(P.wf(F5)), n_scorede_curve_only=len(P.wf(["curve"])))
    ks = sorted(P.wf(F5))
    res["scorede_origins"] = f"{ks[0][0]}Q{ks[0][1]}-{ks[-1][0]}Q{ks[-1][1]}"
    # runde 1 = simultan: alle fem mod F5 uden f
    sim = {}
    for f in F5:
        cache[(tuple(F5), f)] = test_incumbent(P, F5, f)
        sim[f] = cache[(tuple(F5), f)]
    res["incumbents_mod_F5"] = sim
    res["simultan"] = {}
    for regel in REGLER:
        demoteret = [f for f in F5 if REGLER[regel](sim[f])]
        res["simultan"][regel] = dict(demoteret=demoteret, slutsaet=[f for f in F5 if f not in demoteret])
    res["sekventiel"] = {}
    for regel in REGLER:
        S, sti = eliminering(P, regel, cache)
        res["sekventiel"][regel] = dict(slutsaet=S, n_runder=len(sti), sti=sti)
    # slutmodeller mod curve-only
    saet = {"F5_publiceret": F5}
    for regel in REGLER:
        saet[f"simultan/{regel}"] = res["simultan"][regel]["slutsaet"]
        saet[f"sekventiel/{regel}"] = res["sekventiel"][regel]["slutsaet"]
    res["slutmodel_mod_curve_only"] = {navn: mod_curve_only(P, S, mde_trin3) for navn, S in saet.items()}
    return res


def reproduktion_trin4(P, publ):
    """Trin 4's publicerede incumbent-tal (drop-effekt) genfindes som minus add-effekten."""
    ok = True; detaljer = {}
    for f in F5:
        t = test_incumbent(P, F5, f)
        p = publ["incumbents"][f]
        match = (abs(t["dLL_ved_drop"] - p["dLL_ved_drop"]) < 0.005 and abs(t["dBrier_ved_drop"] - p["dBrier_ved_drop"]) < 0.005
                 and t["folds_drop_pos_pct"] == p["folds_pos_pct"] and t["asym_DEMOTERET"] == p["DEMOTERET"])
        ok &= match
        detaljer[f] = dict(publiceret=[p["dLL_ved_drop"], p["dBrier_ved_drop"], p["folds_pos_pct"]],
                           her=[t["dLL_ved_drop"], t["dBrier_ved_drop"], t["folds_drop_pos_pct"]], match=bool(match))
    return bool(ok), detaljer


def indholds_hash(d):
    body = {k: v for k, v in d.items() if k != "created_utc"}
    return hashlib.sha256(json.dumps(body, sort_keys=True).encode("utf-8")).hexdigest()[:16]


def main():
    meta = json.loads((SNAP / "meta.json").read_text(encoding="utf-8"))
    publ4 = json.loads((V5 / "ablation4_resultat.json").read_text(encoding="utf-8"))
    err4 = json.loads((V5 / "ablation4_erratum_resultat.json").read_text(encoding="utf-8"))
    publ7 = json.loads((V5 / "ablation7_resultat.json").read_text(encoding="utf-8"))
    man = json.loads((V5 / "kalibreringer" / "manifest_72c3371d.json").read_text(encoding="utf-8"))
    mde_trin3 = json.loads((V5 / "ablation3_resultat.json").read_text(encoding="utf-8")).get("mde_pp")

    print(f"=== analyser/demotion.py - {PROTOCOL} - snapshot {SNAP.name} ===")
    print("Svarer paa review-fund G1.4 (asymmetrisk demotionsregel i trin 4). AENDRER INTET I DRIFTEN.\n")

    # ---------------- panel (a): trin 4
    Pa = panel_trin4(SNAP, LEGACY_SPINE)
    rep_ok, rep_det = reproduktion_trin4(Pa, publ4)
    mc, m5 = Pa.wf(["curve"]), Pa.wf(F5)
    m2 = Pa.wf(["curve", "cape_pct"])
    i2, b2, ic, bc, n7, _ = A4.paired_metrics(m2, mc)
    _, _, i5, b5 = C.metrics([(y, q, p, yy) for (y, q), (p, yy) in sorted(m5.items())])
    rep_a = dict(trin4_incumbents_publiceret_genfundet=rep_ok, detaljer=rep_det,
                 ablation7_reference=dict(curve_only=[round(ic, 2), round(bc, 2)], curvecape=[round(i2, 2), round(b2, 2)],
                                          dLL=round(i2 - ic, 2), dBrier=round(b2 - bc, 2), n=n7,
                                          publiceret=dict(curve_only=[publ7["curveonly"]["improvement"], publ7["curveonly"]["brier"]],
                                                          curvecape=[publ7["curvecape"]["improvement"], publ7["curvecape"]["brier"]],
                                                          dLL=publ7["dLL"], dBrier=publ7["dBrier"], n=publ7["n_parret"]),
                                          match=bool(abs(i2 - ic - publ7["dLL"]) < 0.005 and abs(b2 - bc - publ7["dBrier"]) < 0.005
                                                     and n7 == publ7["n_parret"])),
                 F5_wf=[round(i5, 2), round(b5, 2)],
                 snapshot_trin4_publiceret_sha256=publ4["snapshot_sha256"],
                 mappe_2026_08_09_sha256_nu=json.loads((SNAP_TRIN4_MAPPE / "meta.json").read_text(encoding="utf-8")).get("snapshot_sha256"))
    # samme tal fra den nuvaerende 2026-08-09-mappe (hash afviger fra trin 4's - mappen er genhentet)
    try:
        Pa0 = panel_trin4(SNAP_TRIN4_MAPPE, None)
        ok0, det0 = reproduktion_trin4(Pa0, publ4)
        rep_a["mappe_2026_08_09_genfinder_trin4"] = bool(ok0)
    except SystemExit as e:
        rep_a["mappe_2026_08_09_genfinder_trin4"] = f"ikke koert: {e}"
    print(f"Panel (a) trin4: reproduktion af publicerede incumbents: {'OK' if rep_ok else 'AFVIGER'}; "
          f"ablation7-reference (curve+cape vs curve-only) {'OK' if rep_a['ablation7_reference']['match'] else 'AFVIGER'}; "
          f"mappe 2026-08-09: {rep_a['mappe_2026_08_09_genfinder_trin4']}")
    res_a = koer_panel(Pa, mde_trin3)
    res_a["reproduktion"] = rep_a
    res_a["definition"] = dict(snapshot=SNAP.name, rygrad=LEGACY_SPINE, build="ablation4_features.build (BASE10-maske)",
                               walk_forward="ablation4_features.wf (alle origins scores, ingen R_score)", R_score=None)

    # ---------------- panel (b): v5.0.1
    Pb = panel_v501(SNAP, R_V501)
    mcb, m5b = Pb.wf(["curve"]), Pb.wf(F5)
    _, _, icb, bcb = C.metrics([(y, q, p, yy) for (y, q), (p, yy) in sorted(mcb.items())])
    _, _, i5b, b5b = C.metrics([(y, q, p, yy) for (y, q), (p, yy) in sorted(m5b.items())])
    g = man["gate"]
    rep_b = dict(identiske_origins=Pb.identiske_origins,
                 curve_only=[round(icb, 2), round(bcb, 2), len(mcb)], fuldmodel=[round(i5b, 2), round(b5b, 2), len(m5b)],
                 manifest_72c3371d=dict(curve_only=[g["curve_only_wf"], g["curve_only_brier"]],
                                        fuldmodel=[g["fuldmodel_wf"], g["fuldmodel_brier"]], forskel_pp=g["forskel_pp"],
                                        mde_pp=g["mde_pp"], refit_maaned=man["refit_maaned"]),
                 match=bool(abs(icb - g["curve_only_wf"]) < 0.005 and abs(bcb - g["curve_only_brier"]) < 0.005
                            and abs(i5b - g["fuldmodel_wf"]) < 0.005 and abs(b5b - g["fuldmodel_brier"]) < 0.005))
    print(f"Panel (b) v501: curve-only +{icb:.2f}%/+{bcb:.2f}% paa {len(mcb)} origins, F5 +{i5b:.2f}%/+{b5b:.2f}% - "
          f"manifest 72c3371d {'genfundet' if rep_b['match'] else 'AFVIGER'}; identiske origins: {Pb.identiske_origins}")
    res_b = koer_panel(Pb, mde_trin3)
    res_b["reproduktion"] = rep_b
    res_b["definition"] = dict(snapshot=SNAP.name, rygrad="spine.csv", build="ablation2_nber.build_dataset(F5) (V501 section 2)",
                               walk_forward="ablation2_nber.wf_nber med R_score", R_score="2026-09", R_score_midx=R_V501)

    # ---------------- tabeller
    for navn, res in (("(a) trin4", res_a), ("(b) v501", res_b)):
        print(f"\nINCUMBENTS mod F5 uden sig selv - panel {navn} ({res['n_scorede_F5']} scorede origins, {res['scorede_origins']}):")
        print(f"{'feature':<10}{'dLL_add':>8}{'dBr_add':>8}{'niv%':>6}{'allePos':>8}{'pers%':>7}{'MDE':>6}{'tegn':>5}{'stab%':>6}"
              f"  A1 A2 A3  asym   sym   neutral")
        for f in F5:
            t = res["incumbents_mod_F5"][f]
            print(f"{f:<10}{t['dLL_add']:>+8.2f}{t['dBrier_add']:>+8.2f}{t['folds_niveau_pct']:>5.0f}%{str(t['alle_folds_positive']):>8}"
                  f"{t['persistens_pct']:>6.1f}%{t['mde_pp']:>6.1f}{'+' if t['fortegn_fuldfit'] > 0 else '-':>5}{t['fortegn_stab_pct']:>5.0f}%"
                  f"  {'x' if t['A1'] else '.'}  {'x' if t['A2'] else '.'}  {'x' if t['A3'] else '.'}  "
                  f"{'DEMOT' if t['asym_DEMOTERET'] else 'behold':<6} {'behold' if t['sym_BESTAAR'] else 'DEMOT':<6} "
                  f"{'DEMOT' if t['neutral_LL_DEMOTERET'] else 'behold'}" + ("  [persistens<60%]" if t['persistens_flag'] else ""))
        for regel in REGLER:
            s, q = res["simultan"][regel], res["sekventiel"][regel]
            print(f"  {regel:<24} simultan -> {s['slutsaet']}   sekventiel ({q['n_runder']} runder) -> {q['slutsaet']}")
        print(f"  slutmodeller mod curve-only (identiske origins):")
        for nm, m in res["slutmodel_mod_curve_only"].items():
            if m.get("identisk_med_curve_only"):
                print(f"    {nm:<34} {m['features']} = curve-only (+{m['wf_improvement']:.2f}%/+{m['wf_brier']:.2f}%)")
            else:
                g7 = m["gate_v51_ablation7"]
                print(f"    {nm:<34} {m['features']}: +{m['wf_improvement']:.2f}%/+{m['wf_brier']:.2f}% vs curve-only "
                      f"+{m['curve_only_wf']:.2f}%/+{m['curve_only_brier']:.2f}%  dLL={m['dLL']:+.2f} dBrier={m['dBrier']:+.2f} "
                      f"(n={m['n_parret']}; MDE trin3 {m['gate_v501']['mde_trin3_pp']}, gate {m['gate_v501']['mde_gate_pp']}); "
                      f"v5.0-trin6 {'slaar' if m['gate_v50_trin6_kun_LL']['slaar'] else 'slaar ikke'}; "
                      f"v5.1 G2={g7['G2_dLL2_dBrier2']} G3={g7['G3_LOEO']} G5={g7['G5_aera_split']} G6={g7['G6_persistens60']}; "
                      f"aera pre/post 1990 {m['aera_pre1990_dLL']:+.2f}/{m['aera_post1990_dLL']:+.2f}")

    # ---------------- udfald mod det publicerede
    def udfald(res):
        sym_sim = res["simultan"]["symmetrisk"]["slutsaet"]; sym_seq = res["sekventiel"]["symmetrisk"]["slutsaet"]
        return dict(publiceret="feature-saettet UAENDRET: de 5 incumbents bestaar (asymmetrisk regel)",
                    asymmetrisk_genkoert=res["simultan"]["asymmetrisk_publiceret"]["slutsaet"],
                    symmetrisk_simultan=sym_sim, symmetrisk_sekventiel=sym_seq,
                    neutral_LL_simultan=res["simultan"]["neutral_LL"]["slutsaet"],
                    neutral_LL_sekventiel=res["sekventiel"]["neutral_LL"]["slutsaet"],
                    feature_saet_ville_aendres_under_symmetri=bool(sym_sim != F5 or sym_seq != F5),
                    demoteret_under_symmetri_simultan=[f for f in F5 if f not in sym_sim],
                    operationel_model_beroert="nej: v5.0.1 section 6 laaser curve-only; fuldmodellen er kun benchmark")
    out = dict(protocol_version=PROTOCOL, created_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
               review_fund="G1.4", snapshot=SNAP.name, snapshot_sha256=meta["snapshot_sha256"],
               aendrer_driften=False, seed=A4.SEED, mde_trin3_pp=mde_trin3,
               regler=dict(udfordrer_bar_trin4="A1: dLL>=2 & dBrier>=2; A2: >=80% folds paa niveau & alle folds dLL>0; A3: fortegn >=80% LOEO-refits; persistens<60% flagges",
                           asymmetrisk_publiceret="demoter iff dLL(drop)>=1 & dBrier(drop)>=1 & dLL(drop)>0 i >=80% folds (ablation4_features.py:21-23, :299)",
                           symmetrisk="behold iff incumbenten som udfordrer mod de oevrige klarer A1 & A2 & A3 (fortegn = stabilitet af fuld-fit-fortegnet, ingen praeregistreret retning)",
                           neutral_LL="reviewerens hypotetiske regel: demoter iff dLL(drop)>0 & dLL(drop)>0 i >=80% folds",
                           sekventiel="baglaens eliminering til fikspunkt: laveste dLL_add blandt de fejlende fjernes foerst, alle retestes mod det nye saet"),
               paneler=dict(trin4=res_a, v501=res_b),
               udfald_vs_publiceret=dict(trin4=udfald(res_a), v501=udfald(res_b)),
               reference_udfordrere_publiceret_erratum={k: {kk: v[kk] for kk in ("dLL", "dBrier", "n_parret", "folds_niveau_pct",
                                                                                 "alle_folds_positive", "persistens_pct",
                                                                                 "fortegn_stab_pct", "A1", "A2", "A3", "OPTAGET")}
                                                        for k, v in err4["kandidater"].items()})
    out["indholds_hash"] = indholds_hash(out)
    UDFIL.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"\nUDFALD: symmetrisk regel -> trin4 simultan {out['udfald_vs_publiceret']['trin4']['symmetrisk_simultan']}, "
          f"sekventiel {out['udfald_vs_publiceret']['trin4']['symmetrisk_sekventiel']}; "
          f"v501 simultan {out['udfald_vs_publiceret']['v501']['symmetrisk_simultan']}, "
          f"sekventiel {out['udfald_vs_publiceret']['v501']['symmetrisk_sekventiel']}")
    print(f"{UDFIL.relative_to(V5)} skrevet (indholds_hash {out['indholds_hash']}). Intet andet er roert.")


if __name__ == "__main__":
    main()
