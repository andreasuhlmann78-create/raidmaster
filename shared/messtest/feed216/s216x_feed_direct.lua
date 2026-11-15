-- Supervisor 15.11. 20:2x: direkte Messung des Feed-Speichers (nur Arbeit innerhalb GoldSentinelMarkt + VS:FeedNet)
S.s216x_feed_direct = function()
    local N = tonumber(os.getenv("SIM_BIG") or "") or 6000
    for i = 1, N do
        Sim:AddItem(700000 + i, { name = "Massenware " .. i, quality = 1, stack = 20, sell = 10, base = 1000 + (i % 500) })
    end
    local A = T.boot()
    local now = time()
    for id in pairs(Sim.items) do
        for k = 1, 20 do A:RecordPrice(id, 1000 + (k % 7) * 10, 10, now - k * 6 * 3600) end
    end
    Sim:FillMarket(1)
    Sim:OpenAH(); Sim:Advance(2)
    A.UI.ahTab:Click()
    T.clickTab("market")
    local VS = A.FullScan
    if os.getenv("AHS_LOADED") then _G.IsAddOnLoaded = function(n) return n == "AHSentinel" end end
    local GM = _G.GoldSentinelMarkt
    local acc = { FeedNet = 0, Feed = 0, Tick = 0, Pump = 0 }
    local function wrap(tbl, name, key)
        local f = tbl[name]
        tbl[name] = function(...)
            local k0 = collectgarbage("count")
            if key == "Tick" then acc.reader = (acc.reader or 0) + ((GM.reader or GM.readAt) and 1 or 0) end
            local a, b, c = f(...)
            acc[key] = acc[key] + (collectgarbage("count") - k0)
            return a, b, c
        end
    end
    wrap(VS, "FeedNet", "FeedNet"); wrap(GM, "Tick", "Tick"); wrap(GM, "Feed", "Feed")
    local function run(label, feed)
        VS.FEED_ON = feed
        for k in pairs(acc) do acc[k] = 0 end
        Sim:Advance(VS.MIN_GAP and VS.MIN_GAP + 5 or 960)
        collectgarbage("collect")
        local kb0 = collectgarbage("count")
        collectgarbage("stop")
        VS:Start(true)
        local t0 = Sim.clock
        while (VS.running or (VS.curMeasure ~= nil)) and Sim.clock - t0 < 900 do Sim:Advance(0.05, 0.05) end
        local gEnd = collectgarbage("count") - kb0
        local ticks = 0
        while GM.feedJob and ticks < 20000 do Sim:Advance(0.05, 0.05); ticks = ticks + 1 end
        local gAll = collectgarbage("count") - kb0
        collectgarbage("restart"); collectgarbage("collect")
        T.note(string.format("%s stats: read=%s dropped=%s", label, tostring(GM.stats.reads or GM.stats.read), (function() local t={} for k,v in pairs(GM.stats.dropped or {}) do t[#t+1]=k.."="..v end return table.concat(t,",") end)()))
        T.note(string.format("%s Feed %s: bis Scan-Ende +%.0f KB, bis Feed fertig +%.0f KB (%d Bilder danach) | in FeedNet %.0f (davon Feed %.0f) · in Tick %.0f KB, Ticks mit Leser %d",
            label, feed and "an" or "aus", gEnd, gAll, ticks, acc.FeedNet, acc.Feed, acc.Tick, acc.reader or 0))
    end
    run("L1", false); run("L2", true); run("L3", false); run("L4", true); run("L5", false); run("L6", true)
    VS.FEED_ON = false
    T.ok(true, "gemessen")
end
