#!/usr/bin/env python3
"""
tidsrejse.py — koer testsuiten paa en FREMTIDIG kalenderdato (audit 2026-11-13).

Motor, fetch, spine og testsuiten laeser dagens dato: logvinduet, september-fristen (§3.2a), RAADETS_2027's
ikrafttraeden (refit-maaned >= 2027-09) og snapshottets alder. Auditten 2026-11-13 fandt, at 40 af 248 tests (ud over den
bevidste september-alarm) ville fejle fra 2027-09-01 alene paa grund af kalenderen (test-fixturen manglede
bedoemmelsesnoeglen, som motor laeser under en 2027-kalibrering), og at een test ville fejle ved december-ritualet 2026. Dette script flytter date.today() i
test_v5, motor, fetch og spine og koerer hele suiten, saa den slags opdages et aar foer i stedet for i logvinduet.

Koer:  python tidsrejse.py [YYYY-MM-DD ...]
       Uden datoer: den 10. i naeste maaned og den 10. i den foerste september, hvor den aarlige rekalibrering er
       forfalden (hvis den ligger i fremtiden).

Forventet: alt groent — bortset fra TestMotor.test_frosne_vaegte_giver_ingen_reankrings_advarsel paa datoer, hvor
september-rekalibreringen ER forfalden. Det er den bevidste alarm (.github/workflows/tests.yml) og taeller ikke som
fejl her. Enhver anden fejl giver exit 1.

Begraensning: kun kalenderen flyttes. Dataene er de committede snapshots, saa en test, der afhaenger af friske data
paa "dagens" dato, kan fejle her uden at vaere en tidsbombe (ingen goer det i dag). En NY kvartalsmodning mellem to
snapshots (december, marts, juni, september) simuleres ikke; den fejlklasse er fjernet ved, at ingen test laengere
sammenligner to rigtige snapshots.
Ved spring paa over ca. to aar kan tests med syntetiske recessioner i de SENESTE datamaaneder fejle, fordi de
maaneder da er gamle nok til at udloese indholdstriggeren — en egenskab ved de frosne data, ikke en tidsbombe.

Kun stdlib + testsuitens egne afhaengigheder. Skriver intet.
"""
import json, subprocess, sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).parent
ALARM = "test_v5.TestMotor.test_frosne_vaegte_giver_ingen_reankrings_advarsel"


def _koer(dato):
    """Barneprocessen: flyt datoen, koer suiten, print een JSON-linje med de fejlede tests."""
    import unittest
    sys.path.insert(0, str(HERE))
    y, m, d = (int(x) for x in dato.split("-"))

    class FalskDato(date):
        @classmethod
        def today(cls):
            return cls(y, m, d)

    import test_v5, motor, fetch, spine
    for modul in (test_v5, motor, fetch, spine):
        modul.date = FalskDato
    res = unittest.TextTestRunner(verbosity=0, stream=sys.stderr).run(unittest.defaultTestLoader.loadTestsFromModule(test_v5))
    print("TIDSREJSE " + json.dumps(dict(dato=dato, koert=res.testsRun,
                                         fejlede=sorted(t.id() for t, _ in res.failures + res.errors))))


def _forfalden(dato):
    """Er den aarlige september-rekalibrering forfalden pr. dato (motorens egen regel paa de rigtige weights.json)?"""
    sys.path.insert(0, str(HERE))
    import motor
    W = json.loads((HERE / "weights.json").read_text(encoding="utf-8"))
    ref = max(x for x in ((W.get("koersel") or {}).get("maaned"), W.get("refit_maaned")) if x)
    return motor.september_forfalden(ref, date.fromisoformat(dato)), motor.september_forfald(ref)


def standarddatoer(idag=None):
    idag = idag or date.today()
    naeste = date(idag.year + (idag.month == 12), idag.month % 12 + 1, 10)
    _, (sy, sm) = _forfalden(idag.isoformat())
    sep = date(sy, sm, 10)
    return sorted({naeste.isoformat()} | ({sep.isoformat()} if sep > idag else set()))


def main():
    if len(sys.argv) == 3 and sys.argv[1] == "--koer":
        return _koer(sys.argv[2])
    datoer = [a for a in sys.argv[1:] if not a.startswith("-")] or standarddatoer()
    ok = True
    for dato in datoer:
        date.fromisoformat(dato)                                  # fejler hoejlydt paa en ugyldig dato
        r = subprocess.run([sys.executable, str(HERE / "tidsrejse.py"), "--koer", dato], cwd=HERE,
                           capture_output=True, text=True)
        linje = next((ln for ln in r.stdout.splitlines() if ln.startswith("TIDSREJSE ")), None)
        if linje is None:
            print(f"{dato}: testsuiten kunne ikke koeres (exit {r.returncode})\n{r.stderr[-2000:]}")
            ok = False
            continue
        ud = json.loads(linje[len("TIDSREJSE "):])
        forfalden, _ = _forfalden(dato)
        ventet = {ALARM} if forfalden else set()
        uventet = [t for t in ud["fejlede"] if t not in ventet]
        alarm = " (den bevidste september-alarm er roed, som den skal vaere)" if ALARM in ud["fejlede"] and forfalden else ""
        print(f"{dato}: {ud['koert']} tests, {len(uventet)} uventede fejl{alarm}")
        for t in uventet:
            print(f"   FEJL: {t}")
        ok = ok and not uventet
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
