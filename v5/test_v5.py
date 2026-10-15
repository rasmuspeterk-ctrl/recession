#!/usr/bin/env python3
"""
test_v5.py — deterministisk testsuite for v5-kaeden (stdlib unittest, ingen netvaerk).

Daekker praecis de mekanismer kode-reviewet 2026-09-09 fandt fejl i: fetch's
snapshot-livscyklus (.ny/.ukomplet, retry, diff-markering), komplethedsgaten,
finalize6's permanente linjer og promotion-bevaring, motor's --log-guards og
debate.py's arkiv-layout. Alle tests koerer i temp-mapper; rigtige snapshots
laeses kun (kopieres), weights.json/LOG.md roeres aldrig.

Fra kode-reviewet 2026-10-15 (F1-F60, G1-G4): klasserne Test1015* (rolletabel, licensfiler, forklaret
origin-audit, USREC-krydstjek, logvindue, scenarie-appendiks, censurering m.m.). PR #1 (merget 2026-10-14)
og reviewet er flettet: TestMotor/TestFetchMain bruges af begge saet tests.

Koer:  cd v5 && python -m unittest -v test_v5
"""
import contextlib, hashlib, io, json, os, shutil, sys, tempfile, unittest, urllib.error
from datetime import date, timedelta
from pathlib import Path
from unittest import mock
import numpy as np

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
os.environ.setdefault("OPENROUTER_API_KEY", "test-noegle")     # debate.py kraever en noegle ved import
sys.path.insert(0, str(HERE.parent / "debat"))

import fetch as F
import calibrate as C
import finalize6 as F6
import motor as M
import debate as D
import spine as S
import ablation2_nber as A2
import ablation4_features as A4

REAL_SNAP = sorted(d for d in C.RAW.iterdir() if d.is_dir() and C.snapshot_complete(d))[-1]

def sha(b):
    return hashlib.sha256(b).hexdigest()

def fred_bytes(rows, header="observation_date,X"):
    return (header + "\n" + "\n".join(f"{d},{v}" for d, v in rows) + "\n").encode("utf-8")

ROWS = [("2020-01-01", "1.5"), ("2020-02-01", "1.6"), ("2020-03-01", "1.7")]

def make_snapshot(raw, name, series=None, complete=True, manual=True, meta=True):
    """Minimalt syntetisk snapshot: csv'er for alle 'series', manuelle filer, meta.json."""
    d = raw / name
    d.mkdir(parents=True)
    series = list(C.KRAEVEDE) if series is None else series
    m = {"retrieved_utc": "2026-01-01T00:00:00+00:00", "series": {}, "manual": {}, "complete": complete}
    for sid in series:
        b = fred_bytes(ROWS)
        (d / f"{sid}.csv").write_bytes(b)
        m["series"][sid] = dict(rows=3, first="2020-01-01", last="2020-03-01", last_value="1.7",
                                sha256=sha(b), purpose="test")
    if manual:
        for fn, content in (("shiller.csv", b"Date,SP500,CPI,LTR,CAPE\n1871-01,4.44,12.46,5.32,\n"),
                            ("manual.json", b'{"spx_vs_hi": 0.0, "cape": 42.0, "margin_yoy": 51.5}')):
            (d / fn).write_bytes(content)
            m["manual"][fn] = dict(sha256=sha(content), bytes=len(content))
    m["snapshot_sha256"] = "0" * 64
    if meta:
        (d / "meta.json").write_bytes(json.dumps(m, indent=1).encode("utf-8"))
    return d

def licensfri_kilder(snap):
    """(SP500-csv-bytes, multpl-html) for et snapshot. De licensbegraensede filer (F1/F12) findes kun lokalt; i en
    ren klon (CI) bygges stand-ins af snapshottets COMMITTEDE, afledte data: SP500 som hverdagsvaerdier lig
    maanedsmidlet (Shiller-kopien t.o.m. 2023-07, spine.csv's komposit derefter) fra 2016-10-17 (FRED's vindue
    starter midt i en maaned), og multpl-tabellen fra Yale-CAPE/spine-CAPE. November 2016 er delt (dagene foer
    den 14. lavere, efter hoejere), saa et afkortet vindue fra 2016-11-14 giver en DELVIS maaned der afviger
    > 1 % — praecis november-fejlen (F2) — mens hele maanedens middel er uaendret."""
    sp, html = snap / "SP500.csv", snap / "multpl_cape.html"
    if sp.exists() and html.exists():
        return sp.read_bytes(), html.read_bytes()
    import csv as _csv, calendar as _cal
    maaned_sp, maaned_cape = {}, {}
    with (snap / F.YALE).open(encoding="utf-8-sig") as fh:
        for r in _csv.DictReader(fh):
            k = r["Date"].strip()
            if k <= S.SEAM:
                if r.get("SP500"):
                    maaned_sp[k] = float(r["SP500"])
                if r.get("CAPE"):
                    maaned_cape[k] = float(r["CAPE"])
    with (snap / "spine.csv").open(encoding="utf-8") as fh:
        for r in _csv.DictReader(fh):
            if r["Kilde"] != "shiller":
                maaned_sp[r["Date"]] = float(r["SP500"]); maaned_cape[r["Date"]] = float(r["CAPE"])
    snapdag = date.fromisoformat(snap.name)
    linjer = ["observation_date,SP500"]
    for k in sorted(maaned_sp):
        if k < "2016-10":
            continue
        y, m = int(k[:4]), int(k[5:7])
        dage = [date(y, m, d) for d in range(1, _cal.monthrange(y, m)[1] + 1)
                if date(y, m, d).weekday() < 5 and (k > "2016-10" or d >= 17)]
        v = maaned_sp[k]
        if k == "2016-11":                     # delt maaned: middel uaendret, anden halvdel 2 % over
            n1 = sum(d.day < 14 for d in dage); n2 = len(dage) - n1
            hoej = v * 1.02; lav = (v * len(dage) - hoej * n2) / n1
            linjer += [f"{d},{(lav if d.day < 14 else hoej):.4f}" for d in dage]
        else:
            linjer += [f"{d},{v:.4f}" for d in dage]
    for d in range(1, snapdag.day):            # den loebende maaned (ikke lukket -> indgaar ikke)
        dd = date(snapdag.year, snapdag.month, d)
        if dd.weekday() < 5:
            linjer.append(f"{dd},{list(maaned_sp.values())[-1]:.4f}")
    MON = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
    rk = []
    for y in range(1871, snapdag.year + 1):
        for m in range(1, 13):
            k = f"{y:04d}-{m:02d}"
            if k < "1871-02" or k >= f"{snapdag.year:04d}-{snapdag.month:02d}":
                continue
            rk.append(f"<td>{MON[m - 1]} 1, {y}</td>\n<td>\n&#x2002;\n{maaned_cape.get(k, 15.0):.2f}\n</td>")
    side = "<table>" + "".join(f"<tr>{r}</tr>" for r in reversed(rk)) + "</table>"
    return (chr(10).join(linjer) + chr(10)).encode("utf-8"), side.encode("utf-8")


def quiet():
    return contextlib.redirect_stdout(io.StringIO())

# ============================================================== fetch.py
class TestParseRows(unittest.TestCase):
    def test_ok_og_manglende_springes_over(self):
        b = fred_bytes([("2020-01-01", "1.5"), ("2020-02-01", "."), ("2020-03-01", "")])
        self.assertEqual(F.parse_rows(b), [("2020-01-01", "1.5")])

    def test_html_afvises(self):
        with self.assertRaises(RuntimeError):
            F.parse_rows(b"<html><body>maintenance</body></html>")

    def test_tre_kolonner_afvises(self):
        with self.assertRaises(RuntimeError):
            F.parse_rows(b"a,b,c\n1,2,3\n")


class _Resp:
    def __init__(self, b): self.b = b
    def read(self): return self.b
    def __enter__(self): return self
    def __exit__(self, *a): return False

def _http(code):
    return urllib.error.HTTPError("http://x", code, "err", None, None)

class TestFetchSeriesRetry(unittest.TestCase):
    def _run(self, responses):
        calls = []
        def fake_urlopen(url, timeout=60):
            calls.append(url)
            r = responses.pop(0)
            if isinstance(r, Exception):
                raise r
            return _Resp(r)
        with mock.patch.object(F.time, "sleep", lambda s: None), \
             mock.patch.object(F.urllib.request, "urlopen", fake_urlopen):
            return F.fetch_series("TB3MS"), len(calls)

    def test_429_retries_og_lykkes(self):
        (raw, data), n = self._run([_http(429), fred_bytes(ROWS)])
        self.assertEqual(n, 2); self.assertEqual(len(data), 3)

    def test_404_retries_ikke(self):
        with self.assertRaises(urllib.error.HTTPError):
            self._run([_http(404), fred_bytes(ROWS)])

    def test_misdannet_200_retries(self):
        (raw, data), n = self._run([b"<html>nede</html>", fred_bytes(ROWS)])
        self.assertEqual(n, 2); self.assertEqual(data[0], ("2020-01-01", "1.5"))

    def test_opgiver_efter_tre_forsoeg(self):
        with self.assertRaisesRegex(RuntimeError, "opgivet efter 3"):
            self._run([_http(503), _http(503), b"tom,serie\n"])


class TestDiffMark(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.prev = Path(self.tmp.name)
        self.old = fred_bytes(ROWS)
        (self.prev / "X.csv").write_bytes(self.old)
        self.ps = dict(sha256=sha(self.old), last="2020-03-01", last_value="1.7")
    def tearDown(self): self.tmp.cleanup()

    def cur(self, rows):
        b = fred_bytes(rows); return F.parse_rows(b), dict(sha256=sha(b), last=rows[-1][0], last_value=rows[-1][1])

    def test_uaendret(self):
        data, cur = self.cur(ROWS)
        self.assertEqual(F.diff_mark(self.ps, self.prev, "X", data, cur), "")

    def test_ny_obs(self):
        data, cur = self.cur(ROWS + [("2020-04-01", "1.8")])
        self.assertIn("ny obs", F.diff_mark(self.ps, self.prev, "X", data, cur))

    def test_aendret_sidste_vaerdi(self):
        data, cur = self.cur(ROWS[:2] + [("2020-03-01", "9.9")])
        m = F.diff_mark(self.ps, self.prev, "X", data, cur)
        self.assertIn("AENDRET", m); self.assertIn("REVIDERET", m)

    def test_revideret_historik(self):
        data, cur = self.cur([("2020-01-01", "5.5")] + ROWS[1:] + [("2020-04-01", "1.8")])
        self.assertIn("REVIDERET historik", F.diff_mark(self.ps, self.prev, "X", data, cur))

    def test_meta_mangler_men_fil_findes(self):
        data, cur = self.cur(ROWS)
        self.assertIn("mangler i forrige meta", F.diff_mark(None, self.prev, "X", data, cur))

    def test_helt_ny_serie(self):
        data, cur = self.cur(ROWS)
        self.assertEqual(F.diff_mark(None, self.prev, "NY", data, cur), "  (ny serie)")

    def test_ulaeselig_forrige_fil_crasher_ikke(self):
        (self.prev / "X.csv").write_bytes(b"\xff\xfe\x00garbage")
        data, cur = self.cur(ROWS + [("2020-04-01", "1.8")])
        self.assertIn("forrige fil ulaeselig", F.diff_mark(self.ps, self.prev, "X", data, cur))


class TestDiffRolling(unittest.TestCase):
    """FRED serverer SP500 (~10 aar) og ICE HY OAS (~3 aar) som rullende vinduer: raekker der falder af foran er
    ingen revision (12 af 31 'REVIDERET historik' over de 9 snapshot-overgange var falske). Ikke-rullende serier
    tjekkes stadig strengt, saa en stille afkortning af fx TB3MS alarmerer."""
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.prev = Path(self.tmp.name)
        self.base = [(f"2020-01-{d:02d}", str(1 + d / 10)) for d in range(1, 11)]
        for sid in ("SP500", "TB3MS"):
            (self.prev / f"{sid}.csv").write_bytes(fred_bytes(self.base))
        self.ps = dict(sha256=sha(fred_bytes(self.base)), last=self.base[-1][0], last_value=self.base[-1][1])
    def tearDown(self): self.tmp.cleanup()
    def mark(self, sid, rows):
        b = fred_bytes(rows)
        return F.diff_mark(self.ps, self.prev, sid, F.parse_rows(b), dict(sha256=sha(b), last=rows[-1][0], last_value=rows[-1][1]))
    def test_rullende_serie_faar_ikke_revision_af_frafald_foran(self):
        m = self.mark("SP500", self.base[3:] + [("2020-01-11", "2.5")])
        self.assertIn("ny obs", m); self.assertNotIn("REVIDERET", m)
    def test_rullende_serie_aendret_overlap_flages(self):
        r = self.base[3:]; r = [r[0], ("2020-01-05", "9.9")] + r[2:] + [("2020-01-11", "2.5")]
        self.assertIn("REVIDERET", self.mark("SP500", r))
    def test_rullende_serie_tab_af_hale_og_hul_flages(self):
        self.assertIn("REVIDERET", self.mark("SP500", self.base[2:8]))
        self.assertIn("REVIDERET", self.mark("SP500", self.base[3:6] + self.base[7:] + [("2020-01-11", "2.5")]))
    def test_ikke_rullende_serie_med_frafald_foran_flages_stadig(self):
        self.assertIn("REVIDERET", self.mark("TB3MS", self.base[3:] + [("2020-01-11", "2.5")]))


class TestSnapshotSelection(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.raw = Path(self.tmp.name) / "raw"
    def tearDown(self): self.tmp.cleanup()

    def test_fetch_baseline_springer_ukomplette_og_metaloese_over(self):
        make_snapshot(self.raw, "2026-01-01")
        make_snapshot(self.raw, "2026-02-01", complete=False)
        make_snapshot(self.raw, "2026-03-01", meta=False)
        (self.raw / "2026-04-01.ny").mkdir()
        with mock.patch.object(F, "RAW", self.raw):
            self.assertEqual(F.last_snapshot_before(self.raw / "2026-05-01.ny").name, "2026-01-01")

    def test_calibrate_gate_kraever_serier_og_filer(self):
        fuld = make_snapshot(self.raw, "2026-01-01")
        uden_serie = make_snapshot(self.raw, "2026-02-01", series=C.KRAEVEDE[:-1])
        uden_manual = make_snapshot(self.raw, "2026-03-01", manual=False)
        flag = make_snapshot(self.raw, "2026-04-01", complete=False)
        self.assertTrue(C.snapshot_complete(fuld))
        self.assertFalse(C.snapshot_complete(uden_serie))
        self.assertFalse(C.snapshot_complete(uden_manual))
        self.assertFalse(C.snapshot_complete(flag))

    def test_find_snapshot_vaelger_nyeste_brugbare_og_advarer(self):
        make_snapshot(self.raw, "2026-01-01")
        make_snapshot(self.raw, "2026-02-01", complete=False)
        out = io.StringIO()
        with mock.patch.object(C, "RAW", self.raw), contextlib.redirect_stdout(out):
            valgt = C.find_snapshot([])
        self.assertEqual(valgt.name, "2026-01-01")
        self.assertIn("ADVARSEL", out.getvalue()); self.assertIn("2026-02-01", out.getvalue())

    def test_kun_datonavngivne_mapper_er_snapshots(self):
        """Et komplet-udseende '<dato>.ny' efter et nedbrud blev valgt uden advarsel, og motor fejlede paa
        date.fromisoformat('2026-10-14.ny')."""
        make_snapshot(self.raw, "2026-01-01")
        ny = make_snapshot(self.raw, "2026-02-01.ny")
        self.assertFalse(C.snapshot_complete(ny)); self.assertFalse(F.snapshot_complete(ny))
        with mock.patch.object(C, "RAW", self.raw), quiet():
            self.assertEqual(C.find_snapshot([]).name, "2026-01-01")

    def test_find_snapshot_uden_brugbart_snapshot_stopper(self):
        make_snapshot(self.raw, "2026-01-01", complete=False)
        with mock.patch.object(C, "RAW", self.raw), self.assertRaises(SystemExit):
            C.find_snapshot([])

    def test_gammelt_rigtigt_snapshot_uden_nye_serier_er_ubrugeligt(self):
        gammel = C.RAW / "2026-08-09"
        if gammel.exists():
            self.assertFalse(C.snapshot_complete(gammel))
        self.assertTrue(C.snapshot_complete(REAL_SNAP))


class TestFetchMain(unittest.TestCase):
    """Ende-til-ende paa fetch.main() med falsk fetch_series — ingen netvaerk."""
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.raw, self.manual = base / "raw", base / "manual"
        self.manual.mkdir()
        for fn in ("manual.json", "acm.csv"):
            (self.manual / fn).write_bytes(b"x\n")
        (self.manual / F.YALE).write_text(
            "Date,SP500,CPI,LTR,CAPE\n2023-06,4200.0,304.0,3.8,29.0\n2023-07,4500.0,305.0,3.9,30.9\n"
            "2023-08,4457.36,305.98,4.17,30.47\n2023-09,4515.77,306.13,4.09,30.81\n", encoding="utf-8")
        self.today = date.today().isoformat()
        self.log = base / "LOG.md"
    def tearDown(self): self.tmp.cleanup()

    def _run(self, fejler=(), stale=None, multpl=None, fred=None):
        """Falsk FRED, falsk multpl (default: netvaerksfejl -> tom komposit) og friskhed neutraliseret
        (fixturens 2020-raekker er per konstruktion gamle); `stale` overstyrer friskheds-resultatet;
        `fred` = {serie: [(dato, vaerdi)]} overstyrer fixturens ROWS for enkelte serier."""
        def fake(sid, attempts=3):
            if sid in fejler:
                raise RuntimeError("simuleret fejl")
            b = fred_bytes((fred or {}).get(sid, ROWS)); return b, F.parse_rows(b)
        def fake_multpl(attempts=3):
            if multpl is None:
                raise RuntimeError("simuleret multpl-fejl")
            return multpl
        with mock.patch.object(F, "RAW", self.raw), mock.patch.object(F, "MANUAL", self.manual), \
             mock.patch.object(F, "LOG", self.log), \
             mock.patch.object(F, "fetch_series", fake), mock.patch.object(F, "fetch_multpl", fake_multpl), \
             mock.patch.object(F.SP, "staleness", lambda *a, **k: dict(stale or {})), quiet():
            F.main()

    def meta(self, name):
        return json.loads((self.raw / name / "meta.json").read_text(encoding="utf-8"))

    def test_friskhed_kritisk_serie_giver_ukomplet_snapshot(self):
        """§1.7: stale GS10 nedlaegger veto; stale PERMIT goer det ikke, men staar i meta."""
        with self.assertRaises(SystemExit):
            self._run(stale={"GS10": dict(alder_dage=200, graense=70, kritisk=True, sidste="2026-03-01")})
        self.assertTrue((self.raw / f"{self.today}.ukomplet").exists())
        shutil.rmtree(self.raw / f"{self.today}.ukomplet")
        self._run(stale={"PERMIT": dict(alder_dage=200, graense=90, kritisk=False, sidste="2026-03-01")})
        m = self.meta(self.today)
        self.assertTrue(m["complete"]); self.assertIn("PERMIT", m["stale"])

    def test_rygrad_bygges_og_yale_kopi_er_med(self):
        """§1.1: spine.csv med proveniens; Shiller-felter ordret; Yale-kopien og dens hash i snapshottet."""
        self._run()
        d = self.raw / self.today
        self.assertTrue((d / "spine.csv").exists()); self.assertTrue((d / F.YALE).exists())
        lines = (d / "spine.csv").read_text(encoding="utf-8").splitlines()
        self.assertEqual(lines[0], "Date,SP500,CPI,LTR,CAPE,Kilde")
        self.assertIn("2023-07,4500.0,305.0,3.9,30.9,shiller", lines)     # ordret felt-kopi
        self.assertNotIn("2023-08,4457.36", "\n".join(lines))            # forloebig raekke ude (ingen komposit her)
        m = self.meta(self.today)
        self.assertEqual(m["spine"]["seam"], "2023-07"); self.assertIn("yale", m["spine"])
        self.assertIn("fejl", m["spine"]["multpl"])                        # multpl fejlede -> ingen komposit, stadig komplet
        self.assertTrue(m["complete"])

    def test_succes_giver_komplet_dagssnapshot(self):
        self._run()
        self.assertTrue(self.meta(self.today)["complete"])
        self.assertEqual(len(list((self.raw / self.today).glob("*.csv"))), len(F.SERIES) + 3)   # + yale-kopi, spine, acm
        self.assertFalse((self.raw / f"{self.today}.ny").exists())

    def test_kritisk_fejl_giver_ukomplet_forsoeg_og_intet_dagssnapshot(self):
        with self.assertRaises(SystemExit) as cm:
            self._run(fejler={"GS10"})
        self.assertEqual(cm.exception.code, 1)
        self.assertFalse((self.raw / self.today).exists())
        self.assertFalse(self.meta(f"{self.today}.ukomplet")["complete"])

    def test_fejlet_genkoersel_roerer_ikke_komplet_dagssnapshot(self):
        self._run()
        with self.assertRaises(SystemExit):
            self._run(fejler={"TB3MS"})
        self.assertTrue(self.meta(self.today)["complete"])
        self.assertTrue((self.raw / self.today / "TB3MS.csv").exists())
        self.assertTrue((self.raw / f"{self.today}.ukomplet").exists())

    def test_reserveserie_nedlaegger_ikke_veto(self):
        self._run(fejler={"GDPC1"})
        m = self.meta(self.today)
        self.assertTrue(m["complete"]); self.assertEqual(m["reserve_fejlede"], ["GDPC1"])
        self.assertNotIn("GDPC1", m["series"])

    def test_ukomplet_samme_dag_ryddes_ved_succes(self):
        """fetch -> (fejl) -> fetch: '<dato>.ukomplet' sorterer efter '<dato>', saa motor --log afviste for evigt
        ('nyeste snapshot-mappe er ukomplet'), og en ny hentning ryddede den ikke."""
        with self.assertRaises(SystemExit):
            self._run(fejler={"GS10"})
        self.assertTrue((self.raw / f"{self.today}.ukomplet").exists())
        self._run()
        self.assertTrue(self.meta(self.today)["complete"])
        self.assertFalse((self.raw / f"{self.today}.ukomplet").exists())

    def test_logfoert_snapshot_erstattes_ikke(self):
        """Hovedbogsraekkens tal skal kunne genskabes fra sit snapshot: en genhentning samme dag efter --log
        erstattede ellers snapshottet med nye data."""
        self._run()
        foer = self.meta(self.today)["snapshot_sha256"]
        self.log.write_text("| logget | snapshot | P |" + chr(10) + f"| {self.today} | {self.today} | 15.1% |" + chr(10),
                            encoding="utf-8")
        with self.assertRaisesRegex(SystemExit, "erstattes ikke"):
            self._run()
        self.assertEqual(self.meta(self.today)["snapshot_sha256"], foer)

    def _run_rigtige_data(self, sp500_fra=None, argv=("fetch.py",), outlier=None):
        """fetch.main paa det nyeste committede snapshots bytes (falsk netvaerk), evt. med SP500-vinduet
        afkortet foran som FRED's rullende vindue."""
        for fn in ("manual.json", "acm.csv", F.YALE):
            shutil.copy(REAL_SNAP / fn, self.manual / fn)
        sp_bytes, html = licensfri_kilder(REAL_SNAP)
        def fake(sid, attempts=3):
            if sid == "SP500":
                b = sp_bytes
            elif not (REAL_SNAP / f"{sid}.csv").exists():          # licensbegraenset fil kun lokalt: FRED-format stand-in
                b = fred_bytes(ROWS, header=f"observation_date,{sid}")
            else:
                b = (REAL_SNAP / f"{sid}.csv").read_bytes()
            if sid == "SP500" and sp500_fra:
                ln = b.decode("utf-8").splitlines()
                b = (chr(10).join([ln[0]] + [r for r in ln[1:] if r >= sp500_fra]) + chr(10)).encode()
            return b, F.parse_rows(b)
        patches = [mock.patch.object(F, "RAW", self.raw), mock.patch.object(F, "MANUAL", self.manual),
                   mock.patch.object(F, "LOG", self.log), mock.patch.object(F, "fetch_series", fake),
                   mock.patch.object(F, "fetch_multpl", lambda attempts=3: html),
                   mock.patch.object(F.SP, "staleness", lambda *a, **k: {}), mock.patch.object(sys, "argv", list(argv))]
        if outlier is not None:
            patches.append(mock.patch.object(F.SP, "outlier_check", lambda *a, **k: outlier))
        with contextlib.ExitStack() as st:
            for pt in patches:
                st.enter_context(pt)
            st.enter_context(quiet())
            F.main()

    def test_delvis_foerste_sp500_maaned_vaelter_ikke_overlap_tjekket(self):
        """FRED's SP500 er et rullende 10-aars vindue, saa foerste maaned er et DELVIST middel. Starter vinduet
        efter valgrallyet i nov. 2016 (fetch 10.-30. nov. 2026), afveg den >1 % fra Shillers hele-maaneds-middel,
        og 99 %-reglen (n ~80) gjorde snapshottet UKOMPLET: november-ritualet ville vaere blokeret."""
        self._run_rigtige_data(sp500_fra="2016-11-14")
        ov = self.meta(self.today)["spine"]["overlap"]
        self.assertTrue(self.meta(self.today)["complete"])
        self.assertTrue(ov["bestaaet"]); self.assertEqual(ov["sp500_undtagelser"], [])

    def test_accept_outlier_kraever_begrundelse(self):
        with self.assertRaisesRegex(SystemExit, "kraever en begrundelse"):
            self._run_rigtige_data(argv=("fetch.py", "--accept-outlier"), outlier=[("2026-09", "test")])
        with self.assertRaisesRegex(SystemExit, "kraever en begrundelse"):
            self._run_rigtige_data(argv=("fetch.py", "--accept-outlier", "--allow-stale"), outlier=[("2026-09", "test")])
        self.assertFalse((self.raw / f"{self.today}.ny").exists())     # afvist FOER noget skrives (et .ny blokerede --log)

    def test_genkoersel_samme_dag_erstatter_det_komplette_dagssnapshot(self):
        self._run()
        (self.raw / self.today / "gammelt.txt").write_text("x", encoding="utf-8")
        self._run()
        self.assertFalse((self.raw / self.today / "gammelt.txt").exists())        # erstattet, ikke blandet
        self.assertTrue(self.meta(self.today)["complete"])
        self.assertFalse((self.raw / f"{self.today}.ny").exists())

    def test_komposit_rygrad_succesvejen_skriver_proveniens_og_seks_decimaler(self):
        """byg_rygrad hele vejen: multpl ok -> overlap bestaaet -> komposit-raekker 'fred+multpl' (6 decimaler) efter
        Shiller-seamet."""
        idag = date.today()
        mdr, y, m = [], 2023, 6
        while (y, m) < (idag.year, idag.month):                                     # lukkede maaneder 2023-06 .. forrige maaned
            mdr.append(f"{y}-{m:02d}"); y, m = (y + 1, 1) if m == 12 else (y, m + 1)
        sp = {k: 4457.4 for k in mdr}; sp["2023-06"], sp["2023-07"] = 4200.0, 4500.0  # = Yale-fixturens egne vaerdier
        cape = {k: 31.0 for k in mdr}; cape["2023-06"], cape["2023-07"] = 29.0, 30.9
        MON = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
        gammel, y, m = {}, 1871, 2
        while (y, m) < (2023, 6):
            gammel[f"{y}-{m:02d}"] = 20.0; y, m = (y + 1, 1) if m == 12 else (y, m + 1)
        rk = [(k, v) for k, v in {**gammel, **cape}.items()]
        html = ("<table id='datatable'><tr><td>%s 18, %d</td> <td> &#x2002; 99.99 </td></tr>" % (MON[idag.month - 1], idag.year)
                + "".join(f"<tr><td>{MON[int(k[5:7]) - 1]} 1, {k[:4]}</td> <td> &#x2002; {v:.2f} </td></tr>" for k, v in reversed(rk))
                + "</table>")
        self._run(multpl=html.encode("utf-8"), fred=dict(SP500=[(f"{k}-01", v) for k, v in sp.items()],
                                         CPIAUCNS=[(f"{k}-01", 307.0) for k in mdr], GS10=[(f"{k}-01", 4.17) for k in mdr]))
        d = self.raw / self.today
        m_ = self.meta(self.today)
        self.assertTrue(m_["complete"]); self.assertTrue(m_["spine"]["overlap"]["bestaaet"]); self.assertNotIn("fejl", m_["spine"]["multpl"])
        lines = (d / "spine.csv").read_text(encoding="utf-8").splitlines()
        self.assertIn("2023-07,4500.0,305.0,3.9,30.9,shiller", lines)                  # Shiller ordret t.o.m. seamet
        self.assertIn("2023-08,4457.400000,307.000000,4.170000,31.000000,fred+multpl", lines)
        self.assertEqual(lines[-1].split(",")[0], mdr[-1])                           # sidste lukkede maaned; den loebende er ikke med
        self.assertNotIn(b"\r", (d / "cape_multpl.csv").read_bytes())                # LF paa alle maskiner

    def test_manglende_manual_json_goer_snapshottet_ukomplet(self):
        (self.manual / "manual.json").unlink()
        with self.assertRaises(SystemExit):
            self._run()
        self.assertFalse(self.meta(f"{self.today}.ukomplet")["complete"])


# ============================================================== calibrate.py
class TestCalibrate(unittest.TestCase):
    def test_fit_konvergensstop_matcher_300_iterationer(self):
        rng = np.random.default_rng(0)
        X = rng.normal(size=(300, 3)); y = (X @ [1.0, -0.5, 0.2] + rng.normal(size=300) > 0).astype(float)
        self.assertTrue(np.allclose(C.fit(X, y), C.fit(X, y, tol=0.0), atol=1e-9))

    def test_main_overskriver_ikke_driftsvaegtene(self):
        """calibrate.py skrev ubetinget et 5.0-trin1-weights.json oven i de frosne 5.0-final-vaegte;
        motor.py afviste det derefter ('koer finalize6.py')."""
        with tempfile.TemporaryDirectory() as t:
            here = Path(t)
            shutil.copy(HERE / "weights.json", here / "weights.json")
            foer = (here / "weights.json").read_bytes()
            with mock.patch.object(C, "HERE", here), \
                 mock.patch.object(sys, "argv", ["calibrate.py", "--snapshot", str(REAL_SNAP)]), \
                 contextlib.redirect_stdout(io.StringIO()) as out:
                C.main()
            self.assertEqual((here / "weights.json").read_bytes(), foer)
            self.assertIn("overskrives IKKE", out.getvalue())

    def test_read_fred_positionel_og_springer_manglende_over(self):
        with tempfile.TemporaryDirectory() as t:
            (Path(t) / "X.csv").write_bytes(fred_bytes([("2020-01-01", "1.5"), ("2020-02-01", ".")], header="DATE,VALUE"))
            self.assertEqual(C.read_fred(Path(t), "X"), {(2020, 1): 1.5})


# ============================================================== finalize6.py
def _res(rkey, gate, passed=True, med_blok=True, med_gate=True):
    r = {"snapshot": "2026-01-01", "gates": ({gate: passed} if med_gate else {})}
    if med_blok:
        r[rkey] = {"improvement": 36.8, "brier": 34.3}
    return r

class TestPermanenteLinjer(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.here = Path(self.tmp.name)
    def tearDown(self): self.tmp.cleanup()

    def _lines(self, a7=None, a8=None):
        for fn, r in (("ablation7_resultat.json", a7), ("ablation8_resultat.json", a8)):
            if r is not None:
                (self.here / fn).write_text(json.dumps(r), encoding="utf-8")
        out = io.StringIO()
        with mock.patch.object(F6, "HERE", self.here), contextlib.redirect_stdout(out):
            return F6.permanente_linjer(), out.getvalue()

    def test_bestaaet_og_ikke_bestaaet(self):
        lines, _ = self._lines(_res("curvecape", "promoveret", passed=True), _res("curve_awh", "OPTAGET", passed=False))
        self.assertIn("bestaaet", lines["curve_cape"]["status"])
        self.assertIn("ikke bestaaet", lines["curve_awh"]["status"])
        self.assertEqual(lines["curve_cape"]["wf_improvement"], 36.8)

    def test_manglende_fil_advarer_og_udelader(self):
        lines, out = self._lines(a7=None, a8=_res("curve_awh", "OPTAGET"))
        self.assertNotIn("curve_cape", lines); self.assertIn("ADVARSEL", out); self.assertIn("ablation7", out)

    def test_manglende_gate_giver_ukendt_status(self):
        lines, out = self._lines(_res("curvecape", "promoveret", med_gate=False), _res("curve_awh", "OPTAGET"))
        self.assertIn("ukendt", lines["curve_cape"]["status"]); self.assertIn("ADVARSEL", out)

    def test_omdoebt_resultatnoegle_crasher_ikke(self):
        lines, out = self._lines(_res("curvecape", "promoveret", med_blok=False), _res("curve_awh", "OPTAGET"))
        self.assertNotIn("curve_cape", lines); self.assertIn("curve_awh", lines); self.assertIn("ADVARSEL", out)


class TestFinalize6Main(unittest.TestCase):
    """Koerer den rigtige kalibrering (laeser det rigtige snapshot) men skriver i en temp-mappe."""
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.here = Path(self.tmp.name)
        for fn in ("ablation3_resultat.json", "ablation7_resultat.json", "ablation8_resultat.json"):
            if (HERE / fn).exists():
                shutil.copy(HERE / fn, self.here / fn)
    def tearDown(self): self.tmp.cleanup()

    def _main(self):
        with mock.patch.object(F6, "HERE", self.here), mock.patch.object(sys, "argv", ["finalize6.py"]), quiet():
            F6.main()
        return json.loads((self.here / "weights.json").read_text(encoding="utf-8"))

    def test_frisk_genbyg_har_fejlalarm_alle_tre_steder(self):
        W = self._main()
        self.assertEqual(W["operationel"], "curve_only")
        for blok in (W["op"], W["fuldmodel"], W["benchmarks"]["curve_only"]):
            self.assertIn("vaerste_fejlalarm", blok)
        self.assertEqual(W["band"]["n_draws"], 1000)
        self.assertIn("curve_cape", W["benchmarks"]); self.assertIn("curve_awh", W["benchmarks"])

    def test_gate_udfald_kan_ikke_skifte_operationel_model(self):
        """RAADETS_V501 §6: en tidligere 'promoveret' operationel model i weights.json er et gate-udfald,
        ikke en raadsbeslutning — finalize6 ignorerer den (med advarsel) og laaser curve_only."""
        prev = dict(protocol_version="5.0-final", operationel="curve_cape",
                    op=dict(features=["curve", "cape_pct"], w=[-2.0, -1.0, -0.4]))
        (self.here / "weights.json").write_text(json.dumps(prev), encoding="utf-8")
        W = self._main()
        self.assertEqual(W["operationel"], "curve_only")
        self.assertEqual(W["op"]["features"], ["curve"])
        self.assertFalse(W["gate"]["raadsbeslutning_paakraevet"])
        self.assertEqual(W["version"], F6.VERSION)
        self.assertIn("manifest_hash", W)
        self.assertEqual(len(W["band"]["base"]), W["band"]["n_draws"])     # §4.3: basisrate pr. traek

    def test_legacy_replay_roerer_hverken_index_eller_kaeden(self):
        """--legacy er ren verifikation naar v5.0-manifestet findes: index-raekkefoelgen og den
        kalibrering der er i drift aendres ikke (regression: en lokal legacy-replay flyttede v5.0
        sidst i index.json, saa naeste rekalibrering ville have auditeret mod v5.0)."""
        def koer(*extra):
            with mock.patch.object(F6, "HERE", self.here), mock.patch.object(sys, "argv", ["finalize6.py", *extra]), quiet():
                F6.main()
        kal = self.here / "kalibreringer"
        koer("--legacy")
        foer_legacy = (kal / "index.json").read_bytes()
        koer("--legacy")
        self.assertEqual((kal / "index.json").read_bytes(), foer_legacy)       # idempotent
        koer()                                                                  # v5.0.1-kalibrering
        W = json.loads((self.here / "weights.json").read_text(encoding="utf-8"))
        kaede = [e["hash"] for e in json.loads((kal / "index.json").read_text(encoding="utf-8"))]
        self.assertEqual(kaede[-1], W["manifest_hash"])
        koer("--legacy")                                                        # maa ikke flytte v5.0 sidst
        self.assertEqual([e["hash"] for e in json.loads((kal / "index.json").read_text(encoding="utf-8"))], kaede)
        with mock.patch.object(F6, "HERE", self.here):
            self.assertEqual(F6.forrige_manifest()["hash"], W["manifest_hash"])    # kalibreringen i drift

    def test_legacy_replay_verificerer_og_fejler_hoejlydt_ved_aendret_historik(self):
        def koer(*extra):
            with mock.patch.object(F6, "HERE", self.here), mock.patch.object(sys, "argv", ["finalize6.py", *extra]), quiet():
                F6.main()
        koer("--legacy")
        kal = self.here / "kalibreringer"
        h = json.loads((kal / "legacy_mapping.json").read_text(encoding="utf-8"))["manifest_hash"]
        mf = kal / f"manifest_{h}.json"
        m = json.loads(mf.read_text(encoding="utf-8"))
        m["snapshot"] = "1999-01-01"                        # proveniens aendret: stadig samme kalibrering
        mf.write_text(json.dumps(m), encoding="utf-8")
        koer("--legacy")                                    # verificerer paa nyere snapshot, skriver intet
        self.assertEqual(json.loads(mf.read_text(encoding="utf-8"))["snapshot"], "1999-01-01")
        self.assertEqual(len(list(kal.glob("manifest_*.json"))), 1)
        m["origins"] = m["origins"][:-1]                    # indhold aendret: historikken er flyttet
        mf.write_text(json.dumps(m), encoding="utf-8")
        with self.assertRaisesRegex(SystemExit, "ANDEN kalibrering"):
            koer("--legacy")

    def test_det_committede_manifest_kan_genskabes_bitidentisk(self):
        """Determinismevagt (numpy-/platformsdrift): rekalibrering paa det committede manifests EGET snapshot skal give samme
        kalibrering ('UAENDRET') og en weights.json der er identisk bortset fra created_utc — inkl. de 1000 bootstrap-traek."""
        Wc = json.loads((HERE / "weights.json").read_text(encoding="utf-8"))
        for fn in ("weights.json", "nber_announcements.csv"):
            shutil.copy(HERE / fn, self.here / fn)
        shutil.copytree(HERE / "kalibreringer", self.here / "kalibreringer")
        foer = {p.name: p.read_bytes() for p in (self.here / "kalibreringer").iterdir()}
        out = io.StringIO()
        with mock.patch.object(F6, "HERE", self.here), contextlib.redirect_stdout(out), \
             mock.patch.object(sys, "argv", ["finalize6.py", "--snapshot", str(C.RAW / Wc["snapshot"])]):
            F6.main()
        self.assertIn("kalibrering UAENDRET", out.getvalue())
        Wn = json.loads((self.here / "weights.json").read_text(encoding="utf-8"))
        for W in (Wc, Wn):
            W.pop("created_utc")
        self.assertEqual(Wn, Wc)
        self.assertEqual({p.name: p.read_bytes() for p in (self.here / "kalibreringer").iterdir()}, foer)

    def test_curve_only_panelet_afhaenger_ikke_af_rygradens_laengde(self):
        """§1.7/§2: curve-only maa aldrig afhaenge af CAPE-kilden. Med multpl nede ender rygraden 2023-07; foer gav en
        refit da stille det gamle panel (v5.0-vaegtene, n_obs 264), og en vagt mod det ville have blokeret hovedbogen i
        hver refit-maaned. Nu er curve-only-panelet identisk, mens fuldmodellens panel (med CAPE) afkortes."""
        with tempfile.TemporaryDirectory() as t:
            snap = Path(t) / REAL_SNAP.name; shutil.copytree(REAL_SNAP, snap)
            ln = (snap / "spine.csv").read_text(encoding="utf-8").splitlines()
            (snap / "spine.csv").write_text(chr(10).join([ln[0]] + [r for r in ln[1:] if r[:7] <= "2023-07"]) + chr(10),
                                            encoding="utf-8")
            fuld, trunk = A2.build_dataset(REAL_SNAP, ["curve"]), A2.build_dataset(snap, ["curve"])
            self.assertEqual(trunk["qk"], fuld["qk"])
            self.assertTrue(np.array_equal(trunk["F"], fuld["F"]))
            self.assertTrue(np.array_equal(trunk["Y_tek"], fuld["Y_tek"], equal_nan=True))
            self.assertLess(len(A2.build_dataset(snap)["qk"]), len(A2.build_dataset(REAL_SNAP)["qk"]))

    def test_ny_kalibrering_kraever_nyt_versionsnummer(self):
        """§3.3: hver rekalibrering er en ny v5.0.x. Uden stop fik et nyt manifest samme version som det i drift
        (og blev derefter genbrugt uaendret), og en finalize6-koersel mellem rekalibreringer loesnede vaegtene."""
        with self.assertRaisesRegex(SystemExit, "bump VERSION"):
            F6.kraev_ny_version({"version": F6.VERSION, "hash": "abc12345"})
        F6.kraev_ny_version({"version": F6.LEGACY_VERSION, "hash": "6baeade4"})
        F6.kraev_ny_version(None)

    def test_raadsbeslutning_fil_stopper_koerslen_indtil_v51_kode_findes(self):
        kal = self.here / "kalibreringer"; kal.mkdir(exist_ok=True)
        (kal / "raadsbeslutning.json").write_text(json.dumps(dict(operationel="fuldmodel", reference="test", dato="2027-01-01")), encoding="utf-8")
        with self.assertRaisesRegex(SystemExit, "v5.1"):
            self._main()
        (kal / "raadsbeslutning.json").unlink()


# ============================================================== motor.py
class TestMotor(unittest.TestCase):
    """Rigtigt snapshot kopieret til temp-RAW under dagens dato; weights kopieret; LOG.md i temp."""
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(); base = Path(cls.tmp.name)
        cls.raw = base / "raw"; cls.here = base / "v5"; cls.here.mkdir()
        cls.today = date.today().isoformat()
        shutil.copytree(REAL_SNAP, cls.raw / cls.today)
        for fn in ("weights.json", "weights_trin1_teknisk.json", "nber_announcements.csv", "diagnostik.json"):
            shutil.copy(HERE / fn, cls.here / fn)
        if (HERE / "kalibreringer").exists():
            shutil.copytree(HERE / "kalibreringer", cls.here / "kalibreringer")
        # Kalenderuafhaengighed: motor.py sammenligner refit_maaned med date.today(). Testene koerer paa en vaegtkopi med
        # refit 'denne maaned', saa kun test_frosne_vaegte_... (de RIGTIGE vaegte) er den bevidste september-alarm.
        W = json.loads((cls.here / "weights.json").read_text(encoding="utf-8"))
        W["refit_maaned"] = cls.today[:7]
        (cls.here / "weights.json").write_text(json.dumps(W), encoding="utf-8")
    @classmethod
    def tearDownClass(cls): cls.tmp.cleanup()

    def _motor(self, argv, raw=None, here=None, vindue=(1, 31), dag=None):
        """Logvinduet (dag 10-20, G3.6) neutraliseres som standard; test_logvindue_* styrer det selv."""
        out = io.StringIO()
        with mock.patch.object(C, "RAW", raw or self.raw), mock.patch.object(M, "HERE", here or self.here), \
             mock.patch.object(M, "LOGDAG_VINDUE", vindue), \
             mock.patch.object(M, "idag", (lambda: dag) if dag else M.idag), \
             mock.patch.object(sys, "argv", ["motor.py"] + argv), contextlib.redirect_stdout(out):
            M.main()
        return out.getvalue()

    def _scenario(self, y10=None, tb3=None, oas=None, mortgage=None, cp=None, sahm=None, dd=None):
        """Temp-RAW/-HERE med en kopi af REAL_SNAP hvor de sidste observationer er PINNET (40 dages konstant paa DGS10/DTB3
        -> trailing-vinduet er praecis konstanten), saa motorens tal kan regnes i hovedet. Returnerer (raw, here)."""
        t = tempfile.TemporaryDirectory(); self.addCleanup(t.cleanup)
        raw, here = Path(t.name) / "raw", Path(t.name) / "v5"
        snap = raw / self.today
        shutil.copytree(self.raw / self.today, snap); shutil.copytree(self.here, here)
        def add(sid, rows):
            f = snap / f"{sid}.csv"
            if not f.exists():                                   # licensbegraenset fil findes kun lokalt (F1)
                f.write_text(f"observation_date,{sid}" + chr(10), encoding="utf-8")
            tekst = f.read_text(encoding="utf-8")
            f.write_text(tekst + ("" if tekst.endswith(chr(10)) else chr(10)) + "".join(f"{d},{v}{chr(10)}" for d, v in rows),
                         encoding="utf-8")
        d0 = date.fromisoformat(max(d for sid in ("DGS10", "DTB3") for d, _ in C.read_fred_daily(snap, sid)))
        dage = [(d0 + timedelta(days=k)).isoformat() for k in range(1, 41)]
        if y10 is not None:
            add("DGS10", [(d, y10) for d in dage])
        if tb3 is not None:
            add("DTB3", [(d, tb3) for d in dage])
        if oas is not None:
            add("BAMLH0A0HYM2", [(dage[-1], oas)])
        if mortgage is not None:
            add("MORTGAGE30US", [(dage[-1], mortgage)])
        if cp is not None:
            add("RIFSPPFAAD90NB", [(d, cp) for d in dage])
        if sahm is not None:
            y, m = max(C.read_fred(snap, "SAHMREALTIME"))
            add("SAHMREALTIME", [(f"{y + (m == 12)}-{m % 12 + 1:02d}-01", sahm)])
        if dd is not None:
            man = json.loads((snap / "manual.json").read_text(encoding="utf-8")); man["spx_vs_hi"] = dd
            (snap / "manual.json").write_text(json.dumps(man), encoding="utf-8")
        return raw, here

    def _orakel(self, curve):
        """Uafhaengig genberegning af P, 10-90-baandet og dom-ordet ud fra weights.json (ikke fra motor.py's kode)."""
        W = json.loads((self.here / "weights.json").read_text(encoding="utf-8"))
        op = W["op"]; z = (curve - op["mu"]["curve"]) / op["sd"]["curve"]
        f = lambda w: 1 / (1 + np.exp(-(w[0] + w[1] * z)))
        ps = [f(w) for w in W["band"]["W"]]
        lo, hi, p, base = float(np.percentile(ps, 10)), float(np.percentile(ps, 90)), float(f(op["w"])), W["base_rate"]
        dom = ("under basisraten" if p < base else "over basisraten") if (base < lo or base > hi) else "ikke skelnelig"
        return p, lo, hi, dom, W

    def test_log_appender_og_afviser_dublet_samme_maaned(self):
        logf = self.here.parent / "LOG.md"
        logf.write_text("| logget | snapshot | P | baand | basisrate | dom | kurve | antaending | note |\n|---|\n", encoding="utf-8")
        out1 = self._motor(["--log"])
        self.assertIn("LOGGET som raekke 1", out1)
        self.assertIn(f"| {self.today} | {self.today} |", logf.read_text(encoding="utf-8"))
        out2 = self._motor(["--log"])
        self.assertIn("--log AFVIST", out2); self.assertIn("allerede logget", out2)
        self.assertEqual(logf.read_text(encoding="utf-8").count(f"| {self.today} |"), 1)

    def test_log_afvises_naar_nyeste_snapshot_er_ubrugeligt(self):
        with tempfile.TemporaryDirectory() as t:
            raw = Path(t) / "raw"; shutil.copytree(self.raw / self.today, raw / self.today)
            make_snapshot(raw, f"{self.today}.ukomplet", complete=False)
            here = Path(t) / "v5"; shutil.copytree(self.here, here)
            out = self._motor(["--log"], raw=raw, here=here)
        self.assertIn("ADVARSEL: nyeste snapshot-mappe", out)
        self.assertIn("--log AFVIST", out); self.assertNotIn("LOGGET som raekke", out)

    def test_manglende_manual_json_stopper_hoejlydt(self):
        with tempfile.TemporaryDirectory() as t:
            raw = Path(t) / "raw"; shutil.copytree(self.raw / self.today, raw / self.today)
            (raw / self.today / "manual.json").unlink()
            with self.assertRaisesRegex(SystemExit, "manual.json mangler i snapshottet"):
                self._motor(["--snapshot", str(raw / self.today)], raw=raw)

    def test_live_input_er_daglig_og_maanedstallet_printes_ved_siden_af(self):
        out = self._motor(["--json", str(self.here.parent / "d_live.json")])
        self.assertIn("live-input: kurve = trailing maaned af daglige DGS10 - DTB3", out)
        self.assertIn("paa publicerede maanedstal GS10-TB3MS", out)
        L = C.live_kurve(self.raw / self.today)
        # 10Y-tripwiren viser seneste DAGLIGE niveau, ikke maanedssnittet
        self.assertIn(f"{L['y10_seneste'][1]:.2f}% ({L['y10_seneste'][0]})", out)
        self.assertIn("DFF dagligt", out)
        d = json.loads((self.here.parent / "d_live.json").read_text(encoding="utf-8"))
        self.assertEqual(d["live_input"]["kilde"], "daglig")
        self.assertAlmostEqual(d["live_input"]["curve"], round(L["curve"], 4))
        self.assertIn("p_maanedlig", d["live_input"])

    def test_foerste_lograekke_paa_daglig_input_faar_note(self):
        with tempfile.TemporaryDirectory() as t:
            here = Path(t) / "v5"; shutil.copytree(self.here, here)
            logf = here.parent / "LOG.md"
            logf.write_text("| logget | snapshot | P | baand | basisrate | dom | kurve | antaending | note | kalibrering |"
                            + chr(10) + "|---|" + chr(10), encoding="utf-8")
            out = self._motor(["--log"], here=here)
            self.assertIn("LOGGET som raekke 1", out)
            tekst = logf.read_text(encoding="utf-8")
            self.assertIn("input: daglig", tekst)
            W = json.loads((here / "weights.json").read_text(encoding="utf-8"))
            gl_v = json.loads((here / "kalibreringer" / f"manifest_{W['forrige_manifest']}.json")
                              .read_text(encoding="utf-8"))["version"]
            self.assertIn(f"bro: P(v{gl_v} {W['forrige_manifest']})", tekst)   # oktober-rækken skrev 'v?'
            self.assertNotIn("P(v? ", tekst)

    def test_frosne_vaegte_giver_ingen_reankrings_advarsel(self):
        """§3: et nyere snapshot end kalibreringen er forventet — ingen 'koer finalize6 igen'.
        DEN bevidste kalenderalarm (foerste gang september 2027): bruger de RIGTIGE weights.json, ikke setUpClass-kopien."""
        with tempfile.TemporaryDirectory() as t:
            here = Path(t) / "v5"; shutil.copytree(self.here, here)
            shutil.copy(HERE / "weights.json", here / "weights.json")
            out = self._motor([], here=here)
        self.assertNotIn("koer finalize6.py igen", out)
        self.assertIn("vaegte frosne: manifest", out)              # selve §3-linjen (hovedet har ogsaa 'vaegte frosne til ...')
        self.assertNotIn("REKALIBRERING PAAKRAEVET", out)

    def test_aendret_annonceringstabel_afviser_log(self):
        """§3.2b: hash-aendring i nber_announcements.csv -> deterministisk trigger, --log afvises."""
        with tempfile.TemporaryDirectory() as t:
            here = Path(t) / "v5"; shutil.copytree(self.here, here)
            with (here / "nber_announcements.csv").open("a", encoding="utf-8") as fh:
                fh.write("peak,2099-01,2099-07-01,test" + chr(10))
            logf = here.parent / "LOG.md"
            logf.write_text("| logget | snapshot | P | baand | basisrate | dom | kurve | antaending | note | kalibrering |"
                            + chr(10) + "|---|" + chr(10), encoding="utf-8")
            out = self._motor(["--log"], here=here)
        self.assertIn("REKALIBRERING PAAKRAEVET", out); self.assertIn("nber_announcements.csv er aendret", out)
        self.assertIn("--log AFVIST", out); self.assertNotIn("LOGGET som raekke", out)

    def test_forfalden_september_rekalibrering_afviser_log(self):
        """§3.2a: er refit-maaneden mere end et aar bag naeste september, afvises --log."""
        with tempfile.TemporaryDirectory() as t:
            here = Path(t) / "v5"; shutil.copytree(self.here, here)
            W = json.loads((here / "weights.json").read_text(encoding="utf-8"))
            W["refit_maaned"] = "2020-09"
            (here / "weights.json").write_text(json.dumps(W), encoding="utf-8")
            logf = here.parent / "LOG.md"
            logf.write_text("| logget | snapshot | P | baand | basisrate | dom | kurve | antaending | note | kalibrering |"
                            + chr(10) + "|---|" + chr(10), encoding="utf-8")
            out = self._motor(["--log"], here=here)
        self.assertIn("september-rekalibrering er forfalden", out); self.assertIn("--log AFVIST", out)

    def test_json_dump_har_dashboard_kontrakten(self):
        logf = self.here.parent / "LOG.md"
        logf.write_text(
            "| logget | snapshot | P | baand | basisrate | dom | kurve | antaending | note |" + chr(10)
            + "|---|" + chr(10)
            + "| 2026-08-12 | 2026-08-12 | 20.1% | 14.4-29.2% | 18.2% | ikke skelnelig | +0.87 | ingen |  |"
            + chr(10), encoding="utf-8")
        ud = self.here.parent / "dash.json"
        self._motor(["--json", str(ud)])
        d = json.loads(ud.read_text(encoding="utf-8"))
        for n in ("p", "baand", "basisrate", "baand_udelukker_basisrate", "ratio",
                  "dom", "inputs", "benchmarks", "monitors", "pengepolitik",
                  "advarsler", "hovedbog"):
            self.assertIn(n, d)
        self.assertEqual(len(d["baand"]), 2)
        self.assertLess(d["baand"][0], d["p"])
        self.assertLess(d["p"], d["baand"][1])
        # Section 6-reglen: ratio kun naar baandet udelukker basisraten
        self.assertEqual(d["ratio"] is None, not d["baand_udelukker_basisrate"])
        self.assertEqual({m["tilstand"] for m in d["monitors"]} - {"aktiv", "inaktiv", "kontekst", "utilgaengelig"}, set())
        for n in ("scenarie", "parret", "rekalibrering_paakraevet", "sti", "manual_friskhed", "hovedbog_reference"):
            self.assertIn(n, d)                                       # F53/F9/F11/F30/G3.5
        self.assertNotIn("log_blokeringer", d)                        # dagsafhaengigt -> ikke i den reproducerbare JSON
        self.assertNotIn("CP-spaend", " ".join(m["navn"] for m in d["monitors"]))
        self.assertEqual(len(d["hovedbog"]), 1)
        self.assertEqual(d["hovedbog"][0]["p_tal"], 0.201)
        self.assertEqual(d["hovedbog"][0]["baand_tal"], [0.144, 0.292])
        self.assertEqual(d["hovedbog"][0]["kurve_tal"], 0.87)

    def test_json_default_sti_er_repo_roden(self):
        ud = self.here.parent / "dashboard.json"
        if ud.exists():
            ud.unlink()
        self._motor(["--json"])
        self.assertTrue(ud.exists())

    def test_vaegte_uden_fejlalarm_stopper_hoejlydt(self):
        with tempfile.TemporaryDirectory() as t:
            here = Path(t) / "v5"; shutil.copytree(self.here, here)
            W = json.loads((here / "weights.json").read_text(encoding="utf-8"))
            del W["op"]["vaerste_fejlalarm"]
            (here / "weights.json").write_text(json.dumps(W), encoding="utf-8")
            with self.assertRaisesRegex(SystemExit, "vaerste_fejlalarm"):
                self._motor([], here=here)

    # ---- facit-tests: motorens tal og dom regnes uafhaengigt efter paa PINNEDE inputs (29 af 30 plausible
    # mutationer i motorens kerne overlevede foer disse tests) ----
    def test_P_baand_og_dom_matcher_et_uafhaengigt_orakel_i_alle_tre_udfald(self):
        domme = set()
        for y10, tb3 in ((5.50, 1.50), (2.00, 4.00), (4.50, 3.40)):          # stejl, dybt inverteret, ca. P = 15 %
            curve = y10 - tb3
            p, lo, hi, dom, W = self._orakel(curve)
            domme.add(dom)
            raw, here = self._scenario(y10=y10, tb3=tb3)
            ud = here.parent / "d.json"
            out = self._motor(["--log", "--json", str(ud)], raw=raw, here=here)
            d = json.loads(ud.read_text(encoding="utf-8"))
            self.assertAlmostEqual(d["inputs"][0]["vaerdi"], curve, places=3)        # kurve = y10 - tb3 (fortegn)
            self.assertAlmostEqual(d["p"], p, places=5)                              # formlen
            self.assertAlmostEqual(d["baand"][0], lo, places=5); self.assertAlmostEqual(d["baand"][1], hi, places=5)
            self.assertIn({"under basisraten": "laesningen er under basisraten", "over basisraten": "laesningen er over basisraten",
                           "ikke skelnelig": "IKKE SKELNELIG FRA BASISRATEN"}[dom], out)
            r = M.laes_hovedbog(here.parent / "LOG.md")[-1]                          # hovedbogsraekken, laest tilbage
            self.assertEqual((r["dom"], r["kurve"], r["snapshot"], r["kalibrering"]),
                             (dom, f"{curve:+.2f}", self.today, W["manifest_hash"]))
            b = [M.tal_af(v, 0.01) for v in r["baand"].split("-")]
            self.assertAlmostEqual(M.tal_af(r["P"], 0.01), p, delta=0.0006)
            self.assertAlmostEqual(b[0], lo, delta=0.0006); self.assertAlmostEqual(b[1], hi, delta=0.0006)
        self.assertEqual(domme, {"under basisraten", "over basisraten", "ikke skelnelig"},
                         "scenarierne daekker ikke alle tre domme efter en rekalibrering — flyt dem")

    def test_taerskler_taender_og_slukker_monitorerne_og_antaendingskolonnen(self):
        navne = ["Sahm >= 0,50", "HY OAS > 600bp", "S&P dagsluk vs 52u-top < -20%"]
        svaerm = ["CP-spaend 3m > 75bp i 2+ uger", "10Y > 5,25%", "Realkredit 30Y > 7,8%"]
        stress = dict(y10=5.50, tb3=4.00, oas=7.0, mortgage=8.0, cp=6.0, sahm=0.50, dd=-0.25)   # Sahm praecis paa 0,50: >=
        rolig = dict(y10=4.50, tb3=3.00, oas=3.0, mortgage=6.0, cp=3.1, sahm=0.0, dd=-0.01)
        for scen, tilstand in ((stress, "aktiv"), (rolig, "inaktiv")):
            raw, here = self._scenario(**scen)
            ud = here.parent / "d.json"
            self._motor(["--log", "--json", str(ud)], raw=raw, here=here)
            d = json.loads(ud.read_text(encoding="utf-8"))
            mon = {m["navn"]: m["tilstand"] for m in d["monitors"]}
            sc = {m["navn"]: m["tilstand"] for m in d["scenarie"]}
            celle = M.laes_hovedbog(here.parent / "LOG.md")[-1]["antaending"]
            for n in navne:
                self.assertEqual(mon[n], tilstand, n)
                self.assertEqual(n in celle, tilstand == "aktiv", f"{n} i antaending: {celle!r}")
            for n in svaerm:                              # R3: taendes i appendikset, men ALDRIG i kolonnen
                self.assertEqual(sc[n], tilstand, n)
                self.assertNotIn(n, celle)
                self.assertNotIn(n, mon)

    def test_reserveserier_maa_mangle_uden_at_motor_falder(self):
        """fetch.RESERVE goer snapshottet 'komplet' uden disse filer; motor skal have sine fald-tilbage-veje (DFF -> FEDFUNDS,
        THREEFYTP10 -> acm.csv, CPIAUCSL valgfri)."""
        for sid in sorted(F.RESERVE):
            raw, _ = self._scenario()
            (raw / self.today / f"{sid}.csv").unlink(missing_ok=True)      # licensfiler mangler allerede i en ren klon
            self.assertIn("MOTOR v", self._motor([], raw=raw), sid)

    def test_gammelt_snapshot_afvises_med_mindre_allow_stale(self):
        with tempfile.TemporaryDirectory() as t:
            raw = Path(t) / "raw"
            shutil.copytree(self.raw / self.today, raw / (date.today() - timedelta(days=M.STALE_DAYS + 1)).isoformat())
            with self.assertRaisesRegex(SystemExit, "dage gammelt"):
                self._motor([], raw=raw)
            self.assertIn("MOTOR v", self._motor(["--allow-stale"], raw=raw))

    def test_septemberreglens_graenser(self):
        """§3.2a, pinnet med frossen dato: alarmen kommer den foerste september EFTER refit-maaneden; en udloest refit
        (§3.2b, fx april) nulstiller ikke september-planen."""
        class Fast(date):
            fast = None
            @classmethod
            def today(cls): return cls.fast
        for refit, idag, forfalden in (("2026-09", "2027-08-31", False), ("2026-09", "2027-09-01", True),
                                       ("2027-04", "2027-08-31", False), ("2027-04", "2027-09-01", True),
                                       ("2026-10", "2027-08-31", False), ("2026-10", "2027-09-01", True)):
            Fast.fast = date.fromisoformat(idag)
            with tempfile.TemporaryDirectory() as t:
                raw, here = Path(t) / "raw", Path(t) / "v5"
                shutil.copytree(self.raw / self.today, raw / idag); shutil.copytree(self.here, here)
                W = json.loads((here / "weights.json").read_text(encoding="utf-8")); W["refit_maaned"] = refit
                (here / "weights.json").write_text(json.dumps(W), encoding="utf-8")
                with mock.patch.object(M, "date", Fast):
                    out = self._motor([], raw=raw, here=here)
            self.assertEqual("september-rekalibrering er forfalden" in out, forfalden, (refit, idag))

    def test_diagnostik_sektionen_printes_og_dumpes_naar_filen_findes(self):
        """Uden diagnostik.json i temp-mappen springer de andre tests sektion 8 helt over — og den koerer EFTER
        hovedbogsraekken er skrevet, saa et crash der efterlod en raekke uden dashboard."""
        with tempfile.TemporaryDirectory() as t:
            here = Path(t) / "v5"; shutil.copytree(self.here, here)
            shutil.copy(HERE / "diagnostik.json", here / "diagnostik.json")
            ud = Path(t) / "d.json"
            out = self._motor(["--json", str(ud)], here=here)
            d = json.loads(ud.read_text(encoding="utf-8"))
        for s in ("4.1 Episode-tabel", "4.2 LOEO", "4.3 Domsregler", "4.4 Historisk", "4.5 Oracle-fri", "§7.3", "§3.6 Baseline"):
            self.assertIn(s, out)
        self.assertNotIn("diagnostik.json er fra kalibrering", out)         # diagnostikkens manifest_hash = weights.json's
        self.assertIsNotNone(d["diagnostik"])

    def test_fuldmodel_uden_vaegte_crasher_ikke_og_json_er_gyldig(self):
        """finalize6 skriver fuldmodel={features, status:'unavailable — CAPE stale', note} naar multpl er nede ved
        en rekalibrering (accepteret design). Motor crashede da med KeyError 'mu' hver maaned til naeste refit,
        og dashboard.json fik en bar NaN, som JSON.parse afviser."""
        with tempfile.TemporaryDirectory() as t:
            here = Path(t) / "v5"; shutil.copytree(self.here, here)
            W = json.loads((here / "weights.json").read_text(encoding="utf-8"))
            W["fuldmodel"] = dict(features=W["fuldmodel"]["features"], status="unavailable — CAPE stale",
                                  note=W["fuldmodel"].get("note", ""))
            (here / "weights.json").write_text(json.dumps(W), encoding="utf-8")
            ud = here.parent / "d.json"
            out = self._motor(["--json", str(ud)], here=here)
            def ingen_nan(c):
                raise AssertionError(f"ugyldig JSON-konstant {c}")
            d = json.loads(ud.read_text(encoding="utf-8"), parse_constant=ingen_nan)
        self.assertIn("unavailable", out)
        fmb = next(b for b in d["benchmarks"] if b["navn"].startswith("fuldmodel"))
        self.assertIsNone(fmb["live_p"])
        self.assertTrue(all(i["z"] is None for i in d["inputs"] if not i["operationel"]))   # F13: kun kurvens z (mod op)
        Wd = W["op"]
        kz = next(i for i in d["inputs"] if i["operationel"])
        self.assertAlmostEqual(kz["z"], round((kz["vaerdi"] - Wd["mu"]["curve"]) / Wd["sd"]["curve"], 4), places=3)
        normal = self.here.parent / "d_normal.json"
        self._motor(["--json", str(normal)])
        n = json.loads(normal.read_text(encoding="utf-8"))
        self.assertEqual((d["p"], d["baand"], d["dom"]), (n["p"], n["baand"], n["dom"]))    # curve-only koerer videre

    def test_allow_stale_logfoerer_aldrig(self):
        """--allow-stale gaelder aflaesningen; et 50 dage gammelt snapshot maa ikke blive maanedens hovedbogsraekke."""
        with tempfile.TemporaryDirectory() as t:
            gl = (date.today() - timedelta(days=50)).isoformat()
            raw = Path(t) / "raw"; shutil.copytree(self.raw / self.today, raw / gl)
            here = Path(t) / "v5"; shutil.copytree(self.here, here)
            logf = here.parent / "LOG.md"
            logf.write_text("| logget | snapshot | P | baand | basisrate | dom | kurve | antaending | note | kalibrering |"
                            + chr(10) + "|---|" + chr(10), encoding="utf-8")
            out = self._motor(["--allow-stale", "--log"], raw=raw, here=here)
            self.assertIn("--log AFVIST: snapshottet er 50 dage gammelt", out)
            self.assertNotIn("LOGGET som raekke", out)
            self.assertNotIn(f"| {gl} |", logf.read_text(encoding="utf-8"))

    def test_crlf_i_annonceringstabellen_udloeser_ikke_rekalibrering(self):
        """§3.2b: formatering udloeser ikke. En Windows-checkout med core.autocrlf gav CRLF -> ny byte-hash ->
        'REKALIBRERING PAAKRAEVET' og blokeret --log."""
        with tempfile.TemporaryDirectory() as t:
            here = Path(t) / "v5"; shutil.copytree(self.here, here)
            f = here / "nber_announcements.csv"
            f.write_bytes(f.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
            out = self._motor([], here=here)
        self.assertNotIn("nber_announcements.csv er aendret", out)

    def test_cpi_12m_er_tolv_kalendermaaneder(self):
        out = self._motor([])
        s = M.udfyld_huller(C.read_fred(self.raw / self.today, "CPIAUCSL"))[0]
        k = max(s)
        linje = next(ln for ln in out.splitlines() if "CPI (SA) 3m/6m/12m ann." in ln)
        self.assertIn(f"/ {(s[k] / s[(k[0] - 1, k[1])] - 1) * 100:.1f}%", linje)

    def test_oktober_cpi_2026_crasher_ikke_og_hullet_markeres(self):
        """FRED har tomme felter for CPI 2025-10 (BLS-shutdown). Naar oktober-CPI 2026 er udgivet, slog motor
        (2025, 10) op og fejlede med KeyError — november-ritualet ville vaere blokeret."""
        with tempfile.TemporaryDirectory() as t:
            raw = Path(t) / "raw"; snap = raw / self.today
            shutil.copytree(self.raw / self.today, snap)
            nl = chr(10)
            for sid in ("CPIAUCNS", "CPIAUCSL"):
                f = snap / f"{sid}.csv"
                linjer = f.read_text(encoding="utf-8").splitlines()
                rk = [ln.split(",")[0] + "," if ln.startswith("2025-10-01") else ln      # hullet, uanset vintage
                      for ln in linjer[1:] if ln[:7] < "2026-10"]
                y, m, v = int(rk[-1][:4]), int(rk[-1][5:7]), float(rk[-1].split(",")[1])
                while (y, m) < (2026, 10):
                    y, m, v = (y, m + 1, v * 1.003) if m < 12 else (y + 1, 1, v * 1.003)
                    rk.append(f"{y}-{m:02d}-01,{v:.3f}")
                f.write_text(linjer[0] + nl + nl.join(rk) + nl, encoding="utf-8")
            out = self._motor([], raw=raw)
            sa = C.read_fred(snap, "CPIAUCSL")
        self.assertIn("DATAHUL: CPIAUCNS 2025-10 mangler (BLS udgav aldrig oktober 2025", out)
        okt25 = (sa[(2025, 9)] * sa[(2025, 11)]) ** 0.5
        linje = next(ln for ln in out.splitlines() if "CPI (SA) 3m/6m/12m ann." in ln)
        self.assertIn(f"/ {(sa[(2026, 10)] / okt25 - 1) * 100:.1f}% (2025-10 interpoleret)", linje)


# ============================================================== debate.py
class TestMotorHelpers(unittest.TestCase):
    """read_fred_raw + ann_rate — indfoert da claims/permits-pladserne blev udfyldt."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def _skriv(self, navn, raekker):
        nl = chr(10)
        (self.tmp / navn).write_text(
            "observation_date,V" + nl + "".join(f"{d},{v}{nl}" for d, v in raekker),
            encoding="utf-8")

    def test_raw_bevarer_alle_ugeobs(self):
        """C.read_fred kollapser ugedata til maanedens sidste obs; raw maa ikke."""
        uger = [("2026-08-01", "200000"), ("2026-08-08", "212000"),
                ("2026-08-15", "207000"), ("2026-08-22", "204000")]
        self._skriv("ICSA.csv", uger)
        raw = M.read_fred_raw(self.tmp, "ICSA")
        self.assertEqual(len(raw), 4)
        self.assertEqual(raw[0], ("2026-08-01", 200000.0))
        self.assertEqual(sum(v for _, v in raw) / 4, 205750.0)
        # kontrasten der begrunder helperen:
        self.assertEqual(len(C.read_fred(self.tmp, "ICSA")), 1)

    def test_raw_springer_punktum_over(self):
        self._skriv("X.csv", [("2026-08-01", "1.0"), ("2026-08-08", "."), ("2026-08-15", "3.0")])
        self.assertEqual([v for _, v in M.read_fred_raw(self.tmp, "X")], [1.0, 3.0])

    def test_tal_af_parser_og_fejler_stille(self):
        self.assertEqual(M.tal_af("18.0%", 0.01), 0.18)
        self.assertEqual(M.tal_af("+0.87"), 0.87)
        self.assertEqual(M.tal_af("14,4%", 0.01), 0.144)
        for skidt in ("", "ingen", None, "ikke skelnelig"):
            self.assertIsNone(M.tal_af(skidt))

    def test_laes_hovedbog_tager_alle_kolonner_og_springer_resten_over(self):
        nl = chr(10)
        logf = self.tmp / "LOG.md"
        logf.write_text(
            "# HOVEDBOG" + nl
            + "| logget | snapshot | P | baand | basisrate | dom | kurve | antaending | note |" + nl
            + "|---|---|" + nl
            + "| 2026-08-12 | 2026-08-12 | 20.1% | 14.4-29.2% | 18.2% | ikke skelnelig | +0.87 | ingen |  |" + nl
            + "| 2026-09-09 | 2026-09-09 | 18.0% | 12.7-26.3% | 18.2% | ikke skelnelig | +0.96 | ingen | note her |" + nl,
            encoding="utf-8")
        hb = M.laes_hovedbog(logf)
        self.assertEqual(len(hb), 2)
        self.assertEqual(hb[0]["logget"], "2026-08-12")
        self.assertEqual(hb[0]["note"], "")
        self.assertEqual(hb[1]["note"], "note her")
        self.assertEqual(hb[1]["kurve"], "+0.96")

    def test_laes_hovedbog_uden_fil_giver_tom_liste(self):
        self.assertEqual(M.laes_hovedbog(self.tmp / "findes-ikke.md"), [])

    def test_ann_rate_annualiserer(self):
        # 1% pr. maaned i 3 maaneder -> (1,01^3)^4 - 1 = 12,68%
        s = {(2026, m): 100 * 1.01 ** (m - 1) for m in range(1, 5)}
        self.assertAlmostEqual(M.ann_rate(s, 3), ((1.01 ** 3) ** 4 - 1) * 100, places=6)

    def test_ann_rate_for_kort_serie_giver_nan(self):
        self.assertTrue(np.isnan(M.ann_rate({(2026, 1): 100.0}, 3)))

    def test_september_forfald_nulstilles_ikke_af_udloest_refit(self):
        """§3.2b: en udloest refit nulstiller ikke september-planen. Den gamle formel gav (aar+1, 9) for
        alle refit-maaneder <= 9 og (aar+2, 9) ellers — et aar for sent for alle maaneder undtagen september."""
        self.assertEqual(M.september_forfald("2026-09"), (2027, 9))
        self.assertEqual(M.september_forfald("2027-04"), (2027, 9))    # NBER-udloest refit i april
        self.assertEqual(M.september_forfald("2027-01"), (2027, 9))
        self.assertEqual(M.september_forfald("2027-10"), (2028, 9))    # september-refit koert paa et oktober-snapshot

    def test_endelig_goer_nan_til_null(self):
        d = M.endelig({"a": float("nan"), "b": [1.0, float("inf"), {"c": np.float64("nan")}], "d": "nan", "e": 2})
        self.assertEqual(d, {"a": None, "b": [1.0, None, {"c": None}], "d": "nan", "e": 2})
        json.dumps(d, allow_nan=False)

    def test_inversionsnote_igangvaerende_sluttet_og_live(self):
        fk = [(2026, m) for m in range(1, 7)]
        self.assertEqual(M.inversionsnote(fk, np.array([0.5, -0.2, -0.4, 0.1, 0.3, 0.2]), 0.2),
                         "sluttede 2026-03 (3 mdr siden), dybde -0.40pp")
        self.assertEqual(M.inversionsnote(fk, np.array([0.5, 0.1, 0.2, -0.1, -0.3, -0.2]), -0.2),
                         "igangvaerende siden 2026-04 (3 mdr t.o.m. 2026-06), dybde hidtil -0.30pp")
        n = M.inversionsnote(fk, np.array([0.5, -0.2, -0.4, 0.1, 0.3, 0.2]), -0.05)
        self.assertTrue(n.startswith("live-kurven (trailing maaned) er inverteret (-0.05pp); paa maanedstal sluttede 2026-03"))
        self.assertEqual(M.inversionsnote(fk, np.array([0.5] * 6), 0.5), "ingen inversion i historikken")
        # spejlbilledet: seneste maanedstal inverteret, men live-kurven er allerede positiv
        self.assertEqual(M.inversionsnote(fk, np.array([0.5, 0.1, 0.2, -0.1, -0.3, -0.2]), 0.15),
                         "paa maanedstal igangvaerende siden 2026-04 (3 mdr t.o.m. 2026-06), dybde hidtil -0.30pp; "
                         "live-kurven er ikke laengere inverteret (+0.15pp)")

    def test_claims_maaned_bruger_maanedsmiddel_og_kun_komplette_maaneder(self):
        """Oktober 2026 har 5 loerdage (3., 10., 17., 24., 31.): med data t.o.m. 24/10 er oktober IKKE komplet
        (den gamle '>= 4 obs'-regel sagde komplet). Statistikken er maanedsmidlen, ikke sidste uge."""
        uger = lambda aar, mdr, dage, v: [(f"{aar}-{mdr:02d}-{d:02d}", v + i) for i, d in enumerate(dage)]
        raw = (uger(2025, 9, (6, 13, 20, 27), 200.0) + uger(2025, 10, (4, 11, 18, 25), 210.0)
               + uger(2026, 9, (5, 12, 19, 26), 220.0) + uger(2026, 10, (3, 10, 17, 24), 240.0))
        full, pct = M.claims_12m_maaned(raw)
        self.assertEqual(full, "2026-09")
        self.assertAlmostEqual(pct, (221.5 / 201.5 - 1) * 100)
        full, pct = M.claims_12m_maaned(raw + [("2026-10-31", 250.0)])
        self.assertEqual(full, "2026-10")
        self.assertAlmostEqual(pct, ((240 + 241 + 242 + 243 + 250) / 5 / 211.5 - 1) * 100)

    def test_mdr_foer_krydser_aarsskifte(self):
        self.assertEqual(M.mdr_foer((2026, 1), 1), (2025, 12))
        self.assertEqual(M.mdr_foer((2026, 10), 12), (2025, 10))
        self.assertEqual(M.mdr_foer((2026, 3), 27), (2023, 12))

    def test_udfyld_huller_interpolerer_log_lineaert(self):
        s, fyldt = M.udfyld_huller({(2025, 9): 100.0, (2025, 11): 121.0})
        self.assertEqual(fyldt, [(2025, 10)])
        self.assertAlmostEqual(s[(2025, 10)], 110.0)
        s, fyldt = M.udfyld_huller({(2025, 12): 100.0, (2026, 3): 133.1})
        self.assertEqual(fyldt, [(2026, 1), (2026, 2)])
        self.assertAlmostEqual(s[(2026, 1)], 110.0)
        self.assertAlmostEqual(s[(2026, 2)], 121.0)
        self.assertEqual(M.udfyld_huller({(2026, 1): 1.0, (2026, 2): 2.0}), ({(2026, 1): 1.0, (2026, 2): 2.0}, []))

    def test_ann_rate_er_kalenderbaseret_ved_hul(self):
        """FRED mangler 2025-10 (BLS-shutdown). 12m fra 2026-09 skal maales fra 2025-09; positionelt
        blev det 2025-08 (13 maaneder) — 10/10-dashboardet viste CPI 12m 3,7 % mod sande 3,4 %."""
        s = {M.mdr_foer((2026, 9), n): 100 * 1.003 ** (13 - n) for n in range(14) if n != 11}
        self.assertNotIn((2025, 10), s)
        self.assertAlmostEqual(M.ann_rate(s, 12), (1.003 ** 12 - 1) * 100, places=9)
        s[(2026, 10)] = s[(2026, 9)] * 1.003            # startmaaneden er selve hullet
        self.assertTrue(np.isnan(M.ann_rate(s, 12)))
        self.assertAlmostEqual(M.ann_rate(M.udfyld_huller(s)[0], 12), (1.003 ** 12 - 1) * 100, places=9)


class TestSpine(unittest.TestCase):
    """RAADETS_V501 §1 + §1.7: rygrad-guards. Defekt-fixture = den frosne Yale-fil."""

    def _multpl_html(self, n_maaneder, foerste=(1871, 2), live=True):
        MON = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
        y, m = foerste
        rows = []
        for i in range(n_maaneder):
            rows.append(f"<tr><td>{MON[m-1]} 1, {y}</td> <td> &#x2002; {10 + (i % 30) * 0.5:.2f} </td></tr>")
            m += 1
            if m > 12:
                y, m = y + 1, 1
        rows.reverse()
        if live:
            rows.insert(0, f"<tr><td>{MON[m-1]} 18, {y}</td> <td> &#x2002; 99.99 </td></tr>")
        return "<table id='datatable'>" + "".join(rows) + "</table>"

    def test_parse_multpl_udelader_live_raekke_og_aaben_maaned(self):
        html = self._multpl_html(1870)
        out = S.parse_multpl(html, today=date(2026, 9, 19))
        self.assertEqual(min(out), "1871-02")
        self.assertNotIn("2026-09", out)          # loebende maaned er ikke lukket
        self.assertTrue(all(v < 99 for v in out.values()))

    def test_parse_multpl_fejler_haardt_ved_format_drift(self):
        with self.assertRaisesRegex(RuntimeError, "raekker"):
            S.parse_multpl(self._multpl_html(500), today=date(2026, 9, 19))
        with self.assertRaisesRegex(RuntimeError, "foerste maaned"):
            S.parse_multpl(self._multpl_html(1870, foerste=(1880, 1)), today=date(2026, 9, 19))

    def test_monthly_mean_aggregerer_uger_til_middel(self):
        rows = [("2026-08-01", "200000"), ("2026-08-08", "212000"), ("2026-08-15", "."),
                ("2026-08-22", "204000"), ("2026-09-05", "206000")]
        m = S.monthly_mean(rows)
        self.assertEqual(m["2026-08"], 205333.33333333334)
        self.assertEqual(m["2026-09"], 206000.0)

    def test_overlap_check_bestaar_paa_identiske_og_fejler_paa_skaeve(self):
        sh = {f"2016-{m:02d}": (2000.0 + m, 240.0, 2.0, 25.0) for m in range(1, 13)}
        sh.update({f"1995-{m:02d}": (500.0, 150.0, 6.0, 20.0) for m in range(1, 13)})
        sp = {k: v[0] * 1.0002 for k, v in sh.items()}
        ca = {k: v[3] * 0.9999 for k, v in sh.items()}
        r = S.overlap_check(sh, sp, ca)
        self.assertTrue(r["bestaaet"]); self.assertEqual(r["sp500_undtagelser"], [])
        ca_skaev = dict(ca); ca_skaev["1995-06"] = 20.0 * 1.05           # 5 % > max 1 %
        self.assertFalse(S.overlap_check(sh, sp, ca_skaev)["bestaaet"])

    def test_outlier_check_fanger_niveau_og_spring(self):
        ok = {"2026-01": 30.0, "2026-02": 31.0, "2026-03": 30.5}
        self.assertEqual(S.outlier_check(ok), [])
        bad = dict(ok); bad["2026-04"] = 61.0; bad["2026-05"] = 30.0
        probs = S.outlier_check(bad)
        self.assertTrue(any("niveau" in p for _, p in probs))
        self.assertTrue(any("m/m" in p for _, p in probs))

    def test_build_spine_er_shiller_til_seam_og_komposit_kun_hvor_alt_findes(self):
        sh = {"2023-06": (4200.0, 304.0, 3.8, 29.0), "2023-07": (4500.0, 305.0, 3.9, 30.9),
              "2023-08": (4457.36, 305.98, 4.17, 30.47), "2023-09": (4515.77, 306.13, 4.09, 30.81)}
        sp = {"2023-08": 4457.4, "2023-09": 4409.1, "2023-10": 4269.0}
        cpi = {"2023-08": 307.0, "2023-09": 307.8, "2023-10": 307.7}
        gs = {"2023-08": 4.17, "2023-09": 4.38, "2023-10": 4.80}
        cape = {"2023-08": 30.09, "2023-09": 29.80}                     # ingen 2023-10 -> stop
        rows = S.build_spine(sh, sp, cpi, gs, cape)
        self.assertEqual([r[0] for r in rows], ["2023-06", "2023-07", "2023-08", "2023-09"])
        self.assertEqual(rows[1][5], "shiller"); self.assertEqual(rows[2][5], "fred+multpl")
        self.assertEqual(rows[3][1], 4409.1)                               # Shillers forloebige 4515.77 erstattet

    def test_build_spine_tolererer_et_cpi_hul_men_ikke_manglende_sp500_eller_cape(self):
        sh = {"2023-07": (4500.0, 305.0, 3.9, 30.9)}
        sp = {"2023-08": 4457.4, "2023-09": 4409.1, "2023-10": 4269.0, "2023-11": 4460.0}
        cpi = {"2023-08": 307.0, "2023-10": 307.7, "2023-11": 307.1}       # 2023-09 mangler (som BLS okt-2025)
        gs = {}
        cape = {"2023-08": 30.09, "2023-09": 29.80, "2023-10": 28.70}      # ingen 2023-11 -> stop der
        rows = S.build_spine(sh, sp, cpi, gs, cape)
        self.assertEqual([r[0] for r in rows], ["2023-07", "2023-08", "2023-09", "2023-10"])
        self.assertIsNone(rows[2][2])                                     # CPI-hul skrives tomt (NaN)
        self.assertEqual(S.cpi_huller(rows), (["2023-09"], []))
        # en endnu ikke udgivet sidste maaned er ikke et 'aegte hul' (10/10-metaen kaldte 2026-09 et hul)
        rows2 = S.build_spine(sh, sp, {k: v for k, v in cpi.items() if k != "2023-10"}, gs, cape)
        self.assertEqual(S.cpi_huller(rows2), ([], ["2023-09", "2023-10"]))

    def test_staleness_er_udgivelsesbevidst(self):
        today = date(2026, 9, 19)
        friske = {"GS10": "2026-08-01", "CPIAUCNS": "2026-08-01", "A191RL1Q225SBEA": "2026-04-01",
                  "DTB3": "2026-09-17", "spine": "2026-08-01"}
        self.assertEqual(S.staleness(friske, today), {})
        # augustdata stemplet 1/8 er 49 dage gamle 19/9 og stadig nyeste udgivelse (Astra R4)
        self.assertEqual(S.staleness({"GS10": "2026-08-01"}, today), {})
        st = S.staleness({"GS10": "2026-05-01", "PERMIT": "2026-05-01"}, today)
        self.assertTrue(st["GS10"]["kritisk"]); self.assertFalse(st["PERMIT"]["kritisk"])

    def test_defekt_fixture_den_frosne_yale_fil_flages(self):
        """Den test der ville have fanget fejlen i oktober 2023 (Kimi R1)."""
        yale = HERE / "manual" / "shiller_yale_2023-09.csv"
        if not yale.exists():
            yale = HERE / "manual" / "shiller.csv"
        sidste = [l.split(",")[0] for l in yale.read_text(encoding="utf-8").splitlines()[1:] if l][-1]
        st = S.staleness({"spine": sidste + "-01"}, date(2023, 10, 17))    # dagen Yale sidst opdaterede
        self.assertEqual(st, {})                                          # frisk DEN dag ...
        st = S.staleness({"spine": sidste + "-01"}, date(2024, 1, 15))
        self.assertIn("spine", st)                                        # ... forældet tre maaneder senere

    def test_nyeste_snapshot_har_frisk_rygrad(self):
        """RØD FØR REPARATIONEN (v5.0.1 §8): det nyeste komplette snapshots rygrad maa ikke vaere stale
        paa hentedagen. Bevis for at guarden ville have fanget den frosne spine."""
        snap = C.find_snapshot([])
        meta = json.loads((snap / "meta.json").read_text(encoding="utf-8"))
        hentet = date.fromisoformat(meta["retrieved_utc"][:10])
        f = snap / "spine.csv" if (snap / "spine.csv").exists() else snap / "shiller.csv"
        sidste = [l.split(",")[0] for l in f.read_text(encoding="utf-8").splitlines()[1:] if l][-1]
        st = S.staleness({"spine": sidste + "-01"}, hentet)
        self.assertEqual(st, {}, f"rygraden i {snap.name} slutter {sidste}: {st}")


class TestEligibility(unittest.TestCase):
    """RAADETS_V501 §2 (raekkeunivers, gate) + §3.5 (gulv, fortegnsbevidst audit) + §1.5a (legacy-replay)."""

    def _D(self, qks):
        return dict(qk=qks, qend=np.array([A2.qend_idx(y, q) for y, q in qks]),
                    year=np.array([y for y, _ in qks]), F=np.zeros((len(qks), 1)), feats=["curve"])

    def test_ny_top_uden_usrec_onset_stopper_hoejlydt(self):
        """§3.2b: en ny top-raekke som snapshottets USREC endnu ikke viser, blev ignoreret i stilhed — og
        rekalibreringen 'forbrugte' triggeren (annonceringstabellens hash) uden at toppen indgik."""
        eps = A2.episodes_from_usrec(A2.load_usrec(REAL_SNAP))
        self.assertEqual(len(A2.load_announcements(eps)), len(eps))          # de committede raekker matcher alle
        with tempfile.TemporaryDirectory() as t:
            tekst = (HERE / "nber_announcements.csv").read_text(encoding="utf-8").rstrip(chr(10))
            (Path(t) / "nber_announcements.csv").write_text(tekst + chr(10) + "peak_2026,2026-05,2026-10-05,test" + chr(10),
                                                           encoding="utf-8")
            with mock.patch.object(A2, "HERE", Path(t)), self.assertRaisesRegex(SystemExit, "matcher intet USREC-onset"):
                A2.load_announcements(eps)

    def test_gulv_holder_umodne_origins_ude_aldrig_nul(self):
        # een onset 2030-01 (midx), trough 2030-06; R = 2029-09: origins hvis vindue+18 rager ud over R er UDE
        eps = [(A2.midx(2030, 1), A2.midx(2030, 6))]
        avail = {eps[0][0]: A2.midx(2030, 7)}
        usrec = {i: 0 for i in range(A2.midx(2020, 1), A2.midx(2031, 1))}
        for i in range(eps[0][0], eps[0][1] + 1):
            usrec[i] = 1
        qks = [(y, q) for y in range(2025, 2030) for q in (1, 2, 3, 4)]
        D = self._D(qks)
        R = A2.midx(2029, 9)
        elig, yR = A2.eligible_fit(D, eps, avail, usrec, R)
        sidste_ok = max(j for j in range(len(qks)) if elig[j])
        self.assertEqual(qks[sidste_ok], (2027, 1))             # qend 2027-03 + 12 + 18 = 2029-09 = R -> med
        self.assertFalse(elig[sidste_ok + 1])                    # 2027Q2 rager ud over R -> ude, ikke 0
        self.assertEqual(yR[~elig].sum(), 0.0)                   # ingen label paa ikke-berettigede
        # samme onset annonceret FOER R: origins inde i recessionen er ude
        R2 = A2.midx(2031, 12)
        elig2, yR2 = A2.eligible_fit(D, eps, avail, usrec, R2)
        # origins med onset i vinduet faar label 1 (2029Q1..2029Q4: vinduer 2029-04.. daekker 2030-01)
        # 2029Q3/Q4 har onset i vinduet men er UMODNE ved R2 (qend + 30 mdr > R2) -> ude; sidste positive = 2029Q2
        self.assertEqual([qks[j] for j in range(len(qks)) if elig2[j] and yR2[j] == 1.0][-1], (2029, 2))
        self.assertFalse(elig2[qks.index((2029, 3))])

    def test_origin_audit_er_fortegnsbevidst(self):
        forrige = [[2022, 3, 0], [2022, 4, 0], [2023, 1, 0], [2023, 2, 1]]
        nye = [[2022, 4, 0], [2023, 1, 0], [2023, 2, 0], [2023, 3, 0], [2023, 4, 0]]
        a = A2.origin_audit(forrige, nye)
        self.assertEqual(a["tilfoejede"], ["2023Q3", "2023Q4"])
        self.assertEqual(a["fjernede"], ["2022Q3"])
        self.assertEqual(a["omlabelede"], ["2023Q2"])
        self.assertTrue(a["identitet_ok"])                       # 5 = 4 + 2 - 1
        self.assertEqual(A2.origin_audit(None, nye)["n_forrige"], 0)

    def test_gate_assertion_kraever_identiske_origin_identiteter(self):
        D1 = self._D([(2020, 1), (2020, 2)]); D2 = self._D([(2020, 1), (2020, 3)])
        self.assertFalse(A2.samme_origins(D1, D2))               # samme antal, forskellig identitet
        self.assertTrue(A2.samme_origins(D1, self._D([(2020, 1), (2020, 2)])))

    def test_raekkeunivers_starter_ved_protokolkonstanten(self):
        D = A2.build_dataset(REAL_SNAP, ["curve"])
        self.assertEqual(D["qk"][0], C.START_QK)

    def test_legacy_replay_reproducerer_v50_vaegte_eksakt(self):
        """§1.5a: den frosne Yale-rygrad gennem den nye kaede -> w = [-2.1755, -1.6907], n_obs 264."""
        yale = "shiller_yale_2023-09.csv" if (REAL_SNAP / "shiller_yale_2023-09.csv").exists() else "shiller.csv"
        usrec = A2.load_usrec(REAL_SNAP); eps = A2.episodes_from_usrec(usrec); avail = A2.load_announcements(eps)
        Dc = A2.build_dataset(REAL_SNAP, ["curve"], spine_file=yale)
        elig, yR = A2.eligible_fit(Dc, eps, avail, usrec, A2.midx(2026, 9))
        X = Dc["F"][elig]; y = yR[elig]
        w = C.fit((X - X.mean(0)) / X.std(0, ddof=1), y)
        self.assertEqual([round(float(v), 4) for v in w], [-2.1755, -1.6907])
        self.assertEqual(int(elig.sum()), 264)


class TestErratumAggregering(unittest.TestCase):
    """RAADETS_V501 §5: den praeregistrerede spec (maanedsmiddel af ICSA) implementeret korrekt."""

    def test_icsa_maanedsmiddel_bruger_alle_uger_og_read_fred_kollapser(self):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t)
            (d / "ICSA.csv").write_text("observation_date,ICSA" + chr(10) + "2026-08-01,200000" + chr(10)
                                        + "2026-08-08,212000" + chr(10) + "2026-08-15,207000" + chr(10)
                                        + "2026-08-22,204000" + chr(10) + "2026-09-05,206000" + chr(10), encoding="utf-8")
            m = A4.icsa_maanedsmiddel(d)
            self.assertEqual(m[(2026, 8)], 205750.0)                       # middel af fire uger
            self.assertEqual(m[(2026, 9)], 206000.0)
            # fejlklassen, dokumenteret: read_fred beholder kun maanedens sidste uge, og den gamle
            # monthly_mean() kunne derfor ikke aendre noget
            gammel = A4.monthly_mean(C.read_fred(d, "ICSA"))
            self.assertEqual(gammel[(2026, 8)], 204000.0)


class TestLiveKurve(unittest.TestCase):
    """Live-input (drift 2026-09-28): kurven maales paa trailing maaned af daglige DGS10/DTB3."""

    def test_daglige_maanedssnit_er_gs10_og_tb3ms(self):
        """Paastanden der baerer hele aendringen: GS10/TB3MS ER maanedssnit af DGS10/DTB3.
        Verificeret 2026-09-28: max 0,50bp afvigelse i alle 776 maaneder siden 1962 (afrunding)."""
        par = (("DGS10", "GS10"), ("DTB3", "TB3MS"))
        for dag, mnd in par:
            daglig = C.read_fred_daily(REAL_SNAP, dag)
            maaned = C.read_fred(REAL_SNAP, mnd)
            agg = {}
            for d, v in daglig:
                agg.setdefault((int(d[:4]), int(d[5:7])), []).append(v)
            ks = [k for k in agg if k in maaned and k >= (1990, 1)]
            self.assertGreater(len(ks), 400)
            maks = max(abs(float(np.mean(agg[k])) - maaned[k]) for k in ks)
            self.assertLessEqual(maks, 0.01, f"{dag} vs {mnd}: max afvigelse {maks*100:.2f}bp")

    def test_maaned_foer_klipper_til_maanedens_laengde(self):
        self.assertEqual(C.maaned_foer("2026-09-24"), "2026-08-24")
        self.assertEqual(C.maaned_foer("2026-03-31"), "2026-02-28")
        self.assertEqual(C.maaned_foer("2024-03-30"), "2024-02-29")
        self.assertEqual(C.maaned_foer("2026-01-15"), "2025-12-15")

    def test_trailing_vindue_og_fallback_til_maanedstal(self):
        nl = chr(10)
        with tempfile.TemporaryDirectory() as t:
            d = Path(t)
            (d / "GS10.csv").write_text("observation_date,GS10" + nl + "2026-07-01,4.60" + nl + "2026-08-01,4.68" + nl, encoding="utf-8")
            (d / "TB3MS.csv").write_text("observation_date,TB3MS" + nl + "2026-07-01,3.73" + nl + "2026-08-01,3.72" + nl, encoding="utf-8")
            rk10 = [("2026-08-20", "4.70"), ("2026-08-25", "4.70"), ("2026-09-10", "5.00"), ("2026-09-24", "5.30")]
            rk3 = [("2026-08-20", "3.70"), ("2026-08-25", "3.70"), ("2026-09-10", "3.90"), ("2026-09-24", "4.10"),
                   ("2026-09-25", ".")]
            (d / "DGS10.csv").write_text("observation_date,DGS10" + nl + "".join(f"{a},{b}{nl}" for a, b in rk10), encoding="utf-8")
            (d / "DTB3.csv").write_text("observation_date,DTB3" + nl + "".join(f"{a},{b}{nl}" for a, b in rk3), encoding="utf-8")
            L = C.live_kurve(d)
            self.assertEqual(L["kilde"], "daglig")
            self.assertEqual(L["vindue"], ["2026-08-25", "2026-09-24"])         # 20/8 ligger foer 24/8 -> ude
            self.assertEqual(L["n_dage"], 3)
            self.assertAlmostEqual(L["y10"], (4.70 + 5.00 + 5.30) / 3)
            self.assertAlmostEqual(L["curve"], (1.00 + 1.10 + 1.20) / 3)
            self.assertEqual(L["y10_seneste"], ["2026-09-24", 5.30])
            self.assertAlmostEqual(L["maanedlig"]["curve"], 0.96)
            (d / "DGS10.csv").unlink()
            L2 = C.live_kurve(d)
            self.assertEqual(L2["kilde"], "maanedlig")
            self.assertAlmostEqual(L2["curve"], 0.96)
            self.assertIn("mangler", L2["note"])

    def test_vindue_graense_er_streng_og_kun_faelles_handelsdage_taeller(self):
        """Vinduet er STRENGT efter samme dato forrige maaned, og en dag hvor kun det ene ben findes (helligdag) taeller ikke."""
        nl = chr(10)
        with tempfile.TemporaryDirectory() as t:
            d = Path(t)
            (d / "GS10.csv").write_text("observation_date,GS10" + nl + "2026-08-01,4.00" + nl, encoding="utf-8")
            (d / "TB3MS.csv").write_text("observation_date,TB3MS" + nl + "2026-08-01,2.00" + nl, encoding="utf-8")
            rk10 = [("2026-08-24", "9.00"), ("2026-08-25", "4.00"), ("2026-09-02", "9.00"), ("2026-09-10", "4.00"), ("2026-09-24", "4.00")]
            rk3 = [("2026-08-24", "1.00"), ("2026-08-25", "2.00"), ("2026-09-10", "2.00"), ("2026-09-24", "2.00")]
            (d / "DGS10.csv").write_text("observation_date,DGS10" + nl + "".join(f"{a},{b}{nl}" for a, b in rk10), encoding="utf-8")
            (d / "DTB3.csv").write_text("observation_date,DTB3" + nl + "".join(f"{a},{b}{nl}" for a, b in rk3), encoding="utf-8")
            L = C.live_kurve(d)
        # 24/8 = maaned_foer(24/9) ligger PAA graensen -> ude; 2/9 findes kun i DGS10 -> ude
        self.assertEqual(L["vindue"], ["2026-08-25", "2026-09-24"]); self.assertEqual(L["n_dage"], 3)
        self.assertAlmostEqual(L["y10"], 4.0); self.assertAlmostEqual(L["tb3"], 2.0); self.assertAlmostEqual(L["curve"], 2.0)


class TestSnapshotIntegritet(unittest.TestCase):
    """Snapshots er uforanderlige: hver fil matcher sin hash i meta.json, og snapshot_sha256 genberegnes
    (fanger linjeskifts-konvertering, haandredigering og afkortede filer — ellers kontrolleres det intetsteds)."""
    def test_alle_committede_snapshots_matcher_deres_hashes(self):
        n = 0
        for d in sorted(p for p in C.RAW.iterdir() if p.is_dir() and (p / "meta.json").exists() and len(p.name) == 10):
            m = json.loads((d / "meta.json").read_text(encoding="utf-8"))
            hs = {f"{sid}.csv": v["sha256"] for sid, v in m["series"].items()}
            hs.update({fn: v["sha256"] for fn, v in m["manual"].items()})
            sp = m.get("spine", {})
            if sp.get("sha256"):
                hs["spine.csv"] = sp["sha256"]
            if sp.get("yale"):
                hs[sp["yale"]["fil"]] = sp["yale"]["sha256"]
            if sp.get("multpl", {}).get("sha256"):
                hs["multpl_cape.html"] = sp["multpl"]["sha256"]
            lokale = {f"{sid}.csv" for sid in S.LOKALE} | set(S.LOKALE_FILER)
            for fn, h in hs.items():
                if fn in lokale and not (d / fn).exists():
                    continue                          # F1/F12: committes ikke; hashen staar i meta og indgaar nedenfor
                self.assertEqual(sha((d / fn).read_bytes()), h, f"{d.name}/{fn} afviger fra hashen i meta.json")
            ryg = ([f"spine:{sp.get('sha256', '')}", f"yale:{sp.get('yale', {}).get('sha256', '')}",
                    f"multpl:{sp.get('multpl', {}).get('sha256', '')}"] if sp else [])       # foer v5.0.1 ingen rygrad i hashen
            kombineret = "".join(sorted(f"{k}:{v['sha256']}" for k, v in m["series"].items())
                                 + [f"{k}:{v['sha256']}" for k, v in sorted(m["manual"].items())] + ryg)
            self.assertEqual(sha(kombineret.encode()), m["snapshot_sha256"], d.name)
            n += 1
        self.assertGreaterEqual(n, 9)


class TestDebate(unittest.TestCase):
    def test_fejlet_genkald_overskriver_ikke_arkiveret_svar(self):
        """Et genkald med --only der fejler (fx netvaerk) skrev '[KALD FEJLEDE]' oven i rundens arkiverede svar."""
        m = D.MODELS[0]
        with tempfile.TemporaryDirectory() as t:
            rd = Path(t) / "runder" / "runde1"; rd.mkdir(parents=True)
            (rd / f"{m['slug']}.md").write_text("arkiveret svar", encoding="utf-8")
            fejl = dict(ok=False, model_id="x", text="[KALD FEJLEDE: test]", raw=None, prompt_tokens=0, completion_tokens=0)
            with mock.patch.object(D, "HERE", Path(t)), mock.patch.object(D, "call_model", lambda *a, **k: fejl), \
                 mock.patch.object(sys, "argv", ["debate.py", "round1", "--only", m["slug"]]), quiet(), \
                 self.assertRaises(SystemExit) as cm:
                D.main()
            self.assertEqual(cm.exception.code, 2)                                  # fejlede kald -> exit 2, som foer
            self.assertEqual((rd / f"{m['slug']}.md").read_text(encoding="utf-8"), "arkiveret svar")
        with mock.patch.object(sys, "argv", ["debate.py", "round1", "--only"]), self.assertRaisesRegex(SystemExit, "--only <slug>"):
            D.main()

    def test_read_round_laeser_arkivets_runde_mapper(self):
        r1 = D.read_round(1)
        self.assertEqual(len(r1), len(D.MODELS))
        self.assertIn("PROPOSAL: GPT-5.6 Sol", D.build_prompt("round2", D.MODELS[0]))

    def test_tom_runde_fejler_hoejlydt(self):
        with tempfile.TemporaryDirectory() as t:
            (Path(t) / "runder" / "runde1").mkdir(parents=True)
            with mock.patch.object(D, "HERE", Path(t)), self.assertRaises(SystemExit):
                D.build_prompt("round2", D.MODELS[0])


# ============================================================== kode-review 2026-10-15
class Test1015Roller(unittest.TestCase):
    """F18/F1: EEN rolletabel; kun P/refit-serier nedlaegger veto; licensbegraensede filer er lokale."""

    def test_veto_er_p_og_refit_og_kraevede_afledes(self):
        self.assertEqual(set(C.KRAEVEDE), set(S.VETO))
        self.assertTrue({"GS10", "TB3MS", "DGS10", "DTB3", "USREC"} <= set(S.VETO))
        for sid in ("BAMLH0A0HYM2", "ICSA", "PERMIT", "SP500", "MORTGAGE30US", "RIFSPPFAAD90NB"):
            self.assertNotIn(sid, S.VETO)
            self.assertIn(sid, F.RESERVE)
        self.assertEqual(set(S.LOKALE), {"BAMLH0A0HYM2", "SP500", "BAA10Y"})

    def test_gitignore_holder_lokale_filer_ude(self):
        gi = (HERE.parent / ".gitignore").read_text(encoding="utf-8")
        for sid in S.LOKALE:
            self.assertIn(f"v5/data/raw/*/{sid}.csv", gi)
        for fn in S.LOKALE_FILER:
            self.assertIn(f"v5/data/raw/*/{fn}", gi)

    def test_snapshot_uden_licensfiler_er_komplet(self):
        with tempfile.TemporaryDirectory() as t:
            d = make_snapshot(Path(t), "2026-01-01", series=list(S.VETO))
            self.assertTrue(C.snapshot_complete(d))


class Test1015Fetch(unittest.TestCase):
    """F23/F24/F2/F5/F25/F31 i fetch."""
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.prev = Path(self.tmp.name)
    def tearDown(self): self.tmp.cleanup()

    def test_rullende_vindue_er_ikke_en_revision(self):
        old = [("2020-01-01", "1.0"), ("2020-01-02", "1.1"), ("2020-01-03", "1.2")]
        (self.prev / "SP500.csv").write_bytes(fred_bytes(old))
        new = [("2020-01-02", "1.1"), ("2020-01-03", "1.2"), ("2020-01-06", "1.3")]
        b = fred_bytes(new)
        cur = dict(sha256=sha(b), last="2020-01-06", last_value="1.3")
        m = F.diff_mark(dict(sha256="x", last="2020-01-03", last_value="1.2"), self.prev, "SP500", F.parse_rows(b), cur)
        self.assertIn("rullende vindue", m); self.assertNotIn("REVIDERET", m)
        # en aendret vaerdi paa en faelles dato ER en revision — ogsaa i et rullende vindue
        new2 = [("2020-01-02", "9.9"), ("2020-01-03", "1.2"), ("2020-01-06", "1.3")]
        b2 = fred_bytes(new2)
        m2 = F.diff_mark(dict(sha256="x", last="2020-01-03", last_value="1.2"), self.prev, "SP500", F.parse_rows(b2),
                         dict(sha256=sha(b2), last="2020-01-06", last_value="1.3"))
        self.assertIn("REVIDERET", m2)

    def test_parse_rows_kolonne_til_ebp(self):
        b = b"date,gz_spread,ebp,est_prob\n2026-08-01,0.88,-0.23,0.13\n2026-09-01,0.93,-0.39,0.09\n"
        self.assertEqual(F.parse_rows(b, "ebp"), [("2026-08-01", "-0.23"), ("2026-09-01", "-0.39")])
        with self.assertRaises(RuntimeError):
            F.parse_rows(b)                                    # bred CSV uden kolonnevalg afvises stadig

    def test_refit_klar(self):
        ok, g = F.refit_klar({"multpl": {"sha256": "x"}, "sidste": "2026-09"}, [], {})
        self.assertTrue(ok); self.assertEqual(g, [])
        ok, g = F.refit_klar({"multpl": {"fejl": "x"}, "sidste": "2023-07"}, ["SP500"], {"spine": dict(sidste="2023-07-01")})
        self.assertFalse(ok); self.assertEqual(len(g), 3)

    def test_build_spine_baerer_lukkede_maaneder_og_fred_vinder(self):
        sh = {"2023-07": (4500.0, 305.0, 3.9, 30.9)}
        tidl = {"2023-08": 4457.4, "2023-09": 4409.1}
        sp = {"2023-09": 4410.0, "2023-10": 4269.0}           # 2023-08 er rullet ud af FRED-vinduet
        cape = {"2023-08": 30.09, "2023-09": 29.80, "2023-10": 28.7}
        rows = S.build_spine(sh, sp, {}, {}, cape, tidligere_sp500=tidl)
        self.assertEqual([r[0] for r in rows], ["2023-07", "2023-08", "2023-09", "2023-10"])
        self.assertEqual(rows[1][1], 4457.4)                   # baaret uaendret fra forrige rygrad
        self.assertEqual(rows[2][1], 4410.0)                   # FRED leverer stadig -> FRED

    def test_outlier_accepteret_par_springes_over_men_revision_fanges(self):
        cape = {"2026-01": 30.0, "2026-02": 20.0, "2026-03": 20.5}
        self.assertTrue(S.outlier_check(cape))
        self.assertEqual(S.outlier_check(cape, accepterede={"2026-02": 20.0}), [])
        cape["2026-02"] = 19.0                                 # revideret vaerdi -> fanges igen
        self.assertTrue(S.outlier_check(cape, accepterede={"2026-02": 20.0}))


class Test1015FetchMain(unittest.TestCase):
    """F5: multpl-udfald -> refit_klar false; F18: monitor-fejl er ikke veto (F24/F2 daekkes af TestFetchMain)."""
    setUp = TestFetchMain.setUp; tearDown = TestFetchMain.tearDown
    _run = TestFetchMain._run; meta = TestFetchMain.meta

    def test_multpl_udfald_er_komplet_men_ikke_refit_klar(self):
        self._run()
        m = self.meta(self.today)
        self.assertTrue(m["complete"]); self.assertFalse(m["spine"]["refit_klar"])
        self.assertTrue(any("multpl" in g for g in m["spine"]["refit_blokeret"]))
        self.assertIn("lokale_filer", m)

    def test_monitor_serie_fejl_nedlaegger_ikke_veto(self):
        self._run(fejler={"ICSA", "BAMLH0A0HYM2", "PERMIT"})
        m = self.meta(self.today)
        self.assertTrue(m["complete"])
        self.assertEqual(sorted(m["reserve_fejlede"]), ["BAMLH0A0HYM2", "ICSA", "PERMIT"])


class Test1015NBER(unittest.TestCase):
    """F7/F15/G4.3/F14/F6: annonceringstabellen, USREC og den forklarede audit."""

    def _usrec(self, til, episoder):
        u = {i: 0 for i in range(A2.midx(1975, 1), til + 1)}
        for o, t in episoder:
            for i in range(o, min(t, til) + 1):
                u[i] = 1
        return u

    def test_krydstjek_fanger_manglende_peak_raekke_og_aaben_episode(self):
        rows = A2.laes_annonceringer()
        u0 = A2.load_usrec(REAL_SNAP)
        self.assertEqual(A2.usrec_krydstjek(A2.episodes_from_usrec(u0), rows, u0), [])        # i synk i dag
        u = dict(u0)
        start = max(u0) + 1
        top = start + 4                                                   # syntetisk top efter snapshottets USREC
        for i in range(start, top + 5):
            u[i] = 1 if i >= top else 0                                   # NBER daterer en top; USREC aaben
        eps = A2.episodes_from_usrec(u)
        self.assertEqual(A2.aaben_episode(u), top)
        fejl = A2.usrec_krydstjek(eps, rows, u)
        top_txt = f"{top // 12}-{top % 12 + 1:02d}"
        self.assertTrue(any(top_txt in f and "ingen peak-raekke" in f for f in fejl), fejl)
        with self.assertRaisesRegex(SystemExit, "UDE AF SYNK"):
            A2.load_announcements(eps, usrec=u)
        ekstra = rows + [dict(event="peak_2099", cycle_month="2099-01", announcement_date="2099-07-01", source="t")]
        self.assertTrue(any("2099-01" in f for f in A2.usrec_krydstjek(A2.episodes_from_usrec(u0), ekstra, u0)))

    def test_tabel_hash_er_kanonisk_og_crlf_er_ikke_en_datering(self):
        with tempfile.TemporaryDirectory() as t:
            src = (HERE / "nber_announcements.csv").read_bytes().replace(b"\r\n", b"\n")
            f = Path(t) / "a.csv"; f.write_bytes(src)
            gl_sha = hashlib.sha256(src).hexdigest(); gl_k = A2.tabel_hash(f)
            f.write_bytes(src.replace(b"\n", b"\r\n"))
            self.assertFalse(A2.tabel_aendret(gl_sha, None, f=f))           # CRLF
            self.assertFalse(A2.tabel_aendret(gl_sha, gl_k, f=f))
            self.assertEqual(A2.tabel_hash(f), gl_k)
            kilde_aendret = src.replace(b"nber.org/cycles (Business Cycle Dating Committee announcement)", b"https://www.nber.org/x")
            f.write_bytes(kilde_aendret)
            self.assertFalse(A2.tabel_aendret(gl_sha, None, f=f))           # kun source: ikke en datering (KANONISK_FOR_RAA)
            f.write_bytes(src + b"peak_2027,2027-01,2027-09-15,nber.org\n")
            self.assertTrue(A2.tabel_aendret(gl_sha, None, f=f))
            self.assertTrue(A2.tabel_aendret(gl_sha, gl_k, f=f))

    def test_live_censurering_inde_i_annonceret_recession(self):
        u = self._usrec(A2.midx(2009, 12), [(A2.midx(2008, 1), A2.midx(2009, 6))])
        eps = A2.episodes_from_usrec(u)
        avail = {eps[0][0]: A2.midx(2008, 12)}
        self.assertIsNone(A2.i_annonceret_recession(u, eps, avail, A2.midx(2008, 6)))     # ikke annonceret endnu
        self.assertIsNotNone(A2.i_annonceret_recession(u, eps, avail, A2.midx(2009, 2)))  # annonceret, inde
        self.assertIsNone(A2.i_annonceret_recession(u, eps, avail, A2.midx(2009, 9)))     # efter bunden

    def test_origin_audit_forklarer_kun_modning_censur_og_ny_annoncering(self):
        eps = [(A2.midx(2027, 2), A2.midx(2027, 9))]
        R_gl, R = A2.midx(2026, 9), A2.midx(2027, 9)
        forrige = [[2023, 4, 0], [2024, 1, 0]]
        modnet = [[2023, 4, 0], [2024, 1, 0], [2024, 2, 0], [2024, 3, 0]]     # 2024Q2/Q3 modnes i (R_gl, R]
        a = A2.origin_audit(forrige, modnet, R_gl=R_gl, R=R, eps=eps, avail={eps[0][0]: A2.midx(2028, 1)})
        self.assertTrue(a["forklaret_ok"]); self.assertEqual(a["forklaringer"]["2024Q2"], "modnet")
        # omlabeling uden ny annoncering = uforklaret -> fejl (den gamle identitet kunne aldrig fejle)
        relab = [[2023, 4, 0], [2024, 1, 1], [2024, 2, 0], [2024, 3, 0]]
        b = A2.origin_audit(forrige, relab, R_gl=R_gl, R=R, eps=eps, avail={eps[0][0]: A2.midx(2028, 1)})
        self.assertFalse(b["forklaret_ok"]); self.assertTrue(any("2024Q1" in u for u in b["uforklarede"]))
        # et origin der dukker op uden at vaere modnet = uforklaret
        c = A2.origin_audit(forrige, forrige + [[2026, 1, 0]], R_gl=R_gl, R=R, eps=eps, avail={})
        self.assertFalse(c["forklaret_ok"])


class Test1015NBERKaede(unittest.TestCase):
    """G4.5 (§3.5): NBER-dateringens vej gennem kaeden — fra annoncering til fit, og gennem finalize6."""

    def test_nyt_positivt_origin_naar_fittet_foerst_ved_modenhed(self):
        """Syntetisk: en onset 2030-01 annonceret 2030-07. Ved R lige efter annonceringen er origins med onset i
        vinduet umodne (18-mdr-gulvet) -> n_pos uaendret; ved R >= onset + 18 kommer de ind som positive."""
        qks = [(y, q) for y in range(1990, 2032) for q in (1, 2, 3, 4)]
        rng = np.random.default_rng(3)
        D = dict(qk=qks, qend=np.array([A2.qend_idx(y, q) for y, q in qks]), year=np.array([y for y, _ in qks]),
                 F=rng.normal(size=(len(qks), 1)), feats=["curve"])
        eps = [(A2.midx(2001, 4), A2.midx(2001, 11)), (A2.midx(2008, 1), A2.midx(2009, 6)), (A2.midx(2020, 3), A2.midx(2020, 4)),
               (A2.midx(2030, 1), A2.midx(2030, 6))]
        avail = {o: o + 6 for o, _ in eps}
        usrec = {i: 0 for i in range(A2.midx(1989, 1), A2.midx(2032, 12))}
        for o, t in eps:
            for i in range(o, t + 1):
                usrec[i] = 1
        n_pos = lambda R: F6.fit_model(D, eps, avail, usrec, R)["n_pos"]
        foer = n_pos(A2.midx(2030, 8))                       # lige efter annonceringen
        self.assertEqual(foer, n_pos(A2.midx(2029, 12)))     # annonceringen alene flytter intet (G4.1)
        efter = n_pos(A2.midx(2031, 7) + 12)                 # onset + 18 og vinduernes modning er passeret
        self.assertGreater(efter, foer)

    def test_top_annoncering_genbruger_kalibreringen_og_registrerer_triggeren(self):
        """En ny top-raekke (USREC aaben) paa kalibreringens eget snapshot: indholdet er uaendret (origins med
        onset i vinduet er umodne), manifestet genbruges — og koerslen registreres som nber-datering."""
        W = json.loads((HERE / "weights.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as t:
            here, raw = Path(t) / "v5", Path(t) / "raw"
            here.mkdir()
            for fn in ("weights.json", "ablation3_resultat.json", "ablation7_resultat.json", "ablation8_resultat.json"):
                if (HERE / fn).exists():
                    shutil.copy(HERE / fn, here / fn)
            shutil.copytree(HERE / "kalibreringer", here / "kalibreringer")
            snap = raw / W["snapshot"]
            shutil.copytree(C.RAW / W["snapshot"], snap)
            f = snap / "USREC.csv"
            linjer = f.read_text(encoding="utf-8").splitlines()
            sidste = linjer[-1].split(",")[0]
            linjer[-1] = sidste + ",1"                                      # USREC aaben fra seneste maaned
            f.write_text(chr(10).join(linjer) + chr(10), encoding="utf-8")
            y, m = int(sidste[:4]), int(sidste[5:7])
            top = f"{y if m > 1 else y - 1}-{(m - 2) % 12 + 1:02d}"           # NBER-top = maaneden foer onset
            tabel = (HERE / "nber_announcements.csv").read_text(encoding="utf-8").rstrip(chr(10))
            (here / "nber_announcements.csv").write_text(tabel + chr(10) + f"peak_test,{top},{W['snapshot']},test" + chr(10),
                                                          encoding="utf-8")
            out = io.StringIO()
            with mock.patch.object(F6, "HERE", here), mock.patch.object(A2, "HERE", here), contextlib.redirect_stdout(out), \
                 mock.patch.object(sys, "argv", ["finalize6.py", "--snapshot", str(snap)]):
                F6.main()
            Wn = json.loads((here / "weights.json").read_text(encoding="utf-8"))
        self.assertIn("kalibrering UAENDRET", out.getvalue())
        self.assertEqual(Wn["manifest_hash"], W["manifest_hash"])
        self.assertEqual(Wn["op"]["w"], W["op"]["w"])
        self.assertTrue(Wn["koersel"]["manifest_genbrugt"])
        self.assertIn("nber-datering", Wn["koersel"]["trigger"])
        self.assertNotEqual(Wn["announcement_table_kanonisk"], W.get("announcement_table_kanonisk"))


class Test1015Finalize6(unittest.TestCase):
    """F4/F5/F8/G1.7/G4.2/G4.4/F49/F51/F54 i finalize6."""
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.here = Path(self.tmp.name)
        for fn in ("ablation3_resultat.json", "ablation7_resultat.json", "ablation8_resultat.json"):
            if (HERE / fn).exists():
                shutil.copy(HERE / fn, self.here / fn)
        shutil.copy(HERE / "nber_announcements.csv", self.here / "nber_announcements.csv")
    def tearDown(self): self.tmp.cleanup()

    def _main(self, *extra):
        with mock.patch.object(F6, "HERE", self.here), mock.patch.object(sys, "argv", ["finalize6.py", *extra]), quiet():
            F6.main()
        return json.loads((self.here / "weights.json").read_text(encoding="utf-8"))

    def test_uden_trigger_kraeves_reparation_og_genbrug_bevarer_refit_maaned(self):
        W1 = self._main()                                          # foerste kalibrering (ingen forrige)
        self.assertIn("mde_gate_pp", W1["gate"]); self.assertIn("koersel", W1)
        m1 = json.loads((self.here / "kalibreringer" / f"manifest_{W1['manifest_hash']}.json").read_text(encoding="utf-8"))
        self.assertIn("miljoe", m1); self.assertIn("band_sha256", m1["bootstrap"]); self.assertTrue(m1["L_R_audit"]["ok"])
        andre_ikke_sep = [d for d in sorted(C.RAW.iterdir()) if d.is_dir() and C.snapshot_complete(d)
                          and d != REAL_SNAP and int(d.name[5:7]) != 9]
        if andre_ikke_sep:                                          # et ANDET snapshot uden trigger kraever --reparation
            with self.assertRaisesRegex(SystemExit, "ingen deterministisk trigger"):
                self._main("--snapshot", str(andre_ikke_sep[-1]))
        self._main()                                                # ren reproduktion paa eget snapshot er tilladt
        mf1 = self.here / "kalibreringer" / f"manifest_{W1['manifest_hash']}.json"
        gl = "2025-09" if m1["refit_maaned"] != "2025-09" else "2024-09"   # G4.2: forrige refit i en ANDEN maaned
        m1["refit_maaned"] = gl
        mf1.write_text(json.dumps(m1, indent=1, ensure_ascii=False), encoding="utf-8")
        W2 = self._main("--reparation", "test: genkoersel uden dataaendring")
        self.assertEqual(W2["manifest_hash"], W1["manifest_hash"])          # samme kalibrering genbrugt
        self.assertEqual(W2["refit_maaned"], gl)                            # G4.2: manifestets, ikke koerslens
        self.assertIsNone(W2["koersel"])                                    # reproduktion paa eget snapshot er ingen koersel
        self.assertEqual(W2["audit"], m1["audit"])                          # F49
        self.assertEqual(len(list((self.here / "kalibreringer").glob("manifest_*.json"))), 1)
        # G4.2: en genbrugende koersel paa et ANDET snapshot registreres i weights.json.koersel (ikke som ny kalibrering)
        andre = [d for d in sorted(C.RAW.iterdir()) if d.is_dir() and C.snapshot_complete(d) and d != REAL_SNAP]
        if andre:
            W3 = self._main("--snapshot", str(andre[-1]), "--reparation", "test: andet snapshot")
            if W3["manifest_hash"] == W1["manifest_hash"]:
                self.assertTrue(W3["koersel"]["manifest_genbrugt"])
                self.assertEqual(W3["refit_maaned"], gl)
                self.assertEqual(W3["created_utc"], m1["created_utc"])     # kalibreringens dato, ikke koerslens

    def test_rygrad_ikke_klar_advarer_men_blokerer_ikke(self):
        """F5 + PR #1: en vagt der STOPPEDE finalize6 ved et multpl-udfald ville blokere hovedbogen i hver
        refit-maaned; curve-only er uafhaengig af rygraden, saa det er en advarsel."""
        with tempfile.TemporaryDirectory() as t:
            snap = Path(t) / REAL_SNAP.name
            shutil.copytree(REAL_SNAP, snap)
            m = json.loads((snap / "meta.json").read_text(encoding="utf-8"))
            m.setdefault("spine", {})["refit_klar"] = False; m["spine"]["refit_blokeret"] = ["multpl fejlede"]
            (snap / "meta.json").write_text(json.dumps(m), encoding="utf-8")
            out = io.StringIO()
            with mock.patch.object(F6, "HERE", self.here), contextlib.redirect_stdout(out), \
                 mock.patch.object(sys, "argv", ["finalize6.py", "--snapshot", str(snap)]):
                F6.main()
            self.assertIn("ADVARSEL (F5)", out.getvalue())
            self.assertTrue((self.here / "weights.json").exists())

    def test_fuldmodel_status_foelger_gaten(self):
        self.assertIn("RAADSBESLUTNING", F6.fuldmodel_status(dict(raadsbeslutning_paakraevet=True, fuldmodel_slaar=True)))
        self.assertIn("under MDE", F6.fuldmodel_status(dict(raadsbeslutning_paakraevet=False, fuldmodel_slaar=True)))
        self.assertIn("ikke bestaaet", F6.fuldmodel_status(dict(raadsbeslutning_paakraevet=False, fuldmodel_slaar=False)))

    def test_forrige_manifest_fejler_hoejlydt_naar_filen_mangler(self):
        (self.here / "weights.json").write_text(json.dumps(dict(manifest_hash="deadbeef")), encoding="utf-8")
        with mock.patch.object(F6, "HERE", self.here), self.assertRaisesRegex(SystemExit, "deadbeef"):
            F6.forrige_manifest()

    def test_korrektionsbro_trin_ii_rapporteres(self):
        """F51 (V501 §1.5b): broen ved fast input skal have alle tre trin, og trin (ii) er synligt forskelligt."""
        m, ekstra = F6.rekalibrer(REAL_SNAP)
        b = F6.bro(REAL_SNAP, ekstra, F6.live_x(REAL_SNAP))
        self.assertEqual(set(b["trin"]), {"i_legacy_rygrad", "ii_korrigerede_kilder_samme_origins", "iii_udvidet_panel"})
        self.assertEqual(b["trin"]["ii_korrigerede_kilder_samme_origins"]["n_obs"], F6.LEGACY_NOBS)


class Test1015Motor(unittest.TestCase):
    """F4/F13/F18/F14/G3.6/F48/F51 i motor (laaner TestMotors temp-opsaetning uden at genkoere dens tests)."""
    setUpClass = classmethod(TestMotor.setUpClass.__func__)
    tearDownClass = classmethod(TestMotor.tearDownClass.__func__)
    _motor = TestMotor._motor

    def _log(self, here):
        logf = here.parent / "LOG.md"
        logf.write_text("| logget | snapshot | P | baand | basisrate | dom | kurve | antaending | note | kalibrering |"
                        + chr(10) + "|---|" + chr(10), encoding="utf-8")
        return logf

    def test_september_formlen(self):
        d = lambda y, m: date(y, m, 15)
        self.assertFalse(M.september_forfalden("2026-09", d(2027, 8)))
        self.assertTrue(M.september_forfalden("2026-09", d(2027, 9)))
        self.assertTrue(M.september_forfalden("2026-08", d(2026, 9)))      # foer: skubbet et aar (F4)
        self.assertFalse(M.september_forfalden("2026-10", d(2027, 8)))
        self.assertTrue(M.september_forfalden("2026-10", d(2027, 9)))
        for rm in range(1, 13):
            sep = 2026 if rm < 9 else 2027
            self.assertTrue(M.september_forfalden(f"2026-{rm:02d}", d(sep, 9)))
            self.assertFalse(M.september_forfalden(f"2026-{rm:02d}", date(sep, 8, 31)))

    def test_ann_rate_bruger_kalendernoegler(self):
        s2 = {(2025, 10): 100.0, (2026, 10): 103.0}
        self.assertAlmostEqual(M.ann_rate(s2, 12), 3.0)
        self.assertTrue(np.isnan(M.ann_rate({(2025, 9): 100.0, (2026, 10): 103.0}, 12)))   # 13 mdr -> NaN
        self.assertTrue(np.isnan(M.yoy({(2025, 9): 100.0, (2026, 10): 103.0})))

    def test_fuldmodel_unavailable_crasher_ikke(self):
        """F13: weights.json med fuldmodel 'unavailable — CAPE stale' (V501 §2) koerer med --log og --json."""
        with tempfile.TemporaryDirectory() as t:
            here = Path(t) / "v5"; shutil.copytree(self.here, here)
            W = json.loads((here / "weights.json").read_text(encoding="utf-8"))
            W["fuldmodel"] = dict(features=C.F5, status="unavailable — CAPE stale", note="test")
            (here / "weights.json").write_text(json.dumps(W), encoding="utf-8")
            self._log(here)
            out = self._motor(["--log", "--json", str(Path(t) / "d.json")], here=here)
            d = json.loads((Path(t) / "d.json").read_text(encoding="utf-8"))
        self.assertIn("LOGGET som raekke 1", out); self.assertIn("unavailable", out)
        self.assertIsNone(next(b for b in d["benchmarks"] if b["navn"].startswith("fuldmodel"))["live_p"])

    def test_manglende_monitor_serier_vaelter_ikke_laesningen(self):
        """F18/F1: ICSA, PERMIT og den licensbegraensede HY OAS-fil kan mangle (klon uden lokale filer)."""
        with tempfile.TemporaryDirectory() as t:
            raw = Path(t) / "raw"; shutil.copytree(self.raw / self.today, raw / self.today)
            for sid in ("ICSA", "PERMIT", "BAMLH0A0HYM2", "SP500", "SAHMREALTIME"):
                (raw / self.today / f"{sid}.csv").unlink(missing_ok=True)
            here = Path(t) / "v5"; shutil.copytree(self.here, here)
            self._log(here)
            out = self._motor(["--log"], raw=raw, here=here)
            logtxt = (here.parent / "LOG.md").read_text(encoding="utf-8")
        self.assertIn("LOGGET som raekke 1", out)
        self.assertIn("[?] Sahm", out)
        self.assertIn("meta.json", out)                               # HY OAS fra meta.json's last_value
        self.assertIn("monitor utilgaengelig: ICSA, PERMIT, SAHMREALTIME", logtxt)

    def test_scenarie_appendiks_er_uden_for_antaendings_kolonnen(self):
        out = self._motor([])
        ant, scen = out.split("SCENARIE-APPENDIKS")[0], out.split("SCENARIE-APPENDIKS")[1]
        self.assertNotIn("CP-spaend", ant.split("4) MONITORS")[1])
        for n in ("CP-spaend", "10Y > 5,25%", "Realkredit"):
            self.assertIn(n, scen.split("5) MARKET")[0])
        if (self.raw / self.today / "THREEFYTP10.csv").exists():
            self.assertIn("KW TP", out); self.assertNotIn("ACM TP", out)        # F22: Kim-Wright, ikke ACM

    def test_logvindue_og_ikke_logget_raekker(self):
        with tempfile.TemporaryDirectory() as t:
            here = Path(t) / "v5"; shutil.copytree(self.here, here)
            logf = self._log(here)
            d0 = date.fromisoformat(self.today)
            udenfor = date(d0.year, d0.month, 3)
            out = self._motor(["--log"], here=here, vindue=(10, 20), dag=udenfor)
            self.assertIn("uden for logvinduet", out); self.assertNotIn("LOGGET", out)
            out = self._motor(["--log", "--log-uden-for-vindue", "test af undtagelsen"], here=here, vindue=(10, 20), dag=udenfor)
            self.assertIn("LOGGET som raekke 1", out)
            self.assertIn("uden for logvindue: test af undtagelsen", logf.read_text(encoding="utf-8"))
            # tre maaneder senere: de to mellemliggende maaneder skrives som 'ikke logget'
            senere = date(d0.year + (d0.month + 3 > 12), (d0.month + 2) % 12 + 1, 12)
            raw2 = Path(t) / "raw2"; shutil.copytree(self.raw / self.today, raw2 / senere.isoformat())
            with mock.patch.object(M, "september_forfalden", lambda ref, d: False):   # §3.2a testes for sig
                out = self._motor(["--log"], raw=raw2, here=here, dag=senere)
            tekst = logf.read_text(encoding="utf-8")
            self.assertEqual(tekst.count("(ikke logget)"), 2, out)
            self.assertTrue((here.parent / "hovedbog.jsonl").exists())
            recs = [json.loads(l) for l in (here.parent / "hovedbog.jsonl").read_text(encoding="utf-8").splitlines()]
            self.assertEqual(len(recs), 2); self.assertEqual(len(recs[1]["ikke_logget_foer"]), 2)
            self.assertIn("vindue", recs[0]); self.assertIn("p_maanedlig", recs[0])

    def test_diagnostik_ude_af_synk_blokerer_log(self):
        with tempfile.TemporaryDirectory() as t:
            here = Path(t) / "v5"; shutil.copytree(self.here, here)
            dg = json.loads((here / "diagnostik.json").read_text(encoding="utf-8"))
            dg["manifest_hash"] = "andet"
            (here / "diagnostik.json").write_text(json.dumps(dg), encoding="utf-8")
            self._log(here)
            out = self._motor(["--log"], here=here)
        self.assertIn("--log AFVIST: diagnostik.json passer ikke", out)

    def test_logdag_er_foerste_hverdag_fra_den_10_plus_tre_dage(self):
        """G3.6: oktober 2026 (10. er en loerdag) -> mandag 12.-15.; november -> tirsdag 10.-13."""
        self.assertEqual(M.logvindue(date(2026, 10, 1)), (date(2026, 10, 12), date(2026, 10, 15)))
        self.assertEqual(M.logvindue(date(2026, 11, 28)), (date(2026, 11, 10), date(2026, 11, 13)))
        with tempfile.TemporaryDirectory() as t:
            here = Path(t) / "v5"; shutil.copytree(self.here, here)
            self._log(here)
            d0 = date.fromisoformat(self.today)
            ude = M.logvindue(d0)[1] + timedelta(days=1)
            if ude.month == d0.month:
                out = self._motor(["--log"], here=here, vindue=None, dag=ude)
                self.assertIn("uden for logvinduet", out); self.assertNotIn("LOGGET", out)

    def test_ren_note_og_vindue(self):
        self.assertEqual(M.ren_note("a | b"), "a / b")
        self.assertEqual(M.maanedsvindue(date(2026, 11, 12)), "2026-11..2027-10")
        self.assertEqual(M.siden_sidst([("2026-10-01", 5.0), ("2026-10-02", 5.4), ("2026-10-03", 5.3)], "2026-10-01", 5.25),
                         dict(ekstrem=5.4, dato="2026-10-02", dage_over=2, n=2))

    def test_dd_er_kalibreringsstatistik_paa_rygraden(self):
        """F33: dd = maanedsmiddel / max af 12 maanedsmidler - 1 paa rygradens seneste lukkede maaned (reproducerbar)."""
        r = M.dd_rygrad(REAL_SNAP)
        sp = [(k, v) for k, v, *_ in C.read_shiller(REAL_SNAP) if v is not None and np.isfinite(v)]
        self.assertAlmostEqual(r["dd"], sp[-1][1] / max(v for _, v in sp[-12:]) - 1)
        self.assertEqual(r["maaned"], f"{sp[-1][0][0]}-{sp[-1][0][1]:02d}")

    def test_fuld_maaned_springer_delvis_maaned_over(self):
        rows = [(f"2026-09-{d:02d}", 1.0) for d in range(1, 29)] + [("2026-10-01", 2.0)]
        self.assertEqual(M.fuld_maaned(rows, 15), "2026-09")
        self.assertEqual(M.fuld_maaned(rows + [(f"2026-10-{d:02d}", 2.0) for d in range(2, 20)], 15), "2026-10")

    def test_ikke_logget_raekker_har_ingen_kalibrering(self):
        with tempfile.TemporaryDirectory() as t:
            here = Path(t) / "v5"; shutil.copytree(self.here, here)
            logf = self._log(here)
            d0 = date.fromisoformat(self.today)
            self._motor(["--log"], here=here, dag=date(d0.year, d0.month, 12))
            senere = date(d0.year + (d0.month + 2 > 12), (d0.month + 1) % 12 + 1, 12)
            raw2 = Path(t) / "raw2"; shutil.copytree(self.raw / self.today, raw2 / senere.isoformat())
            with mock.patch.object(M, "september_forfalden", lambda ref, d: False):
                self._motor(["--log"], raw=raw2, here=here, dag=senere)
            gap = [r for r in M.laes_hovedbog(logf) if "ikke logget" in r["logget"]]
            self.assertEqual(len(gap), 1); self.assertEqual(gap[0]["kalibrering"], "")


class TestMergeVerifikation(unittest.TestCase):
    """Fund fra verifikationen af fletningen PR #1 + kode-review (2026-10-15)."""
    setUpClass = classmethod(TestMotor.setUpClass.__func__)
    tearDownClass = classmethod(TestMotor.tearDownClass.__func__)
    _motor = TestMotor._motor

    def _log(self, here):
        logf = here.parent / "LOG.md"
        logf.write_text("| logget | snapshot | P | baand | basisrate | dom | kurve | antaending | note | kalibrering |"
                        + chr(10) + "|---|" + chr(10), encoding="utf-8")
        return logf

    def test_log_json_er_replay_stabil(self):
        """Ritualet 'motor.py --log --json' maa give samme dashboard.json som CI's replay (uden --log) bagefter."""
        with tempfile.TemporaryDirectory() as t:
            here = Path(t) / "v5"; shutil.copytree(self.here, here)
            logf = self._log(here)
            logf.write_text(logf.read_text(encoding="utf-8") + "| 2026-01-12 | 2026-01-12 | 20.0% | 14.0-29.0% | 18.0% | "
                            "ikke skelnelig | +0.50 | ingen |  | 72c3371d |" + chr(10), encoding="utf-8")
            a, b = Path(t) / "a.json", Path(t) / "b.json"
            self._motor(["--log", "--json", str(a)], here=here)
            self._motor(["--snapshot", str(self.raw / self.today), "--allow-stale", "--json", str(b)], here=here)
            self.assertEqual(a.read_bytes(), b.read_bytes())

    def test_samme_snapshot_kan_ikke_logges_igen_naeste_maaned(self):
        with tempfile.TemporaryDirectory() as t:
            here = Path(t) / "v5"; shutil.copytree(self.here, here)
            self._log(here)
            d0 = date.fromisoformat(self.today)
            self.assertIn("LOGGET", self._motor(["--log"], here=here, dag=d0))
            naeste = date(d0.year + (d0.month == 12), d0.month % 12 + 1, min(d0.day, 28))
            with mock.patch.object(M, "september_forfalden", lambda ref, d: False):
                out = self._motor(["--log"], here=here, dag=naeste)
            self.assertIn("allerede grundlag for", out); self.assertNotIn("LOGGET", out)

    def test_log_uden_afsluttende_linjeskift_afvises(self):
        with tempfile.TemporaryDirectory() as t:
            here = Path(t) / "v5"; shutil.copytree(self.here, here)
            logf = self._log(here)
            logf.write_text(logf.read_text(encoding="utf-8").rstrip(chr(10)), encoding="utf-8")
            out = self._motor(["--log"], here=here)
        self.assertIn("ender ikke med et linjeskift", out); self.assertNotIn("LOGGET", out)

    def test_dd_fra_foraeldet_rygrad_goer_fuldmodellen_unavailable(self):
        with tempfile.TemporaryDirectory() as t:
            raw = Path(t) / "raw"; shutil.copytree(self.raw / self.today, raw / self.today)
            f = raw / self.today / "spine.csv"
            ln = f.read_text(encoding="utf-8").splitlines()
            f.write_text(chr(10).join([ln[0]] + [r for r in ln[1:] if r[:7] <= "2023-07"]) + chr(10), encoding="utf-8")
            ud = Path(t) / "d.json"
            self._motor(["--json", str(ud)], raw=raw)
            d = json.loads(ud.read_text(encoding="utf-8"))
        fmb = next(b for b in d["benchmarks"] if b["navn"].startswith("fuldmodel"))
        self.assertIsNone(fmb["live_p"]); self.assertIn("dd stale", fmb["status"])

    def test_ren_note_og_splitlines(self):
        self.assertEqual(M.ren_note("a|b" + chr(0x2028) + "c" + chr(11) + "d"), "a/b c d")

    def test_diff_mark_fanger_indsat_observation(self):
        with tempfile.TemporaryDirectory() as t:
            prev = Path(t)
            gl = [("2020-01-01", "1.5"), ("2020-03-01", "1.7")]               # 2020-02 manglede (hul)
            (prev / "CPIAUCNS.csv").write_bytes(fred_bytes(gl))
            b = fred_bytes(ROWS)                                             # hullet udfyldt, samme sidste obs
            m = F.diff_mark(dict(sha256="x", last="2020-03-01", last_value="1.7"), prev, "CPIAUCNS", F.parse_rows(b),
                            dict(sha256=sha(b), last="2020-03-01", last_value="1.7"))
        self.assertIn("REVIDERET", m)

    def test_bestem_trigger_bruger_seneste_koersels_tabel(self):
        """Efter en genbrugende NBER-koersel (weights.json har den nye tabel) er naeste september 'september (aarlig)'."""
        gl = dict(version="5.0.1", announcement_table_sha256="gammel", announcement_table_kanonisk="K0")
        ny = dict(version="5.0.2", refit_maaned="2027-09", announcement_table_sha256="ny", announcement_table_kanonisk="K1")
        self.assertIn("nber", F6.bestem_trigger(ny, gl))
        self.assertEqual(F6.bestem_trigger(ny, gl, ref=dict(announcement_table_sha256="ny", announcement_table_kanonisk="K1")),
                         "september (aarlig)")


class Test1015Calibrate(unittest.TestCase):
    def test_calibrate_main_roerer_ikke_weights_json(self):
        """F45: calibrate.py (ogsaa --check) skriver calibrate_resultat.json, aldrig de frosne driftsvaegte."""
        with tempfile.TemporaryDirectory() as t:
            here = Path(t)
            with mock.patch.object(C, "HERE", here), mock.patch.object(C, "run", lambda snap: dict(periode="x", n_obs=1, n_episoder=1,
                     base_rate=0.1, episoder=[], wf_table={})), mock.patch.object(C, "acceptance", lambda res: ("", True)), \
                 mock.patch.object(sys, "argv", ["calibrate.py"]), quiet():
                C.main()
            self.assertTrue((here / "calibrate_resultat.json").exists())
            self.assertFalse((here / "weights.json").exists())


class TestRaad2027SkillSaetning(unittest.TestCase):
    """RAADETS_2027 §1.2: oracle-fri foerst, tre maerkede tal og styrkeklausulen i samme saetning."""

    def test_raekkefoelge_og_styrkeklausul(self):
        op = dict(wf_improvement=27.05)
        diag = {"oracle_fri": {"alle_live_publicerbare": {"improvement": 20.37, "n": 219}}}
        a9 = {"skill": {"curve_nested": {"improvement": 18.32}}}
        s = M.skill_saetning(op, diag, a9)
        i_of, i_or, i_ne = s.index("oracle-fri, fast"), s.index("orakel-censureret, fast"), s.index("nested lambda")
        self.assertLess(i_of, i_or)
        self.assertLess(i_or, i_ne)
        self.assertIn("+20.4%", s)
        self.assertIn("+27.1%", s)
        self.assertIn("+18.3%", s)
        self.assertIn(M.STYRKEKLAUSUL, s)
        self.assertNotIn("\n", s)

    def test_uden_diagnostik_staar_tallet_stadig_med_styrkeklausul(self):
        s = M.skill_saetning(dict(wf_improvement=27.05), None, None)
        self.assertIn("orakel-censureret, fast lambda=1: +27.1%", s)
        self.assertIn(M.STYRKEKLAUSUL, s)



# ============================================================== RAADETS_2027: de forseglede specs (protokol2027.py)
import protokol2027 as P27


class TestRaad2027Forsegling(unittest.TestCase):
    """RAADETS_2027 §12 trin 3: hver spec i spec2027/ er forseglet (sha256 laast i koden) og pushet foer koden."""

    def test_alle_specs_matcher_deres_forsegling(self):
        for navn, h in P27.SPECS.items():
            self.assertEqual(P27.spec_sha256(navn), h, navn)
            self.assertEqual(P27.kraev_forseglet(navn), h)

    def test_aendret_spec_stopper_hoejlydt(self):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t) / "spec2027"; shutil.copytree(P27.SPEC_DIR, d)
            navn = sorted(P27.SPECS)[0]
            (d / navn).write_bytes((d / navn).read_bytes() + b"tilfoejet efter forseglingen\n")
            with mock.patch.object(P27, "SPEC_DIR", d):
                with self.assertRaisesRegex(SystemExit, "aendret efter forseglingen"):
                    P27.kraev_forseglet(navn)
                (d / navn).unlink()
                with self.assertRaisesRegex(SystemExit, "mangler"):
                    P27.kraev_forseglet(navn)

    def test_crlf_arbejdskopi_giver_samme_forsegling(self):
        navn = sorted(P27.SPECS)[0]
        with tempfile.TemporaryDirectory() as t:
            d = Path(t) / "spec2027"; d.mkdir()
            lf = (P27.SPEC_DIR / navn).read_bytes().replace(b"\r\n", b"\n")
            (d / navn).write_bytes(lf.replace(b"\n", b"\r\n"))
            with mock.patch.object(P27, "SPEC_DIR", d):
                self.assertEqual(P27.spec_sha256(navn), P27.SPECS[navn])

    def test_ikrafttraeden_er_september_2027(self):
        self.assertFalse(P27.i_kraft(A2.midx(2027, 8)))
        self.assertTrue(P27.i_kraft(A2.midx(2027, 9)))
        self.assertFalse(P27.i_kraft_maaned("2026-09"))
        self.assertTrue(P27.i_kraft_maaned("2027-09"))
        self.assertFalse(P27.i_kraft_maaned(None))


class TestRaad2027Gate(unittest.TestCase):
    """RAADETS_2027 §2.3 (spec2027/1_gate.md): ensidet gate mod egen kritisk vaerdi -> kun et dagsordenspunkt."""

    FELTER = {"protokol", "spec_sha256", "identiske_origins", "n_origins", "curve_only_wf", "curve_only_brier",
              "fuldmodel_wf", "fuldmodel_brier", "delta_pp", "sd_block_pp", "kritisk_vaerdi_pp", "dagsordenspunkt",
              "mde80_pp", "mde80_note", "uden_stoerste_blok", "ved_start", "note"}

    @classmethod
    def setUpClass(cls):
        TestMotor.setUpClass.__func__(cls)

    @classmethod
    def tearDownClass(cls):
        TestMotor.tearDownClass.__func__(cls)

    _motor = TestMotor._motor

    def test_reglen_er_ensidet(self):
        over, K, mde80 = P27.regel(0.0, 10.0)
        self.assertAlmostEqual(K, 19.6)
        self.assertAlmostEqual(mde80, 28.01585)
        self.assertFalse(P27.regel(-500.0, 10.0)[0])          # et stort negativt Delta udloeser intet
        self.assertFalse(P27.regel(K, 10.0)[0])               # Delta = K udloeser ikke
        self.assertTrue(P27.regel(K + 1e-9, 10.0)[0])         # Delta lige over K udloeser

    def test_uparrede_lister_stopper_refitten(self):
        a = [(1970, 1, 0.2, 0.0), (1970, 2, 0.3, 1.0)]
        with self.assertRaisesRegex(SystemExit, "uparret"):
            P27.parret(a, [(1970, 1, 0.2, 0.0), (1970, 3, 0.3, 1.0)])
        with self.assertRaisesRegex(SystemExit, "uparret"):
            P27.parret(a, [(1970, 1, 0.2, 0.0), (1970, 2, 0.3, 0.0)])          # samme origin, anden label
        self.assertEqual(P27.parret(a, a), [(1970, 1, 0.2, 0.2, 0.0), (1970, 2, 0.3, 0.3, 1.0)])

    def test_stoerst_bidragende_blok(self):
        eps = [(A2.midx(1970, 1), A2.midx(1970, 12)), (A2.midx(1980, 1), A2.midx(1980, 12)),
               (A2.midx(1990, 1), A2.midx(1990, 12))]
        rng = np.random.default_rng(1)
        par = []
        for y in list(range(1962, 1970)) + list(range(1971, 1980)) + list(range(1981, 1990)):
            for q in (1, 2, 3, 4):
                yy = float(rng.random() < 0.3)
                p_5 = (0.8 if yy else 0.1) if 1971 <= y <= 1979 else 0.3     # F5 bedre KUN i blok 1
                par.append((y, q, p_5, 0.3, yy))
        rk, top = P27.uden_blokke(par, eps)
        self.assertEqual(top["blok"], 1)
        delta = P27._skill_diff([(a, b, c) for (_, _, a, b, c) in par])
        self.assertLess(top["delta_uden_pp"], delta)
        self.assertEqual(top["bidrag_pp"], max(r["bidrag_pp"] for r in rk))
        self.assertEqual(sum(r["n_origins"] for r in rk), len(par))

    def _finalize(self, ikraft):
        with tempfile.TemporaryDirectory() as t:
            here = Path(t)
            for fn in ("ablation7_resultat.json", "ablation8_resultat.json"):     # NB: ablation3_resultat.json kopieres ikke
                shutil.copy(HERE / fn, here / fn)
            with mock.patch.object(F6, "HERE", here), mock.patch.object(P27, "IKRAFT", ikraft), \
                 mock.patch.object(sys, "argv", ["finalize6.py", "--snapshot", str(C.RAW / "2026-09-19")]), quiet():
                F6.main()
            return json.loads((here / "weights.json").read_text(encoding="utf-8"))

    def test_2027_gate_paa_kalibreringens_snapshot(self):
        W = self._finalize(A2.midx(2026, 1))         # ikrafttraeden flyttet frem: 2027-reglen koerer paa 72c3371d's data
        g = W["gate"]
        self.assertEqual(set(g), self.FELTER)
        self.assertEqual(g["protokol"], "RAADETS_2027 §2.3")
        self.assertEqual(g["spec_sha256"], P27.SPECS["1_gate.md"])
        self.assertEqual((g["n_origins"], g["curve_only_wf"], g["fuldmodel_wf"]), (198, 27.05, 23.16))
        self.assertEqual(g["delta_pp"], -3.89)
        self.assertEqual(g["kritisk_vaerdi_pp"], 21.06)         # repoets gamle "MDE" var en kritisk vaerdi (§2.2)
        self.assertAlmostEqual(g["mde80_pp"], 2.801585 * g["sd_block_pp"], delta=0.02)
        self.assertFalse(g["dagsordenspunkt"])
        self.assertEqual(g["ved_start"]["1953Q2"]["delta_pp"], -31.0)    # = analyser/universstart.py
        self.assertIn("delta_pp", g["ved_start"]["1960Q1"])
        top = g["uden_stoerste_blok"]["blok"]
        self.assertEqual(top["bidrag_pp"], max(r["bidrag_pp"] for r in g["uden_stoerste_blok"]["alle"]
                                               if r["bidrag_pp"] is not None))
        tekst = json.dumps(g) + json.dumps(W["fuldmodel"])
        for forbudt in ("4.42", "4,42", "mde_pp", "raadsbeslutning_paakraevet", "RAADSBESLUTNING"):
            self.assertNotIn(forbudt, tekst)
        self.assertIn("kaldes aldrig evidens og skifter intet", g["note"])
        self.assertIn("frossen benchmark", W["fuldmodel"]["status"])
        self.assertEqual(W["operationel"], "curve_only")

    def test_foer_ikrafttraeden_er_gaten_v501s(self):
        W = self._finalize(P27.IKRAFT)
        self.assertNotIn("protokol", W["gate"])
        self.assertIn("raadsbeslutning_paakraevet", W["gate"])
        self.assertEqual(W["op"]["w"], json.loads((HERE / "weights.json").read_text(encoding="utf-8"))["op"]["w"])

    def test_motor_printer_ikke_laant_stoejgulv_under_2027_gate(self):
        """Spec 1 §5: under en 2027-gate printer motor ikke trin 3's 4,42 (stoejgulv-linjen fra diagnostik.gate_mde)."""
        with tempfile.TemporaryDirectory() as t:
            here = Path(t) / "v5"; shutil.copytree(self.here, here)
            W = json.loads((here / "weights.json").read_text(encoding="utf-8"))
            W["gate"] = dict(protokol="RAADETS_2027 §2.3", identiske_origins=True,
                             note="Delta -3.89pp <= kritisk vaerdi 21.06pp")
            W["fuldmodel"]["note"] = W["gate"]["note"]
            (here / "weights.json").write_text(json.dumps(W), encoding="utf-8")
            ud = self._motor(["--allow-stale"], here=here)
        self.assertNotIn("Stoejgulvet", ud)
        self.assertNotIn("4.42", ud)
        self.assertIn("Stoejgulvet", self._motor(["--allow-stale"]))     # kontrol: v5.0.1-gaten printer den stadig



def koer_finalize6_2027(ikraft, snapshot="2026-09-19", ann_bytes=None):
    """finalize6 i en temp-mappe med RAADETS_2027's ikrafttraeden flyttet til `ikraft` (tests af 2027-stien paa
    kalibreringens egne data). -> (weights.json, manifest, stdout)."""
    with tempfile.TemporaryDirectory() as t:
        here = Path(t)
        for fn in ("ablation7_resultat.json", "ablation8_resultat.json"):
            shutil.copy(HERE / fn, here / fn)
        if ann_bytes is not None:
            (here / "nber_announcements.csv").write_bytes(ann_bytes)
        out = io.StringIO()
        with mock.patch.object(F6, "HERE", here), mock.patch.object(P27, "IKRAFT", ikraft), \
             mock.patch.object(sys, "argv", ["finalize6.py", "--snapshot", str(C.RAW / snapshot)]), \
             contextlib.redirect_stdout(out):
            F6.main()
        W = json.loads((here / "weights.json").read_text(encoding="utf-8"))
        m = json.loads((here / "kalibreringer" / f"manifest_{W['manifest_hash']}.json").read_text(encoding="utf-8"))
        return W, m, out.getvalue()


class TestRaad2027LR(unittest.TestCase):
    """RAADETS_2027 §9 (spec2027/2_L_R_audit.md): datostemplede eligibility-tests for 1990-91, 2001 og 1980-81 med
    graensetests R-1/R (Fable) og negative kontroller paa censureringen — skal bestaa, foer auditten koerer."""

    @classmethod
    def setUpClass(cls):
        snap = C.RAW / "2026-09-19"
        cls.usrec = A2.load_usrec(snap)
        cls.eps = A2.episodes_from_usrec(cls.usrec)
        cls.avail = A2.load_announcements(cls.eps, usrec=cls.usrec)
        cls.rows = A2.laes_annonceringer()
        cls.info = P27.episode_info(cls.eps, cls.rows, cls.avail, cls.usrec)
        cls.D = A2.build_dataset(snap, ["curve"])
        _, cls.win, _ = A2.nber_labels(cls.D, cls.eps, cls.usrec)

    def _o(self, y, q, R):
        """(eligible, label, status) for origin yQq ved refit-maaned R; produktionens eligible_fit skal vaere enig."""
        j = self.D["qk"].index((y, q))
        e, yR = P27.eligible_2027(self.D, self.info, self.avail, self.win, R, 18)
        e1, y1 = A2.eligible_fit(self.D, self.eps, self.avail, self.usrec, R)
        self.assertEqual(bool(e[j]), bool(e1[j]), f"{y}Q{q} ved {R}")
        if e[j]:
            self.assertEqual(yR[j], y1[j])
        return bool(e[j]), int(yR[j]), P27.censur_status(int(self.D["qend"][j]), R, self.info)

    def _modning(self, y, q, label):
        """Alder maales fra vinduets slutning: ude ved qend + 18 (Sols fejl) og ved H + L_R - 1, inde ved H + L_R."""
        qe = A2.qend_idx(y, q)
        self.assertFalse(self._o(y, q, qe + 18)[0])
        self.assertFalse(self._o(y, q, qe + 12 + 18 - 1)[0])
        self.assertEqual(self._o(y, q, qe + 12 + 18), (True, label, "fri"))

    def _inde(self, y, q, aP, aT):
        """Negativ kontrol: 'aaben' ved hver R fra topannonceringen til maaneden foer bundannonceringen, derefter
        'censureret'; aldrig eligible."""
        for R in range(aP, aT):
            self.assertEqual(self._o(y, q, R)[::2], (False, "aaben"), f"{y}Q{q} ved {R}")
        for R in (aT, aT + 1, A2.qend_idx(y, q) + 30, A2.midx(2026, 9)):
            self.assertEqual(self._o(y, q, R)[::2], (False, "censureret"), f"{y}Q{q} ved {R}")

    def _efter_bund(self, y, q, aT):
        """Afgoerelse ved bundannonceringen: 'aaben' ved aT - 1, 'fri' ved aT."""
        qe = A2.qend_idx(y, q)
        self.assertEqual(P27.censur_status(qe, aT - 1, self.info), "aaben")
        self.assertEqual(P27.censur_status(qe, aT, self.info), "fri")

    def test_1990_91(self):
        m = A2.midx
        self._modning(1990, 1, 1)                          # positivt origin foer toppen (onset 1990-08)
        for q in ((1990, 4), (1991, 1)):
            self._inde(*q, aP=m(1991, 4), aT=m(1992, 12))  # top 1991-04-25, bund 1992-12-22
        self._efter_bund(1991, 2, m(1992, 12))
        self._modning(1991, 2, 0)                          # modner 1993-12, bunden kendt siden 1992-12

    def test_2001(self):
        m = A2.midx
        self._modning(2000, 2, 1)                          # onset 2001-04 i vinduet
        for q in ((2001, 2), (2001, 3)):
            self._inde(*q, aP=m(2001, 11), aT=m(2003, 7))  # top 2001-11-26, bund 2003-07-17
        self._efter_bund(2001, 4, m(2003, 7))
        self._modning(2001, 4, 0)

    def test_1980_81_dobbeltdyk(self):
        m = A2.midx
        for q in ((1980, 1), (1980, 2)):
            self._inde(*q, aP=m(1980, 6), aT=m(1981, 7))   # top 1980-06-03, bund 1981-07-08
        for q in ((1980, 3), (1981, 2)):                   # efter 1980-bunden: aaben indtil 1981-07, label 1 fra 1981-onsettet
            self._efter_bund(*q, m(1981, 7))
            self._modning(*q, 1)
        self._inde(1981, 3, aP=m(1982, 1), aT=m(1983, 7))  # inde i 1981-82 (top 1982-01-06, bund 1983-07-08)
        self._efter_bund(1982, 4, m(1983, 7))
        self._modning(1982, 4, 0)

    def test_audit_paa_det_committede_snapshot(self):
        a = P27.L_R_audit(self.D, self.eps, self.avail, self.usrec, A2.midx(2026, 9), self.rows)
        self.assertEqual(a["L_R"], 18)
        self.assertEqual((a["top_led"]["max_lag"], a["top_led"]["raekke"]), (12, "peak_2007"))
        self.assertEqual((a["bund_led"]["max_lag"], a["bund_led"]["raekke"]), (21, "trough_1991"))
        self.assertTrue(a["top_led"]["ok"] and a["bund_led"]["ok"])
        self.assertEqual((a["konflikter"]["n"], a["finalitetsbrud"]["n"]), (0, 0))
        self.assertTrue(a["ok"])
        P27.stop_ved_brud(a)                                # ingen undtagelse

    def _rows(self, event, dato):
        return [dict(r, announcement_date=dato) if r["event"] == event else dict(r) for r in self.rows]

    def test_brud_paa_hvert_led_stopper(self):
        top = P27.L_R_audit(self.D, self.eps, self.avail, self.usrec, A2.midx(2026, 9), self._rows("peak_2007", "2009-07-15"))
        self.assertEqual((top["L_R"], top["top_led"]["ok"], top["bund_led"]["ok"]), (19, False, True))
        with self.assertRaisesRegex(SystemExit, "top-leddet er brudt .* stopper refitten alene"):
            P27.stop_ved_brud(top)                          # top-bruddet stopper, selv om bund-leddet er ok
        bund = P27.L_R_audit(self.D, self.eps, self.avail, self.usrec, A2.midx(2026, 9), self._rows("trough_1991", "1993-10-15"))
        self.assertEqual((bund["L_R"], bund["top_led"]["ok"], bund["bund_led"]["ok"]), (19, True, False))
        with self.assertRaisesRegex(SystemExit, "bund-leddet er brudt"):
            P27.stop_ved_brud(bund)
        self.assertEqual(P27.L_R_formel(self._rows("trough_1991", "1993-09-15"))["bund_led"]["ok"], True)   # lag 30: graensen

    def test_finalize6_koerer_auditten_fra_2027_og_stopper_ved_brud(self):
        W, m, ud = koer_finalize6_2027(A2.midx(2026, 1))
        a = m["L_R_audit"]
        self.assertEqual((a["protokol"], a["L_R"], a["ok"]), ("RAADETS_2027 §9", 18, True))
        self.assertEqual(a["spec_sha256"], P27.SPECS["2_L_R_audit.md"])
        self.assertIn("L_R-audit (RAADETS_2027 §9)", ud)
        self.assertNotIn("blueprint §1", ud)
        tabel = (HERE / "nber_announcements.csv").read_bytes().replace(b"peak_2007,2007-12,2008-12-01", b"peak_2007,2007-12,2009-07-01")
        self.assertIn(b"2009-07-01", tabel)
        with self.assertRaisesRegex(SystemExit, "L_R-auditten er brudt"):
            koer_finalize6_2027(A2.midx(2026, 1), ann_bytes=tabel)
        _, m0, ud0 = koer_finalize6_2027(P27.IKRAFT)        # foer ikrafttraeden: v5.0.1's top-only-print
        self.assertIn("blueprint §1", ud0)
        self.assertNotIn("protokol", m0["L_R_audit"])



import replay2027 as RP


class TestRaad2027Indholdstrigger(unittest.TestCase):
    """RAADETS_2027 §6.1 (spec2027/3_indholdstrigger_replay.md §2): een refit pr. ny onset + enhver omlabeling."""

    @classmethod
    def setUpClass(cls):
        cls.snap = C.RAW / "2026-09-19"
        cls.usrec = A2.load_usrec(cls.snap)
        cls.eps = A2.episodes_from_usrec(cls.usrec)
        cls.avail = A2.load_announcements(cls.eps, usrec=cls.usrec)
        cls.D = A2.build_dataset(cls.snap, ["curve"])

    def _manifest(self, R):
        return F6.fit_model(self.D, self.eps, self.avail, self.usrec, R)["_origins"]

    def _it(self, R, origins, R_M):
        return P27.indholdstrigger(self.D, self.eps, self.avail, self.usrec, R, origins, R_M)

    def test_ny_onset_udloeser_een_gang_ved_foerste_modne_positive(self):
        m = A2.midx
        ft = P27.foerste_trigger(self.D, self.eps, self.avail, self.usrec, m(2003, 12), self._manifest(m(2001, 9)), m(2001, 9))
        self.assertEqual(ft["trigger_maaned"], "2002-12")             # 2000Q2 modner 2002-12 (top annonceret 2001-11)
        self.assertEqual(ft["nye_onsets"], {"2001-04": ["2000Q2"]})
        self.assertEqual(ft["omlabelinger"], [])
        self.assertEqual((ft["protokol"], ft["spec_sha256"]), ("RAADETS_2027 §6", P27.SPECS["3_indholdstrigger_replay.md"]))
        efter = self._manifest(m(2002, 12))                           # refitten ved trigger-maaneden
        t2 = self._it(m(2003, 3), efter, m(2002, 12))                 # 2000Q3: naeste positive for SAMME onset
        self.assertIn([2000, 3, 1], self._manifest(m(2003, 3)))
        self.assertFalse(t2["udloest"])                               # venter paa september

    def test_nymodnede_negative_udloeser_aldrig(self):
        m = A2.midx
        man = self._manifest(m(2005, 9))
        for R in range(m(2005, 10), m(2006, 9)):
            self.assertFalse(self._it(R, man, m(2005, 9))["udloest"], R)
        self.assertGreater(len(self._manifest(m(2006, 8))), len(man))      # der ER modnet nye (negative) origins

    def test_omlabeling_udloeser(self):
        m = A2.midx
        man = [list(o) for o in self._manifest(m(2010, 9))]
        k = next(i for i, o in enumerate(man) if o[2] == 1)
        man[k][2] = 0
        t_ = self._it(m(2010, 10), man, m(2010, 9))
        self.assertTrue(t_["udloest"])
        self.assertEqual(t_["omlabelinger"], [f"{man[k][0]}Q{man[k][1]} 0->1"])

    def test_triggeren_aendrer_intet_ved_fittet(self):
        m = A2.midx
        man = self._manifest(m(2001, 9))
        foer = A2.eligible_fit(self.D, self.eps, self.avail, self.usrec, m(2002, 12))
        self._it(m(2002, 12), man, m(2001, 9))
        efter = A2.eligible_fit(self.D, self.eps, self.avail, self.usrec, m(2002, 12))
        self.assertTrue(np.array_equal(foer[0], efter[0]) and np.array_equal(foer[1], efter[1]))


class TestRaad2027IndholdstriggerKaede(unittest.TestCase):
    """finalize6 og motor under en 2027-kalibrering (ikrafttraeden flyttet frem i testen)."""

    @classmethod
    def setUpClass(cls):
        TestMotor.setUpClass.__func__(cls)

    @classmethod
    def tearDownClass(cls):
        TestMotor.tearDownClass.__func__(cls)

    _motor = TestMotor._motor

    def _forrige(self, here, R_M):
        """En 'kalibrering i drift' fittet ved R_M paa 2026-09-19 (version != VERSION), med weights.json der peger paa den."""
        with mock.patch.object(F6, "HERE", here), quiet():
            mf, _ = F6.rekalibrer(C.RAW / "2026-09-19", R=R_M, version="5.0.1-test")
        mf.update(hash="test0001", audit={}, gate={})
        (here / "kalibreringer").mkdir(exist_ok=True)
        (here / "kalibreringer" / "manifest_test0001.json").write_text(json.dumps(mf), encoding="utf-8")
        ann = here / "nber_announcements.csv"
        shutil.copy(HERE / "nber_announcements.csv", ann)
        (here / "weights.json").write_text(json.dumps(dict(protocol_version="5.0-final", manifest_hash="test0001",
                                                           announcement_table_sha256=C.ann_sha256(ann),
                                                           announcement_table_kanonisk=A2.tabel_hash(ann))), encoding="utf-8")

    def _finalize(self, R_M, snapshot):
        with tempfile.TemporaryDirectory() as t:
            here = Path(t)
            for fn in ("ablation7_resultat.json", "ablation8_resultat.json"):
                shutil.copy(HERE / fn, here / fn)
            with mock.patch.object(P27, "IKRAFT", A2.midx(2020, 1)):
                self._forrige(here, R_M)
                out = io.StringIO()
                with mock.patch.object(F6, "HERE", here), contextlib.redirect_stdout(out), \
                     mock.patch.object(sys, "argv", ["finalize6.py", "--snapshot", str(C.RAW / snapshot)]):
                    F6.main()
            W = json.loads((here / "weights.json").read_text(encoding="utf-8"))
            m = json.loads((here / "kalibreringer" / f"manifest_{W['manifest_hash']}.json").read_text(encoding="utf-8"))
            return W, m, out.getvalue()

    def test_finalize6_indholdstrigger_er_en_gyldig_trigger(self):
        W, m, ud = self._finalize(A2.midx(2021, 8), "2026-10-15")     # 2019Q1 (onset 2020-03) modner 2021-09
        it = m["indholdstrigger"]
        self.assertEqual(it["trigger_maaned"], "2021-09")
        self.assertEqual(it["nye_onsets"], {"2020-03": ["2019Q1"]})
        self.assertEqual(it["evalueret_ved"], "2026-10")
        self.assertTrue(m["trigger"].startswith("nber-indhold (RAADETS_2027 §6): trigger-maaned 2021-09"))
        self.assertEqual(W["trigger"], m["trigger"])
        self.assertIn("NBER-indholdstrigger (RAADETS_2027 §6): trigger-maaned 2021-09", ud)
        self.assertEqual(F6.manifest_hash(m), m["hash"])                # feltet er proveniens (uden for hashen)
        self.assertTrue(m["audit"]["forklaret_ok"])

    def test_finalize6_uden_trigger_stopper_som_foer(self):
        with self.assertRaisesRegex(SystemExit, "indholdstriggeren, RAADETS_2027 §6, er ikke udloest"):
            self._finalize(A2.midx(2026, 9), "2026-10-15")

    def _motor_2027(self, origins_filter, manifest=True, ikraft=A2.midx(2020, 1)):
        with tempfile.TemporaryDirectory() as t:
            here = Path(t) / "v5"; shutil.copytree(self.here, here)
            shutil.copy(HERE.parent / "BEDOEMMELSESNOEGLE.md", Path(t) / "BEDOEMMELSESNOEGLE.md")   # §10.4-tjekket
            W = json.loads((here / "weights.json").read_text(encoding="utf-8"))
            W["manifest_hash"] = "test0002"
            (here / "weights.json").write_text(json.dumps(W), encoding="utf-8")
            if manifest:
                mm = json.loads((HERE / "kalibreringer" / "manifest_72c3371d.json").read_text(encoding="utf-8"))
                mm["origins"] = [o for o in mm["origins"] if origins_filter(o)]
                (here / "kalibreringer" / "manifest_test0002.json").write_text(json.dumps(mm), encoding="utf-8")
            with mock.patch.object(P27, "IKRAFT", ikraft):
                return self._motor(["--allow-stale", "--log", "--json", str(Path(t) / "d.json")], here=here), \
                    json.loads((Path(t) / "d.json").read_text(encoding="utf-8"))

    def test_motor_blokerer_log_ved_udloest_trigger(self):
        uden_2020 = lambda o: not (o[2] == 1 and (o[0], o[1]) >= (2019, 1))       # manifestet mangler onset 2020-03
        ud, d = self._motor_2027(uden_2020)
        self.assertIn("REKALIBRERING PAAKRAEVET: NBER-indholdstrigger (RAADETS_2027 §6): ny onset 2020-03", ud)
        self.assertIn("--log AFVIST: rekalibrering paakraevet", ud)
        self.assertTrue(any("NBER-indholdstrigger" in r for r in d["rekalibrering_paakraevet"]))
        ud, d = self._motor_2027(lambda o: True)                                    # manifestet har alt: ingen trigger
        self.assertNotIn("NBER-indholdstrigger", ud)
        ud, _ = self._motor_2027(uden_2020, manifest=False)                         # fail-closed
        self.assertIn("kan ikke evalueres", ud)
        ud, d = self._motor_2027(uden_2020, ikraft=P27.IKRAFT)                      # foer ikrafttraeden: evalueres ikke
        self.assertNotIn("indholdstrigger", ud.lower())


class TestRaad2027Replay(unittest.TestCase):
    """RAADETS_2027 §6.2 (spec 3 §3): den konfigurationsspecifikke replay."""

    def test_september_alene_reproducerer_E5_eksakt(self):
        r = RP.replay(C.RAW / "2026-09-19", A2.midx(2026, 9), regel=("september",))
        self.assertEqual([(v["navn"], v["n"], v["skill_LL"], v["skill_brier"]) for v in r["varianter"]],
                         [("realtid_aaben_episode", 561, 24.41, 22.22), ("realtid_uden_vintage", 644, 28.95, 26.89),
                          ("orakel", 583, 33.28, 32.46)])
        self.assertEqual((r["n_raekker"], r["foerste_logget"], r["n_refits"]), (668, "1968-09", 59))

    def test_regimet_tre_varianter_i_raekkefoelge_og_indholdsrefits(self):
        r = RP.replay(C.RAW / "2026-09-19", A2.midx(2026, 9))
        self.assertEqual([v["navn"] for v in r["varianter"]], ["realtid_aaben_episode", "realtid_uden_vintage", "orakel"])
        self.assertEqual(r["overskrift"], RP.OVERSKRIFT)
        self.assertEqual(r["regel"], ["september", "hash", "indhold"])
        self.assertIn(dict(R="2002-12", grund="indhold: ny onset 2001-04 (2000Q2)"), r["indholdsudloeste_refits"])
        self.assertTrue(any(g.startswith("hash: peak_2001") for x in r["refits"] if x["R"] == "2001-12" for g in x["grunde"]))
        tekst = chr(10).join(RP.linjer(r))
        self.assertLess(tekst.index("realtid (motorens"), tekst.index("realtid uden USREC"))
        self.assertLess(tekst.index("realtid uden USREC"), tekst.index("orakel (endelig"))
        for e5 in ("24.41", "24,41", "28.95", "28,95", "33.28", "33,28"):
            self.assertNotIn(e5, tekst)
        self.assertIn("ikke dette regimes skill", tekst)

    def test_hash_maaneden_er_E5s(self):
        """En annoncering senest paa logdagen rammer samme maaned, ellers naeste (2020-06-08 -> juni; 1991-04-25 -> maj)."""
        r = RP.replay(C.RAW / "2026-09-19", A2.midx(2026, 9), regel=("september", "hash"))
        hash_R = {x["R"] for x in r["refits"] if any(g.startswith("hash") for g in x["grunde"])}
        self.assertTrue({"2020-06", "1991-05", "2008-12", "2010-10", "1981-07"} <= hash_R)
        self.assertNotIn("1991-04", hash_R)

    def test_main_koerer_kun_ved_refitten(self):
        with mock.patch.object(sys, "argv", ["replay2027.py"]), self.assertRaisesRegex(SystemExit, "koeres ved september-refitten 2027"):
            RP.main()



class TestRaad2027MaanedligtFit(unittest.TestCase):
    """RAADETS_2027 §3.3/§4 (spec2027/4_maanedligt_fit_uscorede.md): fastlaast lambda-normalisering, den parrede
    samme-origins-diagnostik med identitetstjek i kode, og P ved 1953Q2/1960Q1."""

    @classmethod
    def setUpClass(cls):
        cls.snap = C.RAW / "2026-09-19"
        cls.R = A2.midx(2026, 9)
        cls.usrec = A2.load_usrec(cls.snap)
        cls.eps = A2.episodes_from_usrec(cls.usrec)
        cls.avail = A2.load_announcements(cls.eps, usrec=cls.usrec)
        cls.Dq = A2.build_dataset(cls.snap, ["curve"])

    def test_lambda_er_samme_straf_pr_observation(self):
        self.assertAlmostEqual(P27.lambda_m(800, 267), 800 / 267)
        self.assertAlmostEqual(P27.lambda_m(267, 267), 1.0)
        with self.assertRaisesRegex(SystemExit, "N_q = 0"):
            P27.lambda_m(10, 0)
        fit = P27.maanedligt_fit(self.snap, self.Dq, self.eps, self.avail, self.usrec, self.R)
        self.assertEqual((fit["N_m"], fit["N_q"]), (800, 267))
        self.assertAlmostEqual(fit["l2"], 800 / 267, places=5)
        # uafhaengig genberegning: samme raekker, l2 = N_m/N_q (ikke 1)
        Dm = P27.maanedligt_univers(self.snap, self.Dq)
        elig, yR = P27.eligible_maanedlig(Dm, self.eps, self.avail, self.R, P27._labels_m(Dm, self.eps, self.usrec))
        X = Dm["F"][elig]; mu, sd = X.mean(0), X.std(0, ddof=1)
        w = C.fit((X - mu) / sd, yR[elig], l2=800 / 267)
        self.assertEqual(fit["w"], [round(float(v), 4) for v in w])
        self.assertNotEqual(fit["w"], [round(float(v), 4) for v in C.fit((X - mu) / sd, yR[elig], l2=1.0)])

    def test_universet_er_frekvensgates(self):
        sys.path.insert(0, str(HERE / "analyser"))
        import frekvensgate as FG
        a, b = P27.maanedligt_univers(self.snap, self.Dq), FG.byg_maanedligt(self.snap, self.Dq, ["curve"])
        self.assertEqual(list(a["midx"]), list(b["midx"]))
        self.assertTrue(np.array_equal(a["F"], b["F"]))

    def test_parret_diagnostik_B_reproducerer_3_2b_og_A_er_parret(self):
        d = P27.maanedlig_parret(self.snap, self.eps, self.avail, self.usrec, self.R)
        B = d["varianter"]["B"]
        self.assertEqual((B["n_parrede_origins"], B["labels_uenige"], B["forskel_pp"], B["sd_pp"], B["ci10"], B["ci90"]),
                         (198, 0, -1.02, 2.58, -4.47, 1.32))           # = frekvensgate_resultat.json, parret_tyndet_vs_kvartal
        self.assertEqual(B["basisrate"], 0.1616)
        A = d["varianter"]["A"]
        self.assertEqual((A["n_parrede_origins"], A["labels_uenige"]), (198, 0))
        self.assertGreater(A["lambda_spaend"][0], 1.0)                 # normaliseringen er aktiv i hvert vindue
        self.assertEqual(list(d["varianter"]), ["A", "B"])
        self.assertIn("fortegns-uinformativt", d["sprog"])

    def test_identiteterne_fejler_hoejlydt(self):
        kv = [(1970, 1, 0.2, 0.0), (1970, 2, 0.3, 1.0)]
        self.assertEqual(P27.identiteter(list(kv), kv), (2, 0.5))
        with self.assertRaisesRegex(SystemExit, "origin-maengderne"):
            P27.identiteter(kv[:1], kv)
        with self.assertRaisesRegex(SystemExit, "uenige labels"):
            P27.identiteter([(1970, 1, 0.2, 0.0), (1970, 2, 0.3, 0.0)], kv)

    def test_finalize6_skriver_uscorede_kun_fra_2027(self):
        W, m, ud = koer_finalize6_2027(A2.midx(2026, 1))
        us = W["uscorede"]
        self.assertEqual(us, m["uscorede"])
        self.assertEqual(us["spec_sha256"], P27.SPECS["4_maanedligt_fit_uscorede.md"])
        self.assertEqual((us["maanedligt_fit"]["N_m"], us["maanedligt_fit"]["N_q"]), (800, 267))
        start = json.loads((HERE / "diagnostik.json").read_text(encoding="utf-8"))["start_sensitivitet"]
        for felt, navn in (("start_1953Q2", "1953Q2"), ("start_1960Q1", "1960Q1")):
            self.assertEqual(us[felt]["w"], start[navn]["w"])            # samme fit som diagnostik.start_sensitivitet
            self.assertEqual(us[felt]["n_obs"], start[navn]["n_obs"])
        self.assertEqual(F6.manifest_hash(m), m["hash"])               # uden for indholds-hashen
        self.assertIn("uscoret (RAADETS_2027 §3.3)", ud)
        W0, m0, _ = koer_finalize6_2027(P27.IKRAFT)                     # foer ikrafttraeden: intet
        self.assertNotIn("uscorede", W0)
        self.assertNotIn("uscorede", m0)


class TestRaad2027UscoredeHovedbog(unittest.TestCase):
    """Spec 4 §3/§5/§6/§7: motor logger de tre uscorede kolonner under en 2027-kalibrering, en censureret raekke faar
    en uscoret record, og UDFALD.csv's supplerende kolonne haandhaeves."""

    @classmethod
    def setUpClass(cls):
        TestMotor.setUpClass.__func__(cls)
        snap = C.RAW / "2026-09-19"
        usrec = A2.load_usrec(snap); eps = A2.episodes_from_usrec(usrec); avail = A2.load_announcements(eps, usrec=usrec)
        cls.us = P27.uscorede(snap, A2.build_dataset(snap, ["curve"]), eps, avail, usrec, A2.midx(2026, 9))

    @classmethod
    def tearDownClass(cls):
        TestMotor.tearDownClass.__func__(cls)

    _motor = TestMotor._motor
    _scenario = TestMotor._scenario

    def _med_uscorede(self, here):
        W = json.loads((here / "weights.json").read_text(encoding="utf-8"))
        W["uscorede"] = self.us
        (here / "weights.json").write_text(json.dumps(W), encoding="utf-8")

    def test_tre_uscorede_kolonner_og_jsonl_felter(self):
        raw, here = self._scenario(y10=4.50, tb3=3.40)
        self._med_uscorede(here)
        ud = here.parent / "d.json"
        out = self._motor(["--log", "--json", str(ud)], raw=raw, here=here)
        forv = P27.p_uscorede(self.us, 4.50 - 3.40)
        self.assertIn("Uscoret (RAADETS_2027 §3.3/§4; aldrig i dommen)", out)
        r = M.laes_hovedbog(here.parent / "LOG.md")[-1]
        self.assertEqual((r["P_maanedligt_fit"], r["P_1953Q2"], r["P_1960Q1"]),
                         tuple(f"{forv[k]*100:.1f}%" for k in ("p_maanedligt_fit", "p_start_1953Q2", "p_start_1960Q1")))
        linje = [ln for ln in (here.parent / "LOG.md").read_text(encoding="utf-8").splitlines() if ln.startswith("| 2")][-1]
        self.assertEqual(linje.count("|"), 17)                                     # 16 celler
        rec = json.loads((here.parent / "hovedbog.jsonl").read_text(encoding="utf-8").splitlines()[-1])
        for k, v in forv.items():
            self.assertAlmostEqual(rec[k], v, places=6)
        self.assertNotIn("uscoret_censur", rec)                                     # ikke censureret
        d = json.loads(ud.read_text(encoding="utf-8"))
        self.assertAlmostEqual(d["uscorede"]["p_maanedligt_fit"], forv["p_maanedligt_fit"], places=6)
        self.assertNotEqual(d["p"], d["uscorede"]["p_maanedligt_fit"])              # P er fortsat kvartalsfittets

    def test_uden_2027_kalibrering_skrives_intet_nyt(self):
        raw, here = self._scenario(y10=4.50, tb3=3.40)
        ud = here.parent / "d.json"
        out = self._motor(["--log", "--json", str(ud)], raw=raw, here=here)
        self.assertNotIn("Uscoret", out)
        linje = [ln for ln in (here.parent / "LOG.md").read_text(encoding="utf-8").splitlines() if ln.startswith("| 2")][-1]
        self.assertEqual(linje.count("|"), 14)                                     # 13 celler som i dag
        rec = json.loads((here.parent / "hovedbog.jsonl").read_text(encoding="utf-8").splitlines()[-1])
        self.assertNotIn("p_maanedligt_fit", rec)
        self.assertNotIn("uscorede", json.loads(ud.read_text(encoding="utf-8")))

    def test_censureret_maaned_faar_uscoret_record(self):
        """§10.4: en laesning inde i en annonceret (aaben) recession logges med dom 'censureret', scores ikke, men P og
        de uscorede felter foeres i hovedbog.jsonl's 'uscoret_censur'."""
        raw, here = self._scenario(y10=4.50, tb3=3.40)
        self._med_uscorede(here)
        snap = raw / self.today
        u = (snap / "USREC.csv").read_text(encoding="utf-8").splitlines()
        hoved, rk = u[0], [ln for ln in u[1:] if ln.strip()]
        rk = rk[:-3] + [ln.split(",")[0] + ",1" for ln in rk[-3:]]               # aaben episode: de tre seneste maaneder
        (snap / "USREC.csv").write_text(chr(10).join([hoved] + rk) + chr(10), encoding="utf-8")
        onset = rk[-3].split(",")[0][:7]
        oy, om = int(onset[:4]), int(onset[5:7])
        top = f"{oy - (om == 1)}-{(om - 2) % 12 + 1:02d}"
        sidst = rk[-1].split(",")[0][:7]
        ann = f"{int(sidst[:4]) + (sidst[5:7] == '12')}-{int(sidst[5:7]) % 12 + 1:02d}-01"
        tab = here / "nber_announcements.csv"
        tab.write_text(tab.read_text(encoding="utf-8").rstrip(chr(10)) + chr(10) + f"peak_test,{top},{ann},test" + chr(10), encoding="utf-8")
        W = json.loads((here / "weights.json").read_text(encoding="utf-8"))
        W["announcement_table_sha256"], W["announcement_table_kanonisk"] = C.ann_sha256(tab), A2.tabel_hash(tab)
        (here / "weights.json").write_text(json.dumps(W), encoding="utf-8")
        out = self._motor(["--log"], raw=raw, here=here)
        self.assertIn("CENSURERET", out)
        r = M.laes_hovedbog(here.parent / "LOG.md")[-1]
        self.assertEqual(r["dom"], "censureret")
        rec = json.loads((here.parent / "hovedbog.jsonl").read_text(encoding="utf-8").splitlines()[-1])
        self.assertTrue(rec["censureret"])
        uc = rec["uscoret_censur"]
        self.assertAlmostEqual(uc["p"], rec["p"])
        self.assertAlmostEqual(uc["p_maanedligt_fit"], rec["p_maanedligt_fit"])
        self.assertEqual(uc["vindue"], rec["vindue"])
        self.assertIn("RAADETS_2027 §10.4", uc["note"])

    def test_udfald_tjek(self):
        log = [dict(logget="2026-10-10", P="15.1%", dom="ikke skelnelig"), dict(logget="2027-11-12", P="40.0%", dom="censureret"),
               dict(logget="2027-12 (ikke logget)", P="–", dom="")]
        ok = [dict(raekke_logget="2026-10-10", Y="0", uscoret_censureret="nej"),
              dict(raekke_logget="2027-11-12", Y="1", uscoret_censureret="ja")]
        self.assertEqual(P27.udfald_tjek(log, ok, P27.UDFALD_KOLONNER), [])
        for fejl_raekke, tekst in ((dict(raekke_logget="2026-11-11", Y="0", uscoret_censureret="nej"), "ingen logget raekke"),
                                   (dict(raekke_logget="2026-10-10", Y="2", uscoret_censureret="nej"), "Y ="),
                                   (dict(raekke_logget="2027-11-12", Y="0", uscoret_censureret="nej"), "forventet 'ja'"),
                                   (dict(raekke_logget="2026-10-10", Y="0", uscoret_censureret="ja"), "forventet 'nej'"),
                                   (dict(raekke_logget="2027-12", Y="0", uscoret_censureret="nej"), "ingen logget raekke")):
            self.assertTrue(any(tekst in x for x in P27.udfald_tjek(log, [fejl_raekke], P27.UDFALD_KOLONNER)), tekst)
        self.assertTrue(P27.udfald_tjek(log, [], ["raekke_logget", "Y", "afgjort_dato", "kilde", "note"]))

    def test_de_committede_filer_er_konsistente(self):
        """CI haandhaever §10.4's supplerende kolonne paa de rigtige filer (UDFALD.csv mod LOG.md)."""
        import csv as _csv
        with (HERE.parent / "UDFALD.csv").open(encoding="utf-8", newline="") as fh:
            rd = _csv.DictReader(fh)
            rk = list(rd)
            kol = rd.fieldnames
        self.assertEqual(P27.udfald_tjek(M.laes_hovedbog(HERE.parent / "LOG.md"), rk, kol), [])
        hoved = [ln for ln in (HERE.parent / "LOG.md").read_text(encoding="utf-8").splitlines() if ln.startswith("| logget")][0]
        self.assertTrue(hoved.rstrip().endswith("| P_maanedlig | P_maanedligt_fit | P_1953Q2 | P_1960Q1 |"))



class TestRaad2027LiveCensurering(unittest.TestCase):
    """RAADETS_2027 §10.4 (spec2027/5_live_censurering.md): live-reglen er byte-identisk med noeglens §1 (d), og
    motorens aabne-episode-regel opfoerer sig som teksten siger."""

    NOEGLE = HERE.parent / "BEDOEMMELSESNOEGLE.md"

    @classmethod
    def setUpClass(cls):
        TestMotor.setUpClass.__func__(cls)

    @classmethod
    def tearDownClass(cls):
        TestMotor.tearDownClass.__func__(cls)

    _motor = TestMotor._motor

    def test_regelteksten_er_byte_identisk_med_noeglen(self):
        self.assertEqual(P27.regeltekst().encode("utf-8"), P27.noeglens_regel(self.NOEGLE).encode("utf-8"))
        self.assertTrue(P27.regeltekst().startswith("**(d) Realtidscensurering.**"))
        self.assertTrue(P27.regeltekst().endswith("og de to tolkes i tandem."))
        self.assertTrue(P27.kraev_regel_identisk(self.NOEGLE))

    def test_afvigelse_stopper(self):
        with tempfile.TemporaryDirectory() as t:
            k = Path(t) / "BEDOEMMELSESNOEGLE.md"
            k.write_bytes(self.NOEGLE.read_bytes().replace("scores ikke, fordi".encode("utf-8"), "scores ikke, da".encode("utf-8")))
            with self.assertRaisesRegex(SystemExit, "ikke byte-identisk"):
                P27.kraev_regel_identisk(k)
            k.write_bytes(self.NOEGLE.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))   # CRLF er ingen afvigelse
            self.assertTrue(P27.kraev_regel_identisk(k))

    def test_aaben_episode_reglen(self):
        """'Logget inde i en annonceret recession': top annonceret senest i maaneden, og episoden daekker maaneden —
        til og med bunden, eller uden slut saa laenge USREC's seneste maaned er 1."""
        m = A2.midx
        u = {i: 0 for i in range(m(2000, 1), m(2027, 1))}
        for i in range(m(2026, 7), m(2027, 1)):
            u[i] = 1                                                              # aaben episode fra 2026-07
        for i in range(m(2008, 1), m(2009, 7)):
            u[i] = 1                                                              # afsluttet episode 2008-01..2009-06
        eps = A2.episodes_from_usrec(u)
        avail = {m(2008, 1): m(2008, 12), m(2026, 7): m(2026, 11)}
        self.assertIsNone(A2.i_annonceret_recession(u, eps, avail, m(2026, 10)))      # inde, men ikke annonceret: scores
        self.assertIsNotNone(A2.i_annonceret_recession(u, eps, avail, m(2026, 11)))   # annonceret: censureret
        self.assertIsNotNone(A2.i_annonceret_recession(u, eps, avail, m(2027, 3)))    # aaben: efter seneste USREC-maaned
        self.assertIsNotNone(A2.i_annonceret_recession(u, eps, avail, m(2009, 6)))    # til og med bunden
        self.assertIsNone(A2.i_annonceret_recession(u, eps, avail, m(2009, 7)))       # efter bunden: scores
        self.assertIsNone(A2.i_annonceret_recession(u, eps, avail, m(2008, 11)))      # foer annonceringen: scores

    def test_motor_stopper_under_2027_kalibrering_hvis_reglen_afviger(self):
        with tempfile.TemporaryDirectory() as t:
            here = Path(t) / "v5"; shutil.copytree(self.here, here)
            (Path(t) / "BEDOEMMELSESNOEGLE.md").write_bytes(
                self.NOEGLE.read_bytes().replace("scores ikke, fordi".encode("utf-8"), "scores ikke, da".encode("utf-8")))
            with mock.patch.object(P27, "IKRAFT", A2.midx(2020, 1)), self.assertRaisesRegex(SystemExit, "ikke byte-identisk"):
                self._motor(["--allow-stale"], here=here)
            self._motor(["--allow-stale"], here=here)                 # foer ikrafttraeden: ingen kontrol


if __name__ == "__main__":
    unittest.main()
