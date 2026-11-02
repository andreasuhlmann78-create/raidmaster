"""Unit test for GoldSentinelGame.lua: every game version, project constants, secret values, newest copy wins.

    python3 -I shared/test_gamelib.py
"""
import os, sys
import lupa.luajit21 as L

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = open(os.path.join(HERE, "GoldSentinelGame.lua"), encoding="utf-8").read()

def load(interface, project=None, secrets=False, pre=""):
    lua = L.LuaRuntime(unpack_returned_tuples=True)
    lua.execute("""
        SlashCmdList = {}
        GetBuildInfo = function() return "x.y.z", "12345", "Oct 1 2026", %d end
    """ % interface)
    if project:
        lua.execute("WOW_PROJECT_%s = 13; WOW_PROJECT_ID = 13" % project)
    if secrets:
        lua.execute("issecretvalue = function(v) return v == 'SECRET' end")
    if pre:
        lua.execute(pre)
    lua.eval("load")(SRC, "GoldSentinelGame")()
    return lua, lua.globals().GoldSentinelGame

fails = 0
def check(name, cond):
    global fails
    print(("OK   " if cond else "FAIL ") + name)
    if not cond: fails += 1

cases = [(11508, None, "era"), (11509, None, "era"), (11404, None, "era"), (16001, None, "forever"), (16002, None, "forever"),
         (17000, None, "forever"), (20505, None, "tbc"), (30405, None, "wrath"), (40402, None, "cata"), (50504, None, "mists"),
         (120105, None, "retail"), (0, "CAMELOT", "forever"), (0, "MAINLINE", "retail"), (99999, None, None)]
for i, p, want in cases:
    _, G = load(i, p)
    check(f"{i} {p or ''} -> {want}", G.flavor == want)
_, G = load(16001)
check("Forever: modern, not classic", G.IsForever and G.IsModern and not G.IsClassic)
_, G = load(11509)
check("Era: classic, not modern", G.IsEra and G.IsClassic and not G.IsModern and not G.IsForever)
_, G = load(120105)
check("Retail: modern", G.IsRetail and G.IsModern)
lua, G = load(16001, secrets=True)
check("IsSecret / Safe with issecretvalue", G.IsSecret("SECRET") and not G.IsSecret(5) and G.Safe("SECRET") is None and G.Safe(5) == 5)
lua, G = load(11509)
check("IsSecret without issecretvalue = false", G.IsSecret("SECRET") is False and G.Safe(7) == 7)
lua.execute("issecretvalue = function() error('boom') end")
check("IsSecret never raises", G.IsSecret(1) is False)
_, G = load(16001, pre="GoldSentinelGame = { version = 99, flavor = 'newer' }")
check("newer copy already loaded wins", G.flavor == "newer")
_, G = load(16001, pre="GoldSentinelGame = { version = 0, flavor = 'old' }")
check("older copy is replaced", G.flavor == "forever" and G.version == 1)
check("status text", "forever" in G.Status(G) and "16001" in G.Status(G))
print("GAMELIB OK" if not fails else f"GAMELIB {fails} FAILURES")
sys.exit(1 if fails else 0)
