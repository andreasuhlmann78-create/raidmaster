# AHSentinel

**Market analysis, sniper and gold-making toolkit for the auction house – for every WoW version.**

> ⚠️ **This addon is in beta.** It may still contain bugs. If you run into an error or unexpected behaviour in-game, please report it in the comments – ideally with the Lua error message (if any) and the WoW version you play on.

> 🔁 **Formerly "AH Analyzer Pro".** Since version 0.62.0 the addon is called **AHSentinel**. Your saved data is taken over automatically on the first login. The zip now contains only the folder `AHSentinel` – if the old folder `AHAnalyzerPro` is still in your AddOns, AHSentinel tells you once in the chat: just delete it. The new command is `/ahs` (`/ahp` still works).

AHSentinel scans the auction house, keeps a price history for every item and turns it into market values, trends and charts. It finds bargains for you, helps you sell at the right price and keeps a ledger of everything you earn and spend. It opens in its own resizable window with just five tabs – **Overview, Buy, Sell, Market, Ledger** – can be used completely with the mouse and speaks the language of your WoW client.

---

## What's new

### Version 0.65.108

- **Market tab "Disenchant" now uses the same "worth up to"** as tooltip, buy list, batch buy, Sniper and API (row and
  detail line). The "minimum profit" option is only a filter now. Sniper disenchant targets are always set exactly to
  "worth up to" (chat message only from 5 % change).
- **Market core measures correctly:**
  - Own auctions: a cancel or sale message that arrives before the new auction list is no longer lost.
    "Relisted" is only guessed from really new auctions (several equal stacks no longer confuse it).
  - Disenchant recommendations are checked against the material value 24 h later, vendor recommendations
    against the confirmed vendor price (no longer against the item's AH price).
- **Releases (part D) in the Market tab:** a way below 60 % hits is hidden ("Way … locked (hits n %)"); a way with
  fewer than 20 cases shows its rows grey "still learning (n of 20)"; Flipping, Gaps and Crowded stay grey until
  30 own sales are measured. Measuring continues in the background.
- Self test "Plausibility (Ü3)": no implausible row may be shown as a recommendation.
- Tests T573–T579 (T-MA1b/c, T-MA2c, T-FG1–T-FG3, T-RK2c).

### Version 0.65.107

- **One "worth up to" everywhere (disenchanting):** tooltip, buy list mark "[Disenchant pays]", warning guard, Sniper
  disenchant targets, Market tab "Disenchant", the Market buy limit, the batch buy and the API now use one single
  calculation. Before, the tooltip and the Market tab could show two different limits for the same item.
  - Worth up to = net value × the stricter of (1 / (1 + minimum return)) and (1 − learned safety margin).
    Without learning: 10 % margin below 10 real disenchants.
  - The batch buy no longer subtracts the minimum return a second time (items up to "worth up to" are bought).
  - Self test: "One worth up to per item" checks 20 scanned items – two different values = error.
- **Implausible suggestions** (profit over 300 %) are marked "implausible: …" in the Market tab and are not counted
  as recommendations.
- **Sniper: budget used up -> question.** When a target's budget is used up and a buyable hit appears, the next buy key
  press / wheel turn does not buy but asks: "Budget of X used up (n bought). Keep buying? Top up the budget by X."
  "Yes" (Enter) adds the original budget (at most what your gold allows), the next turn buys. "No" changes nothing.
  The question comes again every time the topped-up budget is used up. Max price and quantity stay unchanged.
- **One command table:** the /ahs handler now works only from the command list – every command it understands is in
  /ahs help and in the typing list (new there: doppelt, resetscan, messreihe, ahdebug, ah).
- **API:** WorthUpTo returns a 4th value (safety 0–1, nil = still learning) and a 5th value (price per piece); the 1st
  value stays the total for qty. MaterialCost walks the price ladder for the needed quantity. Trend words of
  MarketState documented in API.md.
- **Tests:** "/ahs testroutine echt" checks the basic rules on your own data (read only: suggestions, one "worth up
  to", Sniper budget); also runs quietly after every full scan and writes violations to the diagnostic log
  ("GRUNDREGEL VERLETZT"). New tests for market-core releases (59 % locked, 61 % free, 19 cases learning) and for
  auction mail with any sender.
- Tests T556–T572 (T-RK2a/b, T-Ü3b, T-SB1–T-SB6, T-BL1/5/6, T-API-PM2/PM3, T-TU5, T-TU7, T-BP-1113-1).

### Version 0.65.106

- **Market core, step 1 "trust" (measurements for the new market tab):**
  - Every shown buy recommendation (flip, vendor, disenchant from the Market tab, Sniper hits) is remembered and checked
    24 hours later against the scan: hit rate and mean error per way. A way with at least 20 cases and less than 60 %
    hits is locked automatically (log "WEG GESPERRT"); below 20 cases it shows "still learning".
  - Sale vs. cancel: when one of your own auctions disappears with a long remaining time, the detection guesses "sold"
    or "re-posted"; the real cause (sale / your cancel) gives its error rate – the basis for releasing sales numbers.
  - Vendor prices: how many were confirmed by the game and how many differed from the remembered table.
  - New test report section "MARKT-KERN" with these numbers, limits marked "VERFEHLT" (missed).
- Tests T550–T555 (T-MA1–T-MA3, T-Ü1–T-Ü3).

### Version 0.65.105

- **No more posting too cheap when the market rises 125–150 %.** With a full price ladder (≥ 3 offers or ≥ 5 pieces)
  the suggestion is always just below the cheapest offer; your old learned price only applies to single outliers.
- **Warning guard (on by default):** clicking "Post" with a price more than 10 % below the cheapest offer (full ladder),
  more than 25 % below market value, or below the vendor/your purchase price: nothing is posted – raid warning sound,
  the button flashes red and a window asks: "Adjust price (…)" (Enter) / "Post anyway" / "Cancel", showing how much
  you would give away. Series and re-posting are stopped the same way. Buying above the target's max price, above
  "Worth up to" or more than 25 % above market value (without buyout) warns too – press again within 10 s to buy
  anyway. Options: warning guard on/off, sound on/off. Every warning is logged (WARNSCHUTZ).
- Tests T542–T549 (T-AB4d, T-WS1–T-WS6).

### Version 0.65.104

- **Command list while typing "/ahs": a mouse click now selects a command, Enter runs it.** The list stays open after the
  click, the chat input gets the focus back, and the header shows "Enter = /ahs …". If you then press Enter with the
  beginning you typed (e.g. "/ahs ent"), the selected command runs. A selection is valid for 10 s; Tab selects the next
  entry. The chat input is still never written to (no taint).
- Tests T537–T541 (T-CH1–T-CH5).

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
