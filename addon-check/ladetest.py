"""Ladetest: jede Addon-ZIP einmal wirklich laden – in einem nachgebauten WoW (Lua 5.1 über lupa).

Entstanden am 3. November 2026: ThreatSentinel 2.4.1–2.4.3 lud im Spiel überhaupt nicht (Core.lua rief ns:On auf, bevor
die Funktion definiert war). Die Syntaxprüfung sah das nicht, weil der Code gültig war – er scheiterte erst beim Ausführen.

Ablauf je Addon-Ordner in der ZIP und je Client (WoW Forever 16001 und Classic Era 11508, soweit die .toc ihn nennt):
  1. die passende .toc wählen (Name_Camelot.toc für Forever, Name_Vanilla.toc für Era, sonst Name.toc),
  2. alle Dateien in der Reihenfolge der .toc laden (.xml: <Script file> und <Include file> in ihrer Reihenfolge),
     jede mit (Addon-Name, Namensraum) wie im Spiel,
  3. ADDON_LOADED, PLAYER_LOGIN und PLAYER_ENTERING_WORLD auslösen.

Die Nachbildung ist bewusst gutmütig: Jede unbekannte Blizzard-Funktion oder -Tabelle ist ein harmloser Platzhalter,
damit fehlende Teile der Nachbildung keinen Alarm auslösen. Darum gilt:
  * Fehler beim LADEN mit "(a nil value)" -> FEHLER. Ein nil kann hier nur aus dem Addon selbst kommen (eigene Tabelle,
    eigene Funktion noch nicht definiert, eigener globaler Name). Genau das bricht das Addon im Spiel.
  * andere Fehler beim Laden und alle Fehler in den Start-Ereignissen -> WARNUNG (kann an der Nachbildung liegen;
    bitte ansehen).
Ohne lupa wird der Ladetest übersprungen (der Discord-Bot hat lupa nicht immer).
"""
import re
import zipfile

LOAD_FLAVORS = [
    # Name, Interface für GetBuildInfo, Bereich in der .toc, Suffixe der passenden .toc
    ("WoW Forever", 16001, (16000, 19999), ("_Camelot", "_Forever")),
    ("Classic Era", 11508, (10000, 15999), ("_Vanilla", "_Classic", "_Era")),
]

MOCK = r"""
local rawget, rawset, setmetatable, type, tostring = rawget, rawset, setmetatable, type, tostring

-- Platzhalter: jedes Feld wieder ein Platzhalter, aufrufbar, rechnet und verkettet ohne Fehler
local DummyMT = {}
local function Dummy() return setmetatable({}, DummyMT) end
local function zero() return 0 end
local function no() return false end
local NUMERIC = { "Num", "Count", "Width", "Height", "Size", "Scale", "Level", "Time", "Alpha", "Left", "Right",
                  "Top", "Bottom", "Value", "Max", "Min", "Offset", "Duration", "Cooldown", "Index", "ID" }
DummyMT.__index = function(t, k)
  if type(k) == "string" then
    -- Abfragen geben im Spiel Zahlen bzw. ja/nein zurück: so bleibt "x() or 0", math.max(x(), …) und for 1, x() gültig
    if k:match("^Is") or k:match("^Has") or k:match("^Can") or k:match("^Should") then return no end
    if k:match("^Get") then
      for _, w in ipairs(NUMERIC) do if k:find(w, 1, true) then return zero end end
    end
  end
  local d = Dummy(); rawset(t, k, d); return d
end
DummyMT.__call = function() return Dummy() end
DummyMT.__concat = function(a, b) return tostring(type(a) == "table" and "" or a) .. tostring(type(b) == "table" and "" or b) end
DummyMT.__tostring = function() return "" end
DummyMT.__add = function() return 0 end; DummyMT.__sub = DummyMT.__add; DummyMT.__mul = DummyMT.__add
DummyMT.__div = DummyMT.__add; DummyMT.__mod = DummyMT.__add; DummyMT.__unm = DummyMT.__add
DummyMT.__lt = function() return false end; DummyMT.__le = DummyMT.__lt
DummyMT.__len = function() return 0 end
GS_Dummy = Dummy

-- Frames mit echtem Zustand für die häufigen Methoden, alles andere Platzhalter
GS_FRAMES = {}
local FrameMT = {}
FrameMT.__index = function(t, k)
  local m = rawget(FrameMT, k)
  if m ~= nil then return m end
  return Dummy()
end
function FrameMT:RegisterEvent(e) self._events[e] = true end
function FrameMT:RegisterUnitEvent(e) self._events[e] = true end
function FrameMT:UnregisterEvent(e) self._events[e] = nil end
function FrameMT:UnregisterAllEvents() self._events = {} end
function FrameMT:IsEventRegistered(e) return self._events[e] == true end
function FrameMT:SetScript(s, fn) self._scripts[s] = fn end
function FrameMT:GetScript(s) return self._scripts[s] end
function FrameMT:HookScript(s, fn) local old = self._scripts[s]; self._scripts[s] = function(...) if old then old(...) end return fn(...) end end
function FrameMT:Show() self._shown = true end
function FrameMT:Hide() self._shown = false end
function FrameMT:IsShown() return self._shown end
function FrameMT:IsVisible() return self._shown end
function FrameMT:GetName() return self._name end
function FrameMT:GetParent() return self._parent end
function FrameMT:GetPoint() return "CENTER", nil, "CENTER", 0, 0 end
function FrameMT:GetWidth() return 100 end
function FrameMT:GetHeight() return 100 end
function FrameMT:GetSize() return 100, 100 end
function FrameMT:GetScale() return 1 end
function FrameMT:GetEffectiveScale() return 1 end
function FrameMT:GetChecked() return false end
function FrameMT:GetText() return self._text or "" end
function FrameMT:SetText(t) self._text = t end
function FrameMT:GetValue() return 0 end
function FrameMT:GetNumPoints() return 1 end
function FrameMT:GetObjectType() return self._kind or "Frame" end
function FrameMT:IsObjectType(k) return k == (self._kind or "Frame") end
function FrameMT:GetChildren() return end
function FrameMT:GetRegions() return end
function FrameMT:GetFrameLevel() return 1 end
function FrameMT:GetStringWidth() return 50 end
function FrameMT:GetLeft() return 0 end
function FrameMT:GetTop() return 0 end
function FrameMT:GetRight() return 100 end
function FrameMT:GetBottom() return 0 end
function FrameMT:GetCenter() return 50, 50 end
function FrameMT:IsMouseOver() return false end
function FrameMT:IsProtected() return false end
function FrameMT:IsForbidden() return false end
function FrameMT:GetAttribute() return nil end
function FrameMT:CreateFontString(n) return CreateFrame("FontString", n) end
function FrameMT:CreateTexture(n) return CreateFrame("Texture", n) end
function FrameMT:CreateAnimationGroup() return CreateFrame("AnimationGroup") end
function FrameMT:CreateAnimation() return CreateFrame("Animation") end
function FrameMT:CreateLine() return CreateFrame("Line") end
function FrameMT:CreateMaskTexture() return CreateFrame("Texture") end

function CreateFrame(kind, name, parent, template)
  local f = setmetatable({ _events = {}, _scripts = {}, _shown = true, _kind = kind, _parent = parent }, FrameMT)
  if type(name) == "string" then
    name = name:gsub("%$parent", type(parent) == "table" and (parent._name or "") or "")
    f._name = name
    rawset(_G, name, f)
  end
  f.Text = setmetatable({ _events = {}, _scripts = {} }, FrameMT)
  GS_FRAMES[#GS_FRAMES + 1] = f
  return f
end
function GS_Fire(ev, ...)
  for _, f in ipairs(GS_FRAMES) do
    local h = f._events[ev] and f._scripts.OnEvent
    if h then h(f, ev, ...) end
  end
end

print = function() end            -- Ausgaben der Addons nicht in den Prüfbericht
-- WoW-Lua-Zusätze
function strsplit(sep, s, n)
  s = tostring(s or ""); local out, i = {}, 1
  while true do
    local a, b = s:find(sep, i, true)
    if not a or (n and #out >= n - 1) then out[#out + 1] = s:sub(i); break end
    out[#out + 1] = s:sub(i, a - 1); i = b + 1
  end
  return unpack(out)
end
function strtrim(s, c) return (tostring(s or ""):gsub("^%s+", ""):gsub("%s+$", "")) end
function strjoin(sep, ...) return table.concat({...}, sep) end
function wipe(t) for k in pairs(t) do t[k] = nil end return t end
table.wipe = wipe
tinsert, tremove, tsort, tconcat = table.insert, table.remove, table.sort, table.concat
format, strlen, strsub, strfind, strmatch, strlower, strupper, strrep, strbyte, strchar, gsub, gmatch =
  string.format, string.len, string.sub, string.find, string.match, string.lower, string.upper, string.rep,
  string.byte, string.char, string.gsub, string.gmatch
string.trim = strtrim; string.split = function(s, sep) return strsplit(sep, s) end
floor, ceil, abs, min, max, sqrt, random, mod = math.floor, math.ceil, math.abs, math.min, math.max, math.sqrt, math.random, math.fmod
math.huge = math.huge or 1/0
bit = bit or { band = function(a, b) return 0 end, bor = function(a, b) return a end, bxor = function(a) return a end,
               lshift = function(a) return a end, rshift = function(a) return a end }
time, date = os.time, os.date
function GetTime() return 1000 end
function GetServerTime() return 1793750400 end
function GetTimePreciseSec() return 1000 end
function debugprofilestop() return 0 end
function debugstack() return "" end
function debuglocals() return "" end
local handler = function() end
function geterrorhandler() return handler end
function seterrorhandler(f) handler = f end
function issecure() return false end
function securecall(f, ...) if type(f) == "function" then return f(...) end end
function hooksecurefunc(a, b, c)
  local t, name, fn = _G, a, b
  if type(a) == "table" then t, name, fn = a, b, c end
  local old = t[name]
  if type(old) == "function" then t[name] = function(...) local r = { old(...) }; fn(...); return unpack(r) end end
end
function InCombatLockdown() return false end
function UnitAffectingCombat() return false end
function GetLocale() return "deDE" end
function UnitName(u) return "Tester", nil end
function UnitFullName(u) return "Tester", "Realm" end
function GetRealmName() return "Realm" end
function GetNormalizedRealmName() return "Realm" end
function UnitClass() return "Krieger", "WARRIOR", 1 end
function UnitRace() return "Ork", "Orc", 2 end
function UnitLevel() return 20 end
function UnitFactionGroup() return "Horde", "Horde" end
function UnitGUID() return "Player-1-00000001" end
function UnitExists(u) return u == "player" end
function UnitIsPlayer(u) return u == "player" end
function UnitHealth() return 100 end
function UnitHealthMax() return 100 end
function UnitPower() return 100 end
function UnitPowerMax() return 100 end
function GetNumGroupMembers() return 0 end
function GetNumSubgroupMembers() return 0 end
function IsInGroup() return false end
function IsInRaid() return false end
function IsInGuild() return false end
function IsInInstance() return false, "none" end
function GetMoney() return 0 end
function GetCVar() return "0" end
function GetCVarBool() return false end
function GetScreenWidth() return 1920 end
function GetScreenHeight() return 1080 end
function GetFramerate() return 60 end
function GetNumAddOns() return 0 end
function GetAddOnInfo() return nil end
function IsLoggedIn() return false end
function GetCurrentRegion() return 3 end
function GetSpecialization() return nil end
function GetNumTalentTabs() return 0 end
function GetCursorPosition() return 0, 0 end
function GetZoneText() return "" end
function GetRealZoneText() return "" end
function GetSubZoneText() return "" end
function GetMinimapZoneText() return "" end
function GetInstanceInfo() return "", "none", 0, "", 0, 0, false, 0, 0 end
function GetItemInfo() return nil end
function GetItemCount() return 0 end
function IsShiftKeyDown() return false end
function IsControlKeyDown() return false end
function IsAltKeyDown() return false end
UIParent = CreateFrame("Frame", "UIParent"); WorldFrame = CreateFrame("Frame", "WorldFrame")
UISpecialFrames = {}; SlashCmdList = {}; StaticPopupDialogs = {}
RAID_CLASS_COLORS = setmetatable({}, { __index = function() return { r = 1, g = 1, b = 1, colorStr = "ffffffff", GenerateHexColor = function() return "ffffffff" end, WrapTextInColorCode = function(_, s) return s end } end })
DEFAULT_CHAT_FRAME = CreateFrame("Frame", "DEFAULT_CHAT_FRAME")
NUM_BAG_SLOTS = 4; MAX_PARTY_MEMBERS = 4; MAX_RAID_MEMBERS = 40; NUM_CHAT_WINDOWS = 10
"""

FLAVOR_LUA = {
    "WoW Forever": r"""
function GetBuildInfo() return "1.60.1", "70753", "Nov 3 2026", 16001 end
WOW_PROJECT_CAMELOT = 99; WOW_PROJECT_ID = 99; WOW_PROJECT_MAINLINE = 1; WOW_PROJECT_CLASSIC = 2
function issecretvalue(v) return false end
""",
    "Classic Era": r"""
function GetBuildInfo() return "1.15.8", "65000", "Oct 1 2026", 11508 end
WOW_PROJECT_ID = 2; WOW_PROJECT_CLASSIC = 2; WOW_PROJECT_MAINLINE = 1
""",
}

# Globale Namen, die ein Platzhalter sein dürfen: sieht aus wie Blizzard (Grossbuchstabe, C_, Enum …) und ist kein
# Name des Addons selbst. Eigene Globals (SavedVariables, Namen mit dem Addon-Namen) bleiben nil wie im Spiel.
GLOBALS_GUARD = r"""
local own, ownPrefix = ...
setmetatable(_G, { __index = function(t, k)
  if type(k) ~= "string" or own[k] then return nil end
  for _, p in ipairs(ownPrefix) do if k:sub(1, #p):lower() == p:lower() then return nil end end
  if k:match("^[A-Z]") or k:match("^C_") then
    -- globale Abfragen wie bei Tabellenfeldern: Is…/Has…/Can… = nein, Get…Num…/…Count… = 0
    local probe = GS_Dummy()[k]
    if type(probe) == "function" then rawset(t, k, probe); return probe end
    local d = GS_Dummy(); rawset(t, k, d); return d
  end
  return nil
end })
"""

RUNNER = r"""
return function(src, file, addon, ns)
  local f, err = loadstring(src, "@" .. file)
  if not f then return false, err end
  local count = 0
  debug.sethook(function() count = count + 1; if count > 400 then error("Ladetest: Zeitlimit (Endlosschleife?)") end end, "", 1000000)
  local ok, e = pcall(f, addon, ns)
  debug.sethook()
  return ok, e
end
"""


def _parse_toc(text):
    meta, files = {}, []
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("##"):
            m = re.match(r"##\s*([\w-]+)\s*:\s*(.*)", s)
            if m:
                meta[m.group(1)] = m.group(2).strip()
        elif s and not s.startswith("#"):
            files.append(s.replace("\\", "/"))
    return meta, files


def _expand(z, lower, folder, files):
    """toc-Einträge in Lua-Dateien in Ladereihenfolge auflösen (XML: Script/Include in Reihenfolge)."""
    out, names = [], set()

    def walk(path, depth=0):
        real = lower.get(path.lower())
        if not real or depth > 10:
            return
        if real.lower().endswith(".lua"):
            out.append(real)
        elif real.lower().endswith(".xml"):
            text = z.read(real).decode("utf-8", "replace")
            names.update(re.findall(r'\bname\s*=\s*"([A-Za-z_]\w*)"', text))
            base = real.rsplit("/", 1)[0]
            for kind, f in re.findall(r'<(Script|Include)\b[^>]*\bfile\s*=\s*"([^"]+)"', text):
                walk(f"{base}/{f.replace(chr(92), '/')}", depth + 1)
    for f in files:
        walk(f"{folder}/{f}")
    return out, names


def _pick_toc(tocs, folder, suffixes):
    for t in tocs:
        stem = t.rsplit("/", 1)[-1][:-4]
        if any(stem.lower() == (folder + s).lower() for s in suffixes):
            return t
    main = [t for t in tocs if t.rsplit("/", 1)[-1][:-4].lower() == folder.lower()]
    return main[0] if main else None


def load_test(path):
    """-> Liste (level, text). Leere Liste, wenn alles lädt oder lupa fehlt (dann ("SKIP", grund))."""
    try:
        from lupa.lua51 import LuaRuntime
    except ImportError:
        return [("SKIP", "lupa fehlt – Ladetest übersprungen")]
    res = []
    z = zipfile.ZipFile(path)
    names = [n for n in z.namelist() if not n.endswith("/")]
    lower = {n.lower(): n for n in names}
    tocs_all = [n for n in names if n.lower().endswith(".toc") and n.count("/") == 1]
    folders = sorted({t.split("/", 1)[0] for t in tocs_all})
    for folder in folders:
        tocs = [t for t in tocs_all if t.startswith(folder + "/")]
        for flavor, iface, (lo, hi), suffixes in LOAD_FLAVORS:
            toc = _pick_toc(tocs, folder, suffixes)
            if not toc:
                continue
            meta, files = _parse_toc(z.read(toc).decode("utf-8", "replace"))
            ifaces = [int(x) for x in re.findall(r"\d+", meta.get("Interface", ""))]
            if not any(lo <= i <= hi for i in ifaces):
                continue                                   # dieser Client wird vom Addon nicht unterstützt
            deps = meta.get("Dependencies", "") + "," + meta.get("RequiredDeps", "")
            if any(d.strip() and not d.strip().lower().startswith(("blizzard_",)) for d in deps.split(",")):
                continue                                   # braucht ein anderes Addon: einzeln nicht ladbar
            lua_files, xml_names = _expand(z, lower, folder, files)
            lua = LuaRuntime(unpack_returned_tuples=True)
            lua.execute(MOCK)
            lua.execute(FLAVOR_LUA[flavor])
            own = set(re.findall(r"[A-Za-z_]\w*", meta.get("SavedVariables", "") + " " +
                                 meta.get("SavedVariablesPerCharacter", "")))
            g = lua.globals()
            g.GS_OWN = lua.table_from({k: True for k in own})
            # eigene Namen und die gemeinsamen GoldSentinel-Dateien sind beim ersten Laden leer (nil), wie im Spiel
            g.GS_PREFIX = lua.table_from([folder, "GoldSentinel"] + ([folder.replace("Sentinel", "")] if "Sentinel" in folder else []))
            lua.execute(GLOBALS_GUARD.replace("local own, ownPrefix = ...", "local own, ownPrefix = GS_OWN, GS_PREFIX"))
            for n in xml_names:                            # in XML angelegte Frames gibt es im Spiel schon
                lua.execute(f'CreateFrame("Frame", "{n}")')
            runner = lua.execute(RUNNER)
            ns = lua.table()
            label = f"{folder} ({flavor})"
            broken = []                                    # Dateien, die mit "nil value" abbrechen
            for f in lua_files:
                r = runner(z.read(f).decode("utf-8", "replace"), f, folder, ns)
                ok, err = r if isinstance(r, tuple) else (r, None)
                if not ok:
                    msg = str(err)
                    if "Zeitlimit" in msg:
                        res.append(("WARNUNG", f"Ladetest {label}: {f} – {msg}"))
                    elif "nil value" in msg:
                        broken.append((f, msg))
                    else:
                        res.append(("WARNUNG", f"Ladetest {label}: {f} – {msg} (beim Laden; kann an der Nachbildung liegen)"))
            if broken:
                f, msg = broken[0]
                more = f" Danach brechen {len(broken) - 1} weitere Dateien ab (Folgefehler: " + \
                       ", ".join(b[0].rsplit("/", 1)[-1] for b in broken[1:6]) + (" …" if len(broken) > 6 else "") + ")." \
                    if len(broken) > 1 else ""
                res.append(("FEHLER", f"Ladetest {label}: {f} lädt nicht – {msg}. Im Spiel bricht die Datei hier ab "
                                      f"(oft: Funktion benutzt, bevor sie definiert ist, oder Datei in falscher Reihenfolge "
                                      f"in der .toc).{more}"))
                continue                                   # Start-Ereignisse sind dann ohnehin kaputt
            for ev, args in (("ADDON_LOADED", f'"{folder}"'), ("PLAYER_LOGIN", ""), ("PLAYER_ENTERING_WORLD", "true, false")):
                r = lua.execute(f"local ok, e = pcall(GS_Fire, '{ev}'{', ' + args if args else ''}); return ok, tostring(e)")
                ok, err = r if isinstance(r, tuple) else (r, None)
                if not ok:
                    res.append(("WARNUNG", f"Ladetest {label}: Fehler bei {ev} – {err} (nachgebautes Spiel; bitte ansehen)"))
                    break
    return res
