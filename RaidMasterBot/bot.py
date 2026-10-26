"""
RaidMaster-Bot für Discord
- Raidanmeldungen mit Knöpfen (Anmelden, Ersatzbank, Vielleicht, Abmelden)
- Charakterprofil (Name, Klasse, Rolle) – einmal eingeben, danach ein Klick
- Erinnerung vor dem Raid
- Export-Text für das WoW-Addon RaidMaster (Einladungen, Abgleich)
- DKP-Tabelle und Loot-Protokoll aus der RaidMaster-Datei des Raidleiters
- /dkp zum Abfragen des eigenen Standes
- Skillungen aus dem Addon in den Profilen
- Läuft 24/7 auf einem Server: Daten kommen per Uploader vom PC der Raidleitung,
  Updates installiert der Bot selbst (GitHub oder /update)

Start: python launcher.py   (Einstellungen in config.json)
"""

from __future__ import annotations

import asyncio
import gzip
import io
import json
import logging
import os
import shutil
import sys
import re
import time
import zipfile
import zlib
from datetime import datetime
from zoneinfo import ZoneInfo

import discord
from discord import app_commands
from discord.ext import tasks

import raidmaster_data as rmd
import render as rimg
import server_setup
import mc_tactics
import updater

BASE = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE, "config.json")
DATA_DIR = os.path.join(BASE, "data")

log = logging.getLogger("raidmaster")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")

ORANGE = 0xFF8C1A
GREY = 0x555555

# ---------------------------------------------------------------------------
# Einstellungen
# ---------------------------------------------------------------------------

DEFAULT_CONFIG = {
    "token": "",
    "guild_id": 0,
    "timezone": "Europe/Zurich",
    "raid_creator_roles": ["Offizier", "Raidleitung"],
    "reminder_minutes": 60,
    "close_after_hours": 6,
    "savedvariables_path": "",
    "dkp_channel_id": 0,
    "dkp_channels": {},
    "loot_channel_id": 0,
    "assignment_channel_id": 0,
    "officer_channel_id": 0,
    "addon_channel_id": 0,
    "announce_channel_id": 0,
    "pug_channel_id": 0,
    "raid_channels": {},
    "auto_raid_categories": True,
    "notify_addon_updates": True,
    "notify_spec_changes": True,
    "send_assignment_dms": True,
    "data_channel_id": 0,
    "botcmd_channel_id": 0,
    "uploader_webhooks": [],
    "update_repo": "",
    "update_branch": "main",
    "update_token": "",
    "update_check_minutes": 30,
    "backup_days": 7,
    "message_content_intent": False,
    "guild_name": "test",
    "welcome_channel_id": 0,
    "command_list_channel_id": 0,
    "pug_invite_code": "",
    "pug_invite_url": "",
}

CONFIG_ERROR = 3   # launcher.py startet dann nicht neu


def load_config() -> dict:
    if not os.path.isfile(CONFIG_PATH):
        example = os.path.join(BASE, "config.example.json")
        if os.path.isfile(example):
            shutil.copy(example, CONFIG_PATH)
        print("Bitte zuerst config.json ausfüllen (Token, Server-ID usw.) – siehe ANLEITUNG.md")
        sys.exit(CONFIG_ERROR)
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    for k, v in DEFAULT_CONFIG.items():
        cfg.setdefault(k, v)
    if not cfg["token"] or "HIER" in cfg["token"]:
        print("In config.json fehlt der Bot-Token – siehe ANLEITUNG.md")
        sys.exit(CONFIG_ERROR)
    return cfg


def save_config():
    """Schreibt die aktuellen Einstellungen zurück in config.json."""
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


cfg = load_config()
TZ = cfg["timezone"]
book = rmd.RaidBook(DATA_DIR)
state = rmd.Store(os.path.join(DATA_DIR, "state.json"), {"dkp_messages": {}, "last_loot": None, "assign_v": 0,
                                                        "addon_version": "", "addon_message": None})
for _k, _v in {"installed_sha": "", "failed_sha": "", "last_backup": 0, "last_upload": 0, "last_upload_by": ""}.items():
    state.data.setdefault(_k, _v)
UPLOAD_PATH = os.path.join(DATA_DIR, "RaidMaster.lua")
# eigene Beute-Datenbank (aus den Lootfenstern der Bosskills aller Uploader)
lootdb = rmd.Store(os.path.join(DATA_DIR, "loot_db.json"), rmd.lootdb_empty())
for _k, _v in rmd.lootdb_empty().items():
    lootdb.data.setdefault(_k, _v)
EXIT_CODE = 0
if isinstance(state.data.get("dkp_messages"), list):
    # älteres Format: eine Tabelle -> gehört zu Molten Core
    state.data["dkp_messages"] = {"mc": state.data["dkp_messages"]}

# ---------------------------------------------------------------------------
# Bot
# ---------------------------------------------------------------------------


class RaidBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        # nur nötig, falls Uploads trotz Erwähnung des Bots ohne Anhang ankommen (siehe ANLEITUNG)
        intents.message_content = bool(cfg.get("message_content_intent", False))
        # Beitritte erkennen (PUG-Einladungslink -> Rolle Gast); braucht den "Server Members Intent"
        intents.members = not state.data.get("members_intent_missing", False)
        intents.invites = True
        super().__init__(intents=intents)
        self.invite_uses: dict[str, int] = {}
        self.tree = app_commands.CommandTree(self)
        self.dkp_data = None
        self.dkp_db = None
        self.dkp_rows: list[dict] = []
        self.dkp_mtime = 0.0

    async def setup_hook(self):
        if cfg.get("guild_id"):
            guild = discord.Object(id=int(cfg["guild_id"]))
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            log.info("Befehle für den Server synchronisiert.")
        else:
            await self.tree.sync()
            log.info("Befehle global synchronisiert (kann bis zu 1 Stunde dauern). Tipp: guild_id eintragen.")
        reminder_loop.start()
        dkp_loop.start()
        update_loop.change_interval(minutes=max(5, int(cfg.get("update_check_minutes") or 30)))
        update_loop.start()
        backup_loop.start()
        test_cleanup_loop.start()

    async def on_ready(self):
        log.info("Angemeldet als %s – bereit (Version %s).", self.user, updater.bot_version(BASE))
        if not getattr(self, "_release_checked", False):
            self._release_checked = True
            try:
                await report_update_result()
            except Exception:
                log.exception("Update-Meldung fehlgeschlagen")
            try:
                await check_addon_release()
            except Exception:
                log.exception("Prüfung der Addon-Version fehlgeschlagen")
            try:
                made = await ensure_listed_raid_categories()
                if made:
                    await post_bot_log("🆕 Raid-Kategorien angelegt: " + ", ".join(made) + " (Anmeldung, Sprachkanal, Taktik, DKP, Loot).")
            except Exception:
                log.exception("Raid-Kategorien konnten nicht angelegt werden")
            try:
                rep = await ensure_guild_rules()
                if rep:
                    log.info("Gildenregeln: %s", "; ".join(rep))
                    await post_bot_log("📜 Gildenregeln: " + "; ".join(rep))
            except Exception:
                log.exception("Gildenregeln konnten nicht angelegt werden")
            try:
                await sync_class_roles()
            except Exception:
                log.exception("Klassenfarben konnten nicht gesetzt werden")
            try:
                report = await post_all_tactics()
                if report:
                    log.info("Taktiken: %s", "; ".join(report))
            except Exception:
                log.exception("Taktiken konnten nicht gepostet werden")
            try:
                await ensure_welcome(update=False)
            except Exception:
                log.exception("Willkommenstext konnte nicht gepostet werden")
            try:
                await ensure_command_list()
            except Exception:
                log.exception("Befehlsliste konnte nicht gepostet werden")
            # offene Raid-Nachrichten auf den aktuellen Stand bringen (z. B. Knöpfe nach einem Update)
            for r in book.open_raids():
                try:
                    await update_raid_message(r)
                except Exception:
                    log.exception("Raid-Nachricht %s konnte nicht aktualisiert werden", r.get("id"))
        await refresh_invite_cache()

    async def on_invite_create(self, invite):
        await refresh_invite_cache()

    async def on_invite_delete(self, invite):
        await refresh_invite_cache()

    async def on_member_join(self, member):
        try:
            await handle_member_join(member)
        except Exception:
            log.exception("Beitritt konnte nicht verarbeitet werden")

    async def on_message(self, message: discord.Message):
        if cfg.get("data_channel_id") and message.channel.id == int(cfg["data_channel_id"]) and message.webhook_id:
            try:
                await receive_upload(message)
            except Exception:
                log.exception("Upload konnte nicht verarbeitet werden")


bot = RaidBot()

# ---------------------------------------------------------------------------
# Hilfen
# ---------------------------------------------------------------------------


def is_creator(member) -> bool:
    if not isinstance(member, discord.Member):
        return False
    perms = member.guild_permissions
    if perms.administrator or perms.manage_guild:
        return True
    allowed = {r.lower() for r in cfg.get("raid_creator_roles", [])}
    return any(role.name.lower() in allowed for role in member.roles)


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


def raid_view(raid: dict) -> discord.ui.View:
    v = discord.ui.View(timeout=None)
    closed = bool(raid.get("closed"))
    rid = raid["id"]
    v.add_item(discord.ui.Button(label="Anmelden", emoji="✅", style=discord.ButtonStyle.success, custom_id=f"rm:an:{rid}", disabled=closed, row=0))
    v.add_item(discord.ui.Button(label="Ersatzbank", emoji="🪑", style=discord.ButtonStyle.secondary, custom_id=f"rm:ersatz:{rid}", disabled=closed, row=0))
    v.add_item(discord.ui.Button(label="Vielleicht", emoji="❔", style=discord.ButtonStyle.secondary, custom_id=f"rm:vielleicht:{rid}", disabled=closed, row=0))
    v.add_item(discord.ui.Button(label="Abmelden", emoji="❌", style=discord.ButtonStyle.danger, custom_id=f"rm:ab:{rid}", disabled=closed, row=0))
    v.add_item(discord.ui.Button(label="Charakter ändern", emoji="👤", style=discord.ButtonStyle.secondary, custom_id=f"rm:char:{rid}", row=1))
    v.add_item(discord.ui.Button(label="Für RaidMaster (Offiziere)", emoji="📋", style=discord.ButtonStyle.primary, custom_id=f"rm:export:{rid}", row=1))
    return v


async def update_raid_message(raid: dict):
    if raid.get("message_id"):
        try:
            channel = bot.get_channel(raid["channel_id"]) or await bot.fetch_channel(raid["channel_id"])
            await channel.get_partial_message(raid["message_id"]).edit(embed=raid_embed(raid), view=raid_view(raid))
        except discord.HTTPException as e:
            log.warning("Raid-Nachricht %s konnte nicht aktualisiert werden: %s", raid["id"], e)


def status_text(actual: str, wanted: str) -> str:
    if actual != wanted and actual == "ersatz":
        return "Der Raid ist voll – du stehst auf der **Ersatzbank**."
    return {
        "an": "Du bist **angemeldet**. ✅",
        "ersatz": "Du stehst auf der **Ersatzbank**. 🪑",
        "vielleicht": "Du bist als **vielleicht** eingetragen. ❔",
        "ab": "Du bist **abgemeldet**. ❌",
    }.get(actual, "")


def profile_text(p: dict) -> str:
    text = f"**{p['name']}** ({rmd.CLASSES.get(p['cls'], p['cls'])}, {rmd.ROLES.get(p['role'], p['role'])})"
    spec = p.get("spec")
    if spec:
        text += f" · Skillung **{spec['label']}**" + (f" ({spec['points']})" if spec.get("points") else "")
    return text


async def send_export(inter: discord.Interaction, raid: dict):
    if not is_creator(inter.user):
        await inter.response.send_message("Den Export dürfen nur Offiziere bzw. die Raidleitung abrufen.", ephemeral=True)
        return
    lineup = None
    if raid["signups"]:
        att, _, _ = rmd.attendance(bot.dkp_data, book)
        lineup = rmd.build_lineup(raid, att)
    link = cfg.get("pug_invite_url", "") if raid.get("mode") == "pug" else ""
    text = rmd.export_text(raid, TZ, lineup, link, raid.get("softres", ""))
    intro = ("Diesen Text kopieren und im Spiel bei **RaidMaster → Anmeldungen → Importieren** einfügen. "
             "Enthält Aufstellung und feste Gruppen – das Addon lädt automatisch ein und sortiert die Gruppen.")
    if len(text) < 1800:
        await inter.response.send_message(f"{intro}\n```\n{text}\n```", ephemeral=True)
    else:
        file = discord.File(io.BytesIO(text.encode("utf-8")), filename=f"raid_{raid['id']}_anmeldungen.txt")
        await inter.response.send_message(intro + " (Liste ist lang – als Datei angehängt.)", file=file, ephemeral=True)


# ---------------------------------------------------------------------------
# Charakterprofil (Klasse, Rolle, Name)
# ---------------------------------------------------------------------------


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
            text += "\n" + status_text(actual, pv.status)
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


# ---------------------------------------------------------------------------
# Knöpfe an den Raid-Nachrichten (funktionieren auch nach Neustart)
# ---------------------------------------------------------------------------


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

        actual = book.signup(raid, inter.user.id, action, profile, int(time.time()))
        await inter.response.edit_message(embed=raid_embed(raid), view=raid_view(raid))
        await inter.followup.send(f"{status_text(actual, action)}\nCharakter: {profile_text(profile)}", ephemeral=True)
    except Exception:
        log.exception("Fehler bei Knopf %s", cid)
        try:
            if not inter.response.is_done():
                await inter.response.send_message("Da ist etwas schiefgelaufen. Bitte erneut versuchen.", ephemeral=True)
        except discord.HTTPException:
            pass


# ---------------------------------------------------------------------------
# Befehle: /raid ...
# ---------------------------------------------------------------------------

raid_group = app_commands.Group(name="raid", description="Raidanmeldungen verwalten")


async def raid_autocomplete(inter: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    out = []
    for r in sorted(book.all(), key=lambda r: -r["start"]):
        start = datetime.fromtimestamp(r["start"], ZoneInfo(TZ)).strftime("%d.%m. %H:%M")
        label = f"#{r['id']} {r['title']} – {start}" + (" (geschlossen)" if r.get("closed") else "")
        if current.lower() in label.lower():
            out.append(app_commands.Choice(name=label[:100], value=r["id"]))
        if len(out) >= 20:
            break
    return out


def known_raids() -> list[tuple[str, str]]:
    """Alle Raids: feste Liste, im Addon erkannte und in Discord angelegte."""
    keys = rmd.pool_list(bot.dkp_data or {})
    for k in (cfg.get("raid_channels") or {}):
        if k not in keys:
            keys.append(k)
    names = cfg.get("raid_names") or {}
    return [(k, names.get(k) or rmd.pool_name(k, bot.dkp_data)) for k in keys]


async def raid_pool_autocomplete(inter: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    return [app_commands.Choice(name=n, value=k) for k, n in known_raids() if current.lower() in n.lower()][:20]


def raid_channel(pool: str, kind: str) -> int:
    return int(((cfg.get("raid_channels") or {}).get(pool) or {}).get(kind) or 0)


@raid_group.command(name="erstellen", description="Neuen Raid zur Anmeldung erstellen")
@app_commands.describe(titel="z. B. Molten Core Mittwoch", datum="TT.MM.JJJJ, z. B. 29.10.2026", uhrzeit="HH:MM, z. B. 20:00",
                       raid="Welcher Raid? (bestimmt Kategorie und DKP-Topf, Standard Molten Core)",
                       beschreibung="optional, z. B. Treffpunkt und Buffs", max_spieler="optional, z. B. 40 (0 = unbegrenzt)",
                       modus="DKP-Raid (Gilde) oder PUG-Raid (Loot über softres.it)",
                       softres="PUG: Link zum softres.it-Raid (kann auch später mit /raid softres gesetzt werden)")
@app_commands.choices(modus=[app_commands.Choice(name="DKP-Raid (Gilde)", value="dkp"),
                             app_commands.Choice(name="PUG-Raid (softres.it)", value="pug")])
@app_commands.autocomplete(raid=raid_pool_autocomplete)
async def raid_create(inter: discord.Interaction, titel: str, datum: str, uhrzeit: str, raid: str = "mc",
                      beschreibung: str | None = None, max_spieler: app_commands.Range[int, 0, 40] = 0,
                      modus: app_commands.Choice[str] | None = None, softres: str | None = None):
    pool = raid
    if not is_creator(inter.user):
        await inter.response.send_message("Raids erstellen dürfen nur Offiziere bzw. die Raidleitung.", ephemeral=True)
        return
    try:
        start = rmd.parse_datetime(datum, uhrzeit, TZ)
    except ValueError:
        await inter.response.send_message("Datum oder Uhrzeit nicht erkannt. Beispiel: Datum `29.10.2026`, Uhrzeit `20:00`.", ephemeral=True)
        return
    if start.timestamp() < time.time():
        await inter.response.send_message("Dieser Zeitpunkt liegt in der Vergangenheit.", ephemeral=True)
        return
    mode = modus.value if modus else "dkp"
    softres_link = clean_softres(softres)
    if softres and not softres_link:
        await inter.response.send_message("Das ist kein softres.it-Link. Beispiel: `https://softres.it/raid/abcd`", ephemeral=True)
        return
    # Zielkanal: Anmeldung der Raid-Kategorie bzw. #pug-anmeldung
    target_id = cfg.get("pug_channel_id") if mode == "pug" else raid_channel(pool, "signup")
    target = await channel_by_id(target_id) if target_id else None
    if target is None:
        target = inter.channel
    raid = book.create(titel[:80], start, (beschreibung or "")[:500], max_spieler, inter.user.id, target.id, mode=mode)
    raid["pool"] = pool
    raid["pool_name"] = dict(known_raids()).get(pool, pool)
    if mode == "pug" and softres_link:
        raid["softres"] = softres_link
    if target.id == inter.channel_id:
        await inter.response.send_message(embed=raid_embed(raid), view=raid_view(raid))
        msg = await inter.original_response()
    else:
        msg = await target.send(embed=raid_embed(raid), view=raid_view(raid))
        await inter.response.send_message(f"Raid erstellt in {target.mention}.", ephemeral=True)
    raid["message_id"] = msg.id
    book.save()
    if mode == "pug":
        role = discord.utils.get(inter.guild.roles, name="Gast") if inter.guild else None
        if role:
            try:
                await target.send(f"{role.mention} 🎲 Neuer PUG-Raid: **{raid['title']}** ({raid['pool_name']}) am <t:{raid['start']}:F> – Anmeldung oben"
                                  + (f", Soft Reserve: {raid['softres']}" if raid.get("softres") else "") + "!",
                                  allowed_mentions=discord.AllowedMentions(roles=True))
            except discord.HTTPException:
                pass
    log.info("Raid #%s erstellt: %s", raid["id"], titel)


# ---------------------------------------------------------------------------
# Testraid: 40 Anmeldungen mit zufälligen Namen (für Tests von Anmeldung, Export und Einteilung)
# ---------------------------------------------------------------------------
TEST_RAID_HOURS = 2
TEST_NAMES = [
    "Thorgrim", "Elandra", "Brakkus", "Sylvara", "Garrok", "Mirelle", "Durnhelm", "Kaelith", "Brunhild", "Varonis",
    "Grimbald", "Lunessa", "Torvak", "Isolde", "Krugnar", "Faelyn", "Hadrik", "Seraphine", "Borin", "Aeris",
    "Galdor", "Nyria", "Ulfgar", "Thalindra", "Morgrim", "Celestia", "Rokhar", "Ilyana", "Dagnar", "Vespera",
    "Haldor", "Liora", "Brogan", "Eowyna", "Kazrak", "Selwyn", "Tormund", "Arwena", "Gorath", "Miravel",
    "Fendrik", "Shaela", "Bjornar", "Talwen", "Drakon", "Ysolde", "Hrothgar", "Nimara", "Korgath", "Elowen",
]
# MC-Aufstellung: (Klasse, Rolle, Skillung, Anzahl) – Paladin bzw. Schamane je nach Fraktion
TEST_LINEUP = [
    ("WARRIOR", "tank", "Schutz 5/5/41", 4), ("WARRIOR", "melee", "Furor 20/31/0", 6),
    ("PRIEST", "heal", "Heilig 21/30/0", 5), ("PRIEST", "ranged", "Schatten 5/0/46", 1),
    ("@HYBRID", "heal", "", 5), ("DRUID", "heal", "Wiederherstellung 11/0/40", 2), ("DRUID", "melee", "Wilder Kampf 0/30/21", 1),
    ("ROGUE", "melee", "Kampf 21/30/0", 4), ("MAGE", "ranged", "Frost 10/0/41", 6),
    ("WARLOCK", "ranged", "Zerstörung 0/21/30", 3), ("HUNTER", "ranged", "Treffsicherheit 0/31/20", 3),
]
TEST_BENCH = [("WARRIOR", "melee", "Furor 20/31/0"), ("PRIEST", "heal", "Heilig 21/30/0"), ("MAGE", "ranged", "Frost 10/0/41"),
              ("ROGUE", "melee", "Kampf 21/30/0"), ("HUNTER", "ranged", "Treffsicherheit 0/31/20")]
TEST_MAYBE = [("DRUID", "heal", "Wiederherstellung 11/0/40"), ("WARLOCK", "ranged", "Zerstörung 0/21/30"), ("@HYBRID", "heal", "")]


@raid_group.command(name="testraid", description="Testraid mit 40 Anmeldungen (zufällige Namen) – verschwindet nach 2 Stunden")
@app_commands.describe(raid="Welcher Raid? (Standard Molten Core)", fraktion="Paladine (Allianz) oder Schamanen (Horde)")
@app_commands.choices(fraktion=[app_commands.Choice(name="Allianz (Paladine)", value="alliance"),
                                app_commands.Choice(name="Horde (Schamanen)", value="horde")])
@app_commands.autocomplete(raid=raid_pool_autocomplete)
async def raid_test(inter: discord.Interaction, raid: str = "mc", fraktion: app_commands.Choice[str] | None = None):
    if not is_creator(inter.user):
        await inter.response.send_message("Einen Testraid dürfen nur Offiziere bzw. die Raidleitung anlegen.", ephemeral=True)
        return
    import random
    pool = raid
    hybrid = ("SHAMAN", "Wiederherstellung 5/0/46") if fraktion and fraktion.value == "horde" else ("PALADIN", "Heilig 31/20/0")
    target_id = raid_channel(pool, "signup")
    target = await channel_by_id(target_id) if target_id else None
    if target is None:
        target = inter.channel
    now = int(time.time())
    start = datetime.fromtimestamp(now + 3600, ZoneInfo(TZ))
    pool_name = dict(known_raids()).get(pool, pool)
    t = book.create(f"TEST {pool_name}"[:80], start,
                    f"🧪 Testdaten mit zufälligen Namen – {TEST_RAID_HOURS} Std. nach dem Anlegen verschwindet dieser Raid wieder.", 40,
                    inter.user.id, target.id, mode="dkp")
    t.update(pool=pool, pool_name=pool_name, test=True, expires=now + TEST_RAID_HOURS * 3600, reminded=True)
    names = random.sample(TEST_NAMES, len(TEST_NAMES))
    n = 0

    def add(cls, role, spec, status):
        nonlocal n
        if cls == "@HYBRID":
            cls, spec = hybrid
        label, _, points = spec.rpartition(" ") if spec else ("", "", "")
        uid = 900000000000000000 + n          # erfundene Nutzer-IDs, nie echte Mitglieder
        t["signups"][str(uid)] = {"t": now + n, "name": names[n], "cls": cls, "role": role, "status": status,
                                  "spec": f"{label} {points}".strip(), "test": True}
        n += 1
    for cls, role, spec, count in TEST_LINEUP:
        for _ in range(count):
            add(cls, role, spec, "an")
    for cls, role, spec in TEST_BENCH:
        add(cls, role, spec, "ersatz")
    for cls, role, spec in TEST_MAYBE:
        add(cls, role, spec, "vielleicht")
    book.save()
    msg = await target.send(embed=raid_embed(t), view=raid_view(t))
    t["message_id"] = msg.id
    book.save()
    await inter.response.send_message(
        f"🧪 Testraid #{t['id']} in {target.mention} angelegt: {book.count_status(t, 'an')} angemeldet, "
        f"{book.count_status(t, 'ersatz')} Ersatzbank, {book.count_status(t, 'vielleicht')} vielleicht. "
        f"Er verschwindet <t:{t['expires']}:R>.", ephemeral=True)
    log.info("Testraid #%s angelegt (%d Anmeldungen).", t["id"], len(t["signups"]))


async def remove_expired_test_raids():
    """Testraids nach Ablauf löschen (Nachricht und Eintrag)."""
    now = time.time()
    for t in [x for x in book.all() if x.get("test") and x.get("expires", 0) <= now]:
        if t.get("message_id"):
            try:
                ch = await channel_by_id(t["channel_id"])
                if ch:
                    await ch.get_partial_message(int(t["message_id"])).delete()
            except discord.HTTPException:
                pass
        book.raids.data["raids"].pop(str(t["id"]), None)
        book.save()
        log.info("Testraid #%s entfernt.", t["id"])


@raid_group.command(name="absagen", description="Raid absagen (Angemeldete werden benachrichtigt)")
@app_commands.describe(raid="Welcher Raid?")
@app_commands.autocomplete(raid=raid_autocomplete)
async def raid_cancel(inter: discord.Interaction, raid: str):
    if not is_creator(inter.user):
        await inter.response.send_message("Nur Offiziere bzw. die Raidleitung.", ephemeral=True)
        return
    r = book.get(raid)
    if not r:
        await inter.response.send_message("Raid nicht gefunden.", ephemeral=True)
        return
    r["closed"] = True
    r["cancelled"] = True
    book.save()
    await update_raid_message(r)
    ids = [uid for uid, s in r["signups"].items() if s["status"] in ("an", "ersatz", "vielleicht")]
    mentions = " ".join(f"<@{u}>" for u in ids)
    await inter.response.send_message(f"❌ **{r['title']}** (<t:{r['start']}:F>) wurde abgesagt. {mentions}",
                                      allowed_mentions=discord.AllowedMentions(users=True))


def clean_softres(link: str | None) -> str:
    """Nur echte softres.it-Links zulassen."""
    link = (link or "").strip().strip("<>")
    if not link:
        return ""
    if not link.startswith("http"):
        link = "https://" + link
    if not re.match(r"^https://(www\.)?softres\.it/[\w\-/?=&#.]+$", link):
        return ""
    return link


@raid_group.command(name="softres", description="softres.it-Link für einen PUG-Raid setzen oder ändern")
@app_commands.describe(raid="Welcher Raid?", link="z. B. https://softres.it/raid/abcd (leer = entfernen)")
@app_commands.autocomplete(raid=raid_autocomplete)
async def raid_softres(inter: discord.Interaction, raid: str, link: str = ""):
    if not is_creator(inter.user):
        await inter.response.send_message("Nur Offiziere bzw. die Raidleitung.", ephemeral=True)
        return
    r = book.get(raid)
    if not r:
        await inter.response.send_message("Raid nicht gefunden.", ephemeral=True)
        return
    value = clean_softres(link)
    if link and not value:
        await inter.response.send_message("Das ist kein softres.it-Link. Beispiel: `https://softres.it/raid/abcd`", ephemeral=True)
        return
    if value:
        r["softres"] = value
    else:
        r.pop("softres", None)
    book.save()
    await update_raid_message(r)
    await inter.response.send_message(
        f"softres.it-Link für **{r['title']}** " + (f"gesetzt: {value}" if value else "entfernt.")
        + "\nIm Spiel kommt er mit dem Import („Für RaidMaster“) ins Addon.", ephemeral=True)


@raid_group.command(name="schliessen", description="Anmeldung für einen Raid schließen")
@app_commands.describe(raid="Welcher Raid?")
@app_commands.autocomplete(raid=raid_autocomplete)
async def raid_close(inter: discord.Interaction, raid: str):
    if not is_creator(inter.user):
        await inter.response.send_message("Nur Offiziere bzw. die Raidleitung.", ephemeral=True)
        return
    r = book.get(raid)
    if not r:
        await inter.response.send_message("Raid nicht gefunden.", ephemeral=True)
        return
    r["closed"] = True
    book.save()
    await update_raid_message(r)
    await inter.response.send_message(f"Anmeldung für **{r['title']}** geschlossen.", ephemeral=True)


@raid_group.command(name="oeffnen", description="Anmeldung wieder öffnen")
@app_commands.describe(raid="Welcher Raid?")
@app_commands.autocomplete(raid=raid_autocomplete)
async def raid_open(inter: discord.Interaction, raid: str):
    if not is_creator(inter.user):
        await inter.response.send_message("Nur Offiziere bzw. die Raidleitung.", ephemeral=True)
        return
    r = book.get(raid)
    if not r:
        await inter.response.send_message("Raid nicht gefunden.", ephemeral=True)
        return
    r["closed"] = False
    r["cancelled"] = False
    book.save()
    await update_raid_message(r)
    await inter.response.send_message(f"Anmeldung für **{r['title']}** wieder geöffnet.", ephemeral=True)


@raid_group.command(name="export", description="Anmeldungen als Text für RaidMaster im Spiel")
@app_commands.describe(raid="Welcher Raid?")
@app_commands.autocomplete(raid=raid_autocomplete)
async def raid_export(inter: discord.Interaction, raid: str):
    r = book.get(raid)
    if not r:
        await inter.response.send_message("Raid nicht gefunden.", ephemeral=True)
        return
    await send_export(inter, r)


@raid_group.command(name="liste", description="Offene Raids anzeigen")
async def raid_list(inter: discord.Interaction):
    raids = book.open_raids()
    if not raids:
        await inter.response.send_message("Keine offenen Raids.", ephemeral=True)
        return
    lines = []
    for r in raids:
        link = f"https://discord.com/channels/{inter.guild_id}/{r['channel_id']}/{r['message_id']}" if r.get("message_id") else ""
        lines.append(f"**#{r['id']} {r['title']}** – <t:{r['start']}:F> – {book.count_status(r, 'an')} angemeldet {link}")
    await inter.response.send_message("\n".join(lines)[:1990], ephemeral=True)


async def channel_by_id(channel_id) -> discord.abc.Messageable | None:
    if not channel_id:
        return None
    try:
        return bot.get_channel(int(channel_id)) or await bot.fetch_channel(int(channel_id))
    except discord.HTTPException as e:
        log.warning("Kanal %s nicht erreichbar: %s", channel_id, e)
        return None


async def post_lineup(raid: dict, extra_channel=None) -> int:
    """Aufstellung berechnen und in #einteilung und #offiziere posten. Liefert Anzahl Kanäle."""
    att, n, source = rmd.attendance(bot.dkp_data, book)
    lineup = rmd.build_lineup(raid, att)
    texts = rmd.lineup_text(raid, lineup, source, n)
    targets = []
    for cid in (cfg.get("assignment_channel_id"), cfg.get("officer_channel_id")):
        ch = await channel_by_id(cid)
        if ch and ch not in targets:
            targets.append(ch)
    if extra_channel and extra_channel not in targets:
        targets.append(extra_channel)
    for ch in targets:
        try:
            for t in texts:
                await ch.send(t)
        except discord.HTTPException as e:
            log.warning("Aufstellung konnte nicht gepostet werden: %s", e)
    return len(targets)


@raid_group.command(name="aufstellung", description="Aufstellung und feste Gruppen berechnen und posten (#einteilung, #offiziere)")
@app_commands.describe(raid="Welcher Raid?")
@app_commands.autocomplete(raid=raid_autocomplete)
async def raid_lineup(inter: discord.Interaction, raid: str):
    if not is_creator(inter.user):
        await inter.response.send_message("Nur Offiziere bzw. die Raidleitung.", ephemeral=True)
        return
    r = book.get(raid)
    if not r:
        await inter.response.send_message("Raid nicht gefunden.", ephemeral=True)
        return
    await inter.response.defer(ephemeral=True, thinking=True)
    try:
        await asyncio.to_thread(reload_dkp_if_needed)
    except Exception:
        log.exception("RaidMaster-Datei nicht lesbar")
    n = await post_lineup(r, None if (cfg.get("assignment_channel_id") or cfg.get("officer_channel_id")) else inter.channel)
    await inter.followup.send(f"Aufstellung gepostet ({n} Kanal/Kanäle). Für das Spiel: Knopf **Für RaidMaster** am Raid – "
                              "der Export enthält jetzt die Gruppen.", ephemeral=True)


# Taktiken aller Raids (Molten Core ausführlich aus mc_tactics, die übrigen aus raid_tactics.json = Addon-Daten)
try:
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "raid_tactics.json"), encoding="utf-8") as _fh:
        RAID_TACTICS = {r["key"]: r for r in json.load(_fh)}
except (OSError, ValueError, KeyError):
    RAID_TACTICS = {}


def tactics_posts(pool: str) -> list[str]:
    """Beiträge (je max. 2000 Zeichen) mit der Taktik eines Raids; leer, wenn keine bekannt ist."""
    if pool == "mc":
        return [text for _, text in mc_tactics.TACTICS]
    r = RAID_TACTICS.get(pool)
    if not r or not r.get("bosses"):
        return []
    order = " → ".join(b["name"] for b in r["bosses"])
    posts = [f"# ⚔️ {r['name']} – Raidtaktik\n**Bosse:** {order}\n\nJe Boss ein Beitrag: Fähigkeiten, Taktik und das Wichtigste. "
             "Die Kurzinfo kommt im Raid als Schlachtzugwarnung aus dem Addon (Seite Raidleiter)."]
    for b in r["bosses"]:
        lines = [f"## {b['name']}"]
        text = [t for t in b.get("text") or []]
        if text and not text[0].startswith("-") and not text[0].startswith("Taktik"):
            lines.append(f"*{text[0]}*")
            text = text[1:]
        for t in text:
            if not t.strip():
                continue
            if t.startswith("- "):
                lines.append("• " + t[2:])
            elif t.startswith("Taktik:"):
                lines.append("\n**Taktik:**" + t[len("Taktik:"):])
            elif t.rstrip().endswith(":") and len(t) < 60:
                lines.append("\n**" + t.rstrip() + "**")
            else:
                lines.append(t)
        if b.get("wichtig"):
            w = b["wichtig"]
            lines.append("\n**⚠️ Wichtig:**" + (w[len("Wichtig:"):] if w.startswith("Wichtig:") else " " + w))
        posts.append("\n".join(lines)[:1990])
    return posts


async def post_tactics(pool: str, channel) -> int:
    posts = tactics_posts(pool)
    for text in posts:
        await channel.send(text)
        await asyncio.sleep(0.6)
    return len(posts)


async def post_all_tactics(force: bool = False) -> list[str]:
    """Taktik in jeden Taktik-Kanal der Raid-Kategorien (z. B. #mc-taktik, #onyxia-taktik).
    Ohne force nur einmal je Kanal und nur, wenn der Bot dort noch nichts gepostet hat."""
    done = set(state.data.get("tactics_posted") or [])
    hashes = state.data.setdefault("tactics_hash", {})
    report = []
    for pool, chans in (cfg.get("raid_channels") or {}).items():
        if not isinstance(chans, dict) or not chans.get("tactics"):
            continue
        ch = await channel_by_id(chans["tactics"])
        if not ch:
            continue
        name = rmd.pool_name(pool, bot.dkp_data)
        posts = tactics_posts(pool)
        if not posts:
            report.append(f"{name}: keine Taktik bekannt")
            continue
        digest = str(zlib.crc32("\n".join(posts).encode("utf-8")))
        if pool in done and not force:
            if hashes.get(pool) == digest:
                continue
            # Taktik wurde überarbeitet: alte Beiträge des Bots ersetzen
            try:
                async for m in ch.history(limit=60):
                    if m.author.id == bot.user.id:
                        await m.delete()
                        await asyncio.sleep(0.4)
            except discord.HTTPException:
                pass
            done.discard(pool)
            force_this = True
        else:
            force_this = force
        if not force_this:
            try:
                async for m in ch.history(limit=30):
                    if m.author.id == bot.user.id:
                        done.add(pool)
                        break
            except discord.HTTPException:
                pass
            if pool in done:
                report.append(f"{name}: schon vorhanden")
                continue
        try:
            n = await post_tactics(pool, ch)
            report.append(f"{name}: {n} Beiträge in {ch.mention}")
            done.add(pool)
            hashes[pool] = digest
        except discord.HTTPException as e:
            report.append(f"{name}: Fehler {e}")
    state.data["tactics_posted"] = sorted(done)
    state.save()
    return report


@raid_group.command(name="taktik", description="Postet die Raidtaktik (ein Beitrag pro Boss) in den Taktik-Kanal des Raids")
@app_commands.describe(raid="Welcher Raid? Leer = alle Raids mit Taktik-Kanal (z. B. #mc-taktik, #onyxia-taktik)")
@app_commands.autocomplete(raid=raid_pool_autocomplete)
async def raid_tactics(inter: discord.Interaction, raid: str = ""):
    if not is_creator(inter.user):
        await inter.response.send_message("Nur Offiziere bzw. die Raidleitung.", ephemeral=True)
        return
    await inter.response.defer(ephemeral=True, thinking=True)
    if not raid:
        report = await post_all_tactics(force=True)
        await inter.followup.send("Taktiken gepostet:\n" + ("\n".join("• " + r for r in report) or "Keine Taktik-Kanäle gefunden – `/raidmaster-einrichten` ausführen."), ephemeral=True)
        return
    channel = await channel_by_id(raid_channel(raid, "tactics"))
    if channel is None and inter.guild:
        channel = discord.utils.get(inter.guild.text_channels, name="raid-taktik")
    channel = channel or inter.channel
    if not tactics_posts(raid):
        await inter.followup.send(f"Für {rmd.pool_name(raid, bot.dkp_data)} ist keine Taktik hinterlegt.", ephemeral=True)
        return
    try:
        n = await post_tactics(raid, channel)
    except discord.HTTPException as e:
        await inter.followup.send(f"Posten fehlgeschlagen: {e}", ephemeral=True)
        return
    await inter.followup.send(f"Taktik in {channel.mention} gepostet ({n} Beiträge).", ephemeral=True)


bot.tree.add_command(raid_group)


# ---------------------------------------------------------------------------
# Befehle: Charakter und DKP
# ---------------------------------------------------------------------------


@bot.tree.command(name="charakter", description="Deinen Charakter (Name, Klasse, Rolle) festlegen")
async def character_cmd(inter: discord.Interaction):
    await inter.response.send_message("Wähle Klasse und Rolle und gib dann deinen Charakternamen ein.",
                                      view=ProfileView("", None, book.profile(inter.user.id)), ephemeral=True)


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
        await inter.response.send_message("Nur Offiziere bzw. die Raidleitung.", ephemeral=True)
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


@bot.tree.command(name="raidmaster-einrichten", description="Legt Kanäle, Rollen und Berechtigungen für die Gilde automatisch an")
async def setup_cmd(inter: discord.Interaction):
    member = inter.user
    if not isinstance(member, discord.Member) or not (member.guild_permissions.administrator or member.guild_permissions.manage_guild):
        await inter.response.send_message("Die Einrichtung dürfen nur Admins (Recht „Server verwalten“) starten.", ephemeral=True)
        return
    me = inter.guild.me
    missing = []
    if not me.guild_permissions.manage_channels:
        missing.append("Kanäle verwalten")
    if not me.guild_permissions.manage_roles:
        missing.append("Rollen verwalten")
    if missing:
        await inter.response.send_message(
            "Dem Bot fehlen dafür einmalig die Rechte: **" + "**, **".join(missing) + "**.\n"
            "So gibst du sie ihm: **Servereinstellungen → Rollen → Raidmaster tool → Berechtigungen** → "
            "die genannten Rechte einschalten → speichern. Danach `/raidmaster-einrichten` erneut ausführen.\n"
            "Nach der Einrichtung kannst du die Rechte wieder ausschalten.",
            ephemeral=True)
        return
    await inter.response.defer(ephemeral=True, thinking=True)
    settings = None
    if bot.dkp_data and isinstance(bot.dkp_data.get("settings"), dict):
        settings = bot.dkp_data["settings"]
    try:
        extra = {k: rmd.pool_name(k, bot.dkp_data) for k in rmd.pool_list(bot.dkp_data or {}) if k not in rmd.POOLS}
        report = await server_setup.run_setup(inter.guild, member, cfg, settings, extra)
        cfg.setdefault("raid_names", {}).update(extra)
        save_config()
        await check_addon_release()
        report.append(await ensure_welcome(update=True))
        report.append(await ensure_command_list())
    except discord.Forbidden:
        await inter.followup.send("Discord hat eine Aktion verweigert. Prüfe, ob die Rolle **Raidmaster tool** in "
                                  "**Servereinstellungen → Rollen** möglichst weit oben steht, und versuche es erneut.", ephemeral=True)
        return
    text = "\n".join(report)
    while text:
        part, text = text[:1900], text[1900:]
        await inter.followup.send(part, ephemeral=True)
    log.info("Server-Einrichtung durch %s abgeschlossen.", member)


@bot.tree.error
async def on_app_command_error(inter: discord.Interaction, error: app_commands.AppCommandError):
    log.exception("Befehlsfehler", exc_info=error)
    msg = "Da ist etwas schiefgelaufen."
    try:
        if inter.response.is_done():
            await inter.followup.send(msg, ephemeral=True)
        else:
            await inter.response.send_message(msg, ephemeral=True)
    except discord.HTTPException:
        pass


# ---------------------------------------------------------------------------
# Hintergrund: Erinnerung und automatisches Schließen
# ---------------------------------------------------------------------------


@tasks.loop(seconds=60)
async def reminder_loop():
    now = time.time()
    for raid in book.open_raids():
        if raid.get("cancelled"):
            continue
        until = raid["start"] - now
        if not raid.get("reminded") and 0 < until <= cfg["reminder_minutes"] * 60:
            raid["reminded"] = True
            book.save()
            if raid["signups"] and (cfg.get("assignment_channel_id") or cfg.get("officer_channel_id")):
                await post_lineup(raid)
            ids = [uid for uid, s in raid["signups"].items() if s["status"] in ("an", "ersatz", "vielleicht")]
            if ids:
                try:
                    channel = bot.get_channel(raid["channel_id"]) or await bot.fetch_channel(raid["channel_id"])
                    mentions = " ".join(f"<@{u}>" for u in ids)
                    await channel.send(f"⏰ **{raid['title']}** startet <t:{raid['start']}:R>! {mentions}",
                                       allowed_mentions=discord.AllowedMentions(users=True))
                except discord.HTTPException as e:
                    log.warning("Erinnerung fehlgeschlagen: %s", e)
        if now - raid["start"] > cfg["close_after_hours"] * 3600:
            raid["closed"] = True
            book.save()
            await update_raid_message(raid)


@reminder_loop.before_loop
async def before_reminder():
    await bot.wait_until_ready()


# ---------------------------------------------------------------------------
# Hintergrund: DKP-Tabelle und Loot-Protokoll
# ---------------------------------------------------------------------------


def dkp_channel_for(pool: str) -> int:
    if raid_channel(pool, "dkp"):
        return raid_channel(pool, "dkp")
    channels = cfg.get("dkp_channels") or {}
    cid = channels.get(pool)
    if not cid and pool == "mc":
        cid = cfg.get("dkp_channel_id")
    return int(cid or 0)


def table_file(png: bytes | None, name: str):
    return discord.File(io.BytesIO(png), filename=name) if png else None


async def dkp_list_messages(pool: str, rows: list[dict], data: dict | None, db: dict | None, head: str) -> list[str]:
    """DKP-Stände als feste Textliste – für alle Raids gleich (MC, Onyxia, BWL …):
    Punkt in Klassenfarbe, Name, Klasse, DKP, ggf. Ersatzbank. "Verdient" wird mitgezählt, aber nicht gezeigt."""
    standby = set(str(n) for n in ((((db or {}).get("config") or {}).get("standby")) or {}).keys())
    total, count = rmd.pool_total(rows)
    lines = [head, f"Gesamt: **{total} DKP** · {count} Spieler", ""]
    n = 0
    for r_ in rows:
        if r_["dkp"] == 0 and r_["name"] not in standby:
            continue
        n += 1
        dot = await class_emoji(r_.get("class"))
        cls = rimg.CLASS_NAMES.get(str(r_.get("class") or "").upper(), "")
        dkp = f"**{r_['dkp']}** DKP" if r_["dkp"] >= 0 else f"**{r_['dkp']}** DKP ❗"
        lines.append(f"`{n:>2}.` {dot} **{r_['name']}** · {cls} · {dkp}" + (" · *Ersatzbank*" if r_["name"] in standby else ""))
    if n == 0:
        lines.append("Noch keine DKP.")
    state.save()
    return rmd.split_discord("\n".join(lines))


def standings_png(pool: str, rows: list[dict], data: dict | None, subtitle: str, db: dict | None = None) -> bytes | None:
    """DKP-Stände wie die Seite im Addon (Name, Klasse, DKP, Verdient, Status) – alle Raids zusammengefasst."""
    try:
        standby = set(str(n) for n in ((((db or {}).get("config") or {}).get("standby")) or {}).keys())
        out = []
        for r_ in rows:
            if r_["dkp"] == 0 and not r_.get("earned") and r_["name"] not in standby:
                continue
            out.append({"name": r_["name"], "class": r_.get("class"), "dkp": r_["dkp"], "earned": r_.get("earned") or 0,
                        "status": "Ersatzbank" if r_["name"] in standby else ""})
        total, count = rmd.pool_total(rows)
        return rimg.render_addon_dkp(rmd.pool_name(pool, data), out, total, count, subtitle)
    except Exception as e:  # noqa: BLE001
        log.warning("DKP-Bild konnte nicht gezeichnet werden: %s", e)
        return None


def summary_png(s: dict) -> bytes | None:
    try:
        from datetime import datetime as _dt
        day = _dt.fromtimestamp(s["t"]).strftime("%d.%m.%Y")
        return rimg.render_summary(f"Raid-Abrechnung {s['pool_name']} – {day}",
                                   f"Bosse: {len(s['bosses'])} · Teilnehmer: {sum(1 for r in s['rows'] if r.get('present', True))}",
                                   s["rows"])
    except Exception as e:  # noqa: BLE001
        log.warning("Abrechnungs-Bild konnte nicht gezeichnet werden: %s", e)
        return None


async def send_summary(ch, s: dict, prefix: str = "", test: bool = False) -> int:
    """Raid-Abrechnung senden: Kopf + Bild (Klassenfarben), sonst als Text. Liefert die Anzahl Nachrichten."""
    png = summary_png(s)
    n = 0
    if png:
        head = prefix + rmd.raid_summary_head(s)
        if test:
            await send_test(ch, head, file_bytes=png, filename="abrechnung.png")
        else:
            await ch.send(content=head, file=table_file(png, "abrechnung.png"))
        n += 1
        for text in rmd.raid_summary_items(s):
            if test:
                await send_test(ch, text)
            else:
                await ch.send(text)
            n += 1
        return n
    for i, text in enumerate(rmd.format_raid_summary(s)):
        for part in rmd.split_discord((prefix + text) if i == 0 else text):
            if test:
                await send_test(ch, part)
            else:
                await ch.send(part)
            n += 1
    return n


async def post_dkp_tables():
    """Je Raid-Topf eine Tabelle im passenden Kanal (z. B. #mc-dkp) – wie die Seite DKP im Addon.
    Aktualisiert wird nach dem Raid: läuft gerade ein Raid, bleibt die Tabelle auf dem letzten Stand."""
    if rmd.session_active(bot.dkp_db) and state.data.get("dkp_messages"):
        log.info("Raid läuft noch – DKP-Tabelle wird nach dem Raidende aktualisiert.")
        return
    summaries = rmd.raid_summaries(bot.dkp_data)
    for pool in rmd.pool_list(bot.dkp_data):
        rows = rmd.standings(bot.dkp_data, pool)
        last = rmd.add_raid_columns(rows, summaries, pool)
        bot.last_raid_info = getattr(bot, "last_raid_info", {})
        bot.last_raid_info[pool] = last
        if not any(r["dkp"] != 0 for r in rows):
            continue
        channel_id = dkp_channel_for(pool)
        if not channel_id:
            log.info("Kein DKP-Kanal für %s eingetragen – /raidmaster-einrichten legt ihn an.", rmd.pool_name(pool, bot.dkp_data))
            continue
        await post_dkp_table(pool, channel_id, rows)


async def cleanup_dkp_channels():
    """Einmalig: alte Abrechnungen und Item-Zeilen des Bots aus den DKP-Kanälen entfernen –
    dort steht nur noch die zusammengefasste DKP-Tabelle."""
    if state.data.get("dkp_cleanup_v1"):
        return
    keep = {int(i) for ids in (state.data.get("dkp_messages") or {}).values() for i in (ids or [])}
    seen = set()
    for pool in rmd.pool_list(bot.dkp_data) if bot.dkp_data else []:
        cid = dkp_channel_for(pool)
        if not cid or cid in seen:
            continue
        seen.add(cid)
        ch = await channel_by_id(cid)
        if not ch:
            continue
        try:
            async for m in ch.history(limit=300):
                if m.author.id == bot.user.id and m.id not in keep:
                    await m.delete()
                    await asyncio.sleep(0.4)
        except discord.HTTPException as e:
            log.info("DKP-Kanal konnte nicht aufgeräumt werden: %s", e)
    state.data["dkp_cleanup_v1"] = True
    state.save()


async def post_raid_summaries():
    """Nach jedem beendeten Raid eine Abrechnung im DKP-Kanal des Raids (bleibt stehen = Verlauf über die Wochen).
    Beim ersten Mal werden alle noch gespeicherten Raidabende nachgetragen."""
    # Standard: keine einzelnen Abrechnungen – die Raids stehen zusammengefasst in der DKP-Tabelle (wie im Addon)
    if not cfg.get("raid_summaries", False):
        await cleanup_dkp_channels()
        return
    done = set(state.data.get("raid_summaries_done") or [])
    posted = False
    for s in rmd.raid_summaries(bot.dkp_data):
        if s["id"] in done:
            continue
        ch = await channel_by_id(dkp_channel_for(s["pool"]))
        if not ch:
            continue
        # alte DKP-Tabelle entfernen – sie wird danach unter der Abrechnung neu gepostet
        for msg_id in (state.data.setdefault("dkp_messages", {})).pop(s["pool"], None) or []:
            try:
                await ch.get_partial_message(msg_id).delete()
            except discord.HTTPException:
                pass
        await send_summary(ch, s)
        await asyncio.sleep(0.5)
        done.add(s["id"])
        posted = True
    if posted:
        state.data["raid_summaries_done"] = sorted(done)[-1000:]
        state.save()


async def remove_overall():
    """Die Gesamtsumme über alle Raids wird nicht gebraucht: den vom Bot angelegten Kanal #dkp-gesamt einmal entfernen."""
    if state.data.get("dkp_total_removed"):
        return
    ch = await channel_by_id(cfg.get("dkp_total_channel_id"))
    if ch is None:
        guild = bot_guild()
        ch = discord.utils.get(guild.text_channels, name="dkp-gesamt") if guild else None
    if ch is not None and getattr(ch, "name", "") == "dkp-gesamt":
        try:
            await ch.delete(reason="RaidMaster: Gesamtsumme über alle Raids wird nicht mehr gebraucht")
            log.info("Kanal #dkp-gesamt entfernt.")
        except discord.HTTPException as e:
            log.warning("#dkp-gesamt konnte nicht entfernt werden: %s", e)
            return
    cfg.pop("dkp_total_channel_id", None)
    save_config()
    state.data.pop("dkp_total_messages", None)
    state.data["dkp_total_removed"] = True
    state.save()


async def post_dkp_table(pool: str, channel_id: int, rows: list[dict]):
    try:
        channel = bot.get_channel(int(channel_id)) or await bot.fetch_channel(int(channel_id))
    except discord.HTTPException as e:
        log.warning("DKP-Kanal nicht erreichbar: %s", e)
        return
    last = (getattr(bot, "last_raid_info", {}) or {}).get(pool)
    after = ""
    if last:
        after = f"nach dem Raid vom {datetime.fromtimestamp(last['t']).strftime('%d.%m.%Y')}"
    head = (f"**DKP-Stände {rmd.pool_name(pool, bot.dkp_data)}**" + (f" – {after}" if after else "")
            + f" · aktualisiert <t:{int(bot.dkp_mtime)}:f>")
    # feste Textliste (wird nur bearbeitet, nicht neu gepostet) – für alle Raids gleich
    chunks = await dkp_list_messages(pool, rows, bot.dkp_data, bot.dkp_db, head)
    png = None
    all_ids = state.data.setdefault("dkp_messages", {})
    ids = list(all_ids.get(pool) or [])
    new_ids = []
    for i, text in enumerate(chunks):
        msg_id = ids[i] if i < len(ids) else None
        done = False
        file = table_file(png, "dkp.png") if (png and i == 0) else None
        if msg_id:
            try:
                if file:
                    await channel.get_partial_message(msg_id).edit(content=text, attachments=[file])
                else:
                    await channel.get_partial_message(msg_id).edit(content=text, attachments=[])
                new_ids.append(msg_id)
                done = True
            except discord.HTTPException:
                pass
        if not done:
            file = table_file(png, "dkp.png") if (png and i == 0) else None
            m = await channel.send(content=text, file=file) if file else await channel.send(text)
            new_ids.append(m.id)
    for msg_id in ids[len(chunks):]:
        try:
            await channel.get_partial_message(msg_id).delete()
        except discord.HTTPException:
            pass
    all_ids[pool] = new_ids
    state.save()


# ---------------------------------------------------------------------------
# Items wie im Spiel: Embed mit Qualitätsfarbe, Tooltip und echtem Spielsymbol
# ---------------------------------------------------------------------------
WOWHEAD_FLAVOR = "classic"


async def item_icon(link: str | None, tip: dict | None) -> str | None:
    """URL des Item-Symbols."""
    return rmd.icon_url(await item_icon_name(link, tip))


async def item_icon_name(link: str | None, tip: dict | None) -> str | None:
    """Name des Item-Symbols (z. B. inv_boots_05). Pfad vom Addon -> Name direkt, sonst einmal bei
    Wowhead nachschlagen (Ergebnis wird gemerkt)."""
    name = rmd.icon_name_from_hint(tip.get("ic") if tip else None)
    if name:
        return name
    iid = rmd.item_id(link)
    if not iid:
        return None
    cache = state.data.setdefault("item_icons", {})
    if str(iid) in cache:
        return cache[str(iid)]
    found = None
    try:
        import aiohttp
        timeout = aiohttp.ClientTimeout(total=8)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            for flavor in (WOWHEAD_FLAVOR, "tbc", "wotlk"):
                async with session.get(f"https://nether.wowhead.com/{flavor}/tooltip/item/{iid}") as resp:
                    if resp.status == 200:
                        js = await resp.json(content_type=None)
                        if isinstance(js, dict) and js.get("icon"):
                            found = str(js["icon"]).lower()
                            break
    except Exception as e:  # noqa: BLE001
        log.info("Item-Symbol %s nicht gefunden: %s", iid, e)
        return None
    cache[str(iid)] = found
    state.save()
    return found


async def wowhead_tip(link: str | None) -> dict | None:
    """Tooltip von Wowhead (deutsch, sonst englisch), falls das Addon keinen geliefert hat. Wird gemerkt."""
    iid = rmd.item_id(link)
    if not iid:
        return None
    cache = state.data.setdefault("wh_tips", {})
    if str(iid) in cache:
        return cache[str(iid)]
    found = None
    try:
        import aiohttp
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=6)) as session:
            for url in (f"https://nether.wowhead.com/{WOWHEAD_FLAVOR}/de/tooltip/item/{iid}",
                        f"https://nether.wowhead.com/{WOWHEAD_FLAVOR}/tooltip/item/{iid}"):
                async with session.get(url) as resp:
                    if resp.status != 200:
                        continue
                    js = await resp.json(content_type=None)
                if isinstance(js, dict) and js.get("tooltip"):
                    found = rmd.tip_from_wowhead_html(js["tooltip"], js.get("name"), js.get("quality"), js.get("icon"))
                    break
    except Exception as ex:  # noqa: BLE001
        log.info("Wowhead-Tooltip %s nicht geladen: %s", iid, ex)
        return None
    if found:
        found["l"] = [list(x) for x in found["l"]]
    cache[str(iid)] = found
    if len(cache) > 500:
        for k in list(cache)[:len(cache) - 500]:
            cache.pop(k, None)
    state.save()
    return found


async def item_embed(e: dict, db: dict | None, test: bool = False, tip: dict | None = None) -> discord.Embed:
    """Ein vergebenes Item als Embed wie der Tooltip im Spiel."""
    tip = tip or rmd.item_tip(db, e.get("link"))
    if not tip or not tip.get("l"):
        # kein Tooltip vom Addon (ältere Version oder Item noch nicht gelesen): bei Wowhead nachschlagen
        wh = await wowhead_tip(e.get("link"))
        if wh:
            tip = {**wh, "l": [tuple(x) for x in wh.get("l") or []], "q": (tip or {}).get("q") or wh.get("q")}
    name = (tip or {}).get("n") or e["item"]
    emb = discord.Embed(title=name, url=rmd.wowhead_url(e.get("link"), WOWHEAD_FLAVOR),
                        color=rmd.item_color(e.get("link"), tip))
    desc = f"🎁 **{e['name']}** · **{e['amount']} DKP** · <t:{int(e['t'])}:t>"
    block = rmd.tooltip_block(tip)
    emb.description = desc + ("\n" + block if block else "")
    icon = await item_icon(e.get("link"), tip)
    if icon:
        emb.set_thumbnail(url=icon)
    cls = (((db or {}).get("data") or {}).get("players") or {}).get(e["name"], {})
    cls = cls.get("c") if isinstance(cls, dict) else None
    emb.set_author(name=f"{e['name']}" + (f" · {rimg.CLASS_NAMES.get(str(cls).upper(), '')}" if cls else ""),
                   icon_url=rimg.class_icon_url(cls))
    emb.set_footer(text=(("TEST · " if test else "") + e.get("pool_name", "")))
    return emb


QUALITY_SQUARES = {0: "⬜", 1: "⬜", 2: "🟩", 3: "🟦", 4: "🟪", 5: "🟧"}
_emoji_lock = asyncio.Lock()


async def item_emoji(link: str | None, tip: dict | None) -> str:
    """Item-Symbol als Emoji für den Zeilenanfang (eigenes App-Emoji aus dem Spielsymbol).
    Geht das nicht, ein Quadrat in der Qualitätsfarbe."""
    q = (tip or {}).get("q")
    if not isinstance(q, int):
        q = {0xA335EE: 4, 0x0070DD: 3, 0x1EFF00: 2, 0xFF8000: 5}.get(rmd.item_color(link), 4)
    fallback = QUALITY_SQUARES.get(q, "🟪")
    try:
        name = await item_icon_name(link, tip)
    except Exception:  # noqa: BLE001
        name = None
    if not name:
        return fallback
    cache = state.data.setdefault("item_emojis", {})
    if name in cache:
        return cache[name] or fallback
    ename = re.sub(r"[^A-Za-z0-9_]", "_", name)[:32]
    if len(ename) < 2:
        return fallback
    async with _emoji_lock:
        if name in cache:
            return cache[name] or fallback
        try:
            existing = state.data.get("_app_emojis_loaded")
            if not existing and hasattr(bot, "fetch_application_emojis"):
                for em in await bot.fetch_application_emojis():
                    cache.setdefault(em.name, f"<:{em.name}:{em.id}>")
                state.data["_app_emojis_loaded"] = True
                if ename in cache:
                    cache[name] = cache[ename]
                    state.save()
                    return cache[name]
            import aiohttp
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=8)) as session:
                async with session.get(f"https://wow.zamimg.com/images/wow/icons/medium/{name}.jpg") as resp:
                    img = await resp.read() if resp.status == 200 else None
            if not img or not hasattr(bot, "create_application_emoji"):
                cache[name] = None
                state.save()
                return fallback
            em = await bot.create_application_emoji(name=ename, image=img)
            cache[name] = f"<:{em.name}:{em.id}>"
        except Exception as e:  # noqa: BLE001
            log.info("Item-Emoji %s nicht möglich: %s", name, e)
            cache[name] = None
        state.save()
        return cache[name] or fallback


async def class_emoji(cls: str | None) -> str:
    """Punkt in der genauen Klassenfarbe vor dem Namen (eigenes App-Emoji, sonst ähnliches Unicode-Emoji)."""
    c = str(cls or "").upper()
    if c not in rimg.CLASS_COLORS:
        return ""
    fallback = rimg.CLASS_FALLBACK_EMOJI.get(c, "")
    cache = state.data.setdefault("class_emojis", {})
    if c in cache:
        return cache[c] or fallback
    async with _emoji_lock:
        if c in cache:
            return cache[c] or fallback
        ename = f"rm_{c.lower()}"
        try:
            if hasattr(bot, "fetch_application_emojis"):
                for em in await bot.fetch_application_emojis():
                    if em.name == ename:
                        cache[c] = f"<:{em.name}:{em.id}>"
                        state.save()
                        return cache[c]
            png = rimg.class_dot_png(c)
            if png and hasattr(bot, "create_application_emoji"):
                em = await bot.create_application_emoji(name=ename, image=png)
                cache[c] = f"<:{em.name}:{em.id}>"
            else:
                cache[c] = None
        except Exception as e:  # noqa: BLE001
            log.info("Klassen-Emoji %s nicht möglich: %s", c, e)
            cache[c] = None
        state.save()
        return cache[c] or fallback


def player_class(db: dict | None, name: str) -> str | None:
    p_ = (((db or {}).get("data") or {}).get("players") or {}).get(name)
    return p_.get("c") if isinstance(p_, dict) else None


def remember_tip(link: str | None, tip: dict | None, db: dict | None):
    """Tooltip für das Menü "Tooltip anzeigen" merken (auch Testdaten, die sonst nicht gespeichert sind)."""
    iid = rmd.item_id(link)
    if not iid:
        return
    store = state.data.setdefault("tip_cache", {})
    store[str(iid)] = {"link": link, "tip": tip, "t": int(time.time())}
    if len(store) > 400:
        for k, _ in sorted(store.items(), key=lambda kv: kv[1].get("t", 0))[:len(store) - 400]:
            store.pop(k, None)


async def loot_line(e: dict, db: dict | None) -> str:
    tip = rmd.item_tip(db, e.get("link"))
    remember_tip(e.get("link"), tip, db)
    emoji = await item_emoji(e.get("link"), tip)
    item = (tip or {}).get("n") or e["item"]
    item_txt = f"**{item}**"     # nur Symbol und Name – kein Link, kein Tooltip
    dot = await class_emoji(player_class(db, e["name"]))
    return f"{emoji} <t:{int(e['t'])}:t> {dot}**{e['name']}** erhält {item_txt} für {e['amount']} DKP"


def tip_view(items: list[dict], db: dict | None = None) -> discord.ui.View | None:
    """Auswahlmenü "Tooltip anzeigen" unter der Loot-Liste (je Menü 25 Items, höchstens 5 Menüs)."""
    opts = []
    for e in items:
        iid = rmd.item_id(e.get("link"))
        if not iid:
            continue
        p_ = (((db or {}).get("data") or {}).get("players") or {}).get(e["name"])
        cls = (p_.get("c") if isinstance(p_, dict) else "") or ""
        value = f"{iid}|{e['name']}|{e['amount']}|{int(e['t'])}|{cls}"[:100]
        opts.append(discord.SelectOption(label=str(e["item"])[:100], description=f"{e['name']} · {e['amount']} DKP"[:100],
                                         value=value))
    if not opts:
        return None
    view = discord.ui.View(timeout=None)
    for n, i in enumerate(range(0, min(len(opts), 125), 25)):
        part = opts[i:i + 25]
        # Werte müssen je Menü eindeutig sein
        seen, uniq = set(), []
        for o in part:
            if o.value in seen:
                continue
            seen.add(o.value)
            uniq.append(o)
        view.add_item(discord.ui.Select(custom_id=f"rmtip:{n}:{int(time.time() * 1000) % 10**9}",
                                        placeholder="🔍 Tooltip anzeigen …" + (f" ({n + 1})" if len(opts) > 25 else ""),
                                        options=uniq, min_values=1, max_values=1))
    return view


async def send_loot_list(channel, items: list[dict], db: dict | None, header: str | None = None, test: bool = False) -> int:
    """Loot als kompakte Liste: Item-Symbol vorne, Uhrzeit, Gewinner, Item (Link zu Wowhead), DKP.
    Darunter ein Menü, das den Tooltip wie im Spiel zeigt (nur für den, der auswählt)."""
    lines = [await loot_line(e, db) for e in items]
    state.save()
    text = ((header + "\n") if header else "") + "\n".join(lines)
    parts = rmd.split_discord(text)
    view = None     # kein Tooltip-Menü mehr unter der Loot-Liste
    sent = 0
    for i, part in enumerate(parts):
        v = view if i == len(parts) - 1 else None
        if test:
            await send_test(channel, part, view=v)
        else:
            await channel.send(content=part, view=v) if v else await channel.send(part)
        sent += 1
    return sent


async def show_tip(inter: discord.Interaction):
    """Antwort auf das Menü "Tooltip anzeigen": Tooltip-Karte nur für den Klickenden.
    Sofort bestätigen (Discord wartet nur 3 Sekunden), dann die Karte nachreichen."""
    values = (inter.data or {}).get("values") or []
    if not values:
        return
    try:
        await inter.response.defer(ephemeral=True, thinking=True)
    except discord.HTTPException:
        pass
    iid, name, amount, t, cls = (values[0].split("|") + ["", "", "0", "0", ""])[:5]
    cached = (state.data.get("tip_cache") or {}).get(str(iid)) or {}
    link = cached.get("link") or f"|Hitem:{iid}|h[Item {iid}]|h"
    e = {"name": name, "amount": amount, "t": int(t or 0), "item": rmd.item_name(link), "link": link, "pool_name": ""}
    emb = await item_embed(e, {"data": {"players": {name: {"c": cls}}}} if cls else None, tip=cached.get("tip"))
    await inter.followup.send(embed=emb, ephemeral=True)


async def post_new_loot():
    entries = rmd.loot_entries(bot.dkp_data)
    if not entries:
        return
    last = state.data.get("last_loot")
    newest = [entries[-1]["t"], str(entries[-1]["id"])]
    if last is None:
        # Beim ersten Start nichts Altes posten
        state.data["last_loot"] = newest
        state.save()
        return
    fresh = [e for e in entries if (e["t"], str(e["id"])) > (last[0], last[1])]
    state.data["last_loot"] = newest
    state.save()
    by_pool: dict[str, list] = {}
    for e in fresh:
        by_pool.setdefault(e["pool"], []).append(e)
    for pool, items in by_pool.items():
        channel = await channel_by_id(raid_channel(pool, "loot") or cfg.get("loot_channel_id"))
        if not channel:
            continue
        try:
            await send_loot_list(channel, items, bot.dkp_db)
        except discord.HTTPException as ex:
            log.warning("Loot-Liste mit Symbolen nicht möglich (%s) – als Text.", ex)
            lines = [f"🎁 **{e['name']}** erhält **{e['item']}** für {e['amount']} DKP ({e['pool_name']})" for e in items]
            for text in rmd.split_discord("\n".join(lines)):
                await channel.send(text)


@tasks.loop(seconds=30)
async def dkp_loop():
    await process_new_data()


async def process_new_data():
    try:
        changed = await asyncio.to_thread(reload_dkp_if_needed)
    except Exception as e:
        # Datei wird evtl. gerade von WoW geschrieben – beim nächsten Durchlauf erneut
        log.warning("RaidMaster-Datei noch nicht lesbar: %s", e)
        return
    if not changed:
        return
    log.info("Neue DKP-Daten gelesen (%d Spieler).", len(bot.dkp_rows))
    try:
        await sync_specs()
        try:
            await sync_class_roles()
        except Exception:  # noqa: BLE001
            log.exception("Klassenfarben konnten nicht gesetzt werden")
        await ensure_new_raid_categories()
        await post_raid_summaries()
        await post_dkp_tables()
        await remove_overall()
        await post_new_loot()
        await update_lootdb()
        await process_assignment()
    except discord.HTTPException as e:
        log.warning("Posten fehlgeschlagen: %s", e)


# ---------------------------------------------------------------------------
# Eigene Beute-Datenbank: welcher Boss droppt was (aus euren eigenen Raids)
# Beutetabelle je Raid im Loot-Kanal (nach jedem Raid neu unten angehängt), Befehle /beute ...
# ---------------------------------------------------------------------------
async def update_lootdb(force_pools: list[str] | None = None):
    db = bot.dkp_db or {}
    if test_info(db):
        return
    uploader = state.data.get("last_upload_by") or ""
    added = rmd.lootdb_merge(lootdb.data, db, uploader)
    if added:
        lootdb.save()
        log.info("Beute-Datenbank: %d neue Kills von %s.", added, uploader or "?")
    if not cfg.get("loot_tables", True):
        return
    pools = force_pools if force_pools is not None else ([b["p"] for b in rmd.lootdb_bosses(lootdb.data)] if added else [])
    done = []
    for pool in pools:
        if pool and pool not in done:
            done.append(pool)
            try:
                await post_loot_table(pool)
            except discord.HTTPException as e:
                log.warning("Beutetabelle %s nicht gepostet: %s", pool, e)


async def lootdb_text(pool: str) -> list[str]:
    emojis = {}
    for b in rmd.lootdb_bosses(lootdb.data, pool):
        items, _ = rmd.lootdb_boss_loot(lootdb.data, b["e"])
        for it in items[:15]:
            if it["id"] not in emojis:
                link = rmd.item_link_for(it["id"], it["n"], it["q"])
                emojis[it["id"]] = await item_emoji(link, {"ic": it.get("ic"), "q": it.get("q")})
    kills = sum(b["kills"] for b in rmd.lootdb_bosses(lootdb.data, pool))
    head = (f"📖 **Beutetabelle {rmd.pool_name(pool, bot.dkp_data)}** – aus euren eigenen Raids ({kills} Bosskills) · "
            f"aktualisiert <t:{int(time.time())}:f>\n_Zahl = so oft gedroppt / so oft getötet._\n")
    lines = rmd.lootdb_lines(lootdb.data, pool, lambda it: emojis.get(it["id"], ""))
    return rmd.split_discord(head + "\n".join(lines).strip())


async def post_loot_table(pool: str):
    """Beutetabelle des Raids im Loot-Kanal: alte Nachrichten weg, neue unten (unter der letzten Lootliste)."""
    ch_id = raid_channel(pool, "loot") or cfg.get("loot_channel_id")
    channel = await channel_by_id(ch_id) if ch_id else None
    if channel is None:
        return
    chunks = await lootdb_text(pool)
    all_ids = state.data.setdefault("lootdb_messages", {})
    for msg_id in all_ids.get(pool) or []:
        try:
            await channel.get_partial_message(int(msg_id)).delete()
        except discord.HTTPException:
            pass
    new_ids = []
    for part in chunks:
        m = await channel.send(part)
        new_ids.append(m.id)
    all_ids[pool] = new_ids
    state.save()


beute_group = app_commands.Group(name="beute", description="Eigene Beute-Datenbank: welcher Boss droppt was")


async def lootdb_boss_autocomplete(inter: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    return [app_commands.Choice(name=f"{b['n']} ({rmd.pool_name(b['p'], bot.dkp_data) if b['p'] else '?'})"[:100], value=str(b["e"]))
            for b in rmd.lootdb_find_boss(lootdb.data, current)][:25]


def _boss_by_value(value: str) -> dict | None:
    for b in rmd.lootdb_bosses(lootdb.data):
        if str(b["e"]) == str(value) or b["n"].lower() == str(value).lower():
            return b
    found = rmd.lootdb_find_boss(lootdb.data, value)
    return found[0] if len(found) == 1 else None


@beute_group.command(name="boss", description="Was droppt dieser Boss? (aus euren eigenen Raids)")
@app_commands.describe(boss="Bossname")
@app_commands.autocomplete(boss=lootdb_boss_autocomplete)
async def beute_boss(inter: discord.Interaction, boss: str):
    b = _boss_by_value(boss)
    if not b:
        await inter.response.send_message("Diesen Boss gibt es noch nicht in der Beute-Datenbank – sie füllt sich mit jedem Bosskill.",
                                          ephemeral=True)
        return
    await inter.response.defer(ephemeral=True)
    items, kills = rmd.lootdb_boss_loot(lootdb.data, b["e"])
    lines = [f"**{b['n']}** · {kills} Kill{'s' if kills != 1 else ''} · {rmd.pool_name(b['p'], bot.dkp_data) if b['p'] else ''}"]
    for it in items:
        em = await item_emoji(rmd.item_link_for(it["id"], it["n"], it["q"]), {"ic": it.get("ic"), "q": it.get("q")})
        lines.append(f"{em} {it['n']} – {it['c']}/{kills} ({round(it['rate'] * 100)} %) · ID {it['id']}")
    for part in rmd.split_discord("\n".join(lines)):
        await inter.followup.send(part, ephemeral=True)


@beute_group.command(name="entfernen", description="Falsch erfasstes Item aus der Beutetabelle eines Bosses nehmen (Offiziere)")
@app_commands.describe(boss="Bossname", item="Item-ID oder Name")
@app_commands.autocomplete(boss=lootdb_boss_autocomplete)
async def beute_entfernen(inter: discord.Interaction, boss: str, item: str):
    if not is_creator(inter.user):
        await inter.response.send_message("Das dürfen nur Offiziere bzw. die Raidleitung.", ephemeral=True)
        return
    b = _boss_by_value(boss)
    if not b:
        await inter.response.send_message("Boss nicht gefunden.", ephemeral=True)
        return
    items, _ = rmd.lootdb_boss_loot(lootdb.data, b["e"])
    target = next((it for it in items if str(it["id"]) == item.strip() or it["n"].lower() == item.strip().lower()), None)
    if not target:
        await inter.response.send_message(f"{item} gehört bei {b['n']} nicht zur Beute.", ephemeral=True)
        return
    rmd.lootdb_remove(lootdb.data, b["e"], target["id"])
    lootdb.save()
    await inter.response.send_message(f"{target['n']} aus der Beutetabelle von {b['n']} entfernt.", ephemeral=True)
    if b["p"]:
        try:
            await post_loot_table(b["p"])
        except discord.HTTPException:
            pass


@beute_group.command(name="export", description="Beute-Datenbank als Datei (z. B. für Partner-Gilden)")
async def beute_export(inter: discord.Interaction):
    if not is_creator(inter.user):
        await inter.response.send_message("Das dürfen nur Offiziere bzw. die Raidleitung.", ephemeral=True)
        return
    data = json.dumps(lootdb.data, ensure_ascii=False, indent=1).encode("utf-8")
    await inter.response.send_message(f"Beute-Datenbank: {len(lootdb.data.get('kills') or [])} Kills, "
                                      f"{len(lootdb.data.get('items') or {})} Items.",
                                      file=discord.File(io.BytesIO(data), filename="beute-datenbank.json"), ephemeral=True)


@beute_group.command(name="tabellen", description="Beutetabellen in den Loot-Kanälen neu posten (Offiziere)")
async def beute_tabellen(inter: discord.Interaction):
    if not is_creator(inter.user):
        await inter.response.send_message("Das dürfen nur Offiziere bzw. die Raidleitung.", ephemeral=True)
        return
    await inter.response.defer(ephemeral=True)
    pools = rmd.lootdb_pools(lootdb.data)
    await update_lootdb(pools)
    await inter.followup.send(f"Beutetabellen gepostet: {', '.join(rmd.pool_name(p, bot.dkp_data) for p in pools) or 'noch keine Daten'}.",
                              ephemeral=True)


bot.tree.add_command(beute_group)


# ---------------------------------------------------------------------------
# Klassenfarben für Discord-Mitglieder: je Klasse eine Rolle in der WoW-Klassenfarbe
# (Name im Discord erscheint dann wie im Spiel). Klasse aus dem Profil (/profil bzw. Anmeldung),
# sonst über den Discord-Namen aus den RaidMaster-Daten.
# ---------------------------------------------------------------------------
def member_class(member, players: dict) -> str | None:
    p = book.profile(member.id)
    if p and p.get("cls") in rimg.CLASS_COLORS:
        return p["cls"]
    names = {str(n).lower(): (v.get("c") if isinstance(v, dict) else None) for n, v in (players or {}).items()}
    for cand in (getattr(member, "nick", None), getattr(member, "global_name", None), member.name):
        if not cand:
            continue
        c = str(cand).strip().lower()
        cls = names.get(c) or names.get(c.split(" ")[0]) or names.get(re.split(r"[^\wäöüß]", c)[0] if c else "")
        if cls and str(cls).upper() in rimg.CLASS_COLORS:
            return str(cls).upper()
    return None


async def ensure_class_role(guild, cls: str):
    name = rimg.CLASS_NAMES.get(cls, cls.title())
    color = discord.Colour.from_rgb(*rimg.CLASS_COLORS[cls])
    ids = cfg.setdefault("class_roles", {})
    role = guild.get_role(int(ids.get(cls) or 0)) or discord.utils.get(guild.roles, name=name)
    if role is None:
        role = await guild.create_role(name=name, colour=color, hoist=False, mentionable=False,
                                       reason="RaidMaster: Klassenfarbe wie im Spiel")
        # direkt unter die Bot-Rolle schieben, damit die Farbe vor anderen farbigen Rollen gilt
        try:
            me = guild.me
            await guild.edit_role_positions({role: max(1, me.top_role.position - 1)})
        except discord.HTTPException:
            pass
    elif role.colour != color and role < guild.me.top_role:
        try:
            await role.edit(colour=color, reason="RaidMaster: Klassenfarbe wie im Spiel")
        except discord.HTTPException:
            pass
    if str(ids.get(cls)) != str(role.id):
        ids[cls] = role.id
        save_config()
    return role


async def sync_class_roles(only=None) -> int:
    """Jedem Mitglied die Rolle seiner Klasse geben (und andere Klassenrollen entfernen). Liefert die Anzahl Änderungen."""
    guild = bot_guild()
    if guild is None or not guild.me.guild_permissions.manage_roles:
        return 0
    players = (bot.dkp_data or {}).get("players") or {}
    members = list(only) if only else list(guild.members)
    if not members and not only:
        for uid in list(book.profiles.data.keys()):
            m = guild.get_member(int(uid))
            if m is None:
                try:
                    m = await guild.fetch_member(int(uid))
                except discord.HTTPException:
                    m = None
            if m:
                members.append(m)
    changes = 0
    class_role_ids = {int(v) for v in (cfg.get("class_roles") or {}).values() if v}
    for m in members:
        if m.bot:
            continue
        cls = member_class(m, players)
        if not cls:
            continue
        try:
            role = await ensure_class_role(guild, cls)
            class_role_ids.add(role.id)
            wrong = [r_ for r_ in m.roles if r_.id in class_role_ids and r_.id != role.id]
            if wrong:
                await m.remove_roles(*wrong, reason="RaidMaster: Klasse geändert")
                changes += 1
            if role not in m.roles:
                await m.add_roles(role, reason="RaidMaster: Klassenfarbe wie im Spiel")
                changes += 1
        except discord.HTTPException as e:
            log.info("Klassenrolle für %s nicht möglich: %s", m, e)
    if changes:
        log.info("Klassenfarben: %d Änderung(en).", changes)
    return changes


async def sync_specs():
    """Skillungen aus dem Addon in die Discord-Profile übernehmen."""
    changes = book.apply_specs(rmd.specs_from_db(bot.dkp_db))
    if not changes:
        return
    log.info("Skillungen übernommen: %s", ", ".join(f"{c['name']} {rmd.spec_short(c['spec'])}" for c in changes))
    ids = {str(c["user_id"]) for c in changes}
    for raid in book.open_raids():
        if ids & set(raid["signups"].keys()):
            await update_raid_message(raid)
    if not cfg.get("notify_spec_changes", True):
        return
    for c in changes:
        if c["old_role"] == c["role"] or not c["old_role"]:
            continue
        spec = c["spec"]
        text = (f"🧬 Deine Skillung aus dem Spiel wurde übernommen: **{c['name']} – {spec['label']}**" + (f" ({spec['points']})" if spec.get("points") else "") + ".\n"
                f"Deine Rolle für Raids ist jetzt **{rmd.ROLES.get(c['role'], c['role'])}** "
                f"(vorher {rmd.ROLES.get(c['old_role'], c['old_role'])}). Ändern kannst du das jederzeit mit `/charakter`.")
        try:
            user = bot.get_user(c["user_id"]) or await bot.fetch_user(c["user_id"])
            await user.send(text)
        except discord.HTTPException:
            pass


async def ensure_guild_rules() -> list[str]:
    """Kategorie 📜 REGELN (Zusammenleben in der Gilde) anlegen und die Regeltexte posten.
    Ändert sich ein Text in guild_rules.json, ersetzt der Bot seine Beiträge im Kanal."""
    guild = bot_guild()
    if guild is None or not guild.me.guild_permissions.manage_channels:
        return []
    report = await server_setup.ensure_rules_category(guild, cfg)
    save_config()
    hashes = state.data.setdefault("rules_hash", {})
    msgs = state.data.setdefault("rules_messages", {})
    for rule in server_setup.guild_rules():
        key = rule["key"]
        ch = await channel_by_id((cfg.get("rules_channels") or {}).get(key))
        if not ch:
            continue
        posts = [p for p in rule.get("posts") or [] if p.strip()]
        digest = str(zlib.crc32("\n".join(posts).encode("utf-8")))
        if hashes.get(key) == digest and msgs.get(key):
            continue
        old = list(msgs.get(key) or [])
        new_ids = []
        for i, text in enumerate(posts):
            text = text[:2000]
            done = False
            if i < len(old):
                try:
                    await ch.get_partial_message(old[i]).edit(content=text)
                    new_ids.append(old[i])
                    done = True
                except discord.HTTPException:
                    pass
            if not done:
                m = await ch.send(text)
                new_ids.append(m.id)
            await asyncio.sleep(0.4)
        for mid in old[len(posts):]:
            try:
                await ch.get_partial_message(mid).delete()
            except discord.HTTPException:
                pass
        msgs[key] = new_ids
        hashes[key] = digest
        report.append(f"📜 #{key}: Regeln {'aktualisiert' if old else 'gepostet'}")
        state.save()
    return report


async def ensure_listed_raid_categories() -> list[str]:
    """Alle Raids der festen Liste (MC, Onyxia, BWL, ZG, AQ, Naxx …) bekommen ihre Kategorie mit Kanälen."""
    if not cfg.get("guild_id"):
        return []
    guild = bot.get_guild(int(cfg["guild_id"]))
    if guild is None or not guild.me.guild_permissions.manage_channels:
        return []
    known = set((cfg.get("raid_channels") or {}).keys())
    made = []
    for key, name, emoji, prefix in server_setup.RAIDS:
        if key in known:
            continue
        try:
            await server_setup.ensure_raid(guild, cfg, key, name, emoji, prefix)
        except discord.HTTPException as e:
            log.warning("Kategorie für %s konnte nicht angelegt werden: %s", name, e)
            continue
        cfg.setdefault("raid_names", {})[key] = name
        save_config()
        made.append(name)
        log.info("Raid-Kategorie angelegt: %s", name)
    return made


async def ensure_new_raid_categories():
    """Hat das Addon einen neuen Raid erkannt, bekommt er automatisch eine eigene Kategorie."""
    if not cfg.get("auto_raid_categories", True) or not cfg.get("guild_id"):
        return
    known = set((cfg.get("raid_channels") or {}).keys())
    guild = bot.get_guild(int(cfg["guild_id"]))
    if guild is None:
        return
    for key in rmd.pool_list(bot.dkp_data):
        if key in known:
            continue
        name = rmd.pool_name(key, bot.dkp_data)
        perms = guild.me.guild_permissions
        if not perms.manage_channels:
            log.info("Neuer Raid %s erkannt – für eine eigene Kategorie braucht der Bot das Recht 'Kanäle verwalten'.", name)
            continue
        try:
            await server_setup.ensure_raid(guild, cfg, key, name)
        except discord.HTTPException as e:
            log.warning("Kategorie für %s konnte nicht angelegt werden: %s", name, e)
            continue
        cfg.setdefault("raid_names", {})[key] = name
        save_config()
        log.info("Neue Raid-Kategorie angelegt: %s", name)
        ch = await channel_by_id(cfg.get("announce_channel_id"))
        if ch:
            await ch.send(f"🆕 **Neuer Raid erkannt: {name}!** Eigene Kategorie mit Anmeldung, Taktik, DKP und Loot ist angelegt.")


# ---------------------------------------------------------------------------
# Addon-Versionen: neue ZIP im Ordner "addon" -> #raid-addon + Nachricht an alle
# ---------------------------------------------------------------------------

ADDON_DIR = os.path.join(BASE, "addon")


def version_tuple(v: str) -> tuple:
    return tuple(int(x) for x in re.findall(r"\d+", v or "0"))


def addon_version_key(key: str, v: str) -> tuple:
    """Vergleichswert einer Addon-Version. AH Analyzer Pro wurde von 5.9.x auf 0.59.x
    umbenannt (5.9.13 -> 0.59.13): alte Nummern werden dafür umgerechnet, damit
    0.59.14 neuer ist als 5.9.12."""
    t = version_tuple(v)
    if key == "ahanalyzerpro" and t and t[0] >= 1:
        return (0, t[0] * 10 + (t[1] if len(t) > 1 else 0)) + t[2:]
    return t


# Weitere Addons von GoldSentinel: Schlüssel = Name der TOC-Datei (klein, ohne _Vanilla usw.)
EXTRA_ADDONS = {
    "ahanalyzerpro": {"title": "AH Analyzer Pro", "folder": "AHAnalyzerPro", "channel": "aktionshaus_channel_id",
                      "channel_name": "aktionshaus"},
}


def zip_addon_info(path: str) -> tuple[str, str, str] | None:
    """(Schlüssel, Ordnername, Version) aus einer Addon-ZIP oder None."""
    try:
        with zipfile.ZipFile(path) as z:
            tocs = [n for n in z.namelist() if n.lower().endswith(".toc") and "/" in n.strip("/")]
            tocs = tocs or [n for n in z.namelist() if n.lower().endswith(".toc")]
            if not tocs:
                return None
            tocs.sort(key=lambda n: ("_" in os.path.basename(n), len(n)))
            toc = tocs[0]
            text = z.read(toc).decode("utf-8-sig", "replace")
    except (zipfile.BadZipFile, OSError, KeyError):
        return None
    m = re.search(r"##\s*Version:\s*v?([\d.]+)", text)
    if not m:
        return None
    base = os.path.basename(toc)[:-4]
    key = base.split("_")[0].lower()
    folder = toc.split("/")[0] if "/" in toc else base.split("_")[0]
    return key, folder, m.group(1)


def find_addon_package(key: str = "raidmaster") -> tuple[str, str] | None:
    """Neueste ZIP eines Addons im Ordner addon: (Pfad, Version aus der TOC)."""
    if not os.path.isdir(ADDON_DIR):
        return None
    best = None
    for fn in os.listdir(ADDON_DIR):
        if not fn.lower().endswith(".zip"):
            continue
        path = os.path.join(ADDON_DIR, fn)
        info = zip_addon_info(path)
        if not info or info[0] != key:
            continue
        if best is None or addon_version_key(key, info[2]) > addon_version_key(key, best[1]):
            best = (path, info[2])
    return best


def zip_changelog(path: str, key: str, since: str | None, upto: str, limit: int = 3500) -> str:
    """Changelog-Abschnitte aus der ZIP: alles nach Version `since` bis einschließlich `upto`."""
    try:
        with zipfile.ZipFile(path) as z:
            name = next((n for n in z.namelist() if n.lower().endswith("/changelog.md") or n.lower() == "changelog.md"), None)
            if not name:
                return ""
            text = z.read(name).decode("utf-8", "replace")
    except (zipfile.BadZipFile, OSError, KeyError):
        return ""
    lo = addon_version_key(key, since) if since else None
    hi = addon_version_key(key, upto)
    out, keep = [], False
    for line in text.splitlines():
        m = re.match(r"^##\s+v?([\d.]+)", line)
        if m:
            v = addon_version_key(key, m.group(1))
            keep = v <= hi and (lo is None or v > lo)
            if keep:
                out.append(f"**{m.group(1)}**")
            continue
        if keep and not line.startswith(">"):        # Beta-Hinweis weglassen
            out.append(line)
    text = "\n".join(out).strip()
    text = re.sub(r"\n{3,}", "\n\n", text)
    if len(text) > limit:
        text = text[:limit].rsplit("\n", 1)[0] + "\n…"
    return text


async def check_extra_releases():
    """Neue Versionen der weiteren Addons (z. B. AH Analyzer Pro) in ihrem Kanal posten."""
    versions = state.data.setdefault("extra_versions", {})
    for key, meta in EXTRA_ADDONS.items():
        pkg = find_addon_package(key)
        if not pkg:
            continue
        path, version = pkg
        if addon_version_key(key, version) <= addon_version_key(key, versions.get(key) or "0"):
            continue
        ch = await channel_by_id(cfg.get(meta["channel"]))
        if not ch:
            log.info("%s %s gefunden, aber Kanal #%s fehlt (/raidmaster-einrichten).", meta["title"], version, meta["channel_name"])
            continue
        notes = zip_changelog(path, key, versions.get(key), version)
        embed = None
        if notes:
            embed = discord.Embed(title=f"{meta['title']} {version} – what's new", description=notes, color=0xFFD100)
        await ch.send(
            f"🆕 **{meta['title']} {version}** ist da!\n"
            f"Download: Datei unten herunterladen, entpacken und den Ordner **{meta['folder']}** in "
            "`Interface/AddOns` ersetzen. Deine Einstellungen bleiben erhalten.",
            embed=embed,
            file=discord.File(path, filename=f"{meta['folder']}-{version}.zip"))
        versions[key] = version
        state.save()
        log.info("%s %s in #%s veröffentlicht.", meta["title"], version, meta["channel_name"])


# Ankündigungen: Textdateien im Repo-Ordner "announce" werden je einmal gepostet.
# Dateiname: <kanal>-<irgendwas>.md, z. B. aktionshaus-0.59.22.md oder raid-addon-info.md
ANNOUNCE_DIR = os.path.join(BASE, "announce")
ANNOUNCE_CHANNELS = {"aktionshaus": "aktionshaus_channel_id", "raid-addon": "addon_channel_id"}


async def check_announcements():
    if not os.path.isdir(ANNOUNCE_DIR):
        return
    done = state.data.setdefault("announced", [])
    for fn in sorted(os.listdir(ANNOUNCE_DIR)):
        if not fn.lower().endswith(".md") or fn in done:
            continue
        chan_key = next((v for k, v in ANNOUNCE_CHANNELS.items() if fn.lower().startswith(k + "-")), None)
        if not chan_key:
            continue
        ch = await channel_by_id(cfg.get(chan_key))
        if not ch:
            continue
        try:
            with open(os.path.join(ANNOUNCE_DIR, fn), "r", encoding="utf-8") as f:
                text = f.read().strip()
        except OSError:
            continue
        # Discord: höchstens 2000 Zeichen pro Nachricht - an Absätzen teilen
        parts, cur = [], ""
        for para in text.split("\n\n"):
            if len(cur) + len(para) + 2 > 1900 and cur:
                parts.append(cur)
                cur = ""
            cur = (cur + "\n\n" + para) if cur else para
        if cur:
            parts.append(cur)
        for p in parts:
            await ch.send(p[:2000])
        done.append(fn)
        state.save()
        log.info("Ankündigung %s gepostet.", fn)


async def check_addon_release():
    await check_extra_releases()
    await check_announcements()
    pkg = find_addon_package("raidmaster")
    if not pkg:
        return
    path, version = pkg
    if version_tuple(version) <= version_tuple(state.data.get("addon_version") or "0"):
        return
    ch = await channel_by_id(cfg.get("addon_channel_id"))
    if not ch:
        log.info("Neue Addon-Version %s gefunden, aber kein Kanal #raid-addon eingetragen (/raidmaster-einrichten).", version)
        return
    msg = await ch.send(
        f"🆕 **RaidMaster {version}** ist da!\n"
        "Download: Datei unten herunterladen, entpacken und den Ordner **RaidMaster** in "
        "`Interface/AddOns` ersetzen. Deine Einstellungen und DKP bleiben erhalten.",
        file=discord.File(path, filename=f"RaidMaster-{version}.zip"))
    state.data["addon_version"] = version
    state.data["addon_message"] = msg.jump_url
    state.save()
    log.info("Addon %s in #raid-addon veröffentlicht.", version)
    if cfg.get("notify_addon_updates", True):
        await notify_registered(
            f"🆕 **Neue RaidMaster-Version {version}** – bitte das Addon aktualisieren!\n"
            f"Download in **#raid-addon**: {msg.jump_url}")


async def notify_registered(text: str):
    """Allen registrierten Spielern (Charakter im Bot hinterlegt) eine Direktnachricht schicken."""
    sent = failed = 0
    for uid in list(book.profiles.data.keys()):
        try:
            user = bot.get_user(int(uid)) or await bot.fetch_user(int(uid))
            await user.send(text)
            sent += 1
        except discord.HTTPException:
            failed += 1
        await asyncio.sleep(1)
    log.info("Benachrichtigung an %d Spieler verschickt (%d ohne Direktnachrichten).", sent, failed)


@bot.tree.command(name="addon-hochladen", description="Neue Addon-Version (ZIP) hochladen – wird im passenden Kanal veröffentlicht (Admins)")
@app_commands.describe(datei="Addon-ZIP, z. B. AHAnalyzerPro-5.9.zip oder RaidMaster-1.6.0.zip")
async def addon_upload_cmd(inter: discord.Interaction, datei: discord.Attachment):
    if not is_admin(inter.user):
        await inter.response.send_message("Nur Admins (Recht „Server verwalten“).", ephemeral=True)
        return
    if not datei.filename.lower().endswith(".zip") or datei.size > 25 * 1024 * 1024:
        await inter.response.send_message("Bitte eine Addon-ZIP (max. 25 MB) anhängen.", ephemeral=True)
        return
    await inter.response.defer(ephemeral=True, thinking=True)
    os.makedirs(ADDON_DIR, exist_ok=True)
    tmp = os.path.join(ADDON_DIR, "upload.tmp")
    with open(tmp, "wb") as f:
        f.write(await datei.read())
    info = zip_addon_info(tmp)
    if not info or (info[0] != "raidmaster" and info[0] not in EXTRA_ADDONS):
        os.remove(tmp)
        known = ", ".join(["RaidMaster"] + [m["title"] for m in EXTRA_ADDONS.values()])
        await inter.followup.send(f"In der ZIP wurde keine bekannte Addon-TOC mit Version gefunden (bekannt: {known}).", ephemeral=True)
        return
    key, folder, version = info
    target = os.path.join(ADDON_DIR, f"{folder}-{version}.zip")
    os.replace(tmp, target)
    log.info("Addon-ZIP hochgeladen: %s %s von %s", folder, version, inter.user)
    await check_addon_release()
    where = "#raid-addon" if key == "raidmaster" else "#" + EXTRA_ADDONS[key]["channel_name"]
    await inter.followup.send(f"✅ **{folder} {version}** gespeichert – wird in **{where}** veröffentlicht "
                              "(falls die Version neuer ist als die zuletzt gepostete).", ephemeral=True)


@bot.tree.command(name="addon", description="Link zur aktuellen RaidMaster-Addon-Version")
async def addon_cmd(inter: discord.Interaction):
    v = state.data.get("addon_version")
    if not v:
        await inter.response.send_message("Es wurde noch keine Addon-Version veröffentlicht.", ephemeral=True)
        return
    await inter.response.send_message(f"Aktuelle Version: **RaidMaster {v}** – Download: {state.data.get('addon_message')}", ephemeral=True)


async def process_assignment():
    """Neue Einteilung aus dem Addon: Übersicht posten und jedem Spieler eine Direktnachricht schicken."""
    a = rmd.assignment_from_db(bot.dkp_db)
    if not a or int(a.get("v") or 0) <= int(state.data.get("assign_v") or 0):
        return
    state.data["assign_v"] = int(a["v"])
    state.save()
    ch = await channel_by_id(cfg.get("assignment_channel_id"))
    if ch:
        for text in rmd.assignment_overview(a):
            await ch.send(text)
    if not cfg.get("send_assignment_dms", True):
        return
    # Charaktername -> Discord-Nutzer über die Profile
    by_name = {p["name"].lower(): int(uid) for uid, p in book.profiles.data.items()}
    names = set()
    for c in (a.get("ctx") or {}).values():
        if isinstance(c, dict):
            names.update(str(n) for n in (c.get("p") or {}).keys())
    sent, missing = 0, []
    for name in sorted(names):
        uid = by_name.get(name.lower())
        text = rmd.personal_assignment(a, name)
        if not uid or not text:
            missing.append(name)
            continue
        try:
            user = bot.get_user(uid) or await bot.fetch_user(uid)
            await user.send(text[:1990])
            sent += 1
        except discord.HTTPException:
            missing.append(name)
        await asyncio.sleep(0.5)
    log.info("Einteilung: %d Direktnachrichten verschickt, ohne Discord-Verknüpfung/DM: %s", sent, ", ".join(missing) or "-")

# ---------------------------------------------------------------------------
# Server-Betrieb: Daten-Upload vom PC der Raidleitung
# ---------------------------------------------------------------------------

def is_admin(member) -> bool:
    return isinstance(member, discord.Member) and (member.guild_permissions.administrator or member.guild_permissions.manage_guild)


def check_upload(raw: bytes, filename: str) -> tuple[str, dict]:
    """Entpackt und prüft einen Upload. Liefert (Text, RaidMasterDB) oder wirft ValueError."""
    if filename.lower().endswith(".gz"):
        try:
            raw = gzip.decompress(raw)
        except OSError:
            raise ValueError("Datei ist nicht richtig gepackt")
    text = raw.decode("utf-8", errors="replace")
    try:
        db = rmd.parse_saved_variables(text).get("RaidMasterDB")
    except Exception as e:  # noqa: BLE001
        raise ValueError(f"Datei nicht lesbar: {e}")
    if not isinstance(db, dict) or not isinstance(db.get("data"), dict):
        raise ValueError("keine RaidMaster-Daten enthalten")
    return text, db


async def receive_upload(message: discord.Message):
    allowed = [int(x) for x in cfg.get("uploader_webhooks") or []]
    if allowed and message.webhook_id not in allowed:
        log.warning("Upload von unbekanntem Webhook %s ignoriert.", message.webhook_id)
        return
    att = next((a for a in message.attachments if a.filename.lower().endswith((".lua", ".lua.gz", ".gz"))), None)
    if not att:
        if not message.attachments:
            log.warning("Upload ohne Anhang empfangen – Message Content Intent einschalten (siehe ANLEITUNG, Probleme).")
            await post_bot_log("⚠️ Daten-Upload ohne Datei empfangen: Im Discord-Entwicklerportal unter Bot → Privileged "
                               "Gateway Intents den **Message Content Intent** einschalten, in config.json "
                               "`\"message_content_intent\": true` setzen und den Bot neu starten.")
        return
    if att.size > 25 * 1024 * 1024:
        log.warning("Upload zu groß (%d Bytes).", att.size)
        return
    raw = await att.read()
    try:
        text, db = await asyncio.to_thread(check_upload, raw, att.filename)
    except ValueError as e:
        log.warning("Upload abgelehnt: %s", e)
        return
    if test_info(db):
        # Testmodus des Test-Tools: echte Daten bleiben unberührt, Test wird gepostet und nach 10 Min. gelöscht
        uploader = message.author.name if message.author else "?"
        try:
            await message.delete()
        except discord.HTTPException:
            pass
        state.data["last_test_upload"] = int(time.time())
        state.data["last_test_upload_by"] = uploader
        state.save()
        if test_info(db).get("post"):
            try:
                n = await handle_test_upload(db, uploader)
                await post_bot_log(f"🧪 Testdaten von {uploader} empfangen – {n} Nachrichten gepostet, werden nach 10 Minuten gelöscht."
                                   if n else f"🧪 Testdaten von {uploader} empfangen, aber keine DKP-/Loot-Kanäle gefunden "
                                   "(`/raidmaster-einrichten` ausführen).")
            except Exception as e:  # noqa: BLE001
                log.exception("Testdaten konnten nicht gepostet werden")
                await post_bot_log(f"⚠️ Testdaten von {uploader} konnten nicht gepostet werden: {e}")
        else:
            log.info("Upload von %s aus dem Testmodus ignoriert (echte Daten bleiben).", uploader)
            await post_bot_log(f"🧪 Daten von {uploader} kamen aus dem Testmodus (ohne „Test an Discord senden“) – nicht übernommen, echte DKP bleiben.")
        return
    new_version = int((db.get("data") or {}).get("version") or 0)
    current = int((bot.dkp_data or {}).get("version") or 0)
    uploader = message.author.name if message.author else "?"
    if new_version < current and uploader != state.data.get("last_upload_by"):
        log.info("Upload von %s ignoriert: älterer DKP-Stand (%d < %d).", uploader, new_version, current)
        await post_bot_log(f"ℹ️ Daten von {uploader} nicht übernommen: älterer DKP-Stand als der vorhandene.")
        return
    os.makedirs(DATA_DIR, exist_ok=True)
    tmp = UPLOAD_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(tmp, UPLOAD_PATH)
    state.data["last_upload"] = int(time.time())
    state.data["last_upload_by"] = uploader
    state.save()
    log.info("Neue Daten von %s empfangen (%d KB).", uploader, len(text) // 1024)
    if cfg.get("upload_receipts", True):
        players = len((db.get("data") or {}).get("players") or {})
        await post_bot_log(f"📥 Daten von {uploader} empfangen ({players} Spieler) – DKP- und Loot-Kanäle werden aktualisiert.")
    try:
        await message.delete()
    except discord.HTTPException:
        pass
    await process_new_data()


# ---------------------------------------------------------------------------
# Testmodus (RaidMasterTest): DKP, Teilnehmer und Loot wie echt posten, nach 10 Minuten löschen
# ---------------------------------------------------------------------------

TEST_TTL = 600


def test_info(db: dict | None) -> dict | None:
    t = (db or {}).get("testMode")
    return t if isinstance(t, dict) and t.get("active") else None


async def send_test(channel, text: str | None, embeds: list | None = None,
                    file_bytes: bytes | None = None, filename: str = "bild.png", view=None):
    """Testnachricht senden und zum Löschen vormerken (übersteht auch einen Neustart des Bots).
    Zu lange Texte werden in Discord-taugliche Stücke geteilt (max. 2000 Zeichen)."""
    if file_bytes:
        m = await channel.send(content=text or None, file=table_file(file_bytes, filename))
        state.data.setdefault("test_messages", []).append([channel.id, m.id, int(time.time()) + TEST_TTL])
    elif view is not None:
        m = await channel.send(content=text or None, view=view)
        state.data.setdefault("test_messages", []).append([channel.id, m.id, int(time.time()) + TEST_TTL])
    elif embeds:
        m = await channel.send(content=text or None, embeds=embeds)
        state.data.setdefault("test_messages", []).append([channel.id, m.id, int(time.time()) + TEST_TTL])
    else:
        for part in rmd.split_discord(text or ""):
            m = await channel.send(part)
            state.data.setdefault("test_messages", []).append([channel.id, m.id, int(time.time()) + TEST_TTL])
    state.save()


async def handle_test_upload(db: dict, uploader: str):
    data = db.get("data") or {}
    t = test_info(db) or {}
    since = int(t.get("started") or 0)
    log_entries = [e for e in rmd.lua_list(data.get("log"))
                   if isinstance(e, dict) and not e.get("u") and int(e.get("t") or 0) >= since]
    pools = []
    for p in [t.get("pool")] + [e.get("pool") or "mc" for e in log_entries]:
        if p and p not in pools:
            pools.append(str(p))
    head = (f"🧪 **TEST** – aus dem Testmodus von {uploader}, keine echten Daten. "
            f"Wird <t:{int(time.time()) + TEST_TTL}:R> gelöscht.")
    posted = 0
    for pool in pools:
        name = rmd.pool_name(pool, data)
        dkp_ch = await channel_by_id(dkp_channel_for(pool)) or await channel_by_id(cfg.get("botcmd_channel_id"))
        loot_ch = await channel_by_id(raid_channel(pool, "loot") or cfg.get("loot_channel_id")) or dkp_ch
        if not dkp_ch:
            log.info("Test: kein Kanal für %s gefunden.", name)
            continue
        summaries = sorted((x for x in rmd.raid_summaries(data) if x["pool"] == pool and x["t"] >= since),
                           key=lambda x: x["start"])
        # DKP-Kanal: eine Tabelle wie die Seite "DKP-Stände" im Addon – alle Test-Raids zusammengefasst
        rows = rmd.standings(data, pool)
        dkp_head = (f"{head}\n🧪 **DKP-Stände {name}** (Test) – {len(summaries)} Raidabend(e) zusammengefasst")
        for text in await dkp_list_messages(pool, rows, data, db, dkp_head):
            await send_test(dkp_ch, text)
            posted += 1
        # 5) Loot im Loot-Kanal: chronologisch, je Raidabend eine Gruppe
        if loot_ch:
            groups = rmd.loot_by_raid(data, pool, since)
            if groups:
                await send_test(loot_ch, f"{head}\n🧪 **Loot {name}** – {sum(len(g['items']) for g in groups)} Items, nach Raid sortiert.")
                posted += 1
            for g in groups:
                head_line = rmd.format_loot_group(g, "🧪 ")[0].split("\n")[0]
                try:
                    posted += await send_loot_list(loot_ch, g["items"], db, header=head_line, test=True)
                except Exception as ex:  # noqa: BLE001
                    log.warning("Test-Loot mit Symbolen nicht möglich (%s) – als Text.", ex)
                    for text in rmd.format_loot_group(g, "🧪 "):
                        await send_test(loot_ch, text)
                        posted += 1
    log.info("Testdaten von %s gepostet (%d Nachrichten, werden nach %d Min. gelöscht).", uploader, posted, TEST_TTL // 60)
    return posted


@tasks.loop(seconds=60)
async def test_cleanup_loop():
    try:
        await remove_expired_test_raids()
    except Exception:  # noqa: BLE001
        log.exception("Testraids konnten nicht entfernt werden")
    pending = state.data.get("test_messages") or []
    if not pending:
        return
    now = int(time.time())
    keep = []
    for ch_id, msg_id, due in pending:
        if due > now:
            keep.append([ch_id, msg_id, due])
            continue
        try:
            ch = await channel_by_id(ch_id)
            if ch:
                await ch.get_partial_message(int(msg_id)).delete()
        except discord.NotFound:
            pass
        except discord.HTTPException as e:
            if due > now - 3600:      # eine Stunde lang erneut versuchen
                keep.append([ch_id, msg_id, due])
            log.warning("Testnachricht nicht gelöscht: %s", e)
    state.data["test_messages"] = keep
    state.save()


@test_cleanup_loop.before_loop
async def before_test_cleanup():
    await bot.wait_until_ready()


@bot.tree.command(name="uploader", description="Einrichtung des Daten-Uploaders für den PC der Raidleitung (Admins)")
async def uploader_cmd(inter: discord.Interaction):
    if not is_admin(inter.user):
        await inter.response.send_message("Nur Admins (Recht „Server verwalten“).", ephemeral=True)
        return
    ch = await channel_by_id(cfg.get("data_channel_id"))
    if not isinstance(ch, discord.TextChannel):
        await inter.response.send_message("Der Kanal **#bot-daten** fehlt noch – bitte zuerst `/raidmaster-einrichten` ausführen.", ephemeral=True)
        return
    if not ch.permissions_for(ch.guild.me).manage_webhooks:
        await inter.response.send_message(
            "Dem Bot fehlt das Recht **Webhooks verwalten**: Servereinstellungen → Rollen → Raidmaster tool → "
            "Berechtigungen → „Webhooks verwalten“ einschalten → speichern. Danach `/uploader` erneut.", ephemeral=True)
        return
    await inter.response.defer(ephemeral=True, thinking=True)
    hook = None
    for wh in await ch.webhooks():
        if wh.name == "RaidMaster-Uploader" and wh.token:
            hook = wh
            break
    if hook is None:
        hook = await ch.create_webhook(name="RaidMaster-Uploader", reason=f"/uploader von {inter.user}")
    ids = [int(x) for x in cfg.get("uploader_webhooks") or []]
    if hook.id not in ids:
        ids.append(hook.id)
        cfg["uploader_webhooks"] = ids
        save_config()
    conf = {"webhook_url": hook.url, "bot_id": bot.user.id, "savedvariables_path": "", "check_seconds": 10}
    file = discord.File(io.BytesIO(json.dumps(conf, indent=2).encode("utf-8")), filename="uploader_config.json")
    await inter.followup.send(
        "**Daten-Uploader einrichten** (auf dem PC, auf dem du WoW spielst):\n"
        "1. Die Datei unten herunterladen und in den Ordner **uploader** aus dem RaidMaster-Paket legen.\n"
        "2. `uploader.bat` doppelklicken – beim ersten Start sucht er deine RaidMaster-Datei selbst.\n"
        "3. Fertig: Nach jedem `/reload` oder Ausloggen sind DKP, Einteilung und Skillungen nach wenigen Sekunden im Discord.\n"
        "⚠️ Die Datei enthält einen geheimen Link – nicht weitergeben.", file=file, ephemeral=True)


# ---------------------------------------------------------------------------
# Server-Betrieb: Selbst-Update
# ---------------------------------------------------------------------------

async def post_bot_log(text: str):
    ch = await channel_by_id(cfg.get("botcmd_channel_id") or cfg.get("officer_channel_id"))
    if ch:
        try:
            await ch.send(text[:1990])
        except discord.HTTPException:
            pass


async def restart_soon():
    global EXIT_CODE
    EXIT_CODE = updater.RESTART_CODE
    await asyncio.sleep(2)
    await bot.close()


async def apply_update(data: bytes, source: str, ref: str = "", note: str = "") -> str:
    """Installiert eine Update-ZIP. Liefert eine Meldung; startet bei Bot-Änderungen neu."""
    try:
        result = await asyncio.to_thread(updater.install_zip, data, BASE, source, ref)
    except updater.UpdateError as e:
        if ref:
            state.data["failed_sha"] = ref
            state.save()
        text = f"❌ Update ({source}) nicht installiert: {e}"
        await post_bot_log(text)
        return text
    parts = [f"⬇️ **Update** ({source}{' · `' + ref[:7] + '`' if ref else ''})" + (f": {note[:200]}" if note else "")]
    if result.get("addon_version"):
        parts.append(f"Addon: RaidMaster {result['addon_version']}")
    if result["bot_changed"]:
        parts.append(f"Bot: {result['old_version']} → {result['version']} · geändert: {', '.join(result['bot_changed'][:12])}")
        parts.append("Der Bot startet in wenigen Sekunden neu.")
    else:
        parts.append("Bot unverändert.")
        if ref:
            state.data["installed_sha"] = ref
            state.save()
    text = "\n".join(parts)
    await post_bot_log(text)
    if result["bot_changed"]:
        asyncio.create_task(restart_soon())
    else:
        await check_addon_release()
    return text


async def check_github(manual: bool = False) -> str:
    repo = (cfg.get("update_repo") or "").strip()
    if not repo:
        return "Kein GitHub-Repository eingetragen (`update_repo` in config.json)."
    token = (cfg.get("update_token") or "").strip() or None
    branch = cfg.get("update_branch") or "main"
    import aiohttp
    timeout = aiohttp.ClientTimeout(total=120)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        latest = await updater.github_latest(session, repo, branch, token)
        sha = latest["sha"]
        if not sha or sha == state.data.get("installed_sha"):
            return f"✅ Aktuell (Version {updater.bot_version(BASE)}, Commit `{sha[:7]}`)."
        if sha == state.data.get("failed_sha") and not manual:
            return "Letztes Update war fehlerhaft – warte auf eine neue Version."
        data = await updater.github_zip(session, repo, sha, token)
    return await apply_update(data, "GitHub", sha, latest["message"].splitlines()[0] if latest["message"] else "")


@tasks.loop(minutes=30)
async def update_loop():
    if not cfg.get("update_repo"):
        return
    try:
        await check_github(False)
    except updater.UpdateError as e:
        log.warning("Update-Prüfung: %s", e)
    except Exception as e:  # noqa: BLE001 – Netzwerkfehler usw.
        log.warning("Update-Prüfung fehlgeschlagen: %s", e)


@update_loop.before_loop
async def before_update():
    await bot.wait_until_ready()
    await asyncio.sleep(60)


async def confirm_later():
    await asyncio.sleep(150)
    pending = updater.confirm_pending(BASE)
    if pending and pending.get("ref"):
        state.data["installed_sha"] = pending["ref"]
        state.save()


async def report_update_result():
    failed = updater.take_failed(BASE)
    if failed:
        if failed.get("ref"):
            state.data["failed_sha"] = failed["ref"]
            state.save()
        await post_bot_log(f"❌ Das Update auf {failed.get('version')} ist beim Start abgestürzt ({failed.get('reason')}). "
                           f"Die vorherige Version {updater.bot_version(BASE)} läuft wieder.")
    pending = updater.read_json(updater.pending_path(BASE))
    if pending:
        await post_bot_log(f"✅ Update installiert – RaidMaster-Bot **{updater.bot_version(BASE)}** läuft.")
        asyncio.create_task(confirm_later())


@bot.tree.command(name="update", description="Update prüfen bzw. eine Update-ZIP einspielen (Admins)")
@app_commands.describe(datei="Optional: Update-ZIP (RaidMaster-Paket). Leer = auf GitHub nach neuer Version suchen")
async def update_cmd(inter: discord.Interaction, datei: discord.Attachment | None = None):
    if not is_admin(inter.user):
        await inter.response.send_message("Nur Admins (Recht „Server verwalten“).", ephemeral=True)
        return
    await inter.response.defer(ephemeral=True, thinking=True)
    try:
        if datei:
            if not datei.filename.lower().endswith(".zip") or datei.size > 25 * 1024 * 1024:
                await inter.followup.send("Bitte eine ZIP-Datei (max. 25 MB) anhängen.", ephemeral=True)
                return
            text = await apply_update(await datei.read(), f"Upload von {inter.user.display_name}", "", datei.filename)
        else:
            text = await check_github(True)
    except updater.UpdateError as e:
        text = f"❌ {e}"
    except Exception as e:  # noqa: BLE001
        log.exception("Update fehlgeschlagen")
        text = f"❌ Update fehlgeschlagen: {e}"
    await inter.followup.send(text[:1990], ephemeral=True)


# ---------------------------------------------------------------------------
# Server-Betrieb: tägliche Datensicherung
# ---------------------------------------------------------------------------

def make_data_backup() -> str | None:
    if not os.path.isdir(DATA_DIR):
        return None
    folder = os.path.join(BASE, "backup")
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, time.strftime("daten-%Y-%m-%d.zip"))
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        for fn in sorted(os.listdir(DATA_DIR)):
            full = os.path.join(DATA_DIR, fn)
            if os.path.isfile(full) and fn.endswith((".json", ".lua")):
                zf.write(full, fn)
    keep = max(1, int(cfg.get("backup_days") or 7))
    old = sorted(f for f in os.listdir(folder) if f.startswith("daten-") and f.endswith(".zip"))
    for f in old[:-keep]:
        try:
            os.remove(os.path.join(folder, f))
        except OSError:
            pass
    return path


@tasks.loop(hours=1)
async def backup_loop():
    if time.time() - float(state.data.get("last_backup") or 0) < 23 * 3600:
        return
    path = await asyncio.to_thread(make_data_backup)
    state.data["last_backup"] = int(time.time())
    state.save()
    if not path:
        return
    ch = await channel_by_id(cfg.get("data_channel_id"))
    if ch and os.path.getsize(path) < 8 * 1024 * 1024:
        try:
            await ch.send("💾 Tägliche Sicherung der Bot-Daten (Raids, Charaktere, DKP-Datei).",
                          file=discord.File(path))
        except discord.HTTPException as e:
            log.warning("Sicherung konnte nicht gepostet werden: %s", e)


@backup_loop.before_loop
async def before_backup():
    await bot.wait_until_ready()


IMPORT_FILES = ("raids.json", "profiles.json", "state.json", "RaidMaster.lua")


@bot.tree.command(name="daten-import", description="Bot-Daten aus einer Sicherung übernehmen, z. B. beim Umzug auf den Server (Admins)")
@app_commands.describe(datei="Sicherungs-ZIP aus #bot-daten (daten-JJJJ-MM-TT.zip)")
async def import_cmd(inter: discord.Interaction, datei: discord.Attachment):
    if not is_admin(inter.user):
        await inter.response.send_message("Nur Admins (Recht „Server verwalten“).", ephemeral=True)
        return
    if not datei.filename.lower().endswith(".zip") or datei.size > 25 * 1024 * 1024:
        await inter.response.send_message("Bitte die Sicherungs-ZIP anhängen.", ephemeral=True)
        return
    await inter.response.defer(ephemeral=True, thinking=True)
    raw = await datei.read()
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as zf:
            names = {os.path.basename(n): n for n in zf.namelist() if os.path.basename(n) in IMPORT_FILES}
            if "raids.json" not in names and "profiles.json" not in names:
                await inter.followup.send("In der ZIP sind keine Bot-Daten (raids.json / profiles.json).", ephemeral=True)
                return
            contents = {}
            for base_name, member in names.items():
                data = zf.read(member)
                if base_name.endswith(".json"):
                    json.loads(data.decode("utf-8"))
                contents[base_name] = data
    except (zipfile.BadZipFile, ValueError, UnicodeDecodeError) as e:
        await inter.followup.send(f"Die Sicherung ist beschädigt: {e}", ephemeral=True)
        return
    await asyncio.to_thread(make_data_backup)
    os.makedirs(DATA_DIR, exist_ok=True)
    for base_name, data in contents.items():
        with open(os.path.join(DATA_DIR, base_name), "wb") as f:
            f.write(data)
    await inter.followup.send(
        f"✅ Übernommen: {', '.join(sorted(contents))}. Der Bot startet neu, um die Daten zu laden.", ephemeral=True)
    log.info("Daten-Import von %s: %s", inter.user, ", ".join(sorted(contents)))
    asyncio.create_task(restart_soon())


# ---------------------------------------------------------------------------
# PUG-Einladungslink: wer darüber beitritt, bekommt automatisch die Rolle Gast
# ---------------------------------------------------------------------------

def bot_guild():
    return bot.get_guild(int(cfg["guild_id"])) if cfg.get("guild_id") else None


async def fetch_invite_uses(guild) -> dict[str, int] | None:
    if guild is None or not guild.me.guild_permissions.manage_guild:
        return None
    try:
        return {i.code: int(i.uses or 0) for i in await guild.invites()}
    except discord.HTTPException:
        return None


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
            f"👋 Willkommen auf **{member.guild.name}**!\n"
            f"Für unsere PUG-Raids: In {pug} auf **Als PUG-Spieler registrieren** klicken, Charakter festlegen, "
            "dann bei einem Raid anmelden. Soft Reserve und Loot laufen über softres.it (Link am Raid). Viel Spaß!")
    except discord.HTTPException:
        pass


@bot.tree.command(name="pug-einladung", description="Einladungslink für PUG-Spieler (bekommen automatisch die Rolle Gast)")
async def pug_invite_cmd(inter: discord.Interaction):
    if not is_creator(inter.user):
        await inter.response.send_message("Nur Offiziere bzw. die Raidleitung.", ephemeral=True)
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
    if msg_id:
        if not update:
            return "Willkommenstext ist bereits eingetragen."
        try:
            await channel.get_partial_message(int(msg_id)).edit(content=text, allowed_mentions=no_ping)
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
    state.save()
    log.info("Willkommenstext in #%s eingetragen.", channel.name)
    return f"✅ Willkommenstext in {channel.mention} eingetragen."


@bot.tree.command(name="willkommen", description="Willkommenstext in #willkommen aktualisieren, z. B. mit neuem Gildennamen (Admins)")
@app_commands.describe(gildenname="Name eurer Gilde (wird gespeichert)")
async def welcome_cmd(inter: discord.Interaction, gildenname: str | None = None):
    if not is_admin(inter.user):
        await inter.response.send_message("Nur Admins (Recht „Server verwalten“).", ephemeral=True)
        return
    if gildenname:
        cfg["guild_name"] = gildenname.strip()
        save_config()
    await inter.response.send_message(await ensure_welcome(update=True), ephemeral=True)


# ---------------------------------------------------------------------------
# Befehlsliste im Offiziersbereich (nur der Bot schreibt, wird automatisch aktuell gehalten)
# ---------------------------------------------------------------------------

COMMAND_INFO = {
    # Befehl: (Wer, Bereich)
    "raid erstellen": ("Offiziere", "Raids"),
    "raid softres": ("Offiziere", "Raids"),
    "raid aufstellung": ("Offiziere", "Raids"),
    "raid liste": ("Offiziere", "Raids"),
    "raid schliessen": ("Offiziere", "Raids"),
    "raid oeffnen": ("Offiziere", "Raids"),
    "raid absagen": ("Offiziere", "Raids"),
    "raid export": ("Offiziere", "Raids"),
    "raid taktik": ("Offiziere", "Raids"),
    "pug-einladung": ("Offiziere", "Raids"),
    "charakter": ("alle", "Spieler"),
    "dkp": ("alle", "Spieler"),
    "dkpliste": ("alle", "Spieler"),
    "addon": ("alle", "Spieler"),
    "raidmaster-status": ("Offiziere", "Verwaltung"),
    "raidmaster-einrichten": ("Admins", "Verwaltung"),
    "addon-hochladen": ("Admins", "Verwaltung"),
    "willkommen": ("Admins", "Verwaltung"),
    "uploader": ("Admins", "Verwaltung"),
    "update": ("Admins", "Verwaltung"),
    "daten-import": ("Admins", "Verwaltung"),
}
SECTION_ORDER = [("Raids", "⚔️"), ("Spieler", "👤"), ("Verwaltung", "🛠️")]


# Befehle im Spiel (Addon RaidMaster) – stehen unter den Bot-Befehlen
ADDON_COMMAND_BLOCKS = [
    "🎮 **Im Spiel – Addon RaidMaster** (in den Chat tippen)\n"
    "**`/rm`** – RaidMaster-Fenster öffnen/schließen _(alle)_\n"
    "**`/rm adds`** – alle sichtbaren Adds auf einmal nach der Vorlage des Bosses markieren, z. B. Garrs Feuerschwörer "
    "(Gegner-Namensplaketten an, Taste V) _(Raidleitung/Assistenten)_\n"
    "**`/rm clear`** – alle Schlachtzugsymbole auf einmal entfernen _(Raidleitung/Assistenten)_\n"
    "**`/rm bar`** – Symbolleiste ein-/ausblenden _(alle)_\n"
    "**`/rm minimap`** – Minimap-Knopf ein-/ausblenden _(alle)_\n"
    "**`/rm sync`** – DKP-Daten von anderen Addon-Nutzern abgleichen _(alle)_\n"
    "**`/rm version`** – Addon-Version, erkannte Spielversion und Sprache anzeigen _(alle)_\n"
    "**`/rm reset`** – Fensterpositionen zurücksetzen (lädt das Interface neu) _(alle)_",
    "💬 **Im Spiel – Flüstern an den Plündermeister** (auch ohne Addon)\n"
    "**`!bid 50`** – bei einer laufenden Versteigerung 50 DKP bieten _(alle)_\n"
    "**`!dkp`** – eigenen DKP-Stand abfragen _(alle)_\n"
    "**`inv`** – an den Raidleiter flüstern: Einladung in den Raid, solange Werbung läuft _(alle)_",
    "⌨️ **Tastenbelegung im Spiel** – Esc → Tastaturbelegung → RaidMaster: Fenster, nächstes freies Symbol, "
    "einzelne Symbole, **Adds markieren**, **Alle Symbole entfernen**.",
]


def command_list_text() -> list[str]:
    """Liste aller Slash-Befehle aus dem Befehlsbaum – neue Befehle erscheinen automatisch."""
    entries = []
    for cmd in bot.tree.get_commands():
        subs = getattr(cmd, "commands", None)
        if subs:
            for sub in subs:
                entries.append((f"{cmd.name} {sub.name}", sub.description, [p.name for p in sub.parameters]))
        else:
            entries.append((cmd.name, cmd.description, [p.name for p in getattr(cmd, "parameters", [])]))
    blocks = [f"📖 **Alle Bot-Befehle** · RaidMaster-Bot {updater.bot_version(BASE)}\n"
              "Befehl im Chat mit `/` beginnen und aus der Liste wählen. Diese Liste aktualisiert der Bot selbst."]
    by_section: dict[str, list[str]] = {}
    for name, desc, params in sorted(entries):
        who, section = COMMAND_INFO.get(name, ("alle", "Sonstiges"))
        opts = (" · " + " ".join(f"`{p}`" for p in params)) if params else ""
        by_section.setdefault(section, []).append(f"**`/{name}`** – {desc} _({who})_{opts}")
    order = SECTION_ORDER + [(s, "•") for s in by_section if s not in dict(SECTION_ORDER)]
    for section, emoji in order:
        if by_section.get(section):
            blocks.append(f"{emoji} **{section}**\n" + "\n".join(by_section[section]))
    blocks.append("_Offiziere = Rollen Offizier/Raidleitung · Admins = Recht „Server verwalten“_")
    blocks.extend(ADDON_COMMAND_BLOCKS)
    return rmd.chunk_blocks(blocks)


async def ensure_command_list() -> str:
    guild = bot_guild()
    if guild is None:
        return "Befehlsliste: Server nicht gefunden."
    channel = await channel_by_id(cfg.get("command_list_channel_id")) or discord.utils.get(guild.text_channels, name="befehlsliste")
    if channel is None:
        return "Befehlsliste: Kanal #befehlsliste fehlt – `/raidmaster-einrichten` ausführen."
    parts = command_list_text()
    old_ids = list(state.data.get("command_list_messages") or [])
    new_ids = []
    no_ping = discord.AllowedMentions(roles=False, users=False, everyone=False)
    for i, text in enumerate(parts):
        if i < len(old_ids):
            try:
                await channel.get_partial_message(int(old_ids[i])).edit(content=text, allowed_mentions=no_ping)
                new_ids.append(old_ids[i])
                continue
            except discord.HTTPException:
                pass
        msg = await channel.send(text, allowed_mentions=no_ping)
        new_ids.append(msg.id)
    for mid in old_ids[len(parts):]:
        try:
            await channel.get_partial_message(int(mid)).delete()
        except discord.HTTPException:
            pass
    state.data["command_list_messages"] = new_ids
    state.save()
    return f"✅ Befehlsliste in {channel.mention} aktuell."


@dkp_loop.before_loop
async def before_dkp():
    await bot.wait_until_ready()


if __name__ == "__main__":
    try:
        bot.run(cfg["token"], log_handler=None)
    except discord.PrivilegedIntentsRequired:
        # Server Members Intent im Entwicklerportal nicht eingeschaltet -> ohne Beitritts-Erkennung neu starten
        log.error("Server Members Intent ist im Discord-Entwicklerportal nicht eingeschaltet – "
                  "starte ohne PUG-Beitrittserkennung neu (siehe /pug-einladung).")
        state.data["members_intent_missing"] = True
        state.save()
        sys.exit(updater.RESTART_CODE)
    sys.exit(EXIT_CODE)
