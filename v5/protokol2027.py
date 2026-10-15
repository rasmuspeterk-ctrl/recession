#!/usr/bin/env python3
"""
protokol2027.py — RAADETS_2027's beslutninger, der traeder i kraft ved september-refitten 2027.

Hver regel har en forseglet spec i spec2027/, committet og pushet FOER koden her (RAADETS_2027 §12 trin 3).
SPECS laaser hver spec's sha256 (LF-normaliseret); kraev_forseglet() stopper hoejlydt, hvis en spec er aendret
efter forseglingen. Er spec og kode uenige, gaelder spec'en (§3.4).

Intet her aendrer P, baand eller vaegte foer refitten: reglerne gaelder kun for kalibreringer med refit-maaned
R >= IKRAFT (2027-09). En kalibrering med R < IKRAFT (fx reproduktionen af 72c3371d) koerer v5.0.1-reglerne.

  spec2027/1_gate.md   §2.1-2.3  ensidet benchmark-gate mod kritisk vaerdi -> obligatorisk dagsordenspunkt

Kun stdlib + numpy.
"""
import hashlib
from pathlib import Path
import numpy as np

import calibrate as C
import ablation2_nber as A2
import ablation3_frekvens as A3

HERE = Path(__file__).parent
SPEC_DIR = HERE / "spec2027"
IKRAFT = A2.midx(2027, 9)          # september-refitten 2027 (RAADETS_2027 §0)

# sha256 af de forseglede specs (LF-normaliserede bytes); en spec er forseglet, naar den er pushet foer koden
SPECS = {
    "1_gate.md": "127f46beb9212a3ede057f17c8fccdd364b1175f5e09f79b3d2c1a0cdcb4620c",
}

Z_975, Z_80 = 1.959964, 0.841621   # spec 1 §4.1: 80 %-MDE = (z_0,975 + z_0,80) x SD_block (normalteori)
STARTER = (("1953Q2", (1953, 2)), ("1960Q1", (1960, 1)))


def i_kraft(R):
    """Gaelder RAADETS_2027 for en kalibrering med refit-maaned R (midx)?"""
    return R is not None and R >= IKRAFT


def i_kraft_maaned(refit_maaned):
    """Som i_kraft, for en 'YYYY-MM'-streng (weights.json/manifest). None/tom -> False."""
    if not refit_maaned:
        return False
    return i_kraft(A2.midx(int(refit_maaned[:4]), int(refit_maaned[5:7])))


def spec_sha256(navn):
    """sha256 af en spec-fil med LF-linjeskift (core.autocrlf giver CRLF i Windows-arbejdskopier)."""
    return hashlib.sha256((SPEC_DIR / navn).read_bytes().replace(bytes([13, 10]), bytes([10]))).hexdigest()


def kraev_forseglet(navn):
    """Stop hoejlydt, hvis en forseglet spec mangler eller er aendret efter forseglingen. -> sha256."""
    f = SPEC_DIR / navn
    if not f.exists():
        raise SystemExit(f"FEJL (RAADETS_2027 §12): den forseglede spec spec2027/{navn} mangler.")
    h = spec_sha256(navn)
    if h != SPECS[navn]:
        raise SystemExit(f"FEJL (RAADETS_2027 §12): spec2027/{navn} er aendret efter forseglingen "
                         f"({h[:12]} != {SPECS[navn][:12]}). En aendring kraever en raadsbeslutning; gendan filen.")
    return h


# ------------------------------------------------------------------ spec 1: gaten (§2.3)
def _skill_diff(par):
    """Parret skill-forskel i pp (foerste minus anden model) med poolet basisrate — samme formel som
    ablation3.mde_bootstrap. par = [(p_a, p_b, y)]. None naar basisraten er 0 eller 1."""
    if not par:
        return None
    pa = np.clip(np.array([a for a, _, _ in par]), 1e-6, 1 - 1e-6)
    pb = np.clip(np.array([b for _, b, _ in par]), 1e-6, 1 - 1e-6)
    yy = np.array([y for _, _, y in par])
    b = yy.mean()
    if b in (0.0, 1.0):
        return None
    bl = -np.mean(yy * np.log(b) + (1 - yy) * np.log(1 - b))
    la = -np.mean(yy * np.log(pa) + (1 - yy) * np.log(1 - pa))
    lb = -np.mean(yy * np.log(pb) + (1 - yy) * np.log(1 - pb))
    return float(((1 - la / bl) - (1 - lb / bl)) * 100)


def parret(res5, resc):
    """Spec 1 §2: de to walk-forwards' scorede (origin, label)-lister skal vaere identiske — ellers stopper
    refitten (en uparret gate maa aldrig printes som parret). -> [(aar, kvt, p5, pc, y)]."""
    k5 = [(y, q, yy) for (y, q, _, yy) in res5]
    kc = [(y, q, yy) for (y, q, _, yy) in resc]
    if k5 != kc:
        kun5, kunc = sorted(set(k5) - set(kc)), sorted(set(kc) - set(k5))
        raise SystemExit("FEJL (RAADETS_2027 §2.3, spec 1 §2): F5 og curve-only har ikke identiske scorede "
                         f"(origin, label)-lister (kun F5: {kun5[:4]}, kun curve-only: {kunc[:4]}). Gaten er uparret — "
                         "refitten stopper.")
    return [(y, q, p5, pc, yy) for (y, q, p5, yy), (_, _, pc, _) in zip(res5, resc)]


def uden_blokke(par, eps):
    """Spec 1 §4.2: Delta uden hver episodeblok (samme P'er, ingen refit). -> (liste, stoerst bidragende)."""
    grp = {}
    for (y, q, p5, pc, yy) in par:
        grp.setdefault(A3.episode_group(y, eps), []).append((y, q, p5, pc, yy))
    delta = _skill_diff([(p5, pc, yy) for (_, _, p5, pc, yy) in par])
    rk = []
    for g in sorted(grp):
        rest = [(p5, pc, yy) for (y, q, p5, pc, yy) in par if A3.episode_group(y, eps) != g]
        d_k = _skill_diff(rest)
        o = grp[g]
        rk.append(dict(blok=int(g), onset=(f"{eps[g][0] // 12}-{eps[g][0] % 12 + 1:02d}" if g < len(eps) else "hale"),
                       foerste=f"{o[0][0]}Q{o[0][1]}", sidste=f"{o[-1][0]}Q{o[-1][1]}", n_origins=len(o),
                       delta_uden_pp=None if d_k is None else round(d_k, 2),
                       bidrag_pp=None if d_k is None else round(delta - d_k, 2), _bidrag=None if d_k is None else delta - d_k))
    kand = [r for r in rk if r["_bidrag"] is not None]
    top = max(kand, key=lambda r: (r["_bidrag"], -r["blok"])) if kand else None   # ved lighed: tidligste blok
    for r in rk:
        r.pop("_bidrag")
    return rk, top


def _sub(D, fra):
    """Raekkeuniverset fra og med kvartal `fra` (samme snit som diagnostik.start_sensitivitet)."""
    keep = [i for i, qk in enumerate(D["qk"]) if qk >= fra]
    return dict(F=D["F"][keep], feats=D["feats"], Y_tek=D["Y_tek"][keep], qk=[D["qk"][i] for i in keep],
                qend=D["qend"][keep], year=D["year"][keep])


def regel(delta, sd):
    """Spec 1 §3-4: ensidet regel paa de uafrundede tal. -> (dagsordenspunkt, kritisk vaerdi K, 80 %-MDE)."""
    K = 1.96 * sd
    return bool(delta > K), K, (Z_975 + Z_80) * sd


def gate(Dc, D5, eps, avail, usrec, R, resc, res5=None):
    """RAADETS_2027 §2.3 (spec 1): ensidet Delta = skill(F5) - skill(curve) mod K = 1,96 x SD_block ->
    obligatorisk dagsordenspunkt; 80 %-MDE, Delta uden stoerst bidragende blok og Delta ved 1953Q2/1960Q1 ved
    siden af. Laeser ikke ablation3_resultat.json (4,42 er ude). -> (gate-dict, res5)."""
    h = kraev_forseglet("1_gate.md")
    _, _, impc, brc = C.metrics(resc)
    g = dict(protokol="RAADETS_2027 §2.3", spec_sha256=h, identiske_origins=A2.samme_origins(Dc, D5),
             curve_only_wf=round(impc, 2), curve_only_brier=round(brc, 2))
    if not g["identiske_origins"]:
        g["note"] = ("comparison unavailable — fuldmodellens og curve-onlys origin-identiteter matcher ikke "
                     "(CAPE stale/manglende?). Curve-only koerer videre (RAADETS_V501 §2).")
        return g, []
    if res5 is None:
        res5, _, _ = A2.wf_nber(D5, eps, avail, usrec, A2.L_EMBARGO, R_score=R)
    _, _, imp5, br5 = C.metrics(res5)
    par = parret(res5, resc)
    delta, sd, _lo, _hi = A3.mde_bootstrap(par, eps)
    over, K, mde80 = regel(delta, sd)
    blokke, top = uden_blokke(par, eps)
    ved = {}
    for navn, st in STARTER:
        dc, d5 = _sub(Dc, st), _sub(D5, st)
        if not A2.samme_origins(dc, d5):
            ved[navn] = dict(note="comparison unavailable")
            continue
        rc, _, _ = A2.wf_nber(dc, eps, avail, usrec, A2.L_EMBARGO, R_score=R)
        r5, _, _ = A2.wf_nber(d5, eps, avail, usrec, A2.L_EMBARGO, R_score=R)
        if not rc:
            ved[navn] = dict(note="comparison unavailable — ingen scorede origins")
            continue
        p_ = parret(r5, rc)
        ved[navn] = dict(n_origins=len(p_), foerste=f"{p_[0][0]}Q{p_[0][1]}",
                         curve_only_wf=round(C.metrics(rc)[2], 2), fuldmodel_wf=round(C.metrics(r5)[2], 2),
                         delta_pp=round(_skill_diff([(a, b, y) for (_, _, a, b, y) in p_]), 2))
    g.update(n_origins=len(par), fuldmodel_wf=round(imp5, 2), fuldmodel_brier=round(br5, 2),
             delta_pp=round(delta, 2), sd_block_pp=round(sd, 2), kritisk_vaerdi_pp=round(K, 2),
             dagsordenspunkt=over, mde80_pp=round(mde80, 2),
             mde80_note="normalteori-approksimation (RAADETS_2027 §1.2)",
             uden_stoerste_blok=dict(blok=top, alle=blokke) if top else dict(blok=None, alle=blokke),
             ved_start=ved,
             note=(f"Delta {delta:+.2f}pp {'>' if over else '<='} kritisk vaerdi {K:.2f}pp (1,96 x SD_block {sd:.2f}pp): "
                   f"{'obligatorisk punkt paa raadets dagsorden' if over else 'intet dagsordenspunkt'}. Administrativ "
                   "reviewgraense, ikke en kalibreret signifikanstest; kaldes aldrig evidens og skifter intet "
                   "(RAADETS_2027 §2.3)."))
    return g, res5


def er_2027_gate(g):
    return bool(g) and str(g.get("protokol", "")).startswith("RAADETS_2027")


def fuldmodel_status(g):
    """Spec 1 §5: fuldmodellens statustekst under en 2027-gate."""
    if g.get("dagsordenspunkt"):
        return ("Delta over kritisk vaerdi: obligatorisk punkt paa raadets dagsorden (administrativ reviewgraense, "
                "ikke evidens); frossen benchmark, ikke operationel (RAADETS_2027 §2.1)")
    return "frossen benchmark (RAADETS_2027 §2.1); Delta under kritisk vaerdi — intet dagsordenspunkt"


def gate_linjer(g):
    """finalize6's printlinjer for en 2027-gate (spec 1 §5)."""
    if not g.get("identiske_origins"):
        return [f"gate (RAADETS_2027 §2.3): {g['note']}"]
    ud = [f"gate (RAADETS_2027 §2.3): curve-only +{g['curve_only_wf']:.2f}% / F5 +{g['fuldmodel_wf']:.2f}% paa "
          f"{g['n_origins']} faelles origins; {g['note']}",
          f"   80 %-MDE {g['mde80_pp']:.2f}pp ({g['mde80_note']})"]
    t = g["uden_stoerste_blok"]["blok"]
    if t:
        ud.append(f"   Delta uden stoerst bidragende blok (blok {t['blok']}, onset {t['onset']}, {t['foerste']}..{t['sidste']}, "
                  f"{t['n_origins']} origins): {t['delta_uden_pp']:+.2f}pp")
    for navn, v in g["ved_start"].items():
        ud.append(f"   Delta ved start {navn}: " + (f"{v['delta_pp']:+.2f}pp ({v['n_origins']} origins fra {v['foerste']})"
                                                   if "delta_pp" in v else v["note"]))
    if g.get("dagsordenspunkt"):
        ud.append("DAGSORDENSPUNKT (RAADETS_2027 §2.3): F5 slaar curve-only med mere end den kritiske vaerdi — "
                  "obligatorisk punkt paa raadets dagsorden. Intet skiftes; refitten fortsaetter.")
    return ud
