import sys, collections, statistics as st
from lupa.lua51 import LuaRuntime
lua=LuaRuntime(unpack_returned_tuples=True)
lua.execute(open(sys.argv[1],encoding='utf-8',errors='replace').read())
DB=lua.globals().AHSentinelDB
F=["t","id","q","pr","way","ev","src","v","g","r","rq","rv","rk","mv","aid"]
rows=[]
L=DB.forecast.list
for i in range(1,len(L)+1):
    s=L[i]
    if not s or s[0]!='B': continue
    p=s.split(';')[1:]
    e={F[j]:(p[j] if j<len(p) else '') for j in range(len(F))}
    def n(k):
        try: return float(e[k])
        except: return None
    rows.append(dict(q=n('q') or 1,pr=n('pr'),way=e['way'],ev=n('ev'),src=e['src'],r=e['r'],rq=n('rq') or 0,rv=n('rv'),rk=e['rk'],mv=n('mv'),g=e['g']))
print("Käufe:", len(rows), dict(collections.Counter(r['src'] for r in rows)), "Weg:", dict(collections.Counter(r['way'] for r in rows)))
done=[r for r in rows if r['rv'] is not None and r['rq']>0 and r['pr']]
print("mit Ergebnis (zugeordnet):", len(done))
def agg(lst):
    cost=sum(r['pr']*r['rq'] for r in lst); rev=sum(r['rv'] for r in lst)
    return rev/cost-1 if cost else None, cost, rev
g,c,rv=agg(done); print(f"GESAMT: Einsatz {c/10000:.2f}g · Erlös netto {rv/10000:.2f}g · Gewinn {g*100:+.1f} %")
for src in sorted(set(r['src'] for r in done)):
    g,c,rv=agg([r for r in done if r['src']==src]); print(f"  Quelle {src}: n={sum(1 for r in done if r['src']==src)} Gewinn {g*100:+.1f} % (Einsatz {c/10000:.2f}g)")
print("\nJe Kaufpreis / vorhergesagtem Wert (ev = erwarteter Netto-Wert je Stück):")
def b(x):
    for t in (0.5,0.6,0.7,0.8,0.9,1.0,1.2):
        if x<=t: return f"<= {t:.1f}"
    return "> 1.2"
G=collections.defaultdict(list)
for r in done:
    if r['ev']: G[b(r['pr']/r['ev'])].append(r)
for k in sorted(G, key=lambda x:(x.startswith('>'), x)):
    g,c,rv=agg(G[k]); print(f"  {k}: n={len(G[k])} Gewinn gesamt {g*100:+.1f} %  (Einsatz {c/10000:.2f}g)")
print("\nJe Kaufpreis / Marktwert beim Kauf (mv):")
G=collections.defaultdict(list)
for r in done:
    if r['mv']: G[b(r['pr']/r['mv'])].append(r)
for k in sorted(G, key=lambda x:(x.startswith('>'), x)):
    g,c,rv=agg(G[k]); print(f"  {k}: n={len(G[k])} Gewinn gesamt {g*100:+.1f} %")
