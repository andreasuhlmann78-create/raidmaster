-- BuffSentinel – nachgebautes Spiel für die Offline-Testroutine (TU9). Nur für tests/run_offline.lua.
-- Minimale WoW-API-Attrappe; Lua 5.1 bis 5.4. Keine echten Spielernamen.
local unpack = table.unpack or unpack
local function newObj(kind)
  local o = { _kind = kind, _shown = (kind ~= "Frame" and kind ~= "Button" and kind ~= "ScrollFrame" and kind~="EditBox") , _attr = {}, _scripts = {}, _alpha = 1 }
  return setmetatable(o, { __index = function(t, k)
    local f = rawget(_G, "M_" .. k)
    if f then return f end
    if type(k) == "string" and k:match("^%u") then return function() end end
    return nil
  end })
end
_G.newObj = newObj
local function addRegion(self, o) self._regions = self._regions or {}; self._regions[#self._regions + 1] = o; o._parent = self; return o end
function M_CreateFontString(self) return addRegion(self, newObj("FontString")) end
function M_CreateTexture(self) return addRegion(self, newObj("Texture")) end
function M_GetRegions(self) return unpack(self._regions or {}) end
function M_GetChildren(self) return unpack(self._kids or {}) end
function M_GetParent(self) return self._parent end
function M_SetParent(self, p)
  local old = self._parent
  if old and old._kids then for i, k in ipairs(old._kids) do if k == self then table.remove(old._kids, i) break end end end
  self._parent = p
  if p then p._kids = p._kids or {}; p._kids[#p._kids + 1] = self end
end
function M_RegisterEvent(self, ev) self._events = self._events or {}; self._events[ev] = true end
function M_UnregisterEvent(self, ev) if self._events then self._events[ev] = nil end end
function M_IsEventRegistered(self, ev) return self._events and self._events[ev] or false end
function M_IsVisible(self)
  local o = self
  while o do if not o._shown then return false end o = o._parent end
  return true
end
function M_CreateAnimationGroup(self) return newObj("AnimGroup") end
function M_CreateAnimation(self) return newObj("Anim") end
function M_Show(self) self._shown = true end
function M_Hide(self) self._shown = false end
function M_IsShown(self) return self._shown end
function M_SetAlpha(self, a) self._alpha = a end
function M_SetAttribute(self, k, v) self._attr[k] = v end
function M_GetAttribute(self, k) return self._attr[k] end
function M_SetScript(self, k, f) self._scripts[k] = f end
function M_GetScript(self, k) return self._scripts[k] end
function M_GetFont() return "Fonts\\FRIZQT__.TTF", 12, "" end
function M_GetStringHeight() return 12 end
function M_GetWidth() return 140 end
function M_GetCenter() return 0, 0 end
function M_GetFrameLevel() return 1 end
function M_GetEffectiveScale() return 1 end
function M_GetPoint() return "CENTER", nil, "CENTER", 0, 0 end
function M_GetText() return "" end
function M_GetName(self) return self._name end
function CreateFrame(kind, name, parent, template)
  local o = newObj(kind); o._name = name; if name then _G[name] = o end
  if parent then M_SetParent(o, parent) end
  if kind == "Frame" and not template then o._shown = true end
  return o
end
UIParent = CreateFrame("Frame"); Minimap = CreateFrame("Frame")
DEFAULT_CHAT_FRAME = { AddMessage = function(_, m) print("[CHAT] " .. m:gsub("|c%x%x%x%x%x%x%x%x",""):gsub("|r","")) end }
GameTooltip = newObj("Tooltip")
UISpecialFrames = {}
SOUNDKIT = {}
RAID_CLASS_COLORS = { WARRIOR = {r=0.78,g=0.61,b=0.43}, PRIEST={r=1,g=1,b=1}, MAGE={r=0.4,g=0.8,b=1} }
function wipe(t) for k in pairs(t) do t[k] = nil end return t end
tinsert, tremove = table.insert, table.remove
strlower, strupper = string.lower, string.upper
function strtrim(s) return (s:gsub("^%s+",""):gsub("%s+$","")) end
math.atan2 = math.atan2 or math.atan
NOW = 100
function GetTime() return NOW end
function time() return os.time() end
function GetCVar(k) if k == "ActionButtonUseKeyDown" then return "1" end end
function PlaySound(id) SOUNDS = (SOUNDS or 0) + 1 end
LOCKDOWN = false
function InCombatLockdown() return LOCKDOWN end
COMBAT = false
function UnitAffectingCombat() return COMBAT end
function IsMounted() return false end
function UnitIsDeadOrGhost() return false end
function UnitOnTaxi() return false end
INSTANCE = { false, "none" }
function IsInInstance() return INSTANCE[1], INSTANCE[2] end
RESTING = false
function IsResting() return RESTING end
function GetZonePVPInfo() return nil end
function UnitName(u) return ({player="Testselbst", party1="Testpartner", party2="Testzweiter"})[u] or u end
function UnitLevel() return 60 end
function geterrorhandler() return function() end end
function GetRealmName() return "WoWForever" end
CLASS = CLASS or "WARRIOR"
function UnitClass(u) if u == "player" then return "Krieger", CLASS end return "x", (u=="party1" and "PRIEST" or "MAGE") end
function UnitGUID(u) return "GUID-" .. u end
function UnitExists(u) return u == "player" or u == "party1" or u == "party2" or (u == "target" and TARGET ~= nil) end
function UnitIsConnected() return true end
function UnitIsVisible() return true end
function UnitCanAttack() return true end
function UnitIsDead() return false end
TARGET = nil
function UnitHealth() return TARGET and TARGET.hp or 0 end
function UnitHealthMax() return 100 end
function IsInRaid() return false end
GROUP = 0
function GetNumSubgroupMembers() return GROUP end
-- Zauber (Classic-IDs -> deutsche Namen)
SPELLS = { [6673]="Schlachtruf", [7384]="Überwältigen", [6572]="Rache", [5308]="Hinrichten", [12294]="Tödlicher Stoß",
 [12292]="Weitreichende Stöße", [20230]="Gegenschlag", [100]="Sturmangriff", [23881]="Blutdurst", [1680]="Wirbelwind",
 [12328]="Todeswunsch", [1719]="Tollkühnheit", [20252]="Abfangen", [23922]="Schildschlag", [2565]="Schildblock",
 [871]="Schildwall", [12975]="Letztes Gefecht", [2687]="Blutrausch", [18499]="Berserkerwut",
 [1459]="Arkane Intelligenz", [23028]="Arkane Brillanz", [7302]="Eisrüstung", [6117]="Magische Rüstung", [168]="Frostrüstung",
 [12536]="Freizaubern", [5143]="Arkane Geschosse", [133]="Feuerball", [116]="Frostblitz", [11366]="Pyroschlag", [2139]="Gegenzauber", [1953]="Blinzeln",
 [122]="Frostnova", [12051]="Hervorrufung", [12043]="Geistesgegenwart", [12042]="Arkane Macht", [2136]="Feuerschlag", [11129]="Verbrennen", [11113]="Druckwelle",
 [11426]="Eisbarriere", [12472]="Kälteeinbruch", [11958]="Eisblock" }
local byName = {} for id, n in pairs(SPELLS) do byName[n] = id end
function GetSpellInfo(s)
  local id = type(s) == "number" and s or byName[s]
  if not id or not SPELLS[id] then return nil end
  return SPELLS[id], nil, "Icon" .. id, 0, 0, 0, id
end
KNOWN = {}
function GetNumSpellTabs() return 1 end
function GetSpellTabInfo() return "Allgemein", nil, 0, #KNOWN end
function GetSpellBookItemName(i) return KNOWN[i] end
COOLDOWNS = {}
function GetSpellCooldown(n) local c = COOLDOWNS[n]; if c then return c[1], c[2] end return 0, 0 end
USABLE = {}
function IsUsableSpell(n) local u = USABLE[n]; if u == nil then return true, false end return u[1], u[2] end
function IsSpellInRange() return 1 end
TALENTS = { {}, {}, {} }
function GetNumTalentTabs() return 3 end
function GetNumTalents(tab) return #TALENTS[tab] end
function GetTalentInfo(tab, i) local t = TALENTS[tab][i]; return t[1], "icon", 1, 1, t[2], t[3] or 5 end
AURAS = { player = {} }
function UnitBuff(u, i) local a = (AURAS[u] or {})[i]; if not a then return nil end return a[1], "icon", a[3] or 1, nil, 0, a[2] or 0, nil, nil, nil, a[4] end
CLEU = {}
function CombatLogGetCurrentEventInfo() return unpack(CLEU) end
SlashCmdList = {}
C_Timer = { After = function(_, f) f() end }
function GetTalentInfo(tab, i) local t = TALENTS[tab][i]; return t[1], "icon", t[4] or i, t[5] or 1, t[2], t[3] or 5 end
function strsplit(sep, s) local out = {} for part in (s .. sep):gmatch("(.-)" .. sep:gsub("%p","%%%0")) do out[#out+1] = part end return unpack(out) end
function IsInGuild() return true end
SENT = {}
C_ChatInfo = { RegisterAddonMessagePrefix = function() end, SendAddonMessage = function(p, m, c) SENT[#SENT+1] = {p, m, c} end }

function M_SetWidth(self, w) self._w = w end
function M_SetSize(self, w, h) self._w = w; self._h = h end

function M_SetFont(self, f, size) self._size = size end
-- Entwickler-Erkennung: in den Tests steuerbar (DEV = false -> normaler Spieler)
if not REAL_DEV then
  GoldSentinelDev = { version = 99, IsDev = function() return DEV ~= false end,
    Require = function(self, a) if not self:IsDev() then print("[CHAT] " .. tostring(a) .. ": nur Entwickler") end return self:IsDev() end }
end

LOCALE = LOCALE or "deDE"
function GetLocale() return LOCALE end
