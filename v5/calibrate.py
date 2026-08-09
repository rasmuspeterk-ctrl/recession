#!/usr/bin/env python3
"""
calibrate.py — v5 kalibrering, trin 1: tro reproduktion af v4 (curve.py) fra et
dateret snapshot, uden haandkopierede konstanter.

Trin 1-omfang (raadets byggeorden, S2): SAMME model, SAMME label (teknisk regel),
SAMME walk-forward som v4 — men reproducerbart: alle vaegte skrives til
weights.json med datahash, dato og protokolversion. NBER-onset-labelen er trin 2
og er BEVIDST ikke med her.

Acceptancetest (indbygget): reproducerede MU/SD/W og walk-forward-metrikker
sammenlignes med v4's publicerede konstanter; afvigelser printes.

Kun stdlib + numpy.  Koer:  python calibrate.py [--check] [--snapshot data/raw/YYYY-MM-DD]
"""
import csv, hashlib, json, sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

HERE = Path(__file__).parent
RAW = HERE / "data" / "raw"
PROTOCOL = "5.0-trin1"

# v4's publicerede konstanter (MOTOR.py) — bruges KUN til acceptancetest
V4 = dict(
    MU=dict(curve=1.5064, realrate=1.2741, dd=-0.0540, d_infl=0.0971, cape_pct=0.5744),
    SD=dict(curve=1.1011, realrate=3.4545, dd=0.0808, d_infl=3.4777, cape_pct=0.2955),
    W_12M=[-2.5445, -1.2967, -0.5289, -0.2893, -0.1480, -0.4322],
    improvement=22.9, brier=19.4, n_obs=359, n_episoder=11, base=13.37)

F5 = ["curve", "realrate", "dd", "d_infl", "cape_pct"]
BASE10 = ["curve", "curve_min12", "realrate", "d_rate", "dd", "mom12", "infl", "d_infl", "cape_pct", "g"]
SETS = {
    "1: KURVEN alene":      ["curve"],
    "1b: kurve 12m-min":    ["curve_min12"],
    "2: kurve + realrente": ["curve", "realrate"],
    "3: + drawdown":        ["curve", "realrate", "dd"],
    "4: + inflation":       ["curve", "realrate", "dd", "d_infl"],
    "5: + CAPE":            F5,
    "6: alle 10":           BASE10,
    "kontrol: uden kurve":  ["realrate", "d_rate", "dd", "d_infl", "cape_pct"],
}

# ---------------------------------------------------------------- indlaesning
def find_snapshot(argv):
    if "--snapshot" in argv:
        p = Path(argv[argv.index("--snapshot") + 1])
        return p if p.is_absolute() else HERE / p
    dirs = sorted(d for d in RAW.iterdir() if d.is_dir()) if RAW.exists() else []
    if not dirs:
        sys.exit("FEJL: intet snapshot. Koer foerst: python fetch.py")
    return dirs[-1]

def read_fred(snap, sid):
    """FRED-csv -> dict {(aar, maaned): vaerdi} (maanedlige/kvartalsvise serier)."""
    f = snap / f"{sid}.csv"
    if not f.exists():
        sys.exit(f"FEJL: {f.name} mangler i snapshottet. Koer fetch.py igen.")
    out = {}
    with f.open(encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            d = row["observation_date"]
            v = list(row.values())[1]
            if v in (".", ""):
                continue
            y, m = int(d[:4]), int(d[5:7])
            out[(y, m)] = float(v)
    return out

def read_shiller(snap):
    f = snap / "shiller.csv"
    if not f.exists():
        sys.exit("FEJL: shiller.csv mangler i snapshottet.\n"
                 "Laeg Shiller-historikken i manual/shiller.csv (format: Date,SP500,CPI,LTR,CAPE;\n"
                 "Date=YYYY-MM, maanedlig fra 1871) og koer fetch.py + calibrate.py igen.\n"
                 "Kilde: ie_data.xls fra www.econ.yale.edu/~shiller/data.htm — eller v4's data/spx.csv.")
    rows = []
    with f.open(encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            d = row["Date"].strip()
            y, m = int(d[:4]), int(d[5:7])
            def num(key):
                v = row.get(key, "").strip()
                if v in ("", ".", "0", "0.0"):
                    return np.nan          # v4: replace(0.0, nan)
                try:
                    return float(v)
                except ValueError:
                    return np.nan
            rows.append(((y, m), num("SP500"), num("CPI"), num("LTR"), num("CAPE")))
    rows.sort()
    return rows

# ------------------------------------------------------- feature-konstruktion
def rolling_max(a, w, minp):
    out = np.full(len(a), np.nan)
    for i in range(len(a)):
        win = a[max(0, i - w + 1): i + 1]
        v = win[~np.isnan(win)]
        if len(v) >= minp:
            out[i] = v.max()
    return out

def rolling_min(a, w, minp):
    out = np.full(len(a), np.nan)
    for i in range(len(a)):
        win = a[max(0, i - w + 1): i + 1]
        v = win[~np.isnan(win)]
        if len(v) >= minp:
            out[i] = v.min()
    return out

def shift(a, k):
    out = np.full(len(a), np.nan)
    if k > 0:
        out[k:] = a[:-k]
    elif k < 0:
        out[:k] = a[-k:]
    else:
        out = a.copy()
    return out

def pct_change12(a):
    return (a / shift(a, 12) - 1) * 100

def expanding_cape_pct(cape, minp=120):
    """Som pandas expanding(120).apply(lambda s: (s.iloc[-1] > s).mean()):
    taeller over HELE vinduet inkl. NaN-raekker i naevneren (NaN-sammenligning=False)."""
    out = np.full(len(cape), np.nan)
    valid = 0
    for i in range(len(cape)):
        if not np.isnan(cape[i]):
            valid += 1
        if valid >= minp and not np.isnan(cape[i]):
            win = cape[: i + 1]
            with np.errstate(invalid="ignore"):
                out[i] = np.mean(cape[i] > win)   # NaN > x er False; naevner = i+1
    return out

def build_monthly(shiller, gs10, tb3ms):
    keys = [k for (k, *_) in shiller]
    px   = np.array([r[1] for r in shiller])
    cpi  = np.array([r[2] for r in shiller])
    ltr  = np.array([r[3] for r in shiller])
    cape = np.array([r[4] for r in shiller])
    y10  = np.array([gs10.get(k, np.nan) for k in keys])
    y10  = np.where(np.isnan(y10), ltr, y10)          # v4: y10.fillna(ltr)
    tb3m = np.array([tb3ms.get(k, np.nan) for k in keys])

    infl = pct_change12(cpi)
    M = dict(
        px=px, cpi=cpi, cape=cape, y10=y10, tb3m=tb3m, infl=infl,
        curve=y10 - tb3m,
        realrate=y10 - infl,
        d_rate=tb3m - shift(tb3m, 12),
        dd=px / rolling_max(px, 12, 6) - 1,
        mom12=pct_change12(px),
        d_infl=infl - shift(infl, 12),
        cape_pct=expanding_cape_pct(cape),
    )
    M["curve_min12"] = rolling_min(M["curve"], 12, 6)
    return keys, M

def to_quarterly(keys, M, gdp_g):
    """Sidste ikke-NaN maanedsvaerdi pr. kvartal pr. kolonne (pandas groupby.last)."""
    qkeys, qidx = [], {}
    for i, (y, m) in enumerate(keys):
        qk = (y, (m - 1) // 3 + 1)
        if qk not in qidx:
            qidx[qk] = len(qkeys)
            qkeys.append(qk)
    cols = {}
    for name, arr in M.items():
        out = np.full(len(qkeys), np.nan)
        for i, k in enumerate(keys):
            qk = (k[0], (k[1] - 1) // 3 + 1)
            if not np.isnan(arr[i]):
                out[qidx[qk]] = arr[i]
        cols[name] = out
    g = np.array([gdp_g.get((y, (q - 1) * 3 + 1), np.nan) for (y, q) in qkeys])
    cols["g"] = g
    return qkeys, cols

def make_labels(cols):
    g = cols["g"]
    neg = (g < 0).astype(float)
    neg[np.isnan(g)] = np.nan
    rec_now = np.full(len(g), np.nan)
    for i in range(len(g)):
        if not np.isnan(neg[i]) and i > 0 and not np.isnan(neg[i - 1]):
            rec_now[i] = 1.0 if (neg[i] == 1 and neg[i - 1] == 1) else 0.0
        elif not np.isnan(neg[i]):
            rec_now[i] = 0.0
    fwd = np.stack([shift(rec_now, -k) for k in (1, 2, 3, 4)])
    all_nan = np.all(np.isnan(fwd), axis=0)
    Y = np.full(len(rec_now), np.nan)
    Y[~all_nan] = np.nanmax(fwd[:, ~all_nan], axis=0)
    return rec_now, Y

# ------------------------------------------------------------------- model
def fit(X, y, l2=1.0, it=300):
    X = np.c_[np.ones(len(X)), X]
    w = np.zeros(X.shape[1])
    for _ in range(it):
        p = 1 / (1 + np.exp(-np.clip(X @ w, -30, 30)))
        gr = X.T @ (p - y) + l2 * np.r_[0, w[1:]]
        H = X.T @ (X * (p * (1 - p))[:, None]) + l2 * np.eye(X.shape[1])
        H[0, 0] -= l2
        try:
            w -= np.linalg.solve(H + 1e-6 * np.eye(len(w)), gr)
        except np.linalg.LinAlgError:
            break
    return w

def predict(w, X):
    return 1 / (1 + np.exp(-np.clip(np.c_[np.ones(len(X)), X] @ w, -30, 30)))

def walk_forward(D, feats, start=1960, l2=1.0):
    out = []
    Fmat = np.stack([D[f] for f in feats], axis=1)
    for i in range(len(D["year"])):
        if D["year"][i] < start:
            continue
        trX, trY = Fmat[:i], D["Y"][:i]
        if len(trX) < 60 or trY.sum() < 6:
            continue
        mu, sd = trX.mean(0), trX.std(0, ddof=1)
        sd[sd == 0] = 1
        w = fit((trX - mu) / sd, trY, l2)
        p = float(predict(w, (Fmat[[i]] - mu) / sd)[0])
        out.append((D["year"][i], D["q"][i], p, D["Y"][i]))
    return out

def metrics(rows):
    p = np.clip(np.array([r[2] for r in rows]), 1e-6, 1 - 1e-6)
    y = np.array([r[3] for r in rows])
    ll = -np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))
    b = y.mean()
    bl = -np.mean(y * np.log(b) + (1 - y) * np.log(1 - b))
    brier = (1 - np.mean((p - y) ** 2) / np.mean((b - y) ** 2)) * 100
    return ll, bl, (1 - ll / bl) * 100, brier

def count_episodes(qkeys, rec_now):
    eps, prev = [], None
    for i, v in enumerate(rec_now):
        if v == 1.0:
            if prev is None or i - prev > 2:   # >2 kvartalers hul = ny episode (~200 dage)
                eps.append(qkeys[i])
            prev = i
    return eps

# --------------------------------------------------------------------- main
def run(snap):
    shiller = read_shiller(snap)
    gs10 = read_fred(snap, "GS10")
    tb3ms = read_fred(snap, "TB3MS")
    gdp_g = read_fred(snap, "A191RL1Q225SBEA")

    keys, M = build_monthly(shiller, gs10, tb3ms)
    qkeys, cols = to_quarterly(keys, M, gdp_g)
    rec_now, Y = make_labels(cols)

    mask = ~np.isnan(Y)
    for f in BASE10:
        mask &= ~np.isnan(cols[f])
    D = {f: cols[f][mask] for f in BASE10}
    D["Y"] = Y[mask]
    D["year"] = np.array([qkeys[i][0] for i in range(len(qkeys))])[mask]
    D["q"] = np.array([qkeys[i][1] for i in range(len(qkeys))])[mask]
    dk = [qk for i, qk in enumerate(qkeys) if mask[i]]
    episodes = count_episodes(dk, rec_now[mask])

    table = {}
    for name, feats in SETS.items():
        r = walk_forward(D, feats)
        ll, bl, imp, brier = metrics(r)
        table[name] = dict(features=feats, logloss=round(ll, 4), base=round(bl, 4),
                           improvement=round(imp, 2), brier_skill=round(brier, 2), n_test=len(r))

    # endelig model: set 5 paa hele D med fuld-sample mu/sd (som v4's MOTOR-konstanter)
    Fmat = np.stack([D[f] for f in F5], axis=1)
    mu, sd = Fmat.mean(0), Fmat.std(0, ddof=1)
    sd[sd == 0] = 1
    w = fit((Fmat - mu) / sd, D["Y"])
    return dict(
        n_obs=int(mask.sum()), n_episoder=len(episodes),
        episoder=[f"{y}Q{q}" for (y, q) in episodes],
        base_rate=round(float(D["Y"].mean()), 4),
        features=F5,
        mu={f: round(float(m), 4) for f, m in zip(F5, mu)},
        sd={f: round(float(s), 4) for f, s in zip(F5, sd)},
        w=[round(float(x), 4) for x in w],
        wf_table=table,
        periode=f"{dk[0][0]}Q{dk[0][1]}-{dk[-1][0]}Q{dk[-1][1]}")

def acceptance(res):
    lines = ["", "=" * 74, "ACCEPTANCETEST mod v4's publicerede konstanter", "=" * 74]
    ok = True
    t5 = res["wf_table"]["5: + CAPE"]
    checks = [
        ("n kvartaler", V4["n_obs"], res["n_obs"], 5),
        ("episoder", V4["n_episoder"], res["n_episoder"], 0),
        ("basisrate %", V4["base"], res["base_rate"] * 100, 0.5),
        ("wf-forbedring %", V4["improvement"], t5["improvement"], 0.5),
        ("Brier-skill %", V4["brier"], t5["brier_skill"], 0.5),
    ]
    for navn, want, got, tol in checks:
        d = abs(want - got)
        mark = "OK " if d <= tol else "AFVIGER"
        if d > tol:
            ok = False
        lines.append(f"  {navn:<18} v4={want:>8.2f}  v5={got:>8.2f}  |diff|={d:.2f}  [{mark}]")
    for f in F5:
        dmu = abs(V4["MU"][f] - res["mu"][f]); dsd = abs(V4["SD"][f] - res["sd"][f])
        mark = "OK " if max(dmu, dsd) <= 0.02 else "AFVIGER"
        if max(dmu, dsd) > 0.02:
            ok = False
        lines.append(f"  mu/sd {f:<12} dmu={dmu:.4f} dsd={dsd:.4f}  [{mark}]")
    dw = max(abs(a - b) for a, b in zip(V4["W_12M"], res["w"]))
    mark = "OK " if dw <= 0.05 else "AFVIGER"
    if dw > 0.05:
        ok = False
    lines.append(f"  {'vaegte W_12M':<18} max|diff|={dw:.4f}  [{mark}]")
    lines.append(f"\n  SAMLET: {'BESTAAET — v4 er reproduceret' if ok else 'IKKE bestaaet — undersoeg diff-kilder (se README)'}")
    return "\n".join(lines), ok

def main():
    snap = find_snapshot(sys.argv)
    meta = json.loads((snap / "meta.json").read_text(encoding="utf-8"))
    print(f"=== calibrate.py — {PROTOCOL} — snapshot {snap.name} "
          f"(hash {meta['snapshot_sha256'][:12]}...) ===")
    res = run(snap)

    if "--check" in sys.argv:
        res2 = run(snap)
        print("DETERMINISME: " + ("OK — to koersler identiske" if res == res2 else "FEJL — koersler afviger!"))
        if res != res2:
            sys.exit(3)

    print(f"\nSample: {res['periode']}  {res['n_obs']} kvartaler  "
          f"{res['n_episoder']} episoder  basisrate {res['base_rate']*100:.1f}%")
    print(f"Episoder: {', '.join(res['episoder'])}")
    print(f"\n{'Model':<26}{'log-loss':>10}{'basis':>9}{'forbedring':>12}{'Brier-skill':>13}")
    print("-" * 74)
    for n, t in res["wf_table"].items():
        print(f"{n:<26}{t['logloss']:>10.3f}{t['base']:>9.3f}{t['improvement']:>11.1f}%{t['brier_skill']:>12.1f}%")

    acc_text, acc_ok = acceptance(res)
    print(acc_text)

    out = dict(protocol_version=PROTOCOL,
               created_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
               snapshot=snap.name, snapshot_sha256=meta["snapshot_sha256"],
               acceptance_bestaaet=acc_ok, **res)
    (HERE / "weights.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"\nweights.json skrevet ({'acceptance BESTAAET' if acc_ok else 'acceptance IKKE bestaaet'}).")

if __name__ == "__main__":
    main()
