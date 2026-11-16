## What's new since 0.65.178 (all versions up to this one)
> ⚠️ **This is a beta version.** Please report errors in the comments on CurseForge,
> ideally with the Lua error message and the WoW version you play on.

- **Posting works again:** when the price guard warns, "Post anyway" now posts directly in your click, and if WoW still blocks it, the next click on "Post" posts. "Adjust price" suggests the smallest price that does not warn again (no more endless warning).
- **Sniper "Buy" button:** one click = one purchase. The button says what it buys ("Buy: 1× … for 8s 50c"); commodities take two clicks (ask price, confirm). "Sniper buys with: Mouse wheel / Own key / Button only" – with "Button only" the wheel never buys.
- **Shopping list from a recipe works again:** "Materials as shopping list" and "Only what I'm missing" always create the list (and say why if they cannot); with ProfessionSentinel use `/ahs material` or `/ahs missing` with a recipe selected.
- **Sniper you can trust:** a listing is never bought twice, only purchases confirmed by the server count, the budget also holds against your real gold, all targets are searched in turn, and it no longer gets stuck after a full scan or a server error.
- **Sniper quiet mode (on by default):** while you snipe, only the sniper works – background work waits, so sniping is smoother.
- **Sniper limits:** targets created with "+" never get more budget than your per-item limit; a fixed max above "Worth up to" is shown in yellow, with a button to let the max follow "Worth up to".
- **Market tab:** "Today" (your own things first, then the best chances – each row with a button for the next step), "My stock" (everything you own with its value after fees and the best way) and "Disenchant"; the header says the market direction per level in plain words.
- **Options reorganized:** areas on the left, one column on the right, a search box for every option.
- **Gold safety:** every buy limit keeps your minimum return (default 20 %), also for flipping; there is no "Worth up to" without profit.
- **Choose your ways and your risk:** turn disenchanting, crafting, flipping and vendor flipping on or off; risk careful / normal / bold.
- **Exact bargains:** below vendor price and below disenchant value show real quantities and total profit; "+" creates a safe sniper target; empty lists say why.
- **Honest selling:** the Sell tab says when disenchanting pays more or when selling now means a loss; "Adjust price" takes a price that does not warn again; the duration can follow your play rhythm.
- **My auctions and breaks:** cancel advice no longer costs a deposit for nothing; "Since your last visit" shows what sold and came back, "Before you go" the 3 most important steps.
- **Better numbers:** sales per day measured from your full scans (shared market data of GoldSentinel players can be turned off), disenchant tooltip with your own results, fair disenchant cost in the ledger.
- **Smoother:** no freezes after a full scan, a lot less memory use.
- **Known issue:** a hit can disappear from the button before you click it; the mouse wheel is not affected – fix in the next version.
- **Bekanntes Problem (Deutsch):** Ein Treffer kann vom Knopf verschwinden, bevor du ihn anklickst; das Mausrad ist nicht betroffen – Korrektur in der nächsten Version.
