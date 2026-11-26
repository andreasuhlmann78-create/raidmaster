# Stand Discord-Sitzung

## Stand 26.11.2026 13:10 · Bot 1.5.198 (/addon-pn umgesetzt, zur Prüfung; 1.5.197 angenommen)

## Gerade in Arbeit
- Sobald 1.5.198 läuft: für den Nutzer /addon-pn an:False (Wunsch 26.11. 12:59, keine PN bei neuer RaidMaster-Version).

## Nächste Schritte (Reihenfolge)
1. Bei jeder Nachricht des Nutzers: git pull --rebase, auftraege/Discord/ lesen (git log --oneline -5 -- auftraege/Discord/).
2. D-CI2 im Betrieb gemessen 15:08: Paket 13:51:00 UTC -> Lauf workflow_dispatch 13:51:02 -> Commit 13:51 (Bericht 2026-11-25-1508).
3. Prüfung des Supervisors abwarten, Befunde umsetzen. Neue Aufträge umsetzen. Sonst nichts ändern.

## Offen beim Nutzer
- nichts. Token "github_actions_token" hat der Nutzer 25.11. 14:43 selbst auf dem Server eingetragen (Bot lief da 1.5.197).

## Entscheide des Nutzers seit letztem Stand
- 26.11. 12:59 "der dc bot braucht mir die neuste version vom raidmaster addon nicht mehr zu senden via pm im dc" -> /addon-pn.
- 25.11. ~13:50 (RaidMaster-Sitzung, via Supervisor D-CI2): Bot stösst den Testberichte-Workflow an, Token trägt der Nutzer ein.
- 25.11. 11:39 (via Supervisor D-UPDOC2): Offiziere schalten Addons-automatisch-an.bat ein; Schritt in Anleitung und /uploader.
- 24.11. 21:53 "ich sende ihn denen selber" (Uploader an Offiziere und sich selbst, über die Bot-Befehle).
- 25.11. 08:29 (via Supervisor, D-RAID1): "mc" in forever_raids.json bleibt "forever": true (Entscheid des Nutzers). Nichts ändern.
- 24.11. 20:49 "das discord projekt soll den offiziere das seden" (Uploader 2.3.21); 20:51 "mir natürlich auch über den dc bot";
  20:58 "dann morgen machen, es wird noch eine neue version kommen"; 21:11 "nuester uploader senden bitte"; 21:44 "rm ist ready" (= UP-UPD1 fertig).
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
- config.json: save_config behält ab 1.5.197 vom Nutzer neu eingetragene Schlüssel.
- D-UPALT/D-UPMIN1: nötige Version = max(mindestversion.txt, 2.3.23) ab neueste 2.3.23; state.json "upalt_pn", "upalt_gemeldet", "uploader_geschickt"; erster Lauf mit 2.3.20 = alte Rechner gelten als informiert.
- Tests: python3 -m unittest discover -s tests (in RaidMasterBot/). Befehlsliste: tests/test_befehle_liste.py --schreiben.
