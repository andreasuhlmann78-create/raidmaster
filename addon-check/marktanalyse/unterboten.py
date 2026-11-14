import sys, json, bisect, collections, re
from lupa.lua51 import LuaRuntime
lua=LuaRuntime(unpack_returned_tuples=True)
lua.execute(open(sys.argv[1],encoding='utf-8',errors='replace').read())
DB=lua.globals().AHSentinelDB
BASE=int(re.search(r'local BASE\s*=\s*(\d+)',open('/home/claude/ahanalyzerpro/Forecast.lua').read()).group(1))
F=["t","id","q","a","pr","rel","d","Q","qs","S","ss","u","p","W","N","net","v","g","r","sq","sh","sp","x","ex","rs","cr"]
ser={int(k.rsplit('|',1)[1]):v for k,v in json.load(open(sys.argv[2])).items()}
L=DB.forecast.list; rows=[]
for i in range(1,len(L)+1):
    s=L[i]
    if not s or s[0]!='P': continue
    p=s.split(';')[1:]; e={F[j]:(p[j] if j<len(p) else '') for j in range(len(F))}
    def n(k):
        try: return float(e[k])
        except: return None
    rows.append(dict(t=BASE+int(n('t'))*60,id=int(e['id']),pr=n('pr'),d=n('d') or 2,r=e['r'],sold=(n('sq') or 0)>0,sh=n('sh'),cr=e['cr']))
c=collections.defaultdict(lambda:[0,0]); scans=[]
for r in rows:
    pts=ser.get(r['id'],[]); ts=[x[0] for x in pts]
    end=r['t']+r['d']*3600
    if r['sold'] and r['sh'] is not None: end=min(end,r['t']+r['sh']*3600)
    i=bisect.bisect_left(ts,r['t']+60); j=bisect.bisect_right(ts,end)
    win=pts[i:j]
    if not win: key='kein Scan in der Laufzeit'
    else:
        under=any(x[1] < r['pr']-0.5 for x in win)
        key='unterboten' if under else 'nicht unterboten'
    grp='Abbruch' if r['r']=='c' else ('verkauft' if r['sold'] else 'abgelaufen')
    c[(key,grp)][0]+=1
    r['key']=key; r['grp']=grp
for k in sorted(c): print(k,c[k][0])
print("Abbruch-Grund im Journal (cr):",collections.Counter(r['cr'] for r in rows if r['r']=='c'))
print("--- nicht unterboten + abgelaufen: Preis/Marktwert und Absatz/Tag vs Menge")
for r0 in DB.forecast.list.values():
    pass

for r in rows:
    if r.get('key')=='nicht unterboten' and r['grp']=='abgelaufen': print(r['id'],'Preis',r['pr'])
