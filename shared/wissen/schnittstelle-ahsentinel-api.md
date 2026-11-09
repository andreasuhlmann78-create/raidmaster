# Schnittstelle AHSentinel.API (Version 1) – Vertrag zwischen AHSentinel und anderen Addons

Festgelegt von der Prüf-Sitzung am 9.11.2026. AHSentinel stellt sie bereit, ProfessionSentinel (und künftig andere
GoldSentinel-Addons) benutzen sie. Rechenregeln: shared/wissen/wirtschaft-forever.md.

## Zugriff
- Global `AHSentinel` (neuer Name) mit Feld `API`. Alias: `AHAnalyzerPro.API` (alter interner Name, bleibt bestehen).
- `AHSentinel.API.version` = 1. Neue Funktionen nur hinzufügen, nie Bedeutung oder Rückgabewerte ändern; bei
  Bruch Version 2 mit neuem Feld, Version 1 bleibt.
- Jede Funktion ist sicher: wirft nie einen Lua-Fehler (intern pcall), gibt `nil` zurück, wenn nichts bekannt ist.
- Alle Beträge in Kupfer (ganze Zahlen), je Stück, wenn nicht anders gesagt.

## Funktionen (Version 1)
| Funktion | Rückgabe |
|---|---|
| `API.Price(itemID)` | Preis je Stück, Quelle (`"scan"`, `"market"`, `"vendor"`), Alter in Sekunden |
| `API.NetSale(itemID, qty)` | Netto-Erlös gesamt für qty Stück nach 5 % (bzw. 15 % neutral) und erwartetem Einzahlungsverlust, mindestens Händlerwert; 2. Wert Tabelle `{ gross, cut, depositRisk, vendorWins }` |
| `API.Deposit(itemID, qty, hours)` | Einzahlung (Blizzard-Wert, sonst Formel nach Regelwerk, Minimum gemessen statt fest) |
| `API.CutPct()` | 0.05 (Fraktions-AH) oder 0.15 (neutral) |
| `API.MaterialCost(itemID, qty)` | Kosten gesamt über den günstigsten Weg; 2. Wert Liste `{ { itemID, qty, source = "ah"/"vendor"/"craft", cost } }` |
| `API.DisenchantValue(itemID)` | Wert brutto je Entzauberung, Wert netto, Anzahl eigene Entzauberungen der Gruppe, Quelle (`"own"`, `"table"`); `nil` wenn nicht entzauberbar |
| `API.BestWay(itemID)` | `"sell"` oder `"disenchant"`, Netto-Wert dieses Wegs |
| `API.SellSpeed(itemID)` | Zustand (`"fast"`, `"slow"`, `"rare"`, `nil`), Median-Stunden bis Verkauf, Absatz pro Tag am Markt |
| `API.MinProfitPct()` | eingestellter Mindestgewinn in % (Standard 20) |
| `API.GoldPerHour(kind)` | Kupfer pro Stunde und gemessene Sekunden für `"craft"`, `"disenchant"`, `"flip"`, `"ah"`, `"all"` – `nil`, solange nicht gemessen (kommt mit H9) |
| `API.LastScan()` | Zeitpunkt des letzten Scans (time()), Anzahl Items |

## Ereignis
- AHSentinel ruft nach jedem Scan und jeder Buchungsänderung `AHSentinel.API.OnChanged`-Abonnenten auf:
  `AHSentinel.API.Subscribe(fn)` – `fn(reason)` mit `"scan"`, `"ledger"`, `"settings"`. Aufrufe gedrosselt (höchstens
  einmal je 2 s), nie im Kampf-kritischen Pfad.
