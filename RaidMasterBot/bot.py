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
import os
import sys
import re
import time

import discord
from discord import app_commands
from discord.ext import tasks

import raidmaster_data as rmd
import guildbank
import uploader_setup
import member_area
import market
from bot_hilfen import (  # noqa: E402 – D-3 Schritt 1: Hilfen ohne Zustand
    check_upload,
    test_info,
)
import server_setup
import updater

from kern import (  # noqa: E402 – D-3 Schritt 2: gemeinsame Objekte, nur einmal vorhanden
    BASE,
    DATA_DIR,
    log,
    CONFIG_ERROR,
    save_config,
    cfg,
    TZ,
    book,
    state,
    UPLOAD_PATH,
    GS_UPLOAD_PATH,
    GS_READY_PATH,
    SHOTS_DIR,
)

market.set_tz(TZ)          # D-MN7d: Marktberichte in der Zeitzone des Bots
from grund import (  # noqa: E402 – D-3 Schritt 3: Grundfunktionen
    bot_guild,
    channel_by_id,
    is_admin,
    post_bot_log,
)
import grund  # noqa: E402

# ---------------------------------------------------------------------------
# Bot
# ---------------------------------------------------------------------------


# Verweigert Discord einen "Privileged Intent", startet der Bot ohne ihn neu – aber höchstens einmal je Intent
# (ab Bot 1.5.107). Bis 1.5.106 konnte ein eingeschalteter Message Content Intent, der im Entwicklerportal aus ist,
# eine endlose Sofort-Neustart-Schleife auslösen (jeder Versuch = eine Verbindung zu Discord; Discord setzt den
# Token nach rund 1000 Verbindungen zurück).
MESSAGE_CONTENT_RETRY = 6 * 3600     # danach einmal wieder mit Message Content Intent versuchen


def message_content_blocked() -> bool:
    t = state.data.get("message_content_intent_missing")
    return bool(t) and time.time() - float(t) < MESSAGE_CONTENT_RETRY


class RaidBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        # nur nötig, falls Uploads trotz Erwähnung des Bots ohne Anhang ankommen (siehe ANLEITUNG)
        intents.message_content = bool(cfg.get("message_content_intent", False)) and not message_content_blocked()
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
        icon_map_loop.start()
        monthly_loop.start()
        test_cleanup_loop.start()
        tb_cleanup_loop.start()

    async def on_guild_join(self, guild):
        """UP-404 (c): nach dem (Wieder-)Einladen Befehle sofort für diesen Server anmelden – ohne Neustart."""
        log.warning("Bot wurde auf einen Server eingeladen: %s", guild.id)
        try:
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            log.info("Befehle nach dem Einladen für den Server synchronisiert.")
        except discord.HTTPException as e:
            log.error("Befehle nach dem Einladen nicht synchronisiert: %s", e)
        await check_bot_rights("Einladung")

    async def on_guild_remove(self, guild):
        """UP-404 (b): Entfernen sofort und deutlich im Protokoll (posten geht dann nicht mehr)."""
        log.error("Bot nicht auf dem Server: Der Bot wurde vom Server %s entfernt. Uploads und Befehle gehen erst "
                  "wieder nach einer neuen Einladung.", guild.id)

    async def on_ready(self):
        log.info("Angemeldet als %s – bereit (Version %s).", self.user, updater.bot_version(BASE))
        if cfg.get("message_content_intent") and not self.intents.message_content \
                and not getattr(self, "_mc_warned", False):
            self._mc_warned = True
            try:
                await post_bot_log("⚠️ Gestartet **ohne Message Content Intent**: Er steht in config.json auf true, ist im "
                                   "Discord-Entwicklerportal aber aus (Bot → Privileged Gateway Intents). Bitte dort "
                                   "einschalten – der Bot versucht es beim nächsten Neustart nach frühestens 6 Stunden wieder "
                                   "(oder sofort: `sudo systemctl restart raidmaster`, nachdem der Intent eingeschaltet ist).")
            except Exception:  # noqa: BLE001
                pass
        if not (cfg.get("guild_leader") or "").strip() and not getattr(self, "_leader_warned", False):
            # ab 1.5.112: ohne Eintrag hat der Gildenchef nur Rechte als Server-Besitzer oder Offizier
            self._leader_warned = True
            log.warning("config.json: \"guild_leader\" ist leer – Charaktername des Gildenchefs eintragen "
                        "(sonst Rechte nur als Server-Besitzer oder Offizier).")
        asyncio.create_task(market_catchup())        # D-MN7e: Pakete während des Neustarts nachlesen
        await check_bot_rights("Start")                # UP-404 (b): nie still ohne Server oder ohne Rechte
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
                rep = await sync_raid_visibility()
                if rep:
                    await post_bot_log("🗂️ Raid-Kategorien: " + "; ".join(rep) + " (noch nicht angekündigte Raids sehen nur "
                                       "Offiziere; eingeblendet wird ein Raid, sobald Blizzard ihn für WoW Forever ankündigt).")
            except Exception:
                log.exception("Sichtbarkeit der Raid-Kategorien konnte nicht abgeglichen werden")
            try:
                rep = await apply_fixed_guild_name()
                if rep:
                    await post_bot_log("🏔️ Gildenname **" + FIXED_GUILD_NAME + "**: " + "; ".join(rep))
            except Exception:
                log.exception("Gildenname konnte nicht übernommen werden")
            try:
                power = members_with_power()
                key = "|".join(sorted(power))
                if power and state.data.get("power_warned") != key:
                    state.data["power_warned"] = key
                    state.save()
                    await post_bot_log("🔐 Im Discord sollen nur der Gildenchef und die Offiziere etwas verändern. Diese Mitglieder "
                                       "haben trotzdem Verwaltungsrechte (Servereinstellungen → Rollen prüfen): " + "; ".join(power))
            except Exception:
                log.exception("Rechte-Prüfung fehlgeschlagen")
            try:
                guild0 = bot_guild()
                if guild0 is not None and guild0.me.guild_permissions.manage_channels:
                    rep = await server_setup.ensure_assignment_channels(guild0, cfg)
                    save_config()
                    if rep:
                        await post_bot_log("📋 Einteilung je Raid: " + "; ".join(rep))
            except Exception:
                log.exception("Einteilungs-Kanäle konnten nicht angelegt werden")
            try:
                guild0 = bot_guild()
                if guild0 is not None and guild0.me.guild_permissions.manage_channels:
                    rep = await server_setup.ensure_raid_extra_channels(guild0, cfg)
                    if rep:
                        await post_bot_log("🆕 Zusätzliche Raid-Kanäle: " + "; ".join(rep))
            except Exception:
                log.exception("Zusätzliche Raid-Kanäle konnten nicht angelegt werden")
            try:
                guild0 = bot_guild()
                if guild0 is not None and guild0.me.guild_permissions.manage_channels:
                    rep = await server_setup.ensure_dungeon_category(guild0)
                    if rep:
                        await post_bot_log("🗝️ Dungeon-Sprachkanäle: " + "; ".join(rep))
            except Exception:
                log.exception("Dungeon-Kategorie konnte nicht angelegt werden")
            try:
                guild0 = bot_guild()
                if guild0 is not None and not state.data.get("afk_moved") \
                        and guild0.me.guild_permissions.manage_channels:
                    rep = await server_setup.move_afk_to_general(guild0)
                    state.data["afk_moved"] = True
                    state.save()
                    if rep:
                        await post_bot_log("🔊 " + "; ".join(rep))
            except Exception:
                log.exception("Sprachkanal AFK konnte nicht verschoben werden")
            try:
                guild0 = bot_guild()
                if guild0 is not None and not state.data.get("apply_on_top") \
                        and guild0.me.guild_permissions.manage_channels:
                    rep = await server_setup.place_first(guild0, member_area.APPLY_CATEGORY,
                                                         "RaidMaster: Bewerbung ganz oben (Wunsch Gildenleitung)")
                    if server_setup._find(guild0.categories, member_area.APPLY_CATEGORY) is not None:
                        state.data["apply_on_top"] = True
                        state.save()
                    if rep:
                        await post_bot_log("; ".join(rep))
            except Exception:
                log.exception("Bewerbung konnte nicht nach oben verschoben werden")
            try:
                guild0 = bot_guild()
                if guild0 is not None and not state.data.get("disboard_manage_channels_dropped") \
                        and guild0.me.guild_permissions.manage_roles:
                    rep = await server_setup.drop_disboard_manage_channels(guild0)
                    if not any(r.startswith("⚠️") for r in rep):
                        state.data["disboard_manage_channels_dropped"] = True
                        state.save()
                    if rep:
                        await post_bot_log("; ".join(rep))
            except Exception:
                log.exception("DISBOARD-Recht konnte nicht angepasst werden")
            try:
                guild0 = bot_guild()
                if guild0 is not None and guild0.me.guild_permissions.manage_channels:
                    _, rep = await server_setup.ensure_channel_if_missing(guild0, server_setup.GENERAL, "Gildenhalle",
                                                                          "RaidMaster: Sprachkanal für Gildenmitglieder")
                    if rep:
                        await post_bot_log("🔊 " + "; ".join(rep))
            except Exception:
                log.exception("Sprachkanal Gildenhalle konnte nicht angelegt werden")
            try:
                rep = await maintain_member_area()
                if rep:
                    await post_bot_log("🔐 Nur für Mitglieder freigegeben: " + ", ".join(rep))
            except Exception:
                log.exception("Mitglieder-Bereich konnte nicht abgeglichen werden")
            try:
                guild0 = bot_guild()
                if guild0 is not None and not state.data.get("addon_channels_members") \
                        and guild0.me.guild_permissions.manage_roles:
                    rep = await server_setup.open_addon_channels_to_members(guild0)
                    state.data["addon_channels_members"] = True
                    state.save()
                    if rep:
                        await post_bot_log("📦 Addon's by GoldSentinel ist jetzt für alle Gildenmitglieder sichtbar "
                                           "(schreiben: Offiziere und Bot): " + ", ".join(rep))
            except Exception:
                log.exception("Addon-Kanäle konnten nicht für Mitglieder freigegeben werden")
            try:
                rep = await clear_channels_once()
                if rep:
                    await post_bot_log("\n".join(rep))
            except Exception:
                log.exception("Kanäle konnten nicht geleert werden")
            try:
                rep = await remove_unused_channels_once()
                if rep:
                    await post_bot_log("\n".join(rep))
            except Exception:
                log.exception("Ungenutzte Kanäle konnten nicht geprüft werden")
            try:
                await post_welcome_invite_once()
            except Exception:
                log.exception("Einladung für #willkommen konnte nicht gemeldet werden")
            try:
                rep = await ensure_channel_texts()
                if rep:
                    await post_bot_log("✏️ Texte im neuen Stil: " + ", ".join(rep))
            except Exception:
                log.exception("Kanaltexte konnten nicht aktualisiert werden")
            try:
                rep = await ensure_voice_limits()
                if rep:
                    await post_bot_log("👥 Raid-Sprachkanäle begrenzt auf die Raidgröße: " + ", ".join(rep))
            except Exception:
                log.exception("Platzzahl der Raid-Sprachkanäle konnte nicht gesetzt werden")
            try:
                rep = await ensure_dkp_rules()
                if rep:
                    await post_bot_log("📜 " + "; ".join(rep))
            except Exception:
                log.exception("DKP- und Raid-Regeln konnten nicht gepostet werden")
            try:
                rep = await ensure_guild_rules()
                if rep:
                    log.info("Gildenregeln: %s", "; ".join(rep))
                    await post_bot_log("📜 Gildenregeln: " + "; ".join(rep))
            except Exception:
                log.exception("Gildenregeln konnten nicht angelegt werden")
            try:
                await post_guild_bank()
            except Exception:
                log.exception("Gildenbank-Bestand konnte nicht gepostet werden")
            try:
                rep = await ensure_test_channel()
                if rep:
                    log.info("Testberichte: %s", rep)
                    await post_bot_log(rep)
            except Exception:
                log.exception("#testberichte konnte nicht angelegt werden")
            try:
                await repair_missing_announcements()
            except Exception:
                log.exception("Fehlende Ankündigungen nicht geprüft")
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
            try:
                log.info(await ensure_name_poll())
            except Exception:
                log.exception("Abstimmung über den Gildennamen konnte nicht eingerichtet werden")
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
        route = uploader_setup.route_message(cfg, message.channel.id, message.webhook_id)
        if route == "ignore":
            if uploader_setup.market_source(cfg, message.channel.id, message.webhook_id):
                await market_intake_safe(message)      # MN7: nur GSMARKT1 still mitlesen
            return              # #testberichte: liest die Addon-Prüfung – nie antworten, nie löschen
        if route == "upload":
            try:
                await receive_upload(message)
            except Exception:
                log.exception("Upload konnte nicht verarbeitet werden")
            return
        if (cfg.get("name_poll_channel_id") and message.channel.id == int(cfg["name_poll_channel_id"])
                and not message.author.bot and message.type == discord.MessageType.default):
            try:
                await handle_name_post(message)
            except Exception:
                log.exception("Gildennamen-Vorschlag konnte nicht verarbeitet werden")


bot = RaidBot()
grund.bot = bot          # D-3 Schritt 3: die Grundfunktionen in grund.py benutzen dasselbe Bot-Objekt
import markt_bot  # noqa: E402 – D-3 Schritt 4: Marktdaten (meldet /marktdaten an, darum erst hier)
from markt_bot import (  # noqa: E402
    market_catchup,
    market_intake,
    market_intake_safe,
)
import rechte_bot  # noqa: E402 – D-3 Schritt 5: Rechte des Bots (UP-404)
from rechte_bot import check_bot_rights  # noqa: E402
import pn_bot  # noqa: E402,F401 – D-3 Schritt 6: /pn (meldet den Befehl beim Import an, darum erst hier)
import symbole_bot  # noqa: E402,F401 – D-3 Schritt 7: Symbole, Emojis, Wowhead
import ruhmeshalle_bot  # noqa: E402,F401 – D-3 Schritt 8: Ruhmeshalle (meldet zwei Befehle beim Import an)
from ruhmeshalle_bot import (  # noqa: E402
    update_hall_of_fame,
)
import uploader_bot  # noqa: E402,F401 – D-3 Schritt 9: Uploader-Versand (meldet /uploader beim Import an)
import bank_bot  # noqa: E402,F401 – D-3 Schritt 10: Gildenbank und Raidfähigkeit (meldet /bank beim Import an)
from bank_bot import (  # noqa: E402
    post_guild_bank,
    post_raid_ready,
)
import regeln_bot  # noqa: E402,F401 – D-3 Schritt 11: Regeln
from regeln_bot import (  # noqa: E402
    ensure_dkp_rules,
    ensure_guild_rules,
)
import beute_bot  # noqa: E402,F401 – D-3 Schritt 12: Beute-Datenbank (meldet /beute beim Import an)
from beute_bot import update_lootdb  # noqa: E402
import klassen_bot  # noqa: E402,F401 – D-3 Schritt 13: Klassenfarben
from klassen_bot import sync_class_roles  # noqa: E402
import willkommen_bot  # noqa: E402,F401 – D-3 Schritt 14: Willkommen (meldet /willkommen und /einladung an)
from willkommen_bot import (  # noqa: E402
    ensure_welcome,
    post_welcome_invite_once,
)
import gildenname_bot  # noqa: E402,F401 – D-3 Schritt 15: Gildenname (meldet /gildenname beim Import an)
from gildenname_bot import (  # noqa: E402
    FIXED_GUILD_NAME,
    apply_fixed_guild_name,
    ensure_name_poll,
    handle_name_post,
)
import befehlsliste_bot  # noqa: E402,F401 – D-3 Schritt 16: Befehlslisten
from befehlsliste_bot import ensure_command_list  # noqa: E402
import mitglieder_bot  # noqa: E402,F401 – D-3 Schritt 17: Mitglieder-Bereich und Bewerbung
from mitglieder_bot import maintain_member_area  # noqa: E402
import ankuendigung_bot  # noqa: E402,F401 – D-3 Schritt 18: Addon-Versionen und Ankündigungen
from ankuendigung_bot import ANNOUNCE_DIR, check_addon_release  # noqa: E402
import update_bot  # noqa: E402,F401 – D-3 Schritt 20: Selbst-Update (meldet /update beim Import an)
from update_bot import report_update_result, update_loop  # noqa: E402
import betrieb_bot  # noqa: E402,F401 – D-3 Schritt 21: Server-Betrieb (meldet /daten-import beim Import an)
from betrieb_bot import backup_loop, icon_map_loop, tb_cleanup_loop  # noqa: E402
import pug_bot  # noqa: E402,F401 – D-3 Schritt 22: PUG-Einladung (meldet /pug-einladung beim Import an)
from pug_bot import handle_member_join, refresh_invite_cache  # noqa: E402
import handwerk_bot  # noqa: E402,F401 – D-3 Schritt 23: Berufe-Verzeichnis (meldet /handwerk, /berufe an)
import ereignis_bot  # noqa: E402,F401 – D-3 Schritt 23: Discord-Ereignisse (meldet /raid-ereignisse an)
import raidanzeige_bot  # noqa: E402,F401 – D-3 Schritt 24: Raid-Anzeige
from raidanzeige_bot import update_raid_message  # noqa: E402
import twink_bot  # noqa: E402,F401 – D-3 Schritt 24: Twinks (meldet /twink beim Import an)
from skillung_bot import sync_specs  # noqa: E402 – D-3 Schritt 25: Skillung übernehmen
from dkp_tafel_bot import (  # noqa: E402 – D-3 Schritt 26: DKP-Tabellen und Raid-Abrechnung
    post_dkp_tables,
    post_raid_summaries,
    remove_overall,
)
from beutepost_bot import post_new_loot  # noqa: E402 – D-3 Schritt 27: Beute-Posts
import dkp_nachricht_bot  # noqa: E402,F401 – D-3 Schritt 27: persönliche DKP-Nachricht (meldet /dkp-nachricht an)
from dkp_nachricht_bot import send_raid_dms  # noqa: E402
import monatlich_bot  # noqa: E402,F401 – D-3 Schritt 28: Monatliches, Raider des Monats (meldet /raider-des-monats an)
from monatlich_bot import monthly_loop  # noqa: E402
from testupload_bot import handle_test_upload, test_cleanup_loop  # noqa: E402 – D-3 Schritt 29: Testmodus
from kanalpflege_bot import (  # noqa: E402 – D-3 Schritt 30: Kanalpflege
    clear_channels_once,
    ensure_channel_texts,
    ensure_listed_raid_categories,
    ensure_new_raid_categories,
    ensure_voice_limits,
    remove_unused_channels_once,
    sync_raid_visibility,
)
import dkp_befehle_bot  # noqa: E402,F401 – D-3 Schritt 31: DKP-Befehle (meldet /dkp, /dkpliste, /raidmaster-status an)
from dkp_befehle_bot import reload_dkp_if_needed  # noqa: E402
import raid_bot  # noqa: E402,F401 – D-3 Schritt 32: Raids (meldet /raid und /rekorde beim Import an)
from raid_bot import (  # noqa: E402
    post_all_tactics,
    process_assignment,
    reminder_loop,
)
import anmeldung_bot  # noqa: E402,F401 – D-3 Schritt 33: Anmeldung (on_interaction, /charakter)

# ---------------------------------------------------------------------------
# Hilfen
# ---------------------------------------------------------------------------


POWER_PERMS = ("administrator", "manage_guild", "manage_channels", "manage_roles", "manage_messages", "manage_webhooks")


def members_with_power() -> list[str]:
    """Mitglieder (keine Bots), die über Discord-Rechte den Server ändern können, aber weder Gildenchef noch
    Offizier sind – der Bot meldet sie im Bot-Log, damit die Rechte angepasst werden können."""
    guild = bot_guild()
    out = []
    for m in (guild.members if guild else []):
        if m.bot or is_admin(m):
            continue
        perms = m.guild_permissions
        names = [p for p in POWER_PERMS if getattr(perms, p, False)]
        if names:
            out.append(f"{m.display_name} ({', '.join(names)})")
    return out


# ---------------------------------------------------------------------------
# Charakterprofil, Knöpfe an den Raid-Nachrichten, /charakter: ab 1.5.180 in anmeldung_bot.py.
# /dkp, /dkpliste, /raidmaster-status: ab 1.5.178 in dkp_befehle_bot.py. Hier: /raidmaster-einrichten
# ---------------------------------------------------------------------------
@bot.tree.command(name="raidmaster-einrichten", description="Legt Kanäle, Rollen und Berechtigungen für die Gilde automatisch an")
async def setup_cmd(inter: discord.Interaction):
    member = inter.user
    if not is_admin(member):
        await inter.response.send_message("Die Einrichtung dürfen nur der Gildenchef und die Offiziere starten.", ephemeral=True)
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
        report += await ensure_dkp_rules()
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
        try:
            rep = await sync_raid_visibility()
            if rep:
                await post_bot_log("🗂️ Raid-Kategorien: " + "; ".join(rep))
        except Exception:  # noqa: BLE001
            log.exception("Sichtbarkeit der Raid-Kategorien konnte nicht abgeglichen werden")
        try:
            rep = await maintain_member_area()
            if rep:
                await post_bot_log("🔐 Nur für Mitglieder freigegeben: " + ", ".join(rep))
        except Exception:  # noqa: BLE001
            log.exception("Mitglieder-Bereich konnte nicht abgeglichen werden")
        await post_raid_summaries()
        await post_dkp_tables()
        await remove_overall()
        await post_new_loot()
        await update_lootdb()
        await update_hall_of_fame()
        await post_guild_bank()
        await send_raid_dms()
        await process_assignment()
    except discord.HTTPException as e:
        log.warning("Posten fehlgeschlagen: %s", e)


# ---------------------------------------------------------------------------
# Eigene Beute-Datenbank (/beute): ab 1.5.157 in beute_bot.py. Beute-Posts nach dem Raid: ab 1.5.174 in
# beutepost_bot.py. Persönliche DKP-Nachricht: ab 1.5.174 in dkp_nachricht_bot.py.
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Ruhmeshalle (#ruhmeshalle): Erstkills, Rekord-Tafeln, Aufräumen, /erfolge stehen ab 1.5.153 in ruhmeshalle_bot.py;
# hier noch /rekorde (braucht raid_pool_autocomplete) und Raider des Monats
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Gildenbank (/bank, Bestand in #gildenbank) und Raidfähigkeit: ab 1.5.155 in bank_bot.py
# Beute-Datenbank (/beute, Beutetabellen): ab 1.5.157 in beute_bot.py
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Klassenfarben (Rollen in WoW-Klassenfarbe): ab 1.5.158 in klassen_bot.py.
# Skillung aus dem Spiel in die Raid-Anmeldungen übernehmen (sync_specs): ab 1.5.172 in skillung_bot.py.
# Ersatz bei Absage (offer_substitute, accept_substitute): ab 1.5.172 in ersatz_bot.py.
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Addon-Versionen (neue ZIP im Ordner "addon") und Ankündigungen: ab 1.5.164 in ankuendigung_bot.py
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Server-Betrieb: Daten-Upload vom PC der Raidleitung
# ---------------------------------------------------------------------------

async def receive_upload(message: discord.Message):
    allowed = [int(x) for x in cfg.get("uploader_webhooks") or []]
    if allowed and message.webhook_id not in allowed:
        log.warning("Upload von unbekanntem Webhook %s ignoriert.", message.webhook_id)
        return
    try:
        await market_intake(message)          # MN7: GSMARKT1-Zeilen aus allen Anhängen (vor dem Löschen der Nachricht)
    except Exception:  # noqa: BLE001
        log.exception("Marktdaten konnten nicht gelesen werden")
    # Anhänge nach Dateinamen: RaidMaster.lua(.gz) wie bisher, GuildSentinel.lua(.gz) nur für den Gildenbank-Bestand.
    # Ein alter Uploader schickt nur RaidMaster.lua.gz – das funktioniert unverändert.
    rm_i, gs_i = rmd.pick_upload_files([a.filename for a in message.attachments])
    att = message.attachments[rm_i] if rm_i is not None else None
    gs_att = message.attachments[gs_i] if gs_i is not None else None
    gs_has_bank = False         # D-GS1b: auch bei einer GuildSentinel-Datei > 25 MB gesetzt
    if gs_att is not None and gs_att.size > 25 * 1024 * 1024:
        log.warning("GuildSentinel-Datei %s ist zu gross (%.1f MB > 25 MB) – nicht gelesen.", gs_att.filename,
                    gs_att.size / 1024 / 1024)
    if gs_att is not None and gs_att.size <= 25 * 1024 * 1024:
        try:
            gs_text, gs_db = await asyncio.to_thread(rmd.check_guildsentinel_upload, await gs_att.read(), gs_att.filename)
            gs_has_bank = rmd.guild_bank(gs_db) is not None
            # ohne Gildenbank (nur Raidfähigkeit) getrennt ablegen: der Bank-Stand bleibt unverändert (D-GS1)
            gs_path = GS_UPLOAD_PATH if gs_has_bank else GS_READY_PATH
            os.makedirs(DATA_DIR, exist_ok=True)
            tmp_gs = gs_path + ".tmp"
            with open(tmp_gs, "w", encoding="utf-8") as f_gs:
                f_gs.write(gs_text)
            os.replace(tmp_gs, gs_path)
            log.info("GuildSentinel-Daten empfangen (%s).", "Gildenbank" if gs_has_bank else "nur Raidfähigkeit")
        except (ValueError, OSError, discord.HTTPException) as e:
            log.warning("GuildSentinel-Datei nicht übernommen (alter Stand bleibt): %s", e)
            gs_att = None
            gs_has_bank = False
        if gs_att is not None:
            try:
                await post_raid_ready()
            except Exception:  # noqa: BLE001
                log.exception("Raidfähigkeit konnte nicht gepostet werden")
    if not att and gs_att is not None:
        if gs_has_bank:
            try:
                await post_guild_bank()
            except Exception:  # noqa: BLE001
                log.exception("Gildenbank-Bestand konnte nicht gepostet werden")
        return
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
    # Erstkill-Screenshots vom Uploader (shot_<Boss-ID>_<Zeit>.jpg) aufheben – die Ruhmeshalle postet sie
    for a in message.attachments:
        m_ = re.match(r"^shot_(\d+)_(\d+)\.(jpg|jpeg|png)$", a.filename.lower())
        if m_ and a.size <= 10 * 1024 * 1024:
            try:
                os.makedirs(SHOTS_DIR, exist_ok=True)
                with open(os.path.join(SHOTS_DIR, a.filename.lower()), "wb") as f_:
                    f_.write(await a.read())
            except (OSError, discord.HTTPException) as e:
                log.warning("Screenshot %s nicht gespeichert: %s", a.filename, e)
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
# Beim Start: #testberichte anlegen, fehlende Ankündigungen nachholen (Selbst-Update: ab 1.5.167 in update_bot.py)
# ---------------------------------------------------------------------------



async def ensure_test_channel() -> str | None:
    """#testberichte (OFFIZIERE, nur Bot und Admins) beim Start anlegen, falls er fehlt – ohne /raidmaster-einrichten.
    Der Uploader 1.8.0 und der GitHub-Workflow testberichte.yml brauchen ihn. Liefert eine Meldung oder None."""
    guild = bot_guild()
    if guild is None:
        return None
    had = guildbank.find_channel(guild.text_channels, uploader_setup.TEST_CHANNEL)
    ch, note = await uploader_setup.ensure_test_channel(guild, "Testberichte der GoldSentinel-Addons")
    if ch is not None and cfg.get("testberichte_channel_id") != ch.id:
        cfg["testberichte_channel_id"] = ch.id
        save_config()
    if ch is not None and had is None:
        return ("🧪 Kanal **#testberichte** angelegt (🔒 OFFIZIERE, nur Bot und Admins). Damit der Uploader dort Testberichte "
                "abliefern kann: `/uploader` einmal erneut ausführen und die neue uploader_config.json verwenden.")
    return note


async def repair_missing_announcements():
    """Einmal je Bot-Version: Beiträge aus announce/, die als gepostet gelten, deren Nachrichten aber nicht mehr im
    Discord stehen (z. B. eine Vorstellung, die bis 1.5.97 beim Aufräumen alter Versionen mit gelöscht wurde),
    zum erneuten Posten freigeben. Nur Dateien, die noch in announce/ liegen."""
    marker = "announce_repaired_" + updater.bot_version(BASE)
    if state.data.get(marker) or not os.path.isdir(ANNOUNCE_DIR):
        return
    present = set(os.listdir(ANNOUNCE_DIR))
    rec = state.data.setdefault("announce_msgs", {})
    announced = state.data.setdefault("announced", [])
    freed = []
    for fn, r in list(rec.items()):
        if fn not in present or fn not in announced or not r.get("ids") or not r.get("ch"):
            continue
        ch = await channel_by_id(r["ch"])
        if ch is None:
            continue
        try:
            await ch.fetch_message(int(r["ids"][0]))
        except discord.NotFound:
            announced.remove(fn)
            rec.pop(fn, None)
            freed.append(fn)
        except discord.HTTPException:
            pass
    state.data[marker] = True
    state.save()
    if freed:
        log.info("Ankündigungen fehlten im Discord und werden neu gepostet: %s", ", ".join(freed))
        await post_bot_log("📣 Diese Ankündigungen fehlten im Discord und werden neu gepostet: " + ", ".join(freed))


# ---------------------------------------------------------------------------
# Befehlsliste im Offiziersbereich und #befehle (nur der Bot schreibt): ab 1.5.161 in befehlsliste_bot.py
# ---------------------------------------------------------------------------

@dkp_loop.before_loop
async def before_dkp():
    await bot.wait_until_ready()


if __name__ == "__main__":
    try:
        bot.run(cfg["token"], log_handler=None)
    except discord.PrivilegedIntentsRequired:
        # Ein Intent ist im Entwicklerportal aus. Schritt für Schritt ohne ihn starten – nie endlos:
        # 1. Server Members Intent weglassen, 2. Message Content Intent weglassen, 3. aufhören (kein Neustart).
        if bot.intents.members:
            log.error("Server Members Intent ist im Discord-Entwicklerportal nicht eingeschaltet – "
                      "starte ohne PUG-Beitrittserkennung neu (siehe /pug-einladung).")
            state.data["members_intent_missing"] = True
            state.save()
            sys.exit(updater.RESTART_CODE)
        if bot.intents.message_content:
            log.error("Message Content Intent ist im Discord-Entwicklerportal nicht eingeschaltet, in config.json aber "
                      "\"message_content_intent\": true – starte ohne ihn neu (neuer Versuch frühestens in 6 Stunden).")
            state.data["message_content_intent_missing"] = time.time()
            state.save()
            sys.exit(updater.RESTART_CODE)
        log.error("Discord verweigert die Anmeldung wegen fehlender Intents, obwohl keine besonderen mehr verlangt "
                  "werden – der Bot hält an. Bitte im Entwicklerportal unter Bot -> Privileged Gateway Intents prüfen "
                  "und dann neu starten: sudo systemctl restart raidmaster")
        sys.exit(CONFIG_ERROR)
    sys.exit(grund.EXIT_CODE)          # D-3 Schritt 19 (1.5.165): restart_soon setzt grund.EXIT_CODE
