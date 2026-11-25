-- Minimaler WoW-Mock zum Testen der Addon-Logik
local missing = {}
local timers = {}
local now = 1000
local servertime = 1761300000
function GetTime() return now end
GAMETOC = GAMETOC or 16001
function GetBuildInfo() return "1.16.0", "60000", "Oct 1 2026", GAMETOC end
function GetLocale() return GAMELOCALE or "deDE" end
if not NO_MASTERLOOT then function GiveMasterLoot(...) end function GetMasterLootCandidate(...) end end
function GetServerTime() return servertime end
date = os.date
time = os.time
function wipe(t) for k in pairs(t) do t[k]=nil end return t end
tinsert = table.insert
function strsplit(sep, s)
  local out = {}
  for part in (s..sep):gmatch("(.-)%"..sep) do out[#out+1]=part end
  return unpack(out)
end
function hooksecurefunc(a, b, c) end
function geterrorhandler() return function(e) print("ERROR: "..tostring(e)); ERRORS=(ERRORS or 0)+1 end end
C_Timer = {
  After = function(d, fn) timers[#timers+1] = {t=now+d, fn=fn} end,
  NewTicker = function(d, fn) local tk = {cancelled=false}; tk.Cancel=function(s) s.cancelled=true end; timers[#timers+1]={t=now+d, fn=fn, every=d, tk=tk}; return tk end,
  NewTimer = function(d, fn) local tk = {cancelled=false}; tk.Cancel=function(s) s.cancelled=true end; timers[#timers+1]={t=now+d, fn=fn, tk=tk}; return tk end,
}
function Advance(sec)
  local target = now + sec
  while true do
    table.sort(timers, function(a,b) return a.t < b.t end)
    local tm = timers[1]
    if not tm or tm.t > target then break end
    table.remove(timers, 1)
    now = tm.t
    if not (tm.tk and tm.tk.cancelled) then
      tm.fn(tm.tk)
      if tm.every and not tm.tk.cancelled then tm.t = now + tm.every; timers[#timers+1]=tm end
    end
  end
  now = target
end

-- universeller Frame-Stub
local function NewObj()
  local o = {scripts={}, hooks={}, shown=false, text="", _frame=true}
  return setmetatable(o, {__index=function(t,k)
    local f
    if k=="GetText" then f=function(s) return s.text end
    elseif k=="SetText" then f=function(s,v) s.text=v or "" end
    elseif k=="IsShown" then f=function(s) return s.shown end
    -- 3.0.49 (RM-K2): wie im Spiel – OnShow nur beim Wechsel von verborgen zu sichtbar; SetScript löscht HookScript-Haken
    -- (warcraft.wiki.gg API_ScriptObject_HookScript: "hooks … remain in place until replaced or cleared with SetScript")
    elseif k=="Show" then f=function(s)
        if s.shown then return end
        s.shown=true
        if s.scripts.OnShow then s.scripts.OnShow(s) end
        for _, h in ipairs(s.hooks.OnShow or {}) do h(s) end
      end
    elseif k=="Hide" then f=function(s) s.shown=false end
    elseif k=="IsVisible" then f=function(s)
        local x = s
        while x do
          if not rawget(x, "shown") then return false end
          x = rawget(x, "parent")
        end
        return true
      end
    elseif k=="SetScript" then f=function(s,n,fn) s.scripts[n]=fn; s.hooks[n]=nil end
    elseif k=="HookScript" then f=function(s,n,fn) s.hooks[n]=s.hooks[n] or {}; table.insert(s.hooks[n], fn) end
    elseif k=="SetSize" then f=function(s,w,h) rawset(s,"w",w); rawset(s,"h",h) end
    elseif k=="SetWidth" then f=function(s,w) rawset(s,"w",w) end
    elseif k=="SetHeight" then f=function(s,h) rawset(s,"h",h) end
    elseif k=="ClearAllPoints" then f=function(s) rawset(s,"pt",nil) end
    -- Lage nur für Rahmen direkt an UIParent (Fenster): erster Ankerpunkt, Bildschirm 1920x1080, Skalierung 1
    elseif k=="GetRect" then f=function(s)
        local pt = rawget(s,"pt")
        if not pt then return nil end
        local P = pt.rel or rawget(s,"parent")
        if P ~= UIParent then return nil end
        local w, h = rawget(s,"w") or 100, rawget(s,"h") or 100
        local function at(name, W, H)
          local x = name:find("LEFT") and 0 or name:find("RIGHT") and W or W / 2
          local y = name:find("BOTTOM") and 0 or name:find("TOP") and H or H / 2
          return x, y
        end
        local px, py = at(pt.rp or pt.p, UIParent.w, UIParent.h)
        local fx, fy = at(pt.p, w, h)
        return px + (pt.x or 0) - fx, py + (pt.y or 0) - fy, w, h
      end
    elseif k=="GetScript" then f=function(s,n) return s.scripts[n] end
    elseif k=="SetPoint" or k=="SetAllPoints" then
      -- 3.0.31 (T169): wie im Spiel – ein Bezug, der eine Tabelle, aber kein Rahmen ist, gibt "Wrong object type"
      f=function(s, p, rel, rp, x, y)
        if k=="SetAllPoints" then rel = p end
        if type(rel)=="table" and not rawget(rel,"_frame") then error(k .. "(): Wrong object type for function", 2) end
        if k=="SetPoint" and not rawget(s,"pt") then
          if type(rel) == "number" then rel, rp, x, y = nil, nil, rel, rp end
          if type(rp) == "number" then rp, x, y = nil, rp, x end
          rawset(s, "pt", { p = p, rel = rel, rp = rp or p, x = x, y = y })
        end
      end
    elseif k=="GetPoint" then f=function() return "CENTER", nil, "CENTER", 0, 0 end
    elseif k=="GetMinMaxValues" then f=function(s) return s.mn or 0, s.mx or 0 end
    elseif k=="SetMinMaxValues" then f=function(s,a,b) s.mn=a s.mx=b end
    elseif k=="HasFocus" or k=="GetChecked" then f=function() return false end
    elseif k=="IsEnabled" then f=function() return true end
    elseif k=="GetWidth" then f=function(s) return rawget(s,"w") or 100 end
    elseif k=="GetHeight" then f=function(s) return rawget(s,"h") or 100 end
    elseif k=="GetCenter" then f=function() return 0,0 end
    elseif k=="GetEffectiveScale" then f=function() return 1 end
    elseif k=="CreateFontString" or k=="CreateTexture" then f=function() return NewObj() end
    elseif k=="RegisterEvent" then f=function(s,e) rawset(s,"_ev",rawget(s,"_ev") or {}); s._ev[e]=true end
    else f=function() end end
    rawset(t,k,f)
    return f
  end})
end
FRAMES = {}
function CreateFrame(kind, name, parent, template)
  local o = NewObj(); o.kind=kind; o.parent=parent
  -- 3.0.49 (RM-K2): wie im Spiel ist ein neuer Rahmen sofort sichtbar (ohne OnShow); HARNESS_HIDDEN=1 = altes Verhalten
  if os.getenv("HARNESS_HIDDEN") ~= "1" then o.shown = true end
  if name then _G[name]=o end
  FRAMES[#FRAMES+1]=o
  return o
end
UIParent = NewObj(); UIParent.shown = true; UIParent.w = 1920; UIParent.h = 1080; Minimap = NewObj(); DEFAULT_CHAT_FRAME = {AddMessage=function(_,m) print("CHAT: "..m) end}
GameTooltip = NewObj(); RaidWarningFrame = NewObj(); UISpecialFrames = {}
StaticPopupDialogs = {}; SlashCmdList = {}
LASTPOPUP = nil
function StaticPopup_Show(name, text) local p = {data=nil, text=text, which=name}; LASTPOPUP=p; print("POPUP: "..tostring(text)); return p end
function AcceptPopup() local A = ADDON_NS and ADDON_NS.Auction; if A and A.AwaitingAward and A.AwaitingAward() then A.Award() return end local d = StaticPopupDialogs[LASTPOPUP.which]; d.OnAccept(LASTPOPUP) end
STANDARD_TEXT_FONT="x"; ChatFontNormal={}; ACCEPT="OK"; CANCEL="Abbr"; ERR_TRADE_COMPLETE="Handel abgeschlossen"
RAID_CLASS_COLORS = {WARRIOR={r=0.78,g=0.61,b=0.43}, MAGE={r=0.4,g=0.8,b=1}, PRIEST={r=1,g=1,b=1}}
LOCALIZED_CLASS_NAMES_MALE = {WARRIOR="Krieger", MAGE="Magier", PRIEST="Priester"}
SOUNDKIT = {}
function PlaySound() end
function RaidNotice_AddMessage() end
ChatTypeInfo = {RAID_WARNING={}}
BackdropTemplateMixin = {}
function ReloadUI() end

-- Spielwelt
ME = "Testa"
RAID = { {"Testa",1,"WARRIOR"}, {"Bob",0,"MAGE"}, {"Cleo",0,"PRIEST"} }
GUILD = { {"Testa",1,"WARRIOR"}, {"Bob",3,"MAGE"}, {"Cleo",4,"PRIEST"}, {"Offi",0,"PRIEST"} }
function UnitName(u) if u=="player" then return ME end return nil end
function UnitClass(u) return "Krieger","WARRIOR" end
function IsInRaid() return true end
function IsInGuild() return true end
function GetNumGroupMembers() return #RAID end
function GetRaidRosterInfo(i) local r=RAID[i]; if not r then return nil end return r[1], r[2], 1, 60, r[3], r[3], "MC", true, false end
function UnitIsGroupLeader(u) return true end
function UnitIsGroupAssistant() return true end
function GetNumGuildMembers() return #GUILD end
function GetGuildRosterInfo(i) local g=GUILD[i]; return g[1].."-Realm", "Rang", g[2], 60, g[3], "", "", "", true, 0, g[3] end
function GetGuildInfo() return "Gilde", "Offizier", 1 end
C_GuildInfo = {GuildRoster=function() end}
function GetLootMethod() return "master", 0, 1 end
function GetLootThreshold() return 3 end
function SetLootMethod(m,n) print("SetLootMethod "..m.." "..tostring(n)) end
function SetLootThreshold(n) print("SetLootThreshold "..n) end
SENT = {}
C_ChatInfo = {RegisterAddonMessagePrefix=function() end, SendAddonMessage=function(p,m,c,t) SENT[#SENT+1]={p=p,m=m,c=c,t=t} end}
CHATSENT = {}
function SendChatMessage(m,c,_,t) CHATSENT[#CHATSENT+1]={m=m,c=c,t=t}; print("SAY["..c.."]: "..m) end
ITEMS = {
 [16800]={"|cffa335ee|Hitem:16800::::::::60:::::|h[Arkanistenstiefel]|h|r",4,4,1,"INVTYPE_FEET"},
 [17010]={"|cff0070dd|Hitem:17010::::::::60:::::|h[Feuerkern]|h|r",3,7,0,""},
 [18563]={"|cffff8000|Hitem:18563::::::::60:::::|h[Bindungen]|h|r",5,15,0,""},
}
-- 3.0.32: wie im Spiel nehmen GetItemInfo/GetItemInfoInstant eine Item-ID (Zahl) oder einen Link
function GetItemInfoInstant(link) local id=tonumber(link) or tonumber(tostring(link):match("item:(%d+)")); local it=ITEMS[id]; if not it then return nil end return id,"","",it[5],"icon",it[3],it[4] end
function GetItemInfo(link) local id=tonumber(link) or tonumber(tostring(link):match("item:(%d+)")); local it=ITEMS[id]; if not it then return nil end return "n",it[1],it[2],60,60,"","",1,it[5],"tex" end
function GetInventoryItemLink() return nil end
LOOT = {}
function GetNumLootItems() return #LOOT end
function GetLootSlotLink(i) return LOOT[i] end
function GetLootSourceInfo(i) return "Creature-0-1-2-3-12056-0001" end
function GetMasterLootCandidate(slot,i) local r=RAID[i]; return r and r[1] end
GIVEN = {}
function GiveMasterLoot(slot, i) GIVEN[#GIVEN+1]={slot=slot, to=RAID[i][1], link=LOOT[slot]}; print("GIVE "..tostring(LOOT[slot]).." -> "..RAID[i][1]) end
function GetNumSkillLines() return 0 end
function SetRaidTarget(u,i) print("SetRaidTarget "..u.." "..i) end
function GetRaidTargetIndex() return nil end
function UnitExists(u) return u=="mouseover" end
function UnitIsPlayer() return false end
function UnitIsDead() return false end
function GetCurrentKeyBoardFocus() return nil end
function CombatLogGetCurrentEventInfo() return 0,"UNIT_DIED",nil,nil,nil,nil,nil,"Creature-0-1-2-3-11673-0001","Uralter Kernhund" end
function ClearCursor() end
function GetTradePlayerItemLink() return nil end
function ClickTradeButton() end

setmetatable(_G, {__index=function(t,k) missing[k]=true; return nil end})
function MissingGlobals() local l={} for k in pairs(missing) do l[#l+1]=k end table.sort(l) return l end

-- Addon laden
local RM = {}
ADDON_NS = RM
-- 3.0.37 (Hinweis 18.11. 10:30 "Nachbau wie Forever"): Forever 1.60.1 läuft auf dem modernen Client – es gibt die alten
-- globalen Funktionen NICHT, nur C_Item/C_AddOns/… . Die Nachbildung bietet für Forever genau das (nicht mehr); für die alten
-- Clients (Era usw.) bleiben die globalen Funktionen.
if GAMETOC == 16001 then
  C_Item = C_Item or {}
  C_Item.GetItemInfo = GetItemInfo
  C_Item.GetItemInfoInstant = GetItemInfoInstant
  C_Item.GetItemCount = C_Item.GetItemCount or function() return 0 end
  C_Item.RequestLoadItemDataByID = C_Item.RequestLoadItemDataByID or function() end
  C_AddOns = C_AddOns or {}
  C_AddOns.GetAddOnMetadata = GetAddOnMetadata
  C_AddOns.IsAddOnLoaded = C_AddOns.IsAddOnLoaded or function(n) return n == "RaidMaster" end
  for _, name in ipairs({ "GetItemInfo", "GetItemInfoInstant", "GetItemCount", "GetItemIcon", "GetAddOnMetadata", "IsAddOnLoaded",
      "GetNumAddOns", "GetAddOnInfo", "UnitBuff", "UnitDebuff", "UnitAura", "GetSpellInfo", "GetContainerNumSlots",
      "GetContainerItemInfo", "GetContainerItemLink", "GetItemQualityColor", "IsUsableItem", "GetItemCooldown", "GetSpellCooldown" }) do
    _G[name] = nil
  end
end
-- 3.0.40: Einstellungsfenster des Spiels – Era 1.15 und Forever haben die moderne Settings-API (Kategorie für AddOns), sonst nichts
SETTINGS_CATEGORIES = {}
Settings = {
  RegisterCanvasLayoutCategory = function(frame, name) local c = { frame = frame, name = name }; return c end,
  RegisterAddOnCategory = function(c) SETTINGS_CATEGORIES[#SETTINGS_CATEGORIES + 1] = c end,
}
SettingsPanel = NewObj()
function HideUIPanel(f) if f and f.Hide then f:Hide() end end
-- Testmodus-Erkennung: in den Tests gilt der Entwickler als erkannt (außer DEV_OFF ist gesetzt)
if not GoldSentinelDev then
  GoldSentinelDev = { version = 99, IsDev = function() return not DEV_OFF end,
    Require = function(self, a) if not DEV_OFF then return true end print("DEV-BLOCK " .. tostring(a)); return false end,
    Status = function() return DEV_OFF and "Testmodus: aus" or "Testmodus: an" end }
end
local files = {}
-- Dateien in der Reihenfolge der .toc (wie im Spiel); LootData und Test.lua laden die Tests selbst
for line in io.lines(ADDONDIR .. "/RaidMaster.toc") do
  local f = line:gsub("\\", "/"):gsub("%s+$", "")
  -- T90 (15.11.): Sprachdateien in der TOC-Reihenfolge laden wie im Spiel (nach Locale.lua). Bis 3.0.26 wurden sie
  -- vorne eingefügt (vor Locale.lua) -> RM.LOCALE war noch nil, jede Sprachdatei brach mit "return" ab.
  if f ~= "" and not f:match("^#") and f ~= "Test/LootData.lua" and f ~= "Test/Test.lua" then
    files[#files + 1] = f
  end
end
for _, f in ipairs(files) do
  local chunk = assert(loadfile(ADDONDIR.."/"..f))
  chunk("RaidMaster", RM)
end
function Fire(event, ...) local fr = RM.frame; fr.scripts.OnEvent(fr, event, ...) end
-- Betrachten (Standard: keine Talente beim Betrachten)
function UnitIsConnected() return true end
function CanInspect() return true end
function CheckInteractDistance() return true end
function InCombatLockdown() return false end
function NotifyInspect(u) end
function ClearInspectPlayer() end
function UnitGUID(u) return "GUID-"..u end
function UnitLevel() return 60 end
