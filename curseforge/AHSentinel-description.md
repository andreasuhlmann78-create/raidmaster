# AHSentinel

**Market analysis, sniper and gold-making toolkit for the auction house – for every WoW version.**

> ⚠️ **This addon is in beta.** It may still contain bugs. If you run into an error or unexpected behaviour in-game, please report it in the comments – ideally with the Lua error message (if any) and the WoW version you play on.

> 🔁 **Formerly "AH Analyzer Pro".** Since version 0.62.0 the addon is called **AHSentinel**. Your saved data is taken over automatically on the first login. The zip now contains only the folder `AHSentinel` – if the old folder `AHAnalyzerPro` is still in your AddOns, AHSentinel tells you once in the chat: just delete it. The new command is `/ahs` (`/ahp` still works).

AHSentinel scans the auction house, keeps a price history for every item and turns it into market values, trends and charts. It finds bargains for you, helps you sell at the right price and keeps a ledger of everything you earn and spend. It opens in its own resizable window with just five tabs – **Overview, Buy, Sell, Market, Ledger** – can be used completely with the mouse and speaks the language of your WoW client.

---

## What's new

### Version 0.65.45

- **Ledger fix (WoW Forever):** in a Forever sale invoice the field read as "price" is the **quantity** – 0.65.42 to
  0.65.44 swapped quantity and unit price (e.g. 91 pieces at 1s 84c instead of 184 pieces at 91c). Income was right,
  but average sale price, sell rate and speed were wrong. Fixed when reading invoices, and existing sales are
  corrected once at login ("Ledger: fixed N sales (quantity and unit price)"). Nothing is deleted.
- **Values come from your last scan:** the value of an item is the cheapest offer of your last scan (or a newer
  search) – no 1c off, no cap at the median. Only two safeguards: an obvious outlier (e.g. 1 piece for 1c) is
  replaced by the next real offer, and items missing from the last scan use the market median. Your own average sale
  price is statistics only (Shift in the tooltip, yellow if more than 30 % below the market).
- Tooltip materials show the source ("scan" / "market").

### Version 0.65.44

- **Tooltip, clearer ("variant A"):** without Shift exactly three blocks –
  1. **Price:** "AHSentinel – Price 10s" (own items: market value), market value if different, "Sells: quickly (~3 h)".
  2. **Verdict:** "Disenchanting pays off / does not pay" with profit, "Worth up to", then both ways with amount (better
     one first). Own items: only the two ways. Not disenchantable: only "Sell:".
  3. **Materials:** "Materials (real, from N disenchants)" or "(table)", one line each with chance × quantity and price
     after fees – always, also when Disenchantry is installed (AHSentinel replaces it).
  Everything else (real value with calculation, median, trend, sales per day, vendor price, your sell chance, alts)
  with **Shift**. Setting "short" hides the materials, "everything" shows all without Shift.
- **Sniper:** "Purchase sent" when you confirm; "Bought" only when the server confirms (no more "Bought" followed by
  "failed – counter corrected"). "Price is being checked" only once per reservation. When the price is confirmed:
  a short sound (option "sound on hits"), the Buy button blinks and "Buy now: mouse wheel" appears (never in combat).
- **Bulk buy for disenchanting:** counted only when the purchase succeeds.
- **Profit window:** the "AH fee" line shows only the 5 %; expected re-postings or "vendor pays more" in a grey line.
- Faster: the ledger is indexed per item instead of read completely for every price.

### Version 0.65.43

- **Sell tab – duration preselected (WoW Forever):** 24 h when it costs no more than 2 h (minimum deposit, e.g. dust,
  cloth, herbs); otherwise by how fast the item usually sells for you (under 2 h -> 2 h, under 8 h -> 8 h); without data
  24 h if it costs hardly more, else 8 h. The reason is shown below the buttons; you can still change it.
- **How fast it sells:** measured from your ledger (posted -> sold, expired). Tooltip line "Sells: quickly (~3 h)",
  "slowly (~2 days)" or "hardly (often expires)"; without your own data the market sales per day as before.
- Items that hardly sell for you are no longer suggested for flipping or crafting ("Do today"); the Sell tab shows
  "Often expires – post cheaper or keep it." (no automatic price change).

### Version 0.65.42

**Auction fees like in classic WoW (measured in WoW Forever) – this replaces the "max(5 %, 1s)" rule:**
- **Posting:** deposit = vendor price × quantity × 5 % per 2 hours (2/8/24 h = 5/20/60 %), at least 1s per auction
  in Forever. Blizzard's own value is used when the AH is open. **Selling:** 5 % of the price, the deposit comes back.
  Expired auctions lose the deposit – values and profits include the expected loss (from your sell rate).
- **Sell tab:** the deposit line is back, AH fee 5 %. **Profit window:** "AH fee 5 % + deposit (back on sale)".
- **Ledger:** Forever invoices are read correctly (the "price" is the unit price, the quantity is computed from the
  total). Sales booked by earlier versions are recalculated once at login ("Ledger: recalculated N sales"),
  nothing is deleted. The raw invoice values go to the diagnostic log once per session (RECHNUNG-ROH, no names).
- **Tooltip:** both ways with amount, the better one first: "Disenchant: 9s 35c" / "Sell: 8s 99c" (own items in your
  bags: only these two lines; in the AH below the verdict).
- **Best recipes no longer stutter:** rebuilt only while the profit window is visible, at most every 10 s while you
  craft, and only when prices or the recipe list really changed; reading all recipes is spread over frames.
- **For addon authors:** `AHAnalyzerPro:AuctionFee(total[, itemID, qty])` / `.AHFee` now return the expected selling
  costs of one auction (5 % + expected deposit loss). New: `AHAnalyzerPro:ListingDeposit(itemID, qty, hours, auctions)`.

### Version 0.65.41

**See at a glance whether it pays off – no calculating:**
- **Tooltip – disenchant verdict:** instead of "Disenchant value" and "Profit when buying" there are two lines:
  green "Disenchanting pays off +2s 85c", red "Disenchanting does not pay −65c" or grey "Disenchant: uncertain"
  (a material price is missing or unreliable), and below "Worth up to 7s 79c" (= disenchant value / (1 + minimum
  return, default 20 %), rounded down). Materials, chances and the calculation only with **Shift**. For your own items
  in the bags: "Disenchanting is worth more than selling" or "Selling is worth more than disenchanting".
- **Profit window – best way:**
  - Materials over the cheapest way per reagent: AH, vendor, or crafting it yourself from a recipe you know
    (e.g. Bolt of Linen Cloth from 2 Linen Cloth), up to 2 levels. A small grey line says where it comes from.
    "Materials as shopping list" buys the reagents actually chosen (Linen Cloth instead of the bolt).
  - Value = the better of selling (AH fee max(5 %, 1s) per auction) and disenchanting (only if disenchantable).
  - "Profit" shows the best way, below "best way: disenchant/sell" and the other way with its amount.
    "Best recipes" sorts by it, with "dis."/"sell" behind the amount.

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
