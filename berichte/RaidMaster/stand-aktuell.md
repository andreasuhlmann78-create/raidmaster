# Stand RaidMaster-Sitzung

## Stand 24.11.2026 06:42 · Addon 3.0.40 · Uploader 2.3.19
- Addon 3.0.40 im Spiel ohne Fehler (Ingametest 18.11.), vom Ingametest befreit (Entscheid 18.11. 15:19).
- Uploader 2.3.16 / 2.3.17 / 2.3.18 gepusht, Berichte 2026-11-23-1238 / -1413 / -1517 – zur Prüfung.
- UP-TAGE (Befund HOCH 24.11. 06:16): Ursache belegt (200-MB-Grenze, Platz für 3 Tage), Bericht 2026-11-24-0620-up-tage-analyse.
- Uploader 2.3.19 (UP-TAGE, Entscheid 24.11. 06:26): alles gepackt .lua.gz, 30 Tage, 1 GB, MAX_FILE gepackt 50 MB / ungepackt
  400 MB, abgelehnte Datei nach 30 Min. neu, fremde GuildSentinel.lua.gz gefiltert. Bericht 2026-11-24-0635 – zur Prüfung.
- 24.11. 06:41: Bot hat 2.3.19 per PN an den Nutzer und an 2 von 2 Offizieren geschickt (/uploader im eingebauten Browser).

## Gerade in Arbeit
- nichts (2.3.19 gepusht und verschickt; wartet auf Prüfung und Verteilung auf alle Rechner)

## Nächste Schritte (Reihenfolge)
1. Nach Meldung des Nutzers "alle Rechner umgestellt": Daten-Repo (goldsentinel-daten, nur lokal) prüfen – stand.json
   "uploader" 2.3.19 bei allen 4 Rechnern, Feld "tage", nur .lua.gz in aktuell/ – und im Bericht melden.
2. Addon 3.0.41 – offene Punkte aus offen-raidmaster.txt gebündelt (Nutzung sparen, eine Version):
   - GoldSentinelSync 3 kopieren (Vorprüfung 18.11.: gleiche Zahlen, kein testLearn nötig), GoldSentinelMarkt v3 kopieren
   - Befund 19.11. Platzhalter-Liste Werbung (Pages.lua ~1097) -> "?" mit Tooltip
   - Entscheid 19.11. 09:06: Dev-Befehle nur im Entwicklermodus sichtbar (Hilfe, Befehlsliste, Tooltips), Test mit Gegenprobe
   - Hinweis 20.11.: Test ändert nie Livedaten; Hinweis 20.11.: Lesbarkeit L1–L8 der Testroutine
   - Hinweis 21.11.: Schätzen verboten; Prüfauftrag 21.11. 16:30 Realm-Schlüssel (grep GetRealmName, Bericht)
   - Takt 2 nur falls genutzt (RaidMaster nutzt Takt nicht – im Bericht belegen)
3. Danach Ingametest-Runde (neue Version) und Bericht.

## Offen beim Nutzer
- Uploader 2.3.19 auf JEDEM liefernden Rechner (stand.json nennt 4) ganz entpacken + neu starten; Offiziere ebenso.
  Sonst kürzt ein alter Uploader die Tages-Stände wieder auf 7 Tage (3 Rechner liefern noch ohne "uploader"-Feld = vor 2.3.15).
  Erwartet im Fenster: "Prüfung: geliefert (… gepackt … statt …, Repo …, n Tag(e) von höchstens 30)".
- Melden, wenn alle Rechner umgestellt sind (dann Prüfung Schritt 1).
- Bot-Auftrag Bewerbungen aufräumen (23.11. 15:57) liegt beim Discord-Projekt (Weiterleitung 2026-11-23-1558) – hier nichts zu tun.

## Entscheide des Nutzers seit letztem Stand
- 24.11. 06:26: "ja bau das so um aber mache keine fehler" – Uploader liefert alles gepackt (.lua.gz), Grenze 1 GB, 30 Tage.
- 24.11. 06:40: "ja bitte" – Uploader 2.3.19 per Bot an ihn (PN) und an die Offiziere schicken (erledigt 06:41).
- 24.11. 06:42: Stand vor Zusammenfassen des Kontexts vollständig in diese Datei sichern.

## Wichtig zu wissen
- Leser des Daten-Repos müssen .lua UND .lua.gz lesen; addon-check/marktanalyse/de_ketten_lehrer.py liest festen .lua-Pfad
  (im Bericht 2026-11-24-0635 an den Supervisor gemeldet; addon-check/ ändert nur der Supervisor).
- Uploader: RaidMasterUploader/ (Tests: tests/test_daten 39, test_sync 53, test_uploader 23, test_umfassend 14 – alle grün).
  ZIP download/RaidMasterUploader.zip (13 Dateien, ohne tests/); der Bot holt sie aus raw HEAD.
- Bot-Versand: #gildenbank, /uploader nur_programm:True (an mich) bzw. an_offiziere:True; eingebauter Browser auf 1280x900,
  danach zurück auf desktop. Nutzer loggt sich selbst ein.
- Arbeitskopie Addon: Repo-Ordner RaidMaster/. Nachbau: berichte/RaidMaster/offline (run_routine.lua).
- Echte Daten nur lokal lesen (goldsentinel-daten), nie Namen in Repo/Berichte.
- Discord-Updates in RaidMasterBot/raid_addon_intro.md ≤ ~1990 Zeichen.
