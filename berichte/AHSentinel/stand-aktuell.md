# Stand AHSentinel (Projekt-Sitzung)

## Stand 24.11.2026 07:25 · Version 0.65.388 (Discord, CurseForge gesperrt bis Ingametest)
Repos: ahanalyzerpro (Code, schreiben), raidmaster (announce/, berichte/AHSentinel/), goldsentinel-daten (nur lesen).
Arbeitskopie /home/claude/AHSentinel. Veröffentlichen: /tmp/claude-0/bin/pub.sh <neu> <alt> "<Text>" "<Berichtsdatei>" (nur Discord, löscht nichts in announce/;
 erwartet in /tmp/claude-0/rel/: AHSentinel-<V>.zip, notes.md, bericht.txt, stand.md). ZIP = gleiche Dateiliste wie Vorversion (unzip -Z1, 112 Dateien).
Nachbau: cd /home/claude/ahanalyzerpro && TR_ROWS=1 bash tests/run_offline.sh /home/claude/AHSentinel (~70 s; TR_TEXT=1 = ganzer Text);
 0.65.388: auto OK 1003, FEHLER 0; server PASS. Nur ein Teil: ONLY=s42_testroutine_auto (bzw. s43_testroutine_server).

## Gerade in Arbeit
- nichts angefangen. 0.65.388 veröffentlicht: AHS-R1 (Release-Text DE zuerst), AHS-I4-a (Zahlen offen, Bilder/s beschriftet, Messung im
  längsten Bild), SH-V3/AHS-V3 (GoldSentinelTest V3 kopiert, T277 >= 2). Bericht 2026-11-24-0725-0.65.388-ahs-r1-i4a-v3.txt.

## Nächste Schritte (Reihenfolge Supervisor 24.11. 07:08: R1 -> I4-a -> I3 -> G14-a -> T750/T191)
1. AHS-I3 MITTEL: T126 Scan-Auswertung Ø 3 längste Portionen 8,5 ms (soll <= 8; ui:overview-movers 10 ms, ui:names 9 ms);
   T459 Vollscan-Speicher 3. Scan 20 609 KB ohne gelesene Auktionen (soll <= 10 240 KB), 1 Bild > 40 ms mit Bereinigung, 64 Bereinigungen.
2. G14-a MITTEL (angenommen): Schnäppchenliste je Item und Angebot nur EIN Fall; bestehende Liste beim Spieler nicht löschen, Doppel beim
   Auswerten zusammenfassen; Test mit Gegenprobe (derselbe Treffer 2× -> 1 Fall).
3. Teil 3 HILFE-GRP NIEDRIG: englisch ein Befehl doppelt ("einstellungen -> optionen").
4. T750 (104 UI-Befunde: abgeschnitten 88, überlappt 12; Markt > Überfüllt 52) und T191 (Frame verdeckt Knopf) – eigene Version.
5. Teil 2 UI 1 FEHLER, Teil 4 Sniper S1–S13 2 FEHLER: Einzelheiten aus testberichte/berichte/AHSentinel/AHSentinel-1795437122-*-3/-4.json.
6. Ab jetzt jede Version: CHANGELOG.de.md-Abschnitt Pflicht (sonst bricht der Release-Lauf ab, AHS-R1).

## Offen beim Nutzer
- Neuer Ingametest mit 0.65.388 ("testroutine alles", mindestens "server"): AHS-I1/I2 gelten erst danach als erledigt; CurseForge bleibt
  bis dahin gesperrt. Neue Felder: vollscan_luecke (Lua gesamt, während der Messung bereinigt), vollscan_probe, vollscan_fps.
- Messung Gold-Sicherheit (AHS-POST, Supervisor gibt sie an den Nutzer): Ausrüstung mit Kupfer-Preis einstellen (z. B. 14s57). Bei Fehler:
  Regel "ganze Silber" nur fürs Einstellen zurück (AHS seit 0.65.359 Se:SilverOnly = false).
- Messung RecipeList-Fehler mit nur AHS aktiv.
- MT-Prüfung 24.11.: Markt-Tabelle bleibt Stand 16.11. bis RaidMaster UP-TAGE geklärt (Entscheid 06:17); Kern-Abgleich 28/29/36 Zellen –
  noch kein Auftrag an AHS.

## Entscheide des Nutzers seit letztem Stand
- 07:04 (an den Supervisor): "du musst nicht selber am addon entwickeln nur prüfen" – Supervisor ändert keinen Addon-Code.
- 06:17: CurseForge-Zwischenstand posten; Markt-Tabellen warten auf RaidMaster UP-TAGE (höchstens 1 Tag).

## Wichtig zu wissen
- AHS-I4-a belegt: im 712-ms-Bild +104 907 KB, danach während UpdateAddOnMemoryUsage >= 132 580 KB bereinigt; "Code ausserhalb der Addons"
  zurückgezogen (Verdacht, zu messen). GetFramerate = Mittelwert. Messung RegisterAllEvents nur Testroutine + Einlesen; Nachbau kennt sie nicht.
- GoldSentinelTest Version 3 (nil = FEHLER) im ZIP; TR:Check ebenso streng.
- Test-Regeln: Test-Items ohne GetItemInfo brauchen Itemstufe (P5), Test-Materialien Scan-Zeit (MP2), Testpreise verschiedene Stunden
  (G4/TT3), Trend herausgerechnet (G11), Markt "Alle|<Fraktion>" (G1/G2), Rechnungsmenge Feld 11 (PM1).
- Letzter Test T1005. Neue Tests vor "-- CF-AHS-5 (CurseForge 17.11. …"; Index vor { "BEFUND-S5", . Locale-Schlüssel nach "Seelengebunden – nicht im AH verkaufbar".
- Nie etwas in announce/ löschen (23.11. 11:36), alte Versionen nicht wiederherstellen (12:03). Schliesskassetten-Preise ab 22.11. evtl. verzerrt.
