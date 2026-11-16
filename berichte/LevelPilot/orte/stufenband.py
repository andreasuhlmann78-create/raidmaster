"""OPT-ROUTE 1b: Stufenband je Zone und Fraktion aus dem Datenpaket (Questgeber-Ort = Zone des ersten Fundorts des Startgebers).
Band = 20.–80. Perzentil der Questlevel (mind. 8 Quests). Aufruf: python3 stufenband.py <LevelPilot_Data/Data>"""
import re, sys, collections
d = sys.argv[1]
q = open(d + "/Quests.lua", encoding="utf-8").read()
n = open(d + "/Npcs.lua", encoding="utf-8").read()
npc = {}
for i, b in re.findall(r'^T\[(\d+)\]=(.*)$', n, re.M):
    m = re.search(r's=\{\{(\d+)', b); f = re.search(r'f="([AH]*)"', b)
    if m: npc[int(i)] = (int(m.group(1)), f.group(1) if f else "AH")
zones = collections.defaultdict(lambda: {"A": [], "H": []})
for i, b in re.findall(r'^T\[(\d+)\]=\{(.*)\}$', q, re.M):
    l = re.search(r'\bl=(\d+)', b); sn = re.search(r'\bsn=\{(\d+)', b)
    if not (l and sn): continue
    z = npc.get(int(sn.group(1)))
    if not z: continue
    for fac in "AH":
        if fac in z[1]: zones[z[0]][fac].append(int(l.group(1)))
def band(v):
    v = sorted(v)
    if len(v) < 8: return None
    return v[len(v) // 5], v[len(v) * 4 // 5], len(v)
for fac in "AH":
    rows = sorted((band(z[fac]), m) for m, z in zones.items() if band(z[fac]))
    print(fac, " ".join(f"{m}:{b[0]}-{b[1]}({b[2]})" for b, m in rows))
