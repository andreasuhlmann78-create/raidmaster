# AHSentinel

**Market analysis, sniper and gold-making toolkit for the auction house – for every WoW version.**

> ⚠️ **This addon is in beta.** It may still contain bugs. If you run into an error or unexpected behaviour in-game, please report it in the comments – ideally with the Lua error message (if any) and the WoW version you play on.

> 🔁 **Formerly "AH Analyzer Pro".** Since version 0.62.0 the addon is called **AHSentinel**. Your saved data is taken over automatically on the first login – just install both folders from the zip. The new command is `/ahs` (`/ahp` still works).

AHSentinel scans the auction house, keeps a price history for every item and turns it into market values, trends and charts. It finds bargains for you, helps you sell at the right price and keeps a ledger of everything you earn and spend. It opens in its own resizable window with just five tabs – **Overview, Buy, Sell, Market, Ledger** – can be used completely with the mouse and speaks the language of your WoW client.

---

## What's new

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

### Version 0.64.0

**"Today" – buy and post right in the list:**
- Every row now has a **button with the next step**, no need to switch tabs:
  - Buy suggestions: **Check** looks up the item in the background; the row then shows the real
    current offer ("5x at 2g 40s each = 12g") and the button becomes **Buy 12g**. Several single
    auctions: **Buy (1/3)**, one click each (WoW needs one click per auction). Goods in the modern
    auction house: the price is reserved first, then **Confirm**.
  - **Never more expensive and never more than suggested**, and the capital protection still applies.
    If the offer is gone or more expensive, the row says "no longer worth it" and nothing is bought.
  - After buying: flips get **Post** (price suggestion with price protection), disenchant deals show
    how many are in your bags, vendor deals say "Sell to a vendor".
  - Items from your bags: **Check → Post**. Returned auctions: **Repost**, one click each.
- A click on the row itself still switches to the tab, as before.
- **For other addons:** `AHAnalyzerPro.Today:QuickBuy(itemID, qty, maxPrice, label)` and
  `:QuickSell(itemID, count)` add a row at the top of "Today" – nothing is bought without your click.
- **ProfessionSentinel:** its "craft today" suggestions appear in "Today"; the button walks you
  through buying the reagents, crafting and posting.
- Disenchant texts from 0.63.0 are now translated into all languages.

### Version 0.63.4

- **Bargain watcher only with a reliable market value:** the watcher used to report "bargains" at 0–10 % of the market value – almost always because the market value itself was wrong (moon price, rare item, price crash). As the watcher buys with the mouse wheel, only a market value you can trust counts now.
- **Test mode log:** watcher purchases show as "Sniper buy (watcher)" with the price; goods bought from the buy tab and the sniper show the price too.

### Version 0.63.3

- **Quality tiers (retail):** crafting reagents and crafted items come in several tiers – so far e.g. "Bismuth" showed three times with no difference. The tier icon now follows the name (buy, market, sell, sniper, ledger …).
- **Feedback after posting and cancelling:** instead of "Posting …" / "Cancelling …" staying forever, the window now shows "Posted: …" / "Cancelled: …".
- **Daily summary:** showed "+ all your gold since yesterday" when the game briefly reported 0 gold at login. Such a 0 value no longer counts.
- **Test mode log:** buying goods (retail) now shows the price, a sniper buy is logged as "Sniper buy" instead of "Buyout".

### Version 0.63.2

- **Self-test on retail:** stopped with "script ran too long" (retail stops scripts that run too long in one go – with about 20,000 scanned items that happens). The test now pauses regularly; the language test checks one language per frame.
- **Sell tab with the auction house closed:** showed "No sellable items in your bags" on retail although the bags were full. The "can this be posted?" check now only runs while the auction house is open.
- **Reagent bag (retail):** items in it now count for selling, mail to alts and vendor selling.

*Older versions: see the changelog of each file in the **Files** tab.*

---

## ☕ Support the addon

AHSentinel is free and made in my spare time. If it helps you make gold, you can support it with a small donation – thank you so much!

**[Donate with PayPal](https://www.paypal.com/ncp/payment/46R68N2BF7BTY)**

In-game: the **Support** button in the addon window (or `/ahs donate`).

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
