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
