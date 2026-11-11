# AHSentinel

**Market analysis, sniper and gold-making toolkit for the auction house – for every WoW version.**

> ⚠️ **This addon is in beta.** It may still contain bugs. If you run into an error or unexpected behaviour in-game, please report it in the comments – ideally with the Lua error message (if any) and the WoW version you play on.

> 🔁 **Formerly "AH Analyzer Pro".** Since version 0.62.0 the addon is called **AHSentinel**. Your saved data is taken over automatically on the first login. The zip now contains only the folder `AHSentinel` – if the old folder `AHAnalyzerPro` is still in your AddOns, AHSentinel tells you once in the chat: just delete it. The new command is `/ahs` (`/ahp` still works).

AHSentinel scans the auction house, keeps a price history for every item and turns it into market values, trends and charts. It finds bargains for you, helps you sell at the right price and keeps a ledger of everything you earn and spend. It opens in its own resizable window with just five tabs – **Overview, Buy, Sell, Market, Ledger** – can be used completely with the mouse and speaks the language of your WoW client.

---

## What's new

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

### Version 0.65.88

- **Market "Disenchant": cost and profit over the whole price ladder.** Each row now sums every ladder step up to
  "worth it up to": quantity, total cost, average price, total profit and return (sorted by it), e.g. "40x up to
  15s 43c (avg 12s 38c) · value 18s 55c · profit 2g 47s (50 %)". The quantity is filled from the cheapest step up to
  25 % of your gold (option); the sniper gets exactly this cost as budget and "worth it up to" as max price. Row and
  footer show the same quantity.
- **Value drops with your own quantity** – one function for market, batch buy and tooltip: the more parts you plan
  to buy, the lower the material value (planned quantity, not budget / price).
- **Safety at most "medium" when the main material just rose**, plus "without the rise: X" in the row and detail.
- **Buyout detection (someone buys up a material).** Quantity −70 % within 6 h and price +50 % over market value
  marks a buyout until quantity or price normalise. Buying (market, batch buy, "worth it up to") then uses the old
  price ("Buyout of X – valued at the old price"); selling stays at the current price with "price artificially high –
  sell your own stock now". The test report lists flagged materials (thresholds are measured).
- **"Level ?" fixed**: rows are redrawn when the item data arrives.
- **Shopping list: "~" rows (from the scan) with empty detail fixed.** Before the detail search, a scan row first
  gets its real item key via a browse search by name (suffix/item level). If the browse finds nothing, the row is
  removed right away ("No offers left – removed from the list"), also from "Disenchant worth it", and the scan does
  not bring it back until a newer scan lists it again. "~" rows older than 30 min no longer count for batch buy.
- **Forecast: sales from invoices are assigned again.** In Forever the mail arrives faster than 1 h, so the sale time
  was before the posting and the case counted as "not sold". Partial sales count as a share. The test report shows
  a per-case diagnosis (where each result comes from); the self-correction only learns from cases after this fix.
- **Disenchant forecast split up**: chance × quantity × rest (price etc.) per group in the test report.
- Background tasks yield ahead of time (a frame no longer gets budget + one long step); "Today" computed in smaller
  portions.
- Test routine: the real sync address book and a running sniper hit no longer count as sandbox errors; report paths
  never contain player names. Price tests replace all price sources. Batch buy uses the planned quantity.
- Tests T425–T440 (T-X3–T-X8, T-MD1–T-MD6, T-SR8a/b).

### Version 0.65.87

- **Fix: Lua error on sale messages in WoW Forever.** Protected ("secret") chat and event values are never read any
  more (sale message, purchase, mail, posting and legacy AH events).
- **"Check undercuts" no longer freezes the game.** Only active auctions are checked, one search per item, without
  rebuilding the list after every item: the list is redrawn ONCE at the end. Every step is timed; steps over 50 ms
  appear in the log as LANGSAM.
- **Full scan measurement (for the big test).** The fast full scan now times every step (wait for the server, event,
  reading, digest, tracking, price history/rebuild), the longest gap between two frames (the real freeze), memory
  and garbage collections. The test routine part "server" starts one real fast full scan (read only) and reports it
  in the section "Full scan measurement"; a step or gap over 1 s is an ERROR naming the step. Nothing else changed in
  the full scan.
- **Fix: a single 2c offer no longer crushes material values.** The price ladder is capped only by the cleaned scan
  price, never by the raw minimum; without a cleaned price the ladder value counts as "market, unsure".
- **Fix: stock value too high after everything sold.** An empty list of own auctions (queried, all sold) now means
  "nothing in the AH"; old end times and the forecast journal are used only if the auctions were never queried.
- **Sniper: dead offers are hidden completely.** An offer whose purchase failed or that the server delivers again
  after "gone" disappears for the session (by auction ID, at most 48 h): not in the sniper, shopping list, undercut
  check, current price, price ladder from searches, "% market" or batch buying. Goods without auction ID: after 2
  failures. The status line shows "1 dead offer hidden (price, reason)", log SNIPER-TOT-AUSGEBLENDET. After 3 failed
  different auctions of the same item the item pauses for 10 minutes (log SNIPER-PAUSE). A new auction at the same
  price stays buyable.
- **"Cannot be disenchanted" no longer blocks a whole class.** Learned blocks are per item; a class (e.g. leather
  armor) only after 3 different items failed. Such items now show in "Blocked (N)" as "cannot be disenchanted
  (Forever)" with Release; `/ahs entzaubern freigeben` releases them too.
- Test routine: T410–T424 (T-0, T-UP1–3, T-VM1/2, T-X1, T-X2a/b, T-SR7a–c, T-ME10/11), coverage list extended.

### Version 0.65.86

- **Sniper: dead offers stay gone.** An offer whose purchase failed (e.g. "a higher bid already exists") is locked by
  its auction ID for 10 minutes: if the server delivers it again, it stays "gone" (red) and is never tried again. A
  new auction at the same price stays buyable. Goods without an auction ID: the same price and quantity are skipped
  for 60 s. Log SNIPER-SUCHE counts "dead delivered again".
- Test routine: T409 (T-SR6).

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
