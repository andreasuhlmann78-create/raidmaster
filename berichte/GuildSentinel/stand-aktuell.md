# Stand GuildSentinel – 24.11.2026 06:41 · Version 0.9.60 (Discord; CurseForge erst nach Ingametest)

## Gerade in Arbeit
- Nichts begonnen. Neue Befunde aus dem Ingametest 0.9.60 (23.11. 13:25, offen-guildsentinel.txt Zeile ~715) sind noch NICHT umgesetzt.

## Nächste Schritte (Reihenfolge) – in EINER Version 0.9.61 bündeln (Nutzung sparen, Entscheid 23.11. 07:50)
1. GS-K1 MITTEL: T183 – GuildSentinelFrame überdeckt LevelPilotFrame -> ausweichen wie bei den anderen GoldSentinel-Fenstern; Test mit offenem LevelPilot.
2. GS-K2 MITTEL: T319 – Gruppe > Suche, Knopf "Elite-Quest (LevelPilot)" ausserhalb des Hauptfensters -> ins Fenster (Nachbau fand ihn nicht:
   LevelPilot fehlt im Nachbau -> Knopf mit geladenem LevelPilot nachbauen).
3. GS-L1 MITTEL: T311 – 9 Texte < 4,5:1 im Spiel (Mitglieder > Liste "Name (Hauptchar)" 3,7:1, Mitglieder > Wo 3,9:1, Zusammensetzung
   Klassenknöpfe z. B. "Schamane"): Klassenfarben auf dunklem Grund aufhellen oder Grund ändern bis >= 4,5:1. Nachbau zeigte das nicht
   (Testgilde ohne diese Klassen/Farben) -> Nachbau mit allen Klassenfarben ergänzen.
4. GS-L5 NIEDRIG: T317 – 8 Tooltips Brett > Angebot/Gesuch ("Runenstoff (passt!)", erste Zahl Zeile 3 von 12): Menge/Preis in Zeile 1–2.
5. GS-P1 NIEDRIG: Leistung – längstes Bild 25,8 ms (T269), 15 Bilder > 16 ms; Ursache je Prüfung nennen (T269, T09, T21–T22, T295g),
   Spielbetrieb betroffen ja/nein. Speicher der Prüfungen >= 17 191 KB (grösste T61 1 438 KB) – erklären.
6. Danach: RP/RV im Client bestätigen (Nutzer), CH-G (später, nach AHSentinel).

## Offen beim Nutzer
- Ingametest 0.9.60 erledigt (OK 335, FEHLER 4 = GS-K1/K2/L1/L5). Nach 0.9.61 neuer Ingametest; erst dann CurseForge (Supervisor 09:27).
- Platzhalter-Knopf und gewählte Zeile am Bild; "LANGSAM Seite members" > 16 ms im /gs protokoll (G-4a gilt erst dann als erledigt).

## Entscheide des Nutzers seit letztem Stand
- 23.11. 11:36: In announce/ NICHTS löschen (kein git rm/Umbenennen) – neue Datei dazu, alte bleibt. Eigene Skripte angepasst
  (publish_discord.sh/publish.sh im Arbeitsordner: kein git rm in announce/ mehr). download/ wie bisher.
- 23.11. 12:03: Alte Addon-Versionen nie wieder posten – gelöschte alte Ankündigungen NICHT wiederherstellen.
- 23.11. 12:43: Im Discord ersetzt eine neue Version weiterhin den Beitrag der vorherigen (macht der Bot) – Verbot gilt nur Dateien in announce/.
- 23.11. 09:27/09:46 (Supervisor): 0.9.59 und 0.9.60 angenommen (erledigt nach Ingametest); L7 nicht anwendbar; L5 = T317 für jeden Tooltip mit Zahlen.

## Wichtig zu wissen
- Veröffentlichen: Skript im Arbeitsordner geht beim Zusammenfassen evtl. verloren. Ablauf: cmp shared/ (7 Dateien), Zip bauen, GS-Repo
  committen+pushen, addon_check (kein FEHLER, Zeile "luac5.1"), announce/guildsentinel__guildsentinel-<V>.md + .GuildSentinel.zip DAZULEGEN
  (nichts löschen), Bericht berichte/GuildSentinel/<Zeit>-<thema>.txt, stand-aktuell.md, push, Ankunft mit git show origin/main prüfen.
- Gildenschlüssel "@Fraktion|Gilde"; alte Daten in guildsOld. RaidReady: < 3 Spieler oder < 7 Tage -> keine Wochenzahl.
- Prüfung "return nil, Grund" = SKIP. Testroutine misst zuerst 10 s Umgebung (Offline-Tests: 10 s mehr vorrücken).
- Offline: test/run_alle.sh 229 Läufe, 16947 Einzelprüfungen (RO=1 = Abgleich Lauf für Lauf; letzte Liste nur im Arbeitsordner).
- Locales: tools/loc/new/v0XXX.py + tools/en7.py + python3 tools/en.py + tools/loc/check.py <loc>; Beschriftungen <= 28 Zeichen.
