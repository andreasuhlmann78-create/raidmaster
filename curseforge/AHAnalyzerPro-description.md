# AH Analyzer Pro

**Market analysis, sniper and gold-making toolkit for the auction house – built for WoW Forever and Classic.**

AH Analyzer Pro scans the auction house, keeps a price history for every item and turns it into market values, trends and charts. On top of that it finds bargains for you, helps you sell at the right price and keeps a ledger of everything you earn and spend. It runs as its own tab inside the auction house window and speaks the language of your WoW client.

---

## Features

### Market data
- **Full market scan** with price history for every item
- **Market value** = median of the last 14 days, so single outliers barely count
- **Trends and charts** with time-based EMAs (6 hours, 1 day, 7 days) and crossover markers
- **Bait-offer protection:** a single cheap unit at the bottom of a commodity is recognised and ignored everywhere – no fake market values, no false sniper hits
- Suspiciously cheap prices are re-checked automatically before they count
- **Price sync** between all players using the addon
- Prices and a small price chart in **every item tooltip**, plus vendor price and disenchant value

### Buying
- **Sniper:** targets with max price, quantity, budget, rarity, item level and level filters – searches on its own while the auction house is open
- **Bargain watcher:** searches trade goods (herbs, ore, cloth, leather, enchanting, elemental, gems, cooking …) for anything at or below x % of market value, with sound and chat alert
- **Buy with one mouse-wheel notch** (or your own key binding); the price is confirmed in advance, nothing is bought if it rose meanwhile
- **Shopping lists** with quantities – check all prices at once or turn missing items into sniper targets
- **Watchlist** with alerts

### Selling
- **Sell tab:** price check and undercut suggestion (1 copper, 1 % or 5 %), deposit, AH cut and proceeds – warns when a vendor pays more or when you would sell below your purchase price
- **Series posting:** posts every bag item with a remembered price, one click per auction
- **Auctions tab:** status of your auctions (lowest / tied / undercut / sold) and cancel with one click
- **Collect AH mail** – gold and items from all auction mail with one click (COD is never paid)

### Profit & bookkeeping
- **Ledger:** income after the AH cut, spending, deposits and profit for today / 7 days / 30 days / all time – read from your mailbox invoices, nothing counted twice
- Statistics: sell-through per item, best selling hours and weekdays
- **Profit tab:** bargains below market value, below vendor price or below disenchant value; flipping calculator
- **Professions:** material cost, value of the result and profit for every recipe, best recipes, materials straight to a shopping list
- **Disenchant values that learn** from your own disenchants
- **Alts & gold:** gold, bags and bank of all your characters, gold history of the last 30 days
- CSV export

### Comfort
- Two designs: **Classic** (looks like the WoW auction house) and **Modern**
- Item search by name in any language, by item ID or by shift-click, with suggestions while typing
- Built-in item name list (~23,000 items in 10 languages)
- Help page for every tab, right-click menu on every item, minimap button

---

## Languages

English, German, French, Spanish (EU and Latin America), Portuguese, Italian, Russian, Korean, Chinese (simplified and traditional). The addon follows your client language automatically; you can switch it with `/ahp language`.

## Game versions

Made and tested for **WoW Forever** and Classic Era. The addon is flagged for all current WoW flavours (Classic Era, TBC, Wrath, Cataclysm, Mists of Pandaria Classic, Retail).

## Commands

| Command | Action |
|---|---|
| `/ahp` | open / close the window |
| `/ahp scan` | start a full market scan |
| `/ahp sniper` | sniper on / off |
| `/ahp sync` | price sync on / off |
| `/ahp lists` | shopping lists |
| `/ahp options` | options |
| `/ahp design` | switch between Classic and Modern |
| `/ahp language` | change the addon language |
| `/ahp export` | CSV export |
| `/ahp help` | help |
| `/ahp reset` | reset window and button positions |

Everything can also be done with the mouse.

---

## Credits & license

Made by **GoldSentinel**. Licensed under **GPL-3.0-or-later**.
Item names from [QuestieDB](https://github.com/Questie/QuestieDB) (GPL-3.0) and [wow-classic-items](https://github.com/nexus-devs/wow-classic-items) (MIT) – thank you!
World of Warcraft and all item names © Blizzard Entertainment.
