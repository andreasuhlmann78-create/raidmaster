"""Persönliche DKP-Nachricht (D-3 Schritt 27, ab Bot 1.5.174): nach dem Raid eine Direktnachricht an jeden
Teilnehmer mit Discord-Profil (DKP-Stand, Beute), an- und abbestellbar mit /dkp-nachricht.

UNVERÄNDERT aus bot.py verschoben: der Abschnitt "Persönliche DKP-Nachricht nach dem Raid" (DM_MAX_AGE,
find_member_for_char, send_raid_dms, dkp_dm_cmd; 79 Zeilen). bot.py importiert dieses Modul nach
"grund.bot = bot" (/dkp-nachricht wird beim Import angemeldet) und übernimmt send_raid_dms und
find_member_for_char (Raider des Monats). Weg A (Antwort der Prüf-Sitzung 15.11. 20:48).
"""
from __future__ import annotations

import asyncio
import time

import discord
from discord import app_commands

import grund
import raidmaster_data as rmd
from bot_hilfen import test_info
from grund import bot_guild
from kern import book, cfg, log, state

bot = grund.bot
assert bot is not None, "dkp_nachricht_bot erst nach grund.bot = bot importieren"


# ---------------------------------------------------------------------------
# Persönliche DKP-Nachricht nach dem Raid (Direktnachricht an jeden Teilnehmer mit Discord-Profil)
# ---------------------------------------------------------------------------
DM_MAX_AGE = 2 * 86400


async def find_member_for_char(name: str):
    guild = bot_guild()
    uid = book.user_for_char(name)
    if guild is None:
        return None
    if uid:
        m = guild.get_member(uid)
        if m is None:
            try:
                m = await guild.fetch_member(uid)
            except discord.HTTPException:
                m = None
        return m
    n = name.lower()
    for m in guild.members:
        for cand in (getattr(m, "nick", None), getattr(m, "global_name", None), m.name):
            if cand and str(cand).strip().lower().split(" ")[0] == n:
                return m
    return None


async def send_raid_dms():
    if not cfg.get("raid_dms", True):
        return
    data = bot.dkp_data or {}
    if test_info(bot.dkp_db):
        return
    sent = state.data.setdefault("dm_sent", [])
    now = time.time()
    links = book.alt_links()
    players = data.get("players") or {}
    for summ in rmd.raid_summaries(data):
        if summ["id"] in sent:
            continue
        sent.append(summ["id"])
        if now - summ["t"] > DM_MAX_AGE:
            continue                       # alte Raids beim ersten Start nicht nachschicken
        count = 0
        for row in summ["rows"]:
            if not row.get("present") and not row.get("earned"):
                continue
            main = links.get(row["name"]) or ((players.get(row["name"]) or {}).get("m") if isinstance(players.get(row["name"]), dict) else None)
            member = await find_member_for_char(row["name"]) or (await find_member_for_char(main) if main else None)
            if member is None or member.bot:
                continue
            prof = book.profile(member.id) or {}
            if prof.get("no_dm"):
                continue
            try:
                await member.send(rmd.raid_dm_text(summ, row, data, main))
                count += 1
            except discord.HTTPException:
                pass                       # Direktnachrichten ausgeschaltet
            await asyncio.sleep(0.5)
        log.info("Raid %s: %d persönliche DKP-Nachrichten verschickt.", summ["id"], count)
    del sent[:-200]
    state.save()


@bot.tree.command(name="dkp-nachricht", description="Persönliche DKP-Nachricht nach jedem Raid an- oder abbestellen")
@app_commands.choices(wahl=[app_commands.Choice(name="an", value="an"), app_commands.Choice(name="aus", value="aus")])
async def dkp_dm_cmd(inter: discord.Interaction, wahl: app_commands.Choice[str]):
    p = book.profile(inter.user.id)
    if not p:
        await inter.response.send_message("Lege zuerst dein Charakterprofil an (`/charakter`).", ephemeral=True)
        return
    if wahl.value == "aus":
        p["no_dm"] = True
    else:
        p.pop("no_dm", None)
    book.profiles.save()
    await inter.response.send_message("Nach jedem Raid bekommst du deine DKP-Zusammenfassung per Direktnachricht."
                                      if wahl.value == "an" else "Keine DKP-Nachrichten mehr nach dem Raid.", ephemeral=True)
