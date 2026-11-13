# AHSentinel

**Market analysis, sniper and gold-making toolkit for the auction house – for every WoW version.**

> ⚠️ **This addon is in beta.** It may still contain bugs. If you run into an error or unexpected behaviour in-game, please report it in the comments – ideally with the Lua error message (if any) and the WoW version you play on.

> 🔁 **Formerly "AH Analyzer Pro".** Since version 0.62.0 the addon is called **AHSentinel**. Your saved data is taken over automatically on the first login. The zip now contains only the folder `AHSentinel` – if the old folder `AHAnalyzerPro` is still in your AddOns, AHSentinel tells you once in the chat: just delete it. The new command is `/ahs` (`/ahp` still works).

AHSentinel scans the auction house, keeps a price history for every item and turns it into market values, trends and charts. It finds bargains for you, helps you sell at the right price and keeps a ledger of everything you earn and spend. It opens in its own resizable window with just five tabs – **Overview, Buy, Sell, Market, Ledger** – can be used completely with the mouse and speaks the language of your WoW client.

---

## What's new

### Version 0.65.118

- **New test part `/ahs testroutine tempo`:** measures the speed targets in the game – tooltip calculation, switching
  tabs, sniper reaction, buy per key press, longest frame with the auction house open, login/reload and memory of the
  full scan – and writes them into the test report (field "tempo"), with the slow spot if a target is missed.
- Full scan: the diagnostic log now says whether slow reading portions come from garbage collection.
- Tests T625–T632.

### Version 0.65.117

- **Sniper budget doubled after reset:** "Reset counter" now always sets the budget back to the amount you entered
  (a refill no longer stays in).
- **One "best way" for all numbers:** profit line, "… pays more" and "Max above sale value – every purchase loses about …"
  now all come from the same calculation (sell, disenchant, vendor after fees) – no more contradicting numbers.
- The calculation line "With … budget the sniper buys at most …" is gone from the target tooltip.
- **Sniper and scrolling:** the sniper measures whether the server answers searches without a key press. If not, the
  sniper shows "Scroll to search and buy · last search 12 s ago" and reminds you quietly after 10 s without scrolling.
- Test report: composition of the sync queue per prefix.
- Tests T621–T624.

### Version 0.65.116

- **"Worth up to" for disenchanting was too low:** the material price correction (e.g. ×0.57) was counted twice – once
  in the value and again in the learned safety margin (both measured the same shortfall of your own disenchants). The
  learned margin now only covers what the correction does not already explain. "Worth up to" (sniper max for
  disenchant targets, buy limits) is again value ÷ (1 + minimum profit), e.g. 10s -> 8s 33c instead of 5s 90c.
- Test T620.

### Version 0.65.115

- **Sniper acceptance test in the game:** `/ahs testroutine sniper` (auction house open). First it asks in its own
  window whether ONE real test purchase of 1 piece up to 5c is allowed – it only buys with your own mouse wheel notch or
  key; "No" skips it. Then, with buying locked, it watches the sniper for 2 minutes: hits stay visible (S1), counter and
  budget only count confirmed purchases (S2), pause is visible and "resume" works (S3), frame rate / longest frame /
  sync queue (S5) and reaction time (S6). The result goes into the test report like the other parts.
- Tests T613–T619.

### Version 0.65.114

- **Sniper never loses a real purchase:** if the server sends no answer, the sniper checks your gold after 30 s (gold
  down by the price -> counted). A confirmation that arrives late is still counted (up to 5 min). On the modern auction
  house an error message without a listing (e.g. from a search) no longer marks the purchase as failed.
- **Live tooltip (new):** hovering an offer (sniper list, buy list, bargains, classic auction house row) shows ONE line
  "Profit: −44c / each" (red) or "Profit: +2s 61c / each" (green) – with the price of exactly this offer and the best
  way after fees (sell, disenchant, vendor). It replaces "Disenchant worth it …" and "Worth up to …"; everything else
  stays. Bag tooltips use the market value. "Material prices corrected ×…" now only with Shift.
- **Buy list:** with a quality filter, items whose data loaded later now appear without a new search.
- **Test routine:** sync messages that arrive during the run are applied afterwards (no sandbox error, nothing lost).
- **Flip list:** list and detail always calculate with the same state (no "FLIP-WIDERSPRUCH").
- Diagnostics: "LANGSAM" names the longest single step (file:line); full-scan test waits up to 300 s.
- Tests T602–T612, T597 checks the uploaded fields.

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
