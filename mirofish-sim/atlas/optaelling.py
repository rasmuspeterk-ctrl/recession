#!/usr/bin/env python3
"""Reproducerbar optaelling af trigger-atlassets raa interviewsvar (kode-review 2026-10-15, G2.1-G2.6).

Koer fra repo-roden (kun standardbiblioteket):
    python mirofish-sim/atlas/optaelling.py > mirofish-sim/atlas/optaelling_output.txt

Laeser de syv kanal-JSON'er i denne mappe (svaerm_atlas.py's interview-dump) og seed_v2_neutral.md.
Skriver:
  1. antal svar pr. kanal og spoergsmaal (Q1 trigger-kaede, Q2 tidligste varsel, Q3 falsifikator/tidslinje),
     unikke personaer (agent_id) og identiske reddit/twitter-svar;
  2. for hver atlas-tripwire: hvilke kanaler og spoergsmaal der naevner taersklen (svar/personaer),
     med kontekstkrav, saa fx '400bp' kun taeller ved HY/OAS; og hvor mange af svarene der i samme svar
     gentager seedets nutidstal for serien (fx margin 51,5 %);
  3. claims-niveauer pr. kanal og spoergsmaal;
  4. seed-ekko i Q2 (seedets egne tal gentaget i svarene) og seedets v4-linjer.

Begraensning: regex-optaelling finder NAEVNELSER. Om en naevnelse er agentens egen varseltaerskel, et ekko
af seed/prompt eller en falsifikator, er en laesning af svaret (TRIGGER-ATLAS.md, erratum 2026-10-15).
Udsnittene printes, saa laesningen kan efterproeves. Moenstrene er bevidst brede; enkelte falske positiver
skal sorteres fra ved laesning af udsnittene.
"""
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HER = Path(__file__).resolve().parent
KANALER = ["kontrol_fri", "inflation_fed", "kredit_refi", "aktie_repricing",
           "arbejdsmarked", "fiskal_termpraemie", "eksogent_chok"]
QS = ("Q1", "Q2", "Q3")
BP = r"\s*(?:bp|bps|个基点|基点|basis points?)"
CP_ORD = r"commercial paper|商业票据|\bCP\b"


def laes_svar():
    """-> (liste af dict(kanal, q, noegle, agent_id, platform, tekst), {kanal: [fejl]})."""
    rows, fejl = [], {}
    for k in KANALER:
        d = json.loads((HER / f"{k}.json").read_text(encoding="utf-8"))
        for q in QS:
            sv = d.get(q, {}).get("svar", {})
            if not isinstance(sv, dict) or "result" not in sv:
                fejl.setdefault(k, []).append(f"{q}: http {sv.get('http', '?')}")
                continue
            for noegle, a in sv["result"].get("results", {}).items():
                rows.append(dict(kanal=k, q=q, noegle=noegle, agent_id=a.get("agent_id"),
                                 platform=a.get("platform"), tekst=a.get("response") or ""))
    return rows, fejl


def treffere(tekst, moenster, kontekst=None, vindue=150):
    """Match af moenster; med kontekst kraeves kontekstordet inden for +-vindue tegn."""
    ud = []
    for m in re.finditer(moenster, tekst, re.I):
        a, b = max(0, m.start() - vindue), min(len(tekst), m.end() + vindue)
        if kontekst and not re.search(kontekst, tekst[a:b], re.I):
            continue
        ud.append(tekst[max(0, m.start() - 60): m.end() + 40].replace("\n", " "))
    return ud


# (navn, moenster, kontekst, vindue, seedvaerdi) - atlassets tabel-taerskler (TRIGGER-ATLAS.md:11-17).
# seedvaerdi: seedets/promptens nutidstal for samme serie; taelles naar det staar i SAMME svar som taersklen.
TRIPWIRES = [
    ("HY OAS 350/400/450bp (HY/OAS-kontekst)", r"(?<![\d.])(?:350|400|450)" + BP,
     r"HY|OAS|高收益|high[- ]yield|垃圾债", 200, r"(?<![\d.])271"),
    ("HY OAS 600bp (v4-flag / seedets 'warning trigger')", r"(?<![\d.])600" + BP, None, 0, None),
    ("CP-spaend 75bp (CP-kontekst)", r"(?<![\d.])75" + BP, CP_ORD, 150, None),
    ("CP-/funding-spaend naevnt (begreb, uden taerskel)", CP_ORD, None, 0, None),
    ("10Y 5,25 %", r"(?<![\d.])5[.,]25\s*%", None, 0, None),
    ("Realkredit 7,8 % (realkredit-kontekst)", r"(?<![\d.])7[.,]8\d?\s*%", r"房贷|抵押贷款|按揭|mortgage", 80, None),
    ("Marginlaan 40/50 % (margin-kontekst)", r"(?<![\d.])(?:40|50)\s*%", r"margin|保证金|融资余额|杠杆融资", 250,
     r"51\.5|(?<![\d.])51\s?%"),
    ("Permits 1,40M (permit-kontekst)", r"1[.,]40?\s*(?:M\b|million|百万)|140\s*万|1,400,000", r"permit|许可", 100,
     r"1\.374|137\.4万|137万"),
    ("Realt kontantafkast under 0 (eksplicit 0-graense)",
     r"(?:跌破|下穿|低于|转负|below|under|falls? below|drops? below|crosses? below)\s*(?:0|零)(?!\.\d*[1-9])",
     r"实际现金|real cash", 80, r"0\.04"),
]

SEED_EKKO = [  # seed_v2_neutral.md's egne tal (og prompternes, svaerm_atlas.py:24-40)
    ("CAPE 42", r"(?<![\d.])42(?:\.0)?\s?(?:倍|x\b|\b)"),
    ("margin +51,5 % / 51 %", r"51\.5|(?<![\d.])51\s?%"),
    ("HY 271bp", r"(?<![\d.])271"),
    ("claims 199k", r"199[,，]?000|19\.9万|199\s?[kK]"),
    ("permits 1,374M", r"1\.374|137\.4万|137万"),
    ("HY 600bp (seedets 'warning trigger')", r"(?<![\d.])600\s?(?:bp|bps|基点|个基点| basis)"),
    ("realt kontantafkast -0,04", r"0\.04"),
    ("flagtaellinger '3 of 3 / 0 of 4 / 1 of 1'", r"3\s?of\s?3|0\s?of\s?4|1\s?of\s?1"),
    ("'debasement'", r"debasement"),
]

CLAIMS_KW = re.compile(r"初请|初次申请|初始失业|失业金|失业救济|失业申请|jobless|initial claims|claims", re.I)
CLAIMS_NUM = re.compile(r"(\d{2,3}(?:\.\d)?)\s?万|(\d{3}),?000|(\d{3})\s?[kK]\b")


def claims_vaerdier(tekst):
    ud = []
    for m in CLAIMS_KW.finditer(tekst):
        for n in CLAIMS_NUM.finditer(tekst[m.start(): m.start() + 90]):
            v = float(n.group(1)) * 10 if n.group(1) else float(n.group(2) or n.group(3))
            if 150 <= v <= 400:
                ud.append(round(v))
    return ud


def main():
    rows, fejl = laes_svar()
    print("TRIGGER-ATLAS: optaelling af raa interviewsvar  (mirofish-sim/atlas/optaelling.py)")
    print("=" * 96)

    # ---- 1. antal svar ----
    print("\n1) SVAR PR. KANAL  [Q1, Q2, Q3]")
    c = Counter((r["kanal"], r["q"]) for r in rows)
    personaer = 0
    for k in KANALER:
        rk = [r for r in rows if r["kanal"] == k]
        ids = {r["agent_id"] for r in rk}
        personaer += len(ids)
        par = defaultdict(list)
        for r in rk:
            par[(r["q"], r["agent_id"])].append(r["tekst"])
        dubletter = sum(1 for v in par.values() if len(v) == 2 and v[0] == v[1])
        plat = Counter(r["platform"] for r in rk)
        print(f"   {k:<20}{str([c.get((k, q), 0) for q in QS]):<16}personaer {len(ids):>2}   "
              f"platforme {dict(plat)}   identiske reddit/twitter-par {dubletter}"
              + (f"   FEJL: {'; '.join(fejl[k])}" if k in fejl else ""))
    tom = sum(1 for r in rows if not r["tekst"].strip())
    print(f"   I ALT {len(rows)} svar ({tom} tomme) fra {personaer} personaer "
          f"= {personaer} x {len(QS)} spoergsmaal x 2 platforme = {personaer * len(QS) * 2}")

    # ---- 2. tripwires ----
    print("\n2) ATLAS-TRIPWIRES: hvor naevnes taersklen?   (kanal: Q svar/personaer)")
    for navn, moenster, ktx, vin, seedv in TRIPWIRES:
        pr = defaultdict(lambda: defaultdict(set))   # kanal -> q -> {(noegle, agent_id)}
        ud_snit, med_seed, n_q2, seed_q2 = [], 0, 0, 0
        for r in rows:
            t = treffere(r["tekst"], moenster, ktx, vin)
            if t:
                pr[r["kanal"]][r["q"]].add((r["noegle"], r["agent_id"]))
                ud_snit.append((r["kanal"], r["q"], r["noegle"], t[0]))
                s_ = bool(seedv and re.search(seedv, r["tekst"]))
                med_seed += s_
                n_q2 += r["q"] == "Q2"
                seed_q2 += s_ and r["q"] == "Q2"
        kan = [k for k in KANALER if k in pr]
        kan_q2 = [k for k in kan if pr[k].get("Q2")]
        print(f"\n   {navn}")
        print(f"     kanaler i alt: {len(kan)}   kanaler med Q2 (tidligste varsel): {len(kan_q2)}"
              + (f"   seedets nutidstal i samme svar: Q2 {seed_q2}/{n_q2}, alle {med_seed}/{len(ud_snit)}"
                 if seedv else ""))
        for k in kan:
            celler = ", ".join(f"{q} {len(pr[k][q])}/{len({a for _, a in pr[k][q]})}" for q in QS if pr[k].get(q))
            print(f"       {k:<20}{celler}")
        for kk, q, nk, s in ud_snit[:16]:
            print(f"       [{kk} {q} {nk}] ...{s}...")
        if len(ud_snit) > 16:
            print(f"       (+{len(ud_snit) - 16} udsnit mere)")

    print("\n   CP-/funding-spaend: bp-vaerdier efter et CP-ord i Q2 (hvilket spaend, hvilken taerskel)")
    for r in rows:
        if r["q"] != "Q2":
            continue
        for m in re.finditer(CP_ORD, r["tekst"], re.I):
            vin_ = r["tekst"][m.start(): m.start() + 220]
            vals = sorted({int(v) for v in re.findall(r"(?<![\d.])(\d{2,3})(?:\s*[-–~至]\s*\d{2,3})?" + BP, vin_)})
            if vals:
                print(f"       [{r['kanal']} Q2 {r['noegle']}] {vals} :: {vin_[:110].replace(chr(10), ' ')}...")
                break

    # ---- 3. claims ----
    print("\n3) CLAIMS-NIVEAUER (tusinder/uge) pr. kanal  [tal inden for 90 tegn efter et claims-ord]")
    for q in QS:
        print(f"   {q}")
        for k in KANALER:
            v = Counter()
            for r in rows:
                if r["kanal"] == k and r["q"] == q:
                    v.update(set(claims_vaerdier(r["tekst"])))
            if v:
                print(f"     {k:<20}{sorted(v.items())}   (vaerdi, antal svar)")

    # ---- 4. seed-ekko ----
    print("\n4) SEED-EKKO I Q2: svar der gentager seedets egne tal")
    q2 = [r for r in rows if r["q"] == "Q2"]
    print(f"   Q2-svar i alt: {len(q2)}")
    for navn, p in SEED_EKKO:
        n = sum(1 for r in q2 if re.search(p, r["tekst"], re.I))
        pk = Counter(r["kanal"] for r in q2 if re.search(p, r["tekst"], re.I))
        print(f"     {navn:<44}{n:>3}   {dict(pk)}")
    seed = (HER / "seed_v2_neutral.md").read_text(encoding="utf-8")
    print("\n   Seed-linjer med v4-ramme, v4-flag, 600bp-trigger og flagtaellinger (seed_v2_neutral.md):")
    for i, ln in enumerate(seed.splitlines(), 1):
        if re.search(r"debasement|600bp|of 3|of 4|low spark", ln):
            print(f"     :{i}  {ln.strip()[:150]}")


if __name__ == "__main__":
    main()
