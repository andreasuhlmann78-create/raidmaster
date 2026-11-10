# AHSentinel

**Market analysis, sniper and gold-making toolkit for the auction house – for every WoW version.**

> ⚠️ **This addon is in beta.** It may still contain bugs. If you run into an error or unexpected behaviour in-game, please report it in the comments – ideally with the Lua error message (if any) and the WoW version you play on.

> 🔁 **Formerly "AH Analyzer Pro".** Since version 0.62.0 the addon is called **AHSentinel**. Your saved data is taken over automatically on the first login. The zip now contains only the folder `AHSentinel` – if the old folder `AHAnalyzerPro` is still in your AddOns, AHSentinel tells you once in the chat: just delete it. The new command is `/ahs` (`/ahp` still works).

AHSentinel scans the auction house, keeps a price history for every item and turns it into market values, trends and charts. It finds bargains for you, helps you sell at the right price and keeps a ledger of everything you earn and spend. It opens in its own resizable window with just five tabs – **Overview, Buy, Sell, Market, Ledger** – can be used completely with the mouse and speaks the language of your WoW client.

---

## What's new

### Version 0.65.84

- **Sniper searches by itself again:** the quick full scan (ReplicateItems) no longer blocks the sniper's item search;
  a running shopping search or price check blocks at most 20 s. Opening the AH (also after /reload) starts a search
  right away. Instead of "Nothing searched yet" the sniper shows its state: "next search in 12 s · last 40 s ago:
  5 hits" or "waiting: market scan running", plus "full scan lock N min left (sniper searches anyway)". Log
  SNIPER-SUCHE (target ID, offers, hits ≤ max, bought, block reason; no names).
- **"Purchase failed" only once:** the same offer is reported once; further failures within 30 s become one summary
  line. The failed offer is marked "gone" and never retried – the next wheel tick buys the next matching offer; if
  none is left, a new search starts.
- The warning "Max above sell value" uses the same value as the tooltip (for disenchant items the disenchant value).
- Test routine: T399–T402 (T-SR2–T-SR5).

### Version 0.65.83

- **New market view "Disenchant":** items that bring at least 20 % profit after disenchanting – at the current market,
  after fees. Per row: item (level), price now and quantity up to "worth it up to", value after disenchanting, profit
  per piece and %, safety (green = real results, grey = table). The "Buy" button sets a sniper target (max = worth it
  up to, quantity, budget) – nothing is bought without a click.
- Filters: only items your character can disenchant (enchanting skill), minimum profit 20 % (option 10–50 %), market
  budget (25 % of gold), no row if the main material crashed or is flooded; yellow if the value depends on a freshly
  risen material price. Material sales only as a safety net (more than one day of sales incl. your stock → shortened,
  yellow note).
- Detail on the right: materials with chance, average quantity, current price and hint; your own group results;
  "worth it up to". Footer: only the current purchase (selected row) – no sum of all rows.
- Test report: median time until sale per material (forecast journal).
- Test routine: T392–T398 (T-ME1–T-ME7).

### Version 0.65.82

- **Prices from the current market (your decision):** values come from the current price ladder and sales only – no cap
  and no mixing with the market value (average). The market value is only a warning: "price just rose (for N h)",
  "price dropped (for N h)", "old (N h ago)" when the last scan is older than 2 h, "estimated" without any scan. The
  number itself is not changed. With Shift the source: "price ladder, 311 pcs, sales ~20/day · market value …".
- **Market uses at most 25 % of your gold (your decision):** all buy suggestions (Today, Flips, Vendor) together at
  most this share; the best profit per gold first, a suggestion that does not fit is shortened, otherwise dropped.
  Footer "Capital needed X of Y (at most 25 %)". Option "Market: at most % of gold" (default 25, at most 50); the
  daily budget per strategy follows it.
- **Implausible sales:** at most 2× the average quantity per day and 25 % of the current offer per hour; measured
  values above that are not used (log ABSATZ-UNPLAUSIBEL). Flip texts say "estimated" or "measured, N days".
- **Ledger header:** the stock tile shows "Stock X (in AH Y) − at start Z"; the tooltip computes "Cash + stock − stock
  at start = result". Purchases used for professions (trade goods bought and gone) are shown separately: "Trade ±A ·
  professions −B". Running own auctions also count from the forecast journal when the AH was not queried.
- Test routine: T371 (T-AM1), T384–T391 (T-AM3/4, T-K1–3, T-LG6–8).

### Version 0.65.81

- **Fix (important): honest material prices for disenchanting.** The material price is the realistic sell price from
  the price ladder and sales (no longer capped at the market value). The tooltip says where it comes from: "Scan" only
  for scan values, otherwise "Market" or "price just rose (for N h)". If scan and market value are more than 50 % apart
  the price is grey "unsure"; with Shift both values are shown. A fresh jump (< 24 h) counts at most 1.5× the market
  value; after 24 h the ladder price counts (log MARKTWERT-CHECK). Bait offers (1–2 pieces far below the median) no
  longer pull down the market value from the price history.
- **Disenchant block list with a way back:** right-click asks first ("Yes / Skip just this once / Cancel"). New button
  "Blocked (N)" with a list to unblock single items or all. The empty window says how many items are blocked/skipped.
  `/ahs entzaubern freigeben` unblocks all.
- Speed: the full forecast evaluation no longer runs in the tooltip or after ledger changes; it is computed in the
  background in portions, the tooltip reads the cache.
- Full scan: "/ahs vollscan messen" measures a shorter interval once per session (asks first); the wait message no
  longer claims a server limit ("as a precaution, not measured yet").
- Buy forecast "resell" uses the realistic resale price. Sync: old scan announcements are cleaned up.
- Removed outdated fee texts and unused keys.
- Test routine: T369–T383 (T-HF9–11, H5, T-SK1/2/5, T-SP1–4, background check ≥ 16 ms, 3000-entry tooltip check),
  explanation line "learned vs. history" in the disenchant report.

### Version 0.65.80

- **Fix (important): ledger stock.** "Result with stock" showed −9g 60s and "Stock −8s 22c" although about 4.7g of goods
  were in the bags. The stock value is now never negative: bags and bank at the realistic sell price after fees (at
  least the vendor price) plus your running auctions (listing price × 0.95, deposit already paid). The start of the
  day is saved as a list of items and valued at today's price too, so the tile shows the "result if everything is sold
  at today's price". The tile shows "Stock X (of which in AH Y)"; Per item has a new column "in AH".
- Disenchant settlement: per batch and in total – purchase, loot sold / in AH / stock, fees, result.
- **Fix (important): purchases booked exactly once.** A purchase event only books the purchase with the same
  auction ID (a late event could book a different purchase before); every auction at most once. Purchase invoices in
  Forever: quantity never 0, total from the invoice. Invoice and purchase message are matched by item and quantity
  even if the amount differs (the invoice amount counts, log KAUF-DOPPELT). `/ahs doppelt` lists possible old double
  entries; `/ahs doppelt bereinigen` cleans up clear pairs with a backup (`/ahs doppelt zurück` undoes it).
- Test routine: T364–T368 (T-LG1–T-LG5).

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
