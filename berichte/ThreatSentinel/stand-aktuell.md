# Stand ThreatSentinel

## Stand 23.11.2026 08:50 · Version 2.5.24
Veröffentlicht (download/, announce/), addon_check OK ohne WARNUNG. Bericht: berichte/ThreatSentinel/2026-11-23-0850-version-2.5.24.txt.

## Gerade in Arbeit
Nichts. Alle Aufträge bis 23.11. 08:14 in 2.5.24 umgesetzt, zur Prüfung.

## Nächste Schritte (Reihenfolge)
1. Prüfung von 2.5.24 durch die Prüf-Sitzung abwarten, dabei weiter ins Repo schauen (auftraege/ThreatSentinel/offen-threatsentinel.txt).
2. Messung Aggrometer Stufe 3 ("~ geschätzt"): in Era/TBC Reihenfolge gegen echte Bedrohung zählen – oder ausschalten, falls die Prüf-Sitzung das will (Frage im Bericht).
3. SPÄTER: gemeinsame Befehlsliste (CH-G) erst auf Anweisung.

## Offen beim Nutzer
- Ingametest 2.5.24: /ts testroutine alles (neu: T187 Lesbarkeit, T-LIVE Livedaten, Ort im Bericht).
- Prüfliste OPT: OK/Nicht OK.

## Entscheide des Nutzers seit letztem Stand
- Keine neuen direkt an diese Sitzung (umgesetzt: 19.11. 09:06, 20.11. 08:39, 20.11. 13:44, 21.11. 06:47, 21.11. 16:30, 23.11. 07:50/08:13).

## Wichtig zu wissen
- Bauordner: /home/claude/build/v245/ThreatSentinel (nicht im Repo). Veröffentlichen mit dem Publish-Skript der Sitzung (Zip, addon_check, announce, README).
- Offline-Routine: python3 -I berichte/ThreatSentinel/offline/routine_offline.py <zip|Ordner> Forever|Era [Bereich|alles]; 6 bekannte Nachbildungs-FEHLER (T02, T09, T20, T34, T39, T133).
- Gemeinsame Dateien alle aktuell (Sync 3, Markt 10, Game 3, Test 2, Dev 2, Prüfliste 1). Takt nutzt ThreatSentinel nicht.
- Livedaten-Prüfung: R.LiveTables in TestRoutine.lua; gsTest ist ausgenommen (Testbericht-Ablage).
