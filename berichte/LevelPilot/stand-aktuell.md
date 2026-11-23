# LevelPilot – Stand der Sitzung

## Stand 23.11.2026 16:29 · Version 3.13.11 (veröffentlicht, Discord)

## Gerade in Arbeit
- 3.13.11 gepusht (LP-I1 Teil, LP-I2, LP-I4, LP-I5). Bericht: berichte/LevelPilot/2026-11-23-1629-3.13.11-lp-i1-i5.txt.

## Nächste Schritte (Reihenfolge)
1. LP-I3: T150 ersterweg, T155 Spitzen je Reiseschritt, T263 erste Messung im Spiel – mit den Daten von MININT-M6UO3AL nachstellen.
2. LP-I1 Rest: erster Fall der Grundregeln (55 ms im Nachbau), Start (Keys() der Sicherung), Stücke 25–38 ms (T265/T266/T348/T296/T260).
3. Nächster Ingametest: Felder "bilder40", "stuecke", "einloggen" auswerten (T136–T144, T271–T275 belegen).
4. Notbremse "Routenberechnung" 22.11. 17:05 beim nächsten Upload auswerten.
5. Zeile "Wegabschnitte" nach einer Spielsitzung mit Laufen.
6. LP-K1 NIEDRIG (Hinweis 13:26): weicht LevelPilot den anderen GoldSentinel-Fenstern aus? Prüfen, Test mit offenem GS/BS-Fenster.

## Offen beim Nutzer
- Ingametest 3.13.11.
- Entscheid T31/T32 (einmal neu planen) – gefragt, keine Antwort.

## Entscheide des Nutzers seit letztem Stand
- 23.11. 16:00: Erst laufende Arbeit fertig machen, dann LP-I1..I5 (Auftrag der Prüf-Sitzung).

## Wichtig zu wissen
- Ingametest 3.13.10 stammt aus der Ablage von MININT-M6UO3AL (konto-36a99f17), nicht vom Laptop. Nachbau damit: SVACC=…/MININT-M6UO3AL/…
- Skript scratchpad/m.sh = ganze Routine mit diesen Daten in Donnerfels (Karte 1456, Stufe 30, echte Kartenrahmen).
- Arbeitskopie /home/claude/lp31238/{LevelPilot,LevelPilot_Data}; nach Container-Neustart aus dem Zip in announce/ neu aufbauen.
- Lua 5.1 über lupa, Wrapper scratchpad/lua51. Nachbau immer mit BRAKE=1. ASYNC=1 = Aufträge in Portionen wie im Spiel (Einloggen messen).
- Im Bericht (Tabellen werden nicht gekürzt): bilder40 = Bilder über 40 ms nach Prüfungen, stuecke = längstes Stück je Prüfung, einloggen = T261 ungekürzt.
- Zone 1420 der PC-Daten ist allein grösser als ein Wegdaten-Bericht – Teilen nötig (3.13.11).
