"""Ersatz bei Absage (D-3 Schritt 25, ab Bot 1.5.172): sagt jemand kurz vor dem Raid ab (bis 48 Stunden vorher),
fragt der Bot passende Spieler der Ersatzbank per Direktnachricht; wer zuerst zusagt, rückt nach.

UNVERÄNDERT aus bot.py verschoben: der Abschnitt "Ersatz bei Absage" (SUB_HOURS, offer_substitute,
accept_substitute). Auswahl der Kandidaten: bot_hilfen.sub_candidates. bot.py importiert dieses Modul nach
"grund.bot = bot" und übernimmt beide Funktionen (Knöpfe in on_interaction).
Weg A (Antwort der Prüf-Sitzung 15.11. 20:48).
"""
from __future__ import annotations

import time

import discord

import grund
import raidmaster_data as rmd
from bot_hilfen import sub_candidates
from grund import bot_guild, channel_by_id
from kern import book, cfg, log
from raidanzeige_bot import update_raid_message

bot = grund.bot
assert bot is not None, "ersatz_bot erst nach grund.bot = bot importieren"


# ---------------------------------------------------------------------------
# Ersatz bei Absage: kurz vor dem Raid fragt der Bot passende Spieler der Ersatzbank per Direktnachricht
# ---------------------------------------------------------------------------
SUB_HOURS = 48


async def offer_substitute(raid: dict, leaver: dict):
    try:
        if raid.get("closed") or raid.get("test") or not cfg.get("auto_substitute", True):
            return
        if raid["start"] - time.time() > SUB_HOURS * 3600 or raid["start"] < time.time() - 1800:
            return
        if raid.get("max") and book.count_status(raid, "an") >= raid["max"]:
            return
        cands = sub_candidates(raid, leaver)
        if not cands:
            return
        guild = bot_guild()
        uid, s = cands[0]
        member = guild.get_member(int(uid)) if guild else None
        if member is None and guild:
            try:
                member = await guild.fetch_member(int(uid))
            except discord.HTTPException:
                member = None
        raid.setdefault("subs_asked", []).append(uid)
        book.save()
        if member is None:
            return
        view = discord.ui.View(timeout=None)
        view.add_item(discord.ui.Button(label="Ich komme!", emoji="✅", style=discord.ButtonStyle.success, custom_id=f"rm:sub:{raid['id']}"))
        role = rmd.ROLES.get(leaver.get("role"), leaver.get("role") or "")
        await member.send(f"🪑 Ein Platz ist frei: **{raid['title']}** am <t:{raid['start']}:F> – gesucht wird ein **{role}** "
                          f"(du stehst auf der Ersatzbank). Hast du Zeit? Dann klick auf **Ich komme!**", view=view)
        log.info("Raid #%s: %s als Ersatz gefragt.", raid["id"], s.get("name"))
    except Exception:  # noqa: BLE001
        log.exception("Ersatz konnte nicht gefragt werden")


async def accept_substitute(inter: discord.Interaction, raid: dict):
    uid = str(inter.user.id)
    s = raid["signups"].get(uid)
    if raid.get("closed"):
        await inter.response.send_message("Die Anmeldung ist schon geschlossen – danke trotzdem!", ephemeral=True)
        return
    if raid.get("max") and book.count_status(raid, "an") >= raid["max"] and not (s and s["status"] == "an"):
        await inter.response.send_message("Danke! Der Platz ist leider schon wieder besetzt – du bleibst auf der Ersatzbank.", ephemeral=True)
        return
    profile = book.profile(inter.user.id)
    if not profile:
        await inter.response.send_message("Dein Profil fehlt – bitte beim Raid über „Anmelden“ anmelden.", ephemeral=True)
        return
    if book.signup(raid, inter.user.id, "an", profile, int(time.time())) != "an":     # ab 1.5.185: Rolle voll
        await inter.response.send_message(
            f"Danke! Für **{rmd.ROLES.get(profile['role'], profile['role'])}** ist leider kein Platz mehr frei – du "
            "bleibst auf der Ersatzbank.", ephemeral=True)
        return
    await update_raid_message(raid)
    await inter.response.send_message(f"✅ Super, du bist für **{raid['title']}** angemeldet!", ephemeral=True)
    ch = await channel_by_id(cfg.get("officer_channel_id"))
    if ch:
        try:
            await ch.send(f"🪑 **{profile['name']}** springt bei **{raid['title']}** (<t:{raid['start']}:f>) von der Ersatzbank ein.")
        except discord.HTTPException:
            pass
