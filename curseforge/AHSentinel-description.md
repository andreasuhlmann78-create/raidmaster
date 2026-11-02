# AHSentinel

**Market analysis, sniper and gold-making toolkit for the auction house – for every WoW version.**

> ⚠️ **This addon is in beta.** It may still contain bugs. If you run into an error or unexpected behaviour in-game, please report it in the comments – ideally with the Lua error message (if any) and the WoW version you play on.

> 🔁 **Formerly "AH Analyzer Pro".** Since version 0.62.0 the addon is called **AHSentinel**. Your saved data is taken over automatically on the first login – just install both folders from the zip. The new command is `/ahs` (`/ahp` still works).

AHSentinel scans the auction house, keeps a price history for every item and turns it into market values, trends and charts. It finds bargains for you, helps you sell at the right price and keeps a ledger of everything you earn and spend. It opens in its own resizable window with just five tabs – **Overview, Buy, Sell, Market, Ledger** – can be used completely with the mouse and speaks the language of your WoW client.

---

## What's new

### Version 0.65.2

- **GoldSentinelGame version 2:** the shared game version detection now also wins against early versions
  that other GoldSentinel addons briefly shipped – no Lua errors when several addons are loaded together.
- Vendor prices: if the game has no item link function at the merchant, the item ID is read another way.

### Version 0.65.1

- **Shared game version detection:** AHSentinel now uses **GoldSentinelGame**, the same detection all
  GoldSentinel addons get step by step. WoW Forever always counts as the modern client there, never as Classic.
- New: `/gsgame` shows in the chat which game version was detected; `/ahs debug` shows it too.
- Nothing else changes for you.

### Version 0.65.0

**WoW Forever and Retail (modern client) – nothing stays silently empty any more:**
- **Profession window:** recipes are now read through the modern profession interface
  (`C_TradeSkillUI`) when the old one is missing – the profit panel next to the profession window and the
  crafting suggestions in "Today" work there too. Older game versions keep the old way.
- **Vendor prices:** read through `C_MerchantFrame` when the old function is missing. Items that cost
  a currency or tokens (e.g. Merchant's Favor) are remembered with their exact costs.
- **Raid supplies:** on WoW Forever the Classic raid template is used (`/ahs raid`).
- **Watcher and the 15-minute full scan:** if the server refuses the due full scan after a watcher
  round, the watcher pauses until the full scan has run.
- **Sniper:** if WoW blocks the pre-reserved goods purchase (no error, only a blocked-action event),
  "one notch buys" switches itself off and the sniper goes back to two notches.
- Translations for the WoW Forever deposit texts from 0.64.2 in all languages.

### Version 0.64.2

- **WoW Forever: listing fee counted correctly.** On WoW Forever every auction costs **at least
  1 silver** deposit, and it is **never refunded**, not even when the item sells. AHSentinel now
  detects Forever itself and always subtracts the fee instead of only as a risk for expired auctions:
  flips, sell suggestions in "Today", crafting profits, bargains, disenchant bargains (materials are
  sold in stacks, fee per piece), vendor-vs-AH comparison and the Sell tab (shows "not refunded").
- This mostly affects **cheap items**: an item worth 1s 50c in the AH and 71c at a vendor leaves only
  42c after 5 % and the 1s fee – "Today" then suggests **selling to a vendor**.
- Fee per piece = max(1 silver, deposit of a full stack) ÷ stack size. Other game versions are
  unchanged (the deposit is refunded on a sale).
- Profit calculator: on Forever the 1 silver deposit is included.

### Version 0.64.1

- **"Today" suggests crafting – even without ProfessionSentinel:** AHSentinel now remembers the
  recipes of each character when you open the profession window. "Today" then suggests the 2–3 most
  profitable recipes you **already know** (result sells well, at least 10 % profit after the AH cut).
  The button **Buy reagents** adds a buy row for every missing reagent from the auction house
  (10 % price margin, nothing bought without your click); reagents from vendors are named in the chat.
  When everything is there: "All there – craft".
- With ProfessionSentinel installed, its suggestions are used instead (no duplicates).
- Characters with a crafting profession but without ProfessionSentinel see a small tip at the bottom
  of "Today" – **Hide** removes it for good.

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
- **Sniper:** targets with max price, quantity, budget, rarity, item level and level filters – searches on its own while the auction house is open
- **Bargain watcher:** herbs, ore, cloth, leather, enchanting, elemental, gems, cooking and more – anything at or below x % of market value (default 50 %); never weapons or armour
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
- **Vendor prices** are learned automatically at every merchant
- **Alts & gold:** gold, bags and bank of all your characters, gold history of the last 30 days
- **CSV export**

### Comfort
- **Five tabs** with sub-tabs, price history in its own window, sniper and watcher switchable in the title bar
- Two designs: **Classic** (looks like the WoW auction house) and **Modern**
- Item search by name in any language, by item ID or by shift-click, with suggestions while typing
- Built-in item name list (~33,000 items in 10 languages, incl. The Burning Crusade); lists always show names in your chosen language
- Help page for every tab, right-click menu on every item, minimap button

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

One download for everything – just copy both folders from the zip (`AHSentinel` and the small transition folder `AHAnalyzerPro`) into `Interface\AddOns` of your game.

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
