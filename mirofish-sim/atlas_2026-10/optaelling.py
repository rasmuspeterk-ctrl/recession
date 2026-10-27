#!/usr/bin/env python3
"""Optaelling af oktober-atlassets interviewsvar (mirofish-sim/atlas_2026-10/atlas_raw/*.json).

Koer fra repo-roden (kun standardbiblioteket):
    python mirofish-sim/atlas_2026-10/optaelling.py > mirofish-sim/atlas_2026-10/optaelling_output.txt

Hvad den taeller (samme regel som erratum E1 i TRIGGER-ATLAS.md: en taerskel taeller kun som varsel, naar agenten
selv naevner den i Q2, "tidligste observerbare varsel"):
  1. svar pr. kanal og spoergsmaal, og unikke personaer;
  2. hvilke DATASERIER agenterne naevner i Q2, pr. kanal (antal personaer) og i hvor mange kanaler;
  3. de TAERSKELTAL, de saetter ved de vigtigste serier (fx '400bp' ved HY-spaendet), pr. kanal;
  4. SEED-EKKO: hvor ofte Q2-svarene gentager seedets egne nutidstal (fx 338bp, 198.000) — et tal, der staar i
     seedet, er ikke en uafhaengig taerskel.
Begraensning: regex finder naevnelser, ikke mening. Udsnit printes, saa laesningen kan efterproeves.
"""
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HER = Path(__file__).resolve().parent
RAA = HER / "atlas_raw"
KANALER = ["kontrol_fri", "inflation_fed", "kredit_refi", "aktie_repricing",
           "arbejdsmarked", "fiskal_termpraemie", "eksogent_chok"]
QS = ("Q1", "Q2", "Q3")

# dataserier: navn -> moenster (engelsk og kinesisk, da en del agenter svarer paa kinesisk)
SERIER = {
    "HY-kreditspaend": r"high[- ]yield|\bHY\b|\bOAS\b|junk|高收益|垃圾债",
    "Baa/IG-kreditspaend": r"\bBaa\b|investment[- ]grade|\bIG\b spread|投资级",
    "EBP (excess bond premium)": r"excess bond premium|\bEBP\b|Gilchrist|超额债券溢价",
    "CP/funding-spaend": r"commercial paper|\bCP\b|SOFR|repo rate|funding spread|商业票据|融资利差",
    "Nye ledighedsansoegninger": r"initial (jobless )?claims|jobless claims|\bclaims\b|初请|首次申请失业",
    "Fortsatte ansoegninger": r"continuing claims|持续申请|续请",
    "Sahm/ledighed": r"\bSahm\b|unemployment rate|失业率|萨姆",
    "Loenmodtagere (payrolls)": r"payroll|nonfarm|\bNFP\b|非农",
    "Vikarer/timer": r"temporary[- ]help|temp(orary)? (employment|jobs)|weekly hours|临时工|工作时长",
    "Rentekurve (10y-3m/2y)": r"yield curve|10[- ]?year[- ]minus|10y[- ]?[-/]?[- ]?(3m|2y)|curve inver|收益率曲线|倒挂",
    "10-aarig rente/term-praemie": r"10[- ]?year (treasury|yield)|10Y yield|term premium|期限溢价|10年期",
    "Realkreditrente": r"mortgage rate|30[- ]year (fixed|mortgage)|按揭利率|抵押贷款利率",
    "Restancer (kort/realkredit)": r"delinquen|charge[- ]off|拖欠|违约率|核销",
    "Olie/energi": r"\boil\b|crude|\bWTI\b|Brent|gasoline|diesel|原油|油价|汽油|柴油",
    "Inflation (CPI/PCE)": r"\bCPI\b|\bPCE\b|inflation|通胀|消费者价格",
    "Styrerente/Fed": r"fed funds|federal funds|policy rate|\bFOMC\b|联邦基金|加息",
    "Aktier/VIX": r"\bVIX\b|S&P|equity|drawdown|标普|股市",
    "Marginlaan": r"margin debt|margin call|保证金",
    "Bankudlaan (SLOOS)": r"\bSLOOS\b|lending standards|loan officer|信贷标准",
    "PMI/ISM/LEI": r"\bPMI\b|\bISM\b|leading (economic )?indicator|\bLEI\b|领先经济指标|采购经理",
    "Boligmarked": r"housing starts|building permits|home sales|house price|新屋|房价|建筑许可",
    "Detail/forbrug": r"retail sales|consumer spending|consumption|零售销售|消费支出",
}

# taerskeltal ved de vigtigste serier (et tal inden for +-80 tegn af seriens ord)
TAL = {
    "HY-kreditspaend": (r"(\d{3})\s*(?:bp|bps|basis points?|个基点|基点)", SERIER["HY-kreditspaend"]),
    "CP/funding-spaend": (r"(\d{2,3})\s*(?:bp|bps|basis points?|个基点|基点)", SERIER["CP/funding-spaend"]),
    "Nye ledighedsansoegninger": (r"(\d{3})\s*(?:k\b|,000|000|千|万)", SERIER["Nye ledighedsansoegninger"]),
    "Sahm/ledighed": (r"(\d\.\d{1,2})\s*(?:%|pp|percentage|个百分点)?", SERIER["Sahm/ledighed"]),
    "10-aarig rente/term-praemie": (r"(\d\.\d{1,2})\s*%", SERIER["10-aarig rente/term-praemie"]),
    "Realkreditrente": (r"(\d\.\d{1,2})\s*%", SERIER["Realkreditrente"]),
    "Olie/energi": (r"\$\s?(\d{2,3})", SERIER["Olie/energi"]),
    "Inflation (CPI/PCE)": (r"(\d\.\d)\s*%", SERIER["Inflation (CPI/PCE)"]),
}

# seedets egne nutidstal (seed_v3_neutral.md); et svar der gentager dem, ekkoer seedet
SEED_TAL = {"HY 338bp": r"\b338\s*(?:bp|bps|个基点|基点)|3\.38\s*(?:%|percentage)",
            "claims 198k": r"\b198[,\s]?(?:000|k\b|千)",
            "10Y 5.00/5.31 %": r"\b5\.(?:00|31)\s*%",
            "realkredit 7.32 %": r"\b7\.32\s*%",
            "CPI 3.7 %": r"\b3\.7\s*%",
            "olie $108/115": r"\$\s?(?:108|115)\b",
            "CAPE 40.7": r"\b40\.[67]\d?\b",
            "margin +31 %": r"\b31(?:\.4)?\s*%"}


def laes():
    rows = []
    for k in KANALER:
        d = json.loads((RAA / f"{k}.json").read_text(encoding="utf-8"))
        for q in QS:
            sv = (d.get(q) or {}).get("svar") or {}
            for noegle, a in ((sv.get("result") or {}).get("results") or {}).items():
                rows.append(dict(kanal=k, q=q, agent=a.get("agent_id"), platform=a.get("platform"),
                                 tekst=a.get("response") or ""))
    return rows


def main():
    rows = laes()
    print("=== 1. Svar pr. kanal ===")
    for k in KANALER:
        rk = [r for r in rows if r["kanal"] == k]
        print(f"{k:<20} " + "  ".join(f"{q}: {sum(r['q'] == q for r in rk)}" for q in QS)
              + f"  unikke personaer: {len({r['agent'] for r in rk})}")
    q2 = [r for r in rows if r["q"] == "Q2"]

    print("\n=== 2. Dataserier naevnt i Q2 (tidligste varsel): personaer pr. kanal ===")
    tabel = {}
    for navn, m in SERIER.items():
        pr = {k: len({r["agent"] for r in q2 if r["kanal"] == k and re.search(m, r["tekst"], re.I)}) for k in KANALER}
        tabel[navn] = pr
    hoved = "".join(f"{k[:9]:>10}" for k in KANALER)
    print(f"{'serie':<30}{hoved}{'kanaler':>9}")
    for navn, pr in sorted(tabel.items(), key=lambda t: (-sum(v > 0 for v in t[1].values()), -sum(t[1].values()))):
        print(f"{navn:<30}" + "".join(f"{pr[k]:>10}" for k in KANALER) + f"{sum(v > 0 for v in pr.values()):>9}")

    print("\n=== 3. Taerskeltal i Q2 ved de vigtigste serier (vaerdi: antal personaer, kanaler) ===")
    for navn, (tal_m, ord_m) in TAL.items():
        fund = defaultdict(lambda: defaultdict(set))
        for r in q2:
            t = r["tekst"]
            for m in re.finditer(tal_m, t, re.I):
                a, b = max(0, m.start() - 80), min(len(t), m.end() + 80)
                if re.search(ord_m, t[a:b], re.I):
                    fund[m.group(1)][r["kanal"]].add(r["agent"])
        top = sorted(fund.items(), key=lambda kv: (-len(kv[1]), -sum(len(v) for v in kv[1].values())))[:8]
        print(f"{navn}: " + "; ".join(f"{v} ({sum(len(s) for s in ks.values())} pers., {len(ks)} kan.)" for v, ks in top))

    print("\n=== 4. Seed-ekko i Q2 (svar der gentager seedets nutidstal) ===")
    for navn, m in SEED_TAL.items():
        n = sum(1 for r in q2 if re.search(m, r["tekst"], re.I))
        print(f"{navn:<20} {n:>4} af {len(q2)} Q2-svar")


if __name__ == "__main__":
    main()
