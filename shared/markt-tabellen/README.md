# Markt-Tabellen (schwere Rechnung ausserhalb des Spiels)

Entscheid des Nutzers 14.11.2026 09:01: täglich neu rechnen, AHSentinel schlägt nur nach (kein Ruckeln).
Erzeugt von der Prüf-Sitzung (Werkzeuge in `addon-check/marktanalyse/`) aus den hochgeladenen Daten. Keine Spielernamen.

Datei: `GoldSentinelMarktTabellen.lua` – eine globale Tabelle, nur Zahlen:

```lua
GoldSentinelMarktTabellen = {
  v = 1, erstellt = 1794640000, datenBis = 1794636000,   -- Unix-Zeit
  wellen = { ["26-35"] = { zustand = "durch", index = 0.31, seit = 1794400000 }, ... },  -- "welle" | "durch" | "offen"
  verkauf = { de = { {bis = 0.90, n = 11, quote = 0.30}, {bis = 0.97, n = 10, quote = 0.33}, ... } },  -- je Warengruppe
  entzaubern = { ["2:4:a"] = { n = 450, gewinn = 0.35, chance = 1.05, menge = 1.00, mindest = 0.20 }, ... },
  kaufen = { { bis = 0.7, n = 175, gewinn = 0.44 }, { bis = 0.8, n = 234, gewinn = 0.33 }, ... },  -- Kaufpreis/Wert
  -- NEU 15.11.2026 (Masterplan AHSentinel E): Daten ALLER einsendenden Spieler (Bot-Sammelstelle, D-KERN1), fehlt ohne Daten
  alle = { v = 1, tage = 14, von = 1794..., bis = 1794...,
           felder = { "preis", "absatzMin", "absatzMax", "quellen", "tage", "scans" }, weggelassen = 0,
           H = { [2589] = { 120, 5.0, 7.0, 3, 2, 12 }, ... }, A = { ... } },   -- Schlüssel = Item-ID als ZAHL
}
```
Teil `alle` je Fraktion und Item: `preis` Median der Tages-Mediane (Kupfer, tiefster Stückpreis), `absatzMin`/`absatzMax`
Abgänge je Tag als Spanne (Summe/Summe über die Tage, gewichtet mit der Vergleichsdauer; `nil` = nicht gemessen), `quellen`
höchste Zahl einsendender Spieler an einem Tag (Untergrenze; Kennungen gibt die Sammelstelle nie heraus), `tage`, `scans`.
Aus den neuesten 14 Tagesdateien `testberichte/markt/tages/<JJJJ-MM-TT>.json`; Teil höchstens 40 KB – sonst fallen die Items
mit den wenigsten Scans weg (Anzahl in `weggelassen`). Test: `addon-check/test_markt_tabellen_alle.py`.

Erzeugen: `python3 -I addon-check/marktanalyse/markt_tabellen.py <AHSentinel.lua> [...] shared/markt-tabellen/GoldSentinelMarktTabellen.lua`
(täglich durch die geplante Aufgabe "Markt-Tabellen täglich"). Zählweisen wie im Addon: Verkauf = Anteil verkauft
(Fc:PostOutcome, Abbruch zensiert), Entzaubern Summe/Summe (KF2) mit DE30b-Mindestgewinn, Kaufen Gewinn je Kaufpreis/Wert
(SN-M), Wellen wie Waves.lua – OHNE den angefangenen letzten Tag; zusätzlicher Zustand "steigt" (2 Tage je > +10 %, nur Hinweis).
Auslieferung: AHSentinel nimmt bei jeder Version die neueste Datei unverändert ins ZIP (wie Wegdaten).

Regeln: Jeder Teil mit `n` (Fallzahl). AHSentinel nutzt einen Teil nur als Vorwissen (L2, k = 2); eigene Zählung geht vor.
Fehlt die Datei oder ein Teil: alles läuft ohne. Grösse < 50 KB. Format nur erweitern, nie umbauen (alte Clients).
