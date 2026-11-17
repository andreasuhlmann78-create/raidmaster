import sys,re,collections
R=collections.defaultdict(dict)
for l in open(sys.argv[1]):
    m=re.match(r"(\S+) ([TG]) (\S+ \S+ \S+):.*?Spielzeit (\d+) h (\d+) min.*Grinden (\d+) h",l)
    if m: R[m.group(1)][(m.group(2),m.group(3))]=int(m.group(4))+int(m.group(5))/60+0.5*int(m.group(6))
for d,v in R.items():
    t=sum(x for (g,_),x in v.items() if g=="T"); g=sum(x for (gg,_),x in v.items() if gg=="G")
    print(f"{d}: Läufe {len(v)} Training {t:.1f} Gegenprobe {g:.1f} Summe {t+g:.1f}")
