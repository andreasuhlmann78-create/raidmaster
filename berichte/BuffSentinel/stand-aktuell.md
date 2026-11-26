# BuffSentinel – Stand der Sitzung

## Stand 26.11.2026 11:46 · Version 0.9.66
Veröffentlicht (download/, announce/, Discord). Bericht: berichte/BuffSentinel/2026-11-26-1146-0.9.66-bs-r1-realm-shared-t4.txt.
0.9.66: BS-R1 Realm leer (Profil "Name-" -> stabiler Schlüssel g.lastRealm, Zusammenführen, Sicherung profileMerged), T271;
GoldSentinelTest v4; Version in /bsen hilfe (+Login dev); BS-P2: T269 in Portionen, T146/T156/T179 = GM.DiagLines (shared).
0.9.65 im Spiel bestanden (25.11. 16:00, OK 226 · FEHLER 0).

## Gerade in Arbeit
Nichts angefangen.

## Nächste Schritte (Reihenfolge)
1. Prüfung 0.9.66; T271 mit ECHTEN Daten nachprüfen, sobald der Nutzer den Zugriff auf goldsentinel-daten im Chat erlaubt
   (add_repo wurde am 26.11. von der Rechteprüfung abgelehnt). Messdaten BS-M1: Auswertung Supervisor.
2. Nutzer: T270 Klick-Raster im Spiel (Gruppe, Entwicklermodus), T134, T106 (Raid 40).
3. Danach Nutzer-Entscheid zur Liste 1–6 (Bericht 24.11. 14:08) anhand der Kampfmessungen.
4. BS-P1: Befund GoldSentinelMarkt.DiagLines (gemeinsame Datei) liegt beim Supervisor; eigener Teil erledigt.
5. T249 Zeilenmessung, Prüfliste von Hand; T149 PC zu Hause.

## Offen beim Nutzer
- Ingametest 0.9.65; T270 in einer Gruppe.
- Lesezugriff goldsentinel-daten: Entscheid 25.11. "ja" (über Supervisor), add_repo trotzdem abgelehnt – Nutzer muss es im Chat erlauben.

## Entscheide des Nutzers seit letztem Stand
- 25.11. 15:42 (über Supervisor): BuffSentinel darf goldsentinel-daten LESEN (nur lokal, nie ins öffentliche Repo).

## Wichtig zu wissen
- Quelle /home/claude/BuffSentinel (kein Git). scratchpad: rel.sh (bump+pub+Nachbau aus der Zip), rep.sh, Dateiliste list20.txt
  (neue Dateien eintragen!), post.sh (export S=<scratchpad>). Locales: scratchpad/loc/extra.json + genloc.py (1258 Schlüssel).
- Nachbau erwartet rot: T13 T28 T45 T51 T95. T232 flackert im Nachbau (Serverzeit, Grenze 8 ms) – gemeldet.
- Messung: Messung.lua (M1), Allowed = Option + nicht Testroutine (testAllow nur für T269); Befehl dev.
- Shared nur unverändert: Sync 3, Markt v10, Dev v2, Test 4. Berichte nur "umgesetzt, zur Prüfung". announce/ nie löschen.
