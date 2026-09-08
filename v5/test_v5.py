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
        for fn in ("shiller.csv", "manual.json", "acm.csv"):
            (self.manual / fn).write_bytes(b"x\n")
        self.today = date.today().isoformat()
    def tearDown(self): self.tmp.cleanup()

    def _run(self, fejler=()):
        def fake(sid, attempts=3):
            if sid in fejler:
                raise RuntimeError("simuleret fejl")
            b = fred_bytes(ROWS); return b, F.parse_rows(b)
        with mock.patch.object(F, "RAW", self.raw), mock.patch.object(F, "MANUAL", self.manual), \
             mock.patch.object(F, "fetch_series", fake), quiet():
            F.main()

    def meta(self, name):
        return json.loads((self.raw / name / "meta.json").read_text(encoding="utf-8"))

    def test_succes_giver_komplet_dagssnapshot(self):
        self._run()
        self.assertTrue(self.meta(self.today)["complete"])
        self.assertEqual(len(list((self.raw / self.today).glob("*.csv"))), len(F.SERIES) + 2)
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

    def test_promoveret_model_bevares(self):
        prev = dict(protocol_version="5.0-final", operationel="curve_cape",
                    op=dict(features=["curve", "cape_pct"], mu={"curve": 1.0, "cape_pct": 0.5},
                            sd={"curve": 1.0, "cape_pct": 0.3}, w=[-2.0, -1.0, -0.4],
                            wf_improvement=36.8, wf_brier=34.3, stempel="data-foreslaaet, promoveret 2026-08"),
                    band=dict(metode="test", seed=42, n_draws=1, W=[[-2.0, -1.0, -0.4]]),
                    benchmarks=dict(curve_cape=dict(status="operationel (data-foreslaaet, promoveret 2026-08)")))
        (self.here / "weights.json").write_text(json.dumps(prev), encoding="utf-8")
        W = self._main()
        self.assertEqual(W["operationel"], "curve_cape")
        self.assertEqual(W["op"]["stempel"], "data-foreslaaet, promoveret 2026-08")
        self.assertEqual(W["band"]["n_draws"], 1)
        self.assertEqual(W["benchmarks"]["curve_cape"]["status"], "operationel (data-foreslaaet, promoveret 2026-08)")


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

    def test_vaegte_uden_fejlalarm_stopper_hoejlydt(self):
        with tempfile.TemporaryDirectory() as t:
            here = Path(t) / "v5"; shutil.copytree(self.here, here)
            W = json.loads((here / "weights.json").read_text(encoding="utf-8"))
            del W["op"]["vaerste_fejlalarm"]
            (here / "weights.json").write_text(json.dumps(W), encoding="utf-8")
            with self.assertRaisesRegex(SystemExit, "vaerste_fejlalarm"):
                self._motor([], here=here)


# ============================================================== debate.py
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
