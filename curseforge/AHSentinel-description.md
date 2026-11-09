# AHSentinel

**Market analysis, sniper and gold-making toolkit for the auction house – for every WoW version.**

> ⚠️ **This addon is in beta.** It may still contain bugs. If you run into an error or unexpected behaviour in-game, please report it in the comments – ideally with the Lua error message (if any) and the WoW version you play on.

> 🔁 **Formerly "AH Analyzer Pro".** Since version 0.62.0 the addon is called **AHSentinel**. Your saved data is taken over automatically on the first login. The zip now contains only the folder `AHSentinel` – if the old folder `AHAnalyzerPro` is still in your AddOns, AHSentinel tells you once in the chat: just delete it. The new command is `/ahs` (`/ahp` still works).

AHSentinel scans the auction house, keeps a price history for every item and turns it into market values, trends and charts. It finds bargains for you, helps you sell at the right price and keeps a ledger of everything you earn and spend. It opens in its own resizable window with just five tabs – **Overview, Buy, Sell, Market, Ledger** – can be used completely with the mouse and speaks the language of your WoW client.

---

## What's new

### Version 0.65.39

- **Categories with three levels** like in the Blizzard AH (e.g. Weapons -> One-Handed -> Axes) in Buy; the third
  level appears under the chosen second one.
- **Mail rules:** the category is now chosen from a menu (expand a main category, then pick) instead of clicking
  through more than 50 entries.
- **Selling:** a price more than 100x the market value asks for a second click ("typo? a number without unit = gold").
- **Do today -> below vendor price:** from a scan or search only the cheapest price is known, so the profit is shown
  for 1 piece (the exact quantity comes with the item's listings). No more inflated profits.
- **Sharing disenchant results:** all parts of one sending count as one message (large statistics are no longer cut
  off); a second sending from the same player within a minute is ignored.
- **Playtest:** S7 counts only spells that are a recipe of the open profession; all playtest texts are translated.
- Test routine: no longer replaces any Blizzard function or frame during the tests (TakeInboxMoney, MailFrame,
  IsInGuild, ProfessionsFrame) – new check T242. Command help lists part k and /ahs playtest.
- Options tooltip: "short" now names the line "Disenchant value".
- For other addons: `AHAnalyzerPro:AuctionFee(total)` (also `.AHFee`) = AH fee of one auction in WoW Forever.
- Note: since 0.65.30 prices are kept per realm and faction; going back to 0.65.29 or older shows no prices until
  the next scan.

### Version 0.65.38

**Values you can trust – the remaining points:**
- **Not selling costs money (WoW Forever):** every posting pays the AH fee, even if nothing sells. The real value
  now subtracts the expected re-postings: from your own sell rate of the last 30 days (from 3 postings), otherwise
  from the market (under 1 sale per day: up to one extra posting). Shift in the tooltip shows it
  ("~2.0x posting (your sell rate)"). Era/TBC unchanged.
- **Crafting:** materials you already own count at what you would get for them (real value after fees); missing
  ones at the buy-now price; vendor goods at the vendor price. The product's value uses the same real-value function.
- **Prediction vs. reality:** when posting, AHSentinel remembers its predicted price; when the sale arrives by mail it
  compares. Ledger -> Statistics shows "Deviation: values on average N % too high/low", per item group and in total;
  the diagnostic log gets a WERT entry (no names).
- **Incomplete scans** (stopped early or timed out) are marked: missing items are never treated as gone and the scan
  never counts as complete for sales estimates.
- **Shared prices** count only if they fit your own picture (10–300 % of your median) or a second player reports a
  similar price; until then they are stored as unconfirmed and do not count.

### Version 0.65.37

- **Own small disenchant window** (`/ahs disenchant`, or Buy -> "Worth disenchanting" -> "Disenchant window"):
  icon and name of the next item, "N left to disenchant", buttons **Disenchant**, **Skip**, **Statistics**.
  Movable, position remembered. Opens by itself once after a bulk buy when you close the AH.
  - Order: items bought with the bulk buy first, then the other disenchantable items in your bags.
  - **Disenchant** is a secure button: one click = one item. Locked in combat, no taint.
  - Protection: never items in an equipment set, quest items or items on your block list (right-click the icon:
    "never disenchant"); only green to purple. Blue/purple items and items that clearly sell for more
    (more than 1.5x the disenchant value) need a click on **Release** first.
  - Statistics: disenchants today and in total, materials received, their value.
  - If Disenchantry is loaded, the window does not open by itself (one-time hint).
- **Ledger -> Disenchant:** per day and in total: spent on bulk-bought items, value of the materials received
  (real value after AH fee; material you already sold counts at the real proceeds), profit, number of items and
  return %. A bought item is matched to its disenchant (same item, within 14 days). Own items you disenchant are
  shown separately (material value only), items bought but not yet disenchanted as "still open".
- Tests and comments use invented character names only.

### Version 0.65.36

- **Disenchant watcher:** while the AH is open and the bargain watcher is on, every other watcher round searches
  weapons and armor and checks them with the same limits as "Worth disenchanting" (minimum return, at least 10c
  profit). New finds are reported once: "N items with over X % return available" in chat and on screen – at most
  once a minute, never in combat. It never buys; you buy in Buy -> "Worth disenchanting" as before.
  Switch it off with the new button "Watcher alert: ON/OFF" there.

### Version 0.65.35

- **AH fee in the profit window – one visible assumption:** the fee depends on how many pieces you post per auction
  (at least 1s per auction). The window now says it: "at N pieces per auction (learned / chosen / cautious)".
  Learned from your own postings (median of the last 10); without data 1 piece. Click it to switch 1 / 5 / 20 (stack)
  / automatic, remembered per item. "Best recipes", "Do today" and other addons use the same assumption. The window
  no longer switches between two calculations when item data loads late. (Example: 1 Bolt of Woolen Cloth at 3s 97c,
  materials 3s 42c: fee 1s, loss 45c; at 20 per auction: 20c, profit 35c.)
- **Selling: quantity = everything in your bags** (no longer the last quantity). You change the number yourself.
- **Ledger (WoW Forever):** a sale is booked with the gold the mail really brings – the fee was already booked when
  posting, so no second fee and no refund are deducted. The invoice values go to the diagnostic log (RECHNUNG).
  Cancelling an auction now books the measured refund. Era/TBC unchanged.
- Playtest: new check S10 – AHSentinel's AH fee equals Blizzard's "Deposit" for the same quantity.

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
