# Testberichte der GoldSentinel-Addons

Ausgewertet: 2026-11-11 23:30 UTC

Weg: Addon -> SavedVariables -> RaidMasterUploader -> Discord #testberichte -> hier. Neue Berichte kommen beim nächsten /reload oder Ausloggen und dem nächsten Lauf des Uploaders.

| Addon | letzter Testlauf | Version | Client | OK | FEHLER | übersprungen | im Client prüfen | Fehler im Spiel (7 Tage) |
|---|---|---|---|---|---|---|---|---|
| AHSentinel | 10.11.2026 16:27 UTC | 0.65.86 | forever 1.60.1 (Interface 16001) | 467 | 5 | 22 | 16 | 4 |
| BuffSentinel | 05.11.2026 00:19 UTC | 0.9.7 | forever 1.60.1 (Interface 16001) | 120 | 1 | 10 | 11 | 4 |
| GuildSentinel | 09.11.2026 05:47 UTC | 0.9.13 | forever 1.60.1 (Interface 16001) | 153 | 4 | 23 | 5 | 5 |
| LevelPilot | 05.11.2026 00:21 UTC | 3.12.6 | forever 1.60.1 (Interface 16001) | 11 | 0 | 0 | 0 | 1645 |
| ProfessionSentinel | 09.11.2026 06:57 UTC | 0.9.28 | forever 1.60.1 (Interface 16001) | 5 | 2 | 1 | 0 | 0 |
| RaidMaster | 05.11.2026 00:07 UTC | 3.0.17 | forever 1.60.1 (Interface 16001) | 98 | 3 | 10 | 12 | 2 |
| ThreatSentinel | 10.11.2026 10:06 UTC | 2.5.4 | forever 1.60.1 (Interface 16001) | 7 | 1 | 0 | 1 | 18 |

## Diagnose-Protokolle (GSDIAG1)

| Addon | Anzahl | neueste Datei |
|---|---|---|
| AHSentinel | 70 | `testberichte/diagnose/AHSentinel/0.65.94-a90ab14a9b56.txt` |
| BuffSentinel | 20 | `testberichte/diagnose/BuffSentinel/0.9.12-7f8dfb5af187.txt` |
| GSMesstest | 4 | `testberichte/diagnose/GSMesstest/3-0a66b30190ae.txt` |
| GuildSentinel | 64 | `testberichte/diagnose/GuildSentinel/0.9.24-2b463bdbf513.txt` |
| ProfessionSentinel | 47 | `testberichte/diagnose/ProfessionSentinel/0.9.37-b69a2ad3e0a7.txt` |
| ThreatSentinel | 52 | `testberichte/diagnose/ThreatSentinel/2.5.4-6191344fc78e.txt` |

## Wegdaten (GSWEGE1)

| Addon | Anzahl | neueste Datei |
|---|---|---|
| LevelPilot | 105 | `testberichte/wege/LevelPilot/LevelPilot-wege-1794322533-f6e46f.json` |

## AHSentinel

**Testlauf 0.65.65 · forever 1.60.1 (Interface 16001) · 10.11.2026 06:40 UTC** – OK 55 · FEHLER 1 · übersprungen 4 · im Client prüfen 0 · Sandbox FEHLER: 1 Pfade, wiederhergestellt: watcher.interval
- [SKIP] T40 B – Server: Sniper: Suche (kauft nichts) (grund: Gefertigtes leichtes Geschoss: günstigstes Angebot 1c je Stück - kein Item über 1c, Treffer bei Max 1c wäre richtig)
- [SKIP] T36 B – Handel (simuliert): Gebot (grund: Waren haben keine Gebote)
- [SKIP] T27 B – Einbindung ins Auktionshaus (grund: Einbindung nicht möglich (kein AH-Rahmen))
- [FEHLER] T52 B – Unterboten (ergebnis: Status liegen, Abbrechen-Befehle im Protokoll 0 | erwartet: unterboten)
- [SKIP] T98 D – Server-Wege altes AH (grund: nur im alten Client (Classic Era, TBC))

**Testlauf 0.65.69 · forever 1.60.1 (Interface 16001) · 10.11.2026 08:31 UTC** – OK 365 · FEHLER 1 · übersprungen 21 · im Client prüfen 15 · Sandbox OK
- [CLIENT] T08c A – Berufe-Weiche (Forever) (anleitung: /dump GetNumTradeSkills – muss nil sein, sonst liest das Addon die alte Liste)
- [SKIP] T40 B – Server: Sniper: Suche (kauft nichts) (grund: Gefertigtes leichtes Geschoss: günstigstes Angebot 1c je Stück - kein Item über 1c, Treffer bei Max 1c wäre richtig)
- [SKIP] T36 B – Handel (simuliert): Gebot (grund: Waren haben keine Gebote)
- [SKIP] T31.36 B – Befehle test*/testmodus (grund: würde die laufende Routine stören)
- [CLIENT] T143b J – Alter Ordner AHAnalyzerPro zusätzlich vorhanden (anleitung: Ordner AddOns\AHAnalyzerPro (bis 0.61) zusätzlich aktivieren: genau eine Meldung 'Bitte den alten Ordner ... löschen', keine doppelten /ahs-Befehle, keine Lua-Fehler)
- [SKIP] T97 D – Nachbildung altes AH (grund: nur im alten Client)
- [CLIENT] T142 J – Scan nicht vom Wächter blockiert (anleitung: Forever: Wächter an, Scan fällig -> /ahs scan startet den Scan)
- [CLIENT] T138 J – Wächter und Server-Limit (anleitung: Forever: Wächter 2–3 Runden, dann /ahs scan: startet der Scan?)
- [SKIP] T144 J – CurseForge Forever-Tag (grund: betrifft curseforge/upload.py im raidmaster-Repo, nicht das Addon – prüft die Prüf-Sitzung im Workflow)
- [CLIENT] T145c J – Raid-Vorrat passt zu Forever (anleitung: Passen die Schutztränke zu Barrow Deeps, Hyjalgipfel, Onyxia? (Punkt 5 nach dem Launch))
- [CLIENT] T149 J – Händler-Währungsfunktionen (anleitung: /dump GetMerchantItemCostInfo, /dump GetMerchantItemCostItem – fehlen sie, liest das Addon keine Favor-Kosten)
- [CLIENT] T151 J – Interface-Nummer (anleitung: /dump select(4, GetBuildInfo()) – ist es nicht 16001, neue Nummer in AHSentinel.toc ergänzen)
- [CLIENT] T155c J – Rezept-Auswahl (Forever) (anleitung: Rezept im Blizzard-Berufsfenster wählen -> /dump AHAnalyzerPro.Crafting.lastModernRecipe zeigt dessen ID)
- [SKIP] T59b B – Händler-Verkauf simuliert (grund: HALB: Händler ansprechen, dann /ahs testroutine haendler)
- [SKIP] T186 B – Händler-Knopf verdeckt keinen Reiter des Händlerfensters (grund: HALB: Händler ansprechen, dann /ahs testroutine haendler)
- [CLIENT] T71b B – Alt-Klick im Spiel (anleitung: Alt+Klick auf ein Taschen-Item: Preisverlauf (AH zu) bzw. Einkauf (AH offen))
- [SKIP] T27 B – Einbindung ins Auktionshaus (grund: HALB: Auktionshaus öffnen, dann /ahs testroutine server)
- [SKIP] T37 B – Warenkauf simuliert (grund: HALB: Auktionshaus öffnen, dann /ahs testroutine server)
- [SKIP] T42 B – Sniper-Vorab-Reservierung kauft nie ohne Klick (grund: HALB: Auktionshaus öffnen, dann /ahs testroutine server)
- [SKIP] T50 B – Serie einstellen (grund: HALB: Auktionshaus öffnen, dann /ahs testroutine server)
- [SKIP] T52 B – Unterboten (grund: HALB: Auktionshaus öffnen, dann /ahs testroutine server)
- [SKIP] T126 H – Scan-Auswertung in Portionen (grund: HALB: Auktionshaus öffnen, dann /ahs testroutine server)
- [SKIP] T98 D – Server-Wege altes AH (grund: nur im alten Client (Classic Era, TBC))
- [SKIP] T101 D – Alter Taschen- und Tooltip-Weg (grund: nur im alten Client (Classic Era, TBC))
- [SKIP] T99 D – Alte Berufe-API (grund: nur im alten Client (Classic Era, TBC))
- [SKIP] T100 D – Alter Händler-Weg (grund: nur im alten Client (Classic Era, TBC))
- [SKIP] T120 G – fremde AH-Addons (grund: HALB: Auctionator oder TSM aktiv und Auktionshaus offen)
- [FEHLER] T122 H – Tooltip schnell (ergebnis: 2.10 ms je Aufruf | erwartet: < 2 ms)
- [SKIP] T124 H – Berufsliste (Zwischenspeicher) (grund: HALB: Berufsfenster öffnen, dann /ahs testroutine berufe)
- [SKIP] T148 J – KO 5c: Zwischenspeicher bleibt bei Listen-Ereignissen (grund: HALB: Berufsfenster (moderner Client) öffnen, dann /ahs testroutine berufe)
- [CLIENT] T175 J – Im Spiel (anleitung: Rezept im ProfessionSentinel-Panel ohne vorherigen AHSentinel-Klick anklicken: Berufsfenster zeigt es in < 0,5 s (/ahs protokoll: KLICK ... gewählt))
- [CLIENT] T176 J – Im Spiel (anleitung: Rezept in AHSentinel "Beste Rezepte" anklicken, auch mit Suchtext im Berufsfenster: sofort gewählt, kein Chat-Hinweis)
- [CLIENT] T177 J – Im Spiel (anleitung: Berufsfenster mit AHSentinel und ProfessionSentinel öffnen: nebeneinander, Berufsreiter frei, /ahs protokoll ohne ÜBERLAPPT)
- [CLIENT] T178 J – Im Spiel (anleitung: Kupferne Kettenhose im Gewinn-Fenster: 18c Gewinn, Zeile Einstellgebühr 1s)
- [CLIENT] T179 J – Im Spiel (anleitung: Auktionshaus öffnen, Einkauf -> Waffen: Unterkategorien gleich wie im Blizzard-AH)
- [SKIP] T202 J – Kategorie-Liste behält die Scroll-Position (grund: HALB: Reiter Einkauf einmal öffnen)
- [CLIENT] T197 K – Gewinn-Fenster am Berufsfenster (anleitung: Berufsfenster öffnen (mit und ohne ProfessionSentinel), dann /ahs testroutine k: T192 ohne "überdeckt", T195 ohne Fehler)

**Testlauf 0.65.76 · forever 1.60.1 (Interface 16001) · 10.11.2026 12:35 UTC** – OK 408 · FEHLER 1 · übersprungen 22 · im Client prüfen 16 · Sandbox FEHLER: 1 Pfade, wiederhergestellt: deBackup
- [CLIENT] T08c A – Berufe-Weiche (Forever) (anleitung: /dump GetNumTradeSkills – muss nil sein, sonst liest das Addon die alte Liste)
- [SKIP] T40 B – Server: Sniper: Suche (kauft nichts) (grund: Gefertigtes leichtes Geschoss: günstigstes Angebot 1c je Stück - kein Item über 1c, Treffer bei Max 1c wäre richtig)
- [SKIP] T36 B – Handel (simuliert): Gebot (grund: Waren haben keine Gebote)
- [SKIP] T31.36 B – Befehle test*/testmodus (grund: würde die laufende Routine stören)
- [CLIENT] T143b J – Alter Ordner AHAnalyzerPro zusätzlich vorhanden (anleitung: Ordner AddOns\AHAnalyzerPro (bis 0.61) zusätzlich aktivieren: genau eine Meldung 'Bitte den alten Ordner ... löschen', keine doppelten /ahs-Befehle, keine Lua-Fehler)
- [SKIP] T97 D – Nachbildung altes AH (grund: nur im alten Client)
- [CLIENT] T142 J – Scan nicht vom Wächter blockiert (anleitung: Forever: Wächter an, Scan fällig -> /ahs scan startet den Scan)
- [CLIENT] T138 J – Wächter und Server-Limit (anleitung: Forever: Wächter 2–3 Runden, dann /ahs scan: startet der Scan?)
- [SKIP] T144 J – CurseForge Forever-Tag (grund: betrifft curseforge/upload.py im raidmaster-Repo, nicht das Addon – prüft die Prüf-Sitzung im Workflow)
- [CLIENT] T145c J – Raid-Vorrat passt zu Forever (anleitung: Passen die Schutztränke zu Barrow Deeps, Hyjalgipfel, Onyxia? (Punkt 5 nach dem Launch))
- [CLIENT] T149 J – Händler-Währungsfunktionen (anleitung: /dump GetMerchantItemCostInfo, /dump GetMerchantItemCostItem – fehlen sie, liest das Addon keine Favor-Kosten)
- [CLIENT] T151 J – Interface-Nummer (anleitung: /dump select(4, GetBuildInfo()) – ist es nicht 16001, neue Nummer in AHSentinel.toc ergänzen)
- [CLIENT] T155c J – Rezept-Auswahl (Forever) (anleitung: Rezept im Blizzard-Berufsfenster wählen -> /dump AHAnalyzerPro.Crafting.lastModernRecipe zeigt dessen ID)
- [SKIP] T59b B – Händler-Verkauf simuliert (grund: HALB: Händler ansprechen, dann /ahs testroutine haendler)
- [SKIP] T186 B – Händler-Knopf verdeckt keinen Reiter des Händlerfensters (grund: HALB: Händler ansprechen, dann /ahs testroutine haendler)
- [CLIENT] T71b B – Alt-Klick im Spiel (anleitung: Alt+Klick auf ein Taschen-Item: Preisverlauf (AH zu) bzw. Einkauf (AH offen))
- [SKIP] T27 B – Einbindung ins Auktionshaus (grund: HALB: Auktionshaus öffnen, dann /ahs testroutine server)
- [SKIP] T37 B – Warenkauf simuliert (grund: HALB: Auktionshaus öffnen, dann /ahs testroutine server)
- [SKIP] T42 B – Sniper-Vorab-Reservierung kauft nie ohne Klick (grund: HALB: Auktionshaus öffnen, dann /ahs testroutine server)
- [SKIP] T50 B – Serie einstellen (grund: HALB: Auktionshaus öffnen, dann /ahs testroutine server)
- [SKIP] T52 B – Unterboten (grund: HALB: Auktionshaus öffnen, dann /ahs testroutine server)
- [SKIP] T126 H – Scan-Auswertung in Portionen (grund: HALB: Auktionshaus öffnen, dann /ahs testroutine server)
- [SKIP] T98 D – Server-Wege altes AH (grund: nur im alten Client (Classic Era, TBC))
- [SKIP] T101 D – Alter Taschen- und Tooltip-Weg (grund: nur im alten Client (Classic Era, TBC))
- [SKIP] T99 D – Alte Berufe-API (grund: nur im alten Client (Classic Era, TBC))
- [SKIP] T100 D – Alter Händler-Weg (grund: nur im alten Client (Classic Era, TBC))
- [SKIP] T120 G – fremde AH-Addons (grund: HALB: Auctionator oder TSM aktiv und Auktionshaus offen)
- [SKIP] T124 H – Berufsliste (Zwischenspeicher) (grund: HALB: Berufsfenster öffnen, dann /ahs testroutine berufe)
- [SKIP] T147 J – KO 5b: Zutaten-Knopf ohne SchematicForm (grund: HALB: Berufsfenster (moderner Client) öffnen, dann /ahs testroutine berufe)
- [SKIP] T148 J – KO 5c: Zwischenspeicher bleibt bei Listen-Ereignissen (grund: HALB: Berufsfenster (moderner Client) öffnen, dann /ahs testroutine berufe)
- [FEHLER] T169 H – Aufbau der Rangliste < 16 ms pro Frame (ergebnis: längste Portion 59.0 ms | erwartet: < 16 ms)
- [CLIENT] T175 J – Im Spiel (anleitung: Rezept im ProfessionSentinel-Panel ohne vorherigen AHSentinel-Klick anklicken: Berufsfenster zeigt es in < 0,5 s (/ahs protokoll: KLICK ... gewählt))
- [CLIENT] T176 J – Im Spiel (anleitung: Rezept in AHSentinel "Beste Rezepte" anklicken, auch mit Suchtext im Berufsfenster: sofort gewählt, kein Chat-Hinweis)
- [CLIENT] T177 J – Im Spiel (anleitung: Berufsfenster mit AHSentinel und ProfessionSentinel öffnen: nebeneinander, Berufsreiter frei, /ahs protokoll ohne ÜBERLAPPT)
- [CLIENT] T178 J – Im Spiel (anleitung: Kupferne Kettenhose im Gewinn-Fenster: 18c Gewinn, Zeile Einstellgebühr 1s)
- [CLIENT] T179 J – Im Spiel (anleitung: Auktionshaus öffnen, Einkauf -> Waffen: Unterkategorien gleich wie im Blizzard-AH)
- [SKIP] T202 J – Kategorie-Liste behält die Scroll-Position (grund: HALB: Reiter Einkauf einmal öffnen)
- [CLIENT] T338 K – T-G6 Bereich K in allen Kombinationen (anleitung: Klassisch/Modern × 100/130 % × enGB/deDE: je /ahs testroutine k (nichts abgeschnitten/überlagert))
- [CLIENT] T197 K – Gewinn-Fenster am Berufsfenster (anleitung: Berufsfenster öffnen (mit und ohne ProfessionSentinel), dann /ahs testroutine k: T192 ohne "überdeckt", T195 ohne Fehler)

**Testlauf 0.65.86 · forever 1.60.1 (Interface 16001) · 10.11.2026 16:27 UTC** – OK 467 · FEHLER 5 · übersprungen 22 · im Client prüfen 16 · Sandbox FEHLER: 1 Pfade, wiederhergestellt: sniper.stats.missed
- [CLIENT] T08c A – Berufe-Weiche (Forever) (anleitung: /dump GetNumTradeSkills – muss nil sein, sonst liest das Addon die alte Liste)
- [SKIP] T40 B – Server: Sniper: Suche (kauft nichts) (grund: Gefertigtes leichtes Geschoss: günstigstes Angebot 1c je Stück - kein Item über 1c, Treffer bei Max 1c wäre richtig)
- [SKIP] T36 B – Handel (simuliert): Gebot (grund: Waren haben keine Gebote)
- [SKIP] T31.36 B – Befehle test*/testmodus (grund: würde die laufende Routine stören)
- [CLIENT] T143b J – Alter Ordner AHAnalyzerPro zusätzlich vorhanden (anleitung: Ordner AddOns\AHAnalyzerPro (bis 0.61) zusätzlich aktivieren: genau eine Meldung 'Bitte den alten Ordner ... löschen', keine doppelten /ahs-Befehle, keine Lua-Fehler)
- [SKIP] T97 D – Nachbildung altes AH (grund: nur im alten Client)
- [CLIENT] T142 J – Scan nicht vom Wächter blockiert (anleitung: Forever: Wächter an, Scan fällig -> /ahs scan startet den Scan)
- [CLIENT] T138 J – Wächter und Server-Limit (anleitung: Forever: Wächter 2–3 Runden, dann /ahs scan: startet der Scan?)
- [SKIP] T144 J – CurseForge Forever-Tag (grund: betrifft curseforge/upload.py im raidmaster-Repo, nicht das Addon – prüft die Prüf-Sitzung im Workflow)
- [CLIENT] T145c J – Raid-Vorrat passt zu Forever (anleitung: Passen die Schutztränke zu Barrow Deeps, Hyjalgipfel, Onyxia? (Punkt 5 nach dem Launch))
- [CLIENT] T149 J – Händler-Währungsfunktionen (anleitung: /dump GetMerchantItemCostInfo, /dump GetMerchantItemCostItem – fehlen sie, liest das Addon keine Favor-Kosten)
- [CLIENT] T151 J – Interface-Nummer (anleitung: /dump select(4, GetBuildInfo()) – ist es nicht 16001, neue Nummer in AHSentinel.toc ergänzen)
- [CLIENT] T155c J – Rezept-Auswahl (Forever) (anleitung: Rezept im Blizzard-Berufsfenster wählen -> /dump AHAnalyzerPro.Crafting.lastModernRecipe zeigt dessen ID)
- [SKIP] T59b B – Händler-Verkauf simuliert (grund: HALB: Händler ansprechen, dann /ahs testroutine haendler)
- [SKIP] T186 B – Händler-Knopf verdeckt keinen Reiter des Händlerfensters (grund: HALB: Händler ansprechen, dann /ahs testroutine haendler)
- [CLIENT] T71b B – Alt-Klick im Spiel (anleitung: Alt+Klick auf ein Taschen-Item: Preisverlauf (AH zu) bzw. Einkauf (AH offen))
- [SKIP] T27 B – Einbindung ins Auktionshaus (grund: HALB: Auktionshaus öffnen, dann /ahs testroutine server)
- [SKIP] T37 B – Warenkauf simuliert (grund: HALB: Auktionshaus öffnen, dann /ahs testroutine server)
- [SKIP] T42 B – Sniper-Vorab-Reservierung kauft nie ohne Klick (grund: HALB: Auktionshaus öffnen, dann /ahs testroutine server)
- [SKIP] T50 B – Serie einstellen (grund: HALB: Auktionshaus öffnen, dann /ahs testroutine server)
- [SKIP] T52 B – Unterboten (grund: HALB: Auktionshaus öffnen, dann /ahs testroutine server)
- [SKIP] T126 H – Scan-Auswertung in Portionen (grund: HALB: Auktionshaus öffnen, dann /ahs testroutine server)
- [SKIP] T98 D – Server-Wege altes AH (grund: nur im alten Client (Classic Era, TBC))
- [SKIP] T101 D – Alter Taschen- und Tooltip-Weg (grund: nur im alten Client (Classic Era, TBC))
- [SKIP] T99 D – Alte Berufe-API (grund: nur im alten Client (Classic Era, TBC))
- [SKIP] T100 D – Alter Händler-Weg (grund: nur im alten Client (Classic Era, TBC))
- [SKIP] T120 G – fremde AH-Addons (grund: HALB: Auctionator oder TSM aktiv und Auktionshaus offen)
- [SKIP] T124 H – Berufsliste (Zwischenspeicher) (grund: HALB: Berufsfenster öffnen, dann /ahs testroutine berufe)
- [SKIP] T147 J – KO 5b: Zutaten-Knopf ohne SchematicForm (grund: HALB: Berufsfenster (moderner Client) öffnen, dann /ahs testroutine berufe)
- [SKIP] T148 J – KO 5c: Zwischenspeicher bleibt bei Listen-Ereignissen (grund: HALB: Berufsfenster (moderner Client) öffnen, dann /ahs testroutine berufe)
- [FEHLER] T373 H – Keine Hintergrund-Aufgabe ≥ 16 ms je Frame (während des Ranglisten-Aufbaus) (ergebnis: zu lang: cache:today:10 16.0 ms | erwartet: alle < 16 ms)
- [CLIENT] T175 J – Im Spiel (anleitung: Rezept im ProfessionSentinel-Panel ohne vorherigen AHSentinel-Klick anklicken: Berufsfenster zeigt es in < 0,5 s (/ahs protokoll: KLICK ... gewählt))
- [CLIENT] T176 J – Im Spiel (anleitung: Rezept in AHSentinel "Beste Rezepte" anklicken, auch mit Suchtext im Berufsfenster: sofort gewählt, kein Chat-Hinweis)
- [CLIENT] T177 J – Im Spiel (anleitung: Berufsfenster mit AHSentinel und ProfessionSentinel öffnen: nebeneinander, Berufsreiter frei, /ahs protokoll ohne ÜBERLAPPT)
- [CLIENT] T178 J – Im Spiel (anleitung: Kupferne Kettenhose im Gewinn-Fenster: 18c Gewinn, Zeile Einstellgebühr 1s)
- [CLIENT] T179 J – Im Spiel (anleitung: Auktionshaus öffnen, Einkauf -> Waffen: Unterkategorien gleich wie im Blizzard-AH)
- [SKIP] T202 J – Kategorie-Liste behält die Scroll-Position (grund: HALB: Reiter Einkauf einmal öffnen)
- [FEHLER] T203 J – Entzaubern tatsächlich: 4 bekannte Entzauberungen -> Ø genau, Aufschlüsselung = geschätzter Wert (ergebnis: tatsächlich 211 aus 4, geschätzt 177 = Summe 177, ohne Daten nil · Entzaubern tatsächlich (Ø aus 4) (wenig Daten) 2|TInterface\MoneyFrame\UI-SilverIcon:0:0:2:0|t 11|TInterface\MoneyFrame\UI-CopperIcon:0:0:2:0|t |    Seltsamer Staub  4/4 × Ø 1.8 · AH 99|TInterface\MoneyFrame\UI-CopperIcon:0:0… | erwartet: 250 aus 4 ((7×100 + 1×300) / 4), Summe der Anteile = geschätzter Wert, ohne Daten keine Zeile)
- [FEHLER] T223 J – Entzauberungswert gleich je Gruppe, Gewinn beim Kauf je Kaufpreis, Block-Anteile = Wert, Ausreisser zählt nicht (ergebnis: Wert 128/128, Gewinn 28/-872, Summe 135 = 135, Essenz 2 (ah, unsicher true) | erwartet: gleicher Wert, Gewinn = Wert - Kaufpreis, Summe = Wert, 2c-Angebot ignoriert (Markt 300c))
- [FEHLER] T230 J – Sammelkauf: nur Rendite >= Mindestrendite und >= 10c Gewinn, sortiert; Abschlag 10 % unter 10 Entzauberungen (ergebnis: 0 Kandidaten, oben nil (+nil), danach +nil, Wert ab 10 Entzauberungen 1000 | erwartet: 2, oben +600, dann +400, Wert 1000)
- [CLIENT] T338 K – T-G6 Bereich K in allen Kombinationen (anleitung: Klassisch/Modern × 100/130 % × enGB/deDE: je /ahs testroutine k (nichts abgeschnitten/überlagert))
- [FEHLER] T364 M – T-LG1 26 Stulpen, 14 Seelenstaub, 3 Splitter im Lager, keine Auktionen -> Lager positiv (≈ 4g 67s) (ergebnis: Lager 5|TInterface\MoneyFrame\UI-GoldIcon:0:0:2:0|t 43|TInterface\MoneyFrame\UI-CopperIcon:0:0:2:0|t (im AH 33|TInterface\MoneyFrame\UI-SilverIcon:0:0:2:0|t 24|TInterface\MoneyFrame\UI-CopperIcon:0:0:2:0|t) | erwartet: 4|TInterface\MoneyFrame\UI-GoldIcon:0:0:2:0|t 67|TInterface\MoneyFrame\UI-SilverIcon:0:0:2:0|t 19|TInterface\MoneyFrame\UI-CopperIcon:0:0:2:0|t, im AH 0)
- [CLIENT] T197 K – Gewinn-Fenster am Berufsfenster (anleitung: Berufsfenster öffnen (mit und ohne ProfessionSentinel), dann /ahs testroutine k: T192 ohne "überdeckt", T195 ohne Fehler)

**Fehler im Spiel (letzte 7 Tage)**
- 3× `ADDON_ACTION_BLOCKED`: UNKNOWN() – Version 0.65.16 · forever 1.60.1 (Interface 16001) · zuletzt 08.11.2026 17:09 UTC
- 1× `Lua`: Interface/AddOns/AHSentinel/Seller.lua:1433: attempt to index local 'msg' (a secret string value, while execution tainted by 'AHSentinel') – Version 0.65.80 · forever 1.60.1 (Interface 16001) · zuletzt 10.11.2026 14:28 UTC

## BuffSentinel

**Testlauf 0.9.7 · forever 1.60.1 (Interface 16001) · 05.11.2026 00:19 UTC** – OK 120 · FEHLER 1 · übersprungen 10 · im Client prüfen 11 · Sandbox OK
- [CLIENT] T14 B – Talente in Forever lesbar? (anleitung: /dump BuffSentinel.talentsReadable, BuffSentinel.mainSpec – siehe T74)
- [FEHLER] T29 B – Ereignisse (ergebnis: fehlt: LEARNED_SPELL_IN_TAB · nach Kampfbeginn sichtbar: 0)
- [SKIP] T33 B – Debuffs reinigen (Testdaten) (grund: Reinigen-Raster in Forever/Retail aus)
- [CLIENT] T46 B – Töne hören (anleitung: Optionen > Warntöne > Anhören je Zeile und 'Sounds testen' in der Anordnen-Leiste: alle 7 Töne hörbar)
- [CLIENT] T55 B – Zauber-IDs im laufenden Client (anleitung: in Forever bestätigen – nicht aufgelöst: keine)
- [CLIENT] T74 C – Welche alten Funktionen hat Forever wirklich? (anleitung: /dump GetNumTalentTabs, GetTalentInfo, UnitBuff, GetSpellInfo, C_SpellBook ~= nil, ChatFrame_RemoveChannel, ChatFrameUtil, JoinTemporaryChannel)
- [SKIP] T80 D – Auren auf dem alten Weg (grund: kein UnitBuff – moderner Client)
- [SKIP] T81 D – Zauber auf dem alten Weg (grund: kein UnitBuff – moderner Client)
- [SKIP] T82 D – Zauberbuch auf dem alten Weg (grund: kein UnitBuff – moderner Client)
- [SKIP] T83 D – Gegenstände auf dem alten Weg (grund: kein UnitBuff – moderner Client)
- [SKIP] T84 D – Kampflog-Auslöser (grund: kein UnitBuff – moderner Client)
- [SKIP] T85 D – Hauptbaum nur in Cata (grund: kein UnitBuff – moderner Client)
- [SKIP] T87 D – Alter Kampfweg unverändert (grund: kein UnitBuff – moderner Client)
- [SKIP] T86 D – Fraktion in Era (grund: nur Classic Era)
- [CLIENT] T99 F – Nicht-deutscher Client (anleitung: einmal mit enUS-Client: Optionen öffnen, alle Seiten, Testmodus – Klassennamen aus LOCALIZED_CLASS_NAMES_MALE, Zauber in Client-Sprache, kein Fehler)
- [SKIP] T103 G – Andere Addons des Nutzers (grund: BuffSentinel hat keine Schnittstelle zu anderen GoldSentinel-Addons)
- [CLIENT] T104 G – Mehrere GoldSentinel-Addons gleichzeitig (anleitung: BuffSentinel mit RaidMaster, GuildSentinel, ThreatSentinel, ProfessionSentinel laden: /gsgame eine Zeile, /reload ohne Lua-Fehler, /bsen fehler 'keine Fehler')
- [CLIENT] T106 H – RefreshGroup im Raid 40 (anleitung: im Raid /bsen testroutine leistung – Mittel < 5 ms)
- [CLIENT] T129 J – Klicks nach /reload im Kampf (anleitung: im Kampf /reload, danach dorthin klicken, wo die Buttons waren: kein Zauber)
- [CLIENT] T133 J – Interface-Nummer im Client (anleitung: /dump select(4, GetBuildInfo()) – steht die Zahl in '## Interface' von BuffSentinel.toc? Addon nicht als 'veraltet')
- [CLIENT] T134 J – Ablauf im Forever-Client (anleitung: Buff-Erinnerung vor dem Pull · im Kampf kein Lua-Fehler · /reload, Fehlerliste leer (/bsen testroutine kampf))
- [CLIENT] T135 J – Gegenprobe alter Client (anleitung: Classic Era oder TBC Anniversary: Proc im Kampf, Execute unter 20 %, Dispel im Kampf, Cooldown beim Pull – alles wie vorher; /bsen fehler 'Sperren: nein')

**Fehler im Spiel (letzte 7 Tage)**
- 3× `Event UNIT_AURA`: GetAuraDataByIndex(): Auras cannot be accessed when secret while tainted by 'BuffSentinel'
Lua Taint: BuffSentinel – Version 0.9.7 · forever 1.60.1 (Interface 16001) · zuletzt 08.11.2026 20:31 UTC
- 1× `Event PLAYER_REGEN_ENABLED`: GetAuraDataByIndex(): Auras cannot be accessed when secret while tainted by 'BuffSentinel'
Lua Taint: BuffSentinel – Version 0.9.7 · forever 1.60.1 (Interface 16001) · zuletzt 08.11.2026 20:31 UTC

## GuildSentinel

**Testlauf 0.9.13 · forever 1.60.1 (Interface 16001) · 09.11.2026 05:47 UTC** – OK 153 · FEHLER 4 · übersprungen 23 · im Client prüfen 5 · Sandbox OK
- [SKIP] T09b A – Simulation TBC: Inhalte (grund: beim Laden festgelegt, siehe D / offline 20505)
- [CLIENT] T52 B – Berufsfenster einlesen (anleitung: Jedes eigene Berufsfenster einmal öffnen, dann /gs testroutine b: Seite Berufe zeigt die eigenen Rezepte)
- [CLIENT] T180 B – Bank-Charakter im Spiel (anleitung: Einstellungen > Allgemein: 'Bank-Charakter' anhaken, Bank und Briefkasten öffnen, /reload: Bestand erscheint in #gildenbank (sobald Uploader und Bot aus dem RaidMaster-Auftrag fertig sind))
- [CLIENT] T106 C – echte Kampfsperre (anleitung: Berufe-Seite offen, Kampf beginnen: kein ADDON_ACTION_BLOCKED für GuildSentinel, nach dem Kampf ist der Knopf wieder da)
- [SKIP] T108 D – alter Client (grund: nicht dieser Client)
- [SKIP] T109 D – alter Client (grund: nicht dieser Client)
- [SKIP] T110 D – alter Client (grund: nicht dieser Client)
- [SKIP] T111 D – alter Client (grund: nicht dieser Client)
- [SKIP] T112 D – alter Client (grund: nicht dieser Client)
- [SKIP] T114 D – alter Client (grund: nicht dieser Client)
- [SKIP] T113 D – Berufe klassisch (grund: nicht dieser Client)
- [FEHLER] T118 E – beschädigte Gildendaten (ergebnis: progress>achv: Interface/AddOns/GuildSentinel/Chronicle.lua:131: attempt to index a number value | erwartet: 0 Fehler)
- [SKIP] T115 E – Neuinstallation (grund: würde GuildSentinelDB neu anlegen; offline: jeder Lauf in test/ startet ohne GuildSentinelDB)
- [SKIP] T117 E – Migration (grund: offline in test/run_nilglobals.lua (Altlasten) und run_lang.lua (alte Spracheinstellung))
- [SKIP] T119 E – beschädigte Einstellungen (grund: offline in test/run_nilglobals.lua)
- [SKIP] T123 F – alle Schlüssel vorhanden (grund: Client-Sprache ist de (Schlüssel bzw. Locales.lua))
- [CLIENT] T136 G – Guild Roster Manager (anleitung: mit installiertem GRM: Leitung > GRM-Import zeigt Zahlen; ohne: kein Fehler)
- [SKIP] T137 G – ProfessionSentinel (grund: GuildSentinel nutzt keine Schnittstelle von ProfessionSentinel)
- [FEHLER] T143 H – Seiten mit 500 Mitgliedern (ergebnis: 206.5 ms (langsamste) | erwartet: < 16 ms)
- [SKIP] T145 H – Speicher (grund: Messung im Bericht unten (collectgarbage vor/nach))
- [FEHLER] T154 J – P2: Twink/Main, Danke, Pate mit Vor- und Nachname (ergebnis: <Name>|nil|<Name> | erwartet: <Name> ×3)
- [SKIP] T156 J – P4a: Bewerber-Flüstern im Kampf (grund: wie T85)
- [SKIP] T157 J – P4b: Addon-Nachricht im Kampf (grund: wie T84)
- [SKIP] T158 J – P4c: Abklingzeit im Kampf (grund: wie T86)
- [SKIP] T160 J – P5b: KnowsSpell über C_SpellBook (grund: wie T98/T133)
- [SKIP] T162 J – P6b: ChatFrame_RemoveChannel (grund: wie T101)
- [SKIP] T164 J – Launch-Tag: Interface-Nummer (grund: wie T03)
- [CLIENT] T168 J – K2 im echten Kampf (anleitung: Mitspieler flüstert im Kampf 'gilde'; nach dem Kampf /gs testroutine whisperq und prüfen, ob Hinweis oder Bewerber erscheint)
- [SKIP] T171 J – K5: tools/luac5.1 -v (grund: Werkzeug im Repo (offline))
- [SKIP] T172 J – RM2: Werkzeug nicht in der ZIP (grund: offline (unzip -l))
- [SKIP] T173 J – N8: Offline-Test K2 (grund: offline (test/run_forever95.lua))
- [FEHLER] T82 B – nichts gesendet (ergebnis: echt 1 (C_ChatInfo.SendAddonMessage 1), Warteschlange +0 | erwartet: echt 0, Warteschlange +0)

**Fehler im Spiel (letzte 7 Tage)**
- 4× `ADDON_ACTION_BLOCKED`: UNKNOWN() – Version 0.9.13 · forever 1.60.1 (Interface 16001) · zuletzt 08.11.2026 09:01 UTC
- 1× `ADDON_ACTION_BLOCKED`: fn() – Version 0.9.21 · forever 1.60.1 (Interface 16001) · zuletzt 10.11.2026 10:09 UTC

## LevelPilot

**Testlauf 3.12.6 · forever 1.60.1 (Interface 16001) · 05.11.2026 00:21 UTC** – OK 11 · FEHLER 0 · übersprungen 0 · im Client prüfen 0

**Fehler im Spiel (letzte 7 Tage)**
- 847× `Protokoll CheckNav`: Interface/AddOns/LevelPilot/Protocol.lua:235: attempt to compare a secret number value (execution tainted by 'LevelPilot') – Version 3.12.6 · forever 1.60.1 (Interface 16001) · zuletzt 05.11.2026 14:24 UTC
- 798× `session`: Interface/AddOns/LevelPilot/Session.lua:29: attempt to perform boolean test on a secret boolean value (execution tainted by 'LevelPilot') – Version 3.12.13 · forever 1.60.1 (Interface 16001) · zuletzt 08.11.2026 20:41 UTC

## ProfessionSentinel

**Testlauf 0.9.13 · forever 1.60.1 (Interface 16001) · 05.11.2026 00:17 UTC** – OK 144 · FEHLER 6 · übersprungen 9 · im Client prüfen 13 · Sandbox OK
- [CLIENT] T06 A – Interface-Nummer akzeptiert (anleitung: Launch: /dump select(4, GetBuildInfo()) – die Nummer muss in allen 4 TOCs stehen (Client 16001))
- [CLIENT] T30 B – Lebenslinien-Widget und Hooks (anleitung: Berufsfenster öffnen, dann /ps testroutine b (Widget automatisch OK))
- [CLIENT] T42 B – Echter Kartenpin (halbautomatisch) (anleitung: Rechtsklick im Panel auf ein fehlendes Rezept mit Händler: Pin muss gesetzt werden, danach selbst entfernen; bestätigen mit /ps testroutine ok T42)
- [CLIENT] T50 B – Favor-Stand (anleitung: Handelslager-Händler öffnen (Favor-Stand unbekannt), dann /ps testroutine b)
- [SKIP] T56 B – Händlergunst in anderen Versionen aus (grund: nur Classic Era / Retail)
- [FEHLER] T63 B – Eingabefenster Aufschlag, Mindestgewinn, Marge (lua: ...face/AddOns/Blizzard_StaticPopup_Game/GameDialog.lua:124: invalid option in `format')
- [CLIENT] T69 B – Rezepte in den Taschen (anleitung: ein Rezept-Item in die Taschen legen, dann /ps testroutine b)
- [CLIENT] T70 B – Anbindung an den AHSentinel-Scan (anleitung: mit AHSentinel einen AH-Scan machen: Rezept-Alarm bzw. Gruppe „alerts“ im Panel erscheint (angemeldet: true))
- [CLIENT] T85 B – Andocken und Hinweis „bester Rezept“ (anleitung: Berufsfenster öffnen (Addons dürfen das nicht selbst), dann /ps testroutine b)
- [SKIP] T108 C – Alter Tooltip-Weg (grund: nur im alten Client prüfbar – siehe T120)
- [CLIENT] T113 C – Panel und Tooltip im echten Kampf (anleitung: Panel offen und Rezept in den Taschen überfahren, dann einen Kampf beginnen und Tooltips ansehen: kein Lua-Fehler, kein ADDON_ACTION_BLOCKED)
- [SKIP] T115 D – Berufe auf dem alten Weg (grund: nur Classic Era)
- [SKIP] T117 D – Händlergunst und Gebühr aus (grund: nur Classic Era)
- [SKIP] T118 D – Reiter-Layout wie früher (grund: nur Classic Era / Retail)
- [SKIP] T119 D – Lebenslinie im Blizzard-Fenster alt (grund: nur Classic Era)
- [SKIP] T120 D – Tooltip-Weg im alten Client (grund: nur Classic Era)
- [SKIP] T121 D – TBC bleibt untätig (grund: kein TBC-Client in diesem Lauf (simuliert in T10/T172))
- [SKIP] T122 D – Retail-Eigenheiten (grund: nur Retail)
- [FEHLER] T132 G – Keine globalen Namen überschrieben (ergebnis: 17 Prüfungen, 1 Fehler: nicht erlaubt: ProfessionSentinelAutoTestReportBg, ProfessionSentinelAutoTestReportCloseButton, ProfessionSentinelAutoTestReportInset, ProfessionSentinelAutoTestReportPortrait, ProfessionSentinelAutoTestReportText, ProfessionSentinelAutoTestReportTitleText, ProfessionSentine… | erwartet: 0 Fehler)
- [CLIENT] T138 G – AHSentinel „Heute tun“ zeigt Herstellungen (anleitung: AHSentinel „Heute tun“ öffnen: Zeilen von ProfessionSentinel erscheinen dort)
- [FEHLER] T139 H – Panel-Aufbau je Ansicht (ergebnis: 6 Ansichten, 6 Fehler: recipes 36.1 ms · langsamste 44.2 ms (Lederverarbeitung) | erwartet: < 16 ms)
- [FEHLER] T140 H – Bestes Rezept bei jedem Berufs-Ereignis (ergebnis: 20.2 ms | erwartet: < 16 ms)
- [FEHLER] T143 H – Teure Rechnungen (ergebnis: 6 Rechnungen, 2 Fehler: AD.Plan 1->300 67.6 ms | erwartet: 0 Fehler)
- [CLIENT] T144 H – Lebenslinie im Blizzard-Fenster (anleitung: Berufsfenster öffnen, dann /ps testroutine h)
- [CLIENT] T169 J – Interface-Nummer nach dem Launch (anleitung: /dump select(4, GetBuildInfo()) – Nummer in allen 4 TOCs (Client 16001))
- [CLIENT] T177 J – Gildenblick bleibt leer, solange RaidMaster in Forever nichts einliest (anleitung: automatisch OK; nach dem RaidMaster-Fix: Gildenblick zeigt Einträge)
- [CLIENT] T186 B – Minimap-Button im Spiel (anleitung: Buch-Symbol an der Minimap sichtbar, Tooltip in der Sprache des Clients, Ziehen verschiebt ihn, nach /reload am selben Ort, Linksklick wie /ps, Rechtsklick listet die Optionen; bestätigen mit /ps testroutine ok T186)
- [FEHLER] T145 H – Speicher (ergebnis: 20× Refresh: +0 KB · nach dem Lauf: +1230 KB | erwartet: < 256 KB / < 1024 KB)

**Testlauf 0.9.28 · forever 1.60.1 (Interface 16001) · 09.11.2026 06:57 UTC** – OK 5 · FEHLER 2 · übersprungen 1 · im Client prüfen 0
- [SKIP] S5 S – Gleiche AH-Gebühr wie AHSentinel (grund: 5 Rezepte im Panel anklicken (Berufsfenster offen))
- [FEHLER] S7 S – Kein Neuaufbau-Sturm beim Herstellen (ergebnis: 0.2 Aufbau/s, 3 LANGSAM | erwartet: ≤ 2/s, 0 LANGSAM)
- [FEHLER] S8 S – Oberflächen-Prüfung (Bereich K) (ergebnis: CheckButton verdeckt ProfessionSentinelPanelCloseButton; Button verdeckt ProfessionSentinelPanelCloseButton; CheckButton verdeckt Button; Button verdeckt ProfessionSentinelPanelCloseButton; Button verdeckt ProfessionSentinelPanelCloseButton; Button verdeckt ProfessionSentinelPanelCloseButton; Button… | erwartet: keine)

## RaidMaster

**Testlauf 3.0.17 · forever 1.60.1 (Interface 16001) · 05.11.2026 00:07 UTC** – OK 98 · FEHLER 3 · übersprungen 10 · im Client prüfen 12 · Sandbox OK
- [SKIP] T06 A – Fähigkeiten folgen der Weiche (grund: Caps nur beim Laden berechnet)
- [CLIENT] T35b B – Berufe (Fenster echt öffnen) (anleitung: siehe T152: Knopf 'Meine Berufe einlesen' mehrmals, dann /rm berufe)
- [CLIENT] T36b B – Gildenbank echt (anleitung: Bank-Charakter: Bank öffnen, Post öffnen, dann /rm bank – Bestand > 0 Einträge?)
- [FEHLER] T43 B – Test-Werkzeug selbst (ony) (ergebnis: kein Item vergeben | erwartet: >= 1 (Items vom Server geladen?))
- [CLIENT] T51b C – Absender von Addon-Nachrichten im Kampf geschützt? (anleitung: Forever, im Kampf mit Mitspieler: /rm sync – kommt keine Lua-Meldung, ist alles gut)
- [CLIENT] T54b C – Systemmeldung mit geschütztem Text (anleitung: Forever, im Kampf jemanden einladen lassen: kommt keine Lua-Meldung, ist alles gut (echte geschützte Strings lassen sich nicht nachstellen))
- [SKIP] T71 D – Alter Client (grund: nur im alten Client (Era/TBC))
- [SKIP] T72 D – Alter Client (grund: nur im alten Client (Era/TBC))
- [SKIP] T73 D – Alter Client (grund: nur im alten Client (Era/TBC))
- [SKIP] T74 D – Alter Client (grund: nur im alten Client (Era/TBC))
- [SKIP] T75 D – Alter Client (grund: nur im alten Client (Era/TBC))
- [SKIP] T91 F – Formatplatzhalter (grund: offline geprüft (Lua 5.1 mit lupa))
- [CLIENT] T92 F – Jede Sprache einmal aktiv (anleitung: einmal mit englischem Client /rmtest testroutine F)
- [CLIENT] T103 G – DBM und BigWigs (anleitung: Pull-Timer aus der Boss-Leiste: Balken bei DBM/BigWigs sichtbar?)
- [CLIENT] T104 G – BugSack/BugGrabber (anleitung: mit BugSack: /rmtest testroutine I – Testfehler in BugSack und Diagnose?)
- [FEHLER] T122 I – Doppelte Fehler (ergebnis: Diagnose 1 Einträge, n = 6 | erwartet: 1 Eintrag, n = 3)
- [CLIENT] T133b J – Mouseover-Tasten im echten Kampf (anleitung: Forever: Trainingspuppe/Mob im Kampf per Mouseover-Taste markieren – Symbol da, Fehlerliste leer?)
- [CLIENT] T135 J – Skillungen in Forever (anleitung: /dump GetTalentTabInfo(1) und /dump GetTalentInfo(1,1); Gildenmitglied betrachten)
- [CLIENT] T136b J – Plündermeister vorhanden (anleitung: /dump GiveMasterLoot ~= nil, GetMasterLootCandidate ~= nil; /dump C_PartyInfo and C_PartyInfo.GetLootMethod())
- [FEHLER] T142 J – !dkp mit Doppelnamen (Forever-Weg) (ergebnis: [RaidMaster] <Name>: MC 40 · Ony 90 | erwartet: <Name> … 40)
- [CLIENT] T146 J – Bereitschafts-Check in alten Clients (anleitung: Era/Anniversary mit Fläschchen: /rm bereit – erkannt?)
- [SKIP] T147 J – Berufe-Knopf übersetzt (grund: offline geprüft (Locales))
- [CLIENT] T152 J – Berufe-Knopf im Client (anleitung: Knopf 'Meine Berufe einlesen' mehrmals, dann /rm berufe)
- [SKIP] T90 F – Fehlende Übersetzungen (grund: Grundsprache)
- [SKIP] T70 D – Ganze Routine im alten Client (grund: nur im alten Client (Era/TBC): dort /rmtest testroutine)

**Fehler im Spiel (letzte 7 Tage)**
- 2× `ADDON_ACTION_FORBIDDEN`: SetRaidTarget() – Version 3.0.17 · forever 1.60.1 (Interface 16001) · zuletzt 08.11.2026 19:36 UTC

## ThreatSentinel

**Testlauf 2.4.5 · forever 1.60.1 (Interface 16001) · 09.11.2026 05:49 UTC** – OK 126 · FEHLER 2 · übersprungen 50 · im Client prüfen 12 · Sandbox OK
- [CLIENT] T11 A – Interface-Nummer des Clients in der .toc (anleitung: Interface steht in der Kopfzeile des Berichts; die Prüf-Sitzung vergleicht sie mit ## Interface (am Launch-Tag /dump select(4, GetBuildInfo())))
- [FEHLER] T22 B – ns:FullName (eigener Charakter) (ergebnis: <Name> | erwartet: <Name> ohne Realm)
- [CLIENT] T46 B – Bedrohung prüfen – im Kampf (anleitung: Mob angreifen, im Kampf /ts bedrohung: Status und Prozent (oder 'geschützt') erscheinen, kein Lua-Fehler)
- [SKIP] T25 B – Funktionsprüfung mit Test-Einheiten/Plaketten (grund: braucht nachgebaute Test-Plaketten/-Einheiten über mehrere Module – noch nicht automatisiert)
- [SKIP] T29 B – Funktionsprüfung mit Test-Einheiten/Plaketten (grund: braucht nachgebaute Test-Plaketten/-Einheiten über mehrere Module – noch nicht automatisiert)
- [SKIP] T30 B – Funktionsprüfung mit Test-Einheiten/Plaketten (grund: braucht nachgebaute Test-Plaketten/-Einheiten über mehrere Module – noch nicht automatisiert)
- [SKIP] T41 B – Funktionsprüfung mit Test-Einheiten/Plaketten (grund: braucht nachgebaute Test-Plaketten/-Einheiten über mehrere Module – noch nicht automatisiert)
- [SKIP] T48 B – Funktionsprüfung mit Test-Einheiten/Plaketten (grund: braucht nachgebaute Test-Plaketten/-Einheiten über mehrere Module – noch nicht automatisiert)
- [SKIP] T49 B – Funktionsprüfung mit Test-Einheiten/Plaketten (grund: braucht nachgebaute Test-Plaketten/-Einheiten über mehrere Module – noch nicht automatisiert)
- [SKIP] T50 B – Funktionsprüfung mit Test-Einheiten/Plaketten (grund: braucht nachgebaute Test-Plaketten/-Einheiten über mehrere Module – noch nicht automatisiert)
- [SKIP] T52 B – Funktionsprüfung mit Test-Einheiten/Plaketten (grund: braucht nachgebaute Test-Plaketten/-Einheiten über mehrere Module – noch nicht automatisiert)
- [SKIP] T53 B – Funktionsprüfung mit Test-Einheiten/Plaketten (grund: braucht nachgebaute Test-Plaketten/-Einheiten über mehrere Module – noch nicht automatisiert)
- [SKIP] T54 B – Funktionsprüfung mit Test-Einheiten/Plaketten (grund: braucht nachgebaute Test-Plaketten/-Einheiten über mehrere Module – noch nicht automatisiert)
- [SKIP] T55 B – Funktionsprüfung mit Test-Einheiten/Plaketten (grund: braucht nachgebaute Test-Plaketten/-Einheiten über mehrere Module – noch nicht automatisiert)
- [SKIP] T56 B – Funktionsprüfung mit Test-Einheiten/Plaketten (grund: braucht nachgebaute Test-Plaketten/-Einheiten über mehrere Module – noch nicht automatisiert)
- [SKIP] T57 B – Funktionsprüfung mit Test-Einheiten/Plaketten (grund: braucht nachgebaute Test-Plaketten/-Einheiten über mehrere Module – noch nicht automatisiert)
- [SKIP] T58 B – Funktionsprüfung mit Test-Einheiten/Plaketten (grund: braucht nachgebaute Test-Plaketten/-Einheiten über mehrere Module – noch nicht automatisiert)
- [SKIP] T59 B – Funktionsprüfung mit Test-Einheiten/Plaketten (grund: braucht nachgebaute Test-Plaketten/-Einheiten über mehrere Module – noch nicht automatisiert)
- [SKIP] T65 B – Funktionsprüfung mit Test-Einheiten/Plaketten (grund: braucht nachgebaute Test-Plaketten/-Einheiten über mehrere Module – noch nicht automatisiert)
- [SKIP] T66 B – Funktionsprüfung mit Test-Einheiten/Plaketten (grund: braucht nachgebaute Test-Plaketten/-Einheiten über mehrere Module – noch nicht automatisiert)
- [SKIP] T67 B – Funktionsprüfung mit Test-Einheiten/Plaketten (grund: braucht nachgebaute Test-Plaketten/-Einheiten über mehrere Module – noch nicht automatisiert)
- [SKIP] T68 B – Funktionsprüfung mit Test-Einheiten/Plaketten (grund: braucht nachgebaute Test-Plaketten/-Einheiten über mehrere Module – noch nicht automatisiert)
- [SKIP] T69 B – Funktionsprüfung mit Test-Einheiten/Plaketten (grund: braucht nachgebaute Test-Plaketten/-Einheiten über mehrere Module – noch nicht automatisiert)
- [SKIP] T70 B – Funktionsprüfung mit Test-Einheiten/Plaketten (grund: braucht nachgebaute Test-Plaketten/-Einheiten über mehrere Module – noch nicht automatisiert)
- [SKIP] T71 B – Funktionsprüfung mit Test-Einheiten/Plaketten (grund: braucht nachgebaute Test-Plaketten/-Einheiten über mehrere Module – noch nicht automatisiert)
- [SKIP] T72 B – Funktionsprüfung mit Test-Einheiten/Plaketten (grund: braucht nachgebaute Test-Plaketten/-Einheiten über mehrere Module – noch nicht automatisiert)
- [SKIP] T77 B – Funktionsprüfung mit Test-Einheiten/Plaketten (grund: braucht nachgebaute Test-Plaketten/-Einheiten über mehrere Module – noch nicht automatisiert)
- [SKIP] T78 B – Funktionsprüfung mit Test-Einheiten/Plaketten (grund: braucht nachgebaute Test-Plaketten/-Einheiten über mehrere Module – noch nicht automatisiert)
- [SKIP] T79 B – Funktionsprüfung mit Test-Einheiten/Plaketten (grund: braucht nachgebaute Test-Plaketten/-Einheiten über mehrere Module – noch nicht automatisiert)
- [SKIP] T80 B – Funktionsprüfung mit Test-Einheiten/Plaketten (grund: braucht nachgebaute Test-Plaketten/-Einheiten über mehrere Module – noch nicht automatisiert)
- [SKIP] T82 B – Funktionsprüfung mit Test-Einheiten/Plaketten (grund: braucht nachgebaute Test-Plaketten/-Einheiten über mehrere Module – noch nicht automatisiert)
- [SKIP] T83 B – Funktionsprüfung mit Test-Einheiten/Plaketten (grund: braucht nachgebaute Test-Plaketten/-Einheiten über mehrere Module – noch nicht automatisiert)
- [SKIP] T85 B – Funktionsprüfung mit Test-Einheiten/Plaketten (grund: braucht nachgebaute Test-Plaketten/-Einheiten über mehrere Module – noch nicht automatisiert)
- [SKIP] T88 B – Funktionsprüfung mit Test-Einheiten/Plaketten (grund: braucht nachgebaute Test-Plaketten/-Einheiten über mehrere Module – noch nicht automatisiert)
- [SKIP] T91 B – Funktionsprüfung mit Test-Einheiten/Plaketten (grund: braucht nachgebaute Test-Plaketten/-Einheiten über mehrere Module – noch nicht automatisiert)
- [SKIP] T92 B – Funktionsprüfung mit Test-Einheiten/Plaketten (grund: braucht nachgebaute Test-Plaketten/-Einheiten über mehrere Module – noch nicht automatisiert)
- [SKIP] T97 C – Bedrohung geschützt, ganzer Durchlauf (grund: braucht nachgebaute Test-Plaketten/-Einheiten über mehrere Module – noch nicht automatisiert (5 Testmobs mit Plaketten; Teile in T164, T167-T169))
- [SKIP] T106 C – Chat-, CVar- und Addon-Funktionen fehlen (grund: C_ChatInfo/C_CVar/C_AddOns laufen nicht über ns.API (nur Sendewege, über ns.Act mitgeschrieben))
- [CLIENT] T109 C – Keine geschützten Aktionen im Kampf (anleitung: Im Kampf: Einstellungen öffnen (Hinweis 'nicht im Kampf'), /ts move (verweigert); danach /ts test > Bericht: Blocked: none)
- [CLIENT] T110 C – Plaketten im Kampf in ANZEIGE/AUS (anleitung: Forever, Modus ANZEIGE: Pull mit 3+ Mobs – nichts leuchtet, Plaketten unverändert; nach dem Kampf wieder normal)
- [SKIP] T112 D – Alter Client (grund: nur Classic Era / TBC)
- [SKIP] T113 D – Alter Client (grund: nur Classic Era / TBC)
- [SKIP] T114 D – Alter Client (grund: nur Classic Era / TBC)
- [SKIP] T115 D – Alter Client (grund: nur Classic Era / TBC)
- [SKIP] T116 D – Alter Client (grund: nur Classic Era / TBC)
- [SKIP] T117 D – Gegenprobe im echten Spiel (grund: nur Classic Era / TBC)
- [SKIP] T122 E – Beschädigte Einträge (grund: nicht automatisch: InitDB mit falschen Typen würde Login-Teile der Module auf echten Rahmen auslösen; Typprüfung in Migrate ist ein eigener Auftrag)
- [SKIP] T126 F – Im Code benutzte Schlüssel (grund: vor dem Push per Skript geprüft (manuell))
- [SKIP] T128 F – Andere Sprache aktivieren (grund: Sprachumschaltung (devLocale) ist noch nicht eingebaut)
- [SKIP] T134 G – Schnittstellen zu den anderen Addons (grund: keine Schnittstelle)
- [CLIENT] T135 G – Mehrere GoldSentinel-Addons gleichzeitig (anleitung: Mit RaidMaster, GuildSentinel, BuffSentinel, ProfessionSentinel laden, /reload, /gsgame: eine Zeile, Version 2; /ts testroutine g)
- [SKIP] T136 H – T:Tick mit 10/40 Testmobs (grund: braucht nachgebaute Test-Plaketten/-Einheiten über mehrere Module – noch nicht automatisiert (Testmobs))
- [SKIP] T138 H – Bildweise OnUpdate (grund: braucht nachgebaute Test-Plaketten/-Einheiten über mehrere Module – noch nicht automatisiert (Testplaketten))
- [FEHLER] T139 H – Protokoll-Auswertung (ergebnis: 44.98 ms | erwartet: < 16 ms)
- [SKIP] T147 I – Lua-Fehler ausserhalb von pcall (grund: würde einen echten Fehler im Fehlerfenster/BugSack des Spielers auslösen; GoldSentinelTest.TrackErrors ist angemeldet (siehe Core.lua))
- [CLIENT] T148 J – Kein Ersatz über das Ziel des Mobs (modern) (anleitung: Forever: Mob ohne Bedrohungsdaten bleibt IDLE (Diagnose 'Bedrohung am Ziel'), kein Leuchten)
- [CLIENT] T149 J – Kein stilles IDLE bei geschützten Werten (anleitung: Forever, erster Kampf: /ts bedrohung zeigt 'geschützt', Hinweis 1x)
- [SKIP] T153 J – Blizzard-Plaketten im Kampf nicht anfassen (grund: braucht nachgebaute Test-Plaketten/-Einheiten über mehrere Module – noch nicht automatisiert (siehe T110 im Client))
- [CLIENT] T154 J – Taint im Modus VOLL (anleitung: Pull mit 3+ Mobs im Modus VOLL, danach /ts test > Bericht: 'Blocked: none'; kein 'ThreatSentinel hat eine Aktion blockiert')
- [CLIENT] T157 J – Erkennung einmal pro Kampf, Zustand gespeichert (anleitung: Forever: zwei Kämpfe hintereinander, danach /ts bedrohung: 'zuletzt erkannt' mit Datum und Build)
- [CLIENT] T174 J – UnitIsUnit nur über ns:SameUnit (anleitung: Forever, Gruppe im Kampf: kein Lua-Fehler (Testzentrale-Diagnose 'Fehler: 0'))
- [CLIENT] T176b J – Alter Client: Kampf in der Gruppe (anleitung: Classic Era und TBC Anniversary: Schadens-/Heilmeter zählt, widerstandener Spott wird gemeldet, kein 'Addon geblockt' – Ergebnis dem Nutzer melden)
- [CLIENT] T177 J – Launch-Tag: Interface-Nummer und erster Kampf (anleitung: /dump select(4, GetBuildInfo()); im ersten Kampf /ts bedrohung -> Modus im Bericht)
- [SKIP] T178 J – Lua-Syntaxprüfung (grund: vor dem Push mit addon_check.py (manuell))

**Testlauf 2.5.2 · forever 1.60.1 (Interface 16001) · 09.11.2026 19:33 UTC** – OK 5 · FEHLER 0 · übersprungen 1 · im Client prüfen 1 · Sandbox OK
- [SKIP] T134 G – Schnittstellen zu den anderen Addons (grund: keine Schnittstelle)
- [CLIENT] T135 G – Mehrere GoldSentinel-Addons gleichzeitig (anleitung: Mit RaidMaster, GuildSentinel, BuffSentinel, ProfessionSentinel laden, /reload, /gsgame: eine Zeile, Version 2; /ts testroutine g)

**Testlauf 2.5.4 · forever 1.60.1 (Interface 16001) · 10.11.2026 10:06 UTC** – OK 7 · FEHLER 1 · übersprungen 0 · im Client prüfen 1 · Sandbox OK
- [FEHLER] T181 K – Kein Überlappen mit Blizzard- oder GoldSentinel-Fenstern (ergebnis: Testzentrale überdeckt BuffSentinelAnchor_cd (BuffSentinel) · geprüft 2 | erwartet: keine)
- [CLIENT] T186 K – Oberfläche mit offenen Blizzard-Fenstern (anleitung: Charakterfenster, Karte, Händler oder Post öffnen, dazu Testzentrale und Einstellungen; dann /ts testroutine k: T181 ohne Überlappen)

**Fehler im Spiel (letzte 7 Tage)**
- 3× `Selbsttest`: Interface/AddOns/ThreatSentinel/TestRoutine.lua:1447: TS-Selbsttest Handler – Version 2.4.5 · forever 1.60.1 (Interface 16001) · zuletzt 09.11.2026 05:49 UTC
- 3× `Selbsttest`: TS-Selbsttest 1 – Version 2.4.5 · forever 1.60.1 (Interface 16001) · zuletzt 09.11.2026 05:49 UTC
- 3× `Selbsttest`: TS-Selbsttest – Version 2.4.5 · forever 1.60.1 (Interface 16001) · zuletzt 09.11.2026 05:49 UTC
- 3× `Selbsttest`: ADDON_ACTION_BLOCKED: TestFunc – Version 2.4.5 · forever 1.60.1 (Interface 16001) · zuletzt 09.11.2026 05:49 UTC
- 3× `Selbsttest`: Interface/AddOns/ThreatSentinel/TestRoutine.lua:1433: TS-Selbsttest DD – Version 2.4.5 · forever 1.60.1 (Interface 16001) · zuletzt 09.11.2026 05:49 UTC
- 3× `Selbsttest`: TS-Selbsttest 2 – Version 2.4.5 · forever 1.60.1 (Interface 16001) · zuletzt 09.11.2026 05:49 UTC
