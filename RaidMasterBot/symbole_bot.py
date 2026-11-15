"""Symbole und Wowhead (D-3 Schritt 7, ab Bot 1.5.152): Item-Symbole, Item-Emojis, Klassen-Punkte, Wowhead-Tooltip.

UNVERÄNDERT aus bot.py verschoben: WOWHEAD_FLAVOR, item_icon, item_icon_name, wowhead_tip, QUALITY_SQUARES,
_emoji_lock, item_emoji, class_emoji. Gebraucht von DKP, Beute, Bank, Handwerk und Ruhmeshalle – darum als eigener
Bereich VOR der Ruhmeshalle (sonst müsste die Ruhmeshalle class_emoji aus bot.py holen).
bot.py importiert dieses Modul erst NACH "grund.bot = bot" und übernimmt die Namen.
Weg A (Antwort der Prüf-Sitzung 15.11. 20:48).
"""
from __future__ import annotations

import asyncio
import re

import grund
import raidmaster_data as rmd
import render as rimg
from kern import log, state

bot = grund.bot
assert bot is not None, "symbole_bot erst nach grund.bot = bot importieren"


WOWHEAD_FLAVOR = "classic"


async def item_icon(link: str | None, tip: dict | None) -> str | None:
    """URL des Item-Symbols."""
    return rmd.icon_url(await item_icon_name(link, tip))


async def item_icon_name(link: str | None, tip: dict | None) -> str | None:
    """Name des Item-Symbols (z. B. inv_boots_05). Pfad vom Addon -> Name direkt, sonst einmal bei
    Wowhead nachschlagen (Ergebnis wird gemerkt)."""
    name = rmd.icon_name_from_hint(tip.get("ic") if tip else None)
    if name:
        return name
    iid = rmd.item_id(link)
    if not iid:
        return None
    cache = state.data.setdefault("item_icons", {})
    if str(iid) in cache:
        return cache[str(iid)]
    found = None
    try:
        import aiohttp
        timeout = aiohttp.ClientTimeout(total=8)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            for flavor in (WOWHEAD_FLAVOR, "tbc", "wotlk"):
                async with session.get(f"https://nether.wowhead.com/{flavor}/tooltip/item/{iid}") as resp:
                    if resp.status == 200:
                        js = await resp.json(content_type=None)
                        if isinstance(js, dict) and js.get("icon"):
                            found = str(js["icon"]).lower()
                            break
    except Exception as e:  # noqa: BLE001
        log.info("Item-Symbol %s nicht gefunden: %s", iid, e)
        return None
    cache[str(iid)] = found
    state.save()
    return found


async def wowhead_tip(link: str | None) -> dict | None:
    """Tooltip von Wowhead (deutsch, sonst englisch), falls das Addon keinen geliefert hat. Wird gemerkt."""
    iid = rmd.item_id(link)
    if not iid:
        return None
    cache = state.data.setdefault("wh_tips", {})
    if str(iid) in cache:
        return cache[str(iid)]
    found = None
    try:
        import aiohttp
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=6)) as session:
            for url in (f"https://nether.wowhead.com/{WOWHEAD_FLAVOR}/de/tooltip/item/{iid}",
                        f"https://nether.wowhead.com/{WOWHEAD_FLAVOR}/tooltip/item/{iid}"):
                async with session.get(url) as resp:
                    if resp.status != 200:
                        continue
                    js = await resp.json(content_type=None)
                if isinstance(js, dict) and js.get("tooltip"):
                    found = rmd.tip_from_wowhead_html(js["tooltip"], js.get("name"), js.get("quality"), js.get("icon"))
                    break
    except Exception as ex:  # noqa: BLE001
        log.info("Wowhead-Tooltip %s nicht geladen: %s", iid, ex)
        return None
    if found:
        found["l"] = [list(x) for x in found["l"]]
    cache[str(iid)] = found
    if len(cache) > 500:
        for k in list(cache)[:len(cache) - 500]:
            cache.pop(k, None)
    state.save()
    return found


QUALITY_SQUARES = {0: "⬜", 1: "⬜", 2: "🟩", 3: "🟦", 4: "🟪", 5: "🟧"}
_emoji_lock = asyncio.Lock()


async def item_emoji(link: str | None, tip: dict | None) -> str:
    """Item-Symbol als Emoji für den Zeilenanfang (eigenes App-Emoji aus dem Spielsymbol).
    Geht das nicht, ein Quadrat in der Qualitätsfarbe."""
    q = (tip or {}).get("q")
    if not isinstance(q, int):
        q = {0xA335EE: 4, 0x0070DD: 3, 0x1EFF00: 2, 0xFF8000: 5}.get(rmd.item_color(link), 4)
    fallback = QUALITY_SQUARES.get(q, "🟪")
    try:
        name = await item_icon_name(link, tip)
    except Exception:  # noqa: BLE001
        name = None
    if not name:
        return fallback
    cache = state.data.setdefault("item_emojis", {})
    if name in cache:
        return cache[name] or fallback
    ename = re.sub(r"[^A-Za-z0-9_]", "_", name)[:32]
    if len(ename) < 2:
        return fallback
    async with _emoji_lock:
        if name in cache:
            return cache[name] or fallback
        try:
            existing = state.data.get("_app_emojis_loaded")
            if not existing and hasattr(bot, "fetch_application_emojis"):
                for em in await bot.fetch_application_emojis():
                    cache.setdefault(em.name, f"<:{em.name}:{em.id}>")
                state.data["_app_emojis_loaded"] = True
                if ename in cache:
                    cache[name] = cache[ename]
                    state.save()
                    return cache[name]
            import aiohttp
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=8)) as session:
                async with session.get(f"https://wow.zamimg.com/images/wow/icons/medium/{name}.jpg") as resp:
                    img = await resp.read() if resp.status == 200 else None
            if not img or not hasattr(bot, "create_application_emoji"):
                cache[name] = None
                state.save()
                return fallback
            em = await bot.create_application_emoji(name=ename, image=img)
            cache[name] = f"<:{em.name}:{em.id}>"
        except Exception as e:  # noqa: BLE001
            log.info("Item-Emoji %s nicht möglich: %s", name, e)
            cache[name] = None
        state.save()
        return cache[name] or fallback


async def class_emoji(cls: str | None) -> str:
    """Punkt in der genauen Klassenfarbe vor dem Namen (eigenes App-Emoji, sonst ähnliches Unicode-Emoji)."""
    c = str(cls or "").upper()
    if c not in rimg.CLASS_COLORS:
        return ""
    fallback = rimg.CLASS_FALLBACK_EMOJI.get(c, "")
    cache = state.data.setdefault("class_emojis", {})
    if c in cache:
        return cache[c] or fallback
    async with _emoji_lock:
        if c in cache:
            return cache[c] or fallback
        ename = f"rm_{c.lower()}"
        try:
            if hasattr(bot, "fetch_application_emojis"):
                for em in await bot.fetch_application_emojis():
                    if em.name == ename:
                        cache[c] = f"<:{em.name}:{em.id}>"
                        state.save()
                        return cache[c]
            png = rimg.class_dot_png(c)
            if png and hasattr(bot, "create_application_emoji"):
                em = await bot.create_application_emoji(name=ename, image=png)
                cache[c] = f"<:{em.name}:{em.id}>"
            else:
                cache[c] = None
        except Exception as e:  # noqa: BLE001
            log.info("Klassen-Emoji %s nicht möglich: %s", c, e)
            cache[c] = None
        state.save()
        return cache[c] or fallback
