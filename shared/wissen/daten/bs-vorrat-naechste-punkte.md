# BuffSentinel – Spieldaten für die nächsten Vorrats-Punkte (Supervisor, 15.11.2026 22:06)

Quelle: wago.tools (SpellName deDE, SpellEffect.EffectItemType, SpellAuraOptions.ProcCharges, ItemSparse deDE, Item, ItemEffect,
ItemXItemEffect, ItemPetFood), Zweige wowf 1.60.1.70938 · Era 1.15.9 · TBC (wow_anniversary) 2.5.6 · Wrath (wow_classic_titan) 3.80.2.
Antwort auf berichte/BuffSentinel/…-frage (21:56).

## 1 Managem (Magier) – Herbeizaubern-Zauber -> Item
| Zweig | Zauber -> Item |
|---|---|
| wowf | 759 -> 5514 Manaachat · 3552 -> 5513 Manajadestein · 10053 -> 8007 Manacitrin · 10054 -> 8008 Manarubin |
| Era | wie wowf; weitere Zauber-IDs ohne direkten Item-Weg: 1210, 3553, 3724, 10055, 10056 (nur für "gelernt" zählen) |
| TBC | wie wowf + 27101 -> 22044 Manasmaragd; 36883 Manadiamant herbeizaubern (Item nicht direkt verknüpft) |
| Wrath | 759/3552/10053/10054/27101 wie oben + 42985 -> 33312 Manasaphir · 42986 -> 36799 Manaopal; weitere Zauber 1210, 3553, 10055, 10056, 27390, 36883 |
Regel wie Gesundheitsstein: irgendein Zauber der Zeile gelernt UND keines der Items in den Taschen -> Warnung.

## 2 Inneres Feuer (Priester) – Aufladungen (ProcCharges)
Dein Verdacht "in Era/wowf keine Aufladungen" stimmt NICHT: alle Spieler-Ränge haben **20** Aufladungen in ALLEN Zweigen.
wowf: 588, 602, 1006, 7128, 10951, 10952 = 20 · Era: dieselben = 20 (weitere IDs 609, 624, 1007, 1252–1254, 7129, 7130, 11025, 11026 = 0,
keine Spieler-Ränge) · TBC: + 25431 = 20 · Wrath: + 48040, 48168 = 20.

## 3 Tierfutter (Jäger)
Nur **wowf** hat in den Spieldaten je Item die Futterart (Item.ItemPetFoodID): 411 Items. Era/TBC/Wrath: Spalte fehlt -> Punkt dort weglassen.
Liste: shared/wissen/daten/BuffSentinelVorratDaten.lua (wowf.futter[Item-ID] = Futterart, futterNamen deDE/enUS für den Abgleich mit
GetPetFoodTypes()). Unverändert ins Addon übernehmen erlaubt (reine Zahlen-Daten, wie LevelPilot_Data).

## 4 Seelenstein (Hexenmeister)
- Aura "Seelenstein-Auferstehung": 20707, 20762, 20763, 20764, 20765 (alle Zweige) + TBC/Wrath 27239 + Wrath 47883.
  (TBC/Wrath schreiben "Seelensteinauferstehung" ohne Bindestrich – Namen nie vergleichen, nur IDs.)
- Herstellen: wowf 693, 1377, 20022, 20752, 20755, 20756, 20757 · Era zusätzlich 719, 20766–20769 · TBC/Wrath zusätzlich 27238 · Wrath 47884.
- Items: 5232 Schwacher, 16892 Geringer, 16893 Seelenstein, 16895 Großer, 16896 Erheblicher Seelenstein · TBC/Wrath + 22116 Meisterlicher ·
  Wrath + 36895 Dämonischer Seelenstein. (1199 "Aufgeladener Seelenstein" ist ein anderes Item.)

## 5 Getränke (Manaklassen)
Items mit Benutz-Zauber "Trinken": wowf 39, Era 28, TBC 51, Wrath 64 – Liste in BuffSentinelVorratDaten.lua (<zweig>.getraenke).
"Essen und Trinken" ohne eigenen Zauber "Trinken" sind nicht dabei (Verdacht: zählt kaum; im Client prüfen).
