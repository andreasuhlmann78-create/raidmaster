"""Regeln (D-3 Schritt 11, ab Bot 1.5.156): Gilden-Regeln aus guild_rules.json in den Regel-Kanälen (mit
klickbaren Kanal-Links) und die DKP- und Raid-Regeln in #regeln – bearbeitet statt neu gepostet, nur bei Änderung.

UNVERÄNDERT aus bot.py verschoben: channel_links, ensure_guild_rules, ensure_dkp_rules. Der Bestand der
Gildenbank (unter ihren Regeln) kommt aus bank_bot.py. bot.py importiert dieses Modul nach "grund.bot = bot" und
übernimmt die Namen. Weg A (Antwort der Prüf-Sitzung 15.11. 20:48).
"""
from __future__ import annotations

import asyncio
import re
import zlib

import discord

import grund
import guildbank
import raidmaster_data as rmd
import server_setup
from bank_bot import BANK_CHANNEL, post_guild_bank
from grund import bot_guild, channel_by_id
from kern import cfg, log, lootdb, save_config, state

bot = grund.bot
assert bot is not None, "regeln_bot erst nach grund.bot = bot importieren"


def channel_links(text: str) -> str:
    """{#kanal} in Regeltexten (guild_rules.json) als klickbaren Link; umbenannte Kanäle über CHANNEL_ALIASES.
    Fehlt der Kanal, bleibt **#kanal** als fetter Text stehen."""
    guild = bot_guild()

    def chan(m_):
        name = m_.group(1).strip().lstrip("#").lower()
        c = server_setup.find_channel(guild.text_channels, name) if guild else None
        return c.mention if c else "**#" + name + "**"

    return re.sub(r"\{#([^{}]+)\}", chan, text)


async def ensure_guild_rules() -> list[str]:
    """Kategorie 📜 REGELN (Zusammenleben in der Gilde) anlegen und die Regeltexte posten.
    Ändert sich ein Text in guild_rules.json, ersetzt der Bot seine Beiträge im Kanal."""
    guild = bot_guild()
    if guild is None or not guild.me.guild_permissions.manage_channels:
        return []
    report = await server_setup.ensure_rules_category(guild, cfg)
    save_config()
    hashes = state.data.setdefault("rules_hash", {})
    msgs = state.data.setdefault("rules_messages", {})
    bank_reset = False
    for rule in server_setup.guild_rules():
        key = rule["key"]
        ch = await channel_by_id((cfg.get("rules_channels") or {}).get(key))
        if not ch:
            continue
        examples = server_setup.material_examples(rmd.raid_materials(lootdb.data))
        posts = [channel_links(p.replace("{material_beispiele}", examples)) for p in rule.get("posts") or [] if p.strip()]
        if not posts:
            continue
        digest = str(zlib.crc32("\n".join(posts).encode("utf-8")))
        if hashes.get(key) == digest and msgs.get(key):
            continue
        old = list(msgs.get(key) or [])
        new_ids = []
        for i, text in enumerate(posts):
            text = text[:2000]
            done = False
            if i < len(old):
                try:
                    await ch.get_partial_message(old[i]).edit(content=text)
                    new_ids.append(old[i])
                    done = True
                except discord.HTTPException:
                    pass
            if not done:
                m = await ch.send(text)
                new_ids.append(m.id)
            await asyncio.sleep(0.4)
        for mid in old[len(posts):]:
            try:
                await ch.get_partial_message(mid).delete()
            except discord.HTTPException:
                pass
        msgs[key] = new_ids
        hashes[key] = digest
        report.append(f"📜 #{key}: Regeln {'aktualisiert' if old else 'gepostet'}")
        if key == BANK_CHANNEL:
            # #gildenbank: Regeln oben, Bestand darunter – nach neuen Regeln den Bestand löschen und neu posten
            # (dort, wo er gerade steht – vor 1.5.96 war das #gildenbank-bestand)
            holder_id = state.data.get("bank_channel") or cfg.get("bank_channel_id")
            holder = await channel_by_id(holder_id) if holder_id else None
            await guildbank.reset_bank(holder or ch, state.data)
            bank_reset = True
        state.save()
    if bank_reset:
        try:
            await post_guild_bank()
        except Exception:  # noqa: BLE001
            log.exception("Gildenbank-Bestand konnte nach den Regeln nicht neu gepostet werden")
    return report


async def ensure_dkp_rules() -> list[str]:
    """#regeln: DKP-Regeln und Raid-Regeln. Ändert sich ein Text (oder ein DKP-Wert im Addon), bearbeitet der Bot
    seine Beiträge; seine früheren Regel-Beiträge im Kanal werden übernommen statt doppelt gepostet."""
    guild = bot_guild()
    ch = server_setup.find_channel(guild.text_channels, "regeln") if guild else None
    if ch is None:
        return []
    settings = (bot.dkp_data or {}).get("settings") if isinstance((bot.dkp_data or {}).get("settings"), dict) else None
    mats = rmd.raid_materials(lootdb.data)
    posts = [p[:2000] for p in server_setup.rules_posts(settings, mats, rmd.material_recipes(bot.dkp_db, mats))]
    digest = str(zlib.crc32("\n".join(posts).encode("utf-8")))
    rec = state.data.get("dkp_rules") or {}
    if rec.get("hash") == digest and rec.get("ch") == ch.id and rec.get("ids"):
        return []
    ids = list(rec.get("ids") or []) if rec.get("ch") == ch.id else []
    if not ids:
        # früher gepostete Regeln (z. B. von /raidmaster-einrichten) übernehmen
        try:
            async for m in ch.history(limit=100, oldest_first=True):
                if m.author.id == bot.user.id and (m.content or "").startswith(("**DKP-Regeln**", "**Raid-Regeln", "💎 **So funktionieren unsere DKP", "⚔️ **So raiden wir", "🎁 **Beute und Ersatzbank")):
                    ids.append(m.id)
        except discord.HTTPException:
            pass
    new_ids = []
    for i, text in enumerate(posts):
        done = False
        if i < len(ids):
            try:
                await ch.get_partial_message(ids[i]).edit(content=text)
                new_ids.append(ids[i])
                done = True
            except discord.HTTPException:
                pass
        if not done:
            m = await ch.send(text)
            new_ids.append(m.id)
        await asyncio.sleep(0.4)
    for mid in ids[len(posts):]:
        try:
            await ch.get_partial_message(mid).delete()
        except discord.HTTPException:
            pass
    state.data["dkp_rules"] = {"ch": ch.id, "ids": new_ids, "hash": digest}
    state.save()
    return [f"#regeln: DKP- und Raid-Regeln {'aktualisiert' if ids else 'gepostet'}"]
