# Stand ThreatSentinel

## Stand 23.11.2026 10:30 · Version 2.5.25 (veröffentlicht), 2.5.26 im Bauordner
Veröffentlicht (download/, announce/), addon_check OK ohne WARNUNG. Berichte: 2026-11-23-0850-version-2.5.24.txt, 2026-11-23-0950-version-2.5.25-stufe3.txt.

## Gerade in Arbeit
TS-R1 (Supervisor 09:41, Rollen nur gesichert, ohne Tank keine Lose-Warnung, 1 Hinweis je Gruppe) im Bauordner umgesetzt und offline
getestet (Forever 311 OK, Era 315 OK, Gegenprobe T55 rot). Laut Auftrag KEINE eigene Version: kommt mit dem nächsten Bündel als 2.5.26.
Dabei: T76 räumt erfundenen Mitspieler auf; Option "Heiler nach Klasse erraten" entfernt (T-OPT1: entfernt 1); Sync sendet "H:UNKNOWN",
wenn die eigene Rolle unbekannt ist (alte Clients zeigen dann "UNKNOWN" statt eines Rateworts, kein Lua-Fehler – im Bericht nennen).

## Nächste Schritte (Reihenfolge)
1. Prüfung 2.5.25 durch die Prüf-Sitzung; weiter ins Repo schauen (auftraege/ThreatSentinel/offen-threatsentinel.txt).
2. Nächster Auftrag kommt -> mit TS-R1 als 2.5.26 bündeln, Bericht mit TS-R1-Belegen (T55/T29/T-OPT1, Gegenprobe).
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
