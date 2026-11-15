"""DKP-Befehle (D-3 Schritt 31, ab Bot 1.5.178): DKP-Daten aus der hochgeladenen RaidMaster-Datei bei Bedarf neu
laden (reload_dkp_if_needed), /dkp, /dkpliste, /raidmaster-status.

UNVERÄNDERT aus bot.py verschoben: data_path, reload_dkp_if_needed, dkp_cmd, pool_autocomplete, dkp_list_cmd,
status_cmd. bot.py importiert dieses Modul nach "grund.bot = bot" (drei Befehle werden beim Import angemeldet) und
übernimmt reload_dkp_if_needed (Uploads, Aufstellung). Weg A (Antwort der Prüf-Sitzung 15.11. 20:48).
"""
from __future__ import annotations

import asyncio
import os

import discord
from discord import app_commands

import grund
import raidmaster_data as rmd
import updater
from dkp_tafel_bot import dkp_list_messages
from grund import is_creator
from kern import BASE, UPLOAD_PATH, book, cfg, log, state

bot = grund.bot
assert bot is not None, "dkp_befehle_bot erst nach grund.bot = bot importieren"


def data_path() -> str:
    """Hochgeladene Daten (Server-Betrieb) haben Vorrang, sonst der lokale Pfad aus config.json."""
    if os.path.isfile(UPLOAD_PATH):
        return UPLOAD_PATH
    return cfg.get("savedvariables_path") or ""


def reload_dkp_if_needed():
    path = data_path()
    if not path or not os.path.isfile(path):
        return False
    mtime = os.path.getmtime(path)
    if bot.dkp_data is not None and mtime == bot.dkp_mtime:
        return False
    db = rmd.load_raidmaster_db(path)
    if db is None:
        return False
    data = db.get("data") or {}
    bot.dkp_db = db
    bot.dkp_data = data
    bot.dkp_rows = rmd.standings(data, "mc")
    bot.dkp_mtime = mtime
    return True


@bot.tree.command(name="dkp", description="DKP-Stand abfragen")
@app_commands.describe(name="Charaktername (leer = dein eigener)")
async def dkp_cmd(inter: discord.Interaction, name: str | None = None):
    try:
        await asyncio.to_thread(reload_dkp_if_needed)
    except Exception:
        log.exception("DKP-Datei konnte nicht gelesen werden")
    if not bot.dkp_data:
        await inter.response.send_message("Noch keine DKP-Daten verfügbar.", ephemeral=True)
        return
    if not name:
        p = book.profile(inter.user.id)
        if not p:
            await inter.response.send_message("Gib einen Namen an (`/dkp name:Andi`) oder lege mit `/charakter` deinen Charakter fest.", ephemeral=True)
            return
        name = p["name"]
    summary = rmd.player_summary(bot.dkp_data, name)
    if not summary:
        await inter.response.send_message(f"**{rmd.clean_name(name)}** hat noch keine DKP.", ephemeral=True)
        return
    lines = [f"**{rmd.clean_name(name)}** – DKP pro Raid:"]
    for raid_name, dkp, pos, total in summary:
        lines.append(f"• {raid_name}: **{dkp}** (Platz {pos} von {total})")
    lines.append(f"Stand: <t:{int(bot.dkp_mtime)}:R>")
    await inter.response.send_message("\n".join(lines), ephemeral=True)



@bot.tree.command(name="anwesenheit", description="Wie oft war ein Charakter bei den letzten Raids dabei?")
@app_commands.describe(name="Charaktername (leer = dein eigener)")
async def attendance_cmd(inter: discord.Interaction, name: str | None = None):
    """D-N1 (ab Bot 1.5.183): Teilnahme an den letzten Raidtagen – dieselbe Zählung wie für die Aufstellung
    (rmd.attendance: aus dem Addon, sonst aus den Discord-Anmeldungen)."""
    try:
        await asyncio.to_thread(reload_dkp_if_needed)
    except Exception:
        log.exception("DKP-Datei konnte nicht gelesen werden")
    if not name:
        p = book.profile(inter.user.id)
        if not p:
            await inter.response.send_message("Gib einen Namen an oder lege mit `/charakter` deinen Charakter fest.",
                                              ephemeral=True)
            return
        name = p["name"]
    name = rmd.clean_name(name)
    att, n, source = rmd.attendance(bot.dkp_data, book)
    if not n:
        await inter.response.send_message("Noch keine vergangenen Raids erfasst.", ephemeral=True)
        return
    days = round(att.get(name.lower(), 0) * n)
    unit = "Raidtagen" if source == "Addon" else "Raids"
    await inter.response.send_message(
        f"**{name}** war bei **{days} von {n}** der letzten {unit} dabei ({round(100 * days / n)} %). "
        f"Quelle: {'RaidMaster-Addon' if source == 'Addon' else 'Discord-Anmeldungen'}.", ephemeral=True)

async def pool_autocomplete(inter: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    keys = rmd.pool_list(bot.dkp_data or {})
    out = []
    for k in keys:
        name = rmd.pool_name(k, bot.dkp_data)
        if current.lower() in name.lower():
            out.append(app_commands.Choice(name=name, value=k))
    return out[:20]


@bot.tree.command(name="dkpliste", description="Die ersten Plätze der DKP-Tabelle eines Raids anzeigen")
@app_commands.describe(raid="Welcher Raid? (Standard: Molten Core)")
@app_commands.autocomplete(raid=pool_autocomplete)
async def dkp_list_cmd(inter: discord.Interaction, raid: str = "mc"):
    try:
        await asyncio.to_thread(reload_dkp_if_needed)
    except Exception:
        log.exception("DKP-Datei konnte nicht gelesen werden")
    rows = rmd.standings(bot.dkp_data or {}, raid)
    await inter.response.defer(ephemeral=True)
    chunks = await dkp_list_messages(raid, rows, bot.dkp_data, bot.dkp_db, f"**DKP-Stände {rmd.pool_name(raid, bot.dkp_data)}**")
    await inter.followup.send(chunks[0], ephemeral=True)
    for text in chunks[1:]:
        await inter.followup.send(text, ephemeral=True)


@bot.tree.command(name="raidmaster-status", description="Zeigt, ob der Bot die RaidMaster-Datei findet")
async def status_cmd(inter: discord.Interaction):
    if not is_creator(inter.user):
        await inter.response.send_message("Das dürfen nur der Gildenchef und die Offiziere.", ephemeral=True)
        return
    path = data_path() or "(noch keine Daten)"
    exists = os.path.isfile(path)
    lines = [f"**RaidMaster-Bot {updater.bot_version(BASE)}**"
             + (f" · Commit `{state.data['installed_sha'][:7]}`" if state.data.get("installed_sha") else "")]
    if cfg.get("update_repo"):
        lines.append(f"Updates: GitHub `{cfg['update_repo']}` (alle {cfg.get('update_check_minutes', 30)} Min.)")
    else:
        lines.append("Updates: nur per `/update` mit ZIP (kein GitHub-Repository eingetragen)")
    if state.data.get("last_upload"):
        lines.append(f"Letzter Daten-Upload: <t:{int(state.data['last_upload'])}:R> von {state.data.get('last_upload_by') or '?'}")
    else:
        lines.append("Daten-Uploads: noch keine (`/uploader` einrichten)" if cfg.get("data_channel_id") else
                     "Daten-Uploads: kein Kanal #bot-daten – `/raidmaster-einrichten` ausführen")
    if state.data.get("last_test_upload"):
        lines.append(f"Letzte Testdaten: <t:{int(state.data['last_test_upload'])}:R> von {state.data.get('last_test_upload_by') or '?'}")
    lines.append(f"RaidMaster-Datei: `{path}` " + ("✅" if exists else "❌"))
    if exists:
        lines.append(f"Zuletzt geändert: <t:{int(os.path.getmtime(path))}:R>")
        lines.append(f"Spieler mit DKP: {len(bot.dkp_rows)} · Skillungen bekannt: {len(rmd.specs_from_db(bot.dkp_db))}")
    lines.append(f"DKP-Kanal: {'<#' + str(cfg['dkp_channel_id']) + '>' if cfg.get('dkp_channel_id') else 'aus'}")
    lines.append(f"Loot-Kanal: {'<#' + str(cfg['loot_channel_id']) + '>' if cfg.get('loot_channel_id') else 'aus'}")
    lines.append("Hinweis: WoW speichert die Datei beim Ausloggen oder nach /reload.")
    await inter.response.send_message("\n".join(lines), ephemeral=True)
