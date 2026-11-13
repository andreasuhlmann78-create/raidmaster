import sys, re, json, statistics as st, collections
from datetime import datetime, timezone, timedelta
from lupa.lua51 import LuaRuntime
lua = LuaRuntime(unpack_returned_tuples=True)
lua.execute(open(sys.argv[1], encoding="utf-8", errors="replace").read())
DB = lua.globals().AHSentinelDB
rx = re.compile(r"(\d+),([\d.e+\-]+),([\d.e+\-]*),(\d*),(\d*)")
series = {}
mk_names=[]
for mk in DB.markets.keys():
    mk_names.append(mk)
    m = DB.markets[mk]
    if not m.data: continue
    for id in m.data.keys():
        d = m.data[id]; pts=[]
        if d.hz:
            prev=0
            for dt,p,q,c,f in rx.findall(d.hz):
                prev+=int(dt); fl=int(f) if f else 0
                if fl==0: pts.append((prev,float(p),float(q) if q else None))
        h=d.history
        if h:
            for i in range(1,len(h)+1):
                e=h[i]
                if e is None: continue
                if e.u or e.s: continue
                if e.t and e.p: pts.append((int(e.t),float(e.p),float(e.q) if e.q else None))
        if pts:
            pts.sort(); series[(mk,int(id))]=pts
print("Märkte:", len(mk_names), "Items mit Verlauf:", len(series))
allt=[p[0] for s in series.values() for p in s]
tz=timezone(timedelta(hours=1))
print("Zeitraum:", datetime.fromtimestamp(min(allt),tz), "bis", datetime.fromtimestamp(max(allt),tz), "Punkte:", len(allt))
json.dump({f"{k[0]}|{k[1]}":v for k,v in series.items()}, open(sys.argv[2],"w"))
