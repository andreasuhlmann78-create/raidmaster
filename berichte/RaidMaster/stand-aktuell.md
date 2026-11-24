# Stand RaidMaster-Sitzung

## Stand 24.11.2026 06:36 · Addon 3.0.40 · Uploader 2.3.19
- Addon 3.0.40 im Spiel ohne Fehler (Ingametest 18.11.), vom Ingametest befreit (Entscheid 18.11. 15:19).
- Uploader 2.3.16 / 2.3.17 / 2.3.18 gepusht, Berichte 2026-11-23-1238 / -1413 / -1517 – zur Prüfung.
- UP-TAGE (Befund HOCH 24.11. 06:16): Ursache belegt (200-MB-Grenze, Platz für 3 Tage), Bericht 2026-11-24-0620-up-tage-analyse.
- Uploader 2.3.19 (UP-TAGE, Entscheid 24.11. 06:26): alles gepackt .lua.gz, 30 Tage, 1 GB, MAX_FILE gepackt 50 MB / ungepackt
  400 MB, abgelehnte Datei nach 30 Min. neu, fremde GuildSentinel.lua.gz gefiltert. Bericht 2026-11-24-0635 – zur Prüfung.

## Gerade in Arbeit
- nichts (2.3.19 gepusht; wartet auf Prüfung und Verteilung an alle 4 Rechner)

## Nächste Schritte (Reihenfolge)
1. Nutzer: 2.3.19 auf alle Rechner (Bot /uploader an ihn per PN und an die Offiziere, wenn er will).
2. Nach Verteilung: Daten-Repo prüfen (stand.json "uploader" 2.3.19 bei allen, "tage", nur .lua.gz) und im Bericht melden.
3. Addon 3.0.41 – offene Punkte aus offen-raidmaster.txt gebündelt (Nutzung sparen, eine Version):
   - GoldSentinelSync 3 kopieren (Vorprüfung 18.11.: gleiche Zahlen, kein testLearn nötig), GoldSentinelMarkt v3 kopieren
   - Befund 19.11. Platzhalter-Liste Werbung (Pages.lua ~1097) -> "?" mit Tooltip
   - Entscheid 19.11. 09:06: Dev-Befehle nur im Entwicklermodus sichtbar (Hilfe, Befehlsliste, Tooltips), Test mit Gegenprobe
   - Hinweis 20.11.: Test ändert nie Livedaten; Hinweis 20.11.: Lesbarkeit L1–L8 der Testroutine
   - Hinweis 21.11.: Schätzen verboten; Prüfauftrag 21.11. 16:30 Realm-Schlüssel (grep GetRealmName, Bericht)
   - Takt 2 nur falls genutzt (RaidMaster nutzt Takt nicht – im Bericht belegen)
4. Danach Ingametest-Runde (neue Version) und Bericht.

## Offen beim Nutzer
- Uploader 2.3.19 auf JEDEM liefernden Rechner entpacken + neu starten (sonst kürzt ein alter Uploader wieder auf 7 Tage;
  3 Rechner liefern noch ohne "uploader"-Feld = vor 2.3.15).
- Versand 23.11. 15:10: Bot schickte 2.3.17 an Nutzer und 2 Offiziere (inzwischen überholt durch 2.3.19).

## Entscheide des Nutzers seit letztem Stand
- 24.11. 06:26: "ja bau das so um aber mache keine fehler" – Uploader liefert alles gepackt (.lua.gz), Grenze 1 GB, 30 Tage.

## Wichtig zu wissen
- Leser des Daten-Repos müssen .lua UND .lua.gz lesen; de_ketten_lehrer.py liest festen .lua-Pfad (an Supervisor gemeldet).
- Arbeitskopie Addon: Repo-Ordner RaidMaster/. Uploader: RaidMasterUploader/ (Tests: tests/test_daten|sync|uploader|umfassend).
- Nachbau: berichte/RaidMaster/offline (run_routine.lua: SHOWID, Gegenproben OPT*/PLAYERLEADER/NOPANEL/CMDDEV/SYNCPOKE, Sync-Zählung).
- Echte Daten nur lokal lesen (goldsentinel-daten), nie Namen in Repo/Berichte.
- Discord-Updates in RaidMasterBot/raid_addon_intro.md ≤ ~1990 Zeichen.
