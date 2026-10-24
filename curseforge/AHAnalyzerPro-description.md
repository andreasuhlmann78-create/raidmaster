# AH Analyzer Pro

**Market analysis, sniper and gold-making toolkit for the auction house – for every WoW version.**

> ⚠️ **Version 0.59.22 is a beta.** It may still contain bugs. If you run into an error or unexpected behaviour in-game, please report it in the comments – ideally with the Lua error message (if any) and the WoW version you play on.

AH Analyzer Pro scans the auction house, keeps a price history for every item and turns it into market values, trends and charts. It finds bargains for you, helps you sell at the right price and keeps a ledger of everything you earn and spend. It runs as its own tab inside the auction house window, can be used completely with the mouse and speaks the language of your WoW client.

---

## What's new in 0.59.22

- **New Buy tab** (next to Overview) – works like the auction house's own Buy tab: search, categories, level, rarity. Categories show **instantly** from your last scan while the live search updates them in the background
- **Sniper and Watcher search as often as the server allows** and take turns – the Sniper hunts your targets, the Watcher finds lucky bargains. The speed adjusts itself to the limit of every WoW version
- **The Sniper keeps searching after a hit** – the hit stays buyable with one mouse-wheel notch and the sound repeats while it's there
- **Bait offers** (single units at the very bottom) are no longer shown anywhere and never count for prices
- **Page bar in every list** (‹ 1 2 3 … 20 ›), draggable scrollbars, **Item column sorts by rarity, then name**, new **iLvl** column
- **Size in auction house** option (100–160 %) for large screens
- The AH Analyzer tab **no longer overlaps TSM, Auctionator & co.**
- **Classic auction house** (Classic Era, TBC Anniversary, Wrath): full support, all result pages are read
- **Back button** in the price history, rarity picker with checkboxes everywhere, new look with icons and gold accents, smooth scanning without stutter

---

## Features

### Market data
- **Full market scan** with price history for every item
- **Market value** = median of the last 14 days, so single outliers barely count
- **Trends and charts** with time-based EMAs and crossover markers
- **Bait-offer protection** and automatic re-checks of suspiciously cheap prices
- **Price sync** between all players using the addon
- Prices and a small price chart in **every item tooltip**, plus vendor price and disenchant value

### Buying
- **Sniper:** targets with max price, quantity, budget, rarity, item level and level filters – searches on its own while the auction house is open
- **Bargain watcher:** herbs, ore, cloth, leather, enchanting, elemental, gems, cooking and more – anything at or below x % of market value (default 50 %); never weapons or armour
- **One-notch buying** with the mouse wheel or your own key binding
- **Shopping lists** with quantities – check all prices at once or turn missing items into sniper targets; items already in your bags are subtracted
- **Watchlist** with alerts

### Selling
- **Sell tab:** price check and undercut suggestion (1 copper, 1 % or 5 %), deposit, AH cut and proceeds – warns when a vendor pays more or when you would sell below your purchase price
- **Series posting:** posts every bag item with a remembered price, one click per auction
- **Auctions tab:** status of your auctions (lowest / tied / undercut / sold), cancel with one click
- **Collect AH mail:** gold and items from all auction mail with one click (COD is never paid)

### Profit & bookkeeping
- **Ledger:** income after the AH cut, spending, deposits and profit for today / 7 days / 30 days / all time – read from your mailbox invoices, nothing counted twice
- **Statistics:** sell-through per item, best selling hours and weekdays
- **Profit tab:** bargains below market value, below vendor price or below disenchant value; flipping calculator
- **Professions:** material cost, value of the result and profit for every recipe, best recipes, materials straight to a shopping list
- **Vendor prices** are learned automatically at every merchant
- **Alts & gold:** gold, bags and bank of all your characters, gold history of the last 30 days
- **CSV export**

### Comfort
- Two designs: **Classic** (looks like the WoW auction house) and **Modern**
- Item search by name in any language, by item ID or by shift-click, with suggestions while typing
- Built-in item name list (~23,000 items in 10 languages)
- Help page for every tab, right-click menu on every item, minimap button

---

## Supported game versions

| Game version | Status |
|---|---|
| WoW Forever | main version |
| Classic Era | supported (beta) |
| TBC Anniversary, Wrath Classic, Wrath Titan Reforged | supported (beta) |
| Cataclysm Classic, Mists of Pandaria Classic | supported (beta) |
| Retail | supported (beta) |

One download for everything – just copy the folder `AHAnalyzerPro` into `Interface\AddOns` of your game.

## Languages

English, German, French, Spanish (EU and Latin America), Portuguese, Italian, Russian, Korean, Chinese (simplified and traditional). The addon follows your client language automatically; you can change it in the options or with `/ahp language`.

## Commands

Everything works with the mouse – the commands are optional.

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

---

## Feedback

Found a bug or have an idea? Leave a comment here on CurseForge – bug reports with the Lua error message and your WoW version help the most.

## Credits & license

Made by **GoldSentinel**. Licensed under **GPL-3.0-or-later**.
Item names from [QuestieDB](https://github.com/Questie/QuestieDB) (GPL-3.0) and [wow-classic-items](https://github.com/nexus-devs/wow-classic-items) (MIT) – thank you!
World of Warcraft and all item names © Blizzard Entertainment.
