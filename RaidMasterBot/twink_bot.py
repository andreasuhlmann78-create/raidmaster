"""Twinks (D-3 Schritt 24, ab Bot 1.5.171): weitere Charaktere eines Discord-Mitglieds – /twink hinzufügen|
entfernen|wechseln|liste; Anmeldungen des Mitglieds werden danach aktualisiert ("Main vor Twink" im Addon).

UNVERÄNDERT aus bot.py verschoben: der ganze Abschnitt "Twinks" samt bot.tree.add_command(twink_group).
bot.py importiert dieses Modul nach "grund.bot = bot" (/twink wird beim Import angemeldet).
Weg A (Antwort der Prüf-Sitzung 15.11. 20:48).
"""
from __future__ import annotations

import discord
from discord import app_commands

import grund
import raidmaster_data as rmd
from kern import book
from raidanzeige_bot import update_raid_message

bot = grund.bot
assert bot is not None, "twink_bot erst nach grund.bot = bot importieren"


# ---------------------------------------------------------------------------
# Twinks: weitere Charaktere eines Discord-Mitglieds (Anmeldung, "Main vor Twink" im Addon)
# ---------------------------------------------------------------------------
twink_group = app_commands.Group(name="twink", description="Twinks (weitere Charaktere) verwalten")
CLASS_CHOICES = [app_commands.Choice(name=v, value=k) for k, v in rmd.CLASSES.items()][:25]
ROLE_CHOICES = [app_commands.Choice(name=v, value=k) for k, v in rmd.ROLES.items()]


async def own_char_autocomplete(inter: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    return [app_commands.Choice(name=c["name"] + (" (Main)" if c["main"] else " (Twink)"), value=c["name"])
            for c in book.characters(inter.user.id) if current.lower() in c["name"].lower()][:25]


async def refresh_signups_of(user_id: int):
    for r in book.open_raids():
        if str(user_id) in r["signups"]:
            await update_raid_message(r)


@twink_group.command(name="hinzufügen", description="Twink anlegen (Name wie im Spiel)")
@app_commands.describe(name="Charaktername des Twinks", klasse="Klasse", rolle="Rolle")
@app_commands.choices(klasse=CLASS_CHOICES, rolle=ROLE_CHOICES)
async def twink_add(inter: discord.Interaction, name: str, klasse: app_commands.Choice[str], rolle: app_commands.Choice[str]):
    if not book.profile(inter.user.id):
        await inter.response.send_message("Lege zuerst deinen Main an (`/charakter` oder beim Raid „Charakter registrieren“).", ephemeral=True)
        return
    clean = rmd.clean_name(name)
    if not clean.isalpha():
        await inter.response.send_message("Der Name darf nur Buchstaben enthalten.", ephemeral=True)
        return
    p = book.add_alt(inter.user.id, clean, klasse.value, rolle.value)
    await inter.response.send_message(f"Twink **{clean}** ({klasse.name}, {rolle.name}) gespeichert – Main ist **{p.get('main')}**.\n"
                                      "Mit `/twink wechseln` meldest du dich mit ihm an. Im Spiel gilt „Main vor Twink“.", ephemeral=True)


@twink_group.command(name="entfernen", description="Twink löschen")
@app_commands.autocomplete(name=own_char_autocomplete)
async def twink_remove(inter: discord.Interaction, name: str):
    ok = book.remove_alt(inter.user.id, name)
    await inter.response.send_message(f"Twink **{name}** entfernt." if ok else "Diesen Twink gibt es nicht.", ephemeral=True)
    await refresh_signups_of(inter.user.id)


@twink_group.command(name="wechseln", description="Mit welchem Charakter meldest du dich an? (Main oder Twink)")
@app_commands.autocomplete(name=own_char_autocomplete)
async def twink_switch(inter: discord.Interaction, name: str):
    p = book.switch_char(inter.user.id, name)
    if not p:
        await inter.response.send_message("Diesen Charakter gibt es in deinem Profil nicht (`/twink liste`).", ephemeral=True)
        return
    is_twink = p["name"].lower() != (p.get("main") or p["name"]).lower()
    await inter.response.send_message(f"Du meldest dich jetzt mit **{p['name']}** an" + (f" (Twink von {p['main']})." if is_twink else " (Main)."),
                                      ephemeral=True)


@twink_group.command(name="liste", description="Deine Charaktere (Main und Twinks)")
async def twink_list(inter: discord.Interaction):
    chars = book.characters(inter.user.id)
    if not chars:
        await inter.response.send_message("Noch kein Profil – `/charakter`.", ephemeral=True)
        return
    active = (book.profile(inter.user.id) or {}).get("name", "")
    lines = [f"{'⭐' if c['main'] else '↳'} **{c['name']}** · {rmd.CLASSES.get(c['cls'], c['cls'])} · {rmd.ROLES.get(c['role'], c['role'])}"
             + (" · *aktiv*" if c["name"].lower() == active.lower() else "") for c in chars]
    await inter.response.send_message("\n".join(lines), ephemeral=True)


bot.tree.add_command(twink_group)
