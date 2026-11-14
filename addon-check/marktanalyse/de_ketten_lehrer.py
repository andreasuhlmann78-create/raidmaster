import re
from lupa import LuaRuntime
lua=LuaRuntime(unpack_returned_tuples=True)
lua.execute(open('/home/claude/goldsentinel-daten/aktuell/DESKTOP-NVITMSE/forever/konto-5cb3d536/AHSentinel.lua',encoding='utf-8',errors='replace').read())
db=lua.globals().AHSentinelDB; T=lua.eval('type')
M=db.markets['CAMWOW EU4 Realm 6 PvP|Horde'].data
def ah(i):
    e=M[i]
    if e is None or e.history is None: return None
    last=None
    for k,v in e.history.items(): last=v
    return last.p if last else None
VB=db.vendorBuy
def cost(i):
    v=VB[i]; a=ah(i)
    c=[x for x in (v,a) if x]
    return min(c) if c else None
src=open('/home/claude/professionsentinel/ProfessionSentinel/Data_Forever.lua',encoding='utf-8').read()
items={int(m.group(1)):(m.group(2),int(m.group(3))) for m in re.finditer(r'^\[(\d+)\]=\{"((?:[^"\\]|\\.)*)",(\d+),',src,re.M)}
rows=re.findall(r'^\{(\d+),197,"([^"]*)",(?:"[^"]*"|nil),(?:"[^"]*"|nil),\d+,(\d+),(\d+),(\d+),(\d+),(\d+),(\d+),(\d+),(\d+),\d+,\d+,\{([^}]*)\}',src,re.M)
# Itemstufe (aus Classic-Wissen, ungeprüft)
ILVL={4343:12,4307:11,2580:12,6238:11,2578:14,4308:13,4309:14,2569:13,4312:16,10047:12,6241:12,
2582:17,2583:19,4310:17,4314:22,4316:22,2584:16,4318:23,5542:20,6787:22,
7046:28,7048:29,4324:30,7050:32,7051:32,7052:35,7057:36,7058:37,7062:39,7055:37,7064:42,4326:37,5766:27,
9998:41,9999:41,10001:42,10003:43,10024:46,10026:46,10027:46,10002:43,10004:43,10023:45,10028:48,10031:49,
10042:50,10044:51,13856:52,18258:51}
G=[(15,[(10940,1.5,.80),(10938,1.5,.20)]),(20,[(10940,2.5,.75),(10939,1.5,.20),(10978,1,.05)]),
(25,[(10940,5,.75),(10998,1.5,.15),(10978,1,.10)]),(30,[(11083,1.5,.75),(11082,1.5,.20),(11084,1,.05)]),
(35,[(11083,3.5,.75),(11134,1.5,.20),(11138,1,.05)]),(40,[(11137,1.5,.75),(11135,1.5,.20),(11139,1,.05)]),
(45,[(11137,3.5,.75),(11174,1.5,.20),(11177,1,.05)]),(50,[(11176,1.5,.75),(11175,1.5,.20),(11178,1,.05)]),
(55,[(11176,3.5,.75),(16202,1.5,.20),(14343,1,.05)])]
GN=['5-15','16-20','21-25','26-30','31-35','36-40','41-45','46-50','51-55']
def de(il):
    for gi,(top,mats) in enumerate(G):
        if il<=top:
            v=0
            for i,n,p in mats:
                pr=ah(i)
                if pr is None: return None,GN[gi]
                v+=n*p*pr*0.95
            return v,GN[gi]
    return None,'?'
CLOTH={2996:(2589,2),2997:(2592,2),4305:(4306,2),4339:(4338,2),14048:(14047,4)}
def mcost(i):
    c=cost(i)
    if i in CLOTH:
        cl,n=CLOTH[i]; cc=cost(cl)
        if cc: c=min(c,cc*n) if c else cc*n
    return c
res=[]
for sp,name,s0,y,g,gr,oid,cmin,cmax,bits,reag in rows:
    if not int(bits)&1: continue
    oid=int(oid)
    if items.get(oid,("",0))[1]!=2 or oid not in ILVL: continue
    r=reag.split(','); tot=0; miss=[]
    for k in range(0,len(r),2):
        i,c=int(r[k]),int(r[k+1]); p=mcost(i)
        if p is None: miss.append(items.get(i,('?',))[0]); continue
        tot+=p*c
    v,gn=de(ILVL[oid])
    if v is None or miss: res.append((None,name,gn,tot,v,miss,int(y))); continue
    res.append((v-tot,name,gn,tot,v,miss,int(y)))
def g(c): 
    c=int(round(c)); s='-' if c<0 else ''; c=abs(c); return f"{s}{c//10000}g {c//100%100}s {c%100}c" if c>=10000 else f"{s}{c//100}s {c%100}c" if c>=100 else f"{s}{c}c"
ok=sorted([x for x in res if x[0] is not None],key=lambda x:-x[0])
for p,n,gn,t,v,m,y in ok:
    print(f"{n:35s} Skill {y:3d} DE {gn:6s} Kosten {g(t):>12s} Entzaubern {g(v):>12s} Gewinn {g(p):>12s} {100*p/t:5.0f}%")
print('--- fehlende Preise:')
for x in res:
    if x[0] is None: print(x[1],x[2],x[5])
