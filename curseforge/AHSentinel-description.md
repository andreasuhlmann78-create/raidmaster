# AHSentinel

**Market analysis, sniper and gold-making toolkit for the auction house – for every WoW version.**

> ⚠️ **This addon is in beta.** It may still contain bugs. If you run into an error or unexpected behaviour in-game, please report it in the comments – ideally with the Lua error message (if any) and the WoW version you play on.

> 🔁 **Formerly "AH Analyzer Pro".** Since version 0.62.0 the addon is called **AHSentinel**. Your saved data is taken over automatically on the first login. The zip now contains only the folder `AHSentinel` – if the old folder `AHAnalyzerPro` is still in your AddOns, AHSentinel tells you once in the chat: just delete it. The new command is `/ahs` (`/ahp` still works).

AHSentinel scans the auction house, keeps a price history for every item and turns it into market values, trends and charts. It finds bargains for you, helps you sell at the right price and keeps a ledger of everything you earn and spend. It opens in its own resizable window with just five tabs – **Overview, Buy, Sell, Market, Ledger** – can be used completely with the mouse and speaks the language of your WoW client.

---

## What's new

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

### Version 0.65.99

- **An empty full scan changes nothing.** If the server answers a full scan with no or far too few auctions (under 30 %
  of the last valid one), no market, sales, rhythm or tracking data is taken over: "Full scan without answer – nothing
  taken over." Sales estimates only come from two valid full scans.
- **The Sniper pauses while a full scan is running** (about 30–90 s) – the full scan has priority. The 15-minute lock
  alone does not stop the Sniper. Status line: "waiting: full scan running".
- **Forecast: one case per purchase.** The same purchase could appear many times in the forecast journal. Purchases now
  carry their auction; repeated reports are not recorded again. Existing duplicates are set aside once (not deleted,
  kept in a side list) when the number of identical cases exceeds the purchases in the bookkeeping. Report: "Duplicates 0".
- Tests T499–T501 (T-PD5a/b, T-PD2); simulation test for "scan with commodities updates their price time" (T-MP1).

### Version 0.65.98

- **Sniper purchases are booked at once, even when you buy quickly in a row.** Before, the purchase event could arrive
  after the next purchase had started and was then only booked when the invoice came – disenchanting in between counted
  with cost 0. Every purchase is now remembered by its auction and booked when its event arrives; never twice.
- **Disenchanting an item without known origin** is marked "without purchase" instead of silently counting 0.
- **Correction after a restart (0.65.97) fixed:** material sales that received the cost of the corrected disenchants
  no longer count as "without purchase" – the return is right again and the 30 % warning disappears. Data already
  corrected by 0.65.97 is fixed once at login. Costs without a target (material passed on) are noted in the log.
- **Duplicate "pending" sale bookings from 0.65.93/0.65.94** (without the new ID) are now found and removed once
  (stock restored); real partial sales of the same size stay.
- Tests T491–T498 (T-AB8c/d, T-AB1b–d, T-VF5e, T-PD1a/b).

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
