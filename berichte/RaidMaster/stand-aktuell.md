# Stand RaidMaster-Sitzung

## Stand 23.11.2026 08:35 · Addon 3.0.40 · Uploader 2.3.15
- Addon 3.0.40 im Spiel ohne Fehler (Ingametest 18.11.), vom Ingametest befreit (Entscheid 18.11. 15:19).
- Uploader 2.3.15 (UP-DS2 HOCH) gepusht, Bericht 2026-11-23-0835-uploader-2.3.15-up-ds2.txt – zur Prüfung.

## Gerade in Arbeit
- nichts (UP-DS2 abgeschlossen, wartet auf Prüfung)

## Nächste Schritte (Reihenfolge)
1. Addon 3.0.41 – offene Punkte aus offen-raidmaster.txt gebündelt (Nutzung sparen, eine Version):
   - GoldSentinelSync 3 kopieren (Vorprüfung 18.11.: gleiche Zahlen, kein testLearn nötig), GoldSentinelMarkt v3 kopieren
   - Befund 19.11. Platzhalter-Liste Werbung (Pages.lua ~1097) -> "?" mit Tooltip
   - Entscheid 19.11. 09:06: Dev-Befehle nur im Entwicklermodus sichtbar (Hilfe, Befehlsliste, Tooltips), Test mit Gegenprobe
   - Hinweis 20.11.: Test ändert nie Livedaten; Hinweis 20.11.: Lesbarkeit L1–L8 der Testroutine
   - Hinweis 21.11.: Schätzen verboten; Prüfauftrag 21.11. 16:30 Realm-Schlüssel (grep GetRealmName, Bericht)
   - Takt 2 nur falls genutzt (RaidMaster nutzt Takt nicht – im Bericht belegen)
2. Danach Ingametest-Runde (neue Version) und Bericht.

## Offen beim Nutzer
- Uploader 2.3.15 auf PC und bei beiden Offizieren entpacken (nach Prüfung).

## Entscheide des Nutzers seit letztem Stand
- 23.11. 07:50: Pause aufgehoben, Nutzung sparen ohne Qualitätsverlust.
- 23.11. 08:13: Stand je Sitzung in dieser Datei sichern.

## Wichtig zu wissen
- Arbeitskopie Addon: Repo-Ordner RaidMaster/ (die frühere Kopie /home/claude/RaidMaster gibt es in dieser Umgebung nicht mehr).
- Nachbau: berichte/RaidMaster/offline (run_routine.lua: SHOWID, Gegenproben OPT*/PLAYERLEADER/NOPANEL/CMDDEV/SYNCPOKE, Sync-Zählung).
- Echte Daten nur lokal lesen (goldsentinel-daten), nie Namen in Repo/Berichte.
- Discord-Updates in RaidMasterBot/raid_addon_intro.md ≤ ~1990 Zeichen.
