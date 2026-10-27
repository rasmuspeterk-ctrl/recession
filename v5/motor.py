#!/usr/bin/env python3
"""
MOTOR v5.0.x — maanedlig aflaesning efter raadets Section 8-spec (trin 6) og RAADETS_V501.

Output: operationel P + estimation-sensitivity-baand + basisrate (ratio kun naar baandet
udelukker basisraten), z-inputs, benchmark-tabel (intercept, curve-only, fuldmodel, de afviste
kandidater med deres panel, v4-arv, realtids-Sahm, Chauvet-Piger separat), monitors uden
taellinger, market conditions og kontekst, skabelon-genereret dom der aldrig overstiger tallene.
Sprogregler (Section 6) haandhaeves mekanisk. dashboard.json er en deterministisk funktion af
snapshot, vaegte, diagnostik og LOG.md (CI genskaber den bit-identisk): ingen dags-dato og ingen
licensbegraensede lokale filer indgaar i JSON'en.

Firewall (raadets R3, enstemmigt): kun antaendings-klassen (kurve-inversion, Sahm, HY OAS 600bp,
S&P-drawdown, advance-print) kan staa i hovedbogens antaendings-kolonne. MiroFish-svaermens
tripwires (CP-spaend, 10Y, realkredit) staar i et separat SCENARIE-APPENDIKS (fra 2026-10-15;
kode-review F9/G2.2). Kontekst-linjer ([-]) kan aldrig taendes. En monitor-serie der mangler i
snapshottet vises som [?] utilgaengelig og vaelter aldrig laesningen (F18).

Hovedbogen (LOG.md + hovedbog.jsonl): --log kun i logvinduet (foerste hverdag fra den 10. + 3 dage),
kun naar vaegte, diagnostik og annonceringstabel er i synk; manglende maaneder skrives som
'ikke logget'-raekker; en laesning inde i en annonceret recession faar dom 'censureret' (F14) — reglen er
noeglens §1 (d), skrevet byte-identisk i protokollen (spec2027/5_live_censurering.md, RAADETS_2027 §10.4).

Koer:  python motor.py [--allow-stale] [--log] [--log-uden-for-vindue "<begrundelse>"] [--json [sti]]
                      [--snapshot data/raw/YYYY-MM-DD]
"""
import csv, hashlib, json, math, sys
from datetime import date, timedelta
from pathlib import Path
import numpy as np

import calibrate as C
import spine as SP
import ablation2_nber as A2
import protokol2027 as P27

HERE = Path(__file__).parent
STALE_DAYS = 40
LOGDAG_VINDUE = None              # G3.6: None = logvindue() (BEDOEMMELSESNOEGLE.md); (fra_dag, til_dag) overstyrer (tests)
CAPE_MAX_ALDER = 45               # F30: dage — aeldre live-CAPE -> fuldmodellen 'unavailable — CAPE stale'
SPX_MAX_ALDER = 7                 # F30: dage — manuel S&P vs 52u-top flages (blokerer ikke)
MARGIN_LAG = 25                   # F30: FINRA publicerer ca. 25 dage efter maanedens udgang
MAERKE_MIN_DK = 0.05             # 2026-10-27 (review): kurveaendring under 5bp = parallelt skift, intet steepening-/flattening-maerke
CP_MIN_MAALINGER = 3             # 2026-10-27: CP-renten mangler paa ca. halvdelen af dagene; faerre maalinger paa 14 dage = utilgaengelig
NA = float("nan")
# RAADETS_2027 §1.2: styrkeklausulen staar i SAMME saetning som hvert skill-tal (analyser/styrke_simulation.py;
# stoerrelsesorden, re-afledes fra den konfigurationsspecifikke replay ved september-refit 2027)
STYRKEKLAUSUL = ("80 % styrke kraever stoerrelsesordenen 150 kalenderaars hovedbog; P(3 komplette cyklusblokke "
                 "inden for 20 aar) = 0,25; naive tests forkaster en sand nulhypotese 36-53 % af gangene ved 5-20 aar")


def skill_saetning(op, diag, a9, replay=None):
    """RAADETS_2027 §1.2: oracle-fri fast-lambda-skill foerst, saa orakel-censureret fast lambda og nested lambda,
    hver maerket, og styrkeklausulen i samme saetning. +27,05 % staar aldrig alene. Ved refitten 2027 (spec2027/
    6_skill_saetning_refit.md §4): nested lambda oracle-fri fra diagnostik.json og den re-afledte klausul fra
    replay2027_resultat.json, naar de findes for kalibreringen i drift — ellers den nuvaerende tekst."""
    of = ((diag or {}).get("oracle_fri") or {}).get("alle_live_publicerbare") or {}
    nest = (((a9 or {}).get("skill") or {}).get("curve_nested") or {}).get("improvement")
    nof = (diag or {}).get("nested_oracle_fri") or {}
    dele = []
    if of.get("improvement") is not None:
        dele.append(f"oracle-fri, fast lambda=1: +{of['improvement']:.1f}% ({of['n']} origins)")
    dele.append(f"orakel-censureret, fast lambda=1: +{op['wf_improvement']:.1f}%")
    if nof.get("improvement") is not None:
        dele.append(f"nested lambda, oracle-fri: +{nof['improvement']:.1f}% ({nof['n']} origins; orakel-censureret nested: "
                    f"+{nof['nested_orakel']['improvement']:.1f}%)")
    elif nest is not None:
        dele.append(f"nested lambda (orakel-censureret; oracle-fri udgave ikke beregnet): +{nest:.1f}%")
    kl = ((replay or {}).get("styrke") or {}).get("klausul") or STYRKEKLAUSUL
    return "Walk-forward-skill: " + "; ".join(dele) + " — og " + kl + "."


def idag():
    """Dagens dato (patches i tests)."""
    return date.today()


def logvindue(d):
    """G3.6: logdagen er den foerste hverdag fra og med den 10. i maaneden; --log er tilladt fra logdagen og
    tre kalenderdage frem (saa en blokering — fx en forfalden diagnostik — kan loeses), ellers kun med
    --log-uden-for-vindue "<begrundelse>". Et smalt, forudbestemt vindue fjerner frihedsgraden i at vaelge
    logdag efter at have set mellemlaesninger."""
    start = date(d.year, d.month, 10)
    while start.weekday() >= 5:
        start += timedelta(days=1)
    return start, start + timedelta(days=3)


def latest(series, n=1):
    return sorted(series.items())[-n]


def read_fred_raw(snap, sid):
    """FRED-csv -> [(dato, vaerdi)] i filens raekkefoelge. Noedvendig for ugeserier:
    C.read_fred kollapser til (aar, maaned) og beholder kun maanedens sidste obs."""
    out = []
    with (snap / f"{sid}.csv").open(encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            d, v = list(row.values())[:2]
            if v not in (".", ""):
                out.append((d, float(v)))
    return out


def fred_valgfri(snap, sid):
    """C.read_fred uden sys.exit: None naar filen mangler (kontekst/monitor-serier, F18)."""
    return C.read_fred(snap, sid) if (snap / f"{sid}.csv").exists() else None


def raw_valgfri(snap, sid):
    return read_fred_raw(snap, sid) if (snap / f"{sid}.csv").exists() else None


def seneste_obs(snap, meta, sid):
    """(dato, vaerdi, kilde) for seneste observation. Licensbegraensede filer (spine.LOKALE) findes kun
    lokalt — i et klon uden filen bruges meta.json's last/last_value (F1). None hvis intet findes."""
    d = C.read_fred_daily(snap, sid)
    if d:
        return d[-1][0], d[-1][1], "fil"
    s = meta.get("series", {}).get(sid)
    if s and s.get("last_value") not in (None, "", "."):
        return s["last"], float(s["last_value"]), "meta.json (lokal fil ikke i dette klon)"
    return None


def laes_hovedbog(logf):
    """LOG.md-tabellen -> [dict] med alle kolonner. P/kurve beholder tekstformen;
    dashboardet faar tal via tal_af()."""
    kol = ("logget", "snapshot", "P", "baand", "basisrate", "dom", "kurve", "antaending", "note", "kalibrering",
           "vindue", "input", "P_maanedlig", "P_maanedligt_fit", "P_1953Q2", "P_1960Q1")
    # v5.0.1 (§3.3): 'kalibrering' findes kun i raekker fra og med v5.0.1; 'vindue', 'input' og 'P_maanedlig'
    # kun fra 2026-10-15 (kode-review G3.4/F29); de tre uscorede (RAADETS_2027 §3.3/§4) kun under kalibreringer fra
    # 2027-09. Aeldre raekker har faerre celler og roeres aldrig.
    ud = []
    if not logf.exists():
        return ud
    for ln in logf.read_text(encoding="utf-8").splitlines():
        if ln.startswith("| 2"):
            c = [f.strip() for f in ln.split("|")]
            ud.append(dict(zip(kol, c[1:1 + len(kol)])))
    return ud


def tal_af(txt, faktor=1.0):
    """"18.0%" -> 0.18 ved faktor 0.01. Uparsbart -> None."""
    try:
        return round(float(str(txt).rstrip("%").replace(",", ".")) * faktor, 6)
    except (TypeError, ValueError):
        return None


def fmt(v, spec, na="—"):
    """Formatér et tal; NaN/None -> na."""
    try:
        if v is None or np.isnan(v):
            return na
    except TypeError:
        return na
    return format(v, spec)


def kal_minus(k, n):
    """(aar, maaned) minus n kalendermaaneder."""
    t = k[0] * 12 + (k[1] - 1) - n
    return (t // 12, t % 12 + 1)


def mdr_foer(k, n):
    """(aar, maaned) n kalendermaaneder foer k."""
    i = k[0] * 12 + k[1] - 1 - n
    return (i // 12, i % 12 + 1)


def udfyld_huller(series):
    """Maanedligt prisindeks {(aar, maaned): niveau} -> (kopi, udfyldte maaneder): interne huller
    udfyldes log-lineaert mellem nabomaanederne. FRED har tomme felter for 2025-10 i CPI (BLS udgav
    aldrig oktober 2025, shutdown): uden udfyldning fejler y/y-opslag paa (aar-1, maaned) med KeyError,
    og et positionelt vindue bliver en maaned for langt. Kun til maanedlige niveauserier."""
    ks = sorted(series)
    ud, fyldt = dict(series), []
    for a, b in zip(ks, ks[1:]):
        n = (b[0] - a[0]) * 12 + b[1] - a[1]
        for j in range(1, n):
            k = mdr_foer(b, n - j)
            ud[k] = series[a] * (series[b] / series[a]) ** (j / n)
            fyldt.append(k)
    return ud, fyldt


def hul_mrk(fyldt, k0, ns):
    """' (2025-10 interpoleret)' naar startmaaneden i et af vinduerne k0-n (n i ns) er udfyldt."""
    brugt = sorted({mdr_foer(k0, n) for n in ns} & set(fyldt))
    return f" ({', '.join(f'{y}-{m:02d}' for y, m in brugt)} interpoleret)" if brugt else ""


def inversionsnote(fkeys, curve_m, live_kurve):
    """Inversions-konteksten i sti-advarslen, paa maanedstal (GS10 - TB3MS). Er seneste maaned inverteret, er
    inversionen IGANGVAERENDE (ikke 'sluttede ... (0 mdr siden)'); er kun live-kurven (trailing maaned af daglige
    data) under 0, siges det foran — ellers stod '[X] Kurven inverteret' ved siden af 'sluttede 2024-11'."""
    inv = {i for i, v in enumerate(curve_m) if v < 0}
    if inv:
        li = max(inv); run0 = li
        while run0 - 1 in inv:
            run0 -= 1
        slut = fkeys[li]
        if li == len(curve_m) - 1:
            start = fkeys[run0]
            note = (f"igangvaerende siden {start[0]}-{start[1]:02d} ({li - run0 + 1} mdr t.o.m. "
                    f"{slut[0]}-{slut[1]:02d}), dybde hidtil {float(np.min(curve_m[run0:li+1])):+.2f}pp")
            if live_kurve >= 0:                           # maanedstallet halter: live-kurven er allerede positiv
                note = f"paa maanedstal {note}; live-kurven er ikke laengere inverteret ({live_kurve:+.2f}pp)"
        else:
            note = (f"sluttede {slut[0]}-{slut[1]:02d} ({len(curve_m)-1-li} mdr siden), "
                    f"dybde {float(np.min(curve_m[run0:li+1])):+.2f}pp")
    else:
        note = "ingen inversion i historikken"
    if live_kurve < 0 and not (inv and max(inv) == len(curve_m) - 1):
        note = f"live-kurven (trailing maaned) er inverteret ({live_kurve:+.2f}pp); paa maanedstal " + note
    return note


def claims_12m_maaned(icsa_raw):
    """(sidste KOMPLETTE maaned 'YYYY-MM', 12m %-aendring i maanedsmidlen af ugeobservationerne) — trin 4's
    praeregistrerede spec (erratum v5.0.1 §5; den oprindelige kode tog maanedens sidste uge). En maaned er
    komplet foerst naar sidste uges slutdato + 7 dage ligger i naeste maaned: '>= 4 obs' erklaerede
    5-loerdagsmaaneder komplette en uge for tidligt."""
    s = date.fromisoformat(icsa_raw[-1][0])
    y, m = (s.year, s.month) if (s + timedelta(days=7)).month != s.month else mdr_foer((s.year, s.month), 1)
    def middel(key):
        vals = [v for d, v in icsa_raw if d[:7] == key]
        return sum(vals) / len(vals) if vals else None
    c_now, c_prev = middel(f"{y}-{m:02d}"), middel(f"{y - 1}-{m:02d}")
    return f"{y}-{m:02d}", ((c_now / c_prev - 1) * 100 if c_now and c_prev else float("nan"))


def september_forfald(refit_maaned):
    """(aar, 9) for den foerste september EFTER refit-maaneden (§3.2a). En udloest refit (§3.2b) nulstiller
    ikke september-planen: refit 2027-04 -> 2027-09 (ikke 2028-09); 2026-09 -> 2027-09; 2027-10 -> 2028-09."""
    ry, rm = int(refit_maaned[:4]), int(refit_maaned[5:7])
    return (ry, 9) if rm < 9 else (ry + 1, 9)


def endelig(o):
    """NaN/inf -> None rekursivt: dashboard.json skal vaere gyldig JSON (JSON.parse afviser en bar NaN)."""
    if isinstance(o, float) and not math.isfinite(o):
        return None
    if isinstance(o, dict):
        return {k: endelig(v) for k, v in o.items()}
    if isinstance(o, list):
        return [endelig(v) for v in o]
    return o


def ann_rate(series, n):
    """Annualiseret aendring over n KALENDERmaaneder. Mangler basismaaneden (fx CPI-hullet 2025-10),
    er svaret NaN — aldrig en stille aendring over en anden periode (F3). Kun paa SAESONKORRIGEREDE serier."""
    if not series:
        return NA
    k = max(series)
    b = kal_minus(k, n)
    if b not in series:
        return NA
    return ((series[k] / series[b]) ** (12 / n) - 1) * 100


def yoy(series, k=None):
    """12-maaneders %-aendring paa kalendernoegle (NaN hvis maaneden et aar foer mangler)."""
    if not series:
        return NA
    k = k or max(series)
    b = kal_minus(k, 12)
    return (series[k] / series[b] - 1) * 100 if b in series and k in series else NA


def fra_top12(series):
    """Seneste vaerdi mod max af de seneste 12 kalendermaaneder (incl. seneste), i %."""
    if not series:
        return NA
    k = max(series)
    vin = [series[kal_minus(k, i)] for i in range(12) if kal_minus(k, i) in series]
    return (series[k] / max(vin) - 1) * 100


def _sporede_bnp_snapshots(raw):
    """F32: kun COMMITTEDE snapshots er 'arkivet' (dashboard-replay i CI). None uden git (temp-kopier i tests)."""
    import subprocess
    try:
        r = subprocess.run(["git", "ls-files", "--", "*/A191RL1Q225SBEA.csv"], cwd=raw,
                           capture_output=True, text=True, check=True, timeout=20)
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return None
    spor = {Path(x).parts[0] for x in r.stdout.splitlines() if x.strip()}
    return spor or None


def bnp_foerste_print(raw, snap):
    """F32: hvert kvartals FOERSTE vintage blandt de arkiverede (committede) snapshots t.o.m. det aktuelle —
    ritualet omkring den 10. falder altid mellem advance- og second-estimatet. -> {(aar, mdr): (vaerdi, snapshot)}."""
    ud = {}
    spor = _sporede_bnp_snapshots(raw) if raw.exists() else None
    dirs = [d for d in sorted(raw.iterdir()) if d.is_dir() and len(d.name) == 10 and d.name <= snap.name
            and (spor is None or d.name in spor)] if raw.exists() else []
    if snap not in dirs:
        dirs.append(snap)
    for d in dirs:
        s = fred_valgfri(d, "A191RL1Q225SBEA")
        for k, v in (s or {}).items():
            ud.setdefault(k, (v, d.name))
    return ud


def kurve_maerke(d10, d3, dK):
    """F10-maerket paa maanedens aendring. Review 2026-10-27: under MAERKE_MIN_DK er skiftet parallelt (ingen
    steepening/flattening), ellers det ben, der flyttede sig mest."""
    if abs(dK) < MAERKE_MIN_DK:
        retning = "op" if d10 > 0 and d3 > 0 else "ned" if d10 < 0 and d3 < 0 else None
        return (f"parallelt skift {retning}" if retning else "naesten uaendret") + \
            f" (kurven flyttede sig under {MAERKE_MIN_DK * 100:.0f}bp)"
    if abs(d10) >= abs(d3):
        return "lang-ende-drevet (" + ("bear steepening" if d10 > 0 and dK > 0 else "bull flattening" if d10 < 0 and dK < 0 else "blandet") + ")"
    return "kort-ende-drevet (" + ("bull steepening" if d3 < 0 and dK > 0 else "bear flattening" if d3 > 0 and dK < 0 else "blandet") + ")"


def tandem_note(diag):
    """RAADETS_2027 §1.2: den orakel-censurerede wf-skill staar aldrig alene — benchmark-raekken faar den oracle-fri med."""
    of = ((diag or {}).get("oracle_fri") or {}).get("alle_live_publicerbare") or {}
    if of.get("improvement") is None:
        return None
    return (f"wf-kolonnen er orakel-censureret som de oevrige raekker; citeres kun sammen med oracle-fri "
            f"+{of['improvement']}% ({of['n']} origins), RAADETS_2027 §1.2")


def bnp_efter_advance(kvt, snapshot_navn):
    """Review 2026-10-27: 'foerste print' er den foerste vintage i VORES snapshots. Kom snapshottet efter BEA's
    advance-vindue (kvartalsslut + udgivelseslag + slaek, spine.UDGIVELSE/SLAEK), er det en senere vintage."""
    md = kvt[1] + 2                                                     # kvartalets sidste maaned
    slut = date(kvt[0] + md // 12, md % 12 + 1, 1) - timedelta(days=1)
    frist = slut + timedelta(days=SP.UDGIVELSE["A191RL1Q225SBEA"][1] + SP.SLAEK["q"])
    return date.fromisoformat(snapshot_navn) > frist


def siden_sidst(daily, fra_dato, taerskel, over=True):
    """F28: krydsninger mellem to logninger — max (eller min) og antal dage over taersklen siden fra_dato."""
    obs = [(d, v) for d, v in (daily or []) if d > fra_dato]
    if not obs:
        return None
    ekstrem = max(obs, key=lambda t: t[1]) if over else min(obs, key=lambda t: t[1])
    n = sum(1 for _, v in obs if (v > taerskel if over else v < taerskel))
    return dict(ekstrem=round(ekstrem[1], 4), dato=ekstrem[0], dage_over=n, n=len(obs))


def _nb(a):
    """Monitor-tilstand: True/False (bool, ogsaa fra numpy), None = kontekst, '?' = utilgaengelig."""
    return a if a is None or isinstance(a, str) else bool(a)


def p_of(x, feats, mu, sd, w):
    z = [(x[f] - mu[f]) / sd[f] for f in feats]
    return 1 / (1 + np.exp(-np.clip(w[0] + sum(w[i + 1] * z[i] for i in range(len(feats))), -30, 30)))


def ren_note(t):
    """F48: '|' i en note forskyder hovedbogens kolonner, og ethvert tegn str.splitlines() deler ved (LF, CR, VT, FF,
    FS/GS/RS, NEL, U+2028/9) ville afkorte raekken ved genlaesning."""
    return " ".join(str(t).replace("|", "/").splitlines())


def noegle_hash(logf):
    """Hash af BEDOEMMELSESNOEGLE.md (LF-normaliseret) — skrives i noten i foerste raekke under en ny noegle."""
    f = logf.parent / "BEDOEMMELSESNOEGLE.md"
    if not f.exists():
        return None
    return hashlib.sha256(f.read_bytes().replace(bytes([13, 10]), bytes([10]))).hexdigest()[:8]


def maanedsvindue(d):
    """Hovedbogens scoringsvindue for en raekke logget dato d (noeglens regel, G3.4): origin = maaneden
    foer logningsmaaneden; vinduet = logningsmaaneden + 11 maaneder."""
    y, m = d.year, d.month
    sl = kal_minus((y, m), -11)
    return f"{y}-{m:02d}..{sl[0]}-{sl[1]:02d}"


def september_forfalden(ref, d):
    """§3.2a (F4): er den aarlige september-koersel forfalden pr. dato d, naar seneste koersel var i
    maaned ref ('YYYY-MM')? Forfalden fra den foerste september EFTER ref (en september-koersel paa et
    august-snapshot har ref = august og er derfor stadig forfalden — refit sker paa september-data)."""
    return (d.year, d.month) >= september_forfald(ref)


def fuld_maaned(rows, min_n):
    """Seneste KOMPLETTE kalendermaaned i en daglig/ugentlig serie: den loebende maaned taeller kun med
    mindst min_n observationer (ellers sammenlignes en delvis maaned med en hel maaned aaret foer)."""
    n = {}
    for d, _ in rows:
        n[d[:7]] = n.get(d[:7], 0) + 1
    ks = sorted(n)
    return ks[-1] if n[ks[-1]] >= min_n or len(ks) == 1 else ks[-2]


def cl_udloebsdag(aar, maaned):
    """Sidste handelsdag for NYMEX WTI-kontrakten (CL), der udloeber i (aar, maaned): 3 handelsdage foer den 25.;
    er den 25. ikke en hverdag, 3 handelsdage foer hverdagen foer den 25. (CME-reglen). Helligdage ignoreres og kan
    flytte datoen en dag. Paa og lige foer denne dag kan EIA's spotpris (Cushing) afvige kraftigt fra front-futures
    (2026-10-20: spot 107,89 mod december-kontrakten ca. 97)."""
    d = date(aar, maaned, 25)
    while d.weekday() >= 5:
        d -= timedelta(days=1)
    n = 0
    while n < 3:
        d -= timedelta(days=1)
        if d.weekday() < 5:
            n += 1
    return d


def spot_kurve(snap, op):
    """Kurven paa den seneste faelles handelsdag (DGS10 - DTB3) og P ved driftens frosne vaegte (2026-10-24).
    KONTEKST, ikke P: P maales paa en trailing maaned (F29, ratificeret i RAADETS_2027 §10.1). Linjen viser, hvor
    naeste raekkes input bevaeger sig, naar kurven flytter sig hurtigt (2026-10-22: trailing +1,13 mod spot +0,92)."""
    if op["features"] != ["curve"]:
        return None
    a, b = dict(C.read_fred_daily(snap, "DGS10") or []), dict(C.read_fred_daily(snap, "DTB3") or [])
    faelles = sorted(set(a) & set(b))
    if not faelles:
        return None
    d = faelles[-1]
    k = a[d] - b[d]
    return dict(dato=d, kurve=round(k, 4), p=round(float(p_of(dict(curve=k), op["features"], op["mu"], op["sd"], op["w"])), 6))


def em_probit(snap, vindue):
    """Benchmark: Estrella-Mishkin-probit med NY Fed's publicerede koefficienter, P(recession 12 mdr frem) =
    Phi(-0.5333 - 0.6330 * spread), paa samme trailing vindue som live-inputtet, med DGS10 - DGS3MO (obligations-
    aekvivalent, som NY Fed bruger). Andet maal end P (i recession om 12 mdr, ikke onset inden 12 mdr), og BEREGNET
    her, ikke NY Fed's publicerede tal (NY Fed bruger maanedssnit)."""
    a, c = dict(C.read_fred_daily(snap, "DGS10") or []), dict(C.read_fred_daily(snap, "DGS3MO") or [])
    vin = [d for d in sorted(set(a) & set(c)) if vindue and vindue[0] <= d <= vindue[1]]
    if not vin:
        return None
    s = float(np.mean([a[d] - c[d] for d in vin]))
    return dict(spread=round(s, 4), p=round(0.5 * (1 + math.erf((-0.5333 - 0.6330 * s) / math.sqrt(2))), 6), n_dage=len(vin))


def _paar_foer(rows, dage=365):
    """Seneste (dato, vaerdi) med dato <= sidste dato minus `dage` (daglige/ugentlige serier) — None hvis ingen."""
    graense = (date.fromisoformat(rows[-1][0]) - timedelta(days=dage)).isoformat()
    tidl = [r for r in rows if r[0] <= graense]
    return tidl[-1] if tidl else None


def kontekst_usa(snap):
    """Kontekst-protokollen 2026-10-24 (Rasmus' ordre): raavarer, kreditkort og bolig i USA, som spine.KONTEKST_BLOKKE
    definerer. Hver linje: seneste vaerdi, dato og aendring mod samme periode aaret foer (% for niveauer, pp for
    rater). INGEN taerskler, ingen taellinger, ingen indflydelse paa P, dommen eller antaendingskolonnen. Manglende
    filer springes over (aeldre snapshots). WTI faar et udloebsflag (cl_udloebsdag) og 5-dages median."""
    ud = {}
    for blok, (titel, linjer) in SP.KONTEKST_BLOKKE.items():
        raekker = []
        for sid, navn, frekv, praefiks, suffiks, skala in linjer:
            if not (snap / f"{sid}.csv").exists():
                continue
            rate = suffiks == "%"
            note = None
            if frekv in ("d", "u"):
                rows = C.read_fred_daily(snap, sid)
                if not rows:
                    continue
                dato, v = rows[-1]
                fr = _paar_foer(rows)
                aendr = (v - fr[1] if rate else (v / fr[1] - 1) * 100) if fr else None
                if sid == "DCOILWTICO":
                    med5 = float(np.median([r[1] for r in rows[-5:]]))
                    dd = date.fromisoformat(dato)
                    exp = cl_udloebsdag(dd.year, dd.month)
                    flag = []
                    if 0 <= (exp - dd).days <= 3:
                        flag.append(f"omkring udloeb af front-kontrakten (CL, sidste handelsdag {exp.isoformat()}): "
                                    "spot kan afvige kraftigt fra front-futures")
                    if abs(v / med5 - 1) > 0.05:
                        flag.append(f"afviger {(v / med5 - 1) * 100:+.0f}% fra 5-dages median")
                    wm = SP.monthly_mean(rows)                # F40: den robuste y/y er maanedssnittet (komplet maaned)
                    kw = fuld_maaned(rows, 15); kwg = f"{int(kw[:4]) - 1}{kw[4:]}"
                    note = (f"5-dages median ${med5:.2f}; maanedssnit {kw} y/y "
                            f"{fmt((wm[kw] / wm[kwg] - 1) * 100 if kwg in wm else NA, '+.0f')}%"
                            + ("; " + "; ".join(flag) if flag else ""))
            else:
                s = fred_valgfri(snap, sid)
                if not s:
                    continue
                k = max(s)
                v = s[k]
                dato = f"{k[0]}Q{(k[1] - 1) // 3 + 1}" if frekv == "q" else f"{k[0]}-{k[1]:02d}"
                b = kal_minus(k, 12)
                aendr = ((v - s[b]) if rate else (v / s[b] - 1) * 100) if b in s else None
            vv = v * skala
            vtxt = f"{praefiks}{vv:,.0f}{suffiks}" if abs(vv) >= 1000 else f"{praefiks}{vv:.2f}{suffiks}"
            atxt = "—" if aendr is None else (f"{aendr:+.2f}pp" if rate else f"{aendr:+.1f}%")
            raekker.append(dict(serie=sid, navn=navn, dato=dato, vaerdi=round(vv, 4), enhed=(praefiks + suffiks).strip(),
                                y_y=round(aendr, 3) if aendr is not None else None, y_y_enhed="pp" if rate else "%",
                                tekst=f"{vtxt} ({dato}); y/y {atxt}" + (f"; {note}" if note else "")))
        if raekker:
            ud[blok] = dict(titel=titel, linjer=raekker)
    return ud


def manuelle_tal(man, afledte):
    """2026-10-27: S&P vs 12m-top, CAPE og marginlaan beregnes af fetch (meta.json -> 'afledte'). Det automatiske
    tal bruges, naar det findes og er mindst lige saa nyt som manual.json's; ellers manual.json (reserve).
    -> (effektiv manual-dict, {felt: 'automatisk' | 'manuel'})."""
    ud, kilde = dict(man), {}
    for felt, dfelt, auto_dfelt in (("spx_vs_hi", "spx_dato", "dato"), ("cape", "cape_dato", "dato"),
                                    ("margin_yoy", "margin_periode", "periode")):
        a = afledte.get(felt) or {}
        if "vaerdi" in a and (not man.get(dfelt) or str(a.get(auto_dfelt, "")) >= str(man.get(dfelt))):
            ud[felt], ud[dfelt] = a["vaerdi"], a.get(auto_dfelt)
            kilde[felt] = "automatisk"
        else:
            kilde[felt] = "manuel"
    return ud, kilde


def dd_rygrad(snap):
    """F33: kalibreringens dd-statistik paa den seneste LUKKEDE maaned i snapshottets rygrad (spine.csv):
    maanedsmiddel / max af de seneste 12 maanedsmidler - 1 — praecis C.build_monthly's definition, og
    reproducerbar fra repoet (den licensbegraensede SP500.csv indgaar ikke). None uden rygrad."""
    rows = C.read_shiller(snap)
    sp = [(r[0], r[1]) for r in rows if r[1] is not None and np.isfinite(r[1])]
    if len(sp) < 12:
        return None
    sidste12 = [v for _, v in sp[-12:]]
    k = sp[-1][0]
    return dict(dd=sp[-1][1] / max(sidste12) - 1, maaned=f"{k[0]}-{k[1]:02d}")


def main():
    wf = HERE / "weights.json"
    if not wf.exists():
        sys.exit("FEJL: weights.json mangler. Gendan med git checkout v5/weights.json "
                 "(finalize6 koeres kun ved en §3.2-trigger).")
    W = json.loads(wf.read_text(encoding="utf-8"))
    if W.get("protocol_version") != "5.0-final":
        sys.exit(f"FEJL: weights.json er {W.get('protocol_version')} — de frosne driftsvaegte er overskrevet. "
                 "Gendan med git checkout v5/weights.json (calibrate.py skriver kun weights.json med --overskriv, F45).")
    snap = C.find_snapshot(sys.argv)
    meta = json.loads((snap / "meta.json").read_text(encoding="utf-8"))
    I = idag()
    age = (I - date.fromisoformat(snap.name)).days
    if age > STALE_DAYS and "--allow-stale" not in sys.argv:
        sys.exit(f"FEJL: snapshottet er {age} dage gammelt (>{STALE_DAYS}). fetch.py eller --allow-stale.")

    # ---- §3.2: de deterministiske rekalibreringstriggere; begge blokerer --log ----
    rekal_paakraevet = []
    ann_f = HERE / "nber_announcements.csv"
    if W.get("announcement_table_sha256") and ann_f.exists():
        if A2.tabel_aendret(W["announcement_table_sha256"], W.get("announcement_table_kanonisk"), f=ann_f):
            rekal_paakraevet.append("nber_announcements.csv er aendret siden manifest "
                                    f"{W.get('manifest_hash')} (§3.2b: ny top/bund -> refit ved denne koersel)")
    ref = max(x_ for x_ in ((W.get("koersel") or {}).get("maaned"), W.get("refit_maaned")) if x_) \
        if (W.get("koersel") or {}).get("maaned") or W.get("refit_maaned") else None
    if ref and september_forfalden(ref, I):
        rekal_paakraevet.append(f"den aarlige september-rekalibrering er forfalden (seneste koersel {ref}, §3.2a)")
    D_las = date.fromisoformat(snap.name)                  # laesningens dato: alt i dashboard.json er as-of snapshottet
    rekal_json = [r for r in rekal_paakraevet if "september" not in r] + (
        [f"den aarlige september-rekalibrering er forfalden pr. {snap.name} (seneste koersel {ref}, §3.2a)"]
        if ref and september_forfalden(ref, D_las) else [])
    for r in rekal_paakraevet:
        print(f"REKALIBRERING PAAKRAEVET: {r} — bump VERSION i finalize6.py (§3.3), koer finalize6.py && diagnostik.py "
              "foer --log.")
    if W.get("manifest_hash"):
        print(f"vaegte frosne: manifest {W['manifest_hash']} (refit {W.get('refit_maaned', '?')}); "
              f"snapshot {snap.name} er nyere end kalibreringen — det er forventet (§3).")

    # ---- F7/F14: annonceringstabellen mod USREC; censurering af live-laesningen ----
    usrec = A2.load_usrec(snap)
    eps = A2.episodes_from_usrec(usrec)
    synk = A2.usrec_krydstjek(eps, A2.laes_annonceringer(ann_f), usrec) if ann_f.exists() else []
    for s_ in synk:
        print(f"ANNONCERINGSTABEL UDE AF SYNK MED USREC: {s_}")
    avail = A2.load_announcements(eps, f=ann_f) if ann_f.exists() and not synk else {}
    # RAADETS_2027 §6 (spec2027/3_indholdstrigger_replay.md §2): NBER-indholdstriggeren, naar kalibreringen i drift er
    # fra september-refitten 2027 eller senere (foer: evalueres ikke; laesning og dashboard.json uaendrede)
    if P27.i_kraft_maaned(W.get("refit_maaned")):
        # RAADETS_2027 §10.4 (spec2027/5_live_censurering.md): live-reglen = noeglens §1 (d), byte for byte — ellers stop
        P27.kraev_regel_identisk(HERE.parent / "BEDOEMMELSESNOEGLE.md")
    if P27.i_kraft_maaned(W.get("refit_maaned")) and avail:
        P27.kraev_forseglet("3_indholdstrigger_replay.md")
        mf_ = HERE / "kalibreringer" / f"manifest_{W.get('manifest_hash')}.json"
        if not mf_.exists():
            r_ = (f"manifestet for kalibreringen i drift ({W.get('manifest_hash')}) mangler — NBER-indholdstriggeren "
                  "(RAADETS_2027 §6) kan ikke evalueres (fail-closed)")
        else:
            mm_ = json.loads(mf_.read_text(encoding="utf-8"))
            it_ = P27.indholdstrigger(A2.build_dataset(snap, ["curve"]), eps, avail, usrec, A2.midx(D_las.year, D_las.month),
                                      mm_["origins"], A2.midx(int(W["refit_maaned"][:4]), int(W["refit_maaned"][5:7])))
            r_ = None
            if it_["udloest"]:
                r_ = ("NBER-indholdstrigger (RAADETS_2027 §6): " + "; ".join(
                    [f"ny onset {o} ({', '.join(v)})" for o, v in sorted(it_["nye_onsets"].items())]
                    + [f"omlabeling {x}" for x in it_["omlabelinger"]]) + " — refit ved denne koersel")
        if r_:
            rekal_paakraevet.append(r_)
            rekal_json.append(r_)
            print(f"REKALIBRERING PAAKRAEVET: {r_} — bump VERSION i finalize6.py (§3.3), koer finalize6.py && diagnostik.py "
                  "foer --log.")

    manual_f = snap / "manual.json"
    if not manual_f.exists():
        sys.exit("FEJL: manual.json mangler i snapshottet (spx_vs_hi, cape, margin_yoy). "
                 "Laeg den i manual/ og koer fetch.py igen.")
    man = json.loads(manual_f.read_text(encoding="utf-8"))
    man, man_kilde = manuelle_tal(man, meta.get("afledte") or {})
    utilg = [sid for sid in ("ICSA", "PERMIT", "RIFSPPFAAD90NB", "MORTGAGE30US", "SAHMREALTIME", "RECPROUSM156N")
             if not (snap / f"{sid}.csv").exists()]           # F18: monitor-serier der mangler i snapshottet

    def valgfri(sid):
        s = fred_valgfri(snap, sid)
        if s is None:
            utilg.append(sid)
        return s

    gs10 = C.read_fred(snap, "GS10"); tb3 = C.read_fred(snap, "TB3MS")
    cpi, cpi_fyldt = udfyld_huller(C.read_fred(snap, "CPIAUCNS"))
    # Live-input (drift fra 2026-09-28): kurven maales som TRAILING kalendermaaned af de daglige
    # DGS10/DTB3 — samme statistik som GS10/TB3MS, uden op til en maaneds publiceringsforsinkelse
    # (se C.live_kurve). Vaegtene er uaendrede.
    LI = C.live_kurve(snap)
    y10, tb3m = LI["y10"], LI["tb3"]
    if LI["kilde"] == "daglig":
        y10_dato, y10_niveau = LI["y10_seneste"]
    else:
        (_gy, _gm), y10_niveau = latest(gs10); y10_dato = f"{_gy}-{_gm:02d}, maanedssnit"
    # F3 (PR #1, merget 2026-10-14): BLS udgav aldrig 2025-10; hullet interpoleres log-lineaert og markeres
    # hoejlydt — y/y er altid 12 KALENDERmaaneder (aldrig et stille 13-mdr-vindue). Roerer kun fuldmodellen.
    k0 = max(cpi)
    k1, k2 = kal_minus(k0, 12), kal_minus(k0, 24)
    cpi_yoy = yoy(cpi, k0)
    cpi_yoy_1 = yoy(cpi, k1)
    cpi_hul = sorted(set(cpi_fyldt) & {k0, k1, k2})

    shiller = C.read_shiller(snap)
    cape_hist = np.array([r[4] for r in shiller])
    cape_live = float(man["cape"])
    with np.errstate(invalid="ignore"):
        cape_pct = float(np.mean(cape_live > np.append(cape_hist, cape_live)))

    # ---- F30: manuelle inputs' dataperiode og friskhed (flager, blokerer ikke) ----
    friskhed = {}
    def _alder(felt):
        v = man.get(felt)
        try:
            return (D_las - date.fromisoformat(v)).days if v else None
        except ValueError:
            return None
    cape_alder = _alder("cape_dato")                         # alder as-of snapshottet (reproducerbar)
    friskhed["cape"] = dict(dato=man.get("cape_dato"), alder_dage=cape_alder,
                            stale=cape_alder is None or cape_alder > CAPE_MAX_ALDER)    # ukendt dato = stale (fail-closed)
    spx_alder = _alder("spx_dato")
    friskhed["spx_vs_hi"] = dict(dato=man.get("spx_dato"), alder_dage=spx_alder,
                                 stale=spx_alder is None or spx_alder > SPX_MAX_ALDER)
    mp = man.get("margin_periode")
    forv = None
    for back in range(0, 4):                                 # nyeste maaned m med m's udgang + lag <= laesningens dato
        km = kal_minus((D_las.year, D_las.month), back + 1)
        slut = date(km[0] + (km[1] == 12), km[1] % 12 + 1, 1) - timedelta(days=1)
        if slut + timedelta(days=MARGIN_LAG) <= D_las:
            forv = f"{km[0]}-{km[1]:02d}"
            break
    friskhed["margin_yoy"] = dict(periode=mp, forventet_nyeste=forv, foraeldet=bool(not mp or (forv and mp < forv)))
    if meta.get("afledte"):                                  # kun snapshots fra 2026-10-27 og frem
        for felt in ("cape", "spx_vs_hi", "margin_yoy"):
            friskhed[felt]["kilde"] = man_kilde[felt]
    man_noter = []
    if friskhed["cape"]["stale"]:
        man_noter.append(f"CAPE {cape_alder} dage gammel" if cape_alder is not None else "CAPE uden dato")
    if friskhed["spx_vs_hi"]["stale"]:
        man_noter.append(f"spx_vs_hi {spx_alder} dage gammel" if spx_alder is not None else "spx_vs_hi uden dato")
    if friskhed["margin_yoy"]["foraeldet"]:
        man_noter.append(f"margin {mp} (forventet {forv})" if mp else "margin uden datamaaned")

    # ---- dd (F33): kalibreringens statistik hvis SP500 findes lokalt, ellers manuel dagsluk ----
    ddk = dd_rygrad(snap)
    dd_alder = (D_las - date(int(ddk["maaned"][:4]), int(ddk["maaned"][5:7]), 1)).days if ddk else None
    dd_stale = dd_alder is not None and dd_alder > SP.FRISKHED_DAGE["spine"]      # samme graense som meta.stale.spine
    dd_live = ddk["dd"] if ddk else float(man["spx_vs_hi"])
    dd_kilde = (f"kalibreringsstatistik paa rygradens seneste lukkede maaned {ddk['maaned']} (maanedsmiddel mod 12-mdr max)"
                if ddk else "manuel dagsluk vs 52-ugers top (ingen rygrad)")

    x = dict(curve=y10 - tb3m, realrate=y10 - cpi_yoy, dd=dd_live,
             d_infl=cpi_yoy - cpi_yoy_1, cape_pct=cape_pct)

    op = W["op"]
    p_op = float(p_of(x, op["features"], op["mu"], op["sd"], op["w"]))
    x_m = dict(x, curve=LI["maanedlig"]["curve"], realrate=LI["maanedlig"]["y10"] - cpi_yoy)
    p_maanedlig = float(p_of(x_m, op["features"], op["mu"], op["sd"], op["w"]))
    band_ps = [float(p_of(x, op["features"], op["mu"], op["sd"], wb)) for wb in W["band"]["W"]]
    lo, hi = np.percentile(band_ps, 10), np.percentile(band_ps, 90)
    base = W["base_rate"]
    band_excludes_base = (base < lo) or (base > hi)
    parret = None
    if W["band"].get("base"):                  # v5.0.1 §4.3: parret regel, supplement — Section 6 uaendret
        dlt = np.array(band_ps) - np.array(W["band"]["base"])
        dlo, dhi = np.percentile(dlt, 10), np.percentile(dlt, 90)
        ps_ = bool((dlo > 0) or (dhi < 0))
        parret = dict(baand=[round(float(dlo), 6), round(float(dhi), 6)], skelnelig=ps_,
                      enig_med_baandregel=ps_ == bool(band_excludes_base), daekning="coverage not established")

    # F14: ligger laesningens maaned i en recession hvis top er annonceret pr. i dag?
    live_slut = LI.get("vindue", [None, None])[1] or f"{I.isoformat()}"
    live_idx = A2.midx(int(live_slut[:4]), int(live_slut[5:7]))
    cens = A2.i_annonceret_recession(usrec, eps, avail, live_idx) if avail else None

    fm = W["fuldmodel"]
    fm_grund = None                                         # F13/F3/F30: fuldmodellen kan vaere unavailable
    if "w" not in fm:
        fm_grund = fm.get("status", "unavailable")
    elif friskhed["cape"]["stale"]:
        fm_grund = f"unavailable — CAPE stale ({cape_alder} dage)" if cape_alder is not None else "unavailable — CAPE uden dato"
    elif dd_stale:
        fm_grund = f"unavailable — dd stale (rygraden slutter {ddk['maaned']}, {dd_alder} dage)"
    fm_ok = fm_grund is None
    p_full = float(p_of(x, fm["features"], fm["mu"], fm["sd"], fm["w"])) if fm_ok else NA
    bm = W["benchmarks"]["curve_only"]
    p_curve = float(p_of(x, ["curve"], {"curve": bm["mu"]}, {"curve": bm["sd"]}, bm["w"]))

    # v4-arv (teknisk label), hvis filen findes
    p_arv, arv_grund = None, None
    arvf = HERE / "weights_trin1_teknisk.json"
    if arvf.exists():
        A = json.loads(arvf.read_text(encoding="utf-8"))
        if ("cape_pct" in A["features"] and friskhed["cape"]["stale"]) or ("dd" in A["features"] and dd_stale):
            arv_grund = fm_grund or "unavailable — CAPE/dd stale"     # samme regel som fuldmodellen
        elif all(np.isfinite(x[f]) for f in A["features"]):
            p_arv = float(p_of(x, A["features"], A["mu"], A["sd"], A["w"]))

    sahm_s = valgfri("SAHMREALTIME"); sahm = latest(sahm_s) if sahm_s else None
    cp_s = valgfri("RECPROUSM156N"); cp = latest(cp_s) if cp_s else None
    oas = seneste_obs(snap, meta, "BAMLH0A0HYM2")
    if oas is None:
        utilg.append("BAMLH0A0HYM2")
    gq = sorted(C.read_fred(snap, "A191RL1Q225SBEA").items())
    _dff = C.read_fred_daily(snap, "DFF")
    ff_v = ff_dato = ff_kilde = None
    if _dff:
        ff_dato, ff_v, ff_kilde = _dff[-1][0], _dff[-1][1], "DFF dagligt"
    else:
        ffm = valgfri("FEDFUNDS")
        if ffm:
            (_fy, _fm), ff_v = latest(ffm)
            ff_dato, ff_kilde = f"{_fy}-{_fm:02d}", "FEDFUNDS maanedssnit"
    pce = valgfri("PCEPI")
    pce_fyldt = []
    if pce:
        pce, pce_fyldt = udfyld_huller(pce)
    pce_yoy = yoy(pce) if pce else NA

    fkeys = sorted(set(gs10) & set(tb3))
    curve_m = np.array([gs10[k] - tb3[k] for k in fkeys])
    inv_note = inversionsnote(fkeys, curve_m, x["curve"])

    # F11: P-stien ved FROSNE vaegte paa de seneste 12 publicerede maanedstal + trailing-maaneden
    sti_p = [(f"{k[0]}-{k[1]:02d}", float(p_of({"curve": gs10[k] - tb3[k]}, op["features"], op["mu"], op["sd"], op["w"])))
             for k in fkeys[-12:]]
    if LI["kilde"] == "daglig":
        sti_p.append((f"trailing {LI['vindue'][1]}", p_op))
    sti_top = max(sti_p, key=lambda t: t[1])
    sti_i = [n for n, _ in sti_p].index(sti_top[0])
    sti = dict(punkter=[[n, round(v, 4)] for n, v in sti_p], top=sti_top[0], p_top=round(sti_top[1], 4),
               maaneder_siden_top=len(sti_p) - 1 - sti_i, fald_fra_top_pp=round(100 * (sti_top[1] - p_op), 1),
               note="beskrivende — ingen fremskrivning, ingen indflydelse paa P (DASHBOARD-BRIEF regel 9)")

    # ---------------------------------------------------------------- output
    print("=" * 74)
    ver = W.get("version", "5.0")
    print(f" MOTOR v{ver}   snapshot {snap.name} (hash {meta['snapshot_sha256'][:10]}...)"
          + (f"   kalibrering {W['manifest_hash']}" if W.get("manifest_hash") else ""))
    print(f" operationel model: {'CURVE-ONLY-LOGIT' if W['operationel']=='curve_only' else 'FULDMODEL'} "
          f"paa {W['label_tekst']}")
    print(f" kalibreret {W['created_utc'][:10]} paa {W['n_obs']} kvartaler / {W['n_episoder']} onsets"
          + (f"   (estimering t.o.m. {op['estimering_slut']}; vaegte frosne til naeste rekalibrering)" if op.get("estimering_slut") else ""))
    if op.get("raa"):
        r = op["raa"]
        print(f" raa: P = logit^-1({r['alpha']:+.4f} {r['beta_curve_pr_pp']:+.4f} * kurve_pp)   [beta = w1/s, alpha = w0 - w1*mu/s]")
    if LI["kilde"] == "daglig":
        print(f" live-input: kurve = trailing maaned af daglige DGS10 - DTB3 ({LI['vindue'][0]}..{LI['vindue'][1]}, "
              f"{LI['n_dage']} dage): {LI['y10']:.2f} - {LI['tb3']:.2f} = {LI['curve']:+.2f}pp")
    else:
        print(f" live-input: MAANEDSTAL {LI['maanedlig']['maaned']} — {LI.get('note', '')}")
    if meta.get("stale"):
        print(f" FRISKHED (§1.7): stale inputs {', '.join(meta['stale'])} — se meta.json")
    if utilg:
        print(f" UTILGAENGELIGE monitor-serier i dette snapshot: {', '.join(sorted(set(utilg)))} (vises som [?])")
    print("=" * 74)

    diag = None
    df = HERE / "diagnostik.json"
    if df.exists():
        try:
            diag = json.loads(df.read_text(encoding="utf-8"))
        except ValueError:
            diag = None
    a9 = None
    a9f = HERE / "ablation9_resultat.json"
    if a9f.exists():
        try:
            a9 = json.loads(a9f.read_text(encoding="utf-8"))
        except ValueError:
            a9 = None
    rp = None
    rpf = HERE / "replay2027_resultat.json"                 # RAADETS_2027 §1.2: kun naar den hoerer til kalibreringen i drift
    if rpf.exists():
        try:
            rp = json.loads(rpf.read_text(encoding="utf-8"))
        except ValueError:
            rp = None
        if rp and rp.get("manifest_hash") != W.get("manifest_hash"):
            rp = None
    skill_tekst = skill_saetning(op, diag, a9, rp)
    print(f"\n1) SANDSYNLIGHED   [{skill_tekst}]")
    print(f"   (orakel-censureret wf: +{op['wf_improvement']:.1f}% log-loss / +{op['wf_brier']:.1f}% Brier — fast lambda=1 "
          "(arvet fra v4), fuld-sti-valg mellem to modeller, ikke nested)")
    print(f"   P({W['label_tekst']})     {p_op*100:>6.1f}%")
    em = em_probit(snap, LI.get("vindue")) if LI["kilde"] == "daglig" else None
    konv_txt = None
    if LI["kilde"] == "daglig":
        print(f"   (paa publicerede maanedstal GS10-TB3MS {LI['maanedlig']['maaned']}, kurve "
              f"{LI['maanedlig']['curve']:+.2f}pp: {p_maanedlig*100:.1f}% — samme vaegte, aeldre input)")
        if em:                                              # review 2026-10-27: T10Y3M-forvirringen
            konv_txt = (f"Konvention: 3m-renten er DTB3 paa diskontobasis, ligesom kalibreringens TB3MS. FRED's T10Y3M "
                        f"bruger DGS3MO (CMT, obligationsaekvivalent); paa samme vindue er den kurve {em['spread']:+.2f}pp. "
                        f"Forskellen ({LI['curve'] - em['spread']:.2f}pp) er konvention, ikke data. De frosne vaegte er "
                        "estimeret paa diskontobasis, saa CMT-kurven kan ikke saettes ind i dem; en foelsomhedstest er "
                        "foreslaaet til refitten 2027 (spec2027/udkast/7, kraever raadets mandat).")
            print(f"   ({konv_txt})")
    print(f"   Estimation-sensitivity-baand (10-90%)   {lo*100:.1f}% - {hi*100:.1f}%")
    print(f"   Basisrate                               {base*100:.1f}%")
    if band_excludes_base:
        print(f"   Forhold til basisrate                   {p_op/base:.2f}x")
    else:
        print("   (ratio undertrykt: baandet indeholder basisraten — Section 6)")
    print(f'   Fodnote: "{W["band"]["fodnote"]}"')
    if parret:
        print(f"   Supplement (parret, §4.3): Delta = P - basisrate pr. bootstrap-traek, central 80 %-baand "
              f"[{parret['baand'][0]*100:+.1f}, {parret['baand'][1]*100:+.1f}]pp -> "
              f"{'skelnelig' if parret['skelnelig'] else 'ikke skelnelig'} fra 0 "
              f"({'enig' if parret['enig_med_baandregel'] else 'UENIG'} med baandreglen). "
              "Diagnostik: aendrer ikke dommen. Coverage not established.")
    sk = spot_kurve(snap, op) if LI["kilde"] == "daglig" else None
    if sk:
        print(f"   Spot-kurve {sk['dato']}: {sk['kurve']:+.2f}pp -> {sk['p']*100:.1f}% ved samme vaegte (kontekst, IKKE P: P bruger "
              "trailing maaned, F29/RAADETS_2027 §10.1; viser hvor naeste raekkes input bevaeger sig)")
    p_us = P27.p_uscorede(W["uscorede"], x["curve"]) if W.get("uscorede") else None
    if p_us:
        print(f"   Uscoret (RAADETS_2027 §3.3/§4; aldrig i dommen): maanedligt fit {p_us['p_maanedligt_fit']*100:.1f}% | "
              f"start 1953Q2 {p_us['p_start_1953Q2']*100:.1f}% | start 1960Q1 {p_us['p_start_1960Q1']*100:.1f}%")
    if cens:
        print(f"   CENSURERET: laesningens maaned ligger inde i en annonceret recession (USREC-onset "
              f"{cens[0] // 12}-{cens[0] % 12 + 1:02d}, annonceret {cens[1] // 12}-{cens[1] % 12 + 1:02d}) — "
              "onset-sandsynlighed er ikke defineret (Kimi R5); P printes kun til reference.")

    print("\n2) MODEL-INPUTS (fuldmodellens fem, z mod kalibrering):")
    NAVN = dict(curve="Rentekurve 10y-3m", realrate="Realrente 10y-CPI",
                dd="S&P vs 12-mdr hoejde", d_infl="Aendring i inflation",
                cape_pct="CAPE-percentil (expanding)")
    def z_af(f):
        if fm_ok:
            return (x[f] - fm["mu"][f]) / fm["sd"][f]
        if f in op["features"]:
            return (x[f] - op["mu"][f]) / op["sd"][f]
        return NA
    for f in C.F5:
        star = "  <- operationel" if f in op["features"] else ""
        print(f"   {NAVN[f]:<26}{fmt(x[f], '>8.2f', '       —')}{fmt(z_af(f), '>9.2f', '        —')}{star}")
    print(f"   (dd: {dd_kilde}; manuel dagsluk vs 52u-top {float(man['spx_vs_hi'])*100:+.1f}%)")
    if cpi_hul:
        aarsag = "BLS udgav aldrig oktober 2025, shutdown" if (2025, 10) in cpi_hul else "tomt felt i FRED"
        print(f"   DATAHUL: CPIAUCNS {', '.join(f'{y}-{m:02d}' for y, m in cpi_hul)} mangler ({aarsag}) —{chr(10)}"
              "   interpoleret log-lineaert mellem nabomaanederne. Roerer kun realrate/d_infl (fuldmodellen), ikke P.")

    print("\n3) BENCHMARK-TABEL (printes ogsaa naar den er usmigrende):")
    print(f"   {'model':<34}{'wf-skill':>10}{'live-P':>9}   panel")
    print(f"   {'intercept (basisrate)':<34}{'+0.0%':>10}{base*100:>8.1f}%")
    print(f"   {'curve-only-logit (NY Fed-stil-bm.)':<34}{'+'+format(W['benchmarks']['curve_only']['wf_improvement'],'.1f')+'%':>10}{p_curve*100:>8.1f}%"
          f"   fuld sti t.o.m. {op.get('estimering_slut', '?')}" + ("   <- OPERATIONEL" if W["operationel"] == "curve_only" else ""))
    tandem_txt = tandem_note(diag)
    if tandem_txt:
        print(f"   {'':<34}({tandem_txt})")
    if fm_ok:
        print(f"   {'fuldmodel (5 features)':<34}{'+'+format(fm['wf_improvement'],'.1f')+'%':>10}{p_full*100:>8.1f}%"
              f"   [{fm['status']}]")
    else:
        wf5 = fm.get("wf_improvement")
        print(f"   {'fuldmodel (5 features)':<34}{('+'+format(wf5,'.1f')+'%') if wf5 is not None else '':>10}{'—':>9}   [{fm_grund}]")
    cc = W["benchmarks"].get("curve_cape")
    ca = W["benchmarks"].get("curve_awh")
    trunk = ((diag or {}).get("skill_73") or {}).get("trunkeret_panel") or {}
    if (cc or ca) and trunk.get("improvement") is not None:
        # F42: de afviste kandidater er maalt paa panelet t.o.m. 2023Q2 — sammenlign med curve-only PAA SAMME panel
        print(f"   {'curve-only, SAMME panel (reference)':<34}{'+'+format(trunk['improvement'],'.1f')+'%':>10}{'':>9}   panel t.o.m. 2023Q2")
    if cc:
        print(f"   {'curve+cape (praereg. v5.1-test)':<34}{'+'+format(cc['wf_improvement'],'.1f')+'%':>10}{'':>9}   [{cc['status']}]")
    if ca:
        print(f"   {'curve+awh (praereg. v5.2-test)':<34}{'+'+format(ca['wf_improvement'],'.1f')+'%':>10}{'':>9}   [{ca['status']}]")
    if p_arv is not None:
        print(f"   {'v4-arv (teknisk label)':<34}{'':>10}{p_arv*100:>8.1f}%   [andet maal — arv]")
    elif arv_grund:
        print(f"   {'v4-arv (teknisk label)':<34}{'':>10}{'—':>9}   [{arv_grund}]")
    print(f"   {'realtids-Sahm (trigger 0,50)':<34}{'':>10}{fmt(sahm[1] if sahm else None, '>8.2f', '       ?')}    [naerhorisont-signal]")
    print(f"   {'Chauvet-Piger nowcast':<34}{'':>10}{fmt(cp[1] if cp else None, '>8.1f', '       ?')}%   [coincident, "
          f"{(str(cp[0][0]) + '-' + format(cp[0][1], '02d')) if cp else '?'}, publiceringslag — anden disciplin]")
    if em:
        print(f"   {'Estrella-Mishkin-probit (NY Fed-koef.)':<34}{'':>10}{em['p']*100:>8.1f}%   [andet maal: i recession om 12 mdr; "
              f"beregnet paa trailing 10y-3m (CMT) {em['spread']:+.2f}pp — ikke NY Fed's publicerede tal]")
    print(f"   Note: {fm.get('note', '')}")
    mg_ = (diag or {}).get("gate_mde")
    if mg_ and "laant" not in str(fm.get("note", "")) and not P27.er_2027_gate(W.get("gate")):   # 2027: 4,42 er ude (§2.3)
        print(f"   (Stoejgulvet {mg_.get('mde_trin3_pp')}pp er trin 3's MDE, laant fra frekvenstesten; gatens EGEN MDE paa "
              f"kalibreringens panel er {mg_['mde_gate_pp']}pp (diagnostik, F8). Beslutningsreglen aendres kun af raadet.)")
    if fm_ok:
        print(f"   MODEL-DIVERGENS: operationel {p_op*100:.1f}% vs fuldmodel {p_full*100:.1f}% "
              f"(delta {abs(p_op-p_full)*100:.1f}pp).")
        zc_cape = (x['cape_pct'] - fm['mu']['cape_pct']) / fm['sd']['cape_pct']
        zc_dd = (x['dd'] - fm['mu']['dd']) / fm['sd']['dd']
        print(f"   Divergensen drives af fuldmodellens ekstra led (CAPE z={zc_cape:+.2f}, dd z={zc_dd:+.2f});"
              f"\n   modellerne er statistisk uadskillelige paa skill; curve-only er laast som operationel (V501 §6) — "
              "et skift kraever en raadsbeslutning.")
    else:
        print(f"   MODEL-DIVERGENS: ikke beregnet — fuldmodellen er {fm_grund}.")

    # claims (F46: maanedsmiddel af ALLE uger, som erratum §5) + fortsatte + vikarer (F58)
    icsa_raw = raw_valgfri(snap, "ICSA")
    claims_txt, claims_12m = "utilgaengelig", NA
    if icsa_raw:
        claims_4w = sum(v for _, v in icsa_raw[-4:]) / 4
        full, claims_12m = claims_12m_maaned(icsa_raw)
        claims_txt = f"4u-snit {claims_4w/1000:.0f}k; 12m {fmt(claims_12m, '+.1f')}% (maanedssnit {full})"
    else:
        utilg.append("ICSA")
    arb_txt = []                                            # F58: utestede monitorer — egen linje, ikke 'trin 4'
    ccsa_raw = raw_valgfri(snap, "CCSA")
    if ccsa_raw:
        kc, ccsa_12m = claims_12m_maaned(ccsa_raw)               # samme komplet-maaned-regel som ICSA (PR #1)
        arb_txt.append(f"fortsatte {ccsa_raw[-1][1]/1e6:.2f}M ({ccsa_raw[-1][0]}); maanedssnit {kc} 12m "
                       f"{fmt(ccsa_12m, '+.1f')}%")
    tmp_s = fred_valgfri(snap, "TEMPHELPS")
    if tmp_s:
        kt = max(tmp_s)
        arb_txt.append(f"vikarer {kt[0]}-{kt[1]:02d} 12m {fmt(yoy(tmp_s), '+.1f')}%")

    pmt = valgfri("PERMIT")
    if pmt:
        pmk = sorted(pmt)[-1]
        permits_yoy = yoy(pmt, pmk)
        permits_txt = f"{pmt[pmk]:.0f} ({pmk[0]}-{pmk[1]:02d}); 12m {fmt(permits_yoy, '+.1f')}%"
    else:
        pmk, permits_yoy, permits_txt = None, NA, "utilgaengelig"

    # F32: BNP-linjen paa FOERSTE print (advance) pr. kvartal, udledt af de arkiverede snapshots
    fp = bnp_foerste_print(C.RAW, snap)
    sidste2 = [k for k, _ in gq[-2:]]
    foerste = [fp.get(k, (v, snap.name)) for k, v in gq[-2:]]
    adv_txt = ", ".join(f"{k[0]}Q{(k[1]-1)//3+1} {v:+.1f}% (foerst set af os {d[5:]}"
                        + ("; senere vintage end advance" if bnp_efter_advance(k, d) else "") + ")"
                        for k, (v, d) in zip(sidste2, foerste))
    adv_aktiv = len(foerste) == 2 and all(v < 0 for v, _ in foerste)

    if oas and oas[2] != "fil":
        print(" (HY OAS laeses fra meta.json's last_value: den licensbegraensede fil findes kun lokalt, F1)")
    print("\n4) MONITORS   [individuelle linjer, ingen taellinger, ingen indflydelse paa P]")
    print("   Antaendings-klassen (kan staa i hovedbogens antaendings-kolonne):")
    oas_bp = oas[1] * 100 if oas else None
    hy_zone = ("  I SVAERM-ZONEN 350-450bp" if oas_bp is not None and 350 <= oas_bp <= 450 else "")
    mon = [
        ("Kurven inverteret", x["curve"] < 0, f"{x['curve']:+.2f}pp", "operationel feature"),
        ("Sahm >= 0,50", (sahm[1] >= 0.50) if sahm else "?", f"{sahm[1]:.2f} ({sahm[0][0]}-{sahm[0][1]:02d})" if sahm else "utilgaengelig",
         "testet, ikke bestaaet (trin 4)"),
        ("HY OAS > 600bp", (oas_bp > 600) if oas_bp is not None else "?",
         (f"{oas_bp:.0f}bp ({oas[0]}){hy_zone}" if oas else "utilgaengelig"),
         "v4-flag/seed-taerskel 600bp; ineligible (historik 1997-, FRED leverer kun rullende 3 aar); "
         "svaerm-zone 350-450bp = eneste atlas-taerskel med 3+ kanaler (5)"),
        ("S&P dagsluk vs 52u-top < -20%", float(man["spx_vs_hi"]) < -0.20, f"{float(man['spx_vs_hi'])*100:+.0f}% ({'FRED SP500' if man_kilde['spx_vs_hi'] == 'automatisk' and meta.get('afledte') else 'manuel'}{', ' + man['spx_dato'] if man.get('spx_dato') else ''})",
         "fuldmodel-feature (kalibreringens dd i sektion 2)"),
        ("Advance-estimat: 2 neg. BNP-print", adv_aktiv, adv_txt,
         "uvalideret realtidsdiagnostik paa foerste print i vores snapshots (vintage-flip dokumenteret, trin 5)"),
    ]
    kontekst = [
        ("Claims-momentum", None, claims_txt, "testet, ikke bestaaet (trin 4)"),
        ("Permits y/y", None, permits_txt, "testet, ikke bestaaet (trin 4)"),
    ]
    if arb_txt:
        kontekst.append(("Fortsatte ansoegninger / vikarer", None, "; ".join(arb_txt),
                         "utestet monitor (kontekst, F58) — ingen taerskel"))
    awh = fred_valgfri(snap, "AWHMAN")
    if awh:
        kontekst.append(("Arbejdstimer industri (6m ann.)", None,
                         f"{awh[max(awh)]:.1f} t ({max(awh)[0]}-{max(awh)[1]:02d}); {fmt(ann_rate(awh, 6), '+.1f')}%",
                         "testet, ikke bestaaet (v5.2, sidste skud)"))
    kontekst.append(("Inversionsnote", None, inv_note, "uvalideret kontekst"))
    kontekst.append(("Kurve-sti (P ved frosne vaegte)", None,
                     f"top {sti['p_top']*100:.1f}% ({sti['top']}), {sti['maaneder_siden_top']} mdr siden; "
                     f"nu {p_op*100:.1f}% ({-sti['fald_fra_top_pp']:+.1f}pp fra top)",
                     "beskrivende sti, ingen fremskrivning (R4/F11)"))
    mon = [(n, _nb(a), v, st) for n, a, v, st in mon]
    for navn, aktiv, vaerdi, status in mon:
        boks = "[X]" if aktiv is True else ("[?]" if aktiv == "?" else "[ ]")
        print(f"   {boks} {navn:<36}{vaerdi:<52}  {status}")
    print("   Kontekst (kan aldrig taendes):")
    for navn, aktiv, vaerdi, status in kontekst:
        print(f"   [-] {navn:<36}{vaerdi:<52}  {status}")

    # ---- SCENARIE-APPENDIKS: svaerm-tripwires (R3: uden for modeloutput og antaendings-kolonnen) ----
    rows = laes_hovedbog(HERE.parent / "LOG.md")
    tidl_rows = [r for r in rows if r.get("snapshot") != snap.name]   # replay-stabil: ikke raekken --log netop skriver
    forr = next((r for r in reversed(tidl_rows) if tal_af(r.get("P"), 0.01) is not None), None)
    sidst_logget = forr["logget"][:10] if forr else None
    _pm = {}
    if forr and (C.RAW / forr.get("snapshot", "") / "meta.json").exists() and forr.get("snapshot"):
        _pm = json.loads((C.RAW / forr["snapshot"] / "meta.json").read_text(encoding="utf-8")).get("series", {})
    def fra(*sids):
        """F28: sidste observation forrige LOGGEDE laesning saa (pr. serie; fallback: logdatoen)."""
        ds = [(_pm.get(s_) or {}).get("last") for s_ in sids]
        ds = [d_ for d_ in ds if d_]
        return min(ds) if ds else sidst_logget
    scen = []
    _cp = dict(C.read_fred_daily(snap, "RIFSPPFAAD90NB") or []); _tbd = C.read_fred_daily(snap, "DTB3") or []
    _tb = dict(_tbd)
    cp_spread = None
    if _cp and _tb:
        faelles = sorted(set(_cp) & set(_tb))
        cp_dato = faelles[-1]
        cp_spread_bp = (_cp[cp_dato] - _tb[cp_dato]) * 100
        # 2026-10-27: CP-renten mangler paa ca. halvdelen af dagene (ingen AA-udstedelse). "10 seneste faelles dage"
        # strakte sig derfor over ca. en maaned. Nu: alle maalinger i de seneste 14 kalenderdage (til seneste T-bill-dag);
        # faerre end CP_MIN_MAALINGER -> utilgaengelig i stedet for at straekke vinduet.
        cp_fra = (date.fromisoformat(_tbd[-1][0]) - timedelta(days=13)).isoformat()
        sid14 = [(_cp[d] - _tb[d]) * 100 for d in faelles if d >= cp_fra]
        n_over = sum(v > 75 for v in sid14)
        cp_stale = (date.fromisoformat(_tbd[-1][0]) - date.fromisoformat(cp_dato)).days > 10     # F47
        cp_tynd = len(sid14) < CP_MIN_MAALINGER
        cp_spread = [(d, (_cp[d] - _tb[d]) * 100) for d in faelles]
        ss = siden_sidst(cp_spread, fra("RIFSPPFAAD90NB", "DTB3"), 75) if sidst_logget else None
        scen.append(("CP-spaend 3m > 75bp i 2+ uger", "?" if cp_stale or cp_tynd else n_over == len(sid14),
                     f"{cp_spread_bp:.0f}bp ({cp_dato}{', STALE' if cp_stale else ''}); >75bp {n_over}/{len(sid14)} maalinger "
                     f"de seneste 14 dage{' — for faa maalinger' if cp_tynd else ''}"
                     + (f"; efter {fra('RIFSPPFAAD90NB', 'DTB3')}: max {ss['ekstrem']:.0f}bp ({ss['dato']}), {ss['dage_over']}/{ss['n']} dage over" if ss else ""),
                     f"svaerm-tripwire, 1-2 kanaler (funding); alle maalinger de seneste 14 dage over 75bp (mindst {CP_MIN_MAALINGER} maalinger)"))
        if cp_stale:
            utilg.append(f"CP-spaend stale siden {cp_dato}")
    else:
        utilg.append("RIFSPPFAAD90NB")
        scen.append(("CP-spaend 3m > 75bp i 2+ uger", "?", "utilgaengelig (RIFSPPFAAD90NB/DTB3 mangler i snapshottet)",
                     "svaerm-tripwire, 1-2 kanaler (funding)"))
    _tpd = C.read_fred_daily(snap, "THREEFYTP10")
    tp_dato, tp10, tp_txt = None, None, ""
    if _tpd:
        tp_dato, tp10 = _tpd[-1]
        tp_txt = f" / KW TP {tp10:+.2f}pp (Kim-Wright, Fed Board, {tp_dato[5:]})"         # F22
    elif (snap / "acm.csv").exists():
        with (snap / "acm.csv").open(encoding="utf-8-sig") as fh:
            _rows = list(csv.DictReader(fh))
        tp_txt = f" / ACM TP {float(_rows[-1]['ACMTP10']):+.2f}pp (NY Fed, maanedlig {_rows[-1]['Date']})"
    d10 = C.read_fred_daily(snap, "DGS10")
    ss10 = siden_sidst(d10, fra("DGS10"), 5.25) if sidst_logget and d10 else None
    scen.append(("10Y > 5,25%", y10_niveau > 5.25,
                 f"{y10_niveau:.2f}% ({y10_dato}){tp_txt}"
                 + (f"; efter {fra('DGS10')}: max {ss10['ekstrem']:.2f}% ({ss10['dato']}), {ss10['dage_over']}/{ss10['n']} dage over" if ss10 else ""),
                 "1 kanal (fiskal); kanalens ANTAGNE trigger, ikke Q2-varsel; maaleregel: seneste daglige niveau"))
    mg = C.read_fred_daily(snap, "MORTGAGE30US")
    if mg:
        ssm = siden_sidst(mg, fra("MORTGAGE30US"), 7.8) if sidst_logget else None
        scen.append(("Realkredit 30Y > 7,8%", mg[-1][1] > 7.8, f"{mg[-1][1]:.2f}% ({mg[-1][0]})"
                     + (f"; efter {fra('MORTGAGE30US')}: max {ssm['ekstrem']:.2f}% ({ssm['dato']}), {ssm['dage_over']}/{ssm['n']} uger over" if ssm else ""),
                     "1 kanal (fiskal); kanalens antagne transmission, ikke Q2-varsel"))
    else:
        utilg.append("MORTGAGE30US")
        scen.append(("Realkredit 30Y > 7,8%", "?", "utilgaengelig (MORTGAGE30US mangler i snapshottet)", "1 kanal (fiskal)"))
    print("\n   SCENARIE-APPENDIKS — MiroFish-svaermens tripwires (TRIGGER-ATLAS; uvalideret; raadets R3: uden for")
    print("   modeloutputtet og hovedbogens antaendings-kolonne fra 2026-10-15; proveniens i G2-erratumet):")
    scen = [(n, _nb(a), v, st) for n, a, v, st in scen]
    if [u for u in utilg if u.startswith("CP-spaend stale")]:
        print("   (CP-spaendet er STALE: se (?)-linjen)")
    for navn, aktiv, vaerdi, status in scen:
        boks = "(X)" if aktiv is True else ("(?)" if aktiv == "?" else "( )")
        print(f"   {boks} {navn:<36}{vaerdi:<52}  {status}")

    print()
    print("5) MARKET CONDITIONS — not recession evidence   [kvalitativ]")
    erp = 100 / cape_live - y10_niveau                     # live CAPE mod seneste daglige 10Y
    margin_txt = (f"{float(man['margin_yoy']):+.1f}% (FINRA, datamaaned {mp or '?'}"
                  + (f" — FORAELDET, forventet {forv}" if friskhed['margin_yoy']['foraeldet'] else "") + ")")
    mc = [("CAPE-percentil (expanding)", f"{cape_pct*100:.1f}. pct (CAPE {cape_live:.2f}"
           + (f", {man['cape_dato']}" if man.get("cape_dato") else "") + (" — STALE" if friskhed["cape"]["stale"] else "") + ")"),
          ("Aktierisikopraemie 1/CAPE - y10", f"{erp:+.2f}pp"),
          ("Marginlaan y/y", margin_txt)]
    for navn, vaerdi in mc:
        print(f"       {navn:<34}{vaerdi}")
    # F41: forudsaetnings-tripwires' AKTUELLE status (atlasset viser 10/8-tilstanden)
    rk = (ff_v - pce_yoy) if ff_v is not None and np.isfinite(pce_yoy) else NA
    pm_neg3 = None
    if pmt and pmk:
        ks3 = [kal_minus(pmk, i) for i in range(3)]
        pm_neg3 = all(np.isfinite(yoy(pmt, k)) and yoy(pmt, k) < 0 for k in ks3)
    forud = [("Marginlaan y/y > 40%", float(man["margin_yoy"]) > 40, f"{float(man['margin_yoy']):+.1f}%", "svaerm (1 kanal)"),
             ("Permits < 1,40M + 3 mdr y/y neg.", (pmt[pmk] < 1400 and bool(pm_neg3)) if pmt and pmk else "?",
              permits_txt, "svaerm (1 kanal)"),
             ("Realt kontantafkast FF-PCE < 0", (rk < 0) if np.isfinite(rk) else "?", f"{fmt(rk, '+.2f')}pp", "v4-debaseringsflag (seed-ekko, G2.3)")]
    print("       Forudsaetnings-tripwires (braendstof, ikke gnist; aktuel status):")
    forud = [(n, _nb(a), v, st) for n, a, v, st in forud]
    for navn, aktiv, vaerdi, prov in forud:
        boks = "(X)" if aktiv is True else ("(?)" if aktiv == "?" else "( )")
        print(f"         {boks} {navn:<34}{vaerdi:<28}{prov}")

    # ---- pengepolitik, inflation, kurvens sammensaetning, kredit, NBER-indikatorer: KONTEKST ----
    pol = []
    if ff_v is not None:
        pol.append(("Fed funds (effektiv)", f"{ff_v:.2f}% ({ff_dato}, {ff_kilde})"))
        if pce:
            pk = max(pce)
            pol.append(("Realt kontantafkast FF - PCE", f"{fmt(rk, '+.2f')}pp (PCE y/y {pk[0]}-{pk[1]:02d})"
                        + hul_mrk(pce_fyldt, pk, (12,))))
        if _tbd:
            if _dff:                                            # PR #1: begge ben paa samme dag, som CP-spaendet
                _ffd = dict(_dff); bf_dato = max(set(_ffd) & set(_tb))
                bf_bp = (_tb[bf_dato] - _ffd[bf_dato]) * 100
            else:
                bf_dato, bf_bp = _tbd[-1][0], (_tbd[-1][1] - ff_v) * 100
            pol.append(("3m-bill minus Fed funds", f"{bf_bp:+.0f}bp ({bf_dato}, diskonto)"))
    if pce:
        pol.append(("PCE-infl. 3m/6m/12m ann.", f"{fmt(ann_rate(pce, 3), '.1f')} / {fmt(ann_rate(pce, 6), '.1f')} / {fmt(pce_yoy, '.1f')}%"
                    + hul_mrk(pce_fyldt, max(pce), (3, 6, 12))))
    cpi_sa = fred_valgfri(snap, "CPIAUCSL")
    if cpi_sa:
        cpi_sa, sa_fyldt = udfyld_huller(cpi_sa)
        pol.append(("CPI (SA) 3m/6m/12m ann.",
                    f"{fmt(ann_rate(cpi_sa, 3), '.1f')} / {fmt(ann_rate(cpi_sa, 6), '.1f')} / {fmt(ann_rate(cpi_sa, 12), '.1f')}%"
                    + hul_mrk(sa_fyldt, max(cpi_sa), (3, 6, 12))))
    if tp10 is not None:                                     # 10Y paa TP-datoen (eller naermeste tidligere)
        _d10 = dict(d10 or [])
        _prior = [d for d in _d10 if d <= tp_dato]
        _y = _d10[max(_prior)] if _prior else y10_niveau
        pol.append(("10y = term-praemie + forventet", f"{_y:.2f} = {tp10:.2f} + {_y - tp10:.2f} ({tp_dato}, Kim-Wright)"))
    # F38: kurvens sammensaetning paa SAMME trailing vindue som live-inputtet
    sammensaetning = None
    d2, d1, d3mo = C.read_fred_daily(snap, "DGS2"), C.read_fred_daily(snap, "DGS1"), C.read_fred_daily(snap, "DGS3MO")
    if LI["kilde"] == "daglig" and d2:
        a10, b3, c2 = dict(d10), dict(_tbd), dict(d2)
        vin = [d for d in sorted(set(a10) & set(b3) & set(c2)) if LI["vindue"][0] <= d <= LI["vindue"][1]]
        if vin:
            front = float(np.mean([c2[d] - b3[d] for d in vin])); bag = float(np.mean([a10[d] - c2[d] for d in vin]))
            sammensaetning = dict(front_2y_3m=round(front, 4), bag_10y_2y=round(bag, 4), n_dage=len(vin))
            pol.append(("Kurve = front (2y-3m) + bag (10y-2y)", f"{front + bag:+.2f} = {front:+.2f} + {bag:+.2f}pp (trailing, {len(vin)} dage)"))
            if d1 and d3mo:
                e1, f3 = dict(d1), dict(d3mo)
                vn = [d for d in vin if d in e1 and d in f3]
                if vn:
                    ntfs = float(np.mean([2 * c2[d] - e1[d] - f3[d] for d in vn]))
                    sammensaetning["ntfs_approks"] = round(ntfs, 4)
                    pol.append(("Near-term forward spread (approks.)", f"{ntfs:+.2f}pp (2*2y - 1y - 3m; negativ = lempelser prissat)"))
    forv_txt = None                                          # review 2026-10-27: forventningsdel mod term-praemie
    if tp10 is not None:
        paa = lambda s: ([v for d, v in (s or []) if d <= tp_dato] or [None])[-1]       # samme dag som TP, ellers foer
        b3_tp, c3_tp, forv = paa(_tbd), paa(d3mo), _y - tp10
        if b3_tp is not None:
            kurve_tp = _y - b3_tp
            forv_txt = (f"Kurvens sammensaetning (Kim-Wright, {tp_dato}): 10Y {_y:.2f} = term-praemie {tp10:.2f} + forventet "
                        f"{forv:.2f}. Forventningsdelen minus 3m er {forv - b3_tp:+.2f}pp mod DTB3 (diskonto, modellens konvention)"
                        + (f" og {forv - c3_tp:+.2f}pp mod DGS3MO (CMT)" if c3_tp is not None else "")
                        + (f"; {tp10 / kurve_tp * 100:.0f} % af kurven den dag ({kurve_tp:+.2f}pp) er term-praemie"
                           if kurve_tp > 0 and tp10 > 0 else "")
                        + ". Litteraturen (Rosenberg-Maurer 2008) finder, at det er forventningsdelen, der forudsiger "
                          "recessioner; modellen laeser kun summen. En ACM-version blev testet og afvist i trin 4 "
                          "(-77,9pp fuld sti, primaert straffen for aarene foer 1961). Kontekst, ikke i P; et forslag "
                          "til raadet ligger i spec2027/udkast/7.")
    print()
    print("   PENGEPOLITIK, INFLATION & KURVENS SAMMENSAETNING   [kontekst — ingen indflydelse paa P]")
    for navn, vaerdi in pol:
        print(f"       {navn:<38}{vaerdi}")
    print("       Rente og inflation indgaar i P via kurven (operationel feature) og via")
    print("       realrate/d_infl i fuldmodellen — testet, ikke bestaaet (trin 6). Linjerne")
    print("       her er kontekst: hverken i P eller i hovedbogens antaendings-kolonne.")

    # F36: kreditkanalen ud over HY OAS
    kredit = []
    ebp_f = snap / "EBP.csv"
    if ebp_f.exists():
        with ebp_f.open(encoding="utf-8-sig") as fh:
            er = [r for r in csv.DictReader(fh) if r.get("ebp") not in (None, "", ".")]
        if er:
            kredit.append(("Excess bond premium (GZ/Fed Board)", f"{float(er[-1]['ebp']):+.2f}pp ({er[-1]['date'][:7]}); "
                           f"GZ-spaend {float(er[-1]['gz_spread']):.2f}pp; ekstern in-sample-probit {float(er[-1]['est_prob'])*100:.0f}% "
                           "(andet maal, ikke sammenlignelig med P)"))
    baa = seneste_obs(snap, meta, "BAA10Y")
    if baa:
        kredit.append(("Baa minus 10Y (Moody's)", f"{baa[1]:.2f}pp ({baa[0]})"))
    if kredit:
        print("   KREDIT UD OVER HY OAS   [kontekst — aaben praeregistreringskandidat (EBP), ikke i P]")
        for navn, vaerdi in kredit:
            print(f"       {navn:<38}{vaerdi}")
    # Kontekst-protokollen 2026-10-24: raavarer, kreditkort og bolig i USA (spine.KONTEKST_BLOKKE)
    kusa = kontekst_usa(snap)
    for blok in kusa.values():
        print(f"   {blok['titel']}   [kontekst-protokol 2026-10-24 — ingen indflydelse paa P; ingen taerskler, ingen taelling]")
        for r in blok["linjer"]:
            print(f"       {r['navn']:<38}{r['tekst']}")
    if kusa:
        print("       Raavarer, kreditkort og bolig er ikke features: feature-soegningen er lukket (v5.0-raadet); en test")
        print("       i P kraever ny oekonomisk begrundelse + raadsmandat + forseglet spec foer koersel (RAADETS_V501 §6).")
    # F39: NBER-komiteens egne indikatorer (coincident — anden disciplin), uden taerskler og taellinger
    nber_ind = []
    for sid, navn, fodnote in (("PAYEMS", "Loenmodtagerbeskaeftigelse", "foederale engangsbevaegelser kan dominere"),
                               ("CE16OV", "Husstandsbeskaeftigelse", "januar-befolkningskontrol giver spring"),
                               ("INDPRO", "Industriproduktion", ""),
                               ("W875RX1", "Real indkomst ekskl. overfoersler", ""),
                               ("PCEC96", "Realt privatforbrug", ""),
                               ("CMRMTSPL", "Realt engros/detail/industri-salg", "")):
        s = fred_valgfri(snap, sid)
        if s:
            k = max(s)
            nber_ind.append(dict(serie=sid, navn=navn, maaned=f"{k[0]}-{k[1]:02d}", yoy=round(yoy(s), 2) if np.isfinite(yoy(s)) else None,
                                 fra_12m_top=round(fra_top12(s), 2), note=fodnote))
    if nber_ind:
        print("   NBER-INDIKATORER (coincident, anden disciplin; ingen taerskler, ingen taelling)")
        for r in nber_ind:
            print(f"       {r['navn']:<38}{r['maaned']}: y/y {fmt(r['yoy'], '+.1f')}%, fra 12m-top {r['fra_12m_top']:+.1f}%"
                  + (f"  ({r['note']})" if r["note"] else ""))

    print("\n6) DOM (skabelon-genereret — overstiger aldrig tallene)")
    if cens:
        dom = (f"CENSURERET: inde i en annonceret recession — onset-sandsynlighed ikke defineret (Kimi R5). "
               f"P {p_op*100:.1f}% printes kun til reference.")
    elif band_excludes_base:
        retning = "under" if p_op < base else "over"
        dom = (f"P er {p_op*100:.1f}% mod basisraten {base*100:.1f}%; baandet "
               f"[{lo*100:.1f}-{hi*100:.1f}%] udelukker basisraten — laesningen er {retning} basisraten.")
    else:
        dom = (f"P er {p_op*100:.1f}% mod basisraten {base*100:.1f}%, men baandet "
               f"[{lo*100:.1f}-{hi*100:.1f}%] indeholder basisraten: "
               f"IKKE SKELNELIG FRA BASISRATEN.")
    print(f"   {dom}")
    fa = op.get("vaerste_fejlalarm")
    if not fa:
        sys.exit("FEJL: weights.json mangler op.vaerste_fejlalarm (aeldre/backup-vaegte?) — koer finalize6.py igen.")
    fa_txt = f"Vaerste fejlalarm i walk-forward: {fa['p']*100:.1f}% ({fa['origin']}) uden onset"
    print(f"   P er betinget af NBER-datering pr. {snap.name}. {fa_txt}\n   staar permanent: "
          "kurveregime-risiko gaelder begge veje. Eksogene chok kan ikke forudsiges.")
    beta = (op.get("raa") or {}).get("beta_curve_pr_pp")
    pr10 = abs(beta) * p_op * (1 - p_op) * 0.1 * 100 if beta else NA          # pp pr. 10bp
    dsti = (diag or {}).get("sti") or {}
    hist_sti = (f"Historisk (diagnostik): P var under sin top ved sidste origin foer onset i {dsti['n_under_top']}/{dsti['n_onsets']} "
                f"onsets — median {dsti['median_fald_pp']:.0f}pp fald, median {dsti['median_mdr_top_til_onset']} mdr fra top til onset."
                if dsti.get("n_onsets") and dsti.get("median_fald_pp") is not None
                else "Historiske onsets er ofte sket i re-steepening-fasen.")
    a07 = next((a for a in (diag or {}).get("pre_onset_analoger", []) if a["origin"] == "2007Q4"), None)
    if a07:
        hist_sti += (f" 2007Q4: P {a07['p']*100:.1f}% [{a07['baand'][0]*100:.1f}-{a07['baand'][1]*100:.1f}%], "
                     f"{a07['dom']} — onset kom maaneden efter.")
    sti_txt = (f"Modellen laeser kurvens NIVEAU; {x['curve']:+.2f}pp behandles som {x['curve']:+.2f}pp uden forhistorie. "
               f"Seneste inversion: {inv_note}. {hist_sti} Balance-sheet-drevne recessioner uden frisk "
               "inversion er usynlige for modellen.")
    lang_ende = (f"En stigning i den lange ende saenker P mekanisk (ca. {fmt(pr10, '.1f')}pp pr. 10bp ved nuvaerende kurve); "
                 "atlassets kanal 5 laeser samme bevaegelse som risiko. Dommen er uaendret.")
    print(f"   STI-ADVARSEL (raadsreview 2026-08, enstemmig): {sti_txt}")
    print(f"   LANG ENDE (F10): {lang_ende}")
    if forv_txt:
        print(f"   FORVENTNINGSDEL: {forv_txt}")

    # ---- 7) hovedbogen: diff mod sidste log (med dekomposition) + evt. --log-append ----
    logf = HERE.parent / "LOG.md"
    aktive = [navn for navn, aktiv, _, _ in mon if aktiv is True]
    dom_ord = ("censureret" if cens else "under basisraten" if (band_excludes_base and p_op < base)
               else "over basisraten" if band_excludes_base else "ikke skelnelig")
    print("\n7) HOVEDBOG (LOG.md)")
    aendring = None
    sidste_ae = forr
    if sidste_ae:
        dP = p_op * 100 - tal_af(sidste_ae["P"])
        dK = x["curve"] - (tal_af(sidste_ae["kurve"]) or 0.0)
        print(f"   Sidste log {sidste_ae['logget']}: P {sidste_ae['P']}, kurve {sidste_ae['kurve']}")
        print(f"   AENDRING SIDEN SIDST: P {dP:+.1f}pp, kurve {dK:+.2f}pp")
        aendring = dict(fra=sidste_ae["logget"], dP_pp=round(dP, 2), dK_pp=round(dK, 4))
        gl_snap = C.RAW / sidste_ae.get("snapshot", "")
        if sidste_ae.get("snapshot") and (gl_snap / "meta.json").exists() and (gl_snap / "GS10.csv").exists():
            gl = C.live_kurve(gl_snap)                                       # F10: hvert bens bidrag ved frosne vaegte
            d10_ = LI["y10"] - gl["y10"]; d3_ = LI["tb3"] - gl["tb3"]
            pf = lambda c: float(p_of({"curve": c}, op["features"], op["mu"], op["sd"], op["w"]))
            p_gl = pf(gl["curve"])
            bidrag_10 = pf(gl["curve"] + d10_) - p_gl
            bidrag_3 = p_op - p_gl - bidrag_10
            maerke = kurve_maerke(d10_, d3_, dK)
            aendring.update(d10Y_pp=round(d10_, 4), d3m_pp=round(d3_, 4), bidrag_10Y_pp=round(bidrag_10 * 100, 2),
                            bidrag_3m_pp=round(bidrag_3 * 100, 2), maerke=maerke, input_foer=gl["kilde"])
            tp_gl, tp_ny = C.read_fred_daily(gl_snap, "THREEFYTP10"), _tpd
            dtp_txt = ""
            if tp_gl and tp_ny:
                aendring["dTP_pp"] = round(tp_ny[-1][1] - tp_gl[-1][1], 4)
                aendring["dTP_datoer"] = [tp_gl[-1][0], tp_ny[-1][0]]
                dtp_txt = f" (heraf Kim-Wright-termpraemie {aendring['dTP_pp']:+.2f}pp, {tp_gl[-1][0]}..{tp_ny[-1][0]})"
            print(f"   DEKOMPOSITION (frosne vaegte): kurve {dK:+.2f} = d10Y {d10_:+.2f}{dtp_txt} - d3m {d3_:+.2f}pp -> "
                  f"P-bidrag 10Y {bidrag_10*100:+.1f}pp, 3m {bidrag_3*100:+.1f}pp — {maerke}"
                  + ("" if gl["kilde"] == LI["kilde"] else f" [forrige raekke: {gl['kilde']} input]"))
    else:
        print("   Foerste laesning — ingen historik endnu.")
    ref_tal = (((diag or {}).get("oracle_fri") or {}).get("alle_live_publicerbare") or {}).get("improvement")
    if ref_tal is not None:
        print(f"   Hovedbogens referencetal (BEDOEMMELSESNOEGLE.md §3): +{ref_tal}% (diagnostik 4.5, realtidscensurering) — "
              f"ikke +{op['wf_improvement']:.1f}%. Ingen samlet score foer mindst 3 komplette cyklusblokke.")

    # --log-blokeringer (samlet, saa de staar i JSON'en ogsaa)
    blok = []
    if rekal_paakraevet:
        blok.append("rekalibrering paakraevet (§3.2) — koer finalize6.py && diagnostik.py, derefter motor.py --log")
    nyeste = sorted(d for d in C.RAW.iterdir() if d.is_dir())[-1]
    if age > STALE_DAYS:                                    # PR #1: --allow-stale gaelder kun aflaesningen
        blok.append(f"snapshottet er {age} dage gammelt (>{STALE_DAYS}) — --allow-stale gaelder kun aflaesningen; "
                    "hovedbogen faar kun friske data, koer fetch.py")
    if nyeste != snap:
        blok.append(f"laesningen bygger paa {snap.name}, men nyeste snapshot-mappe er {nyeste.name} "
                    "(ukomplet/ubrugelig) — hovedbogen faar kun friske data; koer fetch.py igen")
    if synk:
        blok.append("ANNONCERINGSTABEL UDE AF SYNK MED USREC — tilfoej/ret raekken (dato fra nber.org), §3.2b")
    if not diag or diag.get("manifest_hash") != W.get("manifest_hash") or (W.get("snapshot") and diag.get("snapshot") != W.get("snapshot")):
        blok.append("diagnostik.json passer ikke til kalibreringen i drift (F51/F26) — koer diagnostik.py")
    idag_s = I.isoformat()
    if rows and rows[-1]["logget"][:7] == idag_s[:7]:
        blok.append(f"{idag_s[:7]} er allerede logget ({rows[-1]['logget']}) — historiske raekker roeres ikke")
    uden_for = None
    lv_fra, lv_til = ((date(I.year, I.month, 1) + timedelta(days=LOGDAG_VINDUE[0] - 1), None) if LOGDAG_VINDUE
                      else logvindue(I))
    i_vindue = (LOGDAG_VINDUE[0] <= I.day <= LOGDAG_VINDUE[1]) if LOGDAG_VINDUE else (lv_fra <= I <= lv_til)
    sidste_rigtige = next((r for r in reversed(rows) if tal_af(r.get("P"), 0.01) is not None), None)
    if any(r.get("snapshot") == snap.name for r in rows) or (sidste_rigtige and snap.name <= sidste_rigtige["logget"][:10]):
        blok.append(f"snapshot {snap.name} er allerede grundlag for / aeldre end forrige hovedbogsraekke "
                    f"({sidste_rigtige['logget'] if sidste_rigtige else '?'}) — hovedbogen faar kun friske data; koer fetch.py")
    if i_vindue and not LOGDAG_VINDUE and D_las < lv_fra:
        blok.append(f"snapshot {snap.name} er hentet foer logvinduet ({lv_fra}) — G3.6: koer fetch.py i vinduet foer --log")
    if logf.exists() and logf.stat().st_size and not logf.read_bytes().endswith(b"\n"):
        blok.append("LOG.md ender ikke med et linjeskift — ret filen foer --log (en ny raekke ville klistres paa den forrige)")
    if not i_vindue:
        if "--log-uden-for-vindue" in sys.argv:
            k = sys.argv.index("--log-uden-for-vindue")
            uden_for = sys.argv[k + 1] if len(sys.argv) > k + 1 and not sys.argv[k + 1].startswith("-") else ""
            if not uden_for.strip():
                blok.append('--log-uden-for-vindue kraever en begrundelse: --log-uden-for-vindue "<hvorfor>"')
        else:
            blok.append(f"{I} er uden for logvinduet "
                        + (f"dag {LOGDAG_VINDUE[0]}-{LOGDAG_VINDUE[1]}" if LOGDAG_VINDUE else f"{lv_fra}..{lv_til}")
                        + " (G3.6, BEDOEMMELSESNOEGLE.md) — "
                        "mellemlaesninger logges aldrig; undtagelse kun med --log-uden-for-vindue \"<begrundelse>\"")

    if "--log" in sys.argv:
        if blok:
            for b in blok:
                print(f"   --log AFVIST: {b}.")
        else:
            # G3.6: manglende maaneder mellem sidste raekke og denne staar som eksplicitte 'ikke logget'-raekker
            mangler = []
            if rows:
                ly, lm = int(rows[-1]["logget"][:4]), int(rows[-1]["logget"][5:7])
                k = kal_minus((ly, lm), -1)
                while k < (I.year, I.month):
                    mangler.append(f"{k[0]}-{k[1]:02d}")
                    k = kal_minus(k, -1)
            noter = []
            if LI["kilde"] == "daglig" and not any("input: daglig" in r.get("note", "") for r in rows):
                noter.append("input: daglig (kurve = trailing maaned DGS10-DTB3; foer: GS10-TB3MS maanedssnit)")
            kh = W.get("manifest_hash", "")
            # §3.4 bro-raekke: foerste raekke under et nyt manifest printer P under gamle OG nye vaegte ved samme input.
            # F48: den gamle kalibrering er den der STAAR i sidste raekke (fallback: weights.json's forrige_manifest)
            sidste_kal = next((r.get("kalibrering") for r in reversed(rows) if r.get("kalibrering")), "") if rows else ""
            if kh and sidste_kal != kh and (sidste_kal or W.get("forrige_manifest")):
                gl_h = sidste_kal or W["forrige_manifest"]
                fm_f = HERE / "kalibreringer" / f"manifest_{gl_h}.json"
                if fm_f.exists():
                    gl_m = json.loads(fm_f.read_text(encoding="utf-8"))
                    glm = gl_m["modeller"]["curve_only"]
                    p_gl = float(p_of(x, glm["features"], glm["mu"], glm["sd"], glm["w"]))
                    noter.append(f"bro: P(v{gl_m.get('version', '?')} {gl_h})={p_gl*100:.1f}% / "
                                 f"P(v{W.get('version', '?')} {kh})={p_op*100:.1f}% ved identiske inputs"
                                 + (f"; trigger: {W['trigger']}" if W.get("trigger") else ""))
            elif kh and sidste_kal == kh and (W.get("koersel") or {}).get("manifest_genbrugt"):
                # G4.2: en trigger-koersel der genbrugte manifestet skal stadig efterlade et spor i hovedbogen — een gang
                ko = W["koersel"]
                tag = f"koersel {ko.get('utc', '')}"
                if ko.get("utc") and not any(tag in r.get("note", "") for r in rows):
                    noter.append(f"{tag}: {ko.get('trigger', '')}")
            ov = meta.get("spine", {}).get("outlier_override")
            if ov:
                noter.append(f"--accept-outlier: {ov.get('begrundelse', '')} ({'; '.join(ov.get('observationer', []))})")
            else:                                           # F31: accept i et tidligere snapshot, endnu ikke logget
                nye_acc = {k_: v_ for k_, v_ in meta.get("spine", {}).get("outliers_accepteret", {}).items()
                           if not sidst_logget or v_.get("accepteret", "") > sidst_logget}
                if nye_acc:
                    noter.append("--accept-outlier: " + "; ".join(f"{k_}: {v_.get('observation', '')} ({v_.get('begrundelse', '')})"
                                                              for k_, v_ in sorted(nye_acc.items())))
            nh = noegle_hash(logf)
            if nh and not any(f"noegle {nh}" in r.get("note", "") for r in rows):
                noter.append(f"noegle {nh} (BEDOEMMELSESNOEGLE.md)")
            if utilg:
                noter.append("monitor utilgaengelig: " + ", ".join(sorted(set(utilg))))
            if man_noter:
                noter.append("manuel: " + ", ".join(man_noter))
            if uden_for:
                noter.append(f"uden for logvindue: {uden_for}")
            vindue = maanedsvindue(I)
            inp = (f"daglig {LI['vindue'][0]}..{LI['vindue'][1]} ({LI['n_dage']}d)" if LI["kilde"] == "daglig"
                   else f"maanedlig {LI['maanedlig']['maaned']}")
            # 'ikke logget'-raekker har ingen P og derfor ingen kalibrering (noeglens pkt. 1e: kolonnen er tom)
            ekstra_tom = " | | |" if p_us else ""             # RAADETS_2027 §3.3/§4: tre uscorede celler fra 2027-09
            linjer = [f"| {m} (ikke logget) | – | ikke logget | | | | | | ingen raekke i logvinduet | | | | |{ekstra_tom}" for m in mangler]
            linjer.append(f"| {idag_s} | {snap.name} | {p_op*100:.1f}% | {lo*100:.1f}-{hi*100:.1f}% | "
                          f"{base*100:.1f}% | {dom_ord} | {x['curve']:+.2f} | "
                          f"{ren_note(', '.join(aktive)) if aktive else 'ingen'} | {ren_note('; '.join(noter))} | {kh} | "
                          f"{vindue} | {ren_note(inp)} | {p_maanedlig*100:.1f}% |"
                          + (f" {p_us['p_maanedligt_fit']*100:.1f}% | {p_us['p_start_1953Q2']*100:.1f}% | "
                             f"{p_us['p_start_1960Q1']*100:.1f}% |" if p_us else ""))
            with logf.open("a", encoding="utf-8", newline="\n") as fh:
                for ln in linjer:
                    fh.write(ln + "\n")
            # fuld record pr. raekke (alt der skal til for at score den uden at laese koden)
            rec = dict(logget=idag_s, snapshot=snap.name, snapshot_sha256=meta["snapshot_sha256"], manifest=kh,
                       version=W.get("version"), p=round(p_op, 6), baand=[round(float(lo), 6), round(float(hi), 6)],
                       basisrate=base, dom=dom_ord, kurve=round(x["curve"], 4), vindue=vindue, input=inp,
                       live_input=dict(kilde=LI["kilde"], vindue=LI.get("vindue"), n_dage=LI.get("n_dage"),
                                       y10=round(LI["y10"], 4), tb3=round(LI["tb3"], 4)),
                       p_maanedlig=round(p_maanedlig, 6), maanedlig=LI["maanedlig"], parret=parret,
                       antaending=aktive, monitors=[dict(navn=n, aktiv=a if a in (True, False) else None, vaerdi=v) for n, a, v, _ in mon],
                       scenarie=[dict(navn=n, aktiv=a if a in (True, False) else None, vaerdi=v) for n, a, v, _ in scen],
                       censureret=bool(cens), noter=noter, noegle=nh, ikke_logget_foer=mangler,
                       kontekst_usa=kusa, spot_kurve=sk)       # kontekst-protokollen 2026-10-24: uscoret, fremadrettet
            if p_us:                                        # RAADETS_2027 §3.3/§4/§10.4 (spec 4): uscorede felter
                rec.update({k: round(v, 6) for k, v in p_us.items()})
                if cens:
                    rec["uscoret_censur"] = dict(p=round(p_op, 6), p_maanedlig=round(p_maanedlig, 6),
                                                 p_maanedligt_fit=round(p_us["p_maanedligt_fit"], 6), vindue=vindue,
                                                 note="uscoret (RAADETS_2027 §10.4): raekken scores ikke (noeglen §1 d); "
                                                      "P og det endelige udfald foeres")
            with (logf.parent / "hovedbog.jsonl").open("a", encoding="utf-8", newline="\n") as fh:
                fh.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n")
            print(f"   LOGGET som raekke {len(rows) + len(mangler) + 1}: {idag_s}, P {p_op*100:.1f}%, dom '{dom_ord}'."
                  + (f" ({len(mangler)} 'ikke logget'-raekke(r) foer: {', '.join(mangler)})" if mangler else ""))
    elif blok:
        print("   (en --log i dag ville blive afvist: " + "; ".join(blok) + ")")

    # ---- datastatus (2026-10-27): er hver serie saa ny, som kilden tillader? ----
    datastatus = [d_ for d_ in (SP.datastatus(sid, v.get("last"), D_las) for sid, v in sorted(meta.get("series", {}).items())) if d_]
    for d_ in datastatus:
        d_["rolle"] = (SP.SERIER.get(d_["serie"]) or (SP.EKSTERNE.get(d_["serie"], {}).get("rolle"),))[0]
    forsinkede = [d_ for d_ in datastatus if d_["status"] == "forsinket"]
    print("\nDATASTATUS (udgivelseskalender, as-of snapshottet):")
    if forsinkede:
        for d_ in forsinkede:
            print(f"   FORSINKET {d_['serie']:<16} {d_['navn']}: {d_['tekst']}")
    else:
        print(f"   Ingen forsinkede serier: alle {len(datastatus)} er saa nye, som kilderne normalt udgiver dem.")

    # ---- 8) diagnostik (RAADETS_V501 §4): printes, aendrer intet ----
    print("\n8) DIAGNOSTIK (RAADETS_V501 §4 — printes ved siden af, aendrer hverken gate, vaegte eller dom)")
    if not diag:
        print("   diagnostik.json mangler — koer python diagnostik.py efter rekalibrering.")
    else:
        if diag.get("manifest_hash") != W.get("manifest_hash"):
            print(f"   ADVARSEL: diagnostik.json er fra kalibrering {diag.get('manifest_hash')}, vaegtene er {W.get('manifest_hash')} — koer diagnostik.py igen.")
        if W.get("snapshot") and diag.get("snapshot") != W.get("snapshot"):
            print(f"   ADVARSEL: diagnostik.json er beregnet paa snapshot {diag.get('snapshot')}, kalibreringen paa {W['snapshot']} (F26) — koer diagnostik.py igen.")
        pr = diag["primaer"]
        print(f"   4.1 Episode-tabel (curve-only wf, {pr['n']} origins; bidrag summerer til +{diag['episode_tabel']['sum_bidrag_pp']}pp):")
        print(f"       {'episode':<24}{'n':>4}{'pos':>5}{'bidrag':>9}{'max P':>8}")
        for r in diag["episode_tabel"]["raekker"]:
            print(f"       {r['episode']:<24}{r['n']:>4}{r['n_pos']:>5}{r['bidrag_pp']:>+8.2f}p{r['max_p']*100:>7.1f}%")
        nb = diag["episode_tabel"]["negative_pr_blok"]
        print("       negative pr. blok (op til onset): " + "; ".join(f"{b['blok']} {b['origins']} {b['bidrag_pp']:+.2f}pp (max {b['max_p']*100:.0f}%)" for b in nb))
        lo8 = diag["loeo"]
        print(f"   4.2 LOEO (sensitivitet): {len(lo8['blokke'])} blokke, median {lo8['median']:+.1f}%, min {lo8['min']:+.1f}%"
              + (f", udefineret {lo8['udefinerede']}" if lo8.get("udefinerede") else "") + " — aldrig co-primaer")
        bt = diag["domsregler_backtest"]
        print(f"   4.3 Domsregler backtestet ({bt['n_origins']} origins x {bt['n_draws']} traek): baandreglen skelnelig {bt['baand_skelnelig']}, "
              f"parret {bt['parret_skelnelig']}, uenige {bt['uenige']} ({bt['uenighedsrate']*100:.1f} %)"
              + (": " + ", ".join(u["origin"] for u in bt["uenige_origins"][:6]) + (" ..." if len(bt["uenige_origins"]) > 6 else "") if bt["uenige"] else ""))
        print("       Ingen automatisk migration af domsreglen: et skift er en separat raadsbeslutning mod praeregistrerede kriterier.")
        pl = diag["parret_loss_bootstrap"]
        print(f"   4.4 Historisk parret loss-bootstrap: middel {pl['middel_pp']:+.3f}, 90 %-interval [{pl['interval_90'][0]:+.3f}, {pl['interval_90'][1]:+.3f}], "
              f"P(<=0) = {pl['andel_ikke_positiv']:.3f}  (skill-diagnostik ved siden af MDE)")
        oc = diag["oracle_fri"]; a = oc["additional_live_publishable"]
        print(f"   4.5 Oracle-fri (censurering som af origin-datoen, modellens egen label): alle live-publicerbare "
              f"{oc['alle_live_publicerbare']['n']} origins +{oc['alle_live_publicerbare']['improvement']}% | ekskl. {a['n']} additional "
              f"live-publishable origins +{oc['ekskl_additional']['improvement']}% (max P blandt dem {a['max_p']*100:.0f}%). Tolkes i tandem.")
        s73 = diag["skill_73"]
        print(f"   §7.3 Trunkeret panel +{s73['trunkeret_panel']['improvement'] if s73.get('trunkeret_panel') else '?'}% | udvidet: faelles origins "
              f"+{s73['udvidet_faelles_origins']['improvement']}%, tilfoejede " + ", ".join(f"{t['origin']} P={t['p']*100:.0f}% Y={int(t['Y'])}" for t in s73["tilfoejede_origins"]))
        print(f"   §3.6 Baseline: publiceret = poolet basisrate (+{pr['improvement']}%); expanding-intercept-udgave +{pr['improvement_expanding']}% (ekstra kolonne, aendrer ikke gaten)")
        if diag.get("start_sensitivitet"):
            ss_ = diag["start_sensitivitet"]
            print("   F34 Universstart (ved kalibreringens bro-input kurve "
                  + f"{ss_.get('input', {}).get('curve', '?')}pp, ikke dagens): "
                  + "; ".join(f"{k} P {v['P']*100:.1f}% / basis {v['basisrate']*100:.1f}%"
                              for k, v in ss_.items() if k != "input") + " (protokol: 1947Q2 — til raadet foer sept. 2027)")
        if diag.get("maanedlig_parret"):
            for ln in P27.parret_linjer(diag["maanedlig_parret"]):
                print(ln)
        if diag.get("styrke"):
            st = diag["styrke"]
            print(f"   G3.2 Hovedbogens styrke: 80 % styrke kraever ca. {st['blokke_80pct']} cyklusblokke (ca. {st['aar_80pct']} aar). "
                  "Hovedbogen er den eneste fuldt prospektive test — men statistisk svag (BEDOEMMELSESNOEGLE.md).")

    if "--json" in sys.argv:
        k = sys.argv.index("--json")
        har_sti = len(sys.argv) > k + 1 and not sys.argv[k + 1].startswith("-")
        ud = Path(sys.argv[k + 1]) if har_sti else HERE.parent / "dashboard.json"

        bmj = [dict(navn="intercept (basisrate)", wf=0.0, live_p=round(base, 6), status=None, panel=None),
               dict(navn="curve-only-logit (NY Fed-stil-bm.)",
                    wf=W["benchmarks"]["curve_only"]["wf_improvement"], live_p=round(p_curve, 6),
                    status="OPERATIONEL" if W["operationel"] == "curve_only" else None,
                    panel=f"fuld sti t.o.m. {op.get('estimering_slut', '?')}",
                    note="fast lambda=1 (arvet fra v4); fuld-sti-valg mellem to modeller, ikke nested"
                         + (f"; {tandem_txt}" if tandem_txt else "")),
               dict(navn="fuldmodel (5 features)", wf=fm.get("wf_improvement"),
                    live_p=round(p_full, 6) if fm_ok else None, status=fm["status"] if fm_ok else fm_grund,
                    panel=f"fuld sti t.o.m. {op.get('estimering_slut', '?')}")]
        if (cc or ca) and trunk.get("improvement") is not None:
            bmj.append(dict(navn="curve-only, samme panel (reference)", wf=trunk["improvement"], live_p=None,
                            status="reference for de afviste kandidater", panel="t.o.m. 2023Q2"))
        for navn, blk in (("curve+cape (praereg. v5.1-test)", cc), ("curve+awh (praereg. v5.2-test)", ca)):
            if blk:
                bmj.append(dict(navn=navn, wf=blk["wf_improvement"], live_p=None, status=blk["status"], panel="t.o.m. 2023Q2"))
        if p_arv is not None or arv_grund:
            bmj.append(dict(navn="v4-arv (teknisk label)", wf=None, live_p=round(p_arv, 6) if p_arv is not None else None,
                            status="andet maal - arv" if p_arv is not None else arv_grund, panel=None))
        bmj.append(dict(navn="realtids-Sahm (trigger 0,50)", wf=None, live_p=None,
                        vaerdi=sahm[1] if sahm else None, status="naerhorisont-signal", panel=None))
        bmj.append(dict(navn="Chauvet-Piger nowcast", wf=None, live_p=round(cp[1] / 100, 6) if cp else None,
                        status="coincident, publiceringslag - anden disciplin", panel=None))
        if em:
            bmj.append(dict(navn="Estrella-Mishkin-probit (NY Fed-koef.)", wf=None, live_p=em["p"],
                            status=f"andet maal: i recession om 12 mdr; beregnet paa trailing 10y-3m (CMT) {em['spread']:+.2f}pp, "
                                   "ikke NY Fed's publicerede tal (NY Fed bruger maanedssnit)",
                            panel=None, spread=em["spread"]))

        hb = laes_hovedbog(logf)
        for r in hb:
            b = [tal_af(v, 0.01) for v in r.get("baand", "").split("-")]
            r["p_tal"] = tal_af(r.get("P"), 0.01)
            r["baand_tal"] = b if len(b) == 2 and None not in b else None
            r["basisrate_tal"] = tal_af(r.get("basisrate"), 0.01)
            r["kurve_tal"] = tal_af(r.get("kurve"))
            r["p_maanedlig_tal"] = tal_af(r.get("P_maanedlig"), 0.01)
            for k_, n_ in (("P_maanedligt_fit", "p_maanedligt_fit_tal"), ("P_1953Q2", "p_1953Q2_tal"), ("P_1960Q1", "p_1960Q1_tal")):
                if r.get(k_):                               # RAADETS_2027: kun raekker under en 2027-kalibrering
                    r[n_] = tal_af(r[k_], 0.01)

        def mrow(n, a, v, s):
            return dict(navn=n, tilstand=("aktiv" if a is True else "utilgaengelig" if a == "?" else
                                          "kontekst" if a is None else "inaktiv"), vaerdi=v, klasse=s)
        data = dict(
            version=W.get("version", "5.0"), manifest_hash=W.get("manifest_hash"),
            forrige_manifest=W.get("forrige_manifest"), raa=op.get("raa"), bro=W.get("bro"),
            gate=W.get("gate"), stale=meta.get("stale"), diagnostik=diag,
            live_input=dict(kilde=LI["kilde"], vindue=LI.get("vindue"), n_dage=LI.get("n_dage"),
                            curve=round(LI["curve"], 4), y10=round(LI["y10"], 4), tb3=round(LI["tb3"], 4),
                            y10_seneste=LI.get("y10_seneste"), tb3_seneste=LI.get("tb3_seneste"),
                            maanedlig=LI["maanedlig"], p_maanedlig=round(p_maanedlig, 6),
                            fed_funds=dict(vaerdi=ff_v, dato=ff_dato, kilde=ff_kilde),
                            sammensaetning=sammensaetning,
                            konvention=dict(kurve_cmt=em["spread"], tekst=konv_txt) if konv_txt else None),
            trigger=W.get("trigger"), delta_vs_forrige=W.get("delta_vs_forrige"), koersel=W.get("koersel"),
            rekalibrering_paakraevet=rekal_json,
            snapshot=snap.name, snapshot_hash=meta["snapshot_sha256"][:10],
            model="curve-only-logit" if W["operationel"] == "curve_only" else "fuldmodel",
            label=W["label_tekst"], kalibreret=W["created_utc"][:10],
            n_obs=W["n_obs"], n_episoder=W["n_episoder"],
            wf_log_loss=op["wf_improvement"], wf_brier=op["wf_brier"],
            wf_note="fast lambda=1 (arvet fra v4); fuld-sti-valg mellem to modeller, ikke nested (G1.1/G1.2)",
            skill_saetning=skill_tekst,
            p=round(p_op, 6), baand=[round(float(lo), 6), round(float(hi), 6)],
            basisrate=base, baand_udelukker_basisrate=bool(band_excludes_base),
            ratio=round(p_op / base, 4) if band_excludes_base else None,
            baand_fodnote=W["band"]["fodnote"], dom=dom, dom_ord=dom_ord, parret=parret,
            censureret=dict(aktiv=bool(cens), onset=f"{cens[0] // 12}-{cens[0] % 12 + 1:02d}" if cens else None),
            inputs=[dict(navn=NAVN[f], vaerdi=round(x[f], 4) if np.isfinite(x[f]) else None,
                         z=round(z_af(f), 4) if np.isfinite(z_af(f)) else None,
                         operationel=f in op["features"]) for f in C.F5],
            dd_kilde=dd_kilde,
            benchmarks=bmj,
            monitors=[mrow(*m) for m in mon] + [mrow(*m) for m in kontekst],
            scenarie=[mrow(*m) for m in scen],
            forudsaetninger=[mrow(*m) for m in forud],
            market_conditions=[dict(navn=n, vaerdi=v) for n, v in mc],
            pengepolitik=[dict(navn=n, vaerdi=v) for n, v in pol],
            kredit=[dict(navn=n, vaerdi=v) for n, v in kredit],
            nber_indikatorer=nber_ind,
            kontekst_usa=kusa, spot_kurve=sk,
            manual_friskhed=friskhed,
            utilgaengelige=sorted(set(utilg)),
            datastatus=datastatus,
            sti=sti, maanedens_aendring=aendring,
            advarsler=dict(vaerste_fejlalarm=fa, sti_advarsel=sti_txt, lang_ende=lang_ende, forventningsdel=forv_txt,
                           eksogen="Eksogene chok kan ikke forudsiges."),
            hovedbog=hb,
            hovedbog_reference=dict(improvement=ref_tal, kilde="diagnostik 4.5 alle live-publicerbare (realtidscensurering)",
                                    note="ikke wf_log_loss — se BEDOEMMELSESNOEGLE.md §3"),
            hovedbog_note="Den eneste fuldt prospektive test — beskytter mod look-ahead, men statistisk svag: der kraeves "
                          "mange komplette konjunkturcykler foer den kan skelne modellen fra basisraten (BEDOEMMELSESNOEGLE.md). "
                          "Vises uden samlet score eller dom.",
            noegle=noegle_hash(logf),
        )
        if p_us:                                            # RAADETS_2027 §3.3/§4: kun under en 2027-kalibrering
            data["uscorede"] = dict({k: round(v, 6) for k, v in p_us.items()},
                                    note="uscorede felter (RAADETS_2027 §3.3/§4); aldrig i P, baand eller dom")
        with ud.open("w", encoding="utf-8", newline="\n") as fh:          # LF paa alle platforme (CI-replay)
            fh.write(json.dumps(endelig(data), indent=2, ensure_ascii=False, allow_nan=False) + chr(10))
        print(f"{chr(10)}   JSON skrevet: {ud}  ({len(hb)} hovedbogsraekker)")


if __name__ == "__main__":
    main()
