import json, sys, statistics as st, collections, math
from datetime import datetime
from zoneinfo import ZoneInfo
Z=ZoneInfo("Europe/Zurich")
S=json.load(open(sys.argv[1]))
ser={int(k.rsplit("|",1)[1]):v for k,v in S.items()}
BANDS={ "05–20 (Seltsamer Staub)":[10940,10938,10939,10978],
        "21–30 (Seelenstaub)":[11083,10998,11082,11084],
        "31–40 (Visionenstaub)":[11137,11134,11135,11138,11139],
        "41–50 (Traumstaub)":[11176,11174,11175,11177,11178],
        "51–60 (Illusionsstaub)":[16204,16202,16203,14343,14344]}
def daymed(pts):
    d=collections.defaultdict(list)
    for t,p,q in pts: d[datetime.fromtimestamp(t,Z).date()].append(p)
    return {k:st.median(v) for k,v in d.items()}
print("== 1. WELLEN je Band (Tagesmedian Mindestpreis, Index = Tag / erster Tag, Mittel über die Materialien) ==")
days_all=sorted({datetime.fromtimestamp(t,Z).date() for v in ser.values() for t,_,_ in v})
for band,ids in BANDS.items():
    per=[]
    for i in ids:
        if i in ser:
            dm=daymed(ser[i])
            if len(dm)>=5: per.append(dm)
    if not per: print(f"  {band}: keine Daten"); continue
    row=[]
    for d in days_all:
        vals=[]
        for dm in per:
            ks=sorted(dm); base=dm[ks[0]]
            if d in dm and base>0: vals.append(dm[d]/base)
        row.append(f"{st.mean(vals):.2f}" if vals else " -- ")
    print(f"  {band:<24} n={len(per)} :", " ".join(row))
print("  Tage:", " ".join(d.strftime('%d.') for d in days_all))
# 2. Tageszyklus: relativer Preis zum Tagesmedian des Items, nach Stunde
def cyc(keyf, items, minpts=20):
    acc=collections.defaultdict(list)
    for i in items:
        pts=ser[i]
        if len(pts)<minpts: continue
        dm=daymed(pts)
        for t,p,q in pts:
            dt=datetime.fromtimestamp(t,Z); m=dm[dt.date()]
            if m>0 and p>0: acc[keyf(dt)].append(math.log(p/m))
    return {k:(math.exp(st.mean(v))-1, len(v)) for k,v in acc.items()}
items=[i for i,v in ser.items() if len(v)>=40]
print(f"\n== 2. TAGESZYKLUS (Preis relativ zum Tagesmedian desselben Items; {len(items)} Items mit ≥ 40 Punkten) ==")
h=cyc(lambda d:d.hour, items)
for k in sorted(h): print(f"  {k:02d} Uhr: {h[k][0]*100:+5.1f} %  (n={h[k][1]})")
# Bestätigung: erste Hälfte der Tage vs. zweite Hälfte
mid=days_all[len(days_all)//2]
def cyc_part(sel):
    acc=collections.defaultdict(list)
    for i in items:
        pts=[x for x in ser[i] if sel(datetime.fromtimestamp(x[0],Z).date())]
        if len(pts)<10: continue
        dm=daymed(pts)
        for t,p,q in pts:
            dt=datetime.fromtimestamp(t,Z); m=dm[dt.date()]
            if m>0 and p>0: acc[dt.hour].append(math.log(p/m))
    return {k:st.mean(v) for k,v in acc.items() if len(v)>=200}
A=cyc_part(lambda d:d<mid); B=cyc_part(lambda d:d>=mid)
ks=sorted(set(A)&set(B))
if len(ks)>3:
    xa=[A[k] for k in ks]; xb=[B[k] for k in ks]
    r=st.correlation(xa,xb)
    same=sum(1 for k in ks if (A[k]>0)==(B[k]>0))
    print(f"  Bestätigung erste/zweite Hälfte ({len(ks)} Stunden): Korrelation {r:+.2f}, gleiche Richtung {same}/{len(ks)}")
print("\n== 3. WOCHENZYKLUS (Tagesmedian je Item relativ zum Item-Median über alle Tage, nach Wochentag) ==")
acc=collections.defaultdict(list); nd=collections.Counter()
for i in items:
    dm=daymed(ser[i])
    if len(dm)<6: continue
    med=st.median(dm.values())
    for d,v in dm.items():
        if med>0 and v>0: acc[d.weekday()].append(math.log(v/med))
for d in days_all: nd[d.weekday()]+=1
names=["Mo","Di","Mi","Do","Fr","Sa","So"]
for k in sorted(acc): print(f"  {names[k]}: {(math.exp(st.mean(acc[k]))-1)*100:+5.1f} %  (Kalendertage im Datensatz: {nd[k]})")
