# COUNCIL BRIEF — Recession Model v5

## Who you are

You are one of seven AI models on an advisory council convened by Rasmus, a Danish solo developer. The council: GPT-5.6 Sol (OpenAI), Kimi K3 (Moonshot), Gemini Pro (Google), Grok 4.5 (xAI), Nemotron 3 Ultra 550B (NVIDIA, open), Gemma 4 31B (Google, open), GPT-OSS-20B (OpenAI, open). You act as senior macro-econometricians. You advise; Rasmus decides.

## Context

Rasmus built MOTOR v4.0 together with Claude Opus 5 (August 2026): a US recession-probability model. Its philosophy, which he wants preserved unless you can show it is wrong:

1. **Radical simplicity.** Six manually updated numbers per month, ~5 minutes of work, one Python file, no dependencies beyond numpy. Runs on a normal Windows PC.
2. **Radical honesty.** Only walk-forward-validated claims get numbers. Everything else is explicitly labeled a checklist, not a probability. Complexity must buy walk-forward skill or it is rejected — this rule already killed one feature (inv_score: adding it dropped log-loss improvement from +22.9% to +18.8%, so it was demoted to a separate check).
3. **Free data only.** Shiller's spreadsheet, FRED, BLS, BEA. No paid feeds.

## The existing system (MOTOR v4.0)

- **LAG 1 (validated):** L2-regularized logistic regression, quarterly. Five features: curve (10y minus 3m), realrate (10y minus CPI y/y), dd (S&P vs 12-month high), d_infl (12-month change in CPI inflation), cape_pct (expanding-window CAPE percentile, 30-year burn-in). Target Y: a "technical recession" (two consecutive quarters of negative real GDP growth) occurring within the next 4 quarters. Calibration: 359 quarters 1934–2024, 11 recession episodes, walk-forward from 1960 (refit each step on past data only; means/SDs from training window only). Result: +22.9% log-loss improvement over the unconditional base rate (13.4%), Brier skill +19.4%. Separate per-horizon weight vectors for +1q…+4q, combined as p9 = 1 − Π(1 − p_h) for horizons 1–3.
- **LAG 2 (checklist, not model):** inversion-aftermath score = depth × exp(−months_since/24), zero after 36 months. Historical bucket table (e.g. score 0.5–1.0 → 14% recession within 4 quarters vs 13% base). Tested as a model feature; made walk-forward performance worse; therefore kept OUT of the model as a separate check.
- **LAG 3 (flags, counted not modeled):** 8 boolean flags in three categories. RECESSION: curve inverted; Sahm > 0.50; HY OAS > 600bp; S&P drawdown > 20%. REPRICING: CAPE above 95th percentile; negative equity risk premium (100/CAPE − y10 < 0); margin debt > +30% y/y. DEBASEMENT: real cash yield negative (fed funds − headline PCE < 0).
- **Verdict layer:** plain-language synthesis. Current reading (Aug 2026): P(recession 12m) = 8.8% vs base 13.4%; 0/4 recession flags; 3/3 repricing flags; 1/1 debasement flag. "Low spark, high fuel."

Full source code of MOTOR.py, the calibration script (curve.py) and the inversion test (inv.py) is appended below.

## Self-documented weaknesses (from the author)

- Recession definition is the technical rule, not NBER. **The 2001 recession is therefore missing from calibration.**
- Only 11 episodes. The 95% interval around the base rate alone is wide enough to overlap the model output; the difference between 8.8% and 13.4% is not statistically certain.
- Worst error: 2023, peak 76.9% predicted, no recession followed. If the yield curve has lost meaning in the current regime (QE, term-premium distortion), that cuts both ways — including now, when it is positive.
- Overlapping 4-quarter target windows → autocorrelated labels; the walk-forward metrics ignore this.
- Real-time label problem: GDP is revised. 2022 H1 printed two negative advance-estimate quarters (later revised); the current backtest uses final revised data, which is look-ahead in the label itself.
- Exogenous shocks are invisible: COVID scored 46% (the model saw the 2019 inversion, not the virus).
- LAG 2 and LAG 3 are not validated. Manual data entry once a month; no automation; no vintage (ALFRED) data.

## Your task

Debate until consensus on a **v5 blueprint**: what to keep, what to kill, what to change, what to add — plus a concrete build plan. Every recommendation must respect the philosophy: complexity must pay for itself in demonstrated walk-forward skill, or be explicitly labeled unvalidated.

## The eight contested questions

**Q1 — Label.** Technical two-quarter rule vs NBER dates (FRED: USREC) vs hybrid. 2001 in or out? How do you handle the fact that real-time GDP would have labeled 2022 H1 a recession before revisions? Which label is even knowable in real time?

**Q2 — Frequency and horizon.** Stay quarterly or go monthly (NBER dates are monthly; most inputs are monthly; episodes stay ~a dozen either way)? Keep the within-4-quarters window? Keep per-horizon models and the p9 = 1 − Π(1 − p_h) combination (it assumes independence across horizons — defensible)?

**Q3 — Features.** Keep the five? Add or drop what — Sahm rule as a feature (not just a flag), initial claims, HY OAS (history only from ~1997), building permits, term-premium-adjusted curve, foreign curves, money/credit growth? How many features can ~12 episodes support before it is curve-fitting? Specify a feature-selection protocol that avoids the garden of forking paths.

**Q4 — Statistics.** Is L2 logit the right engine, or do you argue for Bayesian logit with priors, Markov-switching, gradient boosting, or an ensemble — given n_episodes ≈ 12? How should validation handle overlapping windows and autocorrelation (episode-blocked CV, block bootstrap, HAC-style corrections)? Should the output carry an uncertainty band, and how?

**Q5 — Regime instability.** The 2023 false alarm: QE/term-premium distortion of the curve signal. Adjust the curve (e.g. ACM term premium), add a regime interaction, add the Fed's balance sheet — or accept the error and communicate it? Justify against the walk-forward rule.

**Q6 — Architecture.** Is the layered design (validated model + unvalidated checklists, kept strictly apart) sound epistemics, or should flags be validated and integrated (e.g. as a second ensemble member) — or dropped? Is the layering a defensible firewall or a backdoor for vibes?

**Q7 — Data and ops.** Keep manual 6-number monthly entry, or automate via the free FRED API (with manual fallback)? Add ALFRED vintage data so the backtest uses only information available at the time — worth the complexity? Where exactly does simplicity stop paying?

**Q8 — Output and benchmarks.** What should the tool report (point probability, interval, flags, verdict)? Must v5 be benchmarked against the NY Fed yield-curve probit, Chauvet–Piger smoothed probabilities, and the real-time Sahm rule — and does it need to beat them, or merely be reported alongside them?

## Constraints (non-negotiable)

Python, free data only, runs locally on Windows, solo-maintainable, no look-ahead in fit or label, and the honesty firewall: unvalidated components must be labeled as such in the output.

---

## APPENDIX A — MOTOR.py (the tool itself)
```python
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
```

## APPENDIX B — curve.py (calibration / walk-forward)
```python
"""
AFGOERENDE TEST — rentekurven tilfoejet.

TB3MS 1934-2026 uploadet af brugeren (FRED, primaerkilde).
Shillers 'Long Interest Rate' raekker tilbage til 1871, saa kurven
kan nu beregnes fra 1934 — 20 aar mere end sidste koersel.
"""
import numpy as np, pandas as pd
pd.set_option('display.width', 220)

spx = pd.read_csv('data/spx.csv'); spx['Date']=pd.to_datetime(spx['Date'])
spx = spx.replace(0.0, np.nan).rename(columns={
    'Date':'date','SP500':'px','Consumer Price Index':'cpi',
    'Long Interest Rate':'ltr','PE10':'cape'})
y10 = pd.read_csv('data/y10.csv'); y10['Date']=pd.to_datetime(y10['Date'])
y10 = y10.rename(columns={'Date':'date','Rate':'y10'})
tb  = pd.read_csv('data/tb3m.csv'); tb['observation_date']=pd.to_datetime(tb['observation_date'])
tb  = tb.rename(columns={'observation_date':'date','TB3MS':'tb3m'})
gdp = pd.read_csv('data/gdp.csv'); gdp['date']=pd.to_datetime(gdp['date'])
gdp = gdp[['date','change-chained']].rename(columns={'change-chained':'g'}).dropna()

m = (spx[['date','px','cpi','ltr','cape']]
     .merge(y10,on='date',how='left').merge(tb,on='date',how='left')
     .sort_values('date').reset_index(drop=True))
m['y10'] = m['y10'].fillna(m['ltr'])

# ---- features ----
m['curve']    = m['y10'] - m['tb3m']          # RENTEKURVEN
m['curve_min12'] = m['curve'].rolling(12,min_periods=6).min()
m['infl']     = m['cpi'].pct_change(12)*100
m['realrate'] = m['y10'] - m['infl']
m['d_rate']   = m['tb3m'] - m['tb3m'].shift(12)
m['dd']       = m['px']/m['px'].rolling(12,min_periods=6).max()-1
m['mom12']    = m['px'].pct_change(12)*100
m['d_infl']   = m['infl'] - m['infl'].shift(12)
m['cape_pct'] = m['cape'].expanding(120).apply(lambda s:(s.iloc[-1]>s).mean())

m['q']=m['date'].dt.to_period('Q')
q=m.groupby('q').last(numeric_only=True).reset_index(); q['date']=q['q'].dt.to_timestamp()
gdp['q']=gdp['date'].dt.to_period('Q')
q=q.merge(gdp[['q','g']],on='q',how='left')

neg=(q['g']<0).astype(float)
q['rec_now']=((neg==1)&(neg.shift(1)==1)).astype(float)
for k in range(1,5): q[f'_f{k}']=q['rec_now'].shift(-k)
q['Y']=q[[f'_f{k}' for k in range(1,5)]].max(axis=1)

BASE=['curve','curve_min12','realrate','d_rate','dd','mom12','infl','d_infl','cape_pct','g']
D=q.dropna(subset=BASE+['Y']).reset_index(drop=True)

print("="*82); print("AFGOERENDE TEST — rentekurven med"); print("="*82)
print(f"Observationer:  {len(D)} kvartaler   {D['date'].min():%Y-%m} til {D['date'].max():%Y-%m}")
print(f"Recessioner:    {int(D['Y'].sum())} kvartaler = {D['Y'].mean()*100:.1f}%")
r=D[D['rec_now']==1]['date']; runs=[]
for d in r:
    if runs and (d-runs[-1][-1]).days<=200: runs[-1].append(d)
    else: runs.append([d])
print(f"Episoder:       {len(runs)}  ->  " + ", ".join(f"{x[0]:%Y}" for x in runs))
print(f"\nKurven nu (jul 2026): {m['curve'].iloc[-1]:+.2f}pp  "
      f"(10y {m['y10'].iloc[-1]:.2f}% - 3m {m['tb3m'].iloc[-1]:.2f}%)")

def fit(X,y,l2=1.0,it=300):
    X=np.c_[np.ones(len(X)),X]; w=np.zeros(X.shape[1])
    for _ in range(it):
        p=1/(1+np.exp(-np.clip(X@w,-30,30)))
        gr=X.T@(p-y)+l2*np.r_[0,w[1:]]
        H=X.T@(X*(p*(1-p))[:,None])+l2*np.eye(X.shape[1]); H[0,0]-=l2
        try: w-=np.linalg.solve(H+1e-6*np.eye(len(w)),gr)
        except: break
    return w
pr=lambda w,X:1/(1+np.exp(-np.clip(np.c_[np.ones(len(X)),X]@w,-30,30)))

def wf(feats,start=1960,l2=1.0):
    out=[]
    for i in range(len(D)):
        if D['date'].iloc[i].year<start: continue
        tr=D.iloc[:i]
        if len(tr)<60 or tr['Y'].sum()<6: continue
        mu,sd=tr[feats].mean(),tr[feats].std().replace(0,1)
        w=fit(((tr[feats]-mu)/sd).values,tr['Y'].values,l2)
        x=((D[feats].iloc[[i]]-mu)/sd).values
        out.append((D['date'].iloc[i],float(pr(w,x)[0]),D['Y'].iloc[i]))
    return pd.DataFrame(out,columns=['date','p','y'])

def mt(r):
    p=np.clip(r['p'],1e-6,1-1e-6); y=r['y'].values
    ll=-np.mean(y*np.log(p)+(1-y)*np.log(1-p)); b=y.mean()
    bl=-np.mean(y*np.log(b)+(1-y)*np.log(1-b))
    return ll,bl,(1-ll/bl)*100,(1-np.mean((p-y)**2)/np.mean((b-y)**2))*100

SETS={
 "1: KURVEN alene":        ['curve'],
 "1b: kurve 12m-min":      ['curve_min12'],
 "2: kurve + realrente":   ['curve','realrate'],
 "3: + drawdown":          ['curve','realrate','dd'],
 "4: + inflation":         ['curve','realrate','dd','d_infl'],
 "5: + CAPE":              ['curve','realrate','dd','d_infl','cape_pct'],
 "6: alle 10":             BASE,
 "kontrol: uden kurve":    ['realrate','d_rate','dd','d_infl','cape_pct'],
}
print(); print("="*82)
print("WALK-FORWARD  (fit kun paa fortid, test 1960-2024)"); print("="*82)
print(f"{'Model':<26}{'log-loss':>10}{'basis':>9}{'forbedring':>12}{'Brier-skill':>13}")
print("-"*82)
res={}
for n,f in SETS.items():
    r=wf(f); res[n]=(r,f); ll,bl,imp,bs=mt(r)
    star=" <-- POSITIV" if imp>0 else ""
    print(f"{n:<26}{ll:>10.3f}{bl:>9.3f}{imp:>11.1f}%{bs:>12.1f}%{star}")

best=max(res,key=lambda k:mt(res[k][0])[2])
r,f=res[best]; ll,bl,imp,bs=mt(r)
print(f"\nBEDSTE: {best}   forbedring {imp:+.1f}%   Brier-skill {bs:+.1f}%")

print(); print("="*82); print("LEAD/LAG for kurven"); print("="*82)
x=(D['curve']-D['curve'].mean())/D['curve'].std()
print(f"{'kvartaler foer/efter':<24}"+"".join(f"{k:>7}" for k in range(-8,3)))
row=[np.corrcoef(x,D['rec_now'].shift(k).fillna(0))[0,1] for k in range(-8,3)]
print(f"{'korrelation':<24}"+"".join(f"{v:>7.2f}" for v in row))
print(f"-> staerkest ved {int(np.argmax(np.abs(row)))-8:+d} kvartaler")

print(); print("="*82); print("TOPPUNKTER — hvad sagde bedste model?"); print("="*82)
r['yr']=r['date'].dt.year
for lo,hi in [(1968,1971),(1972,1976),(1978,1983),(1988,1992),(1999,2003),(2005,2010),(2018,2021),(2021,2024)]:
    s=r[(r['yr']>=lo)&(r['yr']<=hi)]
    if len(s)==0: continue
    pk=s.loc[s['p'].idxmax()]
    print(f"  {lo}-{hi}:  top {pk['p']*100:5.1f}%  ({pk['date']:%Y}Q{(pk['date'].month-1)//3+1})"
          f"   faktisk: {'RECESSION' if s['y'].max() else 'ingen'}")

# ---- NU ----
print(); print("="*82); print("AFLAESNING NU"); print("="*82)
mu,sd=D[f].mean(),D[f].std().replace(0,1)
w=fit(((D[f]-mu)/sd).values,D['Y'].values,1.0)
cur=m.dropna(subset=['curve']).iloc[-1]
vals={'curve':cur['curve'],'curve_min12':cur['curve_min12'],'realrate':cur['y10']-cur['infl'],
      'd_rate':cur['tb3m']-m['tb3m'].iloc[-13],'dd':cur['dd'],'mom12':cur['mom12'],
      'infl':cur['infl'],'d_infl':cur['d_infl'],'cape_pct':D['cape_pct'].iloc[-1],'g':2.0}
X=pd.DataFrame([{k:vals[k] for k in f}])
p=float(pr(w,((X-mu[f])/sd[f]).values)[0])
for k in f: print(f"   {k:<14}{vals[k]:>8.2f}")
print(f"\n   P(recession inden for 4 kvartaler) = {p*100:.1f}%")
print(f"   Basisrate                          = {D['Y'].mean()*100:.1f}%")
r.to_csv('wf_curve.csv',index=False)
```

## APPENDIX C — inv.py (inversion-aftermath test)
```python
"""Loeser det aabne spoergsmaal: betyder inversionshistorik noget?"""
import numpy as np, pandas as pd
exec(open('curve.py').read().split('SETS={')[0])

# byg inversionshistorik paa maanedsniveau
mm=m.dropna(subset=['curve']).copy().reset_index(drop=True)
inv=(mm['curve']<0).values
since=np.full(len(mm),np.nan); depth=np.full(len(mm),np.nan); dur=np.full(len(mm),np.nan)
last_end=None; cur_depth=None; cur_len=0; run=0
for i in range(len(mm)):
    if inv[i]:
        run+=1; cur_depth=min(cur_depth,mm['curve'].iloc[i]) if cur_depth is not None else mm['curve'].iloc[i]
        since[i]=0; depth[i]=cur_depth; dur[i]=run
    else:
        if run>0: last_end=i; last_depth=cur_depth; last_len=run; run=0; cur_depth=None
        if last_end is not None:
            since[i]=i-last_end; depth[i]=last_depth; dur[i]=last_len
mm['inv_since']=since; mm['inv_depth']=depth; mm['inv_dur']=dur
mm['inv_recent']=(mm['inv_since']<=36).astype(float)   # inversion inden for 3 aar
mm['inv_score']=np.where(mm['inv_since']<=36, -mm['inv_depth']*np.exp(-mm['inv_since']/24), 0.0)

mq=mm.groupby(mm['date'].dt.to_period('Q')).last(numeric_only=True)
mq.index.name='q'; mq=mq.reset_index()
D2=q.merge(mq[['q','inv_since','inv_depth','inv_dur','inv_recent','inv_score']],on='q',how='left')
BASE2=['curve','realrate','dd','d_infl','cape_pct']
D2=D2.dropna(subset=BASE2+['Y','inv_score']).reset_index(drop=True)
globals()['D']=D2

print("="*74); print("NY VARIABEL: inversions-eftervirkning"); print("="*74)
print("inv_score = dybde * exp(-maaneder_siden/24), 0 hvis >36 mdr siden")
print(f"\nNu: inversion sluttede nov 2024, dybde -1,57pp")
s_now=20; d_now=-1.57
sc_now=-d_now*np.exp(-s_now/24)
print(f"    {s_now} mdr siden -> inv_score = {sc_now:.2f}")
h=D2[D2['inv_score']>0]
print(f"\nHistoriske kvartaler med inv_score > 0: {len(h)}")
print(f"   heraf recession inden 4 kvt: {h['Y'].mean()*100:.0f}%  (mod {D2['Y'].mean()*100:.0f}% generelt)")
for lo,hi in [(0,0.5),(0.5,1.0),(1.0,2.0),(2.0,9)]:
    g=D2[(D2['inv_score']>=lo)&(D2['inv_score']<hi)]
    if len(g)>3: print(f"   inv_score {lo:.1f}-{hi:.1f}: {len(g):>3} kvt, recession {g['Y'].mean()*100:>3.0f}%")

def wf2(feats,start=1960):
    out=[]
    for i in range(len(D2)):
        if D2['date'].iloc[i].year<start: continue
        tr=D2.iloc[:i]
        if len(tr)<60 or tr['Y'].sum()<6: continue
        mu,sd=tr[feats].mean(),tr[feats].std().replace(0,1)
        w=fit(((tr[feats]-mu)/sd).values,tr['Y'].values,1.0)
        out.append((float(pr(w,((D2[feats].iloc[[i]]-mu)/sd).values)[0]),D2['Y'].iloc[i]))
    o=pd.DataFrame(out,columns=['p','y']); p=np.clip(o['p'],1e-6,1-1e-6); y=o['y'].values; b=y.mean()
    ll=-np.mean(y*np.log(p)+(1-y)*np.log(1-p)); bl=-np.mean(y*np.log(b)+(1-y)*np.log(1-b))
    return (1-ll/bl)*100,(1-np.mean((p-y)**2)/np.mean((b-y)**2))*100

print()
print("="*74); print("GOER DET MODELLEN BEDRE?"); print("="*74)
print(f"{'Model':<40}{'forbedring':>13}{'Brier':>10}")
for n,f in [("Kurven alene",['curve']),
            ("v1 (5 features)",BASE2),
            ("+ inv_score",BASE2+['inv_score']),
            ("+ inv_since + inv_depth",BASE2+['inv_since','inv_depth']),
            ("kun kurve + inv_score",['curve','inv_score'])]:
    a,b=wf2(f); print(f"{n:<40}{a:>12.1f}%{b:>9.1f}%")

print()
print("="*74); print("AFLAESNING MED OG UDEN"); print("="*74)
NOW={'curve':0.67,'realrate':0.87,'dd':0.0,'d_infl':0.86,'cape_pct':0.994,'inv_score':sc_now,
     'inv_since':20.0,'inv_depth':-1.57}
for n,f in [("v1 uden inversionshistorik",BASE2),("v2 MED inv_score",BASE2+['inv_score'])]:
    mu,sd=D2[f].mean(),D2[f].std().replace(0,1)
    w=fit(((D2[f]-mu)/sd).values,D2['Y'].values,1.0)
    p=float(pr(w,((pd.DataFrame([NOW])[f]-mu)/sd).values)[0])
    print(f"  {n:<32}{p*100:>6.1f}%")
print(f"  {'Analog-metoden (52 mdr)':<32}{44.2:>6.1f}%")
print(f"  {'Basisrate':<32}{D2['Y'].mean()*100:>6.1f}%")
```
