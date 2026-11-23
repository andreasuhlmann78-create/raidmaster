# Stand AHSentinel (Projekt-Sitzung)

## Stand 23.11.2026 16:52 · Version 0.65.387
Repos: ahanalyzerpro (Code, schreiben; tests/run_offline.sh = Nachbau mit Testroutine), raidmaster (announce/, berichte/AHSentinel/), goldsentinel-daten (nur lesen).
Arbeitskopie /home/claude/AHSentinel; Veröffentlichen mit /tmp/claude-0/bin/pub.sh (nur Discord, löscht NICHTS in announce/).
Nachbau: cd /home/claude/ahanalyzerpro && TR_ROWS=1 bash tests/run_offline.sh /home/claude/AHSentinel (~70 s). 0.65.387: auto 0, server 0 FEHLER.

## Gerade in Arbeit
- AHS-I2 bis auf T750/T191 (UI) umgesetzt (0.65.387), AHS-I4 ausgewertet (Bericht 16:5x: eigene Arbeit 2 ms, keine Bereinigung, Spiel 710 ms;
  Mess-Vorschlag wartet auf Entscheid Supervisor).

## Nächste Schritte (Reihenfolge Supervisor)
1. AHS-I3 (T126 8,5 ms: ui:overview-movers 10 ms, names 9 ms; T459 Speicher 20 MB). 2. HILFE-GRP (englisch "einstellungen -> optionen" doppelt).
3. G14-Vorschlag (Schnäppchen-Liste je Angebot nur ein Fall). 4. T750/T191 UI-Befunde.

## Offen beim Nutzer
- Neuer Testlauf (0.65.387); CurseForge gesperrt (E5).
- Messung: Ausrüstung mit Kupfer-Preis einstellen (wirtschaft-forever "nur ganze Silber" gegen Entscheid 21.11. 08:54).
- Messung RecipeList-Fehler mit nur AHS aktiv.

## Entscheide des Nutzers seit letztem Stand
- keine neuen.

## Wichtig zu wissen
- GoldSentinelTest Run:Check wertet nil als OK (gemeinsame Datei, gemeldet); TR:Check in AHS wertet nil jetzt als FEHLER.
- Test-Items ohne GetItemInfo brauchen eine Itemstufe (P5), Test-Materialien eine Scan-Zeit (MP2), Testpreise verschiedene Stunden (G4).
- Letzter Test T1002. Neue Tests vor "-- CF-AHS-5 (CurseForge 17.11. …"; Index vor { "BEFUND-S5", .
