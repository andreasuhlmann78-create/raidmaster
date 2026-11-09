# AHSentinel

**Market analysis, sniper and gold-making toolkit for the auction house – for every WoW version.**

> ⚠️ **This addon is in beta.** It may still contain bugs. If you run into an error or unexpected behaviour in-game, please report it in the comments – ideally with the Lua error message (if any) and the WoW version you play on.

> 🔁 **Formerly "AH Analyzer Pro".** Since version 0.62.0 the addon is called **AHSentinel**. Your saved data is taken over automatically on the first login. The zip now contains only the folder `AHSentinel` – if the old folder `AHAnalyzerPro` is still in your AddOns, AHSentinel tells you once in the chat: just delete it. The new command is `/ahs` (`/ahp` still works).

AHSentinel scans the auction house, keeps a price history for every item and turns it into market values, trends and charts. It finds bargains for you, helps you sell at the right price and keeps a ledger of everything you earn and spend. It opens in its own resizable window with just five tabs – **Overview, Buy, Sell, Market, Ledger** – can be used completely with the mouse and speaks the language of your WoW client.

---

## What's new

### Version 0.65.60

- **Main window opens beside the auction house** instead of over it, as long as you have not moved it yourself
  (and there is room on the screen).
- **Faster item tooltips:** the AHSentinel lines are cached per item for a few seconds (price data, Shift, settings,
  watchlist and bags are part of the key); the Shift part is only calculated while Shift is held.
- **Test routine can be cancelled:** `/ahs testroutine stop` (or `abbrechen`) and the "Cancel" button in the result
  window stop the run; all data is restored and the report says "cancelled by user".
- Test routine: no real data is changed any more (owned auctions, seller entry, ledger, sniper day counter,
  disenchant log – each test now works on its own copy); sniper and watcher pause during the server searches and are
  restored to your own setting afterwards; a timeout now says why (queries per minute, search, sniper, watcher);
  sniper test sets the max below the cheapest offer; the overlap check only reports windows AHSentinel placed itself
  (windows you moved and invisible frames of other addons are hints).

### Version 0.65.59

- **Fix: Ledger → Return (gold per hour) stopped with a Lua error** ("compare nil with number"): the start of a day is
  now calculated without time(table), which returns nothing in the client for "all time". Same fix for the ledger
  periods, the gold chart, the sniper day counter and the raid hint.
- **Faster:** the market list and "Today" no longer freeze for a moment with 5000+ items – they are kept in a cache and
  recalculated in the background in small portions after a scan or data change (the window updates itself).
- **Profit window and best recipes:** "Best recipes" rebuilds again after crafting (bag contents count as a change);
  the profit window never overlaps the profession window, not even its invisible border.
- **Tooltips of the AHSentinel windows** appear next to the window instead of over its buttons.
- Sale message: the game's text template is written to the diagnostic log once (no names).
- Test routine: no real data is changed any more during a run (activity, remembered recipes, auction size); sniper
  test only counts its own target and shows price, max and unit; new tests (offer 2c at max 1c -> no hit; start of day
  without time(table)); outdated tests adjusted (sale message with "%1$s", sync reception, tooltip check per language,
  own test window ignored in the overlap check, API events).

### Version 0.65.58

- **Price sync reaches players outside your guild (GoldSentinelSync 2, whisper network):** AHSentinel now uses
  version 2 of the shared GoldSentinel sync file. Besides guild and group, it can reach other players with GoldSentinel
  addons by whispering; they pass it on. Known players are remembered locally (AHSentinelDB.gsSync, names and times only).
  - **What goes into the network:** only prices after your own scan, bundled – the most traded items first, at most
    20 messages and at most once every 30 minutes (the network sends at most 40 whispers per minute).
  - **Guild/group only:** the full price list, answers to price requests, item names and disenchant results.
  - "Only guild" in the options keeps everything in the guild (nothing goes into the network).
- **GoldSentinelTest 2:** share error reports with the developer (only with your consent, /gstest).
- Diagnostic log: new "NETZ" line (without player names).

### Version 0.65.57

- **One minimum profit for everything:** the automatic minimum price when selling and AHSentinel.API.MinProfitPct now
  use your setting "minimum return" (same as "Worth up to" in the tooltip, default 20 %).
- For addon authors: API.Price reports "scan" only when the value really comes from the last scan ("market" when an
  outlier was replaced by the median). API.md matches the clarified contract (MaterialCost = crafting cost of the product,
  "vendor" is not an AH price).
- Texts: cancelling an auction loses the deposit (also in WoW Forever); the "per auction" tooltip in the profit window
  shows the measured minimum deposit instead of a fixed 1s.
- Test routine: new tests for the whole tooltip (with/without Shift, not disenchantable), "real from 12 disenchants",
  price source in the materials block, "Purchase sent" via the real confirm path, no flip suggestion for items that rarely
  sell, and at most 3 rebuilds of "Best recipes" while crafting.

### Version 0.65.56

- Test routine: sync tests use guild messages only (no channel messages anywhere in the addon).

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
