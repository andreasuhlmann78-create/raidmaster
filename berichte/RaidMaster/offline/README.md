# RaidMaster – Nachbildung für die Testroutine (offline, ohne Spiel)

Lässt die eingebaute Testroutine von RaidMaster (`/rm testroutine`, Test/Routine.lua) ausserhalb von WoW laufen.
Nur zum Testen – nicht Teil der Addon-ZIP. Alle Namen in der Nachbildung sind erfunden (Testa, Bob, Cleo, Offi, Echt1).

## Aufruf (aus diesem Ordner, Lua 5.1)

    lua run_routine.lua                          # Forever (TOC 16001), deutsch, alle Bereiche
    TOC=11509 lua run_routine.lua                # Classic Era
    lua -e "GAMELOCALE='zhCN'" run_routine.lua   # andere Spielsprache (deDE, enUS, frFR, esES, esMX, itIT, ptBR, ruRU, koKR, zhCN, zhTW)
    AREA=F lua run_routine.lua                   # nur ein Bereich der Routine
    SHOWALL=1 lua run_routine.lua                # jede Prüfung mit Ergebnis ausgeben
    EMU=T114 lua run_routine.lua                 # Prüfungen, deren Fehler nur an der Nachbildung liegt, nicht zählen

Umgebung: `ADDONDIR` (Standard `../../../RaidMaster`), `HARNESS` (Standard `harness.lua`).
Erwartet am Ende: `ALLE OK` (keine FEHLER, Sandbox OK, keine echte Blizzard-Aktion, Testmodus beendet).

## Wichtig (T90, 15.11.2026)
Die Dateien werden in der Reihenfolge von RaidMaster.toc geladen – wie im Spiel. Bis 15.11. fügte die Nachbildung die
Sprachdateien vor Locale.lua ein; dann war RM.LOCALE noch nil und keine Übersetzung wurde geladen (T90 "609:" unter enUS).

## T207 (ab 3.0.48, RM-TAINT1)
`blizzard_fenster.lua` durchsucht alle .lua-Dateien unter ADDONDIR (auch Test/) nach Aufrufen, die Blizzard-Fenster öffnen oder
schliessen (ToggleCharacter, ShowUIPanel, HideUIPanel, …; Kommentare, Zeichenketten und Methoden ausgenommen). Ein Fund ist FAIL.
Gegenprobe im Lauf: eingefügte Aufrufe werden erkannt.

## Grenzen
Zeitmessungen (z. B. T114 Serializer ≤ 16 ms) hängen von der Rechnerlast ab und können vereinzelt ausschlagen –
dann wiederholen. Im Spiel gelten die Werte aus dem Client.
