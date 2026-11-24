# Stand RaidMaster-Sitzung

## Stand 24.11.2026 07:46 · Addon 3.0.40 · Uploader 2.3.20
- Addon 3.0.40 im Spiel ohne Fehler (Ingametest 18.11.), vom Ingametest befreit (Entscheid 18.11. 15:19).
- Uploader 2.3.16–2.3.18 gepusht – zur Prüfung. 2.3.19 vom Supervisor 07:40 angenommen (Lieferung Laptop belegt).
- 2.3.19 am 24.11. 06:41 per Bot an den Nutzer und 2 von 2 Offizieren geschickt.
- Uploader 2.3.20 (UP-ALT HOCH, Entscheid 24.11. 07:22): gültiger Stand im Zweig "sicherung" (nur 2.3.20+ schreibt ihn, zuerst),
  Lieferungen alter Uploader auf main nie übernommen, Wächter stellt main alle 5 Min. zurück; neueste Version = VERSION in
  RaidMasterUploader/uploader.py (raw HEAD), veralteter Uploader liefert nichts und meldet es. Dazu UP-TAGE-a (Text Tages-Löschung).
  Bericht 2026-11-24-0737 (mit Nachtrag) – zur Prüfung.
- SH-V3 (GoldSentinelTest Version 3) gelesen – kommt unverändert mit Addon 3.0.41.

## Gerade in Arbeit
- nichts (2.3.20 gepusht; wartet auf Verteilung und Prüfung)

## Nächste Schritte (Reihenfolge)
1. Nach Freigabe des Nutzers: 2.3.20 per Bot verteilen (/uploader nur_programm:True an ihn, an_offiziere:True an Offiziere).
2. Nach Meldung "alle Rechner umgestellt": Daten-Repo lokal prüfen – Zweig "sicherung" vorhanden, stand.json "uploader" 2.3.20
   bei allen 4 Rechnern, Feld "tage", nur .lua.gz in aktuell/, main = sicherung – Bericht.
3. Addon 3.0.41 – offene Punkte aus offen-raidmaster.txt gebündelt (eine Version):
   - SH-V3: GoldSentinelTest Version 3 kopieren; neue nil-FEHLER einzeln zuordnen und begründen
   - GoldSentinelSync 3 kopieren (Vorprüfung 18.11.: gleiche Zahlen, kein testLearn nötig), GoldSentinelMarkt v3 kopieren
   - Befund 19.11. Platzhalter-Liste Werbung (Pages.lua ~1097) -> "?" mit Tooltip
   - Entscheid 19.11. 09:06: Dev-Befehle nur im Entwicklermodus sichtbar (Hilfe, Befehlsliste, Tooltips), Test mit Gegenprobe
   - Hinweis 20.11.: Test ändert nie Livedaten; Lesbarkeit L1–L8 der Testroutine
   - Hinweis 21.11.: Schätzen verboten; Prüfauftrag 21.11. 16:30 Realm-Schlüssel (grep GetRealmName, Bericht)
   - Takt 2 nur falls genutzt (RaidMaster nutzt Takt nicht – im Bericht belegen)
4. Danach Ingametest-Runde (neue Version) und Bericht.

## Offen beim Nutzer
- Freigabe: 2.3.20 per Bot an ihn und die Offiziere schicken?
- Uploader 2.3.20 auf JEDEM liefernden Rechner (4) ganz entpacken + neu starten. Ab jetzt wird jeder ältere abgewiesen (auch 2.3.19).
  Erwartet im Fenster beim ersten 2.3.20: "Zweig sicherung angelegt …", danach "geliefert (…)".
- Folge des Entscheids: nach JEDER neuen Uploader-Version werden alle Rechner abgewiesen, bis sie aktualisiert sind.
- Optional Weg b) (neuer Token nur für 2.3.20+, sperrt alte ganz aus) – nur auf Wunsch, Anleitung im Bericht 0737.
- Bot-Auftrag Bewerbungen aufräumen liegt beim Discord-Projekt; ebenso PN an Besitzer alter Uploader (Bericht 0737, Punkt 4).

## Entscheide des Nutzers seit letztem Stand
- 24.11. 07:22 (über Supervisor, UP-ALT): "wenn jemand nicht die neuste version drauf hatt die daten nicht mehr annehmen!"
- 24.11. 07:27: "repo" – Aufträge aus dem Repo umsetzen.

## Wichtig zu wissen
- Leser des Daten-Repos: Zweig "sicherung" nehmen, nur Rechner mit stand.json "uploader" nicht älter als VERSION in
  RaidMasterUploader/uploader.py; .lua UND .lua.gz lesen (de_ketten_lehrer.py liest festen .lua-Pfad – an Supervisor gemeldet).
- Alle Uploader bis 2.3.19 schreiben nur den Standardzweig (belegt an 11 Fassungen) – "sicherung" erreichen sie nie.
- Uploader: RaidMasterUploader/ (Tests: test_daten 46, test_sync 53, test_uploader 23, test_umfassend 14 – alle grün).
  ZIP download/RaidMasterUploader.zip (13 Dateien, ohne tests/), Workflow prüft ZIP = Ordner; Bot holt sie aus raw HEAD.
- Bot-Versand: #gildenbank, /uploader nur_programm:True (an mich) bzw. an_offiziere:True; eingebauter Browser auf 1280x900,
  /uploader tippen + Tab, danach Fenster zurück auf desktop. Nutzer loggt sich selbst ein.
- Arbeitskopie Addon: Repo-Ordner RaidMaster/. Nachbau: berichte/RaidMaster/offline (run_routine.lua).
- Echte Daten nur lokal lesen (goldsentinel-daten), nie Namen in Repo/Berichte.
