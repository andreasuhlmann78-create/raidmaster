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
Seit 16.11.2026 03:0x (erste echte Tagesdatei 2026-11-14: 1 Scan, 1 Quelle, kein Vergleich): nur Items MIT gemessenem Absatz und mit
mindestens 2 Quellen an einem Tag (eine Quelle ist meist der Spieler selbst – sonst zählt AHSentinel seine eigenen Daten doppelt).
Weggelassene werden gezählt: `ohneAbsatz`, `eineQuelle`. Ohne passende Items hat der Teil nur die Kopfwerte (kein H/A).

Teil `kern` (16.11.2026, Entscheid des Nutzers 04:51/04:52 – Kern und Prüf-Sitzung tauschen Daten aus): `kern[Weg][Zelle] = { p = Anteil, n = Fälle }`,
gelesen von Kern.lua `K:TableCell` (Vorwissen L2, k = 2). Aus den Zählern `AHSentinelDB.kern` (je Kern-Speicher nur der neueste Stand, erkannt an
`kern.since`), Gewicht wie Kern.lua (≤ 14 Tage 1, ≤ 30 Tage 0,5). Nur Wege über den Markt (`markt`, `gilde`) und nur, wenn der Weg die Güte-Prüfung
besteht (n ≥ 30, Brier besser als die Grundlinie, Brier < 0,20); nie `sell` (steht in `verkauf`, sonst doppelt), nie `buy*`/`marktu`. Zellen erst ab
n ≥ 30. Kopf `kernInfo = { quellen, zellen }`. Regeln und Test: `addon-check/marktanalyse/kern_daten.py`, `test_kern_daten.py` (15/15).
Journale: verkauf/entzaubern/kaufen rechnen über ALLE übergebenen Stände (Tages-Sicherungen, beide Rechner), zusammengeführt ohne Doppelte
(`merge_journals`: Schlüssel = Felder, die sich nie ändern; jeder Schlüssel aus dem neuesten Stand mit allen Vorkommen). Darum alle Stände übergeben:
`python3 -I addon-check/marktanalyse/markt_tabellen.py $(find <goldsentinel-daten> -path "*forever*" -name AHSentinel.lua | sort) <ausgabe.lua>`.
Auswertung und Abgleich mit dem Kern (bei jeder neuen Tabelle): `python3 -I addon-check/marktanalyse/kern_abgleich.py <dieselben Stände>
--aus testberichte/markt/kern/<JJJJ-MM-TT>.md` – Stand je Weg (wie K:Show), Abgleich Verkauf/Kaufen, harte Prüfung "jeder Verkaufsfall genau einmal im
Kern", Rückgabe an den Kern.

Erzeugen: `python3 -I addon-check/marktanalyse/markt_tabellen.py <AHSentinel.lua> [...] shared/markt-tabellen/GoldSentinelMarktTabellen.lua`
(täglich durch die geplante Aufgabe "Markt-Tabellen täglich"). Zählweisen wie im Addon: Verkauf = Anteil verkauft
(Fc:PostOutcome, Abbruch zensiert), Entzaubern Summe/Summe (KF2) mit DE30b-Mindestgewinn, Kaufen Gewinn je Kaufpreis/Wert
(SN-M), Wellen wie Waves.lua – OHNE den angefangenen letzten Tag; zusätzlicher Zustand "steigt" (2 Tage je > +10 %, nur Hinweis).
Auslieferung: AHSentinel nimmt bei jeder Version die neueste Datei unverändert ins ZIP (wie Wegdaten).

Regeln: Jeder Teil mit `n` (Fallzahl). AHSentinel nutzt einen Teil nur als Vorwissen (L2, k = 2); eigene Zählung geht vor.
Fehlt die Datei oder ein Teil: alles läuft ohne. Grösse < 50 KB. Format nur erweitern, nie umbauen (alte Clients).
