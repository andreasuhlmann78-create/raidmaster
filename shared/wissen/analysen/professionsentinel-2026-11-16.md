ANALYSE – NUR FESTGEHALTEN, KEIN AUFTRAG – Fehler werden erst nach Freigabe des Nutzers behoben

# ProfessionSentinel – Nacht-Analyse (Supervisor, begonnen 15.11.2026 19:00)

Geprüfte Version: 0.9.45 (Repo ProfessionSentinel, Commit 45fc6f0, 13.11.2026 22:34; download/ProfessionSentinel-0.9.45.zip).
Seit 0.9.45 keine neue Version (letzte Arbeit 13.11.; die Sitzung arbeitet seither nicht an PS – Fokus AHSentinel).

## 1. Geschichte (aus Repo-Log, 53 Commits, und raidmaster/auftraege/ProfessionSentinel/)
- 0.9.1–0.9.10 (2.–3.11.): WoW-Forever-Grundlagen (Einstellgebühr ≥ 1s, Händlergunst/Handelslager, Kisten), gemeinsame
  Versionserkennung GoldSentinelGame (zweimal zurückgenommen, dann zentral), Rezeptdaten aus Pipeline.
- 0.9.11–0.9.23 (3.–5.11.): Testroutine T01–T204, Klick auf Rezept zuverlässig (mehrere Anläufe: Neuaufbau verschluckte Klicks),
  Andocken an AHSentinel.
- 0.9.24–0.9.39 (9.–12.11.): Ereignis-Sturm (Diagnose 0.9.22: 7450 Neuaufbauten durch TRADE_SKILL_LIST_UPDATE, UI:Refresh je
  101 ms) -> Scan-Ruhezeit, portionierter Neuaufbau (10 ms/Bild), UI-Rework, Preis-Vermittler (AHSentinel, aux, Auctionator).
- 0.9.40–0.9.45 (13.11.): Marktwissen, Befehlsliste, Marktdaten-Netz (GoldSentinelMarkt v1 -> v2).
- Offene Aufträge (offen-professionsentinel.txt): PS-TC1 (TodayCrafts 153 ms am Stück), PS-API1 (KnownRecipes), HK-P Rest,
  PM1–PM7, GoldSentinelMarkt aktualisieren (v3/v4 – inzwischen v6), BL3/BL4 später.

## 2. Was ich gemacht habe
- addon_check auf die Zip: OK, 1 Warnung "GoldSentinelMarkt.lua veraltete offizielle Fassung (Version 2) – auf Version 6".
- tests/run_smoketest.py: Ausgang 0. tests/run_offline.py (alle Spielversionen): forever OK 223 / FEHLER 0 (12 im Client
  prüfen), era OK 205 / 0, retail OK 204 / 0. Leistung im Mock (langsamster Wert): T143 15,5 ms, T246 10,5 ms.
- Code gelesen: Scan.lua (Ereignisse, Refresh), UI.lua (Ereignisse, Neuaufbau), Alerts.lua (Rezept-Alarm), Disenchant.lua
  (Item-Info nachladen), Today.lua (API TodayCrafts), Core.lua (Marktdaten-Netz, ns.Foreign), TOC-Dateien.
- Messdaten aus dem Spiel: GSSniperLog-Protokolle des Nutzers vom 15.11. (Zeilen ADDONS = Spiel-Profiler je Addon).

## 3. Befunde

### P-1 RUCKELN IM SPIEL – GEMESSEN (Schwere: HOCH für das Spielgefühl)
GSSniperLog 15.11. (Spiel-Profiler, Werte seit Sitzungsbeginn): ProfessionSentinel Spitze **921 ms** in einem Bild; Bilder über
50 ms: 76 (18:26) -> 80 (18:37) -> 92 (18:46) -> 102 (18:58). Ziel aller Addons: kein Bild über 16 ms durch ein Addon.
Ursache NICHT belegt. Verdachte aus dem Code (zu messen):
  a) Alerts.lua AL.OnScan läuft im Ereignis SCAN_FINISHED von AHSentinel, im selben Bild: AL.Needed() geht über alle Figuren ×
     Berufe × alle Rezepte (ns.IsLearned je Rezept), dann Sortieren, dann ns.RefreshAll() = direkter UI:Refresh (nicht
     portioniert) + Advisor.Invalidate. Nach dem Scan 19:01 stand im Chat "Rezept-Alarm: 340 fehlende Rezepte" – der Weg lief also.
  b) API.TodayCrafts (Today.lua 276) rechnet bei jedem Aufruf TD.Candidates neu (PS-TC1: 153 ms gemessen, noch offen);
     AHSentinel ruft es auf.
  c) Disenchant.lua 363: GET_ITEM_INFO_RECEIVED für angefragte Items -> nach 1 s ns.RefreshAll(). Während der Item-Info-Stürme
     nach einem AHSentinel-Vollscan (bis 9 400 Ereignisse je 2 s, GSL8-1) kann das jede Sekunde einen vollen Neuaufbau auslösen.
  d) UI:Refresh direkt (Klick, Reiter, Suche) ist nicht portioniert (frühere Diagnose: 101–131 ms).
Messvorschlag (für später): Diagnose-Zeile je Weg mit Dauer (OnScan, TodayCrafts, RefreshAll-Auslöser), Profiler-Spitze je Minute.

### P-2 GoldSentinelMarkt v2 statt v6 (Schwere: MITTEL)
Die gemeinsame Datei ist "neueste Fassung gewinnt"; mit AHSentinel (v6) geladen ist v2 wirkungslos. Ohne AHSentinel läuft v2
mit den alten Mängeln (Feed in einem Stück, ~6,6 MB je Feed, Schalter stoppt geplante Antwort nicht – MN-S2).

### P-3 Smoketest zeigt FEHLER, zählt sie aber nicht (Schwere: NIEDRIG)
tests/smoketest.lua druckt "AUTOTEST OK 179 · FEHLER 25 …" und danach "AUTOTEST OK" (bewusst: Fallergebnisse im einfachen
Mock nur angezeigt, volle Prüfung in run_offline.py). Risiko: eine echte Regression fällt dort nicht auf. Massgeblich ist
run_offline.py (0 FEHLER).

### P-4 Rezept-Alarm meldet eine Summe (340) (Schwere: NIEDRIG, Psychologie)
psychologie.md "Einzelfall statt Summe": "340 fehlende Rezepte im AH" ist für den Spieler nicht handhabbar. Besser: die 1–3
günstigsten bzw. wertvollsten fehlenden Rezepte mit Preis und Figur nennen, Rest im Panel.

### P-5 Generische TOC lädt alle drei Datendateien (Schwere: NIEDRIG, zu messen)
ProfessionSentinel.toc (Interface 120105, 16001, 11509, 11508) lädt Data_Forever, Data_Era UND Data_Retail (2,3 MB Quelltext).
Welche TOC der Forever-Client wählt (_Camelot vs. generisch), im Spiel prüfen (/dump GetAddOnMetadata bzw. Speicher je Addon).
Wählt Forever die generische TOC, kostet Data_Retail Ladezeit/Speicher ohne Nutzen (falls die Datei nicht sofort abbricht).

## 4. Was gut ist (bleibt so)
- Klare Trennung ns.Foreign / ns.Act / ns.foreignTest (Tests verändern nie andere Addons), Sandbox in der Testroutine.
- Ereignis-Sturm-Schutz (Scan.QUIET, Fingerprint, portionierter Neuaufbau beim Herstellen).
- Breite Testabdeckung über vier Spielversionen, 64 Regressionen vorhanden.

## 5. Offene Fragen an den Nutzer (erst nach Freigabe)
- Soll PS wieder bearbeitet werden (PS-TC1/P-1 zuerst)? Bis dahin nichts beauftragt.
