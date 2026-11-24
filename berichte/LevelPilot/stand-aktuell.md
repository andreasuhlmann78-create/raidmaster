# LevelPilot – Stand der Sitzung

## Stand 24.11.2026 06:40 · Version 3.13.11 (veröffentlicht, Discord, md5 10a6f286289957654611767f4a6392ce)

## Gerade in Arbeit
- Nichts angefangen. 3.13.11 gepusht 23.11. 16:29, Bericht berichte/LevelPilot/2026-11-23-1629-3.13.11-lp-i1-i5.txt (umgesetzt, zur Prüfung).
- Prüfung von 3.13.11 durch die Prüf-Sitzung steht aus (offen-levelpilot.txt beobachten).

## Nächste Schritte (Reihenfolge)
1. LP-I3 MITTEL (noch nicht angefasst): T150 Replan Median 16,84 ms (ersterweg 7,6), T155 Spitzen je Reiseschritt (#3 207 ms Stufe 30 Zone 1456
   +2858 KB), T263 erste Messung im Spiel 45 ms / 1153 KB. Zuerst mit den Daten von MININT-M6UO3AL nachstellen, nicht schätzen.
2. LP-I1 Rest:
   - erster Zufallsfall der Grundregeln 55,5 ms im Nachbau (Verdacht: Ereignis-Handler QUEST_COMPLETE im Ersatz);
   - Start 112,6 ms im Spiel (Verdacht: Keys() grosser Tabellen in CopyP am Stück);
   - Nachbau-Stücke 25–38 ms (T265, T266, T348, T296, T260, T33, T128) – im Spiel Faktor 3–7.
3. LP-I1 T136 advisor–T144 (715 ms) und T271–T275: im Nachbau nicht nachstellbar. Beleg kommt mit dem nächsten Ingametest über die neuen
   Berichtsfelder "bilder40" / "stuecke".
4. LP-I2: im nächsten Ingametest T261 und Feld "einloggen" prüfen. Erwartet etwa 975 ms (die doppelt gezählte Neuplanung fällt weg), noch nicht
   gemessen. Verdacht, zu messen: weitere ineinander liegende Messungen (nav/path).
5. LP-K1 NIEDRIG (Hinweis 23.11. 13:26): weicht LevelPilot den anderen GoldSentinel-Fenstern aus? Test mit offenem GuildSentinel-/BuffSentinel-Fenster.
6. Hinweis Blueposts 24.11. 06:15 (BP-2026-11-23-4, kein Auftrag): prüfen, ob LevelPilot das Reittempo aus der Reitfertigkeit ableitet; falls ja,
   bis zum Fix von Blizzard das gemessene Tempo nehmen.
7. Notbremse "Routenberechnung" 22.11. 17:05: beim nächsten Upload des Nutzers auswerten.
8. Zeile "Wegabschnitte": nach einer Spielsitzung mit Laufen (3.13.10 in der Stadt: aufgezeichnet 0, erwartet).

## Offen beim Nutzer
- Ingametest 3.13.11 (wichtig: Felder bilder40, stuecke, einloggen im Bericht; T221, T372, T384).
- Entscheid T31/T32 (einmal neu planen) – gefragt, keine Antwort.

## Entscheide des Nutzers seit letztem Stand
- 23.11. 16:00: Erst laufende Arbeit fertig machen, dann LP-I1 bis LP-I5 (Ingametest 3.13.10).
- 24.11. 06:39: Vor dem Zusammenfassen des Kontexts stand-aktuell.md ganz neu schreiben, committen, pushen, Ankunft prüfen.
- Gelten weiter: immer Deutsch (23.11. 08:36); in announce/ nichts löschen (23.11. 11:36); komplette Dateien bei Code-Änderungen.

## Wichtig zu wissen
- Ingametest 3.13.10 stammt aus der Ablage von MININT-M6UO3AL (goldsentinel-daten, konto-36a99f17), nicht vom Laptop.
  Nachbau: SVACC=/home/claude/goldsentinel-daten/aktuell/MININT-M6UO3AL/forever/konto-36a99f17/LevelPilot.lua.
- Skripte im Scratchpad (bei Neustart weg, dann neu bauen):
  - m.sh: ganze Routine mit diesen Daten in Donnerfels (Karte 1456, Stufe 30, echte Kartenrahmen).
  - dbg_wege.lua: Wegdaten-Versände; dbg_login.lua: Einloggen mit ASYNC=1, Aufträge wie im Spiel.
- Arbeitskopie /home/claude/lp31238/{LevelPilot,LevelPilot_Data} = 3.13.11. Nach einem Container-Neustart aus dem Zip in announce/ neu aufbauen.
- Lua 5.1 über lupa, Wrapper scratchpad/lua51. Nachbau immer mit BRAKE=1. Ersatzwelt hat keine Kontinente: echte Kartenrahmen für T84/T372.
- Ergebnis-Zeilen werden im Bericht nach 300 Zeichen gekürzt; Tabellen (bilder40, stuecke, einloggen) nicht.
- 3.13.11 neu:
  - P:Replan ohne Klick in einem anderen Auftrag -> eigener Auftrag im nächsten Bild (T384).
  - Graph.EdgeKeys/edgeGen; WegeExport teilt zu grosse Zonen (Zone 1420 der PC-Daten 216 565 Zeichen > 200 704).
- T353 "Abgabe nicht möglich" ist eine absichtliche Gegenprobe.
- Offline: run_offline.py 40 Läufe + --nur testroutine 5 Formen, beide 0 FEHLER bei 3.13.11.
