"""PUG-Einladung (D-3 Schritt 22, ab Bot 1.5.169): dauerhafter PUG-Einladungslink (/pug-einladung); wer darüber
beitritt, bekommt automatisch die Rolle Gast und eine kurze Anleitung per PN.

UNVERÄNDERT aus bot.py verschoben: der ganze Abschnitt "PUG-Einladungslink" (refresh_invite_cache,
handle_member_join, pug_invite_cmd). bot.py importiert dieses Modul nach "grund.bot = bot" (/pug-einladung wird
beim Import angemeldet) und übernimmt refresh_invite_cache und handle_member_join (Ereignisse in RaidBot).
Weg A (Antwort der Prüf-Sitzung 15.11. 20:48).
"""
from __future__ import annotations

import asyncio

import discord

import grund
from bot_hilfen import fetch_invite_uses
from grund import bot_guild, channel_by_id, is_creator, restart_soon
from kern import cfg, log, save_config, state

bot = grund.bot
assert bot is not None, "pug_bot erst nach grund.bot = bot importieren"


# ---------------------------------------------------------------------------
# PUG-Einladungslink: wer darüber beitritt, bekommt automatisch die Rolle Gast
# ---------------------------------------------------------------------------

async def refresh_invite_cache():
    uses = await fetch_invite_uses(bot_guild())
    if uses is not None:
        bot.invite_uses = uses


async def handle_member_join(member):
    if not cfg.get("guild_id") or member.guild.id != int(cfg["guild_id"]) or member.bot:
        return
    code = cfg.get("pug_invite_code")
    before = dict(bot.invite_uses)
    after = await fetch_invite_uses(member.guild)
    if after is None:
        return
    bot.invite_uses = after
    used = [c for c, n in after.items() if n > before.get(c, 0)]
    if not code or used != [code]:
        return
    role = discord.utils.get(member.guild.roles, name="Gast")
    if role:
        try:
            await member.add_roles(role, reason="Beitritt über den PUG-Einladungslink")
        except discord.HTTPException as e:
            log.warning("Rolle Gast für %s nicht vergeben: %s", member, e)
            return
    log.info("%s ist über den PUG-Link beigetreten – Rolle Gast vergeben.", member)
    pug = f"<#{cfg['pug_channel_id']}>" if cfg.get("pug_channel_id") else "#pug-anmeldung"
    try:
        await member.send(
            f"👋 Willkommen bei **{cfg.get('guild_name') or member.guild.name}**!\n"
            f"Für unsere PUG-Raids: In {pug} auf **Als PUG-Spieler registrieren** klicken, Charakter festlegen, "
            "dann bei einem Raid anmelden. Soft Reserve und Loot laufen über softres.it (Link am Raid). Viel Spaß!")
    except discord.HTTPException:
        pass


@bot.tree.command(name="pug-einladung", description="Einladungslink für PUG-Spieler (bekommen automatisch die Rolle Gast)")
async def pug_invite_cmd(inter: discord.Interaction):
    if not is_creator(inter.user):
        await inter.response.send_message("Das dürfen nur der Gildenchef und die Offiziere.", ephemeral=True)
        return
    guild = inter.guild
    if state.data.get("members_intent_missing"):
        state.data["members_intent_missing"] = False
        state.save()
        await inter.response.send_message(
            "Dafür muss der Bot neue Mitglieder sehen dürfen:\n"
            "1. https://discord.com/developers/applications → **Raidmaster tool** → **Bot**\n"
            "2. Unter **Privileged Gateway Intents** den **Server Members Intent** einschalten → speichern.\n"
            "3. Ich starte jetzt neu – danach `/pug-einladung` noch einmal.", ephemeral=True)
        asyncio.create_task(restart_soon())
        return
    if not guild.me.guild_permissions.manage_guild:
        await inter.response.send_message(
            "Damit der Bot erkennt, über welchen Link jemand beitritt, braucht er das Recht **Server verwalten**: "
            "Servereinstellungen → Rollen → Raidmaster tool → Berechtigungen → „Server verwalten“ einschalten.", ephemeral=True)
        return
    ch = await channel_by_id(cfg.get("pug_channel_id"))
    if not ch:
        await inter.response.send_message("#pug-anmeldung fehlt – bitte zuerst `/raidmaster-einrichten`.", ephemeral=True)
        return
    await inter.response.defer(ephemeral=True, thinking=True)
    invites = await fetch_invite_uses(guild) or {}
    code = cfg.get("pug_invite_code")
    if not code or code not in invites:
        invite = await ch.create_invite(max_age=0, max_uses=0, unique=True, reason=f"PUG-Einladung ({inter.user})")
        cfg["pug_invite_code"] = invite.code
        cfg["pug_invite_url"] = invite.url
        save_config()
        await refresh_invite_cache()
    await inter.followup.send(
        f"🎲 **PUG-Einladungslink:** {cfg['pug_invite_url']}\n"
        "• Wer über diesen Link beitritt, bekommt automatisch die Rolle **Gast** und sieht nur INFO und PUG.\n"
        "• Eure normalen Einladungslinks bleiben wie bisher.\n"
        "• Im Addon steht der Link nach dem Import („Für RaidMaster“ bei einem PUG-Raid) automatisch im Werbetext – "
        "oder du trägst ihn auf der Seite **Werbung** ein.", ephemeral=True)
