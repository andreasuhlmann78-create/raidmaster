"""Monatliches und Raider des Monats (D-3 Schritt 28, ab Bot 1.5.175): stündliche Schleife (Raidfähigkeit,
Marktdaten-Wochenbericht und -Tageszusammenfassung, monatliche Blizzard-Prüfung, am Monatsanfang Raider des
Monats für den Vormonat) und /raider-des-monats.

UNVERÄNDERT aus bot.py verschoben (samt Kommentar darüber): RDM_ROLE, announce_raider_of_month, monthly_loop,
before_monthly, rdm_cmd. Bleibt in bot.py: /rekorde (braucht raid_pool_autocomplete aus dem Raid-Bereich).
bot.py importiert dieses Modul nach "grund.bot = bot" (/raider-des-monats wird beim Import angemeldet) und
übernimmt monthly_loop (Start in setup_hook). Weg A (Antwort der Prüf-Sitzung 15.11. 20:48).
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import discord
from discord import app_commands
from discord.ext import tasks

import grund
import raidmaster_data as rmd
from bank_bot import post_raid_ready
from dkp_nachricht_bot import find_member_for_char
from grund import bot_guild, is_creator
from kern import TZ, log, state
from markt_bot import blizzard_monthly, post_market_daily, post_market_report
from ruhmeshalle_bot import hall_channel

bot = grund.bot
assert bot is not None, "monatlich_bot erst nach grund.bot = bot importieren"


# Raider des Monats: am Monatsanfang für den Vormonat, mit eigener Rolle für einen Monat
RDM_ROLE = "⭐ Raider des Monats"


async def announce_raider_of_month(year: int, month: int, force: bool = False) -> str:
    ranking = rmd.raider_of_month(bot.dkp_data, year, month, TZ)
    label = f"{month:02d}.{year}"
    if not ranking:
        return f"Im {label} gab es keine Raids."
    top = ranking[0]
    guild = bot_guild()
    role_text = ""
    if guild is not None and guild.me.guild_permissions.manage_roles:
        try:
            role = discord.utils.get(guild.roles, name=RDM_ROLE) or await guild.create_role(
                name=RDM_ROLE, colour=discord.Colour.gold(), hoist=False, mentionable=False, reason="RaidMaster: Raider des Monats")
            for m in list(role.members):
                await m.remove_roles(role, reason="RaidMaster: neuer Raider des Monats")
            member = await find_member_for_char(top["name"])
            if member:
                await member.add_roles(role, reason="RaidMaster: Raider des Monats")
                role_text = f" {member.mention} bekommt für einen Monat die Rolle **{RDM_ROLE}**."
        except discord.HTTPException as e:
            log.warning("Rolle Raider des Monats: %s", e)
    medals = ["🥇", "🥈", "🥉"]
    lines = [f"⭐ **Raider des Monats {label}: {top['name']}!**{role_text}",
             f"{top['raids']} Raids dabei, {top['punctual']}× pünktlich, {top['bench']}× auf der Ersatzbank bereit. Danke für deinen Einsatz!", ""]
    for i, r in enumerate(ranking[:3]):
        lines.append(f"{medals[i]} {r['name']} – {r['raids']} Raids · {r['punctual']}× pünktlich · {r['bench']}× Ersatzbank ({r['score']} Punkte)")
    lines.append("_Punkte: Raid dabei 10 · pünktlich 2 · Ersatzbank bereit 5._")
    ch = await hall_channel()
    if ch:
        await ch.send("\n".join(lines), allowed_mentions=discord.AllowedMentions(users=True))
    return lines[0]


@tasks.loop(hours=1)
async def monthly_loop():
    try:
        await post_raid_ready()
    except Exception:  # noqa: BLE001
        log.exception("Raidfähigkeit konnte nicht gepostet werden")
    try:
        await post_market_report()
    except Exception:  # noqa: BLE001
        log.exception("Marktdaten-Wochenbericht fehlgeschlagen")
    try:
        await post_market_daily()
    except Exception:  # noqa: BLE001
        log.exception("Marktdaten-Tageszusammenfassung fehlgeschlagen")
    try:
        await blizzard_monthly()
    except Exception:  # noqa: BLE001
        log.exception("Blizzard-Prüfung (monatlich) fehlgeschlagen")
    now = datetime.now(ZoneInfo(TZ))
    prev = (now.replace(day=1) - timedelta(days=1))
    key = f"{prev.year}-{prev.month:02d}"
    if state.data.get("rdm_done") == key or now.day > 7:
        return
    if not state.data.get("rdm_done"):
        state.data["rdm_done"] = key       # erster Start: nicht rückwirkend küren
        state.save()
        return
    state.data["rdm_done"] = key
    state.save()
    try:
        await announce_raider_of_month(prev.year, prev.month)
    except Exception:  # noqa: BLE001
        log.exception("Raider des Monats fehlgeschlagen")


@monthly_loop.before_loop
async def before_monthly():
    await bot.wait_until_ready()


@bot.tree.command(name="raider-des-monats", description="Rangliste eines Monats (Offiziere: auch verkünden)")
@app_commands.describe(monat="MM.JJJJ (leer = aktueller Monat)", verkuenden="Offiziere: in #ruhmeshalle verkünden und Rolle vergeben")
async def rdm_cmd(inter: discord.Interaction, monat: str | None = None, verkuenden: bool = False):
    now = datetime.now(ZoneInfo(TZ))
    year, month = now.year, now.month
    if monat:
        m_ = re.match(r"^(\d{1,2})\.(\d{4})$", monat.strip())
        if not m_:
            await inter.response.send_message("Format: MM.JJJJ, z. B. 11.2026", ephemeral=True)
            return
        month, year = int(m_.group(1)), int(m_.group(2))
    if verkuenden:
        if not is_creator(inter.user):
            await inter.response.send_message("Verkünden dürfen nur der Gildenchef und die Offiziere.", ephemeral=True)
            return
        await inter.response.defer(ephemeral=True)
        await inter.followup.send(await announce_raider_of_month(year, month, True), ephemeral=True)
        return
    ranking = rmd.raider_of_month(bot.dkp_data, year, month, TZ)
    if not ranking:
        await inter.response.send_message(f"Im {month:02d}.{year} gibt es (noch) keine Raids.", ephemeral=True)
        return
    lines = [f"⭐ **Rangliste {month:02d}.{year}**"] + [
        f"{i + 1}. {r['name']} – {r['score']} Punkte ({r['raids']} Raids, {r['punctual']}× pünktlich, {r['bench']}× Ersatzbank)"
        for i, r in enumerate(ranking[:10])]
    await inter.response.send_message("\n".join(lines), ephemeral=True)
