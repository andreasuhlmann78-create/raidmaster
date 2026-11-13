import json, sys, statistics as st, collections, math
from datetime import datetime
from zoneinfo import ZoneInfo
Z=ZoneInfo("Europe/Zurich")
S=json.load(open(sys.argv[1]))
ser={int(k.rsplit("|",1)[1]):v for k,v in S.items()}
def resid(pts, win=12*3600):
    # Abweichung vom gleitenden Median ±12 Std. desselben Items (entfernt Trend und Welle)
    ts=[t for t,_,_ in pts]; ps=[p for _,p,_ in pts]
    out=[]; j0=0; j1=0; n=len(pts)
    for i,(t,p,q) in enumerate(pts):
        while ts[j0]<t-win: j0+=1
        while j1<n and ts[j1]<=t+win: j1+=1
        w=[x for x in ps[j0:j1] if x>0]
        if len(w)>=8 and p>0:
            out.append((t, math.log(p/st.median(w))))
    return out
items=[i for i,v in ser.items() if len(v)>=40]
acc=collections.defaultdict(list); half=collections.defaultdict(lambda: collections.defaultdict(list))
allt=sorted(t for i in items for t,_,_ in ser[i]); mid=allt[len(allt)//2]
for i in items:
    for t,r in resid(ser[i]):
        h=datetime.fromtimestamp(t,Z).hour
        acc[h].append(r); half[t<mid][h].append(r)
print("TAGESZYKLUS bereinigt (Abweichung vom gleitenden ±12-Std.-Median desselben Items):")
for h in sorted(acc):
    if len(acc[h])>=500: print(f"  {h:02d} Uhr: {(math.exp(st.mean(acc[h]))-1)*100:+5.1f} %  (n={len(acc[h])})")
ks=[h for h in acc if len(half[True][h])>=200 and len(half[False][h])>=200]
a=[st.mean(half[True][h]) for h in sorted(ks)]; b=[st.mean(half[False][h]) for h in sorted(ks)]
print(f"  Bestätigung erste/zweite Hälfte: Korrelation {st.correlation(a,b):+.2f}, gleiche Richtung {sum(1 for x,y in zip(a,b) if (x>0)==(y>0))}/{len(ks)}")
