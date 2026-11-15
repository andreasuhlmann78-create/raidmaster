"""Discord-Ereignisse (D-3 Schritt 23, ab Bot 1.5.170): jeder Raid steht auch im Ereignis-Kalender des Servers;
/raid-ereignisse legt sie für alle offenen Raids an.

UNVERÄNDERT aus bot.py verschoben: der Abschnitt "Discord-Ereignisse" (RAID_EVENT_HOURS, create_raid_event,
delete_raid_event, raid_events_cmd). bot.py importiert dieses Modul nach "grund.bot = bot" (/raid-ereignisse wird
beim Import angemeldet) und übernimmt create_raid_event und delete_raid_event (Raid erstellen/absagen).
Weg A (Antwort der Prüf-Sitzung 15.11. 20:48).
"""
from __future__ import annotations

import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import discord

import grund
from grund import bot_guild, channel_by_id, is_creator
from kern import TZ, book, cfg, log

bot = grund.bot
assert bot is not None, "ereignis_bot erst nach grund.bot = bot importieren"


# ---------------------------------------------------------------------------
# Discord-Ereignisse: jeder Raid steht auch im Ereignis-Kalender des Servers
# ---------------------------------------------------------------------------
RAID_EVENT_HOURS = 3


async def create_raid_event(raid: dict):
    if not cfg.get("raid_events", True) or raid.get("test") or raid.get("event_id"):
        return
    guild = bot_guild()
    if guild is None or not guild.me.guild_permissions.manage_events:
        if guild is not None:
            log.info("Ereignis für Raid #%s nicht angelegt: Bot braucht die Berechtigung 'Events verwalten'.", raid["id"])
        return
    start = datetime.fromtimestamp(raid["start"], ZoneInfo(TZ))
    if start.timestamp() < time.time() + 60:
        return
    end = start + timedelta(hours=RAID_EVENT_HOURS)
    ch = await channel_by_id(raid.get("channel_id"))
    jump = f"https://discord.com/channels/{guild.id}/{raid['channel_id']}/{raid['message_id']}" if raid.get("message_id") else ""
    desc = (raid.get("description") or "") + (f"\n\nAnmeldung: {jump}" if jump else "")
    try:
        ev = await guild.create_scheduled_event(
            name=raid["title"][:100], start_time=start, end_time=end, entity_type=discord.EntityType.external,
            privacy_level=discord.PrivacyLevel.guild_only, location=f"WoW Forever – {raid.get('pool_name') or 'Raid'}"[:100],
            description=desc[:1000] or None)
        raid["event_id"] = ev.id
        book.save()
    except (discord.HTTPException, TypeError) as e:
        log.warning("Ereignis für Raid #%s nicht angelegt: %s", raid["id"], e)


async def delete_raid_event(raid: dict):
    eid = raid.get("event_id")
    guild = bot_guild()
    if not eid or guild is None:
        return
    try:
        ev = guild.get_scheduled_event(int(eid)) or await guild.fetch_scheduled_event(int(eid))
        await ev.delete()
    except discord.HTTPException:
        pass
    raid.pop("event_id", None)
    book.save()


@bot.tree.command(name="raid-ereignisse", description="Für alle offenen Raids die Discord-Ereignisse anlegen (Offiziere)")
async def raid_events_cmd(inter: discord.Interaction):
    if not is_creator(inter.user):
        await inter.response.send_message("Das dürfen nur der Gildenchef und die Offiziere.", ephemeral=True)
        return
    await inter.response.defer(ephemeral=True)
    n = 0
    for r in book.open_raids():
        if not r.get("event_id") and not r.get("cancelled"):
            await create_raid_event(r)
            n += 1 if r.get("event_id") else 0
    await inter.followup.send(f"{n} Ereignisse angelegt." if n else
                              "Keine neuen Ereignisse (alle haben schon eins, oder dem Bot fehlt die Berechtigung „Events verwalten“).",
                              ephemeral=True)
