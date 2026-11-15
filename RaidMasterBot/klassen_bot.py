"""Klassenfarben (D-3 Schritt 13, ab Bot 1.5.158): je WoW-Klasse eine Rolle in der Klassenfarbe, damit der Name im
Discord wie im Spiel erscheint. Klasse aus dem Profil (/profil bzw. Anmeldung), sonst über den Discord-Namen aus
den RaidMaster-Daten.

UNVERÄNDERT aus bot.py verschoben: member_class, ensure_class_role, sync_class_roles. sync_specs bleibt in bot.py
(aktualisiert Raid-Anmeldungen, gehört zum Raid-Bereich).
bot.py importiert dieses Modul nach "grund.bot = bot" und übernimmt die Namen.
Weg A (Antwort der Prüf-Sitzung 15.11. 20:48).
"""
from __future__ import annotations

import re

import discord

import grund
import render as rimg
from grund import bot_guild
from kern import book, cfg, log, save_config

bot = grund.bot
assert bot is not None, "klassen_bot erst nach grund.bot = bot importieren"


def member_class(member, players: dict) -> str | None:
    p = book.profile(member.id)
    if p and p.get("cls") in rimg.CLASS_COLORS:
        return p["cls"]
    names = {str(n).lower(): (v.get("c") if isinstance(v, dict) else None) for n, v in (players or {}).items()}
    for cand in (getattr(member, "nick", None), getattr(member, "global_name", None), member.name):
        if not cand:
            continue
        c = str(cand).strip().lower()
        cls = names.get(c) or names.get(c.split(" ")[0]) or names.get(re.split(r"[^\wäöüß]", c)[0] if c else "")
        if cls and str(cls).upper() in rimg.CLASS_COLORS:
            return str(cls).upper()
    return None


async def ensure_class_role(guild, cls: str):
    name = rimg.CLASS_NAMES.get(cls, cls.title())
    color = discord.Colour.from_rgb(*rimg.CLASS_COLORS[cls])
    ids = cfg.setdefault("class_roles", {})
    role = guild.get_role(int(ids.get(cls) or 0)) or discord.utils.get(guild.roles, name=name)
    if role is None:
        role = await guild.create_role(name=name, colour=color, hoist=False, mentionable=False,
                                       reason="RaidMaster: Klassenfarbe wie im Spiel")
        # direkt unter die Bot-Rolle schieben, damit die Farbe vor anderen farbigen Rollen gilt
        try:
            me = guild.me
            await guild.edit_role_positions({role: max(1, me.top_role.position - 1)})
        except discord.HTTPException:
            pass
    elif role.colour != color and role < guild.me.top_role:
        try:
            await role.edit(colour=color, reason="RaidMaster: Klassenfarbe wie im Spiel")
        except discord.HTTPException:
            pass
    if str(ids.get(cls)) != str(role.id):
        ids[cls] = role.id
        save_config()
    return role


async def sync_class_roles(only=None) -> int:
    """Jedem Mitglied die Rolle seiner Klasse geben (und andere Klassenrollen entfernen). Liefert die Anzahl Änderungen."""
    guild = bot_guild()
    if guild is None or not guild.me.guild_permissions.manage_roles:
        return 0
    players = (bot.dkp_data or {}).get("players") or {}
    members = list(only) if only else list(guild.members)
    if not members and not only:
        for uid in list(book.profiles.data.keys()):
            m = guild.get_member(int(uid))
            if m is None:
                try:
                    m = await guild.fetch_member(int(uid))
                except discord.HTTPException:
                    m = None
            if m:
                members.append(m)
    changes = 0
    class_role_ids = {int(v) for v in (cfg.get("class_roles") or {}).values() if v}
    for m in members:
        if m.bot:
            continue
        cls = member_class(m, players)
        if not cls:
            continue
        try:
            role = await ensure_class_role(guild, cls)
            class_role_ids.add(role.id)
            wrong = [r_ for r_ in m.roles if r_.id in class_role_ids and r_.id != role.id]
            if wrong:
                await m.remove_roles(*wrong, reason="RaidMaster: Klasse geändert")
                changes += 1
            if role not in m.roles:
                await m.add_roles(role, reason="RaidMaster: Klassenfarbe wie im Spiel")
                changes += 1
        except discord.HTTPException as e:
            log.info("Klassenrolle für %s nicht möglich: %s", m, e)
    if changes:
        log.info("Klassenfarben: %d Änderung(en).", changes)
    return changes
