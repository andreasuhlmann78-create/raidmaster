# Stand Discord-Sitzung

## Stand 24.11.2026 21:50 · Bot 1.5.196 (D-UPD1 umgesetzt, zur Prüfung; 1.5.195 angenommen)

## Gerade in Arbeit
- Uploader 2.3.24 (erste mit Rückfrage j/n, einmal von Hand) per Bot schicken (Nutzer 21:11 "nuester uploader senden bitte"; D-UPMIN1): in #bot-befehle
  /uploader an_offiziere:True UND /uploader nur_programm:True (für den Nutzer). WARTET: kein Browser verbunden (21:11, 21:36, 21:50).

## Nächste Schritte (Reihenfolge)
1. Bei jeder Nachricht des Nutzers: git pull --rebase, auftraege/Discord/ lesen (git log --oneline -5 -- auftraege/Discord/).
2. Browser da -> sofort den Versand oben (vorher VERSION in RaidMasterUploader/uploader.py prüfen = neueste).
3. Prüfung D-UPD1 (Bericht 2026-11-24-2150-d-upd1.txt) abwarten, Befunde umsetzen.
4. Abnahme D-CHK1 im Betrieb (Supervisor 10:55): "✏️ … 3.12.94 … vervollständigt" in #bot-befehle, status.md grün (19:27 grün),
   beim nächsten Versionswechsel keine alte Fassung gepostet -> Bericht nachreichen.

## Offen beim Nutzer
- Browser verbinden (eingebauter Browser der Desktop-App oder Claude in Chrome) für den Uploader-Versand.

## Entscheide des Nutzers seit letztem Stand
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
- D-UPALT/D-UPMIN1: nötige Version = max(mindestversion.txt, 2.3.23) ab neueste 2.3.23; state.json "upalt_pn", "upalt_gemeldet", "uploader_geschickt"; erster Lauf mit 2.3.20 = alte Rechner gelten als informiert.
- Tests: python3 -m unittest discover -s tests (in RaidMasterBot/). Befehlsliste: tests/test_befehle_liste.py --schreiben.
