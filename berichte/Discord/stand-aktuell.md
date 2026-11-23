# Stand Discord-Sitzung

## Stand 23.11.2026 10:00 · Bot 1.5.189 (origin/main, CI grün; Code vom Supervisor angenommen 09:49)

## Gerade in Arbeit
- nichts – D-MITGL1 umgesetzt, zur Prüfung (Bericht 2026-11-23-0926-bot-1.5.189-mitglieder-kanaele.txt).

## Nächste Schritte (Reihenfolge)
1. Nach /update auf dem Server: #bot-log-Meldung zu den Mitglieder-Kanälen abwarten (Rechte/Rollen-Reihenfolge), Supervisor prüft.
2. (entfällt: Rolle Mitglied vom Nutzer 09:50 bestätigt, schon so umgesetzt)
3. Versand daten_config.json (1.5.187/1.5.188): erfolgt durch den Nutzer bzw. seine Sitzung mit Discord-Zugang; Anzahl melden.

## Offen beim Nutzer
- D-MITGL1-R: Bot-Rolle über Mitglied/Raider/Gast/Raidleitung/Offizier – nicht ausgeführt: Discord im Browser nicht angemeldet
  (Anmelden darf die Sitzung nicht). Nutzer meldet sich an oder zieht die Rolle selbst.
- /update auf 1.5.189 und ggf. Bot-Rolle (Rechte/Reihenfolge) nach #bot-log-Meldung anpassen.
- /uploader-daten-senden datei:<daten_config.json> (nur Gildenchef, "Senden" nach Liste).

## Entscheide des Nutzers seit letztem Stand
- 21.11. 07:39/07:40: daten_config.json per Bot an die Offiziere (umgesetzt 1.5.187, Datei im Befehl 1.5.188).
- 21.11. 08:05: Eine Claude-Sitzung des Nutzers bedient Discord und gibt dem Bot den Befehl.
- 23.11. 09:16/09:18/09:20: D-MITGL1 Mitglieder-Kanäle, Rechte je Rolle, Bot = Rechte des Gildenchefs.
- 23.11. 09:50: Rolle Mitglied wie Raider – JA (so in 1.5.189).
- 23.11. 09:59: D-MITGL1-R selbst machen, sehr vorsichtig (Regeln 1–7 in offen-discord.txt).

## Wichtig zu wissen
- Bot läuft auf dem Infomaniak-Server, nicht auf dem PC des Nutzers; diese Sitzung hat keinen Zugriff auf Server/Discord.
- Nutzung sparen gilt (Supervisor 23.11. 07:50): keine Wecker, kurze Berichte.
- Werkzeuge im Scratchpad (betrieb.sh, befehle_dump.py) gehen beim Neustart verloren – Ablauf steht in den Berichten.
