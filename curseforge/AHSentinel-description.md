# AHSentinel

**Market analysis, sniper and gold-making toolkit for the auction house – for every WoW version.**

> ⚠️ **This addon is in beta.** It may still contain bugs. If you run into an error or unexpected behaviour in-game, please report it in the comments – ideally with the Lua error message (if any) and the WoW version you play on.

> 🔁 **Formerly "AH Analyzer Pro".** Since version 0.62.0 the addon is called **AHSentinel**. Your saved data is taken over automatically on the first login. The zip now contains only the folder `AHSentinel` – if the old folder `AHAnalyzerPro` is still in your AddOns, AHSentinel tells you once in the chat: just delete it. The new command is `/ahs` (`/ahp` still works).

AHSentinel scans the auction house, keeps a price history for every item and turns it into market values, trends and charts. It finds bargains for you, helps you sell at the right price and keeps a ledger of everything you earn and spend. It opens in its own resizable window with just five tabs – **Overview, Buy, Sell, Market, Ledger** – can be used completely with the mouse and speaks the language of your WoW client.

---

## What's new

### Version 0.65.104

- **Command list while typing "/ahs": a mouse click now selects a command, Enter runs it.** The list stays open after the
  click, the chat input gets the focus back, and the header shows "Enter = /ahs …". If you then press Enter with the
  beginning you typed (e.g. "/ahs ent"), the selected command runs. A selection is valid for 10 s; Tab selects the next
  entry. The chat input is still never written to (no taint).
- Tests T537–T541 (T-CH1–T-CH5).

### Version 0.65.103

- **Disenchant limits must be right:** "[Disenchant worth it]" in the buy list only when the price is at most "Worth up
  to" (minimum profit) with fresh material prices – before it appeared as soon as the value was above the price.
- **Sniper targets from disenchanting follow the limit:** if "Worth up to" changes by more than 5 % (new material
  prices), the max price is adjusted and reported once in chat.
- **Reference check in the test routine:** the groups 26–30, 31–35 and 36–40 are recalculated independently from the
  scan prices (cheapest − 1c × chance × average amount) and compared with the value the addon uses; more than 5 %
  difference is an ERROR naming the material, its source and age. One report line per group.
- **Vendor prices after the hotfix of 10.11.:** the game's own vendor price comes first; the remembered table is only a
  fallback and is updated when the game reports something else. Vendor flips only with a price confirmed by the game.
- **Minimum deposit 1c (announced for 17.11.):** measured automatically when posting – nothing fixed in the code.
- **AHSentinel.API:** new `WorthUpTo(itemID[, qty])` (same "Worth up to" as the tooltip) and `MarketState(itemID)`
  (normal / buyout / flood / thin / old) for ProfessionSentinel.
- Tests T530–T536 (T-HP1, T-HP2, API-PM, T-ST1–T-ST3).

### Version 0.65.102

- **My auctions: sold auctions disappear after "Refresh"** (and when you open the view); newly sold ones stay visible
  until the next click. The header still counts all sold auctions. New button "Sold: on/off" to show them.
- **Sell suggestion with a single expensive offer** (thin ladder ≥ 150 % of market value): market value instead of
  just under the outlier. "Post cheaper" is never shown while the competition is above the market value.
- **Vendor flips:** a vendor price above twice the market value is treated as wrong (e.g. Iron Grenade) – no vendor
  flip with it.
- **Comprehensive tests (TU1–TU4, TU6):** every market situation (normal, buyout, outlier, flood, thin, empty, old,
  falling/peak, wrong vendor price, relist) runs through the sell suggestion, ladder detection, hints, disenchant buy
  price and vendor check; player flows (typed price, three Sniper targets); default values of empty fields (listed in
  the test report); invariants with 1000 random ladders and random bookkeeping sequences. The test report has one line
  per area (TU1–TU7) and "Regressions: n of m present". Tests T513–T529.
- **Offline tests (TU9):** `tests/run_offline.sh` in the AHAnalyzerPro repository runs the test routine in a simulated
  game without WoW (Lua 5.1).

### Version 0.65.101

- **Sell suggestion follows a buyout.** If the whole price ladder is high (buyout or new market situation: cheapest
  offer ≥ 150 % of market value with at least 3 offers or 5 pieces), the suggestion is just below the cheapest offer –
  no longer your old learned price. Hint: "Buyout – sell high now, the price usually drops soon (2 h)" instead of
  "post cheaper"; the expiry counter is ignored in that case. "Sells only ~N" is hidden until the sales measurement is
  released.
- **A price you typed stays.** A finished price check no longer overwrites a price you entered by hand; changing the
  item or clicking "Suggestion"/"−1" makes it automatic again.
- **Sniper keeps several hits.** If two targets find hits at the same time, both stay buyable (best gap to the max
  price first, then the next); expired hits drop out. Status: "N more hits waiting".
- **Sniper quantity empty:** commodities buy as many as the budget allows ("Quantity: up to budget (N pcs)"), gear 1.
  Warning when quantity × max price is far below the budget.
- Tests T509–T512 (T-AB4c-a/b, T-SM1, T-SM2).

### Version 0.65.100

- **Price history is compacted (smaller save file).** Full detail for 48 hours, then one value per hour up to 7 days,
  then one value per day up to 60 days; older entries are dropped. Items without new prices for 30 days keep only
  daily values. A compacted value is the median of that hour/day, so market values stay the same. Runs in small steps
  90 s after login; the test report shows the estimated size per area and the last compaction.
- **Duplicate repair is safe for commodities:** only "pending" bookings close in time are removed, never completed
  sales (one auction of a commodity is often sold piece by piece at the same price). Removed bookings are kept in a
  side list, and every repair is stored with date, version and count (test report).
- **Full scan check no longer locks forever:** the reference count expires after 24 hours, and two full scans in a row
  with a similar smaller count are accepted (market really smaller).
- **Old purchase price after a restart:** only counted from the oldest entry the disenchant log still covers.
- **Buyout:** the test log notes both prices when a buy calculation uses the price before the buyout.
- Tests: material prices in the test sandbox are always fresh (T223/T230/T425 no longer depend on your real prices);
  new T502–T508 (T-VF5f, T-MP2b, T-PD5c, T-PD7a, T-MP1, T-AB8c, T-AB4b).

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
