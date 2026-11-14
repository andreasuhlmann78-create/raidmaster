GetBuildInfo = GetBuildInfo or function() return "1.16.1", "54000", "Jan 1 2026", 11601 end
GetXPExhaustion = GetXPExhaustion or function() return 1200 end
GetZoneText = GetZoneText or function() return "Durotar" end
GetSubZoneText = GetSubZoneText or function() return "" end
GetRealZoneText = GetRealZoneText or function() return "Durotar" end
GetBindLocation = GetBindLocation or function() return "Klingenhügel" end
local TGT = { guid = "Creature-0-1-2-3-3098-0000", name = "Narbenrücken-Eber", level = 2 }
local oldExists = UnitExists
function UnitExists(u) if u == "target" then return true end return oldExists(u) end
local oldName = UnitName
function UnitName(u) if u == "target" then return TGT.name end return oldName(u) end
local oldLevel = UnitLevel
function UnitLevel(u) if u == "target" then return TGT.level end return oldLevel(u) end
function UnitGUID(u) if u == "target" then return TGT.guid end return nil end
function UnitIsPlayer(u) return u == "player" end
function UnitClassification() return "normal" end
function UnitCanAttack() return true end
C_NamePlate = { GetNamePlates = function() return { { namePlateUnitToken = "target" } } end }
