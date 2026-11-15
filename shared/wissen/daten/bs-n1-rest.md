# BuffSentinel BS-N1 Rest – Spieldaten (Supervisor, 15.11.2026 22:48)

Quelle: wago.tools ItemSparse (BagFamily, TotemCategoryID, deDE), SpellReagents, SpellName (deDE), SpellTotems, TotemCategory (deDE).
Zweige: wowf 1.60.1.70938 · Era 1.15.9 · TBC (wow_anniversary) 2.5.6 · Wrath (wow_classic_titan) 3.80.2. Antwort auf Frage 22:42.

## 1 Seelensplitter-Platz (Hexer)
Item 6265 Seelensplitter: **BagFamily = 4** in allen vier Zweigen (Bit 3, Wert 4 = Seelentasche). Freier Platz zählt in Taschen mit
bagType 0 (normale Tasche) oder bagType mit Bit 4 gesetzt (bit.band(bagType, 4) ~= 0). Keine Item-Liste nötig.

## 2 Federn (Priester Levitieren / Magier Langsamer Fall)
Reagenz **17056 Leichte Feder** ×1 in ALLEN vier Zweigen (auch Wrath – nicht entfernt):
Levitieren 1706 (alle), 27986 (alle), 461329 (wowf, Era) · Langsamer Fall 130 (alle). Andere gleichnamige IDs haben kein Reagenz
(NPC-/Gegenstands-Zauber) – nur die genannten IDs zählen.

## 3 Göttliches Eingreifen (Paladin)
Zauber 19752 -> Reagenz **17033 "Symbol der Offenbarung"** ×1 (alle Zweige). Achtung Name: in den Daten heisst es "Symbol der
Offenbarung", nicht "Symbol der Göttlichkeit". 19753/19754 ohne Reagenz.

## 4 Totems (Schamane)
- **Era**: Zauber verlangen das Totem-ITEM direkt (SpellTotems.Totem): 5175 Erdtotem (22 Zauber), 5176 Feuertotem (67), 5177 Wassertotem (18),
  5178 Lufttotem (15).
- **wowf, TBC, Wrath**: Zauber verlangen eine Totem-KATEGORIE (RequiredTotemCategoryID): 2 Erdtotem, 3 Lufttotem, 4 Feuertotem, 5 Wassertotem.
  Items je Kategorie (ItemSparse.TotemCategoryID): 2 -> 5175, 3 -> 5178, 4 -> 5176, 5 -> 5177. TBC/Wrath zusätzlich Kategorie **21 Meistertotem**
  (Maske 15 = alle vier): TBC 1500; Wrath 1500, 22345, 22395, 22396, 23005, 23199 (die Wrath-Relikte "Totem des …").
  wowf: zusätzlich 3 Zauber direkt mit Item (15786 Totem der Erdbindung -> 5175; 8262 -> 5177; Feuernova 8349–8351 u. a. -> 5176).
- Regel: Element gilt als vorhanden, wenn in den Taschen ein Item der Kategorie liegt ODER ein Meistertotem (21). Ob ein im Relikt-Platz
  ANGELEGTES Meistertotem zählt: Verdacht, im Client prüfen (Wrath) – bis dahin auch den Relikt-Platz mitzählen und im Bericht kennzeichnen.

## 5 Zorn der Gerechtigkeit (Paladin)
Aura-IDs: wowf 25780, 407627, 407628 · Era 25780, 25781, 20450, 407627, 407628 · TBC/Wrath 25780, 25781. (Nur IDs vergleichen.)

## 6 Wasserwandeln / Wasseratmung (Schamane)
Wasserwandeln 546 -> **17058 Fischöl** ×1 · Wasseratmung 131 -> **17057 Glänzende Fischschuppen** ×1 (alle Zweige; andere gleichnamige IDs ohne Reagenz).
