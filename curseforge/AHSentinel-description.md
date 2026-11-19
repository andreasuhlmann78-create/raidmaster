# AHSentinel

**Market analysis, sniper and gold-making toolkit for the auction house – for every WoW version.**

> ⚠️ **This addon is in beta.** It may still contain bugs. If you run into an error or unexpected behaviour in-game, please report it in the comments – ideally with the Lua error message (if any) and the WoW version you play on.

> 🔁 **Formerly "AH Analyzer Pro".** Since version 0.62.0 the addon is called **AHSentinel**. Your saved data is taken over automatically on the first login. The zip now contains only the folder `AHSentinel` – if the old folder `AHAnalyzerPro` is still in your AddOns, AHSentinel tells you once in the chat: just delete it. The new command is `/ahs` (`/ahp` still works).

AHSentinel scans the auction house, keeps a price history for every item and turns it into market values, trends and charts. It finds bargains for you, helps you sell at the right price and keeps a ledger of everything you earn and spend. It opens in its own resizable window with just five tabs – **Overview, Buy, Sell, Market, Ledger** – can be used completely with the mouse and speaks the language of your WoW client.

---

## What's new

### Version 0.65.350

- **Less memory during the full scan in the test routine:** the check "is this a commodity?" now also uses its cache for real items during the test routine (before, it asked the game twice per item), so the test measures the scan like it runs for players.

### Version 0.65.349

- **"Today" sell prices:** an offer list from an older full scan is no longer used unchanged when a newer scan has a different price (a sell suggestion of 1s 25c was compared with a 58c offer from the day before). Cheaper steps that are gone are dropped; a newer, lower price comes first.
- **Smoother watcher:** while a round is running, the watcher only reads the result list when the game reports new results (or once per second) instead of ten times per second.
- **Test routine:** the report names the test location (zone, nameplates in view, ping); the longest frame shows AHSentinel's own work next to it; a separate line shows the longest full-scan frame with own work, the rest and memory per addon.

### Version 0.65.348

- **Watcher no longer waits for minutes:** after a market scan, up to 60 suspiciously cheap offers are re-checked; the watcher now gets a round after 45 seconds at the latest instead of waiting for the whole list.
- **Your own auctions first:** these re-checks now run in the background list, so "Check undercuts" and clicked items are no longer stuck behind them.
- **One "Worth up to" everywhere:** a temporary price store of the disenchant check was also used by the tooltip and the market while the check paused, which could show two different values for one item. It is now only used by the check itself.
- **Less memory during a full scan:** the "Today" list and the forecast wait until the full scan is done (at most 5 minutes).
- **Test routine:** shows the length of the price check lists when a search is blocked; the address book check names the changed fields; the full-scan memory shows the share of each task first.

### Version 0.65.347

- **GoldSentinel communication (version 3):** during a test routine of any GoldSentinel addon, no addresses are learned from test messages and no real whispers are sent; a "player not online" message is recognised more reliably.
- **For other addons:** `AHSentinelAPI.TestRunning()` tells whether AHSentinel's test routine is running.

### Version 0.65.346

- **Less stutter while the auction house updates:** disenchant deals, the overview movers, the ledger tab, price sharing with guild mates and long list sorting now work in small steps.
- **Price history window:** draws the area under the price line with half as many pieces and no longer retries an unsupported colour function for every piece.
- **Crafting detection:** casting a profession's rank spell (it opens the profession window) no longer counts as crafting; only recipes from the profession window count.
- **Test routine:** sniper and watcher checks name what blocked a search ("not testable" when the server blocks); the shared GoldSentinel address book is now left exactly as it was (a test name of another addon no longer breaks the check); more detail for full-scan memory and watcher frame times.

*Older versions: see the changelog of each file in the **Files** tab.*

---

## ☕ Support the addon

AHSentinel is free and made in my spare time. If it helps you make gold, you can support it with a small donation – thank you so much!

**[Donate with PayPal](https://www.paypal.com/ncp/payment/46R68N2BF7BTY)**

In-game: the **Support** button in the addon window (or `/ahs donate`).

---

## Features

### Market tab – what makes the most gold right now
- **Today** (or `/ahs today`): your own things first (post, repost, disenchant, craft), below them the best chances – every row has a button with the next step
- **My stock:** everything you own (bags, bank of all your characters, your auctions) with quantity, value now after fees and the best way to turn it into gold – what loses the most while waiting is on top
- **Disenchant:** items that bring at least 20 % profit after disenchanting, at the current market and after fees; one click makes a sniper target up to "Worth up to"
- **Market direction** per level band and the time until the next full scan is possible, right in the header
- Only what your data really backs is shown; whatever is still learning stays grey. Flip, vendor, gaps, crowded and trends views are available with the expert option
- **Crafting:** profitable recipes you already know, with a button that adds the missing reagents as buy rows (with **ProfessionSentinel** also missing recipes, vendors and drops, step by step)
- **Capital protection:** the market plans with at most 25 % of your gold by default (adjustable from 1 to 50 %)

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
