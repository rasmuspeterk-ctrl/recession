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
        html = (REAL_SNAP / "multpl_cape.html").read_bytes()
        def fake(sid, attempts=3):
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

    def test_refit_paa_trunkeret_rygrad_afvises(self):
        """Curve-only-panelets maanedsindeks kommer fra rygraden: med multpl nede (rygrad t.o.m. 2023-07) gav
        rekalibrer ellers v5.0-vaegtene (n_obs 264) uden fejl — i strid med §2."""
        with tempfile.TemporaryDirectory() as t:
            snap = Path(t) / REAL_SNAP.name; shutil.copytree(REAL_SNAP, snap)
            meta = json.loads((snap / "meta.json").read_text(encoding="utf-8"))
            meta["spine"]["sidste"] = "2023-07"
            (snap / "meta.json").write_text(json.dumps(meta), encoding="utf-8")
            with self.assertRaisesRegex(SystemExit, "rygraden i"):
                F6.rekalibrer(snap)

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
        for fn in ("weights.json", "weights_trin1_teknisk.json", "nber_announcements.csv"):
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

    def _motor(self, argv, raw=None, here=None):
        out = io.StringIO()
        with mock.patch.object(C, "RAW", raw or self.raw), mock.patch.object(M, "HERE", here or self.here), \
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
            add("RIFSPPFAAD90NB", [(dage[-1], cp)])
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
        navne = ["Sahm >= 0,50", "HY OAS > 600bp", "S&P drawdown > 20%", "CP-spaend 3m > 75bp", "10Y > 5,25%", "Realkredit 30Y > 7,8%"]
        stress = dict(y10=5.50, tb3=4.00, oas=7.0, mortgage=8.0, cp=6.0, sahm=0.50, dd=-0.25)   # Sahm praecis paa 0,50: >=
        rolig = dict(y10=4.50, tb3=3.00, oas=3.0, mortgage=6.0, cp=3.1, sahm=0.0, dd=-0.01)
        for scen, tilstand in ((stress, "aktiv"), (rolig, "inaktiv")):
            raw, here = self._scenario(**scen)
            ud = here.parent / "d.json"
            self._motor(["--log", "--json", str(ud)], raw=raw, here=here)
            mon = {m["navn"]: m["tilstand"] for m in json.loads(ud.read_text(encoding="utf-8"))["monitors"]}
            celle = M.laes_hovedbog(here.parent / "LOG.md")[-1]["antaending"]
            for n in navne:
                self.assertEqual(mon[n], tilstand, n)
                self.assertEqual(n in celle, tilstand == "aktiv", f"{n} i antaending: {celle!r}")

    def test_reserveserier_maa_mangle_uden_at_motor_falder(self):
        """fetch.RESERVE goer snapshottet 'komplet' uden disse filer; motor skal have sine fald-tilbage-veje (DFF -> FEDFUNDS,
        THREEFYTP10 -> acm.csv, CPIAUCSL valgfri)."""
        for sid in sorted(F.RESERVE):
            raw, _ = self._scenario()
            (raw / self.today / f"{sid}.csv").unlink()
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
        self.assertTrue(all(i["z"] is None for i in d["inputs"]))
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
            for fn, h in hs.items():
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


if __name__ == "__main__":
    unittest.main()
