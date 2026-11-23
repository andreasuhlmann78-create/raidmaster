# Stand Discord-Sitzung

## Stand 23.11.2026 11:56 · Bot 1.5.191 (origin/main, CI grün, im Server installiert 11:52)

## Gerade in Arbeit
- nichts – D-MITGL1 umgesetzt, zur Prüfung (Bericht 2026-11-23-0926-bot-1.5.189-mitglieder-kanaele.txt).

## Nächste Schritte (Reihenfolge)
1. Nach /update auf dem Server: #bot-log-Meldung zu den Mitglieder-Kanälen abwarten (Rechte/Rollen-Reihenfolge), Supervisor prüft.
2. (entfällt: Rolle Mitglied vom Nutzer 09:50 bestätigt, schon so umgesetzt)
3. Versand daten_config.json (1.5.187/1.5.188): erfolgt durch den Nutzer bzw. seine Sitzung mit Discord-Zugang; Anzahl melden.

## Offen beim Nutzer
- daten_config.json: schon bei allen Offizieren (Bot 11:34 "Keine Empfänger"), nichts zu tun.
- D-MITGL1-R: Nutzer hat Bot-Rolle selbst gezogen (unter Raidleitung, über Offizier) – so belassen. Nächster Start: #bot-log
  soll nur noch "Rollen über dem Bot: Raidleitung" melden.
- /update auf 1.5.189 und ggf. Bot-Rolle (Rechte/Reihenfolge) nach #bot-log-Meldung anpassen.
- /uploader-daten-senden datei:<daten_config.json> (nur Gildenchef, "Senden" nach Liste).

## Entscheide des Nutzers seit letztem Stand
- 21.11. 07:39/07:40: daten_config.json per Bot an die Offiziere (umgesetzt 1.5.187, Datei im Befehl 1.5.188).
- 21.11. 08:05: Eine Claude-Sitzung des Nutzers bedient Discord und gibt dem Bot den Befehl.
- 23.11. 09:16/09:18/09:20: D-MITGL1 Mitglieder-Kanäle, Rechte je Rolle, Bot = Rechte des Gildenchefs.
- 23.11. 09:50: Rolle Mitglied wie Raider – JA (so in 1.5.189).
- 23.11. 09:59: D-MITGL1-R selbst machen, sehr vorsichtig (Regeln 1–7 in offen-discord.txt).
- 23.11. 10:16: Gast (PUG) darf in die 4 Mitglieder-Kanäle – so lassen.
- 23.11. 10:32: Rollen-Reihenfolge so belassen (Raidleitung über Bot und Offizier; Raidleitung = Nutzer).
- 23.11. 11:36: Ankündigungen (announce/*.md) im Repo nicht mehr löschen – an Supervisor gemeldet (Bericht 11:36).
- 23.11. 11:45: die gelöschten Ankündigungen wiederherstellen – erledigt: 33 Dateien (Bot 1.5.191), keine Discord-Beiträge gelöscht.

## Wichtig zu wissen
- Klon war flach: für alte Dateien zuerst git fetch --unshallow. post_bot_log kürzt bei 1990 Zeichen (Vorschlag: aufteilen).
- 1.5.190: Anpinnen-Recht und Warntext umgesetzt; Bot meldete 10:42 je Kanal 3 Rechte gesetzt, Warnung nur Raidleitung.
- /update kann die Sitzung selbst im eingebauten Browser (Konto des Nutzers, #bot-befehle) – Bot-Meldungen stehen dort.
- Bot läuft auf dem Infomaniak-Server, nicht auf dem PC des Nutzers; diese Sitzung hat keinen Zugriff auf Server/Discord.
- Nutzung sparen gilt (Supervisor 23.11. 07:50): keine Wecker, kurze Berichte.
- Werkzeuge im Scratchpad (betrieb.sh, befehle_dump.py) gehen beim Neustart verloren – Ablauf steht in den Berichten.
