# Stand 28.11.2026 12:00 · Version 0.9.102 (announce), 0.9.100 (download) · PAUSE bis Montag 30.11.

## Gerade in Arbeit
- NICHTS – Pause nach Entscheid des Nutzers 28.11. 11:25 ("sobald PS fertig ist, Pause bis Montag").
- 0.9.102 NUR announce/ (Release v0.9.102, Repo 90d1d13, md5 2eaca735…), Bericht 2026-11-28-1200-version-0.9.102.txt – zur Prüfung:
  PS-SK3 (Lehrername je Rezept, Rezept bei keinem besuchten Lehrer nicht im Plan), PS-P4 (ledger gebündelt), PS-PERF-NB1 (Zeit je Teil im
  Protokoll – Ursache noch offen), PS-PLAN-KOST ("Noch zu kaufen"), PS-VAL-HV1/VK1 (Weg, Stück), PS-REZ-ZAHL (Tooltip).
- 0.9.101: angenommen (Code 09:10); Beleg PS-SK3 kein Rückschritt im Bericht 2026-11-28-1134 -> PS-DL 0.9.101 wartet auf Supervisor.
  download/ hat noch 0.9.100.

## Nächste Schritte (Reihenfolge, ab Montag)
1. git pull, offen-professionsentinel.txt lesen (Antwort zu 0.9.101/0.9.102, PS-DL).
2. PS-PERF-NB1: aus dem nächsten /ps protokoll "TEIL … größter Teil …" den Abschnitt nehmen und so teilen, dass kein Bild > 16 ms;
   Nachbau mit echten Daten (tests/nachbau_echt.py … --only-open --profile 15) – lief 28.11. 35 Min. ohne Ergebnis, mit `python3 -u` und mehr Zeit.
3. PS-PERF-TSU1 b): mit "diese Sitzung k" entscheiden, ob Aufbauten ohne Änderung wegfallen.
4. PS-VAL-LB2: Ursache bei AHS (AHS-LB-AH1); PS zeigt nur den Weg.
5. PS-TQ1 a) mit echten Daten; Gilden-Sync-Tag ohne Realm; MITTEL 2/4; Entwickler-Befehle; Lesbarkeit L1–L8; "AH ~Preis".
6. Neue Version erst nach "ANGENOMMEN"/"PS-DL frei" nach download/ (DL-ABN; gleiche Zip/md5, alte Zip entfernen, Addon-Prüfung grün).

## Offen beim Nutzer (Ingametest 0.9.102)
- Schneiderlehrer öffnen -> Tooltip Magiestoffballen "bei keinem besuchten Lehrer (1 besucht)"; Plan ohne Magiestoffballen, Zeile "Nicht im Plan".
- Plan-Kopf "Noch zu kaufen …"; Tooltip "Lohnt bis (Händler/Wiederverkauf/Entzaubern)", Fraktionsbanner "für 2 Stück"?
- Post mit mehreren Briefen -> /ps protokoll "ledger (gebündelt n)"; Berufsfenster -> /ps protokoll "TEIL Neuaufbau (Teil) · … · größter Teil …".
- Aus 0.9.101: Flut-Tooltip beim nächsten Auftreten (PS-GOLD-WID).

## Entscheide des Nutzers seit letztem Stand
- 28.11. 11:25 (über Supervisor): PS nach laufender Arbeit Pause bis Montag 30.11.
- 28.11. 09:10 (Supervisor-Freigabe): Lehrername merken, "lernbar bei <Lehrer>" nur wo gelesen (umgesetzt 0.9.102).
- 28.11. 06:43: Einzel-Einkauf = Eigenbedarf (umgesetzt 0.9.101).

## Wichtig zu wissen
- PS-Repo /home/claude/professionsentinel, Release über Push auf main (Workflow baut Zip); Asset laden über gh api releases/tags/vX.
- Tests: run_offline forever/era/retail (+ --lua51), check_actions, gen_locale_keys, yield_check, run_smoketest - forever era retail
  (Attrappen-Grenzen in tests/smoketest.lua EXPECTED_FAIL, T309 neu dort).
- "125" bei Magiestoffballen ist die Schätzung der Daten, keine Lernstufe – nie anzeigen.
- Protokoll: "×n seit TT.MM., diese Sitzung k"; AUFBAU "Summe je Aufbau" ≠ ein Bild; "längstes Bild" ist das Bild.
