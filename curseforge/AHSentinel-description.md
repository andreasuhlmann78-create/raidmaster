# AHSentinel

**Market analysis, sniper and gold-making toolkit for the auction house – for every WoW version.**

> ⚠️ **This addon is in beta.** It may still contain bugs. If you run into an error or unexpected behaviour in-game, please report it in the comments – ideally with the Lua error message (if any) and the WoW version you play on.

> 🔁 **Formerly "AH Analyzer Pro".** Since version 0.62.0 the addon is called **AHSentinel**. Your saved data is taken over automatically on the first login. The zip now contains only the folder `AHSentinel` – if the old folder `AHAnalyzerPro` is still in your AddOns, AHSentinel tells you once in the chat: just delete it. The new command is `/ahs` (`/ahp` still works).

AHSentinel scans the auction house, keeps a price history for every item and turns it into market values, trends and charts. It finds bargains for you, helps you sell at the right price and keeps a ledger of everything you earn and spend. It opens in its own resizable window with just five tabs – **Overview, Buy, Sell, Market, Ledger** – can be used completely with the mouse and speaks the language of your WoW client.

---

## What's new

### Version 0.65.48

- **Automatic minimum price when selling:** the higher of the vendor price after the AH cut and your own cost per
  piece (purchases of the last 30 days, otherwise crafting cost) + 5 %. A minimum you set by hand still wins. If the
  competition is below it, the suggestion is the minimum and a yellow hint says "Market is below your minimum price –
  post at the minimum or wait" (plus "price falling" when the 24 h trend is below −10 %). You decide – the price field
  stays free.
- **Expired 3× in a row:** the sell tab shows a yellow hint with a cheaper suggestion, the vendor price and the
  deposits lost so far. Nothing happens automatically.

### Version 0.65.47

- **Cancel only when it pays:** an undercut auction is only suggested for cancelling when reposting earns more than
  the lost deposit plus the new deposit's risk. A 1c undercut is now shown as grey "undercut – leave it" and
  "Cancel next undercut" skips it (buyers take the cheapest pieces first anyway). The row tooltip shows the math.
- **At most 90 searches per minute (WoW Forever):** all searches (sniper, watcher, scan, buy, price check) share one
  60-second window below the server limit of 100; the sniper has priority.
- **Neutral auction house (Booty Bay, Gadgetzan, Everlook): 15 % instead of 5 %** on sale – everywhere the cut is
  used. A formula deposit there is marked "(uncertain)" until measured.
- **Sniper:** if your max per piece is above the net sale value (last scan minus cut and deposit risk), a yellow hint
  shows the expected loss per piece. Nothing is blocked.

### Version 0.65.46

- **Minimum deposit is measured, not fixed (WoW Forever):** Blizzard announced lowering the minimum deposit per
  auction from 1s to 1c. AHSentinel no longer hard-codes 1s: the deposit always comes from Blizzard first, the formula
  is only a fallback, and its minimum is learned when you post an auction whose formula deposit is under 1s
  (diagnostic log "MINDESTEINZAHLUNG gemessen=…"). Once 1c is measured, the duration preselection "24 h costs the
  same" drops out on its own.
- Profit window: the AH fee line no longer adds a 1s minimum (only 5 % on sale – the deposit comes back).

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
