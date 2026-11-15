"""Grundfunktionen, die fast alle Bereiche des Bots brauchen (D-3 Schritt 3, ab Bot 1.5.148).

UNVERÄNDERT aus bot.py: Rechte (is_guild_leader, is_admin, is_creator), Kanal holen (channel_by_id), Server
(bot_guild), Meldung in den Bot-Kanal (post_bot_log); ab 1.5.157 raid_channel (Kanal-ID eines Raid-Pools),
ab 1.5.159 is_chef.
Das Bot-Objekt selbst entsteht in bot.py; bot.py trägt es gleich danach hier ein ("grund.bot = bot"), bevor
irgendein Ereignis oder Befehl laufen kann. Die Funktionen lesen "bot" erst beim Aufruf.
Weg A "kern.py + Module" (Antwort der Prüf-Sitzung 15.11. 20:48).
"""
from __future__ import annotations

import discord

from kern import book, cfg, log

bot: discord.Client | None = None      # wird von bot.py gesetzt (grund.bot = bot)
NO_PING = discord.AllowedMentions(roles=False, users=False, everyone=False)   # D-3 Schritt 4: aus bot.py


# Wer im Discord etwas verändern darf: nur der Gildenchef (config "guild_leader", Charaktername aus config.json)
# und die Rolle Offizier. Der Server-Besitzer bleibt als Notfall-Zugang erlaubt, damit sich niemand aussperrt.
def is_guild_leader(member) -> bool:
    if not isinstance(member, discord.Member):
        return False
    leader = (cfg.get("guild_leader") or "").strip().lower()
    if not leader:
        return False
    uid = book.user_for_char(cfg.get("guild_leader"))
    if uid and int(uid) == member.id:
        return True
    for cand in (getattr(member, "nick", None), getattr(member, "global_name", None), member.name):
        c = str(cand or "").strip().lower()
        if c and (c == leader or c.startswith(leader + " ")):
            return True
    return False

def is_admin(member) -> bool:
    if not isinstance(member, discord.Member):
        return False
    if member.guild and member.id == member.guild.owner_id:
        return True
    if is_guild_leader(member):
        return True
    return any(role.name.lower() == "offizier" for role in member.roles)

def is_creator(member) -> bool:
    """Raids, Einteilung, Beute-Daten usw. verwalten – seit 1.5.64 wie alles andere nur Gildenchef und Offiziere."""
    return is_admin(member)

async def channel_by_id(channel_id) -> discord.abc.Messageable | None:
    if not channel_id:
        return None
    try:
        return bot.get_channel(int(channel_id)) or await bot.fetch_channel(int(channel_id))
    except discord.HTTPException as e:
        log.warning("Kanal %s nicht erreichbar: %s", channel_id, e)
        return None

async def post_bot_log(text: str):
    ch = await channel_by_id(cfg.get("botcmd_channel_id") or cfg.get("officer_channel_id"))
    if ch:
        try:
            await ch.send(text[:1990])
        except discord.HTTPException:
            pass

def bot_guild():
    return bot.get_guild(int(cfg["guild_id"])) if cfg.get("guild_id") else None


# D-3 Schritt 12 (1.5.157): aus bot.py – Kanal-ID eines Raid-Pools (signup, loot, dkp …) aus config.json
def raid_channel(pool: str, kind: str) -> int:
    return int(((cfg.get("raid_channels") or {}).get(pool) or {}).get(kind) or 0)


# D-3 Schritt 14 (1.5.159): aus bot.py – nur der Gildenchef bzw. Server-Besitzer
def is_chef(member) -> bool:
    """Nur der Gildenchef (bzw. der Besitzer des Discord-Servers) – z. B. für den Gildennamen."""
    if not isinstance(member, discord.Member):
        return False
    if member.guild and member.id == member.guild.owner_id:
        return True
    return is_guild_leader(member)
