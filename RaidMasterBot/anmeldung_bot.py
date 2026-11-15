"""Anmeldung (D-3 Schritt 33, ab Bot 1.5.180): Knöpfe an den Raid-Nachrichten (an, Ersatzbank, vielleicht, ab,
Export, Tooltip, Ersatz, Bewerbung, Gildenname – funktionieren auch nach einem Neustart), Charakterprofil
(Klasse, Rolle, Name) per Formular, /charakter, PUG- und Raid-Registrierung, Hinweis auf das Addon RaidMaster.

UNVERÄNDERT aus bot.py verschoben (samt Kommentaren direkt darüber): addon_hint, NameModal, ProfileView,
register_pug_player, register_raid_player, on_interaction (@bot.event – meldet sich beim Import am selben
Bot-Objekt an), character_cmd. Weg A (Antwort der Prüf-Sitzung 15.11. 20:48).
"""
from __future__ import annotations

import asyncio
import time

import discord

import grund
import raidmaster_data as rmd
import server_setup
from beutepost_bot import show_tip
from bot_hilfen import profile_text, raid_view, status_text
from ersatz_bot import accept_substitute, offer_substitute
from gildenname_bot import handle_name_button
from grund import bot_guild
from kern import book, log
from klassen_bot import sync_class_roles
from mitglieder_bot import handle_apply_button
from raid_bot import send_export
from raidanzeige_bot import raid_embed, update_raid_message

bot = grund.bot
assert bot is not None, "anmeldung_bot erst nach grund.bot = bot importieren"


def addon_hint(raid: dict | None, actual: str) -> str:
    """Hinweis bei der Anmeldung zu einem Gilden-Raid (ab 1.5.117, Wunsch des Nutzers 12.11.): RaidMaster ist Pflicht."""
    if not raid or raid.get("mode") == "pug" or actual not in ("an", "ersatz", "vielleicht"):
        return ""
    guild = bot_guild()
    ch = server_setup.find_channel(guild.text_channels, "raid-addon") if guild is not None else None
    where = ch.mention if ch is not None else "#raid-addon"
    return ("\n\n📦 **Pflicht für Gilden-Raids:** das Addon **RaidMaster** (Download in " + where +
            "). Bitte vor dem Raid installieren bzw. auf die neueste Version bringen.")


class NameModal(discord.ui.Modal):
    def __init__(self, pv: "ProfileView"):
        super().__init__(title="Dein Charakter")
        self.pv = pv
        self.name_input = discord.ui.TextInput(label="Charaktername (wie im Spiel)", min_length=2, max_length=12,
                                               default=pv.name or None, placeholder="z. B. Andi")
        self.add_item(self.name_input)

    async def on_submit(self, inter: discord.Interaction):
        pv = self.pv
        name = rmd.clean_name(self.name_input.value)
        if not name.isalpha():
            await inter.response.send_message("Der Name darf nur Buchstaben enthalten.", ephemeral=True)
            return
        profile = book.set_profile(inter.user.id, name, pv.cls, pv.role)
        text = "Gespeichert: " + profile_text(profile) + "."
        if isinstance(inter.user, discord.Member):
            try:
                await sync_class_roles(only=[inter.user])
            except Exception:  # noqa: BLE001
                log.exception("Klassenfarbe konnte nicht gesetzt werden")
        raid = book.get(pv.raid_id) if pv.raid_id else None
        if raid and pv.status and not raid.get("closed"):
            actual = book.signup(raid, inter.user.id, pv.status, profile, int(time.time()))
            text += "\n" + status_text(actual, pv.status) + addon_hint(raid, actual)
        await inter.response.send_message(text, ephemeral=True)
        # alle offenen Raids mit dieser Anmeldung aktualisieren
        for r in book.open_raids():
            if str(inter.user.id) in r["signups"]:
                await update_raid_message(r)


class ProfileView(discord.ui.View):
    def __init__(self, raid_id: str, status: str | None, preset: dict | None = None):
        super().__init__(timeout=600)
        self.raid_id = raid_id
        self.status = status
        self.cls = preset["cls"] if preset else None
        self.role = preset["role"] if preset else None
        self.name = preset["name"] if preset else None

        cls_select = discord.ui.Select(
            placeholder="Klasse wählen",
            options=[discord.SelectOption(label=v, value=k, default=(k == self.cls)) for k, v in rmd.CLASSES.items()],
            row=0,
        )
        cls_select.callback = self.on_class
        self.add_item(cls_select)

        role_select = discord.ui.Select(
            placeholder="Rolle wählen",
            options=[discord.SelectOption(label=v, value=k, emoji=rmd.ROLE_ICONS[k], default=(k == self.role)) for k, v in rmd.ROLES.items()],
            row=1,
        )
        role_select.callback = self.on_role
        self.add_item(role_select)

        btn = discord.ui.Button(label="Name eingeben und speichern", style=discord.ButtonStyle.primary, row=2)
        btn.callback = self.on_name
        self.add_item(btn)

    async def on_class(self, inter: discord.Interaction):
        self.cls = (inter.data or {}).get("values", [None])[0]
        await inter.response.defer()

    async def on_role(self, inter: discord.Interaction):
        self.role = (inter.data or {}).get("values", [None])[0]
        await inter.response.defer()

    async def on_name(self, inter: discord.Interaction):
        if not self.cls or not self.role:
            await inter.response.send_message("Bitte zuerst **Klasse** und **Rolle** wählen.", ephemeral=True)
            return
        await inter.response.send_modal(NameModal(self))


async def register_pug_player(inter: discord.Interaction):
    """Knopf 'Als PUG-Spieler registrieren': Rolle Gast + Charakterprofil."""
    note = ""
    role = discord.utils.get(inter.guild.roles, name="Gast") if inter.guild else None
    member_roles = {r.name for r in getattr(inter.user, "roles", [])}
    if member_roles & {"Raider", "Offizier", "Raidleitung"}:
        role = None   # Gildenmitglieder nicht zu Gästen machen – sie würden sonst nur noch PUG sehen
    if role and isinstance(inter.user, discord.Member) and role not in inter.user.roles:
        try:
            await inter.user.add_roles(role, reason="PUG-Registrierung")
            note = "Du hast die Rolle **Gast** und wirst bei neuen PUG-Raids benachrichtigt.\n"
        except discord.HTTPException:
            note = ""
    await inter.response.send_message(
        note + "Wähle jetzt Klasse und Rolle und gib deinen Charakternamen ein – danach kannst du dich mit einem Klick "
        "für PUG-Raids anmelden.",
        view=ProfileView("", None, book.profile(inter.user.id)), ephemeral=True)


async def register_raid_player(inter: discord.Interaction, key: str):
    """Knopf 'Charakter registrieren' in der Anmeldung eines Raids (Gildenspieler)."""
    name = rmd.pool_name(key, bot.dkp_data) if key else "Raids"
    profile = book.profile(inter.user.id)
    intro = (f"Du bist schon registriert: {profile_text(profile)}.\nHier kannst du Klasse, Rolle oder Charakter ändern."
             if profile else
             f"Willkommen bei **{name}**! Wähle Klasse und Rolle und gib deinen Charakternamen ein – danach meldest "
             "du dich bei jedem Raid mit einem Klick an.")
    await inter.response.send_message(intro, view=ProfileView("", None, profile), ephemeral=True)


@bot.event
async def on_interaction(inter: discord.Interaction):
    if inter.type != discord.InteractionType.component:
        return
    cid = (inter.data or {}).get("custom_id", "")
    if cid.startswith("rmtip:"):
        try:
            await show_tip(inter)
        except Exception:  # noqa: BLE001
            log.exception("Tooltip konnte nicht angezeigt werden")
            try:
                await inter.followup.send("Der Tooltip konnte gerade nicht geladen werden – bitte gleich nochmal versuchen.", ephemeral=True)
            except Exception:  # noqa: BLE001
                pass
        return
    if cid.startswith("rmname:"):
        try:
            _, action, pid = cid.split(":", 2)
            await handle_name_button(inter, action, pid)
        except Exception:  # noqa: BLE001
            log.exception("Fehler bei Knopf %s", cid)
            try:
                if not inter.response.is_done():
                    await inter.response.send_message("Da ist etwas schiefgelaufen. Bitte erneut versuchen.", ephemeral=True)
            except discord.HTTPException:
                pass
        return
    if cid.startswith("rmapply:"):
        try:
            _, action, arg = cid.split(":", 2)
            await handle_apply_button(inter, action, arg)
        except Exception:  # noqa: BLE001
            log.exception("Fehler bei Knopf %s", cid)
            try:
                if not inter.response.is_done():
                    await inter.response.send_message("Da ist etwas schiefgelaufen. Bitte erneut versuchen.", ephemeral=True)
            except discord.HTTPException:
                pass
        return
    if not cid.startswith("rm:"):
        return
    try:
        _, action, rid = cid.split(":", 2)
        if action == "pugreg":
            await register_pug_player(inter)
            return
        if action == "raidreg":
            await register_raid_player(inter, rid)
            return
        raid = book.get(rid)
        if not raid:
            await inter.response.send_message("Diesen Raid gibt es nicht mehr.", ephemeral=True)
            return

        if action == "export":
            await send_export(inter, raid)
            return

        if action == "sub":
            await accept_substitute(inter, raid)
            return

        profile = book.profile(inter.user.id)

        if action == "sr":
            # Knopf älterer Raid-Nachrichten
            await inter.response.send_message("Soft Reserve läuft jetzt über softres.it – den Link findest du direkt am Raid.", ephemeral=True)
            await update_raid_message(raid)
            return

        if action == "char":
            await inter.response.send_message(
                "Wähle Klasse und Rolle und gib dann deinen Charakternamen ein.",
                view=ProfileView(rid, None, profile), ephemeral=True)
            return

        if action not in rmd.STATUS:
            return
        if raid.get("closed"):
            await inter.response.send_message("Die Anmeldung für diesen Raid ist geschlossen.", ephemeral=True)
            return

        if not profile:
            await inter.response.send_message(
                "Einmalig: Wähle **Klasse** und **Rolle** und gib dann deinen **Charakternamen** ein. "
                "Danach reicht künftig ein Klick.",
                view=ProfileView(rid, action, None), ephemeral=True)
            return

        before = (raid["signups"].get(str(inter.user.id)) or {}).get("status")
        actual = book.signup(raid, inter.user.id, action, profile, int(time.time()))
        await inter.response.edit_message(embed=raid_embed(raid), view=raid_view(raid))
        if before == "an" and actual in ("ab", "vielleicht"):
            asyncio.create_task(offer_substitute(raid, profile))
        await inter.followup.send(f"{status_text(actual, action)}\nCharakter: {profile_text(profile)}" + addon_hint(raid, actual),
                                  ephemeral=True)
    except Exception:
        log.exception("Fehler bei Knopf %s", cid)
        try:
            if not inter.response.is_done():
                await inter.response.send_message("Da ist etwas schiefgelaufen. Bitte erneut versuchen.", ephemeral=True)
        except discord.HTTPException:
            pass


@bot.tree.command(name="charakter", description="Deinen Charakter (Name, Klasse, Rolle) festlegen")
async def character_cmd(inter: discord.Interaction):
    await inter.response.send_message("Wähle Klasse und Rolle und gib dann deinen Charakternamen ein.",
                                      view=ProfileView("", None, book.profile(inter.user.id)), ephemeral=True)
