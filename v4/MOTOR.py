#!/usr/bin/env python3
"""
================================================================================
 MOTOR v4.0 — FINAL                                          8. august 2026
================================================================================
 Kalibreret paa aegte data: Shiller 1871-2026, US Treasury 1934-2026,
 BEA real BNP 1947-2024.  359 kvartaler, 11 recessionsepisoder.
 Walk-forward valideret: +22,9% log-loss forbedring, Brier-skill +19,4%.

 KOER:  python3 MOTOR.py
 Opdater de seks tal i INPUT nedenfor. Alle er gratis, ~5 minutters arbejde.

 LAG 1 er valideret. LAG 2-4 er IKKE. Laes ADVARSEL nederst.
================================================================================
"""
import numpy as np

# ==============================================================================
# INPUT — opdater disse seks tal manuelt hver maaned
# ==============================================================================
INPUT = dict(
    y10       = 4.40,   # 10-aarig statsobligation, %      fred.stlouisfed.org/series/DGS10
    tb3m      = 3.73,   # 3-maaneders T-bill, %            fred.stlouisfed.org/series/TB3MS
    cpi_yoy   = 3.50,   # CPI aar/aar, %                   bls.gov/cpi
    cpi_yoy_1 = 2.70,   # CPI aar/aar for 12 mdr siden, %  (samme kilde, forrige aar)
    spx_vs_hi = 0.00,   # S&P vs 12-mdr hoejde, decimal    0.00 = paa toppen, -0.15 = 15% under
    cape      = 42.0,   # Shiller CAPE                     multpl.com/shiller-pe
    # --- til LAG 2, opdateres sjaeldent ---
    inv_end_months = 20,    # mdr siden kurven sidst var negativ (nov 2024)
    inv_depth      = -1.57, # dybeste inversion i den periode, pp
    # --- til LAG 3, flag ---
    fed_funds  = 3.63,  # effektiv fed funds, %
    pce_head   = 4.10,  # headline PCE aar/aar, %
    hy_oas     = 271,   # high yield OAS, bp               fred.stlouisfed.org/series/BAMLH0A0HYM2
    sahm       = 0.07,  # Sahm-regel                       fred.stlouisfed.org/series/SAHMREALTIME
    margin_yoy = 51.5,  # marginlaan aar/aar, %            finra.org margin statistics
)

# ==============================================================================
# LAG 1 — RECESSION.  VALIDERET.
# ==============================================================================
MU = dict(curve=1.5064, realrate=1.2741, dd=-0.0540, d_infl=0.0971, cape_pct=0.5744)
SD = dict(curve=1.1011, realrate=3.4545, dd=0.0808, d_infl=3.4777, cape_pct=0.2955)
F  = ['curve','realrate','dd','d_infl','cape_pct']
W_12M = [-2.5445, -1.2967, -0.5289, -0.2893, -0.1480, -0.4322]
W_H   = {1:[-3.7944,-0.6485,-0.1515,-0.7374, 0.0756,-0.3271],
         2:[-3.5725,-0.7327,-0.4688,-0.1868,-0.0363,-0.1217],
         3:[-3.5827,-0.7852,-0.6027,-0.0691,-0.1918,-0.0245],
         4:[-3.7389,-1.0725,-0.5589, 0.0589,-0.4578, 0.1123]}
BASE, NOBS, NEP = 0.1337, 359, 11

def cape_percentil(c):
    """Shiller CAPE -> historisk percentil, stykvis fra 1881-2026 fordelingen."""
    kn=[(5,.00),(10,.05),(13,.20),(15,.35),(17,.50),(20,.65),(24,.80),
        (28,.90),(32,.95),(36,.975),(40,.99),(44.2,1.0)]
    for (a,pa),(b,pb) in zip(kn,kn[1:]):
        if c<=b: return pa+(pb-pa)*(c-a)/(b-a)
    return 1.0

def features(I):
    return dict(
        curve    = I['y10']-I['tb3m'],
        realrate = I['y10']-I['cpi_yoy'],
        dd       = I['spx_vs_hi'],
        d_infl   = I['cpi_yoy']-I['cpi_yoy_1'],
        cape_pct = cape_percentil(I['cape']))

def logit(x, w):
    z = w[0] + sum(w[i+1]*((x[f]-MU[f])/SD[f]) for i,f in enumerate(F))
    return 1/(1+np.exp(-np.clip(z,-30,30)))

x = features(INPUT)
p12 = logit(x, W_12M)
ph  = {k: logit(x, W_H[k]) for k in (1,2,3,4)}
p9  = 1-np.prod([1-ph[k] for k in (1,2,3)])

print("="*78)
print(" MOTOR v4.0                                              8. august 2026")
print("="*78)
print("\nLAG 1 — RECESSION   [VALIDERET: walk-forward +22,9%, Brier +19,4%]\n")
NAVN = {'curve':'Rentekurve 10y-3m','realrate':'Realrente 10y-CPI',
        'dd':'S&P vs 12-mdr hoejde','d_infl':'Aendring i inflation',
        'cape_pct':'CAPE-percentil'}
print(f"  {'Input':<24}{'Vaerdi':>9}{'z-score':>10}")
for f in F:
    print(f"  {NAVN[f]:<24}{x[f]:>9.2f}{(x[f]-MU[f])/SD[f]:>10.2f}")
print()
print(f"  {'P(recession, 12 mdr)':<24}{p12*100:>8.1f}%")
print(f"  {'P(recession,  9 mdr)':<24}{p9*100:>8.1f}%")
print(f"  {'Basisrate':<24}{BASE*100:>8.1f}%")
print(f"  {'Forhold til basisrate':<24}{p12/BASE:>8.2f}x")
print()
print("  Kvartal for kvartal:")
for k in (1,2,3,4):
    bar = "#"*max(1,int(ph[k]*120))
    print(f"    +{k} ({k*3:>2} mdr){ph[k]*100:>7.2f}%  {bar}")

# ------------------------------------------------------------------------------
# LAG 2 — INVERSIONS-EFTERVIRKNING.  Separat tjek, IKKE i modellen.
# ------------------------------------------------------------------------------
s, d = INPUT['inv_end_months'], INPUT['inv_depth']
score = -d*np.exp(-s/24) if s<=36 else 0.0
buckets=[(0.0,0.5,11),(0.5,1.0,14),(1.0,2.0,38),(2.0,9.9,56)]
hit=next((r for a,b,r in buckets if a<=score<b), 11)
print()
print("="*78)
print("LAG 2 — INVERSIONS-EFTERVIRKNING   [tjek, ikke model]")
print("="*78)
print(f"  Inversion sluttede for {s} mdr siden, dybde {d:+.2f}pp")
print(f"  Score = {score:.2f}")
print(f"\n  {'Score-interval':<18}{'Historiske kvt':>16}{'Recession inden 4 kvt':>24}")
for a,b,r in buckets:
    mark = "  <-- HER" if a<=score<b else ""
    print(f"  {a:.1f} - {b:.1f}{'':<10}{'':>16}{r:>22}%{mark}")
print(f"\n  Din bucket giver {hit}% mod basisrate {BASE*100:.0f}%.")
print(f"  Test: inv_score som model-feature GAV DAARLIGERE resultat")
print(f"        (+22,9% -> +18,8%). Bruges derfor kun som tjek.")

# ------------------------------------------------------------------------------
# LAG 3 — FLAG.  IKKE sandsynligheder.  Taelles, ikke modelleres.
# ------------------------------------------------------------------------------
I=INPUT
FLAGS = [
 ("Realt kontantafkast < 0",  I['fed_funds']-I['pce_head'] < 0,
  f"{I['fed_funds']:.2f}% - {I['pce_head']:.2f}% = {I['fed_funds']-I['pce_head']:+.2f}%", "DEBASERING"),
 ("CAPE i oeverste 5%",       cape_percentil(I['cape']) > 0.95,
  f"CAPE {I['cape']:.1f} = {cape_percentil(I['cape'])*100:.1f}. pct", "REPRICING"),
 ("Negativ risikopraemie",    100/I['cape'] - I['y10'] < 0,
  f"{100/I['cape']:.2f}% - {I['y10']:.2f}% = {100/I['cape']-I['y10']:+.2f}pp", "REPRICING"),
 ("Marginlaan > +30% y/y",    I['margin_yoy'] > 30,
  f"{I['margin_yoy']:+.1f}% y/y", "REPRICING"),
 ("Kurven inverteret",        x['curve'] < 0, f"{x['curve']:+.2f}pp", "RECESSION"),
 ("Sahm-regel > 0,50",        I['sahm'] > 0.50, f"{I['sahm']:.2f}", "RECESSION"),
 ("HY OAS > 600bp",           I['hy_oas'] > 600, f"{I['hy_oas']:.0f}bp", "RECESSION"),
 ("S&P drawdown > 20%",       I['spx_vs_hi'] < -0.20, f"{I['spx_vs_hi']*100:+.0f}%", "RECESSION"),
]
print()
print("="*78)
print("LAG 3 — FLAG   [IKKE valideret. Taellinger, ikke sandsynligheder.]")
print("="*78)
for n,v,val,cat in FLAGS:
    print(f"  [{'X' if v else ' '}] {n:<26}{val:<24}{cat}")
for cat in ("RECESSION","REPRICING","DEBASERING"):
    sub=[f for f in FLAGS if f[3]==cat]
    n=sum(1 for f in sub if f[1])
    print(f"\n  {cat:<12}{n}/{len(sub)} udloest")

# ------------------------------------------------------------------------------
# DOM
# ------------------------------------------------------------------------------
rec_n=sum(1 for f in FLAGS if f[3]=="RECESSION" and f[1])
rep_n=sum(1 for f in FLAGS if f[3]=="REPRICING" and f[1])
print()
print("="*78); print("DOM"); print("="*78)
if p12 < BASE and rec_n==0:
    print(f"  RECESSION:   Lav. {p12*100:.1f}% mod basisrate {BASE*100:.1f}%. Nul flag.")
elif rec_n>=2:
    print(f"  RECESSION:   FORHOEJET. {rec_n} flag udloest. Handl.")
else:
    print(f"  RECESSION:   {p12*100:.1f}%. {rec_n} flag.")
print(f"  REPRICING:   {rep_n}/4 flag udloest — {'hoej' if rep_n>=3 else 'moderat'} risiko.")
print(f"  DEBASERING:  {'AKTIV' if I['fed_funds']-I['pce_head']<0 else 'inaktiv'}"
      f" — realt kontantafkast {I['fed_funds']-I['pce_head']:+.2f}%")
print(f"""
  MOENSTER: lav gnist, hoejt braendstof.
  Recessionsrisikoen er valideret lav. Vaerdiansaettelse og gearing
  er ekstreme. Det betyder markedsrisiko FOER oekonomisk risiko.

  ENESTE TRIGGER MED BEVIST LEDETID: kurven under nul.
  Nu {x['curve']:+.2f}pp. Afstand: {x['curve']*100:.0f} basispoint.
""")

print("="*78)
print("ADVARSEL")
print("="*78)
print(f"""  LAG 1 er valideret paa {NOBS} kvartaler og {NEP} episoder. {NEP} er faa.
  95%-interval om basisraten alene er bredt nok til at overlappe
  modellens output. Forskellen mellem {p12*100:.1f}% og {BASE*100:.1f}% er
  IKKE statistisk sikker.

  Modellens vaerste fejl var 2023: 76,9% uden recession. Hvis
  rentekurven har mistet betydning i det nuvaerende regime, gaelder
  det BEGGE veje — ogsaa naar den er positiv.

  LAG 2-4 er ikke valideret. Brug dem som tjekliste, ikke som tal.
  Recessionsdefinition: 2 kvartaler i traek med negativ real BNP-vaekst.
  Det er ikke NBER. 2001 mangler derfor i kalibreringen.

  Kapaciteten til at forudsige eksogene chok er nul. COVID scorede
  46% - modellen saa 2019-inversionen, ikke virussen.
""")
