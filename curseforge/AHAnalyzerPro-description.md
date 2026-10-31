# AH Analyzer Pro

**Market analysis, sniper and gold-making toolkit for the auction house – for every WoW version.**

> ⚠️ **This addon is in beta.** It may still contain bugs. If you run into an error or unexpected behaviour in-game, please report it in the comments – ideally with the Lua error message (if any) and the WoW version you play on.

AH Analyzer Pro scans the auction house, keeps a price history for every item and turns it into market values, trends and charts. It finds bargains for you, helps you sell at the right price and keeps a ledger of everything you earn and spend. It opens in its own resizable window with just five tabs – **Overview, Buy, Sell, Market, Ledger** – can be used completely with the mouse and speaks the language of your WoW client.

---

## What's new

### Version 0.60.8

- **Fixed: no price lines in item tooltips** on some clients (e.g. TBC Anniversary). The addon
  now hooks every way WoW fills an item tooltip and resizes the tooltip after adding its lines.
  The self-test now checks the real bag tooltip.
- **Esc closes only the top window:** e.g. the price history window - the addon window and the
  auction house stay open (before, one Esc closed everything).
- **Price history window:** the close button no longer sits on top of the "All" button.
- **Test mode** now also restores search favorites, repost list and mail rules.
- **Your own searches come first:** a running watcher round is stopped so the buy tab no longer
  waits ("Waiting for the watcher ...").
- Buy tab shows "Bought: ..." instead of "Purchase in progress ..." when done.
- Overview: tenfold price jumps (almost always bogus data) are no longer listed as rises/drops.
- Smaller fixes: test mode log shows sniper buys as such, shopping lists release the keyboard after
  deleting a list, no "N entries" overlap in the lists window, shorter option label "Expiry
  reminder", posting fee on classic AH shows "when posting" instead of "?", iLvl filter hint only
  when there are results, faster mouse-wheel scrolling in the report window, report title
  "Test report".

### Version 0.60.7

- **New "Test" button** at the top of the window (and in the auction house bar): self-test and
  the new **test mode** in one window.
- **Test mode:** try every feature by hand with your real auction house data - buy, bid, sniper
  (mouse wheel too), post, cancel, vendor sale, collecting and sending mail. Every trade is only
  simulated: the command to the server is intercepted and the server's answer is played back, so
  messages, ledger and sniper counters behave like the real thing. All settings and data (lists,
  ledger, sniper, watcher, selling) are restored when you stop test mode - or automatically after
  a /reload or crash. A log shows every simulated action and is included in the copied report.
  Note: only the addon's buttons are simulated, Blizzard's own auction house buttons still buy
  for real. Also: `/ahp testmode`.

### Version 0.60.6

- **Self-test simulates real trading:** with the real auction house listings it now runs instant
  buy, bid, sniper buy, posting and cancelling exactly like the real thing - same listing, same
  price, same command. The command to the server is intercepted, so nothing is bought, posted or
  cancelled; the test finally checks that your gold is unchanged. Chat messages during the
  simulation are marked "[Simulation]".
- **Self-test:** the watcher is switched off again right after its test round, so it no longer
  blocks the following server searches.

### Version 0.60.5

- **Fixed (classic clients):** a Lua error "attempt to compare number with nil" could appear when
  opening the auction house (bid tracking after a reload).
- **Watcher/Sniper status in the header** now always updates when you switch them on or off.
- **Self-test:** a market scan still running in the background no longer makes all server
  searches time out - in the "saved data" mode it is stopped, otherwise the test waits for it.
  Starting a scan during the test is blocked.
- **Self-test:** settings, the watcher and the window (tab, or closed) are restored reliably
  after the test; if something can't be restored, the report says so.
- **Text window** (copy report) now always opens in front, starts at the top and scrolls
  quickly with the mouse wheel (hold Shift for big steps).

### Version 0.60.4

- **Self-test with saved data:** new button "With saved data" in the self-test window (or
  `/ahp test saved`). It tests with the auction house data you already scanned - no new scan.
  It even runs with the auction house closed; the server searches are then skipped.

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
