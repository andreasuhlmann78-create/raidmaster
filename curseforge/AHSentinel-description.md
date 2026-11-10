# AHSentinel

**Market analysis, sniper and gold-making toolkit for the auction house – for every WoW version.**

> ⚠️ **This addon is in beta.** It may still contain bugs. If you run into an error or unexpected behaviour in-game, please report it in the comments – ideally with the Lua error message (if any) and the WoW version you play on.

> 🔁 **Formerly "AH Analyzer Pro".** Since version 0.62.0 the addon is called **AHSentinel**. Your saved data is taken over automatically on the first login. The zip now contains only the folder `AHSentinel` – if the old folder `AHAnalyzerPro` is still in your AddOns, AHSentinel tells you once in the chat: just delete it. The new command is `/ahs` (`/ahp` still works).

AHSentinel scans the auction house, keeps a price history for every item and turns it into market values, trends and charts. It finds bargains for you, helps you sell at the right price and keeps a ledger of everything you earn and spend. It opens in its own resizable window with just five tabs – **Overview, Buy, Sell, Market, Ledger** – can be used completely with the mouse and speaks the language of your WoW client.

---

## What's new

### Version 0.65.78

- **Fix (important): disenchant buys are valued realistically.** Material prices now use the same realistic resale
  price as flips (price ladder and sales per day), after the AH cut and expected deposit losses. Buying many pieces
  lowers the price: if your materials exceed two days of sales, each further day of sales counts one step lower on
  the ladder. Applies to the disenchant value, "Disenchanting pays", bulk buy and disenchant bargains.
- Tooltip: the verdict shows the profit with percent; with Shift "Profit after selling the materials: X (Y %)".
- Ledger -> Disenchant: settlement per purchase batch, e.g. "Batch 10.11.: paid 5g, sold Xg, stock Yg, fees Zg,
  result ±Wg" (mouse over shows all batches).
- **My Auctions:** "8 sold (4g 42s 77c, received 4g 20s 60c)" – received = per auction total × 0.95, rounded down.
  A footer shows the totals of the list per status; with Shift the summary tooltip shows today's total from the ledger.
- **Sniper:** "Result is outdated – bought in this search: 23 for 2g 30s · missed 13 – new search needed." The target
  row shows "50/100 bought · budget 5g used up" (or "budget left …") in full. When the budget is used up you get one
  chat message and a header line; the target stays in the list. The target tooltip explains how many pieces the
  budget allows.
- Test routine: T351–T359 (T-HF8, T-MS1–3, T-SN1–3).

### Version 0.65.77

- **Fix (important): no more fake flips.** "Today" suggested e.g. "buy 4x Unstable Magic Particle up to 45s 97c, post
  again for 2g 3s" – but 855 pieces were on offer at 46–50s; 2g 3s was an outdated offer price. Now ONE realistic
  resale price is used everywhere (Today, Flip, details, watcher): the price at which fewer pieces wait in front of you
  than sell during your duration (price ladder of the full scan or the search), at most the learned normal price and
  the market value; without a ladder at most 15 % above the current lowest price.
- No flip during a price crash or when the supply is flooded (3× the usual amount) – such items show up in "Crowded".
- List and details never contradict each other: a buy row only appears if the details say "buy up to X" too.
- Honest flip profit: after the AH cut and expected deposit losses, quantity at most what you can sell in your share
  of the market.
- Market views no longer stay empty while sales are not yet measured: estimated sales are used and marked grey
  ("estimated"); an empty view says why. Switching views clears the details (or shows the first row).
- **My Auctions:** total of sold goods in the summary line (gross and after the AH cut).
- Test routine: T344–T350 (T-HF1–T-HF7).

### Version 0.65.76

- **Full check after all steps:** `/ahs testroutine alles` runs the automatic part and then the server, professions
  and vendor parts one after the other. If a window is missing, one line says what to open; it waits up to 2 minutes
  and then continues.
- **Test report:** five summary lines at the top (OK/errors, what is left to do in the game, forecast hit rate,
  measured sales available for N items, storage). A coverage list maps every task and test case to its checks or
  says why it can only be checked in the game. Sections with real data: disenchanting, forecast quality, full scan,
  learning database, market tab, gear measurement. The sandbox compares all real tables (also journal, learning, full
  scan); storage sizes and loading time are in the report.
- **Measurement "gear in whole silver"** (`/ahs messreihe`, only with your agreement): with a few cheap grey/white gear
  items it posts at 1s 00c, 1s 01c, 1s 50c, 1s 99c, 2s, 10s 50c, 1g 00s 01c and once with a bid, plus one commodity at
  1s 99c – every posting is cancelled right away, every step is one click, at most 10 postings, costs shown first.
  The result goes into the log and the test report. The price rounding stays as it is until the measurement proves
  otherwise.
- Price sync: a partial price list from the network no longer stops a guild member with a full scan from answering.

### Version 0.65.75

- **New "Market" tab replaces "Today" (step 3):** one bar with 6 views – **Today** (the former "Today" list: your
  things first, then the best chances), **Flip** (below your buy limit, by profit per gold and day), **Vendor**
  (buyout below vendor price), **Gaps** (low supply, steady sales, rising price – your stock first), **Crowded**
  (don't post: far more supply than sales, days until sold, deposit risk) and **Trends** (stable 7/30-day moves,
  falling levelling goods first). Each view: one explanation line, at most 20 rows, one number, confidence as colour,
  one button – the button works exactly as before (check -> buy -> post, never without your click).
- **Details on the right:** click a row or search an item at the top: price and supply over 14 days, price ladder,
  your own history, learned price limits and ONE recommendation ("buy up to X" / "post for Y" / "leave it") with the
  reason; buttons Watchlist, Shopping list, Sniper (with the suggested limit), price history.
- **Market today:** a price index of typical goods at the top ("Market today +3 % (7 days +8 %)").
- The list of all items is gone from the tab bar (the data stays and all views use it); look items up via the search.
- `/ahs heute`, the Today button and other addons (ProfessionSentinel QuickBuy/QuickSell rows on top) open the Market
  tab on "Today". New option: "Market: default view".
- Test routine: new part "m" (market) and a section "Market tab" in the report.

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
