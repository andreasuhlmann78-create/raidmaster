# Stand Discord-Sitzung

## Stand 24.11.2026 20:58 · Bot 1.5.194 (D-CHK1 vom Supervisor 10:55 angenommen, Abnahme im Betrieb offen)

## Gerade in Arbeit
- nichts. Uploader-Versand VERSCHOBEN auf 25.11. (Nutzer 20:58: "dann morgen machen, es wird noch eine neue version kommen").
  Dann: NEUESTE Uploader-Version (VERSION in RaidMasterUploader/uploader.py auf origin) per Bot in #bot-befehle:
  /uploader an_offiziere:True UND /uploader nur_programm:True (an den Nutzer selbst). Browser nötig.

## Nächste Schritte (Reihenfolge)
1. Bei jeder Nachricht des Nutzers: git pull --rebase, auftraege/Discord/ lesen (git log --oneline -5 -- auftraege/Discord/).
2. Nach dem Update auf 1.5.194 in #bot-befehle prüfen: "✏️ … levelpilot-uebersicht-3.12.94 … vervollständigt", KEINE Zeile
   "fehlten im Discord und werden neu gepostet". Danach discord-check/status.md (läuft 35 Min. nach dem Push): erwartet grün.
3. Prüfung D-CHK1 durch den Supervisor abwarten, Befunde umsetzen. Neue Aufträge umsetzen. Sonst nichts ändern.
4. Ab Uploader 2.3.21 in #bot-befehle: "Alter Daten-Uploader (neueste 2.3.21): n PN geschickt" (D-UPALT).

## Offen beim Nutzer
- Morgen: Browser verbinden und sagen, wenn die neue Uploader-Version da ist -> dann schicke ich sie.

## Entscheide des Nutzers seit letztem Stand
- 24.11. 20:49 "das discord projekt soll den offiziere das seden" (Uploader 2.3.21); 20:51 "mir natürlich auch über den dc bot";
  20:58 "dann morgen machen, es wird noch eine neue version kommen".
- 24.11. 10:29 (D-CHK1): neueste Fassungen klären; fehlt dort etwas, entscheidet die Discord-Sitzung über Nachposten; die Prüfung
  lernt für ältere Fassungen dieselbe Regel wie der Bot; gelöscht wird nichts.
  Mein Entscheid daraus: LevelPilot-Übersicht 3.12.94 wird vervollständigt (Bearbeiten + 1 Nachricht anhängen, ohne Ping).
  raid-addon-zusammenfassung-3.0.0: nicht nachposten (Entscheid RaidMaster-Sitzung 10:30, übernommen).

## Ältere Entscheide (schon übertragen, zur Sicherheit)
- 23.11. 12:43 "Ersetzen wie bisher": neue Version ersetzt den Beitrag der vorherigen derselben Reihe.
- 24.11. 06:19: Mitglieder-Kanäle bleiben in 💬 ALLGEMEIN (Kategorie war nur zugeklappt), Bot nicht anpassen.
- 21.11.: daten_config.json per Bot an die Offiziere (1.5.187/1.5.188), am 23.11. bei allen.
- 23.11.: D-MITGL1 (Mitglied wie Raider, Gast in die 4 Kanäle, Rollen-Reihenfolge so).
- 23.11.: announce/*.md nie löschen (11:36). 33 wiederhergestellt (11:45). Alte Versionen nie wieder posten (12:03).

## Wichtig zu wissen
- Bot auf dem Infomaniak-Server, Updates automatisch von GitHub, /update geht auch. Bot-Meldungen in #bot-befehle.
- JEDER Versionswechsel startet einmalige Läufe (repair_missing_announcements, repair_truncated_announcements, Marker je Version
  in state.json). Am 24.11. 10:28 gab 1.5.193 so alte GuildSentinel-Vorstellungen frei (10:31 kurz neu gepostet) – ab 1.5.194 nur
  noch neueste Fassungen.
- Reihe/Fassung: RaidMasterBot/announce_reihe.py ist EIN Ort für Bot und discord-check/check.py ("…-N.md" = Fassung N).
- Discord im eingebauten Browser des Nutzers (sein Konto). Nur lesen, ausser auf Auftrag. Kanal öffnen: Strg+K, Name, Return.
- Verboten: #mc-dkp leeren, "Server zurücksetzen", Rolle Mitglied automatisch vergeben, config.json, uploader_config.json,
  daten_config.json oder token.txt lesen bzw. ändern, Passwörter tippen.
- Nutzung sparen: keine Wecker, kurze Berichte.
- D-UPALT: state.json "upalt_pn", "upalt_gemeldet", "uploader_geschickt"; erster Lauf mit 2.3.20 = alte Rechner gelten als informiert.
- Tests: python3 -m unittest discover -s tests (in RaidMasterBot/). Befehlsliste: tests/test_befehle_liste.py --schreiben.
