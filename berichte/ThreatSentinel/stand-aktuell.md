# Stand ThreatSentinel

## Stand 23.11.2026 10:35 · Version 2.5.26
Veröffentlicht (download/, announce/), addon_check OK ohne WARNUNG. Bericht: berichte/ThreatSentinel/2026-11-23-1035-version-2.5.26-rollen.txt.

## Gerade in Arbeit
Nichts. TS-R1 und TS-R1-a in 2.5.26 umgesetzt, zur Prüfung (Freigabe zur Veröffentlichung: Supervisor 10:24).

## Nächste Schritte (Reihenfolge)
1. Prüfung 2.5.25 durch die Prüf-Sitzung; weiter ins Repo schauen (auftraege/ThreatSentinel/offen-threatsentinel.txt).
2. Ergebnis des Ingametests 2.5.26 auswerten, sobald es im Repo liegt.
3. SPÄTER: gemeinsame Befehlsliste (CH-G) erst auf Anweisung.

## Offen beim Nutzer
- Ingametest 2.5.26 (deckt 2.5.24–2.5.26 ab): /ts testroutine alles (Entwicklermodus /gsdev). Neu: T187 Lesbarkeit, T-LIVE Livedaten, Ort im Bericht.
- Messung Stufe 3 sammelt sich nur in Era/TBC mit Entwicklermodus im Kampf (Zeile im Testbericht).
- Prüfliste OPT: OK/Nicht OK.

## Entscheide des Nutzers seit letztem Stand
- Keine direkten. Supervisor 23.11. 09:23: Stufe 3 aus (TS-S3a/b) – in 2.5.25; 09:41: TS-R1 – im Bauordner (2.5.26).

## Wichtig zu wissen
- Bauordner: /home/claude/build/v245/ThreatSentinel (nicht im Repo). Veröffentlichen mit dem Publish-Skript der Sitzung.
- Offline-Routine: python3 -I berichte/ThreatSentinel/offline/routine_offline.py <zip|Ordner> Forever|Era [Bereich|alles]; 6 bekannte Nachbildungs-FEHLER (T02, T09, T20, T34, T39, T133).
- Gemeinsame Dateien aktuell (Sync 3, Markt 10, Game 3, Test 2, Dev 2, Prüfliste 1). Takt nutzt ThreatSentinel nicht.
- Aggrometer: Formel-Code nur noch in M:MeasureS3 (Meter.lua), Messwerte in ThreatSentinelDB.s3mess.
