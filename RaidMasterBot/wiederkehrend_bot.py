"""Wiederkehrende Raids (D-N1 Wunsch 3, ab Bot 1.5.186): /raid wiederkehrend anlegen|liste|pausieren|loeschen.

Die Gildenleitung legt einen festen Wochentermin an (Raid, Wochentag, Uhrzeit in Europe/Zurich, wie viele Wochen im
Voraus, optional Titel, Beschreibung, Höchstzahl, Plätze je Rolle). Der Bot legt die Termine selbst an (Schleife alle
30 Minuten und direkt nach dem Anlegen): nie doppelt (gleicher Raid + Tag schon da – auch abgesagt oder von Hand
erstellt – oder schon einmal angelegt), nicht vor dem Öffnungsdatum des Raids ("opens" in forever_raids.json).
Gepostet wie /raid erstellen (Anmelde-Kanal der Raid-Kategorie, Discord-Ereignis). Nur DKP-Raids.
Vorlagen in state.json unter "recurring" (Nummern in "recurring_next"). Reine Funktionen: wiederkehrend.py.
bot.py importiert dieses Modul nach raid_bot (Untergruppe von /raid) und startet recurring_loop in setup_hook.
"""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import discord
from discord import app_commands
from discord.ext import tasks

import grund
import raid_post
import raidmaster_data as rmd
import server_setup
import wiederkehrend as wk
from bot_hilfen import raid_view
from ereignis_bot import create_raid_event
from grund import channel_by_id, is_creator, post_bot_log, raid_channel
from kern import TZ, book, cfg, log, state
from raid_bot import known_raids, raid_group, raid_pool_autocomplete
from raidanzeige_bot import raid_embed

bot = grund.bot
assert bot is not None, "wiederkehrend_bot erst nach grund.bot = bot importieren"


def now_local() -> datetime:
    return datetime.now(ZoneInfo(TZ))


def templates() -> list:
    return state.data.setdefault("recurring", [])


def find(number: int) -> dict | None:
    return next((t for t in templates() if t["id"] == number), None)


async def create_from_template(tpl: dict, start: datetime) -> bool:
    """Einen Termin anlegen und posten. False = nicht angelegt (Kanal fehlt, Discord-Fehler) – nächster Lauf versucht
    es wieder."""
    target_id = raid_channel(tpl["pool"], "signup")
    target = await channel_by_id(target_id) if target_id else None
    if target is None:
        log.warning("Wiederkehrender Raid #%s: kein Anmelde-Kanal für %s", tpl["id"], tpl["pool"])
        return False
    raid = book.create(tpl["title"][:80], start, (tpl.get("description") or "")[:500], tpl.get("max") or 0,
                       tpl.get("creator") or 0, target.id, mode="dkp")
    raid["pool"] = tpl["pool"]
    raid["pool_name"] = dict(known_raids()).get(tpl["pool"], tpl["pool"])
    raid["recurring"] = tpl["id"]
    if tpl.get("limits"):
        raid["limits"] = dict(tpl["limits"])
    book.save()

    async def reply(text):
        if text.startswith("Raid erstellt"):
            return
        await post_bot_log(f"⚠️ Wiederkehrender Raid **{tpl['title']}** ({start:%d.%m.%Y}): {text}")
    msg = await raid_post.post_new_raid(book, raid, target, raid_embed(raid), raid_view(raid), reply)
    if msg is None:
        return False
    try:
        await create_raid_event(raid)
    except Exception:  # noqa: BLE001
        log.exception("Discord-Ereignis für wiederkehrenden Raid nicht angelegt")
    log.info("Wiederkehrender Raid #%s angelegt: Raid #%s am %s", tpl["id"], raid["id"], start.isoformat())
    return True


async def run_recurring(only: dict | None = None) -> int:
    """Fällige Termine aller aktiven Vorlagen (oder nur `only`) anlegen. Liefert die Zahl der angelegten Raids."""
    now = now_local()
    made = 0
    for tpl in list(templates()):
        if tpl.get("paused") or (only is not None and tpl is not only):
            continue
        if not server_setup.raid_released(tpl["pool"], cfg):
            continue
        for start in wk.plan(tpl, now, server_setup.raid_opens(tpl["pool"])):
            if wk.already(tpl, start, book.all()):
                continue
            if await create_from_template(tpl, start):
                wk.mark_done(tpl, start, now.date())
                state.save()
                made += 1
    return made


@tasks.loop(minutes=30)
async def recurring_loop():
    try:
        await run_recurring()
    except Exception:  # noqa: BLE001
        log.exception("Wiederkehrende Raids: Lauf fehlgeschlagen")


@recurring_loop.before_loop
async def before_recurring():
    await bot.wait_until_ready()


recurring_group = app_commands.Group(name="wiederkehrend", description="Feste Wochentermine, die der Bot selbst anlegt (Offiziere)",
                                     parent=raid_group)
DAY_CHOICES = [app_commands.Choice(name=n, value=i) for i, n in enumerate(wk.WEEKDAYS)]
NO_RIGHTS = "Das dürfen nur der Gildenchef und die Offiziere."


@recurring_group.command(name="anlegen", description="Festen Wochentermin anlegen – der Bot erstellt die Raids selbst")
@app_commands.describe(raid="Welcher Raid?", wochentag="Wochentag", uhrzeit="HH:MM (Zeit in der Schweiz), z. B. 20:00",
                       wochen_voraus="so viele Wochen im Voraus anlegen (1–4, Standard 2)",
                       titel="optional, Standard: Raidname + Wochentag", beschreibung="optional, z. B. Treffpunkt",
                       max_spieler="optional, 0 = unbegrenzt", tanks="Plätze je Rolle (optional, 0 = keine Grenze)",
                       heiler="Plätze je Rolle (optional)", nahkampf="Plätze je Rolle (optional)",
                       fernkampf="Plätze je Rolle (optional)")
@app_commands.choices(wochentag=DAY_CHOICES)
@app_commands.autocomplete(raid=raid_pool_autocomplete)
async def recurring_add(inter: discord.Interaction, raid: str, wochentag: app_commands.Choice[int], uhrzeit: str,
                        wochen_voraus: app_commands.Range[int, 1, 4] = 2, titel: str | None = None,
                        beschreibung: str | None = None, max_spieler: app_commands.Range[int, 0, 40] = 0,
                        tanks: app_commands.Range[int, 0, 40] | None = None,
                        heiler: app_commands.Range[int, 0, 40] | None = None,
                        nahkampf: app_commands.Range[int, 0, 40] | None = None,
                        fernkampf: app_commands.Range[int, 0, 40] | None = None):
    if not is_creator(inter.user):
        await inter.response.send_message(NO_RIGHTS, ephemeral=True)
        return
    names = dict(known_raids())
    if raid not in names:
        await inter.response.send_message("Diesen Raid kenne ich nicht – bitte aus der Liste wählen.", ephemeral=True)
        return
    try:
        hhmm = wk.parse_time(uhrzeit)
    except ValueError:
        await inter.response.send_message("Uhrzeit bitte als HH:MM, z. B. `20:00`.", ephemeral=True)
        return
    if not server_setup.raid_released(raid, cfg):
        await inter.response.send_message(f"**{names[raid]}** ist für WoW Forever noch nicht angekündigt.", ephemeral=True)
        return
    if any(t["pool"] == raid and t["weekday"] == wochentag.value and t["time"] == hhmm for t in templates()):
        await inter.response.send_message("Diesen Wochentermin gibt es schon (`/raid wiederkehrend liste`).", ephemeral=True)
        return
    limits = {r: v for r, v in (("tank", tanks), ("heal", heiler), ("melee", nahkampf), ("ranged", fernkampf)) if v}
    number = int(state.data.get("recurring_next") or 1)
    state.data["recurring_next"] = number + 1
    tpl = {"id": number, "pool": raid, "title": (titel or f"{names[raid]} {wk.WEEKDAYS[wochentag.value]}")[:80],
           "weekday": wochentag.value, "time": hhmm, "weeks": wochen_voraus, "description": (beschreibung or "")[:500],
           "max": max_spieler, "limits": limits, "paused": False, "creator": inter.user.id, "done": []}
    templates().append(tpl)
    state.save()
    # Termine anlegen kann dauern (Discord wartet nur 3 s auf die erste Antwort)
    await inter.response.defer(ephemeral=True, thinking=True)
    made = await run_recurring(only=tpl)
    opens = server_setup.raid_opens(raid)
    text = f"🔁 Wochentermin **#{number}** eingetragen: {wk.describe(tpl, names[raid])}."
    if opens and opens > now_local().date():
        text += f" Erste Termine ab Öffnung am {opens:%d.%m.%Y}."
    text += f" Jetzt angelegt: {made} Raid{'s' if made != 1 else ''}."
    await inter.followup.send(text, ephemeral=True)


@recurring_group.command(name="liste", description="Alle festen Wochentermine (Offiziere)")
async def recurring_list(inter: discord.Interaction):
    if not is_creator(inter.user):
        await inter.response.send_message(NO_RIGHTS, ephemeral=True)
        return
    if not templates():
        await inter.response.send_message("Keine festen Wochentermine. Anlegen: `/raid wiederkehrend anlegen`.",
                                          ephemeral=True)
        return
    names = dict(known_raids())
    lines = []
    for t in templates():
        line = f"**#{t['id']}** {t['title']} – {wk.describe(t, names.get(t['pool'], t['pool']))}"
        if t.get("limits"):
            line += " · Plätze: " + ", ".join(f"{rmd.ROLES.get(k, k)} {v}" for k, v in t["limits"].items())
        if t.get("paused"):
            line += " · ⏸️ pausiert"
        lines.append(line)
    text = "\n".join(lines)
    await inter.response.send_message(text[:1990], ephemeral=True)


@recurring_group.command(name="pausieren", description="Wochentermin pausieren oder wieder starten (Offiziere)")
@app_commands.describe(nummer="Nummer aus /raid wiederkehrend liste")
async def recurring_pause(inter: discord.Interaction, nummer: int):
    if not is_creator(inter.user):
        await inter.response.send_message(NO_RIGHTS, ephemeral=True)
        return
    t = find(nummer)
    if t is None:
        await inter.response.send_message("Diese Nummer gibt es nicht.", ephemeral=True)
        return
    t["paused"] = not t.get("paused")
    state.save()
    if t["paused"]:
        await inter.response.send_message(f"⏸️ #{nummer} pausiert – es werden keine neuen Termine angelegt. "
                                          "Schon angelegte Raids bleiben.", ephemeral=True)
    else:
        await inter.response.defer(ephemeral=True, thinking=True)
        made = await run_recurring(only=t)
        await inter.followup.send(f"▶️ #{nummer} läuft wieder. Jetzt angelegt: {made}.", ephemeral=True)


@recurring_group.command(name="loeschen", description="Wochentermin löschen (Offiziere) – angelegte Raids bleiben")
@app_commands.describe(nummer="Nummer aus /raid wiederkehrend liste")
async def recurring_delete(inter: discord.Interaction, nummer: int):
    if not is_creator(inter.user):
        await inter.response.send_message(NO_RIGHTS, ephemeral=True)
        return
    t = find(nummer)
    if t is None:
        await inter.response.send_message("Diese Nummer gibt es nicht.", ephemeral=True)
        return
    templates().remove(t)
    state.save()
    await inter.response.send_message(f"🗑️ Wochentermin #{nummer} gelöscht. Schon angelegte Raids bleiben – absagen mit "
                                      "`/raid absagen`.", ephemeral=True)
