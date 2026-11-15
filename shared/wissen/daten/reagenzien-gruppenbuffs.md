# Reagenzien der Gruppenbuffs je Spielversion – aus den Spieldaten (Supervisor, 15.11.2026 21:18)

Quelle: wago.tools, Tabellen SpellReagents + SpellName (deDE) + ItemSparse (deDE), abgerufen 15.11.2026 21:18 aus der Prüf-Sitzung.
Zweige: wowf = WoW Forever 1.60.1.70938 · wow_classic_era = Era 1.15.9 · wow_anniversary = TBC 2.5.6 · wow_classic_titan = Wrath 3.80.2.
Jede Zeile: Zauber-ID, Name, Reagenz (Item-ID, Name), Menge. "–" = gibt es in diesem Zweig nicht. Für BuffSentinel BS-N1 Punkt 1.

| Zauber | Name (deDE) | Reagenz | Menge | wowf | Era | TBC | Wrath |
|---|---|---|---|---|---|---|---|
| 23028 | Arkane Brillanz (R1) | 17020 Arkanes Pulver | 1 | ja | ja | ja | ja |
| 27127 | Arkane Brillanz (R2) | 17020 Arkanes Pulver | 1 | – | – | ja | ja |
| 43002 | Arkane Brillanz (R3) | 17020 Arkanes Pulver | 1 | – | – | – | ja |
| 61316 | Brillanz von Dalaran | 17020 Arkanes Pulver | 1 | – | – | – | ja |
| 21849 | Gabe der Wildnis (R1) | 17021 Wilde Beeren | 1 | ja | ja | ja | ja |
| 21850 | Gabe der Wildnis (R2) | 17026 Wilder Dornwurz | 1 | ja | ja | ja | ja |
| 26991 | Gabe der Wildnis (R3) | 22148 Wilde Federranke | 1 | – | – | ja | ja |
| 48470 | Gabe der Wildnis (R4) | 44605 Wildes Wirbelkraut | 1 | – | – | – | ja |
| 21562 | Gebet der Seelenstärke (R1) | 17028 Heilige Kerze | 1 | ja | ja | ja | ja |
| 21564 | Gebet der Seelenstärke (R2) | 17029 Hochheilige Kerze | 1 | ja | ja | ja | ja |
| 25392 | Gebet der Seelenstärke (R3) | 17029 Hochheilige Kerze | 1 | – | – | ja | ja |
| 48162 | Gebet der Seelenstärke (höchster Rang Wrath) | 44615 Andachtskerze | 1 | – | – | – | ja |
| 27681 | Gebet der Willenskraft (R1) | 17029 Hochheilige Kerze | 1 | ja | ja | ja | ja |
| 32999 | Gebet der Willenskraft (R2) | 17029 Hochheilige Kerze | 1 | – | – | ja | ja |
| 48074 | Gebet der Willenskraft (höchster Rang Wrath) | 44615 Andachtskerze | 1 | – | – | – | ja |
| 27683 | Gebet des Schattenschutzes (R1) | 17029 Hochheilige Kerze | 1 | ja | ja | ja | ja |
| 39374 | Gebet des Schattenschutzes (R2) | 17029 Hochheilige Kerze | 1 | – | – | ja | ja |
| 48170 | Gebet des Schattenschutzes (höchster Rang Wrath) | 44615 Andachtskerze | 1 | – | – | – | ja |
| 20608 / 21169 / 27740 | Reinkarnation (Schamane) | 17030 Ankh | 1 | ja | ja | ja | ja |
| 25782, 25894, 25898, 25916, 25918 | Großer Segen (Macht, Weisheit, Könige …) | 21177 Symbol der Könige | 1 | ja | ja | ja | ja |
| 25890, 25895, 25899, 25919, 25920 | Großer Segen (Licht, Rettung, Refugium, Weisheit) | 21177 Symbol der Könige | 1 | – (wowf nicht in der Tabelle) | ja | teils | teils |
| 27141, 27143, 27145, 27169 | Großer Segen (TBC-Ränge) | 21177 Symbol der Könige | 1 | – | – | ja | 27141/27143 |
| 48933, 48934, 48937, 48938 | Großer Segen (Wrath-Ränge) | 21177 Symbol der Könige | 1 | – | – | – | ja |

Wichtig für die Zählung (kein Fehlalarm):
- Priester: welches Reagenz gebraucht wird, hängt vom HÖCHSTEN gelernten Rang ab (R1 Heilige Kerze 17028, ab R2 Hochheilige
  Kerze 17029, Wrath höchster Rang Andachtskerze 44615). Zählen nur das Reagenz des höchsten gelernten Rangs (IsSpellKnown je ID).
- Druide: R1 17021, R2 17026, R3 22148, R4 44605 – ebenso nach höchstem gelernten Rang.
- 22147 Flintgrassaat gehört zu Wiedergeburt 26994 (TBC/Wrath), NICHT zur Gabe der Wildnis.
- Zweig wowf enthält einige Grosse Segen NICHT (Spalte "–"): dort nur die Zauber zählen, die der Spieler kennt.
- Namen sind die Spieldaten-Namen (deDE), z. B. "Hochheilige Kerze", "Wilde Federranke" – nicht aus dem Gedächtnis übersetzen.
