#!/usr/bin/env python3
"""
analyser/b3_revisionsaudit.py — spec 7B's revisionsaudit af Kim-Wright-term-praemien (RAADETS_SPEC7 §2).

FORMAAL
  Raadet lukkede den historiske test af kurvens forventningsdel og vedtog i stedet en prospektiv audit
  (spec2027/7B_forventningsdel_audit.md, forseglet d1049ac): hvor meget revideres Kim-Wright-term-praemien
  (THREEFYTP10) og dermed forventningsdelen E = (DGS10 - TP) - DTB3 fra maaned til maaned? Et uscoret
  hovedbogsfelt med E maa kun aabne, hvis det samlede max |revision af E| er under 0,10pp OG raadet godkender
  efter 12. aargang. Kravet er visningsstabilitet, ikke evidens for validitet.

HVAD BEREGNES (spec 7B §1-2, fastlaast regnestykke)
  - Aargange: snapshottet bag hver hovedbogsraekke logget EFTER forseglingen (2026-10-27), een pr. maaned,
    12 i traek; mangler en maaneds raekke, starter taellingen forfra. Snapshots foer forseglingen taeller ikke
    og rapporteres ikke her.
  - Sammenligningssaet: hver dato t i aargang 1's sidste 24 maaneder af THREEFYTP10.
  - For hver senere aargang k og hver t: |TP_k(t) - TP_1(t)| og |E_k(t) - E_1(t)| i pp, hvor DGS10 og DTB3
    tages fra aargang 1 (markedsrenterne holdes faste; samme dato, ingen fremfoering). Datoer, der mangler i
    aargang k, taelles og imputeres ikke. Revisioner af DGS10/DTB3 mellem aargange rapporteres separat.
  - Pr. aargang: median og max |revision| af TP og E; samlet max over alle datoer og aargange. Kravet (< 0,10pp)
    vurderes foerst, naar alle 12 aargange findes.
  - ACM (acm.csv i snapshottet, hvis den findes): kun dateret sekundaer serie (sidste maaned og vaerdi pr.
    aargang); aldrig en live-linje og aldrig en "modeluenighed" paa umatchede datoer.

AENDRER INTET I DRIFT: skriver kun analyser/b3_revisionsaudit_resultat.json. Aabner ingen kolonne; det kraever
  raadets godkendelse (spec 7B §3). Kun stdlib + numpy.

Koer:  cd v5 && python analyser/b3_revisionsaudit.py
"""
import json, sys
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent          # v5/analyser
V5 = HERE.parent                                # v5
sys.path.insert(0, str(V5))

import calibrate as C
import motor as M
import protokol2027 as P27

FORSEGLET = "2026-10-27"          # spec 7B forseglet (d1049ac); aargange er raekker logget EFTER denne dato
N_AARGANGE = 12
GRAENSE_PP = 0.10                 # spec 7B §3: administrativt visningsstabilitetskrav, ikke validitet


def _midx(dato):
    return int(dato[:4]) * 12 + int(dato[5:7])


def aargange(raekker):
    """Spec 7B §2: [(logget, snapshot)] for raekker logget efter forseglingen, een pr. maaned. Taellingen starter
    forfra efter en manglende maaned; den foerste loebende serie, der naar 12, bruges. -> (serie, faerdig)."""
    serie = []
    for r in sorted((r for r in raekker if r.get("logget", "") > FORSEGLET and r.get("snapshot")), key=lambda r: r["logget"]):
        if serie and _midx(r["logget"]) == _midx(serie[-1][0]):
            continue                                        # dublet i samme maaned: den foerste raekke gaelder
        if serie and _midx(r["logget"]) != _midx(serie[-1][0]) + 1:
            serie = []                                      # hul: forfra
        serie.append((r["logget"], r["snapshot"]))
        if len(serie) == N_AARGANGE:
            return serie, True
    return serie, False


def _24_mdr_foer(dato):
    y, m, d = int(dato[:4]), int(dato[5:7]), int(dato[8:10])
    try:
        return date(y - 2, m, d).isoformat()
    except ValueError:                                      # 29. februar
        return date(y - 2, m, 28).isoformat()


def _sha(snap, sid):
    try:
        return (json.loads((snap / "meta.json").read_text(encoding="utf-8")).get("series", {}).get(sid) or {}).get("sha256")
    except (OSError, ValueError):
        return None


def _acm(snap):
    f = snap / "acm.csv"
    if not f.exists():
        return None
    rk = [ln.split(",") for ln in f.read_text(encoding="utf-8-sig").splitlines()[1:] if ln.strip()]
    return dict(maaned=rk[-1][0], acmtp10=float(rk[-1][1])) if rk else None


def audit(raekker, raw):
    """Spec 7B §1-3 paa hovedbogens raekker og snapshot-mappen raw. -> resultat-dict."""
    serie, faerdig = aargange(raekker)
    ud = dict(protokol="RAADETS_SPEC7 §2", forseglet=FORSEGLET, n_aargange=len(serie), kraevet=N_AARGANGE,
              faerdig=faerdig, graense_pp=GRAENSE_PP,
              aargange=[dict(nr=i + 1, logget=lg, snapshot=sn, threefytp10_sha256=_sha(raw / sn, "THREEFYTP10"),
                             acm_sekundaer=_acm(raw / sn)) for i, (lg, sn) in enumerate(serie)])
    if not serie:
        ud["status"] = ("ingen aargange endnu: aargang 1 er snapshottet bag den foerste hovedbogsraekke logget efter "
                        f"{FORSEGLET} (2026-11-raekken)")
        return ud
    s1 = raw / serie[0][1]
    tp1 = dict(C.read_fred_daily(s1, "THREEFYTP10") or [])
    y10, tb3 = dict(C.read_fred_daily(s1, "DGS10") or []), dict(C.read_fred_daily(s1, "DTB3") or [])
    if not tp1:
        raise SystemExit(f"FEJL (spec 7B §1): THREEFYTP10 mangler i aargang 1 ({serie[0][1]}).")
    sidst = max(tp1)
    saet = sorted(t for t in tp1 if _24_mdr_foer(sidst) <= t <= sidst)
    e1 = {t: (y10[t] - tp1[t]) - tb3[t] for t in saet if t in y10 and t in tb3}
    ud["sammenligningssaet"] = dict(fra=saet[0], til=saet[-1], n_datoer=len(saet), n_med_E=len(e1))
    pr, alle_e = [], []
    for k, (lg, sn) in enumerate(serie[1:], start=2):
        sk = raw / sn
        tpk = dict(C.read_fred_daily(sk, "THREEFYTP10") or [])
        rtp = [abs(tpk[t] - tp1[t]) for t in saet if t in tpk]
        re = [abs(((y10[t] - tpk[t]) - tb3[t]) - e1[t]) for t in e1 if t in tpk]   # markedsrenter fra aargang 1
        alle_e += re
        mk = {}
        for sid, v1 in (("DGS10", y10), ("DTB3", tb3)):
            vk = dict(C.read_fred_daily(sk, sid) or [])
            dv = [abs(vk[t] - v1[t]) for t in saet if t in vk and t in v1]
            mk[sid] = round(float(max(dv)), 4) if dv else None
        pr.append(dict(nr=k, logget=lg, n_sammenlignet=len(rtp), n_mangler=len(saet) - len(rtp),
                       tp_median=round(float(np.median(rtp)), 4) if rtp else None, tp_max=round(float(max(rtp)), 4) if rtp else None,
                       e_median=round(float(np.median(re)), 4) if re else None, e_max=round(float(max(re)), 4) if re else None,
                       markedsrevision_max=mk))
    ud["revisioner"] = pr
    ud["e_max_samlet"] = round(float(max(alle_e)), 4) if alle_e else None
    if faerdig:
        ud["under_graensen"] = bool(alle_e) and max(alle_e) < GRAENSE_PP
        ud["status"] = ("12 aargange: kravet er " + ("opfyldt" if ud["under_graensen"] else "IKKE opfyldt")
                        + ". Visningsstabilitet, ikke evidens for validitet. Ingen kolonne aabner uden raadets godkendelse "
                          "(spec 7B §3); bestaaes kravet ikke, publiceres auditten, og ingen kolonne aabner.")
    else:
        ud["status"] = f"i gang: {len(serie)} af {N_AARGANGE} aargange; kravet vurderes foerst ved 12."
    return ud


def main():
    h = P27.kraev_forseglet("7B_forventningsdel_audit.md")
    ud = dict(spec_sha256=h, created_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
              **audit(M.laes_hovedbog(V5.parent / "LOG.md"), C.RAW))
    (HERE / "b3_revisionsaudit_resultat.json").write_text(json.dumps(ud, indent=1, ensure_ascii=False) + "\n",
                                                          encoding="utf-8", newline="\n")
    print(f"spec 7B revisionsaudit: {ud['status']}")


if __name__ == "__main__":
    main()
