## ⚠️ WICHTIGES UPDATE – bitte aktualisieren / IMPORTANT UPDATE – please update

> Beta-Version. Bitte melde Fehler in den Kommentaren auf CurseForge, am besten mit der Lua-Fehlermeldung und der WoW-Version.
> Beta version. Please report errors in the comments on CurseForge, ideally with the Lua error message and your WoW version.

### Deutsch – das Wichtigste seit 0.65.393

- **Kein Lua-Fehler „integer overflow“ mehr:** sehr grosse Beträge (über 214 748 Gold in Kupfer, z. B. ein Angebot zum Höchstpreis 9 999 999g 99s 99c) werden überall ohne Fehler angezeigt und gespeichert – bisher war das nur beim CSV-Export behoben. Normale Beträge erscheinen genau wie bisher.
- **Angebote zum Höchstpreis** ergeben keinen unsinnigen Trend mehr (vorher z. B. „+10526315689 %“).
- **Vollscan braucht viel weniger Speicher:** die Preisleitern aller Items liegen kompakt (etwa ein Fünftel), und nach jedem Scan werden deutlich weniger neue Tabellen angelegt. Preise, Tooltips, Empfehlungen und Nachrichten an Mitspieler bleiben genau gleich.
- **Kein Absatz mehr für Ware, die nicht mehr angeboten wird** (vorher z. B. 1972/Tag bei 0 Angeboten).
- **Ruhigerer Wächter-Reiter** und gekürzte Item-Namen in den Markt-Details mit dem ganzen Namen beim Darüberfahren.

### English – the most important changes since 0.65.393

- **No more "integer overflow" Lua error:** very large amounts (above 214,748 gold in copper, e.g. a listing at the maximum price 9,999,999g 99s 99c) are shown and saved everywhere without an error – before, this was only fixed for the CSV export. Normal amounts look exactly as before.
- **Listings at the maximum price** no longer produce a nonsensical trend (before e.g. "+10526315689 %").
- **The full scan needs much less memory:** the price ladders of all items are kept compact (about a fifth), and far fewer new tables are created after every scan. Prices, tooltips, recommendations and messages to other players stay exactly the same.
- **No sell-through for goods that are no longer offered** (before e.g. 1972/day with 0 offered).
- **Calmer Watcher tab** and shortened item names in the market details show the full name on hover.
