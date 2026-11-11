# AHSentinel

**Market analysis, sniper and gold-making toolkit for the auction house – for every WoW version.**

> ⚠️ **This addon is in beta.** It may still contain bugs. If you run into an error or unexpected behaviour in-game, please report it in the comments – ideally with the Lua error message (if any) and the WoW version you play on.

> 🔁 **Formerly "AH Analyzer Pro".** Since version 0.62.0 the addon is called **AHSentinel**. Your saved data is taken over automatically on the first login. The zip now contains only the folder `AHSentinel` – if the old folder `AHAnalyzerPro` is still in your AddOns, AHSentinel tells you once in the chat: just delete it. The new command is `/ahs` (`/ahp` still works).

AHSentinel scans the auction house, keeps a price history for every item and turns it into market values, trends and charts. It finds bargains for you, helps you sell at the right price and keeps a ledger of everything you earn and spend. It opens in its own resizable window with just five tabs – **Overview, Buy, Sell, Market, Ledger** – can be used completely with the mouse and speaks the language of your WoW client.

---

## What's new

### Version 0.65.93

- **Fix: partly sold auctions can be cancelled again.** For goods, the sold parts of an auction keep the same auction
  ID as the remaining active quantity. Cancelling (X in the row and "Cancel next undercut") picked a sold part and
  answered "This auction is already sold." Now the row cancels exactly its own entry and the active remainder is used.
- Bookkeeping: two partial sales of the same auction are both booked as "pending" (no longer skipped), the active
  remainder is not counted as sold.
- Tests T461–T462 (T-VF5a/b).

### Version 0.65.92

- **Smoother fast full scan.** Processing after the full scan now uses a time budget per frame (default 4 ms,
  option 2/4/6/8 ms next to "Fast full scan" – smaller = smoother but longer). The tables per item are reused between
  scans and the digest no longer creates garbage per item, so there is far less memory churn. Everything that is
  rebuilt after the scan (market lists, caches) now runs in portions instead of all in one frame. The option text
  warns that it can still stutter until the next measurement.
- **Measurement extended:** frames per second per step, share of frames over 33 ms, and AHSentinel's own memory
  before/after (test report section "Full scan measurement"). New checks: no step with a frame over 16 ms, memory
  growth ≤ 10 MB.
- "Cancel next undercut" only ever cancels auctions with status "undercut", never "keep"; the test routine only
  touches its own test auction.
- Market values of 0 or less are no longer possible (a price of 0 is not stored); the self-test names the items.
- Test routine: the sniper's "last checked" time no longer counts as a sandbox error.
- Tests T458–T460 (T-VF1–T-VF3).

### Version 0.65.91

- **Merge data from two computers.** If you played on two computers without syncing in between, the GoldSentinel
  uploader can hand AHSentinel the other computer's data (saved variable `AHSentinelMerge`). On the next login
  AHSentinel merges it once and empties it: disenchant results are combined without counting anything twice (only
  missing results are added – nothing is ever lost), purchases, bookings and forecast cases are combined, price
  history is combined per item, the newer full scan and character data win, and your settings on this computer stay.
  Chat: "Data from the other computer merged: …".
- Tests T454–T457 (T-ZM1–T-ZM4).

### Version 0.65.90

- **Sniper hit signal.** When the sniper finds a real hit, the screen edge glows gold 3 times (like the low-health
  glow). It stops when you buy, when the hit is gone, when you close the auction house, or after 4 s at the latest.
  No signal for dead offers, paused items, in combat or with the auction house closed; at most one signal every 3 s.
  Options: "Signal" on/off and colour (gold, green, blue) next to "Sound on hits". The glow never takes mouse clicks.
- Tests T450–T453 (T-SG1–T-SG4).

### Version 0.65.89

- **New bookkeeping: profit like the pros.** Buying is no longer a loss – what you buy sits in your stock at its
  purchase price, and profit is made when you sell: revenue after the 5 % cut − the purchase price of exactly what
  you sold − lost deposits. The ledger head now shows ONE number, "Profit", for today / 7 days / 30 days / since
  restart, with "Sold · Cost · Fees" below. Everything else is in the tooltip: cash, stock at cost and at market
  value, unrealised profit, pending sales and a check against your gold ("not booked: X").
- **Fresh start.** On the first login with this version the books start today. Your old data stays in the background
  (statistics, sell rates, forecasts keep using it) but never counts in the new books. Disenchant, learning,
  forecast and full-scan data are untouched. Items you already own get their realistic value at the start as cost,
  so selling old stock is neither pure profit nor a loss. `/ahs buchhaltung neu` starts the books again (asks first).
- **Cost per item and character (moving average).** Disenchanting moves the cost of the item onto the materials by
  their value; mail to your own alts carries the cost along. Items without a purchase (loot) have cost 0.
- **Sales count right away.** As soon as your own auction shows as sold (in Forever the chat message is protected),
  it is booked as "pending"; the invoice confirms it later – never twice. The test report measures the delay.
- "Per item": Sold, Revenue, Cost, Profit, Profit %.
- Tests T441–T449 (T-BP1–T-BP9).

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
