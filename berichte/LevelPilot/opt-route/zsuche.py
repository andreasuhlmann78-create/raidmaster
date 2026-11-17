#!/usr/bin/env python3
# OPT-ROUTE Stufe 2: Koordinatensuche über Zonen-Gewichte (P.ZONE_BIAS) je Fraktion, Bewertung = Zeit + 0,5 × Grinden
import subprocess, re, shutil, os, sys, json
S = os.path.dirname(os.path.abspath(__file__)); BASE = "/home/claude/lp31238/LevelPilot"
RACES = {"Horde": [("Orc WARRIOR Horde", "LVL=13 MAP=1413 PX=51.5 PY=30.3"), ("Tauren WARRIOR Horde", "LVL=6 MAP=1412 PX=45 PY=55"),
                   ("Scourge PRIEST Horde", "LVL=6 MAP=1420 PX=61 PY=52")],
         "Alliance": [("Human WARRIOR Alliance", "LVL=10 MAP=1429 PX=48 PY=42"), ("NightElf HUNTER Alliance", "LVL=6 MAP=1438 PX=56 PY=60"),
                      ("Dwarf WARRIOR Alliance", "LVL=6 MAP=1426 PX=46 PY=52")]}
fac = sys.argv[1]; zones = [int(z) for z in sys.argv[2].split(",")]; log = open(f"{S}/zsuche_{fac}.log", "a")
def evaluate(bias, tag):
    d = f"{S}/zs_{fac}"; shutil.rmtree(d, ignore_errors=True); shutil.copytree(BASE, d)
    with open(f"{d}/Planner.lua", "a") as f:
        f.write("\nP.ZONE_BIAS = {" + ",".join(f"[{k}]={v}" for k, v in sorted(bias.items())) + "}\n")
    procs = []
    for who, env in RACES[fac]:
        e = dict(os.environ, WORLDHOOK=f"{S}/sim/world_hook.lua", SIMDIR=f"{S}/sim", FOREVER="1", PACKDIR="/home/claude/lp31238/LevelPilot_Data")
        for kv in env.split(): k, v = kv.split("="); e[k] = v
        procs.append(subprocess.Popen(["timeout", "1500", "./lua51", "test26.lua", f"zs_{fac}", "0"] + who.split(), cwd=S, env=e,
                                      stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True))
    tot = 0.0; per = []
    for p in procs:
        out = p.communicate()[0]
        m = re.search(r"Spielzeit (\d+) h (\d+) min", out); g = re.search(r"Grinden (\d+) h", out)
        if not m or not g: per.append("FEHLER"); tot += 1e9; continue
        t = int(m.group(1)) + int(m.group(2)) / 60; tot += t + 0.5 * int(g.group(1)); per.append(f"{t:.1f}/{g.group(1)}")
    log.write(f"{tag} {json.dumps(bias)} -> {tot:.1f} [{' '.join(per)}]\n"); log.flush()
    return tot
bias = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
bias = {int(k): v for k, v in bias.items()}; best = evaluate(bias, "basis" if not bias else "fortsetzung")
for z in zones:
    for v in (0.5, 2.0):
        b = dict(bias); b[z] = v; s = evaluate(b, f"zone {z} x{v}")
        if s < best - 1.0: best, bias = s, b; log.write(f"  ANGENOMMEN {z} x{v}: {best:.1f}\n"); log.flush(); break
log.write(f"ENDE {fac} {json.dumps(bias)} {best:.1f}\n")
