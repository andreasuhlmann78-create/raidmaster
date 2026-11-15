"""Willkommen (D-3 Schritt 14, ab Bot 1.5.159): Willkommenstext in #willkommen (/willkommen), dauerhafter
Einladungslink für #willkommen (/einladung, einmal beim Start in #befehlsliste gemeldet).

UNVERÄNDERT aus bot.py verschoben: welcome_invite_cmd, post_welcome_invite_once, OLD_WELCOME_START,
ensure_welcome, welcome_cmd. Der Text steht in server_setup.welcome_text, der Link in invites.py.
Bleibt in bot.py: PUG-Einladungslink (/pug-einladung, Rolle Gast beim Beitritt).
bot.py importiert dieses Modul nach "grund.bot = bot" (zwei Befehle werden beim Import angemeldet) und übernimmt
die Namen. Weg A (Antwort der Prüf-Sitzung 15.11. 20:48).
"""
from __future__ import annotations

import zlib

import discord
from discord import app_commands

import grund
import invites
import server_setup
from grund import bot_guild, channel_by_id, is_admin, is_chef, is_creator
from kern import cfg, log, save_config, state

bot = grund.bot
assert bot is not None, "willkommen_bot erst nach grund.bot = bot importieren"


@bot.tree.command(name="einladung", description="Dauerhafter Einladungslink für #willkommen (nur Gildenleitung)")
async def welcome_invite_cmd(inter: discord.Interaction):
    if not is_creator(inter.user):
        await inter.response.send_message("Das dürfen nur der Gildenchef und die Offiziere.", ephemeral=True)
        return
    await inter.response.defer(ephemeral=True, thinking=True)
    res = await invites.ensure_welcome_invite(inter.guild, state.data, bot.fetch_invite, str(inter.user))
    state.save()
    await inter.followup.send(invites.invite_text(res), ephemeral=True)


async def post_welcome_invite_once() -> str | None:
    """Einmalig (ab Bot 1.5.110): Link für #willkommen erstellen bzw. prüfen und EINMAL in #befehlsliste posten.
    Nur dort; fehlt #befehlsliste, wird beim nächsten Start erneut versucht."""
    if state.data.get("welcome_invite_posted"):
        return None
    guild = bot_guild()
    if guild is None:
        return None
    channel = await channel_by_id(cfg.get("command_list_channel_id")) or server_setup.find_channel(guild.text_channels, "befehlsliste")
    if channel is None:
        return None
    res = await invites.ensure_welcome_invite(guild, state.data, bot.fetch_invite, "Bot-Start")
    state.save()
    await channel.send(invites.invite_text(res), allowed_mentions=discord.AllowedMentions.none())
    state.data["welcome_invite_posted"] = True
    state.save()
    return "🔗 Dauerhafte Einladung für #willkommen in #befehlsliste gemeldet."


OLD_WELCOME_START = "**Willkommen in unserer Gilde!**"


async def ensure_welcome(update: bool = True) -> str:
    """Willkommenstext in #willkommen eintragen: fehlt er, wird er gepostet; update=True aktualisiert ihn
    (z. B. nach der Einrichtung, wenn neue Kanäle verlinkt werden können). Alte Bot-Begrüßung wird ersetzt."""
    guild = bot_guild()
    if guild is None:
        return "Server nicht gefunden."
    channel = await channel_by_id(cfg.get("welcome_channel_id")) or discord.utils.get(guild.text_channels, name="willkommen")
    if channel is None:
        return "Kanal #willkommen nicht gefunden – bitte zuerst `/raidmaster-einrichten`."
    ids = {c.name: c.id for c in guild.text_channels}
    officer = discord.utils.get(guild.roles, name="Offizier")
    text = server_setup.welcome_text(cfg.get("guild_name") or guild.name, ids, officer.id if officer else None)
    no_ping = discord.AllowedMentions(roles=False, users=False, everyone=False)
    msg_id = state.data.get("welcome_message")
    digest = str(zlib.crc32(text.encode("utf-8")))
    if msg_id:
        # beim Start: nur bearbeiten, wenn sich der Text geändert hat (z. B. neue Fassung mit einem Update)
        if not update and state.data.get("welcome_hash") == digest:
            return "Willkommenstext ist bereits eingetragen."
        try:
            await channel.get_partial_message(int(msg_id)).edit(content=text, allowed_mentions=no_ping)
            state.data["welcome_hash"] = digest
            state.save()
            return f"✅ Willkommenstext in {channel.mention} aktualisiert."
        except discord.HTTPException:
            pass
    # frühere, kurze Begrüßung des Bots entfernen
    try:
        async for old in channel.history(limit=30):
            if old.author.id == bot.user.id and (old.content or "").startswith(OLD_WELCOME_START):
                await old.delete()
    except discord.HTTPException:
        pass
    msg = await channel.send(text, allowed_mentions=no_ping)
    state.data["welcome_message"] = msg.id
    state.data["welcome_hash"] = digest
    state.save()
    log.info("Willkommenstext in #%s eingetragen.", channel.name)
    return f"✅ Willkommenstext in {channel.mention} eingetragen."


@bot.tree.command(name="willkommen", description="Willkommenstext in #willkommen aktualisieren, z. B. mit neuem Gildennamen (Gildenleitung)")
@app_commands.describe(gildenname="Name eurer Gilde (wird gespeichert, nur Gildenchef)")
async def welcome_cmd(inter: discord.Interaction, gildenname: str | None = None):
    if not is_admin(inter.user):
        await inter.response.send_message("Das dürfen nur der Gildenchef und die Offiziere.", ephemeral=True)
        return
    if gildenname:
        # den Gildennamen legt nur der Gildenchef fest (Besitzer des Servers oder eingetragener Gildenchef)
        if not is_chef(inter.user):
            await inter.response.send_message("Den Gildennamen kann nur der Gildenchef ändern.", ephemeral=True)
            return
        cfg["guild_name"] = gildenname.strip()
        save_config()
        state.data["guild_name_applied"] = cfg["guild_name"]
        state.save()
    await inter.response.send_message(await ensure_welcome(update=True), ephemeral=True)
