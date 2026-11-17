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
  local o = {scripts={}, shown=false, text="", _frame=true}
  return setmetatable(o, {__index=function(t,k)
    local f
    if k=="GetText" then f=function(s) return s.text end
    elseif k=="SetText" then f=function(s,v) s.text=v or "" end
    elseif k=="IsShown" then f=function(s) return s.shown end
    elseif k=="Show" then f=function(s) s.shown=true; if s.scripts.OnShow then s.scripts.OnShow(s) end end
    elseif k=="Hide" then f=function(s) s.shown=false end
    elseif k=="SetScript" then f=function(s,n,fn) s.scripts[n]=fn end
    elseif k=="GetScript" then f=function(s,n) return s.scripts[n] end
    elseif k=="SetPoint" or k=="SetAllPoints" then
      -- 3.0.31 (T169): wie im Spiel – ein Bezug, der eine Tabelle, aber kein Rahmen ist, gibt "Wrong object type"
      f=function(s, p, rel)
        if k=="SetAllPoints" then rel = p end
        if type(rel)=="table" and not rawget(rel,"_frame") then error(k .. "(): Wrong object type for function", 2) end
      end
    elseif k=="GetPoint" then f=function() return "CENTER", nil, "CENTER", 0, 0 end
    elseif k=="GetMinMaxValues" then f=function(s) return s.mn or 0, s.mx or 0 end
    elseif k=="SetMinMaxValues" then f=function(s,a,b) s.mn=a s.mx=b end
    elseif k=="HasFocus" or k=="GetChecked" then f=function() return false end
    elseif k=="IsEnabled" then f=function() return true end
    elseif k=="GetWidth" or k=="GetHeight" then f=function() return 100 end
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
  local o = NewObj(); o.kind=kind
  if name then _G[name]=o end
  FRAMES[#FRAMES+1]=o
  return o
end
UIParent = NewObj(); Minimap = NewObj(); DEFAULT_CHAT_FRAME = {AddMessage=function(_,m) print("CHAT: "..m) end}
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
function GetItemInfoInstant(link) local id=tonumber(tostring(link):match("item:(%d+)")); local it=ITEMS[id]; if not it then return nil end return id,"","",it[5],"icon",it[3],it[4] end
function GetItemInfo(link) local id=tonumber(tostring(link):match("item:(%d+)")); local it=ITEMS[id]; if not it then return nil end return "n",it[1],it[2],60,60,"","",1,it[5],"tex" end
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
