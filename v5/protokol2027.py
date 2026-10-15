#!/usr/bin/env python3
"""
protokol2027.py — RAADETS_2027's beslutninger, der traeder i kraft ved september-refitten 2027.

Hver regel har en forseglet spec i spec2027/, committet og pushet FOER koden her (RAADETS_2027 §12 trin 3).
SPECS laaser hver spec's sha256 (LF-normaliseret); kraev_forseglet() stopper hoejlydt, hvis en spec er aendret
efter forseglingen. Er spec og kode uenige, gaelder spec'en (§3.4).

Intet her aendrer P, baand eller vaegte foer refitten: reglerne gaelder kun for kalibreringer med refit-maaned
R >= IKRAFT (2027-09). En kalibrering med R < IKRAFT (fx reproduktionen af 72c3371d) koerer v5.0.1-reglerne.

  spec2027/1_gate.md        §2.1-2.3  ensidet benchmark-gate mod kritisk vaerdi -> obligatorisk dagsordenspunkt
  spec2027/2_L_R_audit.md   §9        L_R = max(18, top-lag, bund-lag - 12); eligibility med info ved R; stop ved brud
  spec2027/3_indholdstrigger_replay.md
                            §6        een refit pr. ny onset + enhver omlabeling; replayen ligger i replay2027.py
  spec2027/4_maanedligt_fit_uscorede.md
                            §3.3/§4/§10.4  maanedligt fit (lambda_m = N_m/N_q), parret diagnostik, uscorede felter

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
    "2_L_R_audit.md": "017f1f3152b32e367e4f67d77be696bf5944a93691ca37dd8462bebb66c0a2e3",
    "3_indholdstrigger_replay.md": "c63471d399768e81b57c39c3c5dc8ea458a2105dfe8456c12caa747f4d76ed3f",
    "4_maanedligt_fit_uscorede.md": "c2c988c97b4c5f516b31fb2d8ebf4d8deccc09f21ab7de9ef5666fa428fa0e33",
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


# ------------------------------------------------------------------ spec 2: L_R-audit og eligibility (§9)
INF = 10 ** 9


def _md(tekst):
    """'YYYY-MM[-DD]' -> midx (maanedsgranularitet, som ablation2_nber.load_announcements)."""
    return A2.midx(int(tekst[:4]), int(tekst[5:7]))


def L_R_formel(rows, L=A2.L_EMBARGO):
    """Spec 2 §2-3: L_R = max(18, max lag_peak, max lag_trough - 12) fra tabellens raekker, og de to uligheder mod
    den operationelle embargo L. Top-leddet og bund-leddet rapporteres hver for sig."""
    lag = lambda r: _md(r["announcement_date"]) - _md(r["cycle_month"])
    top = max(((lag(r), r["event"]) for r in rows if r["event"].startswith("peak")), default=(0, "-"))
    bund = max(((lag(r), r["event"]) for r in rows if r["event"].startswith("trough")), default=(0, "-"))
    return dict(L_embargo=L, L_R=max(18, top[0], bund[0] - 12),
                top_led=dict(max_lag=top[0], raekke=top[1], graense=L, ok=top[0] <= L),
                bund_led=dict(max_lag=bund[0], max_lag_minus_12=bund[0] - 12, raekke=bund[1], graense=L,
                              ok=bund[0] - 12 <= L))


def episode_info(eps, rows, avail, usrec):
    """Spec 2 §4: [(O, T, aP, aT)] pr. USREC-episode. aP = maaneden toppen er kendt (avail; pre-1979 T + 18),
    aT = maaneden bunden er kendt (trough-raekke +/- 2 mdr; pre-1979 T + 18; aaben episode/ingen raekke: aldrig)."""
    aaben = A2.aaben_episode(usrec) if usrec else None
    bunde = [(_md(r["cycle_month"]), _md(r["announcement_date"])) for r in rows if r["event"].startswith("trough")]
    info = []
    for O, T in eps:
        aP = avail.get(O, INF)
        if O == aaben:
            aT = INF
        elif O < A2.POST1979:
            aT = T + A2.PRE1979_TROUGH_LAG
        else:
            hit = [a for t, a in bunde if abs(t - T) <= 2]
            aT = min(hit) if hit else INF
        info.append((O, T, aP, aT))
    return info


def censur_status(q, R, info):
    """Spec 2 §4: origin-maaned q's censurstatus med KUN den information, der er tilgaengelig ved R:
    'censureret' (inde i en episode med kendt bund), 'aaben' (inde i en aaben episode — motorens
    aabne-episode-regel; ikke afgjort) eller 'fri'. T bruges kun, naar bunden er kendt ved R."""
    for O, T, aP, aT in info:
        if aP > R or q < O:
            continue
        if aT <= R:
            if q <= T:
                return "censureret"
        else:
            return "aaben"
    return "fri"


def eligible_2027(D, info, avail, win_onsets, R, L_R):
    """Spec 2 §5 (§9.2): eligible iff qend + 12 + L_R <= R OG censur_status == 'fri'. -> (maske, labels ved R)."""
    n = len(D["qend"])
    elig, yR = np.zeros(n, bool), np.zeros(n)
    for j in range(n):
        q = int(D["qend"][j])
        if q + 12 + L_R > R or censur_status(q, R, info) != "fri":
            continue
        elig[j] = True
        yR[j] = 1.0 if any(avail[o] <= R for o in win_onsets[j]) else 0.0
    return elig, yR


def L_R_audit(D, eps, avail, usrec, R, rows, L=A2.L_EMBARGO):
    """Spec 2 §6: (1) ulighederne, (2) eligible_fit == eligible_2027 for hver maaned 1979-01..R, (3) finalitet: et
    origin, der er modent ved R', har samme (eligibility, label) ved R' som ved R. Returnerer audit-dict; stoppet
    sker i stop_ved_brud (finalize6 printer foerst)."""
    h = kraev_forseglet("2_L_R_audit.md")
    a = dict(protokol="RAADETS_2027 §9", spec_sha256=h, **L_R_formel(rows, L))
    a["interval"] = [f"{A2.POST1979 // 12}-{A2.POST1979 % 12 + 1:02d}", f"{R // 12}-{R % 12 + 1:02d}"]
    if not (a["top_led"]["ok"] and a["bund_led"]["ok"]):
        a.update(konflikter=dict(n=None), finalitetsbrud=dict(n=None), ok=False)
        return a
    info = episode_info(eps, rows, avail, usrec)
    _, win, _ = A2.nber_labels(D, eps, usrec)
    qk = lambda j: f"{D['qk'][j][0]}Q{D['qk'][j][1]}"
    eR, yR = eligible_2027(D, info, avail, win, R, a["L_R"])
    konf, brud = [], []
    for Rp in range(A2.POST1979, R + 1):
        e1, _ = A2.eligible_fit(D, eps, avail, usrec, Rp, L=L)
        e2, y2 = eligible_2027(D, info, avail, win, Rp, a["L_R"])
        mp = f"{Rp // 12}-{Rp % 12 + 1:02d}"
        for j in np.where(e1 != e2)[0]:
            konf.append(f"{qk(j)} ved {mp}: eligible_fit {bool(e1[j])}, §9.2 {bool(e2[j])} "
                        f"(status {censur_status(int(D['qend'][j]), Rp, info)})")
        moden = D["qend"] + 12 + a["L_R"] <= Rp
        for j in np.where(moden)[0]:
            if (bool(e2[j]), y2[j] if e2[j] else None) != (bool(eR[j]), yR[j] if eR[j] else None):
                brud.append(f"{qk(j)}: ved {mp} (eligible {bool(e2[j])}, label {int(y2[j])}) != ved refit "
                            f"(eligible {bool(eR[j])}, label {int(yR[j])})")
    a.update(konflikter=dict(n=len(konf), foerste=konf[:10]), finalitetsbrud=dict(n=len(brud), foerste=brud[:10]),
             n_origins=len(D["qend"]), ok=not konf and not brud)
    return a


def L_R_linjer(a):
    t, b = a["top_led"], a["bund_led"]
    ud = [f"L_R-audit (RAADETS_2027 §9): L_R = max(18, {t['max_lag']}, {b['max_lag']} - 12) = {a['L_R']} | top-leddet: "
          f"max lag_peak {t['max_lag']} ({t['raekke']}) <= {t['graense']}: {'OK' if t['ok'] else 'BRUDT'} | bund-leddet: "
          f"max lag_trough {b['max_lag']} ({b['raekke']}) - 12 = {b['max_lag_minus_12']} <= {b['graense']}: "
          f"{'OK' if b['ok'] else 'BRUDT'}"]
    if a["konflikter"]["n"] is not None:
        ud.append(f"   eligible_fit mod §9.2-eligibility {a['interval'][0]}..{a['interval'][1]}: {a['konflikter']['n']} konflikter; "
                  f"finalitet: {a['finalitetsbrud']['n']} brud")
        for x in a["konflikter"]["foerste"] + a["finalitetsbrud"]["foerste"]:
            ud.append(f"   - {x}")
    return ud


def stop_ved_brud(a):
    """Spec 2 §3/§6: brud -> refitten stopper (intet skrevet) indtil raadet har taget stilling. Et brud paa top-
    leddet stopper alene."""
    grunde = []
    if not a["top_led"]["ok"]:
        grunde.append(f"top-leddet er brudt (max lag_peak {a['top_led']['max_lag']} > {a['top_led']['graense']}, "
                      f"{a['top_led']['raekke']}) — stopper refitten alene (DeepSeek)")
    if not a["bund_led"]["ok"]:
        grunde.append(f"bund-leddet er brudt (max lag_trough - 12 = {a['bund_led']['max_lag_minus_12']} > "
                      f"{a['bund_led']['graense']}, {a['bund_led']['raekke']})")
    if a["konflikter"]["n"]:
        grunde.append(f"{a['konflikter']['n']} konflikter mellem eligible_fit og §9.2 (spec og kode uenige, §3.4)")
    if a["finalitetsbrud"]["n"]:
        grunde.append(f"{a['finalitetsbrud']['n']} modne origins er redigeret efter modning")
    if grunde:
        raise SystemExit("FEJL (RAADETS_2027 §9.3): L_R-auditten er brudt — " + "; ".join(grunde)
                         + ". Refitten stopper; intet er skrevet. Raadet skal tage stilling.")


# ------------------------------------------------------------------ spec 3: indholdstriggeren (§6.1)
def ym(i):
    return f"{i // 12}-{i % 12 + 1:02d}"


def manifest_onsets(origins, eps, avail, R_M):
    """Spec 3 §2: onsets med mindst eet positivt origin i manifestet (origins = [[aar, kvt, label]], refit R_M)."""
    ud = set()
    for y, q, l in origins:
        if int(l) != 1:
            continue
        qe = A2.qend_idx(int(y), int(q))
        ud |= {o for o, _ in eps if qe + 1 <= o <= qe + 12 and avail.get(o, INF) <= R_M}
    return ud


def indholdstrigger(D, eps, avail, usrec, R, origins, R_M):
    """Spec 3 §2 (§6.1): udloest ved R mod manifestet (origins, R_M) i drift? Een gang pr. ny onset (et berettiget
    positivt label for en onset, manifestet ikke har) + enhver omlabeling; aldrig nymodnede negative. Triggeren
    aendrer intet ved fittet. -> dict(udloest, nye_onsets {onset: [origins]}, omlabelinger [..])."""
    elig, yR = A2.eligible_fit(D, eps, avail, usrec, R)
    _, win, _ = A2.nber_labels(D, eps, usrec)
    kendt = manifest_onsets(origins, eps, avail, R_M)
    man = {(int(y), int(q)): int(l) for y, q, l in origins}
    nye, omlab = {}, []
    for j in np.where(elig)[0]:
        k = (int(D["qk"][j][0]), int(D["qk"][j][1]))
        if yR[j] == 1:
            for o in win[j]:
                if avail[o] <= R and o not in kendt:
                    nye.setdefault(ym(o), []).append(f"{k[0]}Q{k[1]}")
        if k in man and man[k] != int(yR[j]):
            omlab.append(f"{k[0]}Q{k[1]} {man[k]}->{int(yR[j])}")
    return dict(udloest=bool(nye or omlab), nye_onsets=nye, omlabelinger=omlab)


def foerste_trigger(D, eps, avail, usrec, R, origins, R_M):
    """Spec 3 §2: den foerste maaned R' i (R_M, R] hvor indholdstriggeren er udloest -> manifestets felt, eller None."""
    h = kraev_forseglet("3_indholdstrigger_replay.md")
    for Rp in range(R_M + 1, R + 1):
        t = indholdstrigger(D, eps, avail, usrec, Rp, origins, R_M)
        if t["udloest"]:
            return dict(protokol="RAADETS_2027 §6", spec_sha256=h, trigger_maaned=ym(Rp), evalueret_ved=ym(R),
                        nye_onsets=t["nye_onsets"], omlabelinger=t["omlabelinger"])
    return None


def trigger_tekst(it):
    """Den korte begrundelse i manifestets/weights.json's trigger-tekst."""
    dele = [f"ny onset {o} ({', '.join(v)})" for o, v in sorted(it["nye_onsets"].items())] + \
           [f"omlabeling {x}" for x in it["omlabelinger"]]
    return f"nber-indhold (RAADETS_2027 §6): trigger-maaned {it['trigger_maaned']}; " + "; ".join(dele)


# ------------------------------------------------------------------ spec 4: maanedligt fit og uscorede felter
MIN_TR_M, MIN_POS_M = 180, 18       # ablation3.wf_monthly: 60 kvartaler / 6 positive i maaneder
STARTFELTER = (("start_1953Q2", (1953, 2)), ("start_1960Q1", (1960, 1)))


def maanedligt_univers(snap, Dq):
    """Spec 4 §2: maaneder med defineret kurve, hvis kvartal ligger i det kvartalsvise curve-only-univers Dq
    (= analyser/frekvensgate.byg_maanedligt(snap, Dq, ['curve']), inkl. rygrad-forlaengelsen)."""
    shiller = C.read_shiller(snap)
    gs10, tb3ms = C.read_fred(snap, "GS10"), C.read_fred(snap, "TB3MS")
    sidst = shiller[-1][0] if shiller else (0, 0)
    shiller = shiller + [(k, np.nan, np.nan, np.nan, np.nan) for k in sorted(set(gs10) & set(tb3ms)) if k > sidst]
    keys, M = C.build_monthly(shiller, gs10, tb3ms)
    F = M["curve"].reshape(-1, 1)
    ok_q = set(Dq["qk"])
    rk = [i for i, (y, m) in enumerate(keys) if not np.isnan(F[i, 0]) and (y, (m - 1) // 3 + 1) in ok_q]
    return dict(F=F[rk], feats=["curve"], midx=np.array([A2.midx(*keys[i]) for i in rk]), ym=[keys[i] for i in rk])


def _labels_m(Dm, eps, usrec):
    win, Y, inr, epo = [], np.zeros(len(Dm["midx"])), np.zeros(len(Dm["midx"]), bool), []
    for j, m in enumerate(Dm["midx"]):
        wo = [o for o, _ in eps if m + 1 <= o <= m + 12]
        win.append(wo)
        Y[j] = 1.0 if wo else 0.0
        inr[j] = usrec.get(int(m), 0) == 1
        e = A2.episode_of(int(m), eps)
        epo.append(e[0] if e else None)
    return win, Y, inr, epo


def eligible_maanedlig(Dm, eps, avail, R, lab):
    """Spec 4 §2: berettigede maanedsraekker ved R (m + 12 + 18 <= R, ikke i en recession annonceret senest R)."""
    win, _Y, _inr, epo = lab
    n = len(Dm["midx"])
    elig, yR = np.zeros(n, bool), np.zeros(n)
    for j in range(n):
        if Dm["midx"][j] + 12 + A2.L_EMBARGO > R or (epo[j] is not None and avail[epo[j]] <= R):
            continue
        elig[j] = True
        yR[j] = 1.0 if any(avail[o] <= R for o in win[j]) else 0.0
    return elig, yR


def lambda_m(N_m, N_q, lambda_q=1.0):
    """Spec 4 §2 (fastlaast): samme straf pr. observation under summeret tab -> lambda_m = lambda_q * N_m / N_q."""
    if N_q <= 0:
        raise SystemExit("FEJL (RAADETS_2027 §3.3, spec 4 §2): N_q = 0 — lambda_m er udefineret.")
    return lambda_q * N_m / N_q


def maanedligt_fit(snap, Dq, eps, avail, usrec, R):
    """Spec 4 §2: det maanedlige curve-only-fit ved refit-maaned R med lambda_m = N_m(R)/N_q(R)."""
    Dm = maanedligt_univers(snap, Dq)
    elig, yR = eligible_maanedlig(Dm, eps, avail, R, _labels_m(Dm, eps, usrec))
    N_q = int(A2.eligible_fit(Dq, eps, avail, usrec, R)[0].sum())
    X, y = Dm["F"][elig], yR[elig]
    mu, sd = X.mean(0), X.std(0, ddof=1)
    sd[sd == 0] = 1
    lam = lambda_m(int(elig.sum()), N_q)
    w = C.fit((X - mu) / sd, y, l2=lam)
    sidste = Dm["ym"][int(np.where(elig)[0][-1])]
    return dict(features=["curve"], mu={"curve": round(float(mu[0]), 4)}, sd={"curve": round(float(sd[0]), 4)},
                w=[round(float(v), 4) for v in w], l2=round(lam, 6), N_m=int(elig.sum()), N_q=N_q, n_pos=int(y.sum()),
                base_rate=round(float(y.mean()), 4), estimering_slut=f"{sidste[0]}-{sidste[1]:02d}")


def start_fits(Dq, eps, avail, usrec, R):
    """Spec 4 §5: curve-only paa universet afkortet til >= 1953Q2 og >= 1960Q1 (som diagnostik.start_sensitivitet)."""
    import finalize6 as F6                       # sen import: finalize6 importerer protokol2027
    ud = {}
    for navn, st in STARTFELTER:
        m = F6.fit_model(_sub(Dq, st), eps, avail, usrec, R)
        ud[navn] = {k: m[k] for k in ("features", "mu", "sd", "w", "n_obs", "base_rate")}
    return ud


def uscorede(snap, Dq, eps, avail, usrec, R):
    """Spec 4 §2/§5: manifestets og weights.json's 'uscorede'-blok for en refit med R >= 2027-09."""
    h = kraev_forseglet("4_maanedligt_fit_uscorede.md")
    return dict(protokol="RAADETS_2027 §3.3/§4/§10.4", spec_sha256=h,
                note="uscorede felter: indgaar aldrig i P, baand, dom, gate, trigger eller noeglens score",
                maanedligt_fit=maanedligt_fit(snap, Dq, eps, avail, usrec, R) | dict(spec_sha256=h),
                **start_fits(Dq, eps, avail, usrec, R))


def _p(model, c):
    z = (c - model["mu"]["curve"]) / model["sd"]["curve"]
    return float(1 / (1 + np.exp(-np.clip(model["w"][0] + model["w"][1] * z, -30, 30))))


def p_uscorede(us, curve):
    """Spec 4 §3/§5: de uscorede P'er ved raekkens live-input."""
    return dict(p_maanedligt_fit=_p(us["maanedligt_fit"], curve),
                p_start_1953Q2=_p(us["start_1953Q2"], curve), p_start_1960Q1=_p(us["start_1960Q1"], curve))


def wf_maanedlig(Dm, Dq, eps, avail, usrec, R_score, variant):
    """Spec 4 §4: purget expanding-origin walk-forward paa maanedsraekker (ablation3.wf_monthly /
    frekvensgate.wf_maanedlig) med straffen `variant`: 'A' = lambda_m(R) = N_m(R)/N_q(R) i hvert vindue, 'B' = 1."""
    lab = _labels_m(Dm, eps, usrec)
    win, Y, inr, epo = lab
    out, lams = [], []
    for i in range(len(Dm["midx"])):
        if Dm["ym"][i][0] < 1960 or Dm["midx"][i] + 12 + A2.L_EMBARGO > R_score:
            continue
        R = int(Dm["midx"][i])
        tr = [j for j in range(i) if Dm["midx"][j] + 12 + A2.L_EMBARGO <= R and not (epo[j] is not None and avail[epo[j]] <= R)]
        if len(tr) < MIN_TR_M:
            continue
        yR = np.array([1.0 if any(avail[o] <= R for o in win[j]) else 0.0 for j in tr])
        if yR.sum() < MIN_POS_M:
            continue
        lam = 1.0 if variant == "B" else lambda_m(len(tr), int(A2.eligible_fit(Dq, eps, avail, usrec, R)[0].sum()))
        X = Dm["F"][tr]
        mu, sd = X.mean(0), X.std(0, ddof=1)
        sd[sd == 0] = 1
        w = C.fit((X - mu) / sd, yR, l2=lam)
        if inr[i]:
            continue
        y, m = Dm["ym"][i]
        out.append((int(y), int(m), float(C.predict(w, (Dm["F"][[i]] - mu) / sd)[0]), float(Y[i])))
        lams.append(lam)
    return out, lams


def identiteter(tyndet, kvartal):
    """Spec 4 §4 (Fable): origin-maengde, labels og poolet basisrate skal vaere identiske — fejler hoejlydt."""
    kt = {(y, q): yy for (y, q, _, yy) in tyndet}
    kq = {(y, q): yy for (y, q, _, yy) in kvartal}
    fejl = []
    if set(kt) != set(kq):
        fejl.append(f"origin-maengderne er forskellige (kun maanedlig: {sorted(set(kt) - set(kq))[:4]}, "
                    f"kun kvartal: {sorted(set(kq) - set(kt))[:4]})")
    uenige = sorted(k for k in set(kt) & set(kq) if kt[k] != kq[k])
    if uenige:
        fejl.append(f"{len(uenige)} uenige labels ({uenige[:4]})")
    bt = float(np.mean(list(kt.values()))) if kt else None
    bq = float(np.mean(list(kq.values()))) if kq else None
    if bt != bq:
        fejl.append(f"poolet basisrate {bt} != {bq}")
    if fejl:
        raise SystemExit("FEJL (RAADETS_2027 §3.3, spec 4 §4): den parrede samme-origins-diagnostik er ikke parret — "
                         + "; ".join(fejl) + ". Intet skrevet; forelaegges raadet.")
    return len(kt), bq


def maanedlig_parret(snap, eps, avail, usrec, R):
    """Spec 4 §4: §3.2(b)-diagnostikken paa refittens panel i to straf-varianter (A primaer, B kontinuitet)."""
    h = kraev_forseglet("4_maanedligt_fit_uscorede.md")
    Dq = A2.build_dataset(snap, ["curve"])
    Dm = maanedligt_univers(snap, Dq)
    kv, _, _ = A2.wf_nber(Dq, eps, avail, usrec, A2.L_EMBARGO, R_score=R)
    q_by = {(y, q): (p, yy) for (y, q, p, yy) in kv}
    ud = dict(protokol="RAADETS_2027 §3.3 (genkoersel af §3.2(b))", spec_sha256=h, R_score=ym(R),
              kvartal=dict(n=len(kv), improvement=round(C.metrics(kv)[2], 2)), varianter={},
              sprog=("Beskrivende diagnostik; aendrer intet. |Delta| under den kritiske vaerdi er fortegns-uinformativt — "
                     "et negativt Delta betyder ikke, at maanedlig er daarligere (Fable)."))
    for v, navn in (("A", "lambda_m = N_m/N_q (forseglet normalisering, primaer)"), ("B", "lambda = 1 (kontinuitet med §3.2(b))")):
        rows, lams = wf_maanedlig(Dm, Dq, eps, avail, usrec, R, v)
        tyndet = [(y, m // 3, p, yy) for (y, m, p, yy) in rows if m % 3 == 0]
        n, base = identiteter(tyndet, kv)
        par = [(y, q, p, q_by[(y, q)][0], yy) for (y, q, p, yy) in tyndet]
        d, sd, lo, hi = A3.mde_bootstrap(par, eps)
        ud["varianter"][v] = dict(navn=navn, n_parrede_origins=n, labels_uenige=0, basisrate=round(base, 4),
                                  maanedlig_tyndet_improvement=round(C.metrics(tyndet)[2], 2),
                                  maanedlig_fuld=dict(n=len(rows), improvement=round(C.metrics(rows)[2], 2)),
                                  forskel_pp=round(float(d), 2), sd_pp=round(sd, 2), ci10=round(lo, 2), ci90=round(hi, 2),
                                  kritisk_vaerdi_pp=round(1.96 * sd, 2),
                                  lambda_spaend=[round(min(lams), 3), round(max(lams), 3)] if lams else None)
    return ud


def parret_linjer(d):
    ud = [f"   §3.3 Maanedlig parret diagnostik ({d['R_score']}; uscoret): kvartal +{d['kvartal']['improvement']}% paa {d['kvartal']['n']} origins"]
    for v, x in d["varianter"].items():
        ud.append(f"       {v} {x['navn']}: tyndet maanedlig +{x['maanedlig_tyndet_improvement']}% paa {x['n_parrede_origins']} "
                  f"identiske origins (0 uenige labels, basisrate {x['basisrate']:.4f}); Delta {x['forskel_pp']:+.2f}pp "
                  f"[{x['ci10']:+.2f}, {x['ci90']:+.2f}], kritisk vaerdi {x['kritisk_vaerdi_pp']:.2f}pp")
    ud.append(f"       {d['sprog']}")
    return ud


# ------------------------------------------------------------------ spec 4 §6: UDFALD.csv (censurerede maaneder)
UDFALD_KOLONNER = ["raekke_logget", "Y", "afgjort_dato", "kilde", "note", "uscoret_censureret"]


def udfald_tjek(log_rows, udfald_rows, kolonner):
    """Spec 4 §6: hver UDFALD-raekke henviser til en logget LOG-raekke, Y i {0,1}, og uscoret_censureret = 'ja' hvis
    og kun hvis LOG-raekkens dom er 'censureret'. -> liste af fejl (tom = konsistent)."""
    fejl = []
    if list(kolonner) != UDFALD_KOLONNER:
        fejl.append(f"UDFALD.csv's kolonner er {list(kolonner)}, forventet {UDFALD_KOLONNER}")
    dom = {r["logget"][:10]: r.get("dom", "") for r in log_rows if r.get("P") not in (None, "", "–")}
    for r in udfald_rows:
        k = (r.get("raekke_logget") or "").strip()
        if k not in dom:
            fejl.append(f"{k}: ingen logget raekke i LOG.md")
            continue
        if (r.get("Y") or "").strip() not in ("0", "1"):
            fejl.append(f"{k}: Y = {r.get('Y')!r} (skal vaere 0 eller 1)")
        forv = "ja" if dom[k] == "censureret" else "nej"
        if (r.get("uscoret_censureret") or "").strip() != forv:
            fejl.append(f"{k}: uscoret_censureret = {r.get('uscoret_censureret')!r}, forventet {forv!r} (dom {dom[k]!r})")
    return fejl
