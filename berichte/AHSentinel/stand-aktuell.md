# Stand AHSentinel (Projekt-Sitzung)

## Stand 24.11.2026 10:35 · Version 0.65.389 (Discord, CurseForge gesperrt)
Repos: ahanalyzerpro (Code, schreiben), raidmaster (announce/, berichte/AHSentinel/), goldsentinel-daten (nur lesen; Ingame-Daten
 im Zweig sicherung: aktuell/AUSPLUSLAPTOP/forever/konto-*/AHSentinel.lua.gz, Testberichte als "GSTEST1{…}" darin).
Arbeitskopie /home/claude/AHSentinel. Veröffentlichen: /tmp/claude-0/bin/pub.sh <neu> <alt> "<Text>" "<Berichtsdatei>" (nur Discord;
 erwartet in /tmp/claude-0/rel/: AHSentinel-<V>.zip, notes.md, bericht.txt, stand.md). ZIP = gleiche 112 Dateien wie Vorversion.
Nachbau: cd /home/claude/ahanalyzerpro && TR_ROWS=1 bash tests/run_offline.sh /home/claude/AHSentinel (~70 s; TR_TEXT=1 ganzer Text);
 0.65.389: auto OK 1007, FEHLER 0; server PASS. T126 im Nachbau schwankt 6–11 ms (Uhr) – Vergleiche immer Median aus mehreren Läufen.
 Eigene Szenarien (Sniper-Teil, echte Spieldaten REAL_SV=) in /tmp/claude-0/sim/wowsim/scenarios_new.lua (zz_i6_sniper, zz_i6_real).

## Gerade in Arbeit
- nichts. 0.65.389 veröffentlicht: AHS-I7 (Diag im Abschluss -> Sandbox), AHS-I5 (Sniper-Zustand abgeschottet, Ursache Spielzustand),
  AHS-I6 (Messfehler belegt: Item-Antworten als ms gezählt), AHS-I4-a Rest (Kosten je Bild). Bericht 2026-11-24-1035-0.65.389-i7-i5-i6.txt.

## Nächste Schritte (Reihenfolge Supervisor 10:15: I7 -> I6 -> I4-a Rest -> I3 -> G14-a -> T750/T191)
1. AHS-I3: T459 Vollscan-Speicher 3. Scan 23 214 KB ohne gelesene Auktionen (soll <= 10 240 KB; je Schritt Einlesen 19 390 KB);
   T126 (im Spiel 0.65.388 OK).
2. G14-a: Schnäppchenliste je Item und Angebot nur EIN Fall; Liste beim Spieler nicht löschen, Doppel beim Auswerten zusammenfassen;
   Test mit Gegenprobe.
3. T750 (0.65.388: 116 Befunde, abgeschnitten 100, Markt > Überfüllt 41–42) und T191 (Frame verdeckt Knopf).
4. Teil 3 HILFE-GRP englisch doppelt (im Spiel 0.65.387 "0 doppelt" – prüfen, ob noch offen).

## Offen beim Nutzer
- Ingametest mit 0.65.389 ("testroutine alles"): erwartet Teil 4 T617/T734 OK (eigene Arbeit ohne Item-Anzahl; sonst Stelle Datei:Zeile
  im Text und Feld sniper_eigen), Teil 6 Sandbox OK (Feld diag_abschluss = Anzahl Einträge im Abschluss).
- Gold-Messung Ausrüstung mit Kupfer-Preis (AHS-POST), RecipeList-Fehler mit nur AHS aktiv.

## Entscheide des Nutzers seit letztem Stand
- keine neuen (Supervisor-Aufträge 08:15, 08:25, 10:00, 10:15 umgesetzt).

## Wichtig zu wissen
- AHS-I6 belegt: fo.item ist ANZAHL (Vollscan GET_ITEM_INFO_RECEIVED), fo.read Teil von fo.job; SniperTest zählt nur job+ev+upd.
- Stelle eigener Skripte (debugstack) nur beim Laden der Dateien (A.db nil) – später gemerkt kostete T126 ~1–2 ms im Nachbau.
- fo.busy: verschachtelte eigene Aufrufe nur im äussersten gezählt; A.OwnFrameReset je Bild (SniperTest OwnFrame, Vollscan MTick).
- TR:SnIsolate für jede Prüfung, die Sniper-Zustand liest (Sn.result/extra/btnHit …).
- Diag Store: Sandbox bei TR.running ODER TR.finishing.
- Letzter Test T1009. Neue Tests vor "-- CF-AHS-5 (CurseForge 17.11. …"; Index vor { "AHS-I7", .
- Nie etwas in announce/ löschen, alte Versionen nicht wiederherstellen. Jede Version: CHANGELOG.de.md-Abschnitt Pflicht (AHS-R1).
