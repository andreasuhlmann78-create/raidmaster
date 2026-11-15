"""Beute-Posts (D-3 Schritt 27, ab Bot 1.5.174): Items wie im Spiel (Embed mit Qualitätsfarbe, Tooltip,
Spielsymbol), Lootliste nach jedem Raid im Loot-Kanal, Tooltip-Knopf (show_tip).

UNVERÄNDERT aus bot.py verschoben: der Abschnitt "Items wie im Spiel" (item_embed, remember_tip, loot_line,
send_loot_list, show_tip, post_new_loot; 117 Zeilen). Symbole/Emojis: symbole_bot, Testnachrichten:
testdaten_bot. bot.py importiert dieses Modul nach "grund.bot = bot" und übernimmt send_loot_list, show_tip und
post_new_loot. Weg A (Antwort der Prüf-Sitzung 15.11. 20:48).
"""
from __future__ import annotations

import time

import discord

import grund
import raidmaster_data as rmd
import render as rimg
from bot_hilfen import player_class
from grund import channel_by_id, raid_channel
from kern import cfg, log, state
from symbole_bot import WOWHEAD_FLAVOR, class_emoji, item_emoji, item_icon, wowhead_tip
from testdaten_bot import send_test

bot = grund.bot
assert bot is not None, "beutepost_bot erst nach grund.bot = bot importieren"


# ---------------------------------------------------------------------------
# Items wie im Spiel: Embed mit Qualitätsfarbe, Tooltip und echtem Spielsymbol
# ---------------------------------------------------------------------------


async def item_embed(e: dict, db: dict | None, test: bool = False, tip: dict | None = None) -> discord.Embed:
    """Ein vergebenes Item als Embed wie der Tooltip im Spiel."""
    tip = tip or rmd.item_tip(db, e.get("link"))
    if not tip or not tip.get("l"):
        # kein Tooltip vom Addon (ältere Version oder Item noch nicht gelesen): bei Wowhead nachschlagen
        wh = await wowhead_tip(e.get("link"))
        if wh:
            tip = {**wh, "l": [tuple(x) for x in wh.get("l") or []], "q": (tip or {}).get("q") or wh.get("q")}
    name = (tip or {}).get("n") or e["item"]
    emb = discord.Embed(title=name, url=rmd.wowhead_url(e.get("link"), WOWHEAD_FLAVOR),
                        color=rmd.item_color(e.get("link"), tip))
    desc = f"🎁 **{e['name']}** · **{e['amount']} DKP** · <t:{int(e['t'])}:t>"
    block = rmd.tooltip_block(tip)
    emb.description = desc + ("\n" + block if block else "")
    icon = await item_icon(e.get("link"), tip)
    if icon:
        emb.set_thumbnail(url=icon)
    cls = (((db or {}).get("data") or {}).get("players") or {}).get(e["name"], {})
    cls = cls.get("c") if isinstance(cls, dict) else None
    emb.set_author(name=f"{e['name']}" + (f" · {rimg.CLASS_NAMES.get(str(cls).upper(), '')}" if cls else ""),
                   icon_url=rimg.class_icon_url(cls))
    emb.set_footer(text=(("TEST · " if test else "") + e.get("pool_name", "")))
    return emb


def remember_tip(link: str | None, tip: dict | None, db: dict | None):
    """Tooltip für das Menü "Tooltip anzeigen" merken (auch Testdaten, die sonst nicht gespeichert sind)."""
    iid = rmd.item_id(link)
    if not iid:
        return
    store = state.data.setdefault("tip_cache", {})
    store[str(iid)] = {"link": link, "tip": tip, "t": int(time.time())}
    if len(store) > 400:
        for k, _ in sorted(store.items(), key=lambda kv: kv[1].get("t", 0))[:len(store) - 400]:
            store.pop(k, None)


async def loot_line(e: dict, db: dict | None) -> str:
    tip = rmd.item_tip(db, e.get("link"))
    remember_tip(e.get("link"), tip, db)
    emoji = await item_emoji(e.get("link"), tip)
    item = (tip or {}).get("n") or e["item"]
    item_txt = f"**{item}**"     # nur Symbol und Name – kein Link, kein Tooltip
    dot = await class_emoji(player_class(db, e["name"]))
    return f"{emoji} <t:{int(e['t'])}:t> {dot}**{e['name']}** erhält {item_txt} für {e['amount']} DKP"


async def send_loot_list(channel, items: list[dict], db: dict | None, header: str | None = None, test: bool = False) -> int:
    """Loot als kompakte Liste: Item-Symbol vorne, Uhrzeit, Gewinner, Item (Link zu Wowhead), DKP.
    Darunter ein Menü, das den Tooltip wie im Spiel zeigt (nur für den, der auswählt)."""
    lines = [await loot_line(e, db) for e in items]
    state.save()
    text = ((header + "\n") if header else "") + "\n".join(lines)
    parts = rmd.split_discord(text)
    view = None     # kein Tooltip-Menü mehr unter der Loot-Liste
    sent = 0
    for i, part in enumerate(parts):
        v = view if i == len(parts) - 1 else None
        if test:
            await send_test(channel, part, view=v)
        else:
            await channel.send(content=part, view=v) if v else await channel.send(part)
        sent += 1
    return sent


async def show_tip(inter: discord.Interaction):
    """Antwort auf das Menü "Tooltip anzeigen": Tooltip-Karte nur für den Klickenden.
    Sofort bestätigen (Discord wartet nur 3 Sekunden), dann die Karte nachreichen."""
    values = (inter.data or {}).get("values") or []
    if not values:
        return
    try:
        await inter.response.defer(ephemeral=True, thinking=True)
    except discord.HTTPException:
        pass
    iid, name, amount, t, cls = (values[0].split("|") + ["", "", "0", "0", ""])[:5]
    cached = (state.data.get("tip_cache") or {}).get(str(iid)) or {}
    link = cached.get("link") or f"|Hitem:{iid}|h[Item {iid}]|h"
    e = {"name": name, "amount": amount, "t": int(t or 0), "item": rmd.item_name(link), "link": link, "pool_name": ""}
    emb = await item_embed(e, {"data": {"players": {name: {"c": cls}}}} if cls else None, tip=cached.get("tip"))
    await inter.followup.send(embed=emb, ephemeral=True)


async def post_new_loot():
    entries = rmd.loot_entries(bot.dkp_data)
    if not entries:
        return
    last = state.data.get("last_loot")
    newest = [entries[-1]["t"], str(entries[-1]["id"])]
    if last is None:
        # Beim ersten Start nichts Altes posten
        state.data["last_loot"] = newest
        state.save()
        return
    fresh = [e for e in entries if (e["t"], str(e["id"])) > (last[0], last[1])]
    state.data["last_loot"] = newest
    state.save()
    by_pool: dict[str, list] = {}
    for e in fresh:
        by_pool.setdefault(e["pool"], []).append(e)
    for pool, items in by_pool.items():
        channel = await channel_by_id(raid_channel(pool, "loot") or cfg.get("loot_channel_id"))
        if not channel:
            continue
        try:
            await send_loot_list(channel, items, bot.dkp_db)
        except discord.HTTPException as ex:
            log.warning("Loot-Liste mit Symbolen nicht möglich (%s) – als Text.", ex)
            lines = [f"🎁 **{e['name']}** erhält **{e['item']}** für {e['amount']} DKP ({e['pool_name']})" for e in items]
            for text in rmd.split_discord("\n".join(lines)):
                await channel.send(text)
