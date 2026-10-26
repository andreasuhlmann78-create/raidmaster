# AH Analyzer Pro

**Market analysis, sniper and gold-making toolkit for the auction house – for every WoW version.**

> ⚠️ **This addon is in beta.** It may still contain bugs. If you run into an error or unexpected behaviour in-game, please report it in the comments – ideally with the Lua error message (if any) and the WoW version you play on.

AH Analyzer Pro scans the auction house, keeps a price history for every item and turns it into market values, trends and charts. It finds bargains for you, helps you sell at the right price and keeps a ledger of everything you earn and spend. It runs as its own tab inside the auction house window, can be used completely with the mouse and speaks the language of your WoW client.

---

## What's new

- **Comfort update:** stack size and number of stacks when posting (classic AH), mail collected automatically, a **minimum price** per item that is never undercut
- **Only what I'm missing:** shopping list from your profession window with just the missing materials (bags, bank and alts counted)
- **Alt-click** any item to open its price history · **sell rate** in the tooltip · reminder when **auctions expire**
- **Favorites** in the Buy tab · **gold goal** for all characters · **guild bank value** · one-click **raid supplies** list · price sync **guild only**
- **No absurd profits:** items showing 1000 % or more profit (bad data) are hidden
- **Sell junk at vendors with one click:** a button below every vendor sells grey items and everything a vendor pays more for than the auction house
- **Inventory value:** Ledger → "Assets" shows what your bags, bank and alts are worth, plus the gold of all characters
- **Daily summary at login:** yesterday's profit, last 7 days, gold of all characters – any time with `/ahp summary`
- **Repost with one click:** expired and cancelled auctions that came back by mail – "Repost (n)" in the Auctions tab
- **Flip recommendations:** Profit → "Flips" – regularly listed items that are cheap right now, with turnover stars
- **Mail to alts:** rules like "Herbs → Alchemist"; at the mailbox "To alts" sends the matching stacks
- **Buy tab:** iLvl for every item, sortable and as a search filter (also in Market) · **Sell tab:** listings appear much faster
- **`/ahp help`** lists all commands in the chat
- **Own, resizable window:** the addon opens in its own window by default – drag the bottom-right corner to make it as big as you like, all lists grow with it. Size and position are saved. Prefer it inside the auction house? Options → "Show in auction house"
- **New Buy tab** – works like the auction house's own Buy tab: search, categories, level, rarity. Categories show **instantly** from your last scan while the live search updates them in the background
- **Sniper and Watcher search as often as the server allows** and take turns – the Sniper hunts your targets, the Watcher finds lucky bargains. The speed adjusts itself to the limit of every WoW version
- **Buy with the mouse wheel – also over the addon window.** The sound repeats while a hit is waiting. Options → "Sniper buys with" / "Watcher buys with": mouse wheel or your own key, separately for each
- **Bid sniping:** Profit → "Bids" lists auctions whose next bid is far below market value, with time left – click to bid in the Buy tab
- **Price protection when posting:** warns before you post far below market value or follow a bait offer
- **Sale notification** with proceeds and profit as soon as an auction sells
- **Sniper shows the total amount** it will buy of an item (quantity, total cost, average price)
- **Bait offers** (single units at the very bottom) are no longer shown anywhere and never count for prices
- **Page bar in every list** (‹ 1 2 3 … 20 ›), draggable scrollbars, **Item column sorts by rarity, then name**, new **iLvl** column
- **Classic auction house** (Classic Era, TBC Anniversary, Wrath): full support – scan, all result pages, buying with the mouse wheel, "Search in auction house"
- **Profit tab:** clear columns – "Current buyout" vs. market value / vendor price / disenchant value
- **Back button** in the price history, rarity picker with checkboxes everywhere, new look with icons and gold accents, smooth scanning without stutter

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
- **Sell tab:** price check and undercut suggestion (1 copper, 1 % or 5 %), deposit, AH cut and proceeds – warns when a vendor pays more or when you would sell below your purchase price
- **Series posting:** posts every bag item with a remembered price, one click per auction
- **Auctions tab:** status of your auctions (lowest / tied / undercut / sold), cancel with one click
- **Collect AH mail:** gold and items from all auction mail with one click (COD is never paid)

### Profit & bookkeeping
- **Ledger:** income after the AH cut, spending, deposits and profit for today / 7 days / 30 days / all time – read from your mailbox invoices, nothing counted twice
- **Statistics:** sell-through per item, best selling hours and weekdays
- **Profit tab:** bargains below market value, below vendor price or below disenchant value; flipping calculator
- **Professions:** material cost, value of the result and profit for every recipe, best recipes, materials straight to a shopping list
- **Vendor prices** are learned automatically at every merchant
- **Alts & gold:** gold, bags and bank of all your characters, gold history of the last 30 days
- **CSV export**

### Comfort
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
