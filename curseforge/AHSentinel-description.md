# AHSentinel

**Market analysis, sniper and gold-making toolkit for the auction house – for every WoW version.**

> ⚠️ **This addon is in beta.** It may still contain bugs. If you run into an error or unexpected behaviour in-game, please report it in the comments – ideally with the Lua error message (if any) and the WoW version you play on.

> 🔁 **Formerly "AH Analyzer Pro".** Since version 0.62.0 the addon is called **AHSentinel**. Your saved data is taken over automatically on the first login. The zip now contains only the folder `AHSentinel` – if the old folder `AHAnalyzerPro` is still in your AddOns, AHSentinel tells you once in the chat: just delete it. The new command is `/ahs` (`/ahp` still works).

AHSentinel scans the auction house, keeps a price history for every item and turns it into market values, trends and charts. It finds bargains for you, helps you sell at the right price and keeps a ledger of everything you earn and spend. It opens in its own resizable window with just five tabs – **Overview, Buy, Sell, Market, Ledger** – can be used completely with the mouse and speaks the language of your WoW client.

---

## What's new

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

### Version 0.65.64

- **Ledger: "Profit" is now called "Cash"** – it is income minus spending minus fees. Bought materials count as
  spending even if they are still in stock (e.g. cloth turned into dust by crafting and disenchanting).
- **New tile "Result incl. stock":** cash plus the change in stock value during the period (bags, bank and active
  auctions of this character, valued like "Sell:" in the tooltip). A stock value is saved at the first login of the day
  and at logout, with the prices of that time. Without a starting value it shows "–".
- **"Per item" has a column "in stock"** (pieces now).
- "1 sale" / "1 purchase" instead of "1 sales".
- **Tooltip:** a price that was not in the last scan is marked "(old)"; if a scan price was replaced as an outlier,
  the value used for the calculation is shown next to it.

### Version 0.65.63

- **Selling is judged by supply and sales:** how many pieces are on the AH at your price or cheaper (without bait
  offers and your own auctions) and how many sell per day give the waiting time and the expected number of listings;
  every listing without a sale costs the deposit on WoW Forever. If it would take more than 7 days, the item "hardly
  sells" – selling is then not the best way (vendor or disenchant). One number everywhere: tooltip, profit window,
  best recipes, "Today" and the API. With Shift the tooltip shows the reason, e.g. "150 on the AH · ~5/day · ~30 days ·
  hardly sells". The sales estimate (disappeared = half sold) is an assumption and is checked in the diagnostic log.
- **Fix: "My auctions" showed wrong prices for active commodity auctions** (e.g. 0c or 2c per piece): the game reports
  the price per piece for active commodity auctions. Price, total, the "value" in the header and undercut detection
  are now correct.
- **Tooltip with Shift:** what you own has its own heading ("Owned:"), with the value in your bags and the stock of
  your other characters.

### Version 0.65.62

- **Item tooltip shows the value of everything in your bags:** for stackable items with at least 2 in your bags, a
  second line under "Sell:" shows the total of all stacks (e.g. "386 in your bags: 2g 0s 72c"), calculated like "Sell:"
  for the whole quantity (or the vendor value if the vendor pays more). The bank is not counted.
- **Posting gear (single items) – diagnosis:** on WoW Forever posting gear through AHSentinel fails with "Internal
  auction error" while Blizzard's window works. AHSentinel now records in the diagnostic log what Blizzard's window
  sends to the server and what AHSentinel sends (types and numbers only, no names), so the call can be built the same way.
- **Real error message when posting fails:** the game's own message is shown (e.g. "Internal auction error") instead of
  "not enough gold or item not available"; failed attempts are written to the diagnostic log.
- **Sell tab:** an empty quantity field counts as 1 (it showed a grey 1 but refused to post).

### Version 0.65.61

- **Fix: "Today" could miss suggestions and freeze for a moment after login** (diagnostic log: 413 ms in one frame).
  Background calculations could not pause inside a protected call (Lua 5.1), so "below vendor price" and flip
  suggestions were silently dropped and the rest ran in one go. They now pause correctly and nothing is lost.
- **Fix: Ledger → "Values right?" (forecast vs. sale) was wrong on WoW Forever:** the real price per piece was taken
  from the quantity field of the invoice ("real 1", +7800 %). Now total / quantity; existing sales are recalculated once.
- **Profit window, "Best recipes":** new prices from the sniper or sync alone rebuild the list at most every 30 seconds
  (before: every 2 seconds while sniping). Opening, switching professions, bags and ledger still update at once.

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
