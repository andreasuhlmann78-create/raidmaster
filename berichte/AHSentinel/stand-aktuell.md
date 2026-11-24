# Stand AHSentinel (Projekt-Sitzung)

## Stand 24.11.2026 06:40 · Version 0.65.387 (Discord, CurseForge gesperrt E5)
Repos: ahanalyzerpro (Code, schreiben), raidmaster (announce/, berichte/AHSentinel/), goldsentinel-daten (nur lesen).
Arbeitskopie /home/claude/AHSentinel. Veröffentlichen: /tmp/claude-0/bin/pub.sh <neu> <alt> "<Text>" "<Berichtsdatei>" (nur Discord, löscht nichts in announce/;
 erwartet in /tmp/claude-0/rel/: AHSentinel-<V>.zip, notes.md, bericht.txt, stand.md). ZIP = gleiche Dateiliste wie Vorversion (unzip -Z1).
Nachbau: cd /home/claude/ahanalyzerpro && TR_ROWS=1 bash tests/run_offline.sh /home/claude/AHSentinel (~70 s); 0.65.387: auto 0, server 0 FEHLER.
 Nur ein Teil: ONLY=s42_testroutine_auto (bzw. s43_testroutine_server). Achtung: time() liefert im Nachbau Bruchteile.

## Gerade in Arbeit
- nichts angefangen. AHS-I2 umgesetzt bis auf T750/T191 (Bericht 2026-11-23-1637-0.65.387-ahs-i2-rest.txt);
  AHS-I4 ausgewertet (Bericht 2026-11-23-1640-ahs-i4-vollscan-luecke.txt: eigene Arbeit 2 ms, keine Bereinigung, Spiel 710 ms, +105 MB Lua im Bild).

## Nächste Schritte (Reihenfolge Supervisor: I1 -> I2 -> I4 -> I3)
1. AHS-I3 MITTEL: T126 Scan-Auswertung Ø 3 längste Portionen 8,5 ms (soll <= 8; ui:overview-movers 10 ms, ui:names 9 ms);
   T459 Vollscan-Speicher 3. Scan 20 609 KB ohne gelesene Auktionen (soll <= 10 240 KB), 1 Bild > 40 ms mit Bereinigung, 64 Bereinigungen.
2. Teil 3 HILFE-GRP NIEDRIG: englisch ein Befehl doppelt ("einstellungen -> optionen").
3. G14-Vorschlag schreiben: alle 300 Schnäppchen-Einträge stammen aus 12 Minuten (Flut) – je Angebot nur ein Fall.
4. T750 (104 UI-Befunde: abgeschnitten 88, überlappt 12; Markt > Überfüllt 52) und T191 (Frame verdeckt Knopf) – eigene Version.
5. Teil 2 UI 1 FEHLER, Teil 4 Sniper S1–S13 2 FEHLER: Einzelheiten aus testberichte/berichte/AHSentinel/AHSentinel-1795437122-*-3/-4.json holen.
6. Nach Entscheid: AHS-I4-Zusatzmessung (Ereignisse im längsten Bild, AH-Fenster offen?, Auktions-Index beim Bildwechsel).

## Offen beim Nutzer
- Neuer Testlauf "testroutine alles" mit 0.65.387; CurseForge bleibt gesperrt (E5), bis die Prüf-Sitzung freigibt.
- Messung Gold-Sicherheit: Ausrüstung mit Kupfer-Preis einstellen (z. B. 14s57). wirtschaft-forever: "Ausrüstung nur ganze Silber
  (199c -> Interner Auktion-Fehler)" gegen Entscheid 21.11. 08:54 ("ganze Silber weg", AHS seit 0.65.359 Se:SilverOnly = false). Bei Fehler: Regel nur fürs Einstellen zurück.
- Messung RecipeList-Fehler mit nur AHS aktiv.
- Entscheid Supervisor: AHS-I4-Zusatzmessung ja/nein.
- Entscheid Supervisor/Nutzer (MT-Prüfung 24.11. 05:39): Markt-Tabelle nicht übernommen – Stände 14.–20.11. fehlen im Daten-Repo; alte Stände
  wiederherstellen oder Fallzahl-Regel für den Neustart aussetzen. Kern-Abgleich 24.11.: 28/29/36 Zellen gehen nicht auf (Ziel 0) – betrifft
  ggf. AHS-Journal/Kern (Verkauf ausserhalb de, de:5); noch kein Auftrag an AHS.
- Gemeinsame Datei GoldSentinelTest.lua: Run:Check wertet nil als OK (gemeldet im Bericht 0.65.387; Änderung nur durch Prüf-Sitzung in shared/).

## Entscheide des Nutzers seit letztem Stand
- keine neuen (24.11. 06:28 nur Frage nach dem Kontext; 06:39 Auftrag: Stand sichern).

## Wichtig zu wissen
- 0.65.387: MV:Advice ohne geprüften Preis -> "Preis nicht geprüft – erneut prüfen" (P8); Ln:RelistHigher = Verkaufen-Vorschlag;
  TR:Check wertet nil als FEHLER (15 verdeckte FEHLER sichtbar gemacht und behoben); SelfTest T21 erst FEHLER, wenn Items 3 Stundenwerte haben.
- Test-Regeln: Test-Items ohne GetItemInfo brauchen Itemstufe (P5; ilvl = false heisst unbekannt), Test-Materialien Scan-Zeit (MP2),
  Testpreise verschiedene Stunden (G4/TT3), Trend herausgerechnet (G11), Markt "Alle|<Fraktion>" (G1/G2), Rechnungsmenge Feld 11 (PM1).
  Echtdaten-Tests: Learn.forceOff, VS.SalesRate nil, A.EvalHours 24, Ledger.PostSizes leer.
- Letzter Test T1002. Neue Tests vor "-- CF-AHS-5 (CurseForge 17.11. …"; Index vor { "BEFUND-S5", . Locale-Schlüssel nach "Seelengebunden – nicht im AH verkaufbar".
- Nie etwas in announce/ löschen (23.11. 11:36), alte Versionen nicht wiederherstellen (12:03). Hinweis Blueposts 24.11.: Schliesskassetten-Preise ab 22.11. evtl. verzerrt.
