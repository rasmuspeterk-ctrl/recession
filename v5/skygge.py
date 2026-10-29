#!/usr/bin/env python3
"""
skygge.py — spec 8 (RAADETS_SPEC8, spec2027/8_hukommelse_skygge.md): en hash-forpligtet hukommelses-skyggemodel.

Skyggemodellen er logit^-1(a + b1*z(curve) + b2*z(curve_min12)), hvor curve_min12 er v4's rullende 12-maaneders
minimum af maanedlig GS10 - TB3MS (calibrate.build_monthly). Den fittes praecis som den operationelle model, paa de
samme raekker (identiteten asserteres og fejler hoejlydt), og refittes kun sammen med september-refitten.

Den har INGEN operationel myndighed (§1.1): aldrig i P, baand, dom, gate, trigger eller antaendingskolonnen, aldrig
i LOG.md eller paa dashboardet. Hver hovedbogsraekke logget fra 2026-11-01 faar een linje i den private,
git-ignorerede skygge_hukommelse.jsonl (med et hemmeligt nonce, spejlet til en backup uden for repoet);
hovedbog.jsonl faar kun linjens sha256 (§3). Intet tal vises: motor printer aldrig p_hukommelse, og --verificer
viser kun antal og raekke-id'er.

Koer:  python skygge.py --fit         een gang pr. operationel kalibrering (efter finalize6 ved september-refitten);
                                      printer koefficienter, skalering og korrelation (§2.5)
       python skygge.py --verificer   §3.3: hver hash i hovedbog.jsonl har en linje i den private fil og i backuppen

Kun stdlib + numpy.
"""
import hashlib, json, os, secrets, sys
from pathlib import Path
import numpy as np

import calibrate as C
import ablation2_nber as A2
import finalize6 as F6
import protokol2027 as P27

HERE = Path(__file__).parent
SPEC = "8_hukommelse_skygge.md"
FEATS = ["curve", "curve_min12"]
FORMAT = "spec8/1"
START = "2026-11-01"                 # §5: fra novemberraekken 2026; ingen backfill
PRIVAT = "skygge_hukommelse.jsonl"   # i repo-roden (HERE.parent), git-ignoreret; samme navn i backup-mappen


# ------------------------------------------------------------------ kanonisk serialisering (spec §2)
def f4(v):
    return f"{float(v):.4f}"


def f6(v):
    return f"{float(v):.6f}"


def kanonisk(rec):
    """Een linje: sorterede noegler, ',' og ':' uden mellemrum, UTF-8 uden escapes. Decimaltal SKAL vaere strenge
    med fast antal decimaler (f4/f6); et raat float stopper hoejlydt, saa formatet ikke kan glide."""
    def tjek(o):
        if isinstance(o, float):
            raise TypeError("spec 8 §2: decimaltal skal vaere strenge med fast antal decimaler")
        for v in (o.values() if isinstance(o, dict) else o if isinstance(o, (list, tuple)) else ()):
            tjek(v)
    tjek(rec)
    return json.dumps(rec, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def sha(linje):
    """skygge_sha256: sha256 af linjens UTF-8-bytes uden LF."""
    return hashlib.sha256(linje.encode("utf-8")).hexdigest()


# ------------------------------------------------------------------ fittet (§2.3-2.5)
def fit_fil(here, manifest):
    return here / "kalibreringer" / f"skygge_{manifest}.json"


def fit_id(fit):
    return hashlib.sha256(json.dumps({k: v for k, v in fit.items() if k != "fit_id"}, sort_keys=True,
                                     ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()[:12]


def kraev_identitet(mc, ms, man):
    """§2.4: skyggens raekker, labels og origins er det operationelle fits; curve-only paa samme rygrad genskaber
    manifestets vaegte. Ellers stop hoejlydt."""
    op, ori = man["modeller"]["curve_only"], [list(o) for o in man["origins"]]
    fejl = []
    if [list(o) for o in ms["_origins"]] != ori:
        fejl.append(f"skyggens berettigede origins ({len(ms['_origins'])}) er ikke manifestets ({len(ori)})")
    if [list(o) for o in mc["_origins"]] != ori:
        fejl.append("curve-only-fittets origins er ikke manifestets")
    if (mc["w"], mc["mu"], mc["sd"]) != (op["w"], op["mu"], op["sd"]):
        fejl.append("curve-only-fittet paa samme rygrad genskaber ikke manifestets w/mu/sd")
    if len(ms["_y"]) != len(mc["_y"]) or not np.array_equal(ms["_y"], mc["_y"]):
        fejl.append("labels er ikke identiske")
    if fejl:
        raise SystemExit("FEJL (spec 8 §2.4): skyggefittets identitet med det operationelle fit holder ikke: "
                         + "; ".join(fejl) + ".")


def fit_skygge(here=HERE):
    """Fit paa den operationelle kalibrerings snapshot og R (weights.json -> manifestet). -> fit-dict med fit_id."""
    spec_h = P27.kraev_forseglet(SPEC)
    W = json.loads((here / "weights.json").read_text(encoding="utf-8"))
    man = json.loads((here / "kalibreringer" / f"manifest_{W['manifest_hash']}.json").read_text(encoding="utf-8"))
    snap = C.RAW / man["snapshot"]
    meta = json.loads((snap / "meta.json").read_text(encoding="utf-8"))
    if meta["snapshot_sha256"] != man["snapshot_sha256"]:
        raise SystemExit(f"FEJL (spec 8 §2.4): snapshot {man['snapshot']} matcher ikke manifestets sha256.")
    R = A2.midx(int(man["refit_maaned"][:4]), int(man["refit_maaned"][5:7]))
    usrec = A2.load_usrec(snap)
    eps = A2.episodes_from_usrec(usrec)
    avail = A2.load_announcements(eps, f=F6.ann_fil(), usrec=usrec)
    Dc, Ds = A2.build_dataset(snap, ["curve"]), A2.build_dataset(snap, FEATS)
    mc, ms = F6.fit_model(Dc, eps, avail, usrec, R), F6.fit_model(Ds, eps, avail, usrec, R)
    kraev_identitet(mc, ms, man)
    X = Ds["F"][ms["_elig"]]
    mu, sd, w = ms["mu"], ms["sd"], ms["w"]
    alfa = w[0] - sum(w[1 + k] * mu[f] / sd[f] for k, f in enumerate(FEATS))
    fit = dict(spec=SPEC, spec_sha256=spec_h, manifest=W["manifest_hash"], snapshot=man["snapshot"],
               snapshot_sha256=man["snapshot_sha256"], refit_maaned=man["refit_maaned"], features=FEATS,
               n_obs=ms["n_obs"], n_pos=ms["n_pos"], base_rate=ms["base_rate"], estimering_slut=ms["estimering_slut"],
               univers_slut=ms["univers_slut"], mu=mu, sd=sd, w=w,
               raa=dict(alpha=round(alfa, 4), **{f"beta_{f}_pr_pp": round(w[1 + k] / sd[f], 4) for k, f in enumerate(FEATS)},
                        note="P = logit^-1(alpha + beta_curve*curve + beta_curve_min12*curve_min12), begge i pp"),
               korrelation_fit=round(float(np.corrcoef(X[:, 0], X[:, 1])[0, 1]), 4),
               origins_sha256=hashlib.sha256(json.dumps(man["origins"]).encode("utf-8")).hexdigest()[:16],
               identitet=dict(origins=len(man["origins"]), curve_only_genskabt=True),
               note="spec 8: skyggemodel uden operationel myndighed; beta_curve_min12 er daarligt bestemt "
                    "(kollinearitet) og er ikke en effekt")
    fit["fit_id"] = fit_id(fit)
    return fit


def skriv_fit(fit, here=HERE):
    """Fit-filen overskrives aldrig (spec §2); et identisk genfit er en no-op."""
    f = fit_fil(here, fit["manifest"])
    if f.exists():
        if json.loads(f.read_text(encoding="utf-8")) == fit:
            return f, False
        raise SystemExit(f"FEJL (spec 8 §2): {f.name} findes med andet indhold og overskrives aldrig.")
    f.write_text(json.dumps(fit, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return f, True


def laes_fit(here, manifest):
    f = fit_fil(here, manifest)
    if not f.exists():
        raise RuntimeError(f"intet skyggefit for manifest {manifest} (koer skygge.py --fit efter refitten)")
    fit = json.loads(f.read_text(encoding="utf-8"))
    if fit.get("manifest") != manifest or fit_id(fit) != fit.get("fit_id"):
        raise RuntimeError(f"{f.name}: fit-id'et passer ikke med indholdet")
    return fit


# ------------------------------------------------------------------ live (§2.1, §2.3)
def live_min12(snap):
    """curve_min12 ved den seneste maaned med publiceret GS10 og TB3MS (cutoff), v4-funktionen paa curve-onlys
    maanedspanel. Ingen trailing-daglig maaned. -> dict med vaerdi, cutoff, vinduet og manglende maaneder."""
    keys, M = A2.maanedspanel(snap, FEATS)
    gs10, tb3 = C.read_fred(snap, "GS10"), C.read_fred(snap, "TB3MS")
    i = max((j for j, k in enumerate(keys) if k in gs10 and k in tb3 and not np.isnan(M["curve"][j])), default=None)
    if i is None:
        raise RuntimeError("ingen maaned med publiceret GS10 og TB3MS")
    v = M["curve_min12"][i]
    if np.isnan(v):
        raise RuntimeError("curve_min12 er udefineret ved cutoff (under 6 observationer i vinduet)")
    lo = max(0, i - 11)                              # rolling_min's vindue er positionelt (12 raekker i panelet)
    (cy, cm), idx = keys[i], {k: j for j, k in enumerate(keys)}
    kal = [((cy * 12 + cm - 1 - k) // 12, (cy * 12 + cm - 1 - k) % 12 + 1) for k in range(11, -1, -1)]
    return dict(curve_min12=float(v), cutoff=f"{cy}-{cm:02d}",
                vindue=f"{keys[lo][0]}-{keys[lo][1]:02d}..{cy}-{cm:02d}",
                n_obs=int(np.sum(~np.isnan(M["curve"][lo:i + 1]))),
                uden_kurve=[f"{y}-{m:02d}" for y, m in kal if (y, m) not in idx or np.isnan(M["curve"][idx[(y, m)]])])


def lav_linje(here, snap, meta, W, kurve, dato, vindue, kode=None):
    """Skyggelinjen for een hovedbogsraekke -> (linje, sha256). Rejser ved enhver fejl. p_hukommelse beregnes af de
    vaerdier, der staar i linjen (4 decimaler), og fit-filens mu/sd/w."""
    P27.kraev_forseglet(SPEC)
    fit = laes_fit(here, W["manifest_hash"])
    lm = live_min12(snap)
    k_s, m_s = f4(kurve), f4(lm["curve_min12"])
    p = F6.p_af(fit, {"curve": float(k_s), "curve_min12": float(m_s)})
    oy, om = divmod(dato.year * 12 + dato.month - 2, 12)
    rec = dict(format=FORMAT, raekke=dato.isoformat(), origin=f"{oy}-{om + 1:02d}", vindue=vindue,
               kurve=k_s, curve_min12=m_s, curve_min12_cutoff=lm["cutoff"], curve_min12_vindue=lm["vindue"],
               p_hukommelse=f6(p), fit=fit["fit_id"], manifest=W["manifest_hash"],
               skalering=dict(mu={f: f4(fit["mu"][f]) for f in FEATS}, sd={f: f4(fit["sd"][f]) for f in FEATS}),
               kode=kode or F6.git_commit(), snapshot=snap.name, snapshot_sha256=meta["snapshot_sha256"],
               mangler=dict(n_obs=lm["n_obs"], uden_kurve=lm["uden_kurve"]), nonce=secrets.token_hex(32))
    linje = kanonisk(rec)
    return linje, sha(linje)


# ------------------------------------------------------------------ lagring (§3)
def backup_mappe():
    """MOTOR_SKYGGE_BACKUP, ellers MOTOR-skygge-backup i brugerens OneDrive (synkes ud af maskinen) eller hjemmemappe."""
    if os.environ.get("MOTOR_SKYGGE_BACKUP"):
        return Path(os.environ["MOTOR_SKYGGE_BACKUP"])
    od = Path(os.environ.get("OneDrive") or Path.home() / "OneDrive")
    return (od if od.is_dir() else Path.home()) / "MOTOR-skygge-backup"


def tilfoej(f, linje):
    """Append-only: een linje + LF, fsync, laest tilbage. En fil uden afsluttende LF er beskadiget: stop."""
    if f.exists() and f.stat().st_size and not f.read_bytes().endswith(b"\n"):
        raise RuntimeError(f"{f.name} ender ikke med LF (beskadiget?) — intet tilfoejet")
    with f.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(linje + "\n")
        fh.flush()
        os.fsync(fh.fileno())
    if f.read_text(encoding="utf-8").split("\n")[-2] != linje:
        raise RuntimeError(f"linjen kunne ikke laeses tilbage fra {f.name}")


def spejl(privat, bf, rod):
    """Backuppen er et byte-praefiks af den private fil; den manglende hale tilfoejes (indhenter en tidligere
    fejlet backup). En divergeret backup roeres ikke. Backuppen maa ikke ligge i repoet."""
    if bf.resolve().is_relative_to(rod.resolve()):
        raise RuntimeError(f"backup-mappen {bf.parent} ligger i repoet")
    bf.parent.mkdir(parents=True, exist_ok=True)
    p, b = privat.read_bytes(), (bf.read_bytes() if bf.exists() else b"")
    if not p.startswith(b):
        raise RuntimeError(f"{bf} er ikke et praefiks af den private fil (divergeret) — roeres ikke")
    if len(p) > len(b):
        with bf.open("ab") as fh:
            fh.write(p[len(b):])
            fh.flush()
            os.fsync(fh.fileno())
    if bf.read_bytes() != p:
        raise RuntimeError(f"{bf} matcher ikke den private fil efter skrivningen")


def grund(e):
    return f"{type(e).__name__}: {e}"[:240]


def hovedbogsfelter(here, snap, meta, W, kurve, dato, vindue, backup=None):
    """motor.py --log, EFTER LOG.md-raekken: skriv skyggelinjen og returner (felter til hovedbog.jsonl, besked).
    (None, None) for raekker foer starten. Fejler aldrig: kan linjen ikke laves eller skrives, logges raekken som
    manglende med grunden (§3.3, §5). Beskeden indeholder aldrig p_hukommelse."""
    if dato.isoformat() < START:
        return None, None
    rod = here.parent
    try:
        linje, h = lav_linje(here, snap, meta, W, kurve, dato, vindue)
        tilfoej(rod / PRIVAT, linje)
    except (Exception, SystemExit) as e:
        return dict(skygge_sha256=None, skygge_mangler=grund(e)), f"skygge (spec 8): MANGLER - {grund(e)}"
    bf = (backup or backup_mappe()) / PRIVAT
    try:
        spejl(rod / PRIVAT, bf, rod)
        bst = f"backup ok ({bf})"
    except (Exception, SystemExit) as e:
        bst = f"BACKUP FEJLEDE ({grund(e)}) - kopier {rod / PRIVAT} uden for repoet nu (spec 8 §3.3)"
    return dict(skygge_sha256=h), f"skygge (spec 8): linje skrevet i {PRIVAT}, sha256 {h[:12]}...; {bst}"


# ------------------------------------------------------------------ verifikation (§3.3)
def _linjer(f):
    if not f.exists():
        return None
    t = f.read_text(encoding="utf-8")
    if t and not t.endswith("\n"):
        raise SystemExit(f"FEJL (spec 8 §3.3): {f} ender ikke med LF.")
    return [ln for ln in t.split("\n") if ln]


def verificer(here=HERE, backup=None):
    """Hver skygge_sha256 i hovedbog.jsonl har praecis een kanonisk linje med samme raekke-id i den private fil og i
    backuppen. -> (ok, rapport-dict). Rapporten har antal og raekke-id'er, aldrig skyggens tal."""
    rod = here.parent
    hb = rod / "hovedbog.jsonl"
    rows = [json.loads(ln) for ln in hb.read_text(encoding="utf-8").splitlines() if ln.strip()] if hb.exists() else []
    forpligtet = [(r["logget"], r["skygge_sha256"]) for r in rows if r.get("skygge_sha256")]
    manglende = [r["logget"] for r in rows if "skygge_sha256" in r and not r["skygge_sha256"]]
    rap = dict(forpligtet=len(forpligtet), manglende_med_grund=manglende)
    ok = True
    for navn, f in (("privat", rod / PRIVAT), ("backup", (backup or backup_mappe()) / PRIVAT)):
        lin = _linjer(f)
        if lin is None:
            rap[navn] = dict(fil=str(f), findes=False)
            ok = ok and not forpligtet
            continue
        pr_hash = {}
        for ln in lin:
            pr_hash.setdefault(sha(ln), []).append(ln)
        uden, forkert = [], []
        for logget, h in forpligtet:
            ls = pr_hash.get(h, [])
            if not ls:
                uden.append(logget)
            elif json.loads(ls[0]).get("raekke") != logget or kanonisk(json.loads(ls[0])) != ls[0]:
                forkert.append(logget)
        hs = {h for _, h in forpligtet}
        rap[navn] = dict(fil=str(f), linjer=len(lin), uden_linje=uden, forkert_raekke_eller_form=forkert,
                         uden_forpligtelse=sum(1 for h in pr_hash if h not in hs),
                         dubletter=sum(len(v) - 1 for v in pr_hash.values()))
        ok = ok and not uden and not forkert
    return ok, rap


def main():
    if "--fit" in sys.argv:
        fit = fit_skygge()
        f, ny = skriv_fit(fit)
        r = fit["raa"]
        print(f"SKYGGEFIT (spec 8) {fit['fit_id']} for manifest {fit['manifest']} - snapshot {fit['snapshot']}, "
              f"R {fit['refit_maaned']}, n_obs {fit['n_obs']}, n_pos {fit['n_pos']}, fit til {fit['estimering_slut']}")
        print(f"  identitet: {fit['identitet']['origins']} origins = manifestets; curve-only genskabt")
        print(f"  mu {fit['mu']}  sd {fit['sd']}  w {fit['w']}")
        print(f"  raa: alpha {r['alpha']:+.4f}, curve {r['beta_curve_pr_pp']:+.4f}/pp, "
              f"curve_min12 {r['beta_curve_min12_pr_pp']:+.4f}/pp; korrelation paa fit-raekkerne {fit['korrelation_fit']:+.4f}")
        print(f"  {'skrevet' if ny else 'uaendret'}: {f}")
    elif "--verificer" in sys.argv:
        ok, rap = verificer()
        print(json.dumps(rap, ensure_ascii=False, indent=1))
        print("OK" if ok else "FEJL: forpligtede hashes uden linje (spec 8 §3.3)")
        sys.exit(0 if ok else 1)
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
