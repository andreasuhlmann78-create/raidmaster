"""Test: Austausch mit dem MARKT-KERN (kern_daten.py) – nur erfundene Daten. Aufruf: python3 -I addon-check/marktanalyse/test_kern_daten.py"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import kern_daten as kd  # noqa: E402
from lupa.lua51 import LuaRuntime  # noqa: E402

ok = fail = 0


def check(name, cond):
    global ok, fail
    if cond:
        ok += 1
    else:
        fail += 1
        print("FEHLT:", name)


D = 86400
T = 1794700800                                   # ein Tagesbeginn
lua = LuaRuntime(unpack_returned_tuples=True)
lua.execute(f"""
DB = {{ kern = {{ v = 1, c = {{
  markt = {{ ["misc:3"] = {{ [{T}] = {{ 100, 5 }}, [{T - 20 * D}] = {{ 40, 4 }}, [{T - 40 * D}] = {{ 1000, 1000 }} }},
             ["de:1"] = {{ [{T}] = {{ 10, 9 }} }} }},
  sell = {{ ["de:3"] = {{ [{T}] = {{ 50, 25 }} }} }},
  buyk = {{ b1 = {{ [{T}] = {{ 5, 5000 }} }} }} }},
  e = {{ markt = {{ [{T}] = {{ 140, 3.0, 4.0, 130, 131, 0, 0, 0 }} }},
         sell = {{ [{T}] = {{ 50, 9.0, 12.0, 30, 31, 0, 0, 0 }} }} }} }} }}
SCHLECHT = {{ kern = {{ v = 1, c = {{ markt = {{ x = {{ [{T}] = {{ 100, 50 }} }} }} }},
  e = {{ markt = {{ [{T}] = {{ 100, 30.0, 25.0, 50, 50, 0, 0, 0 }} }} }} }} }}
WENIG = {{ kern = {{ v = 1, c = {{ markt = {{ x = {{ [{T}] = {{ 10, 5 }} }} }} }}, e = {{ markt = {{ [{T}] = {{ 10, 1.0, 2.0, 5, 5, 0, 0, 0 }} }} }} }} }}
""")
G = lua.globals()
k = kd.kern_of(G.DB)
check("neuester Tag", kd.newest_day(k) == T)
n, y = kd.counts(k, "markt", "misc:3", T)
check("Gewicht L4: heute 1, 20 Tage 0,5, 40 Tage 0 -> n 120, y 7", (n, y) == (120.0, 7.0))
okS, why, r = kd.show(k, "markt", T)
check("K:Show wie Addon seit 0.65.256: Brier besser -> P2 trotz Treffer 130 < 131 (KERN-P2-1)", okS and why == "zeigen")
okF, whyF, _ = kd.show(k, "markt", T, T - 30 * kd.DAY)
check("K:Fallback: 7 Tage bewertet, Brier in 7 Tagen besser -> kein Rückfall", okF)
lua.execute(f"""SCHLECHT7 = {{ kern = {{ v = 1, c = {{ markt = {{ x = {{ [{T}] = {{ 100, 50 }} }} }} }},
  e = {{ markt = {{ [{T}] = {{ 100, 30.0, 25.0, 50, 50, 0, 0, 0 }} }} }} }} }}""")
k7 = kd.kern_of(G.SCHLECHT7)
okR, whyR, _ = kd.show(k7, "markt", T, T - 30 * kd.DAY)
check("K:Fallback: 7 Tage bewertet und Brier schlechter -> Rückfall", (not okR) and whyR.startswith("Rückfall"))
okR2, whyR2, _ = kd.show(k7, "markt", T, T - 2 * kd.DAY)
check("K:Fallback: erst 3 Tage bewertet -> kein Rückfall, nur 'schlägt die Grundlinie nicht'", whyR2 == "schlägt die Grundlinie nicht")
okU, whyU = kd.useful(k, "markt", T)
check("Regel Prüf-Sitzung: Brier 0,0214 < 0,0286 -> weitergeben", okU)
part, info = kd.kern_teil([G.DB])
check("Teil kern: nur markt (sell nie, buy nie)", set(part) == {"markt"})
check("Zelle misc:3 p = 7/120, n 120", part["markt"]["misc:3"] == {"p": round(7 / 120, 4), "n": 120})
check("Zelle de:1 mit n 10 < 30 weggelassen", "de:1" not in part["markt"])
p2, i2 = kd.kern_teil([G.SCHLECHT])
check("Brier schlechter als Grundlinie -> nichts weitergegeben", p2 is None and "nicht besser" in i2["wege"]["markt"])
p3, i3 = kd.kern_teil([G.WENIG])
check("n < 30 -> lernt noch, nichts weitergegeben", p3 is None and "lernt noch" in i3["wege"]["markt"])
p4, i4 = kd.kern_teil([G.DB, G.DB])
check("zwei Quellen summiert (n 240)", p4["markt"]["misc:3"]["n"] == 240 and i4["quellen"] == 2)
check("ohne Kern-Daten -> None, 0 Quellen", kd.kern_teil([lua.eval("{}")]) == (None, {"quellen": 0, "wege": {}}))
lo, hi = kd.wilson(5, 10)
check("Wilson 5/10 ≈ 0,237–0,763", abs(lo - 0.2366) < 0.001 and abs(hi - 0.7634) < 0.001)
# Lua-Form: so liest Kern.lua K:TableCell
import markt_tabellen as mt  # noqa: E402
text = "T = " + mt.lua_val({"v": 1, "kern": part})
lua.execute(text)
c = lua.globals().T.kern.markt["misc:3"]
check("in Lua lesbar wie K:TableCell (p Zahl, n > 0)", abs(c.p - 7 / 120) < 1e-4 and c.n == 120)
# Stände zusammenführen: gleiche Sicherung doppelt -> Kern nur einmal; Journal ohne Doppelte, Vielfachheit bleibt
lua.execute(f"""
A1 = {{ kern = {{ v = 1, since = 5, c = {{}}, e = {{}} }}, forecast = {{ list = {{ "P;100;7;1;1;50;1;2;;;;;;0.5;;;;;de;e;0", "P;100;7;1;1;50;1;2;;;;;;0.5;;;;;de;e;0", "B;90;8;1;40" }} }} }}
A2 = {{ kern = {{ v = 1, since = 5, c = {{ markt = {{ x = {{ [{T}] = {{ 1, 0 }} }} }} }}, e = {{}} }},
       forecast = {{ list = {{ "P;100;7;1;1;50;1;2;;;;;;0.5;;;;;de;s;1", "P;100;7;1;1;50;1;2;;;;;;0.5;;;;;de;e;0", "P;200;9;1;1;60;1;2;;;;;;0.5;;;;;de;s;1" }} }} }}
""")
ns = kd.newest_stores([G.A1, G.A2])
check("newest_stores: gleicher Speicher (since) nur der neueste", len(ns) == 1 and kd.newest_day(kd.kern_of(ns[0])) == T)
# Gleichstand am Kern-Tag: der Stand mit dem jüngeren Journal gewinnt, egal in welcher Reihenfolge (Befund 16.11. 14:40)
lua.execute(f"""
B1 = {{ kern = {{ v = 1, since = 7, c = {{ markt = {{ x = {{ [{T}] = {{ 1, 0 }} }} }} }}, e = {{}} }}, forecast = {{ list = {{ "P;100;7;1" }} }}, alt = 1 }}
B2 = {{ kern = {{ v = 1, since = 7, c = {{ markt = {{ x = {{ [{T}] = {{ 1, 0 }} }} }} }}, e = {{}} }}, forecast = {{ list = {{ "P;300;7;1" }} }}, neu = 1 }}
""")
check("newest_stores: Gleichstand am Tag -> jüngeres Journal (B2 vor B1)", kd.newest_stores([G.B1, G.B2])[0].neu == 1)
check("newest_stores: Gleichstand am Tag -> jüngeres Journal (B1 vor B2 umgekehrt)", kd.newest_stores([G.B2, G.B1])[0].neu == 1)
J = mt.merge_journals([G.A1, G.A2]).forecast.list
vals = [J[i] for i in range(1, len(J) + 1)]
check("Journal: Schlüssel aus dem neuesten Stand (2 Vorkommen, neuestes Ergebnis), B aus altem Stand ergänzt, nichts doppelt",
      len(vals) == 4 and sum(1 for v in vals if v.startswith("P;100;")) == 2 and any(v.endswith("de;s;1") and v.startswith("P;100") for v in vals)
      and any(v.startswith("B;90") for v in vals) and any(v.startswith("P;200") for v in vals))
print(f"{ok}/{ok + fail} Prüfungen bestanden")
sys.exit(1 if fail else 0)
