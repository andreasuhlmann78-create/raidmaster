"""Raid-Anzeige (D-3 Schritt 24, ab Bot 1.5.171): Kärtchen eines Raids (raid_embed) und das Aktualisieren der
Anmelde-Nachricht (update_raid_message) – gebraucht von Anmeldung, Twinks, Ersatzbank, Erinnerungen und Raid-Befehlen.

UNVERÄNDERT aus bot.py verschoben: raid_embed, update_raid_message. Knöpfe der Anmeldung: bot_hilfen.raid_view.
bot.py importiert dieses Modul nach "grund.bot = bot" und übernimmt beide Namen.
Weg A (Antwort der Prüf-Sitzung 15.11. 20:48).
"""
from __future__ import annotations

import discord

import grund
import raidmaster_data as rmd
from bot_hilfen import raid_view
from kern import GREY, ORANGE, book, log

bot = grund.bot
assert bot is not None, "raidanzeige_bot erst nach grund.bot = bot importieren"


def raid_embed(raid: dict) -> discord.Embed:
    start = raid["start"]
    title = raid["title"]
    if raid.get("cancelled"):
        title += " – ABGESAGT"
    elif raid.get("closed"):
        title += " (Anmeldung geschlossen)"
    desc = f"🗓️ <t:{start}:F> · <t:{start}:R>"
    if raid.get("pool_name"):
        desc = f"🏰 **{raid['pool_name']}**\n" + desc
    if raid.get("mode") == "pug":
        desc += "\n🎲 **PUG-Raid** · kein DKP · Soft Reserve und Loot über softres.it"
        if raid.get("softres"):
            desc += f"\n🔗 **Soft Reserve:** {raid['softres']}"
    if raid.get("description"):
        desc += "\n" + raid["description"]
    count = book.count_status(raid, "an")
    desc += f"\n\n**Angemeldet: {count}" + (f" / {raid['max']}" if raid.get("max") else "") + "**"
    summary = rmd.class_summary(raid)
    if summary:
        desc += "\n" + summary
    e = discord.Embed(title=title, description=desc, color=GREY if raid.get("closed") else ORANGE)
    for name, value, inline in rmd.raid_fields(raid):
        e.add_field(name=name, value=value, inline=inline)
    e.set_footer(text=f"Raid-ID {raid['id']} · RaidMaster")
    return e


async def update_raid_message(raid: dict):
    if raid.get("message_id"):
        try:
            channel = bot.get_channel(raid["channel_id"]) or await bot.fetch_channel(raid["channel_id"])
            await channel.get_partial_message(raid["message_id"]).edit(embed=raid_embed(raid), view=raid_view(raid))
        except discord.HTTPException as e:
            log.warning("Raid-Nachricht %s konnte nicht aktualisiert werden: %s", raid["id"], e)
