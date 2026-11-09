"""Tests für shared/GoldSentinelGame.lua (läuft mit: python3 -I shared/tests/test_goldsentinelgame.py).
Prüft alle Spielversionen, geschützte Werte, Forever-Namen, Testmodus, "neueste Version gewinnt" und das
Zusammenspiel mit den frühen, zurückgenommenen Fassungen (variants/) in beiden Ladereihenfolgen."""
import sys
from pathlib import Path
from lupa.lua51 import LuaRuntime
HERE = Path(__file__).resolve().parent
src = (HERE.parent / 'GoldSentinelGame.lua').read_text(encoding='utf-8')
VAR_DIR = str(HERE / 'variants')
fails = 0
def run(label, setup, checks):
    global fails
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute("SlashCmdList = {}; DEFAULT_CHAT_FRAME = {AddMessage=function(self,m) LAST=m end}; function GetLocale() return 'deDE' end")
    lua.execute(setup)
    lua.execute(src)
    for expr, want in checks:
        got = lua.eval(expr)
        ok = got == want
        if not ok: fails += 1
        (None if ok and '-v' not in sys.argv else print(f"{'OK ' if ok else 'FEHLER'} [{label}] {expr} = {got!r}" + ("" if ok else f" (erwartet {want!r})")))
SECRET = """
local SECRET = setmetatable({}, {__tostring=function() error('secret!') end, __eq=function() error('secret!') end,
  __lt=function() error('secret!') end, __concat=function() error('secret!') end, __index=function() error('secret!') end})
S = SECRET
function issecretvalue(v) return rawequal(v, SECRET) end
"""
run("Classic Era", "function GetBuildInfo() return '1.15.9','70576','x',11509 end",
    [("GoldSentinelGame.flavor","era"),("GoldSentinelGame.IsModern",False),("GoldSentinelGame.IsOldAPI",True),
     ("GoldSentinelGame.HasSecrets",False),("GoldSentinelGame.IsSecret('x')",False),
     ("GoldSentinelGame.SameName('Testa','testa-Server')",True),("GoldSentinelGame.SameName('Testa','Testa Beispiel')",False),
     ("GoldSentinelGame.CleanName(' tes ta ')","Testa")])
run("Forever per TOC", SECRET + "function GetBuildInfo() return '1.60.1','70707','x',16001 end",
    [("GoldSentinelGame.flavor","forever"),("GoldSentinelGame.IsForever",True),("GoldSentinelGame.IsModern",True),
     ("GoldSentinelGame.IsOldAPI",False),("GoldSentinelGame.HasSecrets",True),
     ("GoldSentinelGame.IsSecret(S)",True),("GoldSentinelGame.IsSecret(5)",False),("GoldSentinelGame.AnySecret(1,nil,S)",True),
     ("GoldSentinelGame.AnySecret(1,2)",False),("GoldSentinelGame.Safe(S)",None),("GoldSentinelGame.Safe(7)",7),
     ("GoldSentinelGame.Short(S)",None),("GoldSentinelGame.SameName(S,'Testa')",False),("GoldSentinelGame.CleanName(S)",None),
     ("GoldSentinelGame.SameName('Testa','Testa Beispiel')",True),("GoldSentinelGame.SameName('testa beispiel-Server','Testa Beispiel')",True),
     ("GoldSentinelGame.SameName('Testa Beispiel','Testa Eisenfaust')",False),("GoldSentinelGame.SameName('Testa','Testaa')",False),
     ("GoldSentinelGame.CleanName('  testa   beispiel ')","Testa Beispiel")])
run("Forever per Projekt, TOC 16002", "WOW_PROJECT_ID=99; WOW_PROJECT_CAMELOT=99; function GetBuildInfo() return '1.60.2','1','x',16002 end",
    [("GoldSentinelGame.flavor","forever"),("GoldSentinelGame.IsModern",True)])
run("Retail", SECRET + "function GetBuildInfo() return '12.1.5','70688','x',120105 end",
    [("GoldSentinelGame.flavor","retail"),("GoldSentinelGame.IsModern",True),("GoldSentinelGame.SameName('Testa','Testa Beispiel')",False)])
run("TBC Anniversary", "function GetBuildInfo() return '2.5.6','1','x',20506 end",
    [("GoldSentinelGame.flavor","tbc"),("GoldSentinelGame.IsModern",False)])
run("Titan", "function GetBuildInfo() return '3.8.0','1','x',38002 end",
    [("GoldSentinelGame.flavor","titan"),("GoldSentinelGame.IsWrath",True)])
run("MoP", "function GetBuildInfo() return '5.5.4','1','x',50504 end", [("GoldSentinelGame.flavor","mists")])
run("Cata", "function GetBuildInfo() return '4.4.2','1','x',40402 end", [("GoldSentinelGame.flavor","cata")])
run("Testmodus", "function GetBuildInfo() return '1.15.9','1','x',11509 end",
    [("(function() GoldSentinelGame.SetTestFlavor('forever') return GoldSentinelGame.IsForever and GoldSentinelGame.IsModern end)()",True),
     ("(function() GoldSentinelGame.SetTestFlavor(nil) return GoldSentinelGame.flavor end)()","era")])
run("Neueste Version gewinnt", "GoldSentinelGame={version=5, marker='alt'}; function GetBuildInfo() return '1.15.9','1','x',11509 end",
    [("GoldSentinelGame.marker","alt"),("GoldSentinelGame.flavor",None)])
run("Ältere wird ersetzt", "GoldSentinelGame={version=0, marker='alt'}; function GetBuildInfo() return '1.60.1','1','x',16001 end",
    [("GoldSentinelGame.version",3),("GoldSentinelGame.flavor","forever")])
run("Status + Slash", "function GetBuildInfo() return '1.60.1','1','x',16001 end; WOW_PROJECT_ID=1",
    [("(function() SlashCmdList.GOLDSENTINELGAME() return LAST end)()",
      "|cffffb238GoldSentinel|r: Spielversion: WoW Forever (1.60.1, 16001) · API: modern (Kampf-Sperren) · Geschützte Werte: nein")])
run("ohne GetBuildInfo", "", [("GoldSentinelGame.flavor","unknown"),("GoldSentinelGame.toc",0)])

# ---------- Version 2: Ersatznamen ----------
run("V2 Ersatznamen Forever", SECRET + "function GetBuildInfo() return '1.60.1','70707','x',16001 end",
    [("GoldSentinelGame.version",3),("GoldSentinelGame.apiVersion",3),("GoldSentinelGame.interface",16001),
     ("GoldSentinelGame.IsClassic",False),("GoldSentinelGame.ProperName('testa  beispiel-Server')","Testa Beispiel"),
     ("GoldSentinelGame.ProperName('ömer')","ömer"),("GoldSentinelGame.ProperName(S)",None),
     ("GoldSentinelGame.ShortName(' Testa Beispiel-X ')","Testa Beispiel"),("GoldSentinelGame.NormName('Testa   BEISPIEL')","testa beispiel"),
     ("GoldSentinelGame.SameName('Testa','Testa Beispiel', function(v) return v=='testa' end)",True),
     ("GoldSentinelGame.SameName('Testa','Testa Beispiel', function(v) return false end)",False),
     ("GoldSentinelGame.SameName('Testa','Testa Beispiel', function(v) error('x') end)",False),
     ("GoldSentinelGame:Status() ~= nil",True)])
run("V2 IsClassic TBC", "function GetBuildInfo() return '2.5.6','1','x',20506 end", [("GoldSentinelGame.IsClassic",True)])
run("V2 IsClassic unbekannt", "", [("GoldSentinelGame.IsClassic",False)])

# ---------- frühe Fassungen: beide Ladereihenfolgen ----------
import glob, os
VAR = {'GuildSentinel 0.9.6 (CurseForge)': '%s/GuildSentinel-0.9.6.lua', 'ThreatSentinel 2.3.0': '%s/ThreatSentinel-2.3.0.lua',
       'ProfessionSentinel 0.9.3': '%s/ProfessionSentinel-0.9.3.lua', 'BuffSentinel 0.9.2': '%s/BuffSentinel-0.9.2.lua'}
def run_order(label, first, second, checks, env):
    global fails
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute("SlashCmdList = {}; DEFAULT_CHAT_FRAME = {AddMessage=function(self,m) LAST=m end}; function GetLocale() return 'deDE' end")
    lua.execute(env)
    try:
        lua.execute(first); lua.execute(second)
    except Exception as e:
        fails += 1; print(f"FEHLER [{label}] Lua-Fehler beim Laden: {e}"); return
    for expr, want in checks:
        try: got = lua.eval(expr)
        except Exception as e: got = f"LUA-FEHLER {e}"
        ok = got == want
        if not ok: fails += 1
        (None if ok and '-v' not in sys.argv else print(f"{'OK ' if ok else 'FEHLER'} [{label}] {expr} = {got!r}" + ("" if ok else f" (erwartet {want!r})")))
ENV = SECRET + "WOW_PROJECT_ID=99; WOW_PROJECT_CAMELOT=99; function GetBuildInfo() return '1.60.1','70707','x',16001 end"
COMPAT = [("GoldSentinelGame.version",3),("GoldSentinelGame.flavor","forever"),("GoldSentinelGame.IsModern",True),
          ("type(GoldSentinelGame.CleanName)","function"),("GoldSentinelGame.CleanName('testa beispiel')","Testa Beispiel"),
          ("GoldSentinelGame.SameName('Testa','Testa Beispiel')",True),("GoldSentinelGame.IsSecret(S)",True),
          ("GoldSentinelGame.AnySecret(1,S)",True),("GoldSentinelGame.InCombat()",False),
          ("type(GoldSentinelGame.ProperName)","function"),("type(GoldSentinelGame.ShortName)","function"),
          ("type(GoldSentinelGame.NormName)","function"),("GoldSentinelGame.interface",16001),("GoldSentinelGame:Status() ~= nil",True)]
for name, path in VAR.items():
    var = open(path % VAR_DIR, encoding='utf-8').read()
    run_order(f"{name} zuerst, dann V2", var, src, COMPAT, ENV)
    run_order(f"V2 zuerst, dann {name}", src, var, COMPAT, ENV)
R = lambda k: open(VAR[k] % VAR_DIR, encoding='utf-8').read()
run_order("GS 0.9.6, dann V2, dann TS/PS/BS", R('GuildSentinel 0.9.6 (CurseForge)'), src + "\n" + R('ThreatSentinel 2.3.0') + "\n" + R('ProfessionSentinel 0.9.3') + "\n" + R('BuffSentinel 0.9.2'), COMPAT, ENV)
run_order("TS 2.3.0, dann V2, dann GS/PS/BS", R('ThreatSentinel 2.3.0'), src + "\n" + R('GuildSentinel 0.9.6 (CurseForge)') + "\n" + R('ProfessionSentinel 0.9.3') + "\n" + R('BuffSentinel 0.9.2'), COMPAT, ENV)
run_order("V2 zuerst, dann alle vier frühen", src, R('ThreatSentinel 2.3.0') + "\n" + R('GuildSentinel 0.9.6 (CurseForge)') + "\n" + R('ProfessionSentinel 0.9.3') + "\n" + R('BuffSentinel 0.9.2'), COMPAT, ENV)
lua = LuaRuntime(unpack_returned_tuples=True); lua.execute("SlashCmdList = {}"); lua.execute(ENV)
try:
    lua.execute(R('ThreatSentinel 2.3.0') + "\n" + R('GuildSentinel 0.9.6 (CurseForge)')); print("INFO TS 2.3.0 + GS 0.9.6 ohne V2: kein Fehler")
except Exception as e: print("INFO GRENZE: TS 2.3.0 + GS 0.9.6 vertragen sich untereinander nicht (unabhängig von V2):", str(e)[:70])
# Gegenprobe: alte V1 (meine) nach TS 2.3.0 -> zeigt das Problem, das V2 löst
lua = LuaRuntime(unpack_returned_tuples=True); lua.execute("SlashCmdList = {}"); lua.execute(ENV)
lua.execute(open(VAR['ThreatSentinel 2.3.0'] % VAR_DIR).read())
try:
    lua.execute(open(VAR_DIR + '/GoldSentinelGame-v1.lua', encoding='utf-8').read()); print("INFO V1 nach TS 2.3.0: kein Fehler")
except Exception as e: print("INFO V1 nach TS 2.3.0 -> Lua-Fehler (wie vermutet):", str(e)[:90])
print(f"GoldSentinelGame-Tests: {'bestanden' if not fails else str(fails) + ' Fehler'}"); sys.exit(1 if fails else 0)
