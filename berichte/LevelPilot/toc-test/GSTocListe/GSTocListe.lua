-- Messung LW-5 E1: wird diese Datei geladen, nimmt der Client die Interface-Liste "16001, 11509" an
local f = CreateFrame("Frame")
f:RegisterEvent("PLAYER_LOGIN")
f:SetScript("OnEvent", function()
    DEFAULT_CHAT_FRAME:AddMessage("|cffffb238GS Toc-Test Liste|r: geladen (Interface " .. tostring(select(4, GetBuildInfo())) .. ")")
end)
