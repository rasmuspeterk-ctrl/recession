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
