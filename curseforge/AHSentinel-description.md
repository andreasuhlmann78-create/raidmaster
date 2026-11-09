# AHSentinel

**Market analysis, sniper and gold-making toolkit for the auction house – for every WoW version.**

> ⚠️ **This addon is in beta.** It may still contain bugs. If you run into an error or unexpected behaviour in-game, please report it in the comments – ideally with the Lua error message (if any) and the WoW version you play on.

> 🔁 **Formerly "AH Analyzer Pro".** Since version 0.62.0 the addon is called **AHSentinel**. Your saved data is taken over automatically on the first login. The zip now contains only the folder `AHSentinel` – if the old folder `AHAnalyzerPro` is still in your AddOns, AHSentinel tells you once in the chat: just delete it. The new command is `/ahs` (`/ahp` still works).

AHSentinel scans the auction house, keeps a price history for every item and turns it into market values, trends and charts. It finds bargains for you, helps you sell at the right price and keeps a ledger of everything you earn and spend. It opens in its own resizable window with just five tabs – **Overview, Buy, Sell, Market, Ledger** – can be used completely with the mouse and speaks the language of your WoW client.

---

## What's new

### Version 0.65.22

- **Disenchanting in the tooltip – actual and estimated, clearly separated:**
  - "Disenchant actual (avg of N)": only from real disenchants of this group (yours + shared): sum of the materials
    you really got × current AH price from the last scan ÷ N. Below 10 disenchants it says "(little data)", without
    any disenchant the line is left out.
  - "Disenchant estimated (table)": the previous value (table blended with results).
  - One line per material: chance (or actual frequency "x/N") × average amount · AH price from the last scan (with
    age) · market value = share; below it "after fees" (WoW Forever: AH fee 5 %, at least 1s per auction).
  - The tooltip says which value the disenchant bargains use: the actual average from 10 disenchants on, otherwise the
    estimate.
  - New option "Disenchant: per material" (on by default).

### Version 0.65.21

- **WoW Forever fee rule:** Forever has only ONE fee – the AH fee = 5 % of the auction's price, at least 1 silver,
  per auction (per stack), paid when posting. There is no separate deposit any more. Examples: 3s 90c → 1s,
  2s → 1s, 1g → 5s, a stack of 20 at 1c each → 1s once.
- The row "Deposit (not refunded)" is gone from the profit window and the Sell tab; there is only "AH fee (5 %,
  min. 1s)". The same rule is used everywhere: profit window, Sell tab, "Do today", bargains, flips, disenchant
  values, vendor comparison, profit calculator.
- When posting, the fee really taken from your gold is written to the diagnostic log (entry EINSTELLEN: price,
  quantity, fee) to confirm the rule in the game. The deposit measuring of 0.65.17–0.65.20 is removed. The warning when the
  fee is more than 10 % of the price stays.
- Era, TBC and Retail are unchanged (5 % on sale, deposit refunded on sale).

### Version 0.65.20

- **Profession window:** the "Best recipes" list is rebuilt at most every 2 seconds while you craft (it was rebuilt
  up to 190 times in a session); opening and switching professions stay immediate.
- **Sniper (WoW Forever):** the sniper no longer reserves commodities on its own without a key press. WoW Forever
  blocked that call ("action blocked" once per session). Commodities are bought with 2 notches: the 1st reserves,
  the 2nd buys. If WoW blocks it on another client, the addon remembers that for this client, also after /reload.
- **Mail rules to alts:** a rule with a sub-category now also works after /reload at the mailbox without visiting the
  auction house first. Rules from 0.65.11–0.65.17 are found again.
- **Buy:** the category list keeps its scroll position while you type or search, and the selected category stays
  visible. Until the auction house is opened once, Classic Era, TBC and WoW Forever show the classic order (with
  Projectile, Quiver, Reagent).
- **Sale message:** also works when the game text uses a numbered placeholder ("%1$s").
- **Profession window:** without a tab bar the profit window docks directly next to the window (only over its
  invisible border on the old window), never over visible parts. Clicking a recipe no longer turns on "show unlearned".
  In Classic Era and TBC there is no empty line where the deposit line is (WoW Forever only).
- **Deposit:** the warning says when the deposit is refunded on sale (Classic Era, TBC …). Measurements are not taken
  in test mode, an estimate of the old auction house is never stored as a measurement, the money is checked again
  shortly after posting, and the last 300 measurements go into the diagnostic log (numbers only, no names).
  "Do today – craft" deducts the deposit for the whole crafted quantity.
- Price field tooltip shows g/s/c in every language.
- Developer test routine: new area K (interface in the real client: tooltips, overlapping windows, screen, labels,
  plausible values, error loops, T191–T197) and tests T198–T202; saved recipes, window positions and watcher data stay
  unchanged during the routine.

### Version 0.65.18

- **Vendor button no longer covers anything:** the "Sell: … items" button sat below the merchant window and covered the
  "Buyback" tab. It now sits above the merchant window, top right – never next to the "Merchant" / "Buyback" tabs.
- **Only when there is something to sell:** instead of "Sell: 0 items (0)" the button is hidden.
- **Off by default with LevelPilot:** if LevelPilot is loaded and sells grey items itself (on by default there), the
  button stays off until you turn it on yourself in the options ("Button at vendors"). Your own setting always wins.
- Test routine (developer only): T186 checks in game that the button covers no tab of the merchant window (otherwise
  FAIL), T187 checks the default with and without LevelPilot.

### Version 0.65.17

- **Deposit is measured:** every time you post, the addon notes item, vendor price, quantity, duration, your price
  (per piece and total), the deposit the game reports and the deposit really taken from your gold, plus the ratio
  deposit/price and deposit/vendor price – in the diagnostic log (`/ahs protokoll`, entry EINSTELLEN) and in the GSDIAG1
  export, without any names. If the game does not report a deposit, the last measured one for that item is used –
  never a guess.
- **Deposit warning:** if the deposit is more than 10 % of the price, posting asks for a second click. The threshold
  is adjustable in the options (off / 5 / 10 / 20 / 30 %).
- **"Do today": below vendor price:** offers whose price per piece is below the vendor sell price (from the last scan
  or your current search) are shown as "Below vendor price: buy and sell to a vendor" – profit = (vendor price −
  purchase price) × quantity, no AH cut. Only from 10 silver profit per offer (adjustable: all / 5s / 10s / 50s / 1g),
  the best 10, sorted by profit. Items without a vendor price never appear, offers that are gone are hidden. The
  button buys only on your click, then tells you to sell to a vendor.

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
