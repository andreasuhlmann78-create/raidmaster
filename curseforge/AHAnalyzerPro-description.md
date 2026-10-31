# AH Analyzer Pro

**Market analysis, sniper and gold-making toolkit for the auction house – for every WoW version.**

> ⚠️ **This addon is in beta.** It may still contain bugs. If you run into an error or unexpected behaviour in-game, please report it in the comments – ideally with the Lua error message (if any) and the WoW version you play on.

AH Analyzer Pro scans the auction house, keeps a price history for every item and turns it into market values, trends and charts. It finds bargains for you, helps you sell at the right price and keeps a ledger of everything you earn and spend. It opens in its own resizable window with just five tabs – **Overview, Buy, Sell, Market, Ledger** – can be used completely with the mouse and speaks the language of your WoW client.

---

## What's new

### Version 0.60.3

- **Fix for TBC Anniversary (and other classic clients):** "My auctions" never updated and some
  auction house messages (e.g. "auction posted") never arrived. These clients know the event names
  of the modern auction house but never fire them for the classic one; the addon now always uses
  its own events there. Found by the new self-test.
- **Self-test:** the copied report can now be scrolled, and the result list is wider - hover a
  row to see the full text.

### Version 0.60.2

- **Self-test:** Options -> "Self-test" or `/ahp test` checks every feature with real data from
  your auction house: market scan (if needed), market data, every tab, all calculations and real
  server searches (Buy, price check, Sniper, Watcher, your auctions). Buying, bidding, posting and
  cancelling are locked while it runs; your settings and sniper targets are restored afterwards.
  The result is shown in a window, can be copied as a report and is saved in the SavedVariables.

### Version 0.60.1

- **Real minimap button:** the button now sits on the minimap like with other addons - drag it
  around the minimap with the mouse, the position is saved. Works with round and square
  minimaps. Hide or show it in Options or with `/ahp minimap`; `/ahp reset` brings it back.
- **New icon:** a golden scale - on the minimap button, in the title bar and in the addon list.

### Version 0.60.0

**Tidier window - 5 tabs instead of 11:**

- **Overview · Buy · Sell · Market · Ledger.** Related pages are now sub-tabs:
  Buy = Buy, Sniper, Watcher, Bargains · Sell = Post, My auctions · Market = All prices, Watchlist.
  Every feature is still there, nothing was removed.
- **Price history in its own window:** clicking an item opens the price history next to the
  addon - the list you came from stays exactly where it was. The window can be moved and resized.
- **Sniper and watcher in the title bar:** see at a glance whether they are running and turn them
  on or off with one click (right-click opens their tab).
- **Remembers where you were:** the addon opens on the tab you used last, and every main tab
  remembers its last sub-tab.

### Version 0.59.33

**Comfort update - twelve small things that save clicks every day:**

- **Stack size and number of stacks** (classic auction house): in the Sell tab, choose e.g.
  5 stacks of 20. Remembered per item and used by "Post all".
- **Collect mail automatically:** opening the mailbox collects auction mail right away
  (hold Shift while opening to skip). Can be turned off in Options.
- **Minimum price per item:** the new "Min" button in the Sell tab remembers the current price
  as a floor. The suggestion never goes below it, and "Post all" waits instead of selling cheap.
- **Only what I'm missing:** next to your profession window, a new button puts only the missing
  materials on a shopping list - counting your bags, bank and alts.
- **Alt-click an item** in your bags or a link in chat: opens the price history, or the Buy tab
  while the auction house is open.
- **Sell rate in the tooltip:** how much of what you posted actually sold (last 60 days) and how
  long it usually took.
- **Expiring auctions:** a message when your auctions have less than 30 minutes left, and at
  login what expired since your last visit.
- **Favorites in the Buy tab:** save searches (text, category, level, iLvl, rarity) and run them
  again with one click.
- **Gold goal:** set a goal for all characters together (Options or `/ahp goal 5000`) and get a
  message when you reach it. The daily summary shows your progress.
- **Guild bank value:** new view Ledger -> "Guild bank" shows what is in your guild bank and what
  it is worth (TBC and later).
- **Raid supplies:** one click creates a shopping list with potions, flasks, elixirs and buff
  food for a raid week (Classic, TBC, Wrath) - with the total cost. Also `/ahp raid`.
- **Price sync with your guild only:** new option to share prices only with your guild.

*Older versions: see the changelog of each file in the **Files** tab.*

---

## ☕ Support the addon

AH Analyzer Pro is free and made in my spare time. If it helps you make gold, you can support it with a small donation – thank you so much!

**[Donate with PayPal](https://www.paypal.com/ncp/payment/46R68N2BF7BTY)**

In-game: the **Support** button in the addon window (or `/ahp donate`).

---

## Features

### Market data
- **Full market scan** with price history for every item
- **Market value** = median of the last 14 days, so single outliers barely count
- **Trends and charts** with time-based EMAs and crossover markers
- **Bait-offer protection** and automatic re-checks of suspiciously cheap prices
- **Price sync** between all players using the addon
- Prices and a small price chart in **every item tooltip**, plus vendor price and disenchant value

### Buying
- **Sniper:** targets with max price, quantity, budget, rarity, item level and level filters – searches on its own while the auction house is open
- **Bargain watcher:** herbs, ore, cloth, leather, enchanting, elemental, gems, cooking and more – anything at or below x % of market value (default 50 %); never weapons or armour
- **One-notch buying** with the mouse wheel or your own key binding
- **Shopping lists** with quantities – check all prices at once or turn missing items into sniper targets; items already in your bags are subtracted
- **Watchlist** with alerts

### Selling
- **Sell → Post:** price check and undercut suggestion (1 copper, 1 % or 5 %), deposit, AH cut and proceeds – warns when a vendor pays more or when you would sell below your purchase price
- **Series posting:** posts every bag item with a remembered price, one click per auction
- **Sell → My auctions:** status of your auctions (lowest / tied / undercut / sold), cancel with one click
- **Collect AH mail:** gold and items from all auction mail with one click (COD is never paid)

### Profit & bookkeeping
- **Ledger:** income after the AH cut, spending, deposits and profit for today / 7 days / 30 days / all time – read from your mailbox invoices, nothing counted twice
- **Statistics:** sell-through per item, best selling hours and weekdays
- **Buy → Bargains:** below market value, below vendor price or below disenchant value, bids and flip recommendations; flipping calculator
- **Professions:** material cost, value of the result and profit for every recipe, best recipes, materials straight to a shopping list
- **Vendor prices** are learned automatically at every merchant
- **Alts & gold:** gold, bags and bank of all your characters, gold history of the last 30 days
- **CSV export**

### Comfort
- **Five tabs** with sub-tabs, price history in its own window, sniper and watcher switchable in the title bar
- Two designs: **Classic** (looks like the WoW auction house) and **Modern**
- Item search by name in any language, by item ID or by shift-click, with suggestions while typing
- Built-in item name list (~23,000 items in 10 languages)
- Help page for every tab, right-click menu on every item, minimap button

---

## Supported game versions

AH Analyzer Pro works on **every** WoW version – all with the same features:

- **Retail**
- **Mists of Pandaria Classic** and **Cataclysm Classic**
- **Wrath Classic** and **Wrath Titan Reforged**
- **TBC Anniversary**
- **Classic Era** (incl. Hardcore / Season realms)
- **WoW Forever**

Both auction house types are supported: the modern one (Retail, Cata, MoP) and the classic one (Classic Era, TBC, Wrath).

One download for everything – just copy the folder `AHAnalyzerPro` into `Interface\AddOns` of your game.

## Languages

English, German, French, Spanish (EU and Latin America), Portuguese, Italian, Russian, Korean, Chinese (simplified and traditional). The addon follows your client language automatically; you can change it in the options or with `/ahp language`.

## Commands

Everything works with the mouse – the commands are optional.

| Command | Action |
|---|---|
| `/ahp` | open / close the window |
| `/ahp help` | list all commands in the chat |
| `/ahp scan` | start a full market scan |
| `/ahp sniper` | sniper on / off |
| `/ahp summary` | daily summary in the chat |
| `/ahp alts` | rules for mail to alts |
| `/ahp goal 5000` | gold goal (no number: progress, `off`: clear) |
| `/ahp raid` | raid supplies as a shopping list |
| `/ahp lists` | shopping lists |
| `/ahp options` | options |
| `/ahp sync` | price sync on / off |
| `/ahp design` | switch between Classic and Modern |
| `/ahp language` | change the addon language |
| `/ahp export` | CSV export |
| `/ahp donate` | support the addon (PayPal link) |
| `/ahp manual` | help window with guide |
| `/ahp reset` | reset window and button positions |

---

## Feedback

Found a bug or have an idea? Leave a comment here on CurseForge – bug reports with the Lua error message and your WoW version help the most.

## Credits & license

Made by **GoldSentinel**. Licensed under **GPL-3.0-or-later**.
Item names from [QuestieDB](https://github.com/Questie/QuestieDB) (GPL-3.0) and [wow-classic-items](https://github.com/nexus-devs/wow-classic-items) (MIT) – thank you!
World of Warcraft and all item names © Blizzard Entertainment.
