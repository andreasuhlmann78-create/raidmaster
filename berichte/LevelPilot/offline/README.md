# LevelPilot – Offline-Testroutine (TU9)

Testet eine veröffentlichte LevelPilot-ZIP ohne WoW-Client: `/lp testroutine` (Bereiche A–J) und die Regressionsläufe
laufen in einem nachgebauten Spiel (Lua 5.1, `lua/mock2.lua`).

```
python3 berichte/LevelPilot/offline/run_offline.py                       # neueste announce/levelpilot__levelpilot-*.LevelPilot.zip
python3 berichte/LevelPilot/offline/run_offline.py announce/levelpilot__levelpilot-3.12.30.LevelPilot.zip
python3 berichte/LevelPilot/offline/run_offline.py --nur testroutine     # nur Teil 1 (oder --nur regression)
```

Rückgabewert 0 = kein FEHLER, 1 = mindestens ein FEHLER oder ein Lauf ohne Ergebnis.

Lua 5.1: `LUA51=/pfad/zu/lua5.1`, sonst `lua5.1`/`lua51` im PATH, sonst `lupa` (`pip install lupa`).

## Was läuft

| Teil | Skript | Lagen |
|---|---|---|
| Testroutine A–J | `lua/test40.lua` | Forever deDE und enUS (Orc-Krieger L6, Durotar), Forever Allianz (Mensch-Krieger L10, Wald von Elwynn), Classic Era deDE, TBC Classic deDE |
| Regression | `lua/test2.lua` … `lua/test38.lua` | Szenarien seit 2.x; `test15` = Wegnetz-Prüfung (Höhlen, Tunnel, gelaufene Wege, Wegführung) |

Spielversion im Nachbau: `FOREVER=1` (1.60.1), `FLAVOR=era` (1.15.7) oder `FLAVOR=tbc` (2.5.4); Sprache `LOCALE`.

## Nicht im Repo

Läufe mit echten SavedVariables oder Weltsimulation (test26, test28–test31) und die Entwickler-Erkennung (test34, test37)
enthalten Namen und laufen nur in der Arbeitsumgebung der LevelPilot-Sitzung.

## Grenzen

- Zeitmessungen (T150, T155) hängen vom Rechner ab; im Spiel gelten die Werte des Spiels.
- Ein Teil der Tests braucht den echten Client („im Client prüfen“, im Bericht gezählt).
