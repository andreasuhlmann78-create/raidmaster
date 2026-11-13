import sys, json, collections, statistics as st, bisect
from lupa.lua51 import LuaRuntime
lua=LuaRuntime(unpack_returned_tuples=True)
lua.execute(open(sys.argv[1],encoding='utf-8',errors='replace').read())
DB=lua.globals().AHSentinelDB
BASE=None
F=["t","id","q","a","pr","rel","d","Q","qs","S","ss","u","p","W","N","net","v","g","r","sq","sh","sp","x","ex","rs"]
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
    rows.append(dict(tm=n('t'),id=int(e['id']),q=n('q') or 1,pr=n('pr'),r=e['r'],sq=n('sq') or 0,sh=n('sh')))
# Zeitbasis des Journals: t in Minuten seit BASE -> aus Forecast.lua
import re
src=open('/home/claude/ahanalyzerpro/Forecast.lua',encoding='utf-8').read()
m=re.search(r'local BASE\s*=\s*(\d+)',src); BASE=int(m.group(1))
for r in rows: r['t']=BASE+int(r['tm'])*60
ser={int(k.rsplit('|',1)[1]):v for k,v in json.load(open(sys.argv[2])).items()}
def minprice(id,t,before=True):
    pts=ser.get(id,[])
    ts=[x[0] for x in pts]
    i=bisect.bisect_right(ts,t)
    cand=[pts[j] for j in range(max(0,i-3),min(len(pts),i+1)) if abs(pts[j][0]-t)<=2*3600]
    return min((c[1] for c in cand), default=None)
# Abbrüche: unterboten?
under=0; notu=0; unk=0
for r in rows:
    if r['r']=='c':
        mp=minprice(r['id'], r['t']+3600)  # während der Laufzeit
        if mp is None or r['pr'] is None: unk+=1
        elif mp < r['pr']-0.5: under+=1
        else: notu+=1
print(f"Abbrüche 17: unterboten (fremdes Angebot günstiger während der Laufzeit) {under} · nicht unterboten {notu} · unklar {unk}")
# Ketten je Item: Einstellungen bis zum (Teil-)Verkauf
by=collections.defaultdict(list)
for r in sorted(rows,key=lambda x:x['t']): by[r['id']].append(r)
chains=[]
for id,lst in by.items():
    cur=[]
    for r in lst:
        cur.append(r)
        if r['r'] in ('s','t'):
            chains.append(cur); cur=[]
    if cur: chains.append(cur)
done=[c for c in chains if c[-1]['r'] in ('s','t')]
openc=[c for c in chains if c[-1]['r'] not in ('s','t')]
print(f"Ketten: {len(chains)} · mit Verkauf {len(done)} · ohne Verkauf (noch offen/aufgegeben) {len(openc)}")
if done:
    n=[len(c) for c in done]; dur=[(c[-1]['t']-c[0]['t'])/3600+(c[-1]['sh'] or 0) for c in done]
    print(f"  bis zum Verkauf: Einstellungen Median {st.median(n)} (1: {sum(1 for x in n if x==1)}, 2–3: {sum(1 for x in n if 2<=x<=3)}, >3: {sum(1 for x in n if x>3)}) · Zeit bis Verkauf Median {st.median(dur):.1f} Std.")
    drops=[ (c[-1]['pr']/c[0]['pr']) for c in done if len(c)>1 and c[0]['pr'] and c[-1]['pr']]
    if drops: print(f"  Preis beim Verkauf / Preis der ersten Einstellung (Ketten > 1): Median {st.median(drops):.2f} (n {len(drops)})")
