-- Test mit echtem Datenpaket
local dir = arg[0]:match("^(.*)/[^/]*$") or "."
dofile(dir .. "/mock2.lua")
local LP = NS
local fails = 0
local function check(c, m) if c then print("OK     " .. m) else fails = fails + 1 print("FEHLER " .. m) end end
for _, m in ipairs(CHAT) do if m:find("Fehler") or m:find("konnte nicht") then print("CHAT: " .. m) fails = fails + 1 end end
check(LP.QuestDB.pack, "Datenpaket erkannt: " .. LP.QuestDB.packInfo)
local t0 = os.clock()
LP.Planner:Replan()
print(string.format("       Planung: %.2f s", os.clock() - t0))
local list = {}
for i, s in ipairs(LP.Engine:Steps()) do
    if i > 6 then break end
    list[#list + 1] = s.t .. ":" .. (s.id or "-") .. " " .. (s.q or s.text or "") .. (s.map and string.format(" @%d %.1f,%.1f", s.map, s.x or 0, s.y or 0) or "")
end
print("       " .. table.concat(list, "\n       "))
local expect = tonumber(arg[6] or "0")
if expect > 0 then
    local found = false
    for _, s in ipairs(LP.Engine:Steps()) do if s.id == expect then found = true end end
    check(found, "erwartete Startquest " .. expect .. " geplant")
end
local forbid = tonumber(arg[7] or "0")
if forbid > 0 then
    local found = false
    for _, s in ipairs(LP.Engine:Steps()) do if s.id == forbid then found = true end end
    check(not found, "fremde Quest " .. forbid .. " nicht geplant")
end
local v, d = LP.QuestDB:NearestService("repair")
check(v ~= nil, "Reparatur-Händler aus Datenpaket: " .. (v and (v.name .. " " .. math.floor(d) .. " Yards") or "keiner"))
print(fails == 0 and "== ALLE TESTS OK" or ("== " .. fails .. " FEHLER"))
