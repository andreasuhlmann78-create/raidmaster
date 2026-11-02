# Addon-Prüfung

Vorlage shared/GoldSentinelGame.lua: Version 2
Tests der gemeinsamen Datei: bestanden GoldSentinelGame-Tests: bestanden
Lua-Syntaxprüfung mit: lupa (Lua 5.1)

## AHSentinel-0.65.2.zip: OK

## BuffSentinel-0.9.4.zip: OK

## GuildSentinel-0.9.8.zip: OK

## ProfessionSentinel-0.9.8.zip: OK

## RaidMaster-3.0.12.zip: OK

## ThreatSentinel-2.4.1.zip: OK

## levelpilot__levelpilot-3.12.1.LevelPilot.zip: OK

## levelpilot__levelpilot-3.5.0.LevelPilot_Data.zip: OK (5 Warnungen)
- **WARNUNG** LevelPilot_Data/Tools/forever_maps.lua: liegt im Addon, wird aber nicht geladen (in keiner .toc/.xml) – gehört nicht in die ZIP?
- **WARNUNG** LevelPilot_Data/Tools/gen_pack.lua: liegt im Addon, wird aber nicht geladen (in keiner .toc/.xml) – gehört nicht in die ZIP?
- **WARNUNG** LevelPilot_Data/Tools/gen_names.lua: liegt im Addon, wird aber nicht geladen (in keiner .toc/.xml) – gehört nicht in die ZIP?
- **WARNUNG** Lua-Syntaxfehler in einer Datei, die das Spiel nicht lädt (Werkzeug?): LevelPilot_Data/Tools/gen_pack.lua:35: 'end' expected near '&' – am besten nicht in die ZIP packen
- **WARNUNG** GoldSentinelGame.lua fehlt (gemeinsame Versionserkennung noch nicht eingebaut)

