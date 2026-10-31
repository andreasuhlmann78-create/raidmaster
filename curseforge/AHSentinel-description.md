# AHSentinel

**Market analysis, sniper and gold-making toolkit for the auction house – for every WoW version.**

> ⚠️ **This addon is in beta.** It may still contain bugs. If you run into an error or unexpected behaviour in-game, please report it in the comments – ideally with the Lua error message (if any) and the WoW version you play on.

> 🔁 **Formerly "AH Analyzer Pro".** Since version 0.62.0 the addon is called **AHSentinel**. Your saved data is taken over automatically on the first login – just install both folders from the zip. The new command is `/ahs` (`/ahp` still works).

AHSentinel scans the auction house, keeps a price history for every item and turns it into market values, trends and charts. It finds bargains for you, helps you sell at the right price and keeps a ledger of everything you earn and spend. It opens in its own resizable window with just five tabs – **Overview, Buy, Sell, Market, Ledger** – can be used completely with the mouse and speaks the language of your WoW client.

---

## What's new

### Version 0.62.2

- **Test and developer functions are hidden:** the self-test and the test mode (button "Test",
  `/ahs test`, `/ahs testmode`) are only available to the developer now. For everybody else the
  addon looks and works the same, just without these tools.

### Version 0.62.1

**Realistic prices – important for a fresh server, where prices fall every day:**
- **Market value follows the market faster:** newer prices count more (half-life 3 days) instead of a
  plain 14-day median, and silly prices like "1666g 99s 98c" no longer count at all.
- **Price crash detection:** if the last two scans (at least 6 hours apart) are both far below the market
  value, the item is marked "price just crashed" (tooltip) and its market value counts as uncertain.
  Such items are no longer suggested for buying, flipping or selling.
- **"Today" sells at what you really get:** at most 5 % above the cheapest current offer, never the old
  market value. If the AH price has crashed close to the vendor price, it suggests selling to a vendor.
- **Bids** are only suggested on items with a reliable market value and never on silly prices.
- **Profit/day** in bargains counts only a share of the daily sales (you are not the only seller),
  at most the available amount and what 20 % of your gold can buy.
- The overview no longer lists prices ending in …99s 9xc.

**Fixes:**
- **Esc** closes the price history again instead of the whole auction house (also after a language switch).
- **Test mode:** a sniper purchase with the mouse wheel now shows up in the test log and the ledger.
- **Mailbox:** new button "Repost (N)" for returned auctions; on-screen messages say "[Test]" in test
  mode; collecting is slower in test mode so you can try "Stop"; returned test goods are counted.
- `/ahs summary` no longer shows "+all your gold since yesterday" when yesterday's gold is unknown.
- The money field shows what it understood for every input ("= 5s"), not only for plain numbers.
- An item tooltip no longer stays on top of a newly opened window ("Today", options, ...).
- Self-test details no longer show raw icon codes.

**Languages:**
- **About 10,000 more item names in every language,** including all Burning Crusade items
  (English: 25,800 instead of 14,800). Lists no longer show German names in an English interface.
- **Lists always show names in the current language** – search results, sniper targets, watch list,
  shopping lists, ledger, auctions – also right after switching, without a new search.
- The buy tab keeps its category, search text and filters after a language switch.
- Options: long labels (French, Spanish, Russian) wrap into a second line instead of being cut off.
- Buy filters: short placeholders ("Lvl min / max") that no longer overlap.
- Chinese: "simplified" and "traditional" can be told apart in the language list; item names without a
  Chinese name are written without umlauts (ö → oe), which the Chinese font cannot show.
- Self-test: the language check now also finds cut-off option labels, list names in the wrong
  language and counts missing item names per language.

### Version 0.62.0

**AH Analyzer Pro is now called AHSentinel** – part of the Sentinel family (BuffSentinel,
GuildSentinel, ThreatSentinel).

- **Your data is taken over automatically:** the download contains the new folder `AHSentinel`
  and a small `AHAnalyzerPro` folder that only hands your old data (prices, ledger, lists,
  sniper targets, settings) over on the first start. Afterwards you can delete `AHAnalyzerPro`.
- **New command `/ahs`** (also `/ahsentinel`); `/ahp` keeps working.
- Everything else stays the same.

**Install:** copy both folders from the ZIP into `Interface\AddOns` (overwrite the old
`AHAnalyzerPro` folder), start the game, done.

### Version 0.61.2

- **One language for everything:** item names now follow the addon language (unless you chose a
  separate item-name language), and the tooltip shows the item name in that language when it
  differs from the game client's.
- **Language switch rebuilds every window:** besides the main window also "Today", the test window,
  the mail-to-alts rules and the mailbox panel (even while the mailbox is open).
- **Self-test:** new check "language switch" - every addon language once and then back and forth
  several times; window, tabs, texts, item names and tooltip must appear in the chosen language,
  and the original language is restored afterwards.

### Version 0.61.1

- **Fixed: "Today" suggested unrealistic purchases.** Page-by-page scans often see only part of the
  auction house, which looked like huge sales. Sales per day are now only estimated between
  **complete** scans, count only half of each drop (the rest expired or was cancelled) and never
  more than half of what is usually listed. "Price change since scan" also compares complete scans only.
- **Capital protection:** each suggestion in "Today" uses at most 20 % of your gold, all of them
  together at most half; the window shows the capital needed. The self-test checks this.
- **Overview:** rises to several times the market value and drops from a former moon price are no
  longer listed.
- **Mailbox:** the addon's buttons now sit in a tidy panel **next to** the mailbox instead of over
  its frame. "Collect all" is only shown when WoW has no "Open all" button of its own (and in
  test mode for the test mail), "Stop" only while collecting.
- **One money field instead of three:** type "5s", "1g 20s", "4s 85c" or "1.5" (= 1g 50s); a plain
  number shows what it means ("= 5g"). No more silver ending up in the gold field.
- Smaller things: "Bid" without a selected listing says so, the vendor warning when posting only
  appears when it matters (at least 1 silver and 10 %), fictional auctions show up in test mode
  right away, the "Today" window closes when you jump to a tab.

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
