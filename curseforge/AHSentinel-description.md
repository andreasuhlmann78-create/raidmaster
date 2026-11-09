# AHSentinel

**Market analysis, sniper and gold-making toolkit for the auction house – for every WoW version.**

> ⚠️ **This addon is in beta.** It may still contain bugs. If you run into an error or unexpected behaviour in-game, please report it in the comments – ideally with the Lua error message (if any) and the WoW version you play on.

> 🔁 **Formerly "AH Analyzer Pro".** Since version 0.62.0 the addon is called **AHSentinel**. Your saved data is taken over automatically on the first login. The zip now contains only the folder `AHSentinel` – if the old folder `AHAnalyzerPro` is still in your AddOns, AHSentinel tells you once in the chat: just delete it. The new command is `/ahs` (`/ahp` still works).

AHSentinel scans the auction house, keeps a price history for every item and turns it into market values, trends and charts. It finds bargains for you, helps you sell at the right price and keeps a ledger of everything you earn and spend. It opens in its own resizable window with just five tabs – **Overview, Buy, Sell, Market, Ledger** – can be used completely with the mouse and speaks the language of your WoW client.

---

## What's new

### Version 0.65.35

- **AH fee in the profit window – one visible assumption:** the fee depends on how many pieces you post per auction
  (at least 1s per auction). The window now says it: "at N pieces per auction (learned / chosen / cautious)".
  Learned from your own postings (median of the last 10); without data 1 piece. Click it to switch 1 / 5 / 20 (stack)
  / automatic, remembered per item. "Best recipes", "Do today" and other addons use the same assumption. The window
  no longer switches between two calculations when item data loads late. (Example: 1 Bolt of Woolen Cloth at 3s 97c,
  materials 3s 42c: fee 1s, loss 45c; at 20 per auction: 20c, profit 35c.)
- **Selling: quantity = everything in your bags** (no longer the last quantity). You change the number yourself.
- **Ledger (WoW Forever):** a sale is booked with the gold the mail really brings – the fee was already booked when
  posting, so no second fee and no refund are deducted. The invoice values go to the diagnostic log (RECHNUNG).
  Cancelling an auction now books the measured refund. Era/TBC unchanged.
- Playtest: new check S10 – AHSentinel's AH fee equals Blizzard's "Deposit" for the same quantity.

### Version 0.65.34

- **Bulk buying for disenchanting** (Buy tab → Buy): the button "Worth disenchanting" below the categories shows from
  your search only items (armor/weapons) whose disenchant value exceeds the price by the minimum return, with at
  least 10c profit per item – sorted by profit, with columns disenchant value, profit and return %.
  - Every mouse wheel notch over the list, or "Buy next", buys the next item from the top (the first notch loads its
    offers). Before each purchase: offer still there and not more expensive – otherwise skipped.
  - Limits: "at most X gold" (default 5g) and "return from X %" (default 20 %). Stops at the limit, with full bags
    or in combat. Below 10 real disenchants of the group the value counts 10 % less.
  - Status line: "Bought N · paid · expected +profit". Only on your click/notch, never automatic; logged as KAUF
    (no names). No skill filter – in WoW Forever everything can be disenchanted from Enchanting 1.

### Version 0.65.33

- **AH fee in the profit window corrected:** the fee per piece assumed you always post a full stack (e.g. 20 Bolts of
  Woolen Cloth) and split the 1s minimum fee by 20 – so 1 bolt at 3s 98c showed 20c instead of the real 1s. Now the fee
  follows how many pieces you last posted of this item at once; without experience 1 piece (full 1s minimum fee).

### Version 0.65.32

- **Disenchant table from Disenchantry:** the table now follows Disenchantry 1.1.2 (MIT license, Copyright (c) 2026
  x_Raven_x; license text in LICENSE-Disenchantry.txt), based on warcraft.wiki.gg: item level 5–15 without shards
  (80/20), 21–25 armor 75/15/10, 51–65 weapons 75/22/3, **WoW Forever: green weapons item level 21–30 give Greater
  Magic Essence**, blue items from item level 1 and up to 80, epics up to 88. Groups are by item level (as in the
  table), not by required level.
- The material block now shows the quantity range from the table ("1–2×"), from real disenchants the average.
- **Disenchantry loaded:** AHSentinel shows no second material block.

### Version 0.65.31

- **One price for everything:** AHSentinel now values every item with ONE function – tooltip, profit window
  (product and materials), bargains, flips, "Do today", disenchant (block and value), inventory value and the vendor
  comparison all show the same value for the same item. Order of sources: your own sales of the last 14 days, then
  just below the cheapest current offer (at most the median), then the 14-day median. Offers below 10 % or above 300 %
  of the median don't count. For bargains and flips the cheap offer itself is not used as resale value.
- **Real value in the tooltip:** new line "Real value (after fees)" with its source (own sales / AH now / market /
  vendor) and "price old" after 6 hours; hold Shift to see each part (own sales, cheapest offer, median, fee).
- **Vendor price as floor:** if a vendor pays more than the auction house after fees, the vendor price counts.
- Other addons (ProfessionSentinel) can use the same values: `AHAnalyzerPro:RealPrice(itemID)` and
  `AHAnalyzerPro:RealValue(itemID, qty)`; the old `GetSalePrice` now returns the same value.

*Older versions: see the changelog of each file in the **Files** tab.*

---

## ☕ Support the addon

AHSentinel is free and made in my spare time. If it helps you make gold, you can support it with a small donation – thank you so much!

**[Donate with PayPal](https://www.paypal.com/ncp/payment/46R68N2BF7BTY)**

In-game: the **Support** button in the addon window (or `/ahs donate`).

---

## Features

### Today – what makes the most gold right now
- One button (or `/ahs today`) lists the best actions right now, sorted by net profit: flips, buying below vendor or disenchant value, selling from your bags, reposting returned auctions
- **Every row has a button with the next step – right in the list:** *Check* shows the real current offer, *Buy* buys it (never more expensive and never more than suggested), flips then get *Post*
- **Crafting:** profitable recipes you already know, with a button that adds the missing reagents as buy rows (with **ProfessionSentinel** also missing recipes, vendors and drops, step by step)
- **Capital protection:** together at most half of your gold, no single suggestion above 20 %

### Market data
- **Full market scan** with price history for every item
- **Market value** = weighted median of the last 14 days – newer prices count more, so it follows a price crash quickly; silly prices like "1666g 99s 98c" don't count
- **Price crash detection:** the tooltip says "price just crashed", and such items are not suggested
- **Sell-through estimate:** how many sell per day and how reliable the market value is
- **Trends and charts** with time-based EMAs and crossover markers
- **Bait-offer protection** and automatic re-checks of suspiciously cheap prices
- **Price sync** between all players using the addon
- Prices and a small price chart in **every item tooltip**, plus vendor price and disenchant value

### Buying
- **Categories like the Blizzard auction house:** every main category with its sub-categories (Weapons → One-Handed Axes …, Armor → Cloth/Leather …), names and order straight from the game
- **Sniper:** targets with max price, quantity, budget, rarity, item level and level filters – searches on its own while the auction house is open
- **Bargain watcher:** herbs, ore, cloth, leather, enchanting, elemental, gems, cooking and more – anything at or below x % of market value (default 50 %); never weapons or armour. When you start the full scan, it has priority: the watcher pauses until the scan has run
- **One-notch buying** with the mouse wheel or your own key binding
- **Stackable goods combined** (classic auction house): same unit price = one row with the sum and the total price; Shift+click several rows and buy them together
- **Shopping lists** with quantities – check all prices at once or turn missing items into sniper targets; items already in your bags are subtracted
- **Watchlist** with alerts

### Selling
- **Sell → Post:** price check and undercut suggestion (1 copper, 1 % or 5 %), deposit, AH cut and proceeds – warns when a vendor pays more or when you would sell below your purchase price
- **WoW Forever:** the deposit of at least 1 silver per auction is never refunded there – AHSentinel counts it in every profit calculation and suggests the vendor when the fee eats the AH profit
- **Series posting:** posts every bag item with a remembered price, one click per auction
- **Sell → My auctions:** status of your auctions (lowest / tied / undercut / sold), cancel with one click
- **Collect AH mail:** gold and items from all auction mail with one click (COD is never paid)

### Profit & bookkeeping
- **Ledger:** income after the AH cut, spending, deposits and profit for today / 7 days / 30 days / all time – read from your mailbox invoices, nothing counted twice
- **Statistics:** sell-through per item, best selling hours and weekdays
- **Buy → Bargains:** below market value, below vendor price or below disenchant value, bids and flip recommendations, sorted by realistic profit per day; flipping calculator
- **Disenchanting learns together:** your disenchant results are shared with all AHSentinel players (or only your guild), so the drop chances match the server much sooner
- **Professions:** material cost, value of the result and profit for every recipe, best recipes, materials straight to a shopping list
- **Vendor prices** are learned automatically at every merchant – including items that cost a currency (e.g. Merchant's Favor on WoW Forever)
- **Alts & gold:** gold, bags and bank of all your characters, gold history of the last 30 days
- **CSV export**

### Comfort
- **Five tabs** with sub-tabs, price history in its own window, sniper and watcher switchable in the title bar
- Two designs: **Classic** (looks like the WoW auction house) and **Modern**
- Item search by name in any language, by item ID or by shift-click, with suggestions while typing
- Built-in item name list (~33,000 items in 10 languages, incl. The Burning Crusade); lists always show names in your chosen language
- Help page for every tab, right-click menu on every item, minimap button
- **Robust saved data:** a single damaged entry (e.g. after a crash while saving) is repaired on login instead of causing a Lua error

---

## Supported game versions

AHSentinel works on **every** WoW version – all with the same features:

- **Retail**
- **Mists of Pandaria Classic** and **Cataclysm Classic**
- **Wrath Classic** and **Wrath Titan Reforged**
- **TBC Anniversary**
- **Classic Era** (incl. Hardcore / Season realms)
- **WoW Forever**

Both auction house types are supported: the modern one (Retail, Cata, MoP) and the classic one (Classic Era, TBC, Wrath).

One download for everything – just copy the folder `AHSentinel` from the zip into `Interface\AddOns` of your game.

## Languages

English, German, French, Spanish (EU and Latin America), Portuguese, Italian, Russian, Korean, Chinese (simplified and traditional). The addon follows your client language automatically; you can change it in the options or with `/ahs language`.

## Commands

Everything works with the mouse – the commands are optional.

| Command | Action |
|---|---|
| `/ahs` | open / close the window |
| `/ahs help` | list all commands in the chat |
| `/ahs scan` | start a full market scan |
| `/ahs today` | "Today" – what makes the most gold right now |
| `/ahs sniper` | sniper on / off |
| `/ahs summary` | daily summary in the chat |
| `/ahs alts` | rules for mail to alts |
| `/ahs goal 5000` | gold goal (no number: progress, `off`: clear) |
| `/ahs raid` | raid supplies as a shopping list |
| `/ahs lists` | shopping lists |
| `/ahs options` | options |
| `/ahs sync` | price sync on / off |
| `/ahs design` | switch between Classic and Modern |
| `/ahs language` | change the addon language |
| `/ahs export` | CSV export |
| `/ahs donate` | support the addon (PayPal link) |
| `/ahs manual` | help window with guide |
| `/ahs reset` | reset window and button positions |

---

## Feedback

Found a bug or have an idea? Leave a comment here on CurseForge – bug reports with the Lua error message and your WoW version help the most.

## Credits & license

Made by **GoldSentinel**. Licensed under **GPL-3.0-or-later**.
Item names from [QuestieDB](https://github.com/Questie/QuestieDB) (GPL-3.0) and [wow-classic-items](https://github.com/nexus-devs/wow-classic-items) (MIT) – thank you!
World of Warcraft and all item names © Blizzard Entertainment.
