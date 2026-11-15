# Auswertung Kaufen → Entzaubern → Verkaufen (15.11.2026, 11:51–15:01)

Quelle: AHSentinel-SavedVariables (Uploader-Stand 15.11. 15:01), books.log (buy/de/sale/fee) und deLog. Supervisor, mit Lua nachgerechnet.

## Gekauft (Sniper)
- Schultern des Hügelwächters (4251): 224 Stück, 19g37s99 (Ø 8s65)
- Azurblaue Seidenkapuze (7048): 16 Stück, 1g41s06 (Ø 8s81)
- Summe 240 Stück, 20g79s05

## Entzaubert: 227 Stück (Einstand 19g66s47)
| Quelle | Anzahl | Große Astralessenz | Seelenstaub | Gr. glitzernder Splitter |
|---|---|---|---|---|
| 4251 | 218 | 72 | 240 | 8 |
| 7048 | 9 | 5 | 10 | 0 |

## Verkaufspreise (Brutto je Stück, nach Stunde; stabil)
- Große Astralessenz: 15s36 (11 h) · 15s04 (12 h) · 14s93 (14 h)
- Seelenstaub: 4s25 (11 h) · 4s24 (12–13 h) · 4s19 (14 h)
- Splitter: 36s97 (11 h) · 36s76 (14 h)
- Verkauft in der Zeit: 417 Stück, brutto 30g64s56, netto 29g10s93 (5,0 % Gebühr) – teils Ware von vorher.

## Ergebnis (Kette, zu den Preisen von 14 h, netto nach 5 %)
- Wert je entzauberter Schulter: (72×14s18 + 240×3s98 + 8×34s92) / 218 = 10s35 → Gewinn 1s70 je Stück (+19,6 %)
- 218 Schultern: Wert 22g55s52 − Einstand 18g85s02 = **+3g70s50**
- 9 Kapuzen: Wert 1g10s70 − 81s45 = +29s25 (zu wenig Stück, Verdacht)
- Gesamt ≈ **+4g00** in ~3 h 10 min (≈ 1g26/h), Einlage-Verluste 10s65 abziehen → ≈ +3g89
- Gewinnschwelle Schulter: 10s35 Einkaufspreis. Sniper-Max 9s14 → mindestens 1s21 Gewinn je Stück.

## Risiken
- Seelenstaub trägt 42 % des Werts: −1s beim Staub ≈ −1s10 je Schulter.
- Splitter (3,7 % Chance, 35s) tragen 12 % – Schwankung bei kleinen Mengen.
- Tooltip AHS "Seelenstaub Gewinn −19c/Stück" widerspricht dem Ergebnis der Kette: Einstand verkaufter Seelenstaub laut AHS
  5s06/Stück (16g33s02 / 323), bei Aufteilung nach Marktwert wären es ~3s30. Verdacht: Einstand-Aufteilung beim Entzaubern
  (oder ältere, teurere Ware) – Messauftrag an AHS (DE-AUFT1).

## BERICHTIGUNG 16:22 (Supervisor)
Die Rechnung oben nutzt die Ausbeute NUR der 218 Schultern dieses Zeitraums (Glück/Pech dieser Stichprobe, z. B. Splitter 3,7 %).
Die Entzauber-Tabelle hängt im Spiel nur von Qualität und Itemstufe ab. Über die ganze Gruppe "grüne Rüstung 26–30"
(965 Entzauberungen: Staub 1,117, Essenz 0,318, Splitter 0,053 je Entzauberung) ist der ERWARTETE Netto-Wert je Schulter
≈ 10s73 (= Tooltip). Erwarteter Gewinn je Schulter bei Einstand 8s65: ≈ +2s08; bei Sniper-Max 9s14: ≈ +1s59.
Real erzielt in diesem Zeitraum: +1s70 je Schulter (weniger Splitter als erwartet). Der Verdacht TT-DE3 war falsch.
