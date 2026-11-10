# AHSentinel

**Market analysis, sniper and gold-making toolkit for the auction house – for every WoW version.**

> ⚠️ **This addon is in beta.** It may still contain bugs. If you run into an error or unexpected behaviour in-game, please report it in the comments – ideally with the Lua error message (if any) and the WoW version you play on.

> 🔁 **Formerly "AH Analyzer Pro".** Since version 0.62.0 the addon is called **AHSentinel**. Your saved data is taken over automatically on the first login. The zip now contains only the folder `AHSentinel` – if the old folder `AHAnalyzerPro` is still in your AddOns, AHSentinel tells you once in the chat: just delete it. The new command is `/ahs` (`/ahp` still works).

AHSentinel scans the auction house, keeps a price history for every item and turns it into market values, trends and charts. It finds bargains for you, helps you sell at the right price and keeps a ledger of everything you earn and spend. It opens in its own resizable window with just five tabs – **Overview, Buy, Sell, Market, Ledger** – can be used completely with the mouse and speaks the language of your WoW client.

---

## What's new

### Version 0.65.74

- **Learning database (step 2, invisible):** AHSentinel now learns in the background from your own results – nothing
  new to operate, only better numbers in what you already use. Option "Learning" (on) switches it all off again.
  - Chance to sell per price level (price ÷ market value) and duration; expired and cancelled auctions count as "not
    sold" (never left out). Few own cases are pulled towards the item group, then towards shared numbers of all
    players (sync, counts only, no names), then a start value.
  - Price limits per item: the Sell tab suggests the learned normal price when nobody competes or the competition is
    above your maximum; the minimum includes fee and expected deposit losses.
  - Sell tab: "only ~N sell in this duration – keep the rest in your bags". My Auctions: "higher possible" when the
    cheaper competition is gone (cancel only by your click).
  - Safer buying: watcher, bulk buy, flips and disenchant deals use a safety margin from the measured error (20 % until
    20 buys, then at least 10 %) and a daily budget per strategy (10 % of your gold) while its hit rate is below 60 %.
  - Today: a hint when something you bought fell more than 25 % in value ("sell now brings X, waiting expects Y").
  - Rare items: own sales estimated with Croston; market sales use a learned factor per group (from the full scan)
    instead of the fixed 20 % cap.
  - Self-correction every week or 50 new results (damped ±30 %, log "LERNEN"); rhythm (cheap/expensive hour and
    weekday) after 21 days, only when stable.
  - Option "Try higher (+5 %)" (off): every 10th posting suggests 5 % more to learn the price sensitivity.
- Tooltip (Shift): "Chance to sell at market value: 72 % (learned from 23 own sales)", rhythm if known.
- Test routine: new part "l" (learning) with fixed numbers; report and GSTEST1 get a section "Learning database".

### Version 0.65.73

- **Fast full scan (new option, off by default):** in the modern auction house (WoW Forever) the scan button can read
  all single auctions at once with their time left (ReplicateItems) instead of browsing page by page. Read in small
  portions, so the game stays smooth; at most every 15 minutes, otherwise the normal scan runs. `/ahs vollscan` starts
  it once. Prices, market value and history are fed exactly as before (lowest price, quantity; bait offers don't count).
- **Exact queue:** "how many are in front of me" now counts only the pieces at your price or cheaper (price ladder
  from the full scan) instead of all pieces of the item.
- **Real market sales measured:** between two full scans AHSentinel compares the auctions (quantity and buyout, no
  names): gone early with a long time left = bought or cancelled, gone with a short time left = expired (not a sale).
  After 3 days of data the tooltip (Shift) shows "~12/day (measured, 5 days)" instead of the old estimate; until then
  "(estimated)". Your own auctions are used as a cross-check (share of cancels).
- Era/TBC: unchanged (the old auction house has no full scan).
- Test routine: new part "v" (full scan) with fixed numbers; report and GSTEST1 get a section "Full scan" (timing per
  frame, throttling, meaning of the time-left stages, measured sales).

### Version 0.65.72

- **Forecast journal (step 1 of "check every forecast"):** whenever you post, buy or disenchant, AHSentinel now notes
  in the background what it predicted at that moment (chance to sell within the duration, expected hours, number of
  postings, net value; for buys the planned way and value; for disenchanting the expected material value). Later it
  matches the result: sale invoices (oldest posting first, partial sales count proportionally), expired and cancelled
  auctions (counted as "not sold", never left out), loot from disenchanting, what became of bought items.
  No names, compact (at most 3000 entries, older than 60 days only in a small summary). Your ledger, disenchant
  results and price history are only read, never changed.
- **Tooltip (Shift):** once there are 20 own results in the item's group: "Forecasts for you: X % correct (N …)".
- **Test routine:** new part "p" (forecast) with fixed-number checks (Brier score, reliability table, FIFO, partial
  sale, expiry, cancel, ring buffer, size < 300 KB, no names); the report and the GSTEST1 export get a section
  "Forecast quality" from your real data (read only).
- Measurements: which replicate functions exist (only checked, never called), which fields the item search returns,
  and the lowest price/quantity per hour of the day for items you trade or watch (evaluated later).

### Version 0.65.71

- **Disenchant statistics:** rejected results (material outside the table) count as disenchanted and their loot counts,
  but they are shown separately: "(of which rejected N)". They never count for learning.
- **Restore disenchant results:** after a reset the button in the options becomes "Restore" and brings back the last
  backup exactly.
- **Faster tooltip:** the price chart under the tooltip is only redrawn when the item or its data changed.
- **Test routine:** the tooltip speed check shows the time per block; at the end of the report one line says what to
  do for the skipped parts (e.g. "open the auction house, then /ahs testroutine server").

### Version 0.65.70

- **Fix: options overlapped** (e.g. "Self-test" over "Default duration"): there were more options than fit in two
  columns of 18 rows. Each option now gets its own place (20 per column, more columns if needed).
- **Your disenchant results are protected:** "Reset" (Options → Disenchant learned) asks with the number of results
  and saves a backup first. The test routine checks that disenchant data is unchanged after the run (count and
  quantity sums) and reports any difference.
- **Disenchanting:** loot without a single disenchant material (mob, chest, skinning) is never counted as a
  disenchant; the loot must arrive within 5 seconds.
- **Test routine:** new report section "Disenchanting (real data)" – per group own/shared results, rate per material
  against the table (unusual values marked), daily count check and plausibility; also in the GSTEST1 export. New checks
  for the whole chain (spell → loot → counted), learning formula with fixed numbers, shared results and values.
- Tooltip: chance source for disenchant group "up to 15" named correctly.

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
