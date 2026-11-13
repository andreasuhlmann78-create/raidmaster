"""TU9 – ThreatSentinel-Testroutine offline im nachgebauten Spiel der Addon-Prüfung (addon-check/ladetest.py).
Aufruf (aus dem raidmaster-Repo):
    mkdir -p /tmp/ts && unzip -o -q download/ThreatSentinel-<Version>.zip -d /tmp/ts
    python3 -I berichte/ThreatSentinel/offline/routine_offline.py /tmp/ts/ThreatSentinel Forever     # oder Era, dazu optional ein Bereich (a … k, u)
    python3 -I berichte/ThreatSentinel/offline/routine_offline.py download/ThreatSentinel-<Version>.zip Era
    python3 -I berichte/ThreatSentinel/offline/routine_offline.py                 # neueste download/ThreatSentinel-*.zip, Forever
Läuft dieselbe Routine wie /ts testroutine im Spiel, mit simulierten Kämpfen (Lagen als Zeitreihe, Zufallsfälle).
Die Nachbildung ist gutmütig (Frames ohne Rechtecke, kein echter Chat): Fälle, die nur im echten Client gehen, sind
SKIP/CLIENT; die Liste NACHBILDUNG unten nennt die Fälle, die in der Nachbildung aus bekannten Gründen FEHLER sind.
Ende: Zeile "Offline: FEHLER ausserhalb der Nachbildungs-Liste: n" und Rückgabewert 1, wenn n > 0.
Braucht Python 3 mit lupa (pip install lupa).
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..", "..", "addon-check")))
import ladetest as LT
from lupa.lua51 import LuaRuntime

# Argumente: [ZIP oder Ordner] [Forever|Era] [Bereich]. Ohne Quelle (oder mit Forever/Era als erstem Argument):
# die neueste download/ThreatSentinel-*.zip. Eine ZIP wird in einen leeren Arbeitsordner ausgepackt.
import glob, re as _re, tempfile, zipfile
args = sys.argv[1:]
src = None
if args and args[0] not in ("Forever", "Era"):
    src = args.pop(0)
if not src:
    def _ver(p):
        m = _re.search(r"ThreatSentinel-([\d.]+)\.zip$", p)
        return tuple(int(x) for x in m.group(1).split(".")) if m else ()
    zips = sorted(glob.glob(os.path.join(HERE, "..", "..", "..", "download", "ThreatSentinel-*.zip")), key=_ver)
    if not zips:
        sys.exit("keine download/ThreatSentinel-*.zip gefunden")
    src = zips[-1]
if src.lower().endswith(".zip"):
    work = tempfile.mkdtemp(prefix="ts-offline-")
    with zipfile.ZipFile(src) as z:
        z.extractall(work)
    folder = os.path.join(work, "ThreatSentinel")
    print("Quelle: " + os.path.basename(src))
else:
    folder = src
flavor = {"Forever": "WoW Forever", "Era": "Classic Era"}[args[0] if len(args) > 0 else "Forever"]
area = args[1] if len(args) > 1 else ""

toc = open(os.path.join(folder, "ThreatSentinel.toc"), encoding="utf-8").read()
files = [l.strip() for l in toc.splitlines() if l.strip().endswith(".lua")]

lua = LuaRuntime(unpack_returned_tuples=True)
lua.execute('GS_LOCALE = "deDE"')
lua.execute(LT.MOCK)
lua.execute(LT.FLAVOR_LUA[flavor])
g = lua.globals()
g.GS_OWN = lua.table_from({"ThreatSentinelDB": True})
g.GS_PREFIX = lua.table_from(["ThreatSentinel", "GoldSentinel", "Threat"])
lua.execute(LT.GLOBALS_GUARD.replace("local own, ownPrefix = ...", "local own, ownPrefix = GS_OWN, GS_PREFIX"))
# reichere Frames (nur lokal, für Plakettentests): Grösse, Ebene, Farbe, Animationen, Deckkraft
lua.execute("""
local MT = getmetatable(CreateFrame("Frame"))
local oldIndex = MT.__index
MT.__index = function(t, k)   -- eigene Felder (klein geschrieben) wie im Spiel: nil statt Attrappe
  if type(k) == "string" and k:match("^[a-z_]") and rawget(MT, k) == nil then return nil end
  return oldIndex(t, k)
end
function MT:SetScale(s) self._scale = s end
function MT:SetAttribute(k, v) local a = rawget(self, "_attr") or {}; rawset(self, "_attr", a); a[k] = v end
function MT:GetAttribute(k) local a = rawget(self, "_attr"); return a and a[k] end
function MT:SetShown(v) if v then self:Show() else self:Hide() end end
function MT:GetScale() return rawget(self, "_scale") or 1 end
function MT:SetFrameStrata(s) self._strata = s end
function MT:GetFrameStrata() return rawget(self, "_strata") or "MEDIUM" end
function MT:SetVertexColor(r, g, b, a) self._vc = { r, g, b, a } end
function MT:GetVertexColor() local v = rawget(self, "_vc") or { 1, 1, 1, 1 }; return v[1], v[2], v[3], v[4] end
function MT:SetStatusBarColor(r, g, b, a) self._sbc = { r, g, b, a } end
function MT:GetStatusBarColor() local v = rawget(self, "_sbc") or { 1, 1, 1, 1 }; return v[1], v[2], v[3], v[4] end
function MT:Play() self._playing = true end
function MT:Stop() self._playing = false end
function MT:IsPlaying() return rawget(self, "_playing") or false end
function MT:SetAlpha(a) self._alpha = a end
function MT:GetAlpha() return rawget(self, "_alpha") or 1 end
""")
# Zeitgeber: Warteschlange, die der Prüfstand abarbeitet
lua.execute("""
GS_QUEUE = {}
C_Timer = { After = function(d, fn) GS_QUEUE[#GS_QUEUE + 1] = fn end,
            NewTicker = function() return { Cancel = function() end } end,
            NewTimer = function(d, fn) GS_QUEUE[#GS_QUEUE + 1] = fn; return { Cancel = function() end } end }
""")
ns = lua.table()
for f in files:
    src = open(os.path.join(folder, f), encoding="utf-8").read()
    fn = lua.eval("function(src, name, ns) local f, e = loadstring(src, '@' .. name); if not f then error(e) end; return f('ThreatSentinel', ns) end")
    fn(src, f, ns)
lua.execute("""local ok, e = pcall(GS_Fire, 'ADDON_LOADED', 'ThreatSentinel'); if not ok then print('ADDON_LOADED: ' .. tostring(e)) end
local ok2, e2 = pcall(GS_Fire, 'PLAYER_LOGIN'); if not ok2 then print('PLAYER_LOGIN: ' .. tostring(e2)) end""")
g.TSNS = ns
out = lua.execute("""
local ns = TSNS
GoldSentinelDev.IsDev = function(self) assert(self == GoldSentinelDev, "IsDev ohne self"); return true end
GoldSentinelDev.Require = function() return true end
local printed = {}
ns.Print = function(_, m) printed[#printed + 1] = tostring(m) end
ns.Routine:Command(%r)
local guard = 0
while #GS_QUEUE > 0 and guard < 5000 do
  guard = guard + 1
  local fn = table.remove(GS_QUEUE, 1)
  local ok, e = pcall(fn)
  if not ok then printed[#printed + 1] = "QUEUE-FEHLER: " .. tostring(e) end
end
printed[#printed + 1] = "routineRunning=" .. tostring(ns.routineRunning) .. " actLog=" .. tostring(ns.actLog)
return (ns.Routine.lastText or "(kein Bericht)") .. "\\n----\\n" .. table.concat(printed, "\\n")
""" % area)
print(out)

# Fälle, die nur in der Nachbildung FEHLER sind (die Nachbildung kann das Spiel dort nicht nachstellen)
NACHBILDUNG = {
    "T02": "Version aus der .toc: GetAddOnMetadata liefert in der Nachbildung nichts",
    "T09": "Ereignis-Anmeldung: die Nachbildung meldet jedes Ereignis als angemeldet",
    "T20": "UnitIsUnit der Nachbildung vergleicht nicht wie das Spiel",
    "T34": "Positionen: Frames der Nachbildung merken keine Ankerpunkte",
    "T39": "UnitDetailedThreatSituation der Nachbildung liefert Werte ohne Ziel",
    "T76": "Ambiguate/Chat-Ereignis der Nachbildung",
    "T133": "Prefix-Anmeldung der Nachbildung",
    "TU6-R1": "Folge: T76 ist in der Nachbildung FEHLER",
}
import re
report = out.split("----")[0]
bad = []
for line in report.splitlines():
    m = re.match(r"\s*\[FEHLER\] (\S+)", line)
    if m and m.group(1) not in NACHBILDUNG:
        bad.append(line.strip())
for b in bad:
    print("AUSSERHALB: " + b)
print("Offline: FEHLER ausserhalb der Nachbildungs-Liste: %d" % len(bad))
sys.exit(1 if bad else 0)
