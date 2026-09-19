#!/usr/bin/env python3
"""
test_v5.py — deterministisk testsuite for v5-kaeden (stdlib unittest, ingen netvaerk).

Daekker praecis de mekanismer kode-reviewet 2026-09-09 fandt fejl i: fetch's
snapshot-livscyklus (.ny/.ukomplet, retry, diff-markering), komplethedsgaten,
finalize6's permanente linjer og promotion-bevaring, motor's --log-guards og
debate.py's arkiv-layout. Alle tests koerer i temp-mapper; rigtige snapshots
laeses kun (kopieres), weights.json/LOG.md roeres aldrig.

Koer:  cd v5 && python -m unittest -v test_v5
"""
import contextlib, hashlib, io, json, os, shutil, sys, tempfile, unittest, urllib.error
from datetime import date
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
    def tearDown(self): self.tmp.cleanup()

    def _run(self, fejler=(), stale=None, multpl=None):
        """Falsk FRED, falsk multpl (default: netvaerksfejl -> tom komposit) og friskhed neutraliseret
        (fixturens 2020-raekker er per konstruktion gamle); `stale` overstyrer friskheds-resultatet."""
        def fake(sid, attempts=3):
            if sid in fejler:
                raise RuntimeError("simuleret fejl")
            b = fred_bytes(ROWS); return b, F.parse_rows(b)
        def fake_multpl(attempts=3):
            if multpl is None:
                raise RuntimeError("simuleret multpl-fejl")
            return multpl
        with mock.patch.object(F, "RAW", self.raw), mock.patch.object(F, "MANUAL", self.manual), \
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
        for fn in ("weights.json", "weights_trin1_teknisk.json"):
            shutil.copy(HERE / fn, cls.here / fn)
    @classmethod
    def tearDownClass(cls): cls.tmp.cleanup()

    def _motor(self, argv, raw=None, here=None):
        out = io.StringIO()
        with mock.patch.object(C, "RAW", raw or self.raw), mock.patch.object(M, "HERE", here or self.here), \
             mock.patch.object(sys, "argv", ["motor.py"] + argv), contextlib.redirect_stdout(out):
            M.main()
        return out.getvalue()

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
            with self.assertRaises(SystemExit):
                self._motor([], raw=raw)

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
        self.assertEqual({m["tilstand"] for m in d["monitors"]} - {"aktiv", "inaktiv", "kontekst"}, set())
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
        self.assertEqual(S.cpi_huller(rows), ["2023-09"])

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


class TestDebate(unittest.TestCase):
    def test_read_round_laeser_arkivets_runde_mapper(self):
        r1 = D.read_round(1)
        self.assertEqual(len(r1), len(D.MODELS))
        self.assertIn("PROPOSAL: GPT-5.6 Sol", D.build_prompt("round2", D.MODELS[0]))

    def test_tom_runde_fejler_hoejlydt(self):
        with tempfile.TemporaryDirectory() as t:
            (Path(t) / "runder" / "runde1").mkdir(parents=True)
            with mock.patch.object(D, "HERE", Path(t)), self.assertRaises(SystemExit):
                D.build_prompt("round2", D.MODELS[0])


if __name__ == "__main__":
    unittest.main()
