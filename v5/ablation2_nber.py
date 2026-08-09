#!/usr/bin/env python3
"""
ablation2_nber.py — trin 2 i raadets byggeorden: label-ablation.
Teknisk 2-kvartalers-regel -> NBER-ONSET. Alt andet holdes fast (kvartal,
5 features, L2, walk-forward fra 1960) jf. S2: een attribuerbar aendring.

Mekanisk realtidsregel (blueprint Section 1, A8 / Sols regel):
  - Traeningsberettiget: vinduets slut + L maaneder <= refit-dato R (L=18 gulv)
  - Y_t(R)=1 kun hvis en annonceret onset (annonceringstabel) ligger i vinduet
    pr. R; ellers 0 (provisorisk nul — flips rapporteres)
  - Origins inde i en loebende recession ekskluderes fra FIT kun naar onset var
    annonceret pr. R; fra SCORING altid (endelig kronologi — Kimi R5: onset er
    dér mekanisk umulig)
  - Pre-1979-onsets (ingen annonceringsdatoer): tilgaengelige trough + 18 mdr
    (protokolkonstant, dokumenteret antagelse)

FORHAANDSREGISTREREDE GATES (fastlagt FOER koersel, jf. Sol R6/Kimi R3):
  G1  determinisme: to koersler identiske
  G2  walk-forward log-loss-forbedring >= +15% OG Brier-skill >= +12% mod egen basisrate
  G3  2001 fanges: max p blandt scorede origins med 2001-onset i vinduet >= 2x basisraten
  Alle tre bestaaet -> NBER-onset promoveres til v5.0-label (weights.json).
  Ellers: teknisk label bestaar, resultatet publiceres som "testet, ikke bestaaet".

Kun stdlib + numpy.  Koer:  python ablation2_nber.py [--check] [--snapshot ...]
"""
import csv, json, sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

import calibrate as C

HERE = Path(__file__).parent
PROTOCOL = "5.0-trin2-nber"
L_EMBARGO = 18          # maaneder, gulv (blueprint)
PRE1979_TROUGH_LAG = 18 # maaneder, dokumenteret konvention for onsets uden annonceringsraekke
GATE_LL, GATE_BR, GATE_2001 = 15.0, 12.0, 2.0

def midx(y, m):
    return y * 12 + (m - 1)

def qend_idx(y, q):
    return midx(y, q * 3)

def load_usrec(snap):
    u = C.read_fred(snap, "USREC")
    keys = sorted(u)
    return {midx(y, m): int(u[(y, m)]) for (y, m) in keys}

def episodes_from_usrec(usrec):
    """[(onset_idx, trough_idx)] — onset = 0->1-overgang, trough = sidste 1-maaned."""
    idxs = sorted(usrec)
    eps, cur_onset = [], None
    for i in idxs:
        prev = usrec.get(i - 1, 0)
        if usrec[i] == 1 and prev == 0:
            cur_onset = i
        if usrec[i] == 1 and usrec.get(i + 1, 0) == 0 and cur_onset is not None:
            eps.append((cur_onset, i))
            cur_onset = None
    return eps

def load_announcements(eps):
    """onset_idx -> annoncerings-midx. Peak-raekker matches mod naermeste onset (+/-2 mdr);
    onsets uden raekke: trough + PRE1979_TROUGH_LAG."""
    avail = {}
    f = HERE / "nber_announcements.csv"
    rows = list(csv.DictReader(f.open(encoding="utf-8-sig")))
    for r in rows:
        if not r["event"].startswith("peak"):
            continue
        cy, cm = map(int, r["cycle_month"].split("-"))
        ay, am = int(r["announcement_date"][:4]), int(r["announcement_date"][5:7])
        target = midx(cy, cm)
        best = min(eps, key=lambda e: abs(e[0] - target))
        if abs(best[0] - target) <= 2:
            avail[best[0]] = midx(ay, am)
    for onset, trough in eps:
        if onset not in avail:
            avail[onset] = trough + PRE1979_TROUGH_LAG
    return avail

def build_dataset(snap):
    """Genbruger trin 1's feature-univers uraendret; bytter kun labelen."""
    shiller = C.read_shiller(snap)
    gs10 = C.read_fred(snap, "GS10")
    tb3ms = C.read_fred(snap, "TB3MS")
    gdp_g = C.read_fred(snap, "A191RL1Q225SBEA")
    keys, M = C.build_monthly(shiller, gs10, tb3ms)
    qkeys, cols = C.to_quarterly(keys, M, gdp_g)
    rec_now, Y_tek = C.make_labels(cols)          # teknisk label til diagnostik

    mask = ~np.isnan(Y_tek)                        # SAMME raekkeunivers som trin 1
    for f in C.BASE10:
        mask &= ~np.isnan(cols[f])
    keep = [i for i in range(len(qkeys)) if mask[i]]
    D = dict(
        F=np.stack([cols[f][mask] for f in C.F5], axis=1),
        Y_tek=Y_tek[mask],
        qk=[qkeys[i] for i in keep],
    )
    D["qend"] = np.array([qend_idx(y, q) for (y, q) in D["qk"]])
    D["year"] = np.array([y for (y, _) in D["qk"]])
    return D

def nber_labels(D, eps, usrec):
    """Y_final, onset-i-vindue-oversigt og in-recession (endelig kronologi)."""
    n = len(D["qend"])
    win_onsets = [[] for _ in range(n)]
    Y_final = np.zeros(n)
    in_rec_final = np.zeros(n, bool)
    for j in range(n):
        w_lo, w_hi = D["qend"][j] + 1, D["qend"][j] + 12
        for onset, _tr in eps:
            if w_lo <= onset <= w_hi:
                win_onsets[j].append(onset)
        Y_final[j] = 1.0 if win_onsets[j] else 0.0
        in_rec_final[j] = usrec.get(int(D["qend"][j]), 0) == 1
    return Y_final, win_onsets, in_rec_final

def episode_of(idx, eps):
    for onset, trough in eps:
        if onset <= idx <= trough:
            return (onset, trough)
    return None

def wf_nber(D, eps, avail, usrec, L, start=1960, collect_flips=False):
    Y_final, win_onsets, in_rec_final = nber_labels(D, eps, usrec)
    n = len(D["qend"])
    out, power, flips = [], [], set()
    for i in range(n):
        if D["year"][i] < start:
            continue
        R = D["qend"][i]
        tr_idx = []
        for j in range(i):
            if D["qend"][j] + 12 + L > R:
                continue                       # eligibility-gulv (daekker ogsaa purging)
            ep = episode_of(int(D["qend"][j]), eps)
            if ep and avail[ep[0]] <= R:
                continue                       # inde i annonceret recession -> ud af fit
            tr_idx.append(j)
        if len(tr_idx) < 60:
            continue
        yR = np.array([1.0 if any(avail[o] <= R for o in win_onsets[j]) else 0.0
                       for j in tr_idx])
        if collect_flips:
            for k, j in enumerate(tr_idx):
                if yR[k] == 0.0 and Y_final[j] == 1.0:
                    flips.add(j)
        if yR.sum() < 6:
            continue
        X = D["F"][tr_idx]
        mu, sd = X.mean(0), X.std(0, ddof=1)
        sd[sd == 0] = 1
        w = C.fit((X - mu) / sd, yR)
        if in_rec_final[i]:
            continue                           # censureret origin: onset umulig -> ingen score
        p = float(C.predict(w, (D["F"][[i]] - mu) / sd)[0])
        out.append((int(D["year"][i]), int(D["qk"][i][1]), p, float(Y_final[i])))
        power.append((int(D["year"][i]), int(yR.sum()), len(tr_idx)))
    return out, power, sorted(flips)

def wf_teknisk_paa_samme_origins(D, eps, usrec, scored):
    """Diagnostik: trin 1's tekniske label og fit-regler, scoret paa NBER-origin-saettet."""
    _, _, in_rec_final = nber_labels(D, eps, usrec)
    scored_keys = {(y, q) for (y, q, _, _) in scored}
    out = []
    for i in range(len(D["qend"])):
        if (int(D["year"][i]), int(D["qk"][i][1])) not in scored_keys:
            continue
        trX, trY = D["F"][:i], D["Y_tek"][:i]
        if len(trX) < 60 or trY.sum() < 6:
            continue
        mu, sd = trX.mean(0), trX.std(0, ddof=1)
        sd[sd == 0] = 1
        w = C.fit((trX - mu) / sd, trY)
        p = float(C.predict(w, (D["F"][[i]] - mu) / sd)[0])
        out.append((int(D["year"][i]), int(D["qk"][i][1]), p, float(D["Y_tek"][i])))
    return out

def run(snap):
    usrec = load_usrec(snap)
    eps = episodes_from_usrec(usrec)
    avail = load_announcements(eps)
    D = build_dataset(snap)

    res, power, flips = wf_nber(D, eps, avail, usrec, L_EMBARGO, collect_flips=True)
    ll, bl, imp, br = C.metrics(res)
    base = float(np.mean([y for (_, _, _, y) in res]))

    # 2001-fangst: scorede origins hvis vindue indeholder 2001-onset
    onset_2001 = next(o for o, _ in eps if 2001 * 12 <= o < 2002 * 12)
    Y_final, win_onsets, _ = nber_labels(D, eps, usrec)
    keys_2001 = {(int(D["year"][j]), int(D["qk"][j][1]))
                 for j in range(len(D["qend"])) if onset_2001 in win_onsets[j]}
    p2001 = [p for (y, q, p, _) in res if (y, q) in keys_2001]
    max2001 = max(p2001) if p2001 else float("nan")

    # embargo-foelsomhed (Kimi R6): L = 12/18/24
    sens = {}
    for L in (12, 18, 24):
        r2, _, _ = wf_nber(D, eps, avail, usrec, L)
        sens[L] = round(C.metrics(r2)[2], 2)

    tek = wf_teknisk_paa_samme_origins(D, eps, usrec, res)
    tll, tbl, timp, tbr = C.metrics(tek)

    pos_counts = [p for (_, p, _) in power]
    return dict(
        n_scored=len(res), base_rate=round(base, 4),
        first_scored=f"{res[0][0]}Q{res[0][1]}", last_scored=f"{res[-1][0]}Q{res[-1][1]}",
        onsets_total=len(eps),
        onsets_i_sample=sorted({f"{o//12}-{o%12+1:02d}" for j in range(len(D['qend'])) for o in win_onsets[j]}),
        improvement=round(imp, 2), brier=round(br, 2), logloss=round(ll, 4),
        max_p_2001=round(max2001, 4), scored_2001=len(p2001),
        embargo_sens=sens,
        flips_provisoriske_nuller=len(flips),
        power_median_pos=int(np.median(pos_counts)), power_min_pos=int(min(pos_counts)),
        teknisk_samme_origins=dict(improvement=round(timp, 2), brier=round(tbr, 2), n=len(tek)),
    )

def main():
    snap = C.find_snapshot(sys.argv)
    meta = json.loads((snap / "meta.json").read_text(encoding="utf-8"))
    print(f"=== ablation2_nber — {PROTOCOL} — snapshot {snap.name} ===")
    res = run(snap)
    det_ok = True
    if "--check" in sys.argv:
        det_ok = (res == run(snap))
        print("G1 DETERMINISME: " + ("OK" if det_ok else "FEJL"))

    print(f"\nScorede origins: {res['n_scored']}  ({res['first_scored']}-{res['last_scored']}, "
          f"censurerede in-recession-origins fjernet)")
    print(f"Onset-basisrate: {res['base_rate']*100:.1f}%   NBER-onsets i samplevinduer: "
          f"{len(res['onsets_i_sample'])} ({', '.join(res['onsets_i_sample'])})")
    print(f"\n{'':28}{'log-loss-forb.':>15}{'Brier-skill':>13}")
    print(f"{'NBER-onset (L=18)':<28}{res['improvement']:>14.1f}%{res['brier']:>12.1f}%")
    print(f"{'Teknisk, samme origins':<28}{res['teknisk_samme_origins']['improvement']:>14.1f}%"
          f"{res['teknisk_samme_origins']['brier']:>12.1f}%   (diagnostik)")
    print(f"\nEmbargo-foelsomhed L=12/18/24: "
          f"{res['embargo_sens'][12]:.1f}% / {res['embargo_sens'][18]:.1f}% / {res['embargo_sens'][24]:.1f}%"
          + ("   [<=2pp spaend: OK]" if max(res['embargo_sens'].values()) - min(res['embargo_sens'].values()) <= 2
             else "   [>2pp spaend: MATERIEL FORK — flag!]"))
    print(f"Provisoriske nuller der senere flippede til 1: {res['flips_provisoriske_nuller']} raekker")
    print(f"Power (Grok): median positive i traening = {res['power_median_pos']}, min = {res['power_min_pos']}"
          + ("   [>=8: OK]" if res['power_median_pos'] >= 8 else "   [<8: UNDERPOWERED — frys feature-optagelse]"))
    print(f"2001-fangst: max p = {res['max_p_2001']*100:.1f}% over {res['scored_2001']} scorede origins "
          f"(krav >= {GATE_2001:.0f}x basisrate = {GATE_2001*res['base_rate']*100:.1f}%)")

    g2 = res["improvement"] >= GATE_LL and res["brier"] >= GATE_BR
    g3 = res["max_p_2001"] >= GATE_2001 * res["base_rate"]
    print("\nGATES (forhaandsregistreret):")
    print(f"  G1 determinisme      {'BESTAAET' if det_ok else 'FEJLET'}")
    print(f"  G2 skill (>=15/>=12) {'BESTAAET' if g2 else 'FEJLET'}  "
          f"({res['improvement']:.1f}% / {res['brier']:.1f}%)")
    print(f"  G3 2001-fangst       {'BESTAAET' if g3 else 'FEJLET'}  "
          f"({res['max_p_2001']*100:.1f}% vs krav {GATE_2001*res['base_rate']*100:.1f}%)")
    verdict = det_ok and g2 and g3
    print(f"\nSAMLET: {'PROMOVER NBER-onset til v5.0-label' if verdict else 'TESTET, IKKE BESTAAET — teknisk label bestaar'}")

    out = dict(protocol_version=PROTOCOL,
               created_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
               snapshot=snap.name, snapshot_sha256=meta["snapshot_sha256"],
               gates=dict(G1=bool(det_ok), G2=bool(g2), G3=bool(g3), promoveret=bool(verdict)), **res)
    (HERE / "ablation2_resultat.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print("\nablation2_resultat.json skrevet.")

    if verdict and "--promote" in sys.argv:
        promote(snap, meta, res)
    return verdict

def promote(snap, meta, res):
    """Gates bestaaet: endelig fuld-sample-fit paa NBER-onset-label -> weights.json.
    In-recession-origins holdes ude af fittet (samme sporgsmaal som live: onset
    forudsiges kun uden for recession). Gammel weights backes op."""
    usrec = load_usrec(snap)
    eps = episodes_from_usrec(usrec)
    D = build_dataset(snap)
    Y_final, _, in_rec_final = nber_labels(D, eps, usrec)
    fit_mask = ~in_rec_final
    X = D["F"][fit_mask]
    y = Y_final[fit_mask]
    mu, sd = X.mean(0), X.std(0, ddof=1)
    sd[sd == 0] = 1
    w = C.fit((X - mu) / sd, y)

    old = HERE / "weights.json"
    if old.exists():
        (HERE / "weights_trin1_teknisk.json").write_text(old.read_text(encoding="utf-8"), encoding="utf-8")
    out = dict(protocol_version=PROTOCOL,
               created_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
               snapshot=snap.name, snapshot_sha256=meta["snapshot_sha256"],
               label="nber-onset",
               label_tekst="NBER-onset inden 4 kvartaler",
               n_obs=int(fit_mask.sum()), n_episoder=len(res["onsets_i_sample"]),
               base_rate=round(float(y.mean()), 4),
               features=C.F5,
               mu={f: round(float(m), 4) for f, m in zip(C.F5, mu)},
               sd={f: round(float(s), 4) for f, s in zip(C.F5, sd)},
               w=[round(float(x), 4) for x in w],
               wf_improvement=res["improvement"], wf_brier=res["brier"],
               wf_note="purged expanding-origin wf, L=18-embargo, censurerede origins; se ablation2_resultat.json")
    old.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print("PROMOVERET: weights.json er nu NBER-onset (gammel gemt som weights_trin1_teknisk.json).")

if __name__ == "__main__":
    main()
