# Stand ThreatSentinel

## Stand 23.11.2026 10:45 · Version 2.5.25 (veröffentlicht), 2.5.26 im Bauordner
Veröffentlicht (download/, announce/), addon_check OK ohne WARNUNG. Berichte: 2026-11-23-0850-version-2.5.24.txt, 2026-11-23-0950-version-2.5.25-stufe3.txt.

## Gerade in Arbeit
Im Bauordner fertig, noch nicht veröffentlicht (laut Auftrag mit dem nächsten Bündel):
- TS-R1 (09:41): Rolle nur gesichert, ohne Tank kein "lose" + 1 Hinweis je Gruppe (T55, T29, T-OPT1; Gegenprobe rot).
- TS-R1-a (10:19): unbekannte eigene Rolle -> "V:<Version>" statt "H:UNKNOWN" (alte Versionen ignorieren V; Beleg 2.5.25 Sync.lua
  S:Handle ohne else-Zweig). Neue Clients merken Version, Rolle bleibt unbekannt, überdeckt keine Gruppenrolle. Test T-R1a mit
  Gegenstelle 2.5.25 (wörtlicher Zweig "H"), Gegenprobe altes Senden rot. Specs: Sync "unbekannt" ersetzt das Lesen der Skillung nicht.
  Folge für alte Clients: Spieler mit unbekannter Rolle stehen dort nicht in der Sync-Nutzerliste (S:Users 2.5.25, Sync.lua:264).
Offline: Forever 312 OK, Era 316 OK, 6 bekannte Nachbildungs-FEHLER.

## Nächste Schritte (Reihenfolge)
1. Prüfung 2.5.25 durch die Prüf-Sitzung; weiter ins Repo schauen (auftraege/ThreatSentinel/offen-threatsentinel.txt).
2. 2.5.26 veröffentlichen, sobald das Bündel steht (oder Nutzer/Supervisor es freigibt); Bericht mit TS-R1/TS-R1-a-Belegen.
3. SPÄTER: gemeinsame Befehlsliste (CH-G) erst auf Anweisung.

## Offen beim Nutzer
- Ingametest 2.5.25: /ts testroutine alles (Entwicklermodus /gsdev). Neu: T187 Lesbarkeit, T-LIVE Livedaten, Ort im Bericht.
- Messung Stufe 3 sammelt sich nur in Era/TBC mit Entwicklermodus im Kampf (Zeile im Testbericht).
- Prüfliste OPT: OK/Nicht OK.

## Entscheide des Nutzers seit letztem Stand
- Keine direkten. Supervisor 23.11. 09:23: Stufe 3 aus (TS-S3a/b) – in 2.5.25; 09:41: TS-R1 – im Bauordner (2.5.26).

## Wichtig zu wissen
- Bauordner: /home/claude/build/v245/ThreatSentinel (nicht im Repo). Veröffentlichen mit dem Publish-Skript der Sitzung.
- Offline-Routine: python3 -I berichte/ThreatSentinel/offline/routine_offline.py <zip|Ordner> Forever|Era [Bereich|alles]; 6 bekannte Nachbildungs-FEHLER (T02, T09, T20, T34, T39, T133).
- Gemeinsame Dateien aktuell (Sync 3, Markt 10, Game 3, Test 2, Dev 2, Prüfliste 1). Takt nutzt ThreatSentinel nicht.
- Aggrometer: Formel-Code nur noch in M:MeasureS3 (Meter.lua), Messwerte in ThreatSentinelDB.s3mess.
