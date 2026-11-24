# Stand Discord-Sitzung

## Stand 24.11.2026 10:11 · Bot 1.5.193 (D-UPALT umgesetzt, zur Prüfung; 1.5.192 am 23.11. 12:43 angenommen)

## Gerade in Arbeit
- nichts. D-UPALT (PN bei veraltetem Daten-Uploader) in 1.5.193 umgesetzt, Bericht berichte/Discord/2026-11-24-1011-d-upalt.txt.

## Nächste Schritte (Reihenfolge)
1. Bei jeder Nachricht des Nutzers: git pull --rebase, auftraege/Discord/ lesen (git log --oneline -5 -- auftraege/Discord/).
2. Prüfung D-UPALT durch den Supervisor abwarten, Befunde umsetzen. Neue Aufträge umsetzen. Sonst nichts ändern.
3. Ab Uploader 2.3.21 in #bot-log nachsehen: "Alter Daten-Uploader (neueste 2.3.21): n PN geschickt".

## Offen beim Nutzer
- nichts.

## Entscheide des Nutzers seit letztem Stand
- 23.11. 12:43: "Ersetzen wie bisher" – beim Posten einer neuen Version löscht der Bot den Beitrag der vorherigen Version derselben
  Reihe (je Addon steht nur die aktuelle). Nichts ändern. (Steht schon in offen-discord.txt.)
- 24.11. 06:19: Mitglieder-Kanäle bleiben in 💬 ALLGEMEIN. Nicht ohne Kategorie nach oben verschieben, Bot nicht anpassen.
  Hintergrund: Die Kanäle "verschwanden" nicht. Die Kategorie war nur in der Ansicht des Nutzers zugeklappt (das gilt je Mitglied;
  Discord kann Zuklappen nicht verbieten). Belegt im Browser am 24.11. 06:15: alle 4 Kanäle da, keine Lösch-Meldung in #bot-befehle.

## Ältere Entscheide (schon übertragen, zur Sicherheit)
- 21.11.: daten_config.json per Bot an die Offiziere (1.5.187/1.5.188). Am 23.11. bei allen Offizieren ("Keine Empfänger").
- 23.11.: Mitglieder-Kanäle D-MITGL1. Rolle Mitglied wie Raider. Gast (PUG) darf in die 4 Kanäle. Rollen-Reihenfolge so belassen
  (Raidleitung = Nutzer, über dem Bot).
- 23.11.: announce/*.md nie löschen (11:36). 33 Dateien wiederhergestellt (11:45). Alte Versionen nie wieder posten,
  die 9 vor 11:36 gelöschten bleiben weg (12:03).

## Wichtig zu wissen
- Der Bot läuft auf dem Infomaniak-Server. Updates kommen automatisch von GitHub, /update geht auch.
  Bot-Meldungen stehen in #bot-befehle.
- Discord ist im eingebauten Browser des Nutzers erreichbar (sein Konto, eingeloggt). Nur lesen, ausser auf Auftrag.
  Drag-and-drop geht nicht. Slash-Befehle: tippen, Return, Return.
- Verboten: #mc-dkp leeren, "Server zurücksetzen", Rolle Mitglied automatisch vergeben, config.json, uploader_config.json,
  daten_config.json oder token.txt lesen bzw. ändern, Passwörter tippen.
- Nutzung sparen: keine Wecker, kurze Berichte.
- D-UPALT: state.json "upalt_pn" (Rechner->Version), "upalt_gemeldet", "uploader_geschickt" (Mitglied->Version).
  Erster Lauf mit 2.3.20 = alle alten Rechner gelten als informiert (Offiziere 08:37 beliefert).
- Klon ist flach: für alte Dateien zuerst git fetch --unshallow.
- Tests: python3 -m unittest discover -s tests (in RaidMasterBot/). Befehlsliste: tests/test_befehle_liste.py --schreiben.
