#!/usr/bin/env python3
"""
finalize6.py — trin 6: baand + benchmarks + FALLBACK-AFGOERELSE ind i weights.json.

BLUEPRINT-KRAVET (Section 8) BED: paa NBER-onset-labelen slaar curve-only
(+34,3% wf log-loss) fuldmodellen (+33,2%). Den forhaandsforpligtede fallback
(Kimi R5 / Sol R6, nedskrevet i RAADETS_KONSENSUS foer nogen test var koert)
eksekveres derfor mekanisk:
  - OPERATIONEL v5.0-model = curve-only NBER-onset-LOGIT (NY Fed-stil-benchmark; samme L2-logit-motor som alt andet)
  - Fuldmodellen (5 features) printes ved siden af, maerket
    "testet, ikke bestaaet mod benchmark" — med noten at forskellen (1,1pp)
    ligger under stoejgulvet (~4pp MDE fra trin 3) og at Brier gaar modsat
    (33,6 vs 32,8). Gaten er mekanisk; kontekst printes, dommen aendres ikke.
  - Baandet (episode-blok-bootstrap, seed 42) beregnes for den operationelle model.

Kun stdlib + numpy.  Koer:  python finalize6.py
"""
import json, sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

import calibrate as C
import ablation2_nber as A2

HERE = Path(__file__).parent
PROTOCOL = "5.0-final"
SEED = 42
NDRAW = 1000

# Permanente benchmark-linjer (v5.1/v5.2) bygges fra de committede resultatfiler, IKKE fra den
# gamle weights.json: `ablation2 --promote` overskriver den foer finalize6 koerer, saa linjerne
# gik lydloest tabt ved hvert maanedsritual (fundet ved kode-review 2026-09-08).
PERMANENTE = [
    # weights-noegle, resultatfil,           resultat-noegle, bestaaet-flag, status hvis ikke bestaaet
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
                          status=status, kilde=f"{fname} (snapshot {r.get('snapshot', '?')})")
    return lines

def vaerste_fejlalarm(res):
    """Hoejeste wf-sandsynlighed blandt scorede origins UDEN onset i vinduet: beregnet, ikke haandkopieret."""
    y, q, p, _ = max((r for r in res if r[3] == 0.0), key=lambda r: r[2])
    return dict(p=round(p, 4), origin=f"{y}Q{q}")

def boot_weights(Z, y, qend_fit, eps, ndraw):
    rng = np.random.default_rng(SEED)
    grp = np.array([next((k for k, (o, _) in enumerate(eps) if o >= qe), len(eps))
                    for qe in qend_fit])
    gkeys = np.unique(grp)
    W = []
    while len(W) < ndraw:
        rows = np.concatenate([np.where(grp == g)[0]
                               for g in rng.choice(gkeys, size=len(gkeys), replace=True)])
        yb = y[rows]
        if yb.sum() < 5 or yb.sum() > len(yb) - 5:
            continue
        W.append(np.round(C.fit(Z[rows], yb), 4).tolist())
    return W, len(gkeys)

def main():
    snap = C.find_snapshot(sys.argv)
    meta = json.loads((snap / "meta.json").read_text(encoding="utf-8"))
    print(f"=== finalize6 — {PROTOCOL} — snapshot {snap.name} ===")

    usrec = A2.load_usrec(snap)
    eps = A2.episodes_from_usrec(usrec)
    avail = A2.load_announcements(eps)
    D = A2.build_dataset(snap)
    Y, win_onsets, in_rec = A2.nber_labels(D, eps, usrec)
    n_onsets = len({o for wo in win_onsets for o in wo})   # onsets i mindst eet samplevindue (foer: haardkodet 12)
    fitm = ~in_rec
    X5, y = D["F"][fitm], Y[fitm]

    # walk-forward-skill: fuldmodel og curve-only paa identiske origins
    res5, _, _ = A2.wf_nber(D, eps, avail, usrec, A2.L_EMBARGO)
    _, _, imp5, br5 = C.metrics(res5)
    Dc = dict(F=D["F"][:, [0]], qend=D["qend"], year=D["year"], qk=D["qk"])
    resc, _, _ = A2.wf_nber(Dc, eps, avail, usrec, A2.L_EMBARGO)
    _, _, impc, brc = C.metrics(resc)
    print(f"fuldmodel: +{imp5:.1f}%/+{br5:.1f}%   curve-only: +{impc:.1f}%/+{brc:.1f}%")
    fa5, fac = vaerste_fejlalarm(res5), vaerste_fejlalarm(resc)
    print(f"vaerste fejlalarm i wf: fuldmodel {fa5['p']*100:.1f}% ({fa5['origin']}), "
          f"curve-only {fac['p']*100:.1f}% ({fac['origin']})")

    full_beats = imp5 > 0 and imp5 > impc
    operational = "fuldmodel" if full_beats else "curve_only"
    print(f"Section 8-krav: fuldmodel {'slaar' if full_beats else 'SLAAR IKKE'} curve-only "
          f"-> operationel model = {operational} (forhaandsforpligtet fallback)")

    # En one-shot-promotion (fx ablation7 --promote -> operationel="curve_cape") maa ikke
    # reverteres af maanedsgenbygget: den bevares indtil det promoverende script koeres igen.
    prev_w = {}
    if (HERE / "weights.json").exists():
        try:
            prev_w = json.loads((HERE / "weights.json").read_text(encoding="utf-8"))
        except ValueError:
            prev_w = {}
    promoveret = (prev_w.get("operationel")
                  if prev_w.get("operationel") not in (None, "curve_only", "fuldmodel") else None)

    # fuldmodel-fit (til ved-siden-af-linjen)
    mu5, sd5 = X5.mean(0), X5.std(0, ddof=1); sd5[sd5 == 0] = 1
    w5 = C.fit((X5 - mu5) / sd5, y)
    # curve-only-fit (operationel)
    Xc = X5[:, [0]]
    muc, sdc = Xc.mean(0), Xc.std(0, ddof=1); sdc[sdc == 0] = 1
    Zc = (Xc - muc) / sdc
    wc = C.fit(Zc, y)

    if promoveret:
        operational, op, band = promoveret, prev_w["op"], prev_w["band"]
        print(f"BEVARET: promoveret operationel model '{promoveret}' (weights fra "
              f"{prev_w.get('created_utc', '?')[:10]}) roeres ikke af maanedsgenbygget — "
              "genkoer det promoverende ablation-script for at opdatere den.")
    else:
        if operational == "curve_only":
            W, ngrp = boot_weights(Zc, y, D["qend"][fitm], eps, NDRAW)
            op = dict(features=["curve"], mu={"curve": round(float(muc[0]), 4)},
                      sd={"curve": round(float(sdc[0]), 4)},
                      w=[round(float(v), 4) for v in wc],
                      wf_improvement=round(impc, 2), wf_brier=round(brc, 2),
                      vaerste_fejlalarm=fac)
        else:
            Z5 = (X5 - mu5) / sd5
            W, ngrp = boot_weights(Z5, y, D["qend"][fitm], eps, NDRAW)
            op = dict(features=C.F5,
                      mu={f: round(float(m), 4) for f, m in zip(C.F5, mu5)},
                      sd={f: round(float(s), 4) for f, s in zip(C.F5, sd5)},
                      w=[round(float(v), 4) for v in w5],
                      wf_improvement=round(imp5, 2), wf_brier=round(br5, 2),
                      vaerste_fejlalarm=fa5)
        band = dict(metode="episode-blok-bootstrap af vaegte, fast standardisering",
                    fodnote="Not a predictive interval; reflects weight sensitivity to episode composition",
                    seed=SEED, n_draws=len(W), W=W)
        print(f"bootstrap: {len(W)} traek (seed {SEED}, {ngrp} episodeblokke) for {operational}")

    # fuldmodel-noten beregnes (foer: haandskrevne tal). Stoejgulv = trin 3's MDE fra resultatfilen.
    f3 = HERE / "ablation3_resultat.json"
    mde3 = json.loads(f3.read_text(encoding="utf-8")).get("mde_pp") if f3.exists() else None
    gap = abs(imp5 - impc)
    gulv = (f"{'<' if gap < mde3 else '>='} stoejgulv {mde3:.1f}pp (trin 3-MDE)" if mde3 is not None
            else "(stoejgulv ukendt: ablation3_resultat.json mangler)")
    brier_retning = "modsat" if (br5 > brc) != (imp5 > impc) else "samme vej"
    note = f"LL-forskel {gap:.1f}pp {gulv}; Brier gaar {brier_retning}. Gaten er mekanisk."

    out = dict(protocol_version=PROTOCOL,
               created_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
               snapshot=snap.name, snapshot_sha256=meta["snapshot_sha256"],
               label="nber-onset", label_tekst="NBER-onset inden 4 kvartaler",
               frekvens="kvartal",
               n_obs=int(fitm.sum()), n_episoder=n_onsets,
               base_rate=round(float(y.mean()), 4),
               operationel=operational,
               op=op,
               band=band,
               fuldmodel=dict(features=C.F5,
                              mu={f: round(float(m), 4) for f, m in zip(C.F5, mu5)},
                              sd={f: round(float(s), 4) for f, s in zip(C.F5, sd5)},
                              w=[round(float(v), 4) for v in w5],
                              wf_improvement=round(imp5, 2), wf_brier=round(br5, 2),
                              vaerste_fejlalarm=fa5,
                              status=("operationel" if full_beats else
                                      "testet, ikke bestaaet mod benchmark (trin 6)"),
                              note=note),
               benchmarks=dict(intercept=dict(wf_improvement=0.0),
                               curve_only=dict(wf_improvement=round(impc, 2), wf_brier=round(brc, 2),
                                               mu=round(float(muc[0]), 4), sd=round(float(sdc[0]), 4),
                                               w=[round(float(v), 4) for v in wc],
                                               vaerste_fejlalarm=fac),
                               cp_serie="RECPROUSM156N"),
               fallback_note="Forhaandsforpligtet i RAADETS_KONSENSUS (Kimi R5/Sol R6) FOER foerste test.")
    out["benchmarks"].update(permanente_linjer())      # v5.1/v5.2-linjerne, fra resultatfilerne
    if promoveret and promoveret in prev_w.get("benchmarks", {}):
        out["benchmarks"][promoveret]["status"] = prev_w["benchmarks"][promoveret]["status"]
    (HERE / "weights.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print("weights.json (5.0-final) skrevet.")

if __name__ == "__main__":
    main()
