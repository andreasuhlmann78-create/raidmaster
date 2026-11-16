-- Messung LW-5 E1: zeigt, welche .toc der Client gelesen hat (Titel in der AddOn-Liste und hier im Chat)
local f = CreateFrame("Frame")
f:RegisterEvent("PLAYER_LOGIN")
f:SetScript("OnEvent", function()
    local meta = (C_AddOns and C_AddOns.GetAddOnMetadata) or GetAddOnMetadata
    local title = meta and meta("GSTocDatei", "Title")
    DEFAULT_CHAT_FRAME:AddMessage("|cffffb238GS Toc-Test Datei|r: gelesen wurde " .. tostring(title)
        .. " (Interface " .. tostring(select(4, GetBuildInfo())) .. ")")
end)
