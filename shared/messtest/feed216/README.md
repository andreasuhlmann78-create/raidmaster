# s216x_feed_direct – direkte Messung des Feed-Speichers (Supervisor, 15.11.2026 20:25)

Zusatz-Szenario für den AHSentinel-Nachbau (ahanalyzerpro/tests/wowsim). Anhängen an eine KOPIE von scenarios_new.lua, dann
`AHS_LOADED=1 ADDON_DIR=<ahanalyzerpro> SIM_TMP=$(mktemp -d) SIMDIR=<kopie> lua5.1 <kopie>/run.lua s216x_feed_direct`.

Misst bei angehaltener Speicherbereinigung NUR den Speicher, der in VS:FeedNet (davon GM.Feed) und in GoldSentinelMarkt.Tick
neu angelegt wird – je Vollscan, Feed abwechselnd aus/an (6 Läufe). `AHS_LOADED=1` setzt IsAddOnLoaded("AHSentinel") = wahr wie
im Spiel (der Nachbau kennt IsAddOnLoaded nicht -> dort liest GoldSentinelMarkt bei Feed AUS den Scan zusätzlich selbst).
Ergebnisse und Folgerung: shared/wissen/analysen/feed-speicher-2026-11-15.md
