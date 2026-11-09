# AHSentinel

**Market analysis, sniper and gold-making toolkit for the auction house – for every WoW version.**

> ⚠️ **This addon is in beta.** It may still contain bugs. If you run into an error or unexpected behaviour in-game, please report it in the comments – ideally with the Lua error message (if any) and the WoW version you play on.

> 🔁 **Formerly "AH Analyzer Pro".** Since version 0.62.0 the addon is called **AHSentinel**. Your saved data is taken over automatically on the first login. The zip now contains only the folder `AHSentinel` – if the old folder `AHAnalyzerPro` is still in your AddOns, AHSentinel tells you once in the chat: just delete it. The new command is `/ahs` (`/ahp` still works).

AHSentinel scans the auction house, keeps a price history for every item and turns it into market values, trends and charts. It finds bargains for you, helps you sell at the right price and keeps a ledger of everything you earn and spend. It opens in its own resizable window with just five tabs – **Overview, Buy, Sell, Market, Ledger** – can be used completely with the mouse and speaks the language of your WoW client.

---

## What's new

### Version 0.65.30

- **Prices per realm and faction:** AHSentinel now keeps a separate price list for every realm and auction house –
  Horde, Alliance and the neutral auction houses (Booty Bay, Gadgetzan, Everlook). Your own scans and synced prices only
  go into the list of the auction house you are at; tooltips and calculations use your faction's list (at a neutral
  auction house the neutral one).
- **Sync only from the same auction house:** price messages now carry a short code of realm and faction; prices from
  another faction or realm, and old messages without the code, are dropped. (Please update – older versions no longer
  exchange prices with 0.65.30.)
- Your existing prices are kept for the current character's realm and faction. If you have characters on several
  realms or factions, a note tells you that the old prices may be mixed – the next scan replaces them.

### Version 0.65.29

- **Disenchant value instead of "profit":** the tooltip line is now called "Disenchant value ~X (T)" – it depends only
  on the group (quality, item level, armor/weapon) and is the same for all items of that group. New below it:
  "Profit when buying: value − purchase price" (green/red) with the price of the row you point at in the addon
  (buy list, sniper, bargains), at a vendor his price, otherwise the cheapest current offer. In the buy list a mark
  "[disenchanting pays]" appears only if value − price is positive.
- **Material block matches the value:** block and value now use the same price per material – your own sales of the
  last 14 days, otherwise just below the cheapest current offer (at most the median), otherwise the median. The source
  is shown ("AH now" / "market" / "own sales"). Offers below 10 % or above 300 % of the median don't count ("offer
  doubtful") – e.g. 22c for a Greater Mystic Essence.
- **Sharing disenchants:** after 10 new ones, or at the latest 2 minutes after the last one, and on logout.

### Version 0.65.28

- **Opens with the auction house:** the AHSentinel window opens when you open the auction house and closes again
  with it. If it was already open before, it stays open. Option "Open and close with the auction house" (on by
  default). Never pops up in combat.
- **Window always on screen:** the main window stays fully on screen – at most 90 % of the screen, position kept
  inside the edges, also after changing UI scale or resolution.
- **Sniper in WoW Forever:** commodities are bought with two notches – 1st notch reserves the price, 2nd notch buys
  (WoW Forever allows the reservation only from a key press). The status line now says so ("1. … reserve price ·
  2. … buy", then "reserved – again to buy (10 s)"), also while the sniper keeps searching; help and tooltips
  updated. The total line under the list no longer disappears while searching. Era/TBC unchanged.
- Playtest: new check S9 (window opens and closes with the auction house).
- Developer test routine: checks that can't run in this client (no BugSack, missing item data, no real layout) are
  counted as skipped, never as OK or ERROR.

### Version 0.65.27

- **Disenchant table corrected** (source: warcraft.wiki.gg, Classic disenchanting tables): green items up to item
  level 15 give no shard – armor 80 % dust / 20 % essence, weapons 20 % / 80 %. Item level 21–25 now 75/15/10
  (weapons 15/75/10), item level 51–65 weapons 22/75/3; the other levels stay 75/20/5.
- Materials that cannot come from a group (e.g. a shard from item level 15) are no longer counted – neither your own
  (wrongly detected) results nor shared ones.

### Version 0.65.26

- **Disenchant in the tooltip, shorter:**
  - One line "Disenchant: expected gain ~X" (value after fees) with a small comparison ("better than selling" /
    "selling pays more") and the source: "(Ø 12)" = from 12 real disenchants (from 10 on), "(T)" = table.
  - Below it a block "Disenchant – materials (AHSentinel)": icon, name, drop chance and value per piece (AH price from
    the last scan, otherwise market value).
  - Hold Shift to see the whole calculation (actual and estimated, per material, after fees).
  - Option "Disenchant details in tooltip": short / with materials (default) / everything.
- **Disenchant results shared with all AHSentinel users:** every disenchant on every character is counted
  automatically (your alts count as your own) and shared over the public sync channel ("guild only" stays an option).
  Protection: at most 6 messages per sender and minute, materials must match the group, 1–5 pieces per disenchant,
  no jumps, duplicate messages count once. Senders are stored only as a short code, never by name.

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
