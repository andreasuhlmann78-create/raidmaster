-- Test GoldSentinelDev v2 (Prüfsumme statt Name). Aufruf im Repo-Wurzelordner: lua5.1 shared/test_goldsentinel_dev.lua
BN=nil; NAME="Dontdiems"
function UnitName() return NAME end
dofile("shared/GoldSentinelDev.lua")
assert(GoldSentinelDev.version==2)
assert(GoldSentinelDev:IsDev()==true, "Name per Pruefsumme")
-- neu laden (known zurueck): fremder Name
GoldSentinelDev=nil; NAME="Fremd"; dofile("shared/GoldSentinelDev.lua"); assert(GoldSentinelDev:IsDev()==false)
-- BattleTag-Weg unveraendert: fremder Tag -> false, auch mit eigenem Namen
GoldSentinelDev=nil; NAME="Dontdiems"; function BNGetInfo() return nil, "Fremd#1234" end; dofile("shared/GoldSentinelDev.lua"); assert(GoldSentinelDev:IsDev()==false)
-- v1 geladen, dann v2: v2 gewinnt
BNGetInfo=nil; GoldSentinelDev=nil; dofile("RaidMaster/GoldSentinelDev.lua"); assert(GoldSentinelDev.version==1); dofile("shared/GoldSentinelDev.lua"); assert(GoldSentinelDev.version==2 and GoldSentinelDev:IsDev()==true)
-- v2 geladen, dann v1: bleibt v2
dofile("RaidMaster/GoldSentinelDev.lua"); assert(GoldSentinelDev.version==2)
print("GoldSentinelDev v2: 5/5 ok")
