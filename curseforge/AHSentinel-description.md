# AHSentinel

**Market analysis, sniper and gold-making toolkit for the auction house – for every WoW version.**

> ⚠️ **This addon is in beta.** It may still contain bugs. If you run into an error or unexpected behaviour in-game, please report it in the comments – ideally with the Lua error message (if any) and the WoW version you play on.

> 🔁 **Formerly "AH Analyzer Pro".** Since version 0.62.0 the addon is called **AHSentinel**. Your saved data is taken over automatically on the first login. The zip now contains only the folder `AHSentinel` – if the old folder `AHAnalyzerPro` is still in your AddOns, AHSentinel tells you once in the chat: just delete it. The new command is `/ahs` (`/ahp` still works).

AHSentinel scans the auction house, keeps a price history for every item and turns it into market values, trends and charts. It finds bargains for you, helps you sell at the right price and keeps a ledger of everything you earn and spend. It opens in its own resizable window with just five tabs – **Overview, Buy, Sell, Market, Ledger** – can be used completely with the mouse and speaks the language of your WoW client.

---

## What's new

### Version 0.65.69

- **Fix: ledger showed the price as quantity** (e.g. "sold 22000" for ONE cap): on some WoW Forever invoices field 5 is
  the price, not the quantity. It now only counts as quantity if it plausibly is one (never for gear). Saved sales are
  repaired once (backup kept, diagnostic log REPARATUR-MENGE).
- **Fix: positive fees in the ledger:** a refund on sale without a booked deposit (posted via Blizzard's window, another
  addon or before AHSentinel) is now covered by a matching deposit – net 0, like in the game. Postings through
  Blizzard's window or other addons are booked too. Old data is repaired once.
- **Disenchanting is counted on every way:** besides bag clicks and AHSentinel's window, macros and other addons
  (/use bag slot) are now recognised from the bag contents. Results with a material outside the table are no longer
  dropped silently (log DE-ABGELEHNT); every disenchant writes DE-GEZÄHLT or DE-VERPASST. Statistics: "today counted N
  · missed M".
- **Tooltip materials:** learned average quantity ("Ø 1.4"), the table range only with Shift; own and shared results
  named separately.

### Version 0.65.68

- **Fix (0.65.66): with the 2-hour default duration almost everything looked unsellable** – the valuation counted up to
  six lost deposits for anything that does not sell within 14 hours (e.g. dust showed "vendor"). The Sell tab keeps
  2 hours; the valuation uses 24 hours when that costs the same deposit (minimum deposit), otherwise the default
  duration. With Shift the tooltip shows the duration used.
- **Buyout failed – clear message:** "offer is gone (probably already bought)" instead of "offer gone or not enough
  gold"; the game's message is shown, gold is only mentioned when you really lack it. A gone offer is marked, its
  button locked, and it leaves the shopping list. Diagnostic log line KAUF-FEHLER (no names).
- **Minimum bid:** +5 % only when someone has already bid; without a bidder the starting bid is the minimum. If no bid
  below the buyout is possible, the bid field is hidden.
- **Detail search finds nothing although the scan listed the item:** AHSentinel retries once without item level/suffix;
  if it stays empty the row leaves the shopping list (log line DETAIL-LEER).
- Interface for other addons: price source "scan" only if the price really was in the last scan.
- Test routine: button names with text and position; outdated fee texts removed.

### Version 0.65.67

- **Fix: the line "110 in your bags: …" did not appear** (e.g. Strange Dust): the tooltip checked "stackable" with a
  game function that is missing on WoW Forever. It now works with every bag addon. If the total cannot be calculated,
  "Sell:" × quantity is shown instead and the diagnostic log gets one line GESAMTWERT.
- **Disenchant chances of green items on WoW Forever** follow the Forever guide (wow-professions.com): armor 75/20/5,
  weapons 20/75/5 (dust/essence/shard); up to item level 15 stays 80/20 without shard. Your own results still count more.
  Other game versions keep the table from warcraft.wiki.gg.
- **Tooltip:** "Materials (table + N own)" when your own disenchant results are included; with Shift the source of the
  chances. Diagnostic log: one line DE-CHANCEN per group and day (table vs. real results).

### Version 0.65.66

- **New option "Default duration" (standard: 2 hours on WoW Forever):** every new item in the Sell tab starts with it;
  a duration you pick by hand applies only to that posting. Series, repost and "Today" use it too, and so do all
  calculations. "24 h costs the same" remains only a hint.
- **Fix: "Today" told you to sell commodities to a vendor** (e.g. linen bolts) because it assumed 1 piece per auction:
  in the modern auction house a commodity is posted as ONE auction for any quantity – the minimum deposit is paid once.
  The old auction house (Era/TBC) keeps stacks.
- **Sales estimate for crowded items:** auctions on WoW Forever run at most 24 hours, so almost everything disappears
  every day even without a sale. The market sales rate is now capped at 20 % of the quantity in the last scan per day
  (assumption, checked in the diagnostic log). Your own experience (posted vs. sold, from 3 postings) comes first –
  the same number in tooltip, profit window and log.
- **Profit window:** shows the deposit per auction on WoW Forever (back on sale) and the expected number of listings
  with the expected deposit loss.
- **"Today": clicking a row** always does something visible – or shows a hint; errors are no longer swallowed.
- Diagnostic log: ABSATZ with raw rate, cap, own rate and duration; new ENTZAUBERWERT line (materials, chances, net).
- Test routine: watcher setting no longer touched (sandbox), result tooltips beside the window, T33 always with a
  reason, T52 checks "undercut" and "leave it" separately, T27 names the real reason, empty frames of other addons
  are only a hint.

### Version 0.65.65

- **Fix: posting gear failed with "Internal auction error"** on WoW Forever: the server accepts single items (gear)
  only in whole silver. AHSentinel now rounds the price of single items down to whole silver (at least 1s) and shows it
  in the field; undercutting single items uses "−1 silver". Commodities keep copper prices.
- **Fix: dust and essences were "hardly selling"** (0.65.63): the sales rate now always comes from the market; your own
  sales only raise it, and anything you sell yourself regularly is never "hardly sells".
- **"Today" no longer stutters:** the disenchant deals loop now pauses in small portions; the diagnostic log shows the
  steps per frame for slow background tasks.
- **New: command list while typing:** type /ahs in chat and all commands appear above the input box – the ones you
  use most at the top; keep typing to filter, click to run. AHSentinel never writes into the chat box. Can be turned off
  in the options ("Command list while typing").

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
