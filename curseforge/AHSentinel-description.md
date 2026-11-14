# AHSentinel

**Market analysis, sniper and gold-making toolkit for the auction house – for every WoW version.**

> ⚠️ **This addon is in beta.** It may still contain bugs. If you run into an error or unexpected behaviour in-game, please report it in the comments – ideally with the Lua error message (if any) and the WoW version you play on.

> 🔁 **Formerly "AH Analyzer Pro".** Since version 0.62.0 the addon is called **AHSentinel**. Your saved data is taken over automatically on the first login. The zip now contains only the folder `AHSentinel` – if the old folder `AHAnalyzerPro` is still in your AddOns, AHSentinel tells you once in the chat: just delete it. The new command is `/ahs` (`/ahp` still works).

AHSentinel scans the auction house, keeps a price history for every item and turns it into market values, trends and charts. It finds bargains for you, helps you sell at the right price and keeps a ledger of everything you earn and spend. It opens in its own resizable window with just five tabs – **Overview, Buy, Sell, Market, Ledger** – can be used completely with the mouse and speaks the language of your WoW client.

---

## What's new

### Version 0.65.127

- **Accounting – phantom stock removed:** goods still in stock after the repair although they were sold are moved onto
  the invoices once (purchase cost there, not in stock). New: stock check against bags, bank and own auctions – if the
  stock shows more, the test report says so (reported only, nothing changed silently).
- **Gold reconciliation** now only covers the period with recorded gold amounts, over all characters; before that "learning".
- **Bargains tab** no longer calculates when opened but in the background (shows the last result immediately).
- **Sniper/disenchant:** buy limit never above 0.9 × value.
- The test routine no longer writes real gold amounts. Tempo test: startup parts with file:line, tooltip measurement
  notes garbage collection, cause of full-scan gaps, last full-scan measurement survives a reload.
- Test report: purchases per price level, disenchant breakdown from sums. Tests T649, T650.

### Version 0.65.126

- **Empty lists:** the hint in an empty list (e.g. Market > Disenchant) now stays inside the list and wraps to its
  width instead of running across the screen.
- **"Test report" window:** very long reports are shown in parts (arrows top right, "Part x of y") instead of the
  window staying empty/black.
- **More honest sales forecast:** auctions you cancelled yourself no longer count as "not sold" (neither hit nor miss,
  not used for learning). On cancel AHSentinel notes whether you had been undercut. The test report shows the hit rate
  old/new and the sold share per price level.
- Test: the "Today" list with 5000 items is computed in small portions (T647). Tests T645–T648.

### Version 0.65.125

- **Less stutter – compact price history in memory:** in game AHSentinel now keeps the price history as one compact
  number list per item instead of one table per price entry (tens of thousands fewer Lua objects; garbage collection
  has much less work). Saved data stays exactly as before; all values are unchanged.
- **Accounting – repair corrected:** for invoices that were booked twice next to pending sales, the purchase cost now
  goes onto the invoice (the goods are sold) instead of back into stock. If you already started 0.65.124, this is
  corrected once afterwards (backup kept). The repair only counts as done once it has run without errors.
- The tempo test shows the price history tables. Tests T643, T644.

### Version 0.65.124

- **Accounting – profit only from confirmed sales:** auctions that sold but whose payment has not arrived by mail yet
  ("pending") no longer count in profit; they are shown separately as "in transit". Pending entries older than 24 h
  without an invoice are flagged in the tooltip.
- **Invoices in large lots:** an invoice for e.g. 72 items now confirms several small pending entries of the same item
  (summed by quantity) instead of booking a second sale.
- **One-time repair:** pending entries already covered by an invoice that was booked as a new sale are marked "replaced
  by invoice" (nothing deleted, a backup is kept). No more double counting between invoice and pending.
- Test report: profit old/new, number of resolved entries, gold reconciliation since the start date. Tests T640–T642.

### Version 0.65.123

- **Shared command list:** the list while typing `/ahs` now comes from the shared GoldSentinel file
  (GoldSentinelCmdHint.lua), the same for all GoldSentinel addons. Use stays the same (click selects, Tab/Shift+Tab,
  Enter runs); your usage counters are kept.
- Speed test (`/ahs testroutine tempo`): memory of AHSentinel broken down by area (size and number of tables) in the
  test report.
- Tests T638, T639.

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
