# AH Analyzer Pro

**Market analysis, sniper and gold-making toolkit for the auction house – for every WoW version.**

> ⚠️ **This addon is in beta.** It may still contain bugs. If you run into an error or unexpected behaviour in-game, please report it in the comments – ideally with the Lua error message (if any) and the WoW version you play on.

AH Analyzer Pro scans the auction house, keeps a price history for every item and turns it into market values, trends and charts. It finds bargains for you, helps you sell at the right price and keeps a ledger of everything you earn and spend. It opens in its own resizable window with just five tabs – **Overview, Buy, Sell, Market, Ledger** – can be used completely with the mouse and speaks the language of your WoW client.

---

## What's new

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

### Version 0.61.0

**More profit, fewer fake bargains:**

- **"Today" (button in the overview, `/ahp today`):** the actions that bring the most gold right
  now, ranked by estimated net gold - buy below vendor price, flips, selling what is in your bags,
  undercut auctions, items to repost, disenchant and bid deals. Click a row to jump straight to
  the right tab.
- **Sell-through instead of listing prices:** from your scans the addon now estimates how much of
  an item actually sells per day and whether its market value can be trusted. Items that are
  rarely listed or only have "moon prices" (like 2499g 99s 99c) are hidden from bargains, flips and
  the overview (button "also unsure" shows them). Bargains are sorted by **profit per day**, the
  tooltip shows "~N/day sold (estimated)".
- **Net profit with the posting fee:** on the classic auction house the fee is now estimated from
  the vendor price ("approx.") and learned exactly the first time you really post. Profits subtract
  the fee you lose when an auction comes back (based on your own sell rate).

### Version 0.60.11

- **Mailbox buttons always answer:** "Mail collected: ..." now also appears in the middle of the
  screen, and an empty mailbox says "Nothing to collect" instead of staying silent.
- **"To alts" without a rule** says so in the chat before opening the rules window.
- **Test mode:** the fictional "sold" mail belongs to the fictional sold auction, and that auction
  disappears from "My auctions" once its money is collected - like in the game.

### Version 0.60.10

- **Test mode with fictional auctions:** "My auctions" now shows three fictional auctions (one
  undercut, one cheapest, one sold) plus everything you post in test mode - so cancelling and the
  undercut check can be tried without a real auction. The self-test uses a fictional auction for
  "cancel" when you have none.
- **Test mailbox:** in test mode the mailbox buttons of the addon work with fictional mail (sold,
  won, expired, cancelled, outbid, a normal letter): auto-collect, "All", ledger invoices and the
  repost list can all be tried - your real mail stays untouched.
- **Buy tab:** the bid field and the selected listing are reset when you switch to another item
  (no more old bid in the field). The header shows the cheapest listing and the market value
  (median 14 days) separately, and says when more listings are still loading.
- **Sniper:** listings of the previous target are no longer shown under the new target's name.
- **Self-test:** the sniper test buys (simulated) the smallest stack instead of a 2-stack.
- **Price history window:** can be dragged by its title.

### Version 0.60.9

- **Message when the scan is done:** a large message in the middle of the screen ("AH scan done:
  N items") plus a sound (if alert sounds are on in the options) - you no longer have to watch the
  chat. A scan without results is shown there too.

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
