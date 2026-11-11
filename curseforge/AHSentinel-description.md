# AHSentinel

**Market analysis, sniper and gold-making toolkit for the auction house – for every WoW version.**

> ⚠️ **This addon is in beta.** It may still contain bugs. If you run into an error or unexpected behaviour in-game, please report it in the comments – ideally with the Lua error message (if any) and the WoW version you play on.

> 🔁 **Formerly "AH Analyzer Pro".** Since version 0.62.0 the addon is called **AHSentinel**. Your saved data is taken over automatically on the first login. The zip now contains only the folder `AHSentinel` – if the old folder `AHAnalyzerPro` is still in your AddOns, AHSentinel tells you once in the chat: just delete it. The new command is `/ahs` (`/ahp` still works).

AHSentinel scans the auction house, keeps a price history for every item and turns it into market values, trends and charts. It finds bargains for you, helps you sell at the right price and keeps a ledger of everything you earn and spend. It opens in its own resizable window with just five tabs – **Overview, Buy, Sell, Market, Ledger** – can be used completely with the mouse and speaks the language of your WoW client.

---

## What's new

### Version 0.65.97

- **Bookkeeping restart keeps purchase prices (opening balance).** Goods bought before a restart (bags, bank, mail,
  own auctions) keep their purchase price from the old data; only the profit counters start at 0. Goods without any
  purchase (loot) keep the value at the restart. A restart that lost the cost basis is corrected once at login:
  disenchants with cost 0 get the price paid for the item, and the cost moves to the materials (sold ones into the
  sales, the rest into stock). The diagnostic log notes how many bookings were corrected.
- **Plausibility checks:** warning in the profit tooltip if more than 30 % of revenue is "without purchase" or the
  disenchanting return is over 100 %; the test report shows an ERROR for disenchants with cost 0 of a bought item.
- **Gold reconciliation from the same moment as the bookkeeping** (later of day start and restart). Pending sales
  ("arrives by mail") are shown right there; "not booked" only appears above 1 % of turnover.
- **Profit % per item** only from pieces with a purchase (like the header).
- **Posting:** no more Lua error after a successful post. Before posting, AHSentinel checks that the item is still in
  the bag slot; otherwise "Already posted – no longer in your bags". The button stays locked until you select an item.
- **My auctions:** instead of "?" the status shows why the price is not checked yet (AH closed, waiting, Sniper
  searching, server throttling). Your own auctions are checked before the background material prices. Cancelling is
  logged step by step (test log), the cancelled row disappears at once.
- **Buyout (e.g. Soul Dust at 3× the price):** never a buy signal; for your own goods "Expensive now – sell … · Buyout
  – price may drop quickly".
- **Outdated prices:** every material with ≥ 25 % of the disenchant value must be fresh, not only the main material.
- Diagnostic log: type of the last scan in PREIS-ALT; posted vs. server price of your own auction (EIGENE-PREIS).
- Tests T484–T490 (T-AB1, T-AB2, T-AB4, T-AB5, T-AB7, T-AB8a/b).

### Version 0.65.96

- **AHSentinel now tells you when to buy and when to sell – but only when it knows it from its own measurements.**
  One tooltip line, only if proven: "Cheap now – buy (−x % below usual)", "Falling – wait", "Expensive now – sell
  (+x % above usual)" or (your own goods / Sell tab) "Don't sell now – better at <hour> (+x %)". Otherwise no line.
  The same line appears in the Buy and Sniper details and in the Sell tab (there only the selling variants).
- **Rhythm for all items from the scan:** once per hour each item's lowest price and quantity (sales = quantity drop)
  are stored compactly per hour of day and weekday (own weekly rhythm, e.g. raid days from 9.12.). Items without
  offers for 14 days are removed; even 5,000 items stay below 2 MB.
- **Honest:** only with a fresh price (≤ 30 min), never with a buyout flag or outdated material prices, only from
  ≥ 7 days of data and ≥ 3 values for this hour, and only if the deviation is ≥ 10 % and outside the item's normal
  fluctuation. "Buy" never into a fall: if the daily price has been falling for 2 days, it says "Falling – wait".
- **Every line is checked afterwards** (24 hours later or at the named time). A signal type with less than 60 % hits
  (from 20 cases) is hidden until it is better again. Hit rates are in the test report. With Shift and too little data:
  "Rhythm: N more days of measuring".
- Tests T477–T483 (T-JK1–T-JK6).

### Version 0.65.95

- **"Worth up to" in every tooltip of a disenchantable item** – also in your bags, bank, mail, chat links, at the
  vendor and in other windows (other players' gear, loot). It is shown to everyone, with or without Enchanting, and in
  the short tooltip mode too. In the bags it stands right above the two ways (disenchant / sell). The existing option
  "Disench.: on/off" switches the whole disenchant part off together.
- **Never decide with outdated material prices.** If the material that carries most of the disenchant value has no
  price newer than 6 hours: tooltip "Worth up to: Prices outdated – scan first" (no amount, verdict "unsure"), Sniper
  disenchant targets do not buy ("Material prices outdated – scan first"), and the Market "Disenchant" view offers no
  row. Sell values of your own stock still show the old price with the "old" hint.
- **Fresh material prices at the open AH:** after a scan and when you open the AH, the disenchant materials (up to 15,
  most used first) whose price is older than 30 minutes are fetched one by one (throttled). The diagnostic log notes
  the scan type, how many commodities the full scan contained and the price age of the three main materials (PREIS-ALT).
- **Buyout flag stays until disproven:** a material flagged as bought out keeps the price from before the buyout
  across sessions and days, until a newer scan shows the quantity back at ≥ 50 % or the price back at ≤ 120 %.
- **Bookkeeping fixes:** partial sales of the same auction booked by 0.65.92 or older are no longer booked a second time
  (existing doubles are repaired once at login, cost basis restored). Sync merge: positions of the same character
  bought on two computers are now added up (5 + 3 = 8 with both costs). The merge package also reads the older field
  names, and the merge report counts disenchants without a log entry.
- Tests T467–T476 (T-LB1–T-LB4, T-MP1–T-MP3, T-VF5c/d, T-ZM5).

### Version 0.65.94

- **Bookkeeping: return next to the profit.** The head now shows "Profit X · Return Y %" (profit of goods you bought ÷
  what they cost you). Without any cost: "Return –".
- **Where you lose money** (tooltip of the profit): the business type (disenchanting, flipping, crafting, vendor
  goods) and the item with the biggest realised loss, with the amount – or "No losing business". The type comes from
  where the cost came from (AH purchase = flipping, from disenchanting = disenchanting); mixed or unclear = "unknown".
- **Honest about free goods:** profit from goods you never bought (loot, farming, quests) is shown separately in the
  head ("of which without purchase: X", only if any) and does not count in the return.
- Tests T463–T466 (T-BE1–T-BE4).

### Version 0.65.93

- **Fix: partly sold auctions can be cancelled again.** For goods, the sold parts of an auction keep the same auction
  ID as the remaining active quantity. Cancelling (X in the row and "Cancel next undercut") picked a sold part and
  answered "This auction is already sold." Now the row cancels exactly its own entry and the active remainder is used.
- Bookkeeping: two partial sales of the same auction are both booked as "pending" (no longer skipped), the active
  remainder is not counted as sold.
- Tests T461–T462 (T-VF5a/b).

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
