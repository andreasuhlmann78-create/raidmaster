# Stand AHSentinel (Projekt-Sitzung)

## Stand 24.11.2026 14:55 · Version 0.65.390 (Discord, CurseForge gesperrt)
Repos: ahanalyzerpro (Code, schreiben), raidmaster (announce/, berichte/AHSentinel/), goldsentinel-daten (nur lesen; Ingame-Daten
 im Zweig sicherung: aktuell/AUSPLUSLAPTOP/forever/konto-*/AHSentinel.lua.gz, Testberichte als "GSTEST1{…}" darin).
Arbeitskopie /home/claude/AHSentinel. Veröffentlichen: /tmp/claude-0/bin/pub.sh <neu> <alt> "<Text>" "<Berichtsdatei>" (nur Discord;
 erwartet in /tmp/claude-0/rel/: AHSentinel-<V>.zip, notes.md, bericht.txt, stand.md). ZIP = gleiche 112 Dateien wie Vorversion.
Nachbau: cd /home/claude/ahanalyzerpro && TR_ROWS=1 bash tests/run_offline.sh /home/claude/AHSentinel (~70 s); FULL=1 alle 410 (~25 Min.,
 0.65.390: 336 PASS, 74 alte FAIL – gleich wie 0.65.389, keine neuen). T126 im Nachbau schwankt 6–11 ms (Median mehrerer Läufe).
 Eigene Szenarien in /tmp/claude-0/sim/wowsim/scenarios_new.lua: zz_t459real (echte Spieldaten REAL_SV=/tmp/claude-0/ahs_sv3.lua,
 247 000 Auktionen, 3 Scans), zz_i6_sniper, zz_i6_real; SIM_NOTES=1 gibt T.note aus (common.lua in der Kopie erweitert).

## Gerade in Arbeit
- AHS-I3 (T459): 0.65.390 veröffentlicht (Verdichtung mit Vorrat ab 2. Scan, Gültigkeit vor dem Verdichten). Nachbau Scan 3 noch
  11 650 KB > 10 240. Bericht 2026-11-24-1455-0.65.390-ahs-i3-verdichtung.txt.

## Nächste Schritte (Reihenfolge Supervisor: I3 -> I4-a Rest (erledigt bis Ingame-Beleg) -> G14-a -> T750/T191)
1. AHS-I3 weiter: Verfolgung V4 (Spiel 6 118 KB, 559 verfolgte Items) im Nachbau nachstellen (verfolgte Items mit vielen Auktionen,
   Signaturen als Text) und senken; Bestpreise 1 851 KB (db.lastOwnScan – Wiederverwendung riskant, Mitspieler/Märkte); Einlesen ohne
   Lesen ~3 200 KB im Spiel. Ingame-Feld vollscan_verdichtung abwarten (kommt der Vorrat an?).
2. G14-a: Schnäppchenliste je Item und Angebot nur EIN Fall (Liste beim Spieler nicht löschen, Doppel beim Auswerten zusammenfassen).
3. T750 (116 UI-Befunde) und T191.

## Offen beim Nutzer
- Ingametest mit 0.65.390 ("testroutine alles"): T459 mit "Verdichtung … wiederverwendet x, neu y", vollscan_luecke "im Bild (x ms)"
  = Lücke (AHS-I4-a gilt dann als erledigt).
- Gold-Messung Ausrüstung mit Kupfer-Preis (AHS-POST), RecipeList-Fehler mit nur AHS aktiv.

## Entscheide des Nutzers seit letztem Stand
- keine neuen (Supervisor 13:30: I6, I7 erledigt; 13:45: Antwort I4-a angenommen).

## Wichtig zu wissen
- Meine Aussage 07:25 "Bereinigung ≥ 132 580 KB während der Messung" ist zurückgezogen (Bericht 13:40): Messung je Addon war beim ersten
  Bild ≥ 250 ms, nicht beim längsten. Seit 0.65.390 bei jedem neuen längsten Bild (T1010).
- In-game "gelesen" ~20 MB je Scan = Texte aus GetReplicateItemInfo (Nachbau hat sie nicht) – nicht bewertet.
- VS:Finish: Gültigkeit vor dem Verdichten (#it.q > 0 = Menge > 0); Vorrat = memSpare oder self.mem (nur bei gültig).
- Stelle eigener Skripte nur beim Laden (A.db nil); Naht A.defAtTest nur für T1007.
- Letzter Test T1012. Neue Tests vor "-- CF-AHS-5 (CurseForge 17.11. …"; Index vor { "AHS-I3", .
- Nie etwas in announce/ löschen, alte Versionen nicht wiederherstellen. Jede Version: CHANGELOG.de.md-Abschnitt Pflicht (AHS-R1).
