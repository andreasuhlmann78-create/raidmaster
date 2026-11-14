import sys, math
from lupa.lua51 import LuaRuntime
lua=LuaRuntime(unpack_returned_tuples=True)
lua.execute(open(sys.argv[1],encoding='utf-8',errors='replace').read())
DB=lua.globals().AHSentinelDB
F=["t","id","q","a","pr","rel","d","Q","qs","S","ss","u","p","W","N","net","v","g","r","sq","sh","sp","x","ex","rs","cr"]
rows=[]
L=DB.forecast.list
for i in range(1,len(L)+1):
    s=L[i]
    if not s or s[0]!='P': continue
    p=s.split(';')[1:]
    e={F[j]:(p[j] if j<len(p) else '') for j in range(len(F))}
    def n(k):
        try: return float(e[k])
        except: return None
    r=e['r']
    if r not in ('s','t','e'): continue   # s verkauft, t teil, e abgelaufen; c Abbruch raus
    rows.append(dict(id=e['id'],q=n('q') or 1,rel=n('rel'),d=n('d') or 2,Q=n('Q'),qs=e['qs'],S=n('S'),p=n('p'),sold=1 if (n('sq') or 0)>0 else 0,g=e['g'],v=e['v']))
print("Fälle",len(rows),"verkauft",sum(r['sold'] for r in rows))
print("mit Q",sum(r['Q'] is not None for r in rows),"mit S",sum(r['S'] is not None for r in rows))
for r in rows[:5]: print(r)
def brier(pred): return sum((pred[i]-r['sold'])**2 for i,r in enumerate(rows))/len(rows)
def acc(pred): return sum((pred[i]>=0.5)==(r['sold']==1) for i,r in enumerate(rows))/len(rows)
old=[(r['p'] or 0)/100 if (r['p'] or 0)>1 else (r['p'] or 0) for r in rows]
print("alt  Brier %.3f Treffer %.0f%%"%(brier(old),100*acc(old)))
def band(x):
    if x is None: return 'na'
    return 0 if x<=0.90 else 1 if x<=0.97 else 2 if x<=1.03 else 3 if x<=1.10 else 4
def loo(keyf,prior=0.45,k=2):
    pred=[]
    for i,r in enumerate(rows):
        b=keyf(r); same=[o['sold'] for j,o in enumerate(rows) if j!=i and keyf(o)==b]
        pred.append((sum(same)+prior*k)/(len(same)+k))
    return pred
pb=loo(lambda r:band(r['rel']))
print("Preisstufe (ohne eigenen Fall) Brier %.3f Treffer %.0f%%"%(brier(pb),100*acc(pb)))
def qratio(r):
    if r['Q'] is None or not r['S']: return None
    dem=r['S']*r['d']/24
    return (r['Q']+r['q'])/max(dem,1e-9)
def qb(r):
    x=qratio(r)
    if x is None: return 'na'
    return 0 if x<=0.5 else 1 if x<=1 else 2 if x<=2 else 3 if x<=5 else 4
pq=loo(qb)
print("Schlange (ohne eigenen Fall) Brier %.3f Treffer %.0f%%"%(brier(pq),100*acc(pq)))
import collections
c=collections.defaultdict(lambda:[0,0])
for r in rows: c[qb(r)][0]+=1; c[qb(r)][1]+=r['sold']
print("Schlange/Bedarf in Laufzeit:",{k:f"{v[1]}/{v[0]}" for k,v in sorted(c.items(),key=lambda x:str(x[0]))})
c=collections.defaultdict(lambda:[0,0])
for r in rows: c[band(r['rel'])][0]+=1; c[band(r['rel'])][1]+=r['sold']
print("Preisstufe:",{k:f"{v[1]}/{v[0]}" for k,v in sorted(c.items(),key=lambda x:str(x[0]))})
print("Q=0 (vorne):", sum(1 for r in rows if r['Q']==0), "verkauft", sum(r['sold'] for r in rows if r['Q']==0))
print("Q>0:", sum(1 for r in rows if r['Q'] and r['Q']>0), "verkauft", sum(r['sold'] for r in rows if r['Q'] and r['Q']>0))
pc=loo(lambda r:(r['Q']==0))
print("nur 'bin ich vorne' (ohne eigenen Fall) Brier %.3f Treffer %.0f%%"%(brier(pc),100*acc(pc)))
print("Quelle Q:",collections.Counter(r['qs'] for r in rows))
