#!/usr/bin/env python3
"""
finalize6.py — trin 6: baand + benchmarks + FALLBACK-AFGOERELSE ind i weights.json.

BLUEPRINT-KRAVET (Section 8) BED: paa NBER-onset-labelen slaar curve-only
(+34,3% wf log-loss) fuldmodellen (+33,2%). Den forhaandsforpligtede fallback
(Kimi R5 / Sol R6, nedskrevet i RAADETS_KONSENSUS foer nogen test var koert)
eksekveres derfor mekanisk:
  - OPERATIONEL v5.0-model = curve-only NBER-onset-probit (NY Fed-stil)
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
    Y, _, in_rec = A2.nber_labels(D, eps, usrec)
    fitm = ~in_rec
    X5, y = D["F"][fitm], Y[fitm]

    # walk-forward-skill: fuldmodel og curve-only paa identiske origins
    res5, _, _ = A2.wf_nber(D, eps, avail, usrec, A2.L_EMBARGO)
    _, _, imp5, br5 = C.metrics(res5)
    Dc = dict(F=D["F"][:, [0]], qend=D["qend"], year=D["year"], qk=D["qk"])
    resc, _, _ = A2.wf_nber(Dc, eps, avail, usrec, A2.L_EMBARGO)
    _, _, impc, brc = C.metrics(resc)
    print(f"fuldmodel: +{imp5:.1f}%/+{br5:.1f}%   curve-only: +{impc:.1f}%/+{brc:.1f}%")

    full_beats = imp5 > 0 and imp5 > impc
    operational = "fuldmodel" if full_beats else "curve_only"
    print(f"Section 8-krav: fuldmodel {'slaar' if full_beats else 'SLAAR IKKE'} curve-only "
          f"-> operationel model = {operational} (forhaandsforpligtet fallback)")

    # fuldmodel-fit (til ved-siden-af-linjen)
    mu5, sd5 = X5.mean(0), X5.std(0, ddof=1); sd5[sd5 == 0] = 1
    w5 = C.fit((X5 - mu5) / sd5, y)
    # curve-only-fit (operationel)
    Xc = X5[:, [0]]
    muc, sdc = Xc.mean(0), Xc.std(0, ddof=1); sdc[sdc == 0] = 1
    Zc = (Xc - muc) / sdc
    wc = C.fit(Zc, y)

    if operational == "curve_only":
        W, ngrp = boot_weights(Zc, y, D["qend"][fitm], eps, NDRAW)
        op = dict(features=["curve"], mu={"curve": round(float(muc[0]), 4)},
                  sd={"curve": round(float(sdc[0]), 4)},
                  w=[round(float(v), 4) for v in wc],
                  wf_improvement=round(impc, 2), wf_brier=round(brc, 2))
    else:
        Z5 = (X5 - mu5) / sd5
        W, ngrp = boot_weights(Z5, y, D["qend"][fitm], eps, NDRAW)
        op = dict(features=C.F5,
                  mu={f: round(float(m), 4) for f, m in zip(C.F5, mu5)},
                  sd={f: round(float(s), 4) for f, s in zip(C.F5, sd5)},
                  w=[round(float(v), 4) for v in w5],
                  wf_improvement=round(imp5, 2), wf_brier=round(br5, 2))
    print(f"bootstrap: {len(W)} traek (seed {SEED}, {ngrp} episodeblokke) for {operational}")

    out = dict(protocol_version=PROTOCOL,
               created_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
               snapshot=snap.name, snapshot_sha256=meta["snapshot_sha256"],
               label="nber-onset", label_tekst="NBER-onset inden 4 kvartaler",
               frekvens="kvartal",
               n_obs=int(fitm.sum()), n_episoder=12,
               base_rate=round(float(y.mean()), 4),
               operationel=operational,
               op=op,
               band=dict(metode="episode-blok-bootstrap af vaegte, fast standardisering",
                         fodnote="Not a predictive interval; reflects weight sensitivity to episode composition",
                         seed=SEED, n_draws=len(W), W=W),
               fuldmodel=dict(features=C.F5,
                              mu={f: round(float(m), 4) for f, m in zip(C.F5, mu5)},
                              sd={f: round(float(s), 4) for f, s in zip(C.F5, sd5)},
                              w=[round(float(v), 4) for v in w5],
                              wf_improvement=round(imp5, 2), wf_brier=round(br5, 2),
                              status=("operationel" if full_beats else
                                      "testet, ikke bestaaet mod benchmark (trin 6)"),
                              note="LL-forskel 1,1pp < stoejgulv ~4pp (trin 3-MDE); Brier gaar modsat. Gaten er mekanisk."),
               benchmarks=dict(intercept=dict(wf_improvement=0.0),
                               curve_only=dict(wf_improvement=round(impc, 2), wf_brier=round(brc, 2),
                                               mu=round(float(muc[0]), 4), sd=round(float(sdc[0]), 4),
                                               w=[round(float(v), 4) for v in wc]),
                               cp_serie="RECPROUSM156N"),
               fallback_note="Forhaandsforpligtet i RAADETS_KONSENSUS (Kimi R5/Sol R6) FOER foerste test.")
    (HERE / "weights.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print("weights.json (5.0-final) skrevet.")

if __name__ == "__main__":
    main()
