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
import io
import json
import os
import sys
import re
import time
import zlib
from datetime import datetime
from zoneinfo import ZoneInfo

import discord
from discord import app_commands
from discord.ext import tasks

import raidmaster_data as rmd
import guildbank
import uploader_setup
import member_area
import raid_post
import market
from bot_hilfen import (  # noqa: E402 – D-3 Schritt 1: Hilfen ohne Zustand
    _config_ids,
    check_upload,
    clean_softres,
    profile_text,
    raid_view,
    status_text,
    test_info,
)
import server_setup
import mc_tactics
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
    kills_db,
    SHOTS_DIR,
)

market.set_tz(TZ)          # D-MN7d: Marktberichte in der Zeitzone des Bots
from grund import (  # noqa: E402 – D-3 Schritt 3: Grundfunktionen
    NO_PING,
    bot_guild,
    channel_by_id,
    is_admin,
    is_creator,
    post_bot_log,
    raid_channel,
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
    handle_name_button,
    handle_name_post,
)
import befehlsliste_bot  # noqa: E402,F401 – D-3 Schritt 16: Befehlslisten
from befehlsliste_bot import ensure_command_list  # noqa: E402
import mitglieder_bot  # noqa: E402,F401 – D-3 Schritt 17: Mitglieder-Bereich und Bewerbung
from mitglieder_bot import handle_apply_button, maintain_member_area  # noqa: E402
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
from ereignis_bot import create_raid_event, delete_raid_event  # noqa: E402
import raidanzeige_bot  # noqa: E402,F401 – D-3 Schritt 24: Raid-Anzeige
from raidanzeige_bot import raid_embed, update_raid_message  # noqa: E402
import twink_bot  # noqa: E402,F401 – D-3 Schritt 24: Twinks (meldet /twink beim Import an)
from ersatz_bot import accept_substitute, offer_substitute  # noqa: E402 – D-3 Schritt 25: Ersatz bei Absage
from skillung_bot import sync_specs  # noqa: E402 – D-3 Schritt 25: Skillung übernehmen
from dkp_tafel_bot import (  # noqa: E402 – D-3 Schritt 26: DKP-Tabellen und Raid-Abrechnung
    dkp_channel_for,
    dkp_list_messages,
    post_dkp_tables,
    post_raid_summaries,
    remove_overall,
)
from beutepost_bot import post_new_loot, show_tip  # noqa: E402 – D-3 Schritt 27: Beute-Posts
import dkp_nachricht_bot  # noqa: E402,F401 – D-3 Schritt 27: persönliche DKP-Nachricht (meldet /dkp-nachricht an)
from dkp_nachricht_bot import send_raid_dms  # noqa: E402
import monatlich_bot  # noqa: E402,F401 – D-3 Schritt 28: Monatliches, Raider des Monats (meldet /raider-des-monats an)
from monatlich_bot import monthly_loop  # noqa: E402
from testupload_bot import handle_test_upload, test_cleanup_loop  # noqa: E402 – D-3 Schritt 29: Testmodus

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


def addon_hint(raid: dict | None, actual: str) -> str:
    """Hinweis bei der Anmeldung zu einem Gilden-Raid (ab 1.5.117, Wunsch des Nutzers 12.11.): RaidMaster ist Pflicht."""
    if not raid or raid.get("mode") == "pug" or actual not in ("an", "ersatz", "vielleicht"):
        return ""
    guild = bot_guild()
    ch = server_setup.find_channel(guild.text_channels, "raid-addon") if guild is not None else None
    where = ch.mention if ch is not None else "#raid-addon"
    return ("\n\n📦 **Pflicht für Gilden-Raids:** das Addon **RaidMaster** (Download in " + where +
            "). Bitte vor dem Raid installieren bzw. auf die neueste Version bringen.")


async def send_export(inter: discord.Interaction, raid: dict):
    if not is_creator(inter.user):
        await inter.response.send_message("Den Export dürfen nur der Gildenchef und die Offiziere abrufen.", ephemeral=True)
        return
    lineup = None
    if raid["signups"]:
        att, _, _ = rmd.attendance(bot.dkp_data, book)
        lineup = rmd.build_lineup(raid, att)
    link = cfg.get("pug_invite_url", "") if raid.get("mode") == "pug" else ""
    text = rmd.export_text(raid, TZ, lineup, link, raid.get("softres", ""), book.alt_links())
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


def pool_from_channel(channel) -> str | None:
    """Raid-Topf des Kanals (Logik in server_setup.pool_from_channel, dort getestet)."""
    return server_setup.pool_from_channel(channel, cfg.get("raid_channels"))


@raid_group.command(name="erstellen", description="Neuen Raid zur Anmeldung erstellen")
@app_commands.describe(titel="z. B. Molten Core Mittwoch", datum="TT.MM.JJJJ, z. B. 29.10.2026", uhrzeit="HH:MM, z. B. 20:00",
                       raid="Welcher Raid? Ohne Angabe: der Raid des Kanals (z. B. #barrow-anmeldung), sonst Molten Core",
                       beschreibung="optional, z. B. Treffpunkt und Buffs", max_spieler="optional, z. B. 40 (0 = unbegrenzt)",
                       modus="DKP-Raid (Gilde) oder PUG-Raid (Loot über softres.it)",
                       softres="PUG: Link zum softres.it-Raid (kann auch später mit /raid softres gesetzt werden)")
@app_commands.choices(modus=[app_commands.Choice(name="DKP-Raid (Gilde)", value="dkp"),
                             app_commands.Choice(name="PUG-Raid (softres.it)", value="pug")])
@app_commands.autocomplete(raid=raid_pool_autocomplete)
async def raid_create(inter: discord.Interaction, titel: str, datum: str, uhrzeit: str, raid: str | None = None,
                      beschreibung: str | None = None, max_spieler: app_commands.Range[int, 0, 40] = 0,
                      modus: app_commands.Choice[str] | None = None, softres: str | None = None):
    # ohne Angabe: Raid aus dem Kanal, in dem der Befehl kommt (z. B. #barrow-anmeldung -> Barrow Deeps), sonst MC
    # (ab 1.5.121 – vorher immer MC, der Barrow-Raid landete am 12.11. in #mc-anmeldung)
    pool = raid or pool_from_channel(inter.channel) or "mc"
    if not is_creator(inter.user):
        await inter.response.send_message("Raids erstellen dürfen nur der Gildenchef und die Offiziere.", ephemeral=True)
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
    # Raid für WoW Forever noch nicht angekündigt (Kategorie ausgeblendet): keine Anmeldung, die niemand sieht
    if mode != "pug" and not server_setup.raid_released(pool, cfg):
        await inter.response.send_message(
            f"**{rmd.pool_name(pool, bot.dkp_data)}** ist für WoW Forever noch nicht angekündigt – die Kategorie ist für "
            "Mitglieder ausgeblendet. Sie erscheint von selbst, sobald Blizzard den Raid ankündigt. "
            "Bis dahin geht nur ein PUG-Raid (modus: PUG-Raid).", ephemeral=True)
        return
    # ab hier zuerst antworten (Discord wartet nur 3 s) – sonst "Die Anwendung reagiert nicht" und der Raid geht verloren
    await inter.response.defer(ephemeral=True, thinking=True)
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
    # posten; scheitert es, bleibt kein Raid ohne Nachricht im Buch (Befund R1, raid_post.py, Funktionstest T-R1)
    msg = await raid_post.post_new_raid(book, raid, target, raid_embed(raid), raid_view(raid),
                                        lambda text: inter.followup.send(text, ephemeral=True))
    if msg is None:
        return
    await create_raid_event(raid)
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
        await inter.response.send_message("Einen Testraid dürfen nur der Gildenchef und die Offiziere anlegen.", ephemeral=True)
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


@raid_group.command(name="absagen", description="Raid absagen (Angemeldete werden benachrichtigt)")
@app_commands.describe(raid="Welcher Raid?")
@app_commands.autocomplete(raid=raid_autocomplete)
async def raid_cancel(inter: discord.Interaction, raid: str):
    if not is_creator(inter.user):
        await inter.response.send_message("Das dürfen nur der Gildenchef und die Offiziere.", ephemeral=True)
        return
    r = book.get(raid)
    if not r:
        await inter.response.send_message("Raid nicht gefunden.", ephemeral=True)
        return
    r["closed"] = True
    r["cancelled"] = True
    book.save()
    await update_raid_message(r)
    await delete_raid_event(r)
    ids = [uid for uid, s in r["signups"].items() if s["status"] in ("an", "ersatz", "vielleicht")]
    mentions = " ".join(f"<@{u}>" for u in ids)
    await inter.response.send_message(f"❌ **{r['title']}** (<t:{r['start']}:F>) wurde abgesagt. {mentions}",
                                      allowed_mentions=discord.AllowedMentions(users=True))


@raid_group.command(name="softres", description="softres.it-Link für einen PUG-Raid setzen oder ändern")
@app_commands.describe(raid="Welcher Raid?", link="z. B. https://softres.it/raid/abcd (leer = entfernen)")
@app_commands.autocomplete(raid=raid_autocomplete)
async def raid_softres(inter: discord.Interaction, raid: str, link: str = ""):
    if not is_creator(inter.user):
        await inter.response.send_message("Das dürfen nur der Gildenchef und die Offiziere.", ephemeral=True)
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
        await inter.response.send_message("Das dürfen nur der Gildenchef und die Offiziere.", ephemeral=True)
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
        await inter.response.send_message("Das dürfen nur der Gildenchef und die Offiziere.", ephemeral=True)
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


async def assignment_channel(pool: str | None):
    """Einteilungs-Kanal eines Raids (#einteilung-mc, #einteilung-barrow …), sonst der allgemeine."""
    pool = pool or "mc"
    ch = await channel_by_id((cfg.get("assignment_channels") or {}).get(pool))
    if ch:
        return ch
    guild = bot_guild()
    ch = discord.utils.get(guild.text_channels, name=server_setup.assignment_channel_name(pool)) if guild else None
    if ch:
        cfg.setdefault("assignment_channels", {})[pool] = ch.id
        save_config()
        return ch
    return await channel_by_id(cfg.get("assignment_channel_id"))


async def post_lineup(raid: dict, extra_channel=None) -> int:
    """Aufstellung berechnen und im Einteilungs-Kanal des Raids und in #offiziere posten. Liefert Anzahl Kanäle."""
    att, n, source = rmd.attendance(bot.dkp_data, book)
    lineup = rmd.build_lineup(raid, att)
    texts = rmd.lineup_text(raid, lineup, source, n)
    targets = []
    main = await assignment_channel(raid.get("pool"))
    if main:
        targets.append(main)
    for cid in (cfg.get("officer_channel_id"),):
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
        await inter.response.send_message("Das dürfen nur der Gildenchef und die Offiziere.", ephemeral=True)
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
        await inter.response.send_message("Das dürfen nur der Gildenchef und die Offiziere.", ephemeral=True)
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
@bot.tree.command(name="rekorde", description="Bestzeiten der Gilde pro Boss")
@app_commands.describe(raid="optional: nur dieser Raid")
@app_commands.autocomplete(raid=raid_pool_autocomplete)
async def rekorde_cmd(inter: discord.Interaction, raid: str | None = None):
    best = rmd.best_times(kills_db.data)
    rows = [k for k in best.values() if not raid or k.get("p") == raid]
    if not rows:
        await inter.response.send_message("Noch keine Bestzeiten – sie entstehen mit jedem Bosskill (RaidMaster ab 2.9.0).", ephemeral=True)
        return
    rows.sort(key=lambda k: (str(k.get("p") or ""), k["n"]))
    lines, last = ["⏱️ **Bestzeiten der Gilde**"], None
    for k in rows:
        if k.get("p") != last:
            last = k.get("p")
            lines.append(f"__{rmd.pool_name(last, bot.dkp_data) if last else 'Sonstige'}__")
        lines.append(f"{k['n']} – **{rmd.fmt_duration(k['d'])}** (<t:{k['t']}:d>)")
    parts = rmd.split_discord("\n".join(lines))
    await inter.response.send_message(parts[0], ephemeral=True)
    for part in parts[1:]:
        await inter.followup.send(part, ephemeral=True)


# ---------------------------------------------------------------------------
# Gildenbank (/bank, Bestand in #gildenbank) und Raidfähigkeit: ab 1.5.155 in bank_bot.py
# Beute-Datenbank (/beute, Beutetabellen): ab 1.5.157 in beute_bot.py
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Klassenfarben (Rollen in WoW-Klassenfarbe): ab 1.5.158 in klassen_bot.py.
# Skillung aus dem Spiel in die Raid-Anmeldungen übernehmen (sync_specs): ab 1.5.172 in skillung_bot.py.
# Ersatz bei Absage (offer_substitute, accept_substitute): ab 1.5.172 in ersatz_bot.py.
# ---------------------------------------------------------------------------


async def _keep_text(ch, key: str, text: str, prefixes: tuple = (), msg_id: int | None = None, post_missing: bool = False) -> bool:
    """Einen festen Beitrag des Bots aktuell halten: per gespeicherter ID oder am Textanfang im Verlauf finden
    und bearbeiten, wenn sich der Text geändert hat (Knöpfe bleiben erhalten). Postet nichts Neues."""
    if ch is None:
        return False
    rec = state.data.setdefault("kept_texts", {})
    digest = str(zlib.crc32(text.encode("utf-8")))
    cur = rec.get(key) or {}
    mid = msg_id or cur.get("id")
    if mid and cur.get("hash") == digest and cur.get("id") == mid:
        return False
    if not mid and prefixes:
        try:
            async for m in ch.history(limit=100, oldest_first=True):
                if m.author.id == bot.user.id and (m.content or "").startswith(prefixes):
                    mid = m.id
                    break
        except discord.HTTPException:
            return False
    if not mid:
        if not post_missing:
            return False
        try:
            m = await ch.send(text)
        except discord.HTTPException as e:
            log.info("Beitrag %s nicht gepostet: %s", key, e)
            return False
        rec[key] = {"id": m.id, "hash": digest}
        state.save()
        return True
    try:
        await ch.get_partial_message(int(mid)).edit(content=text)
    except discord.NotFound:
        rec.pop(key, None)
        state.save()
        return False
    except discord.HTTPException as e:
        log.info("Beitrag %s nicht aktualisiert: %s", key, e)
        return False
    rec[key] = {"id": int(mid), "hash": digest}
    state.save()
    await asyncio.sleep(0.4)
    return True


async def ensure_channel_texts() -> list[str]:
    """Anleitungen in den Anmelde-Kanälen, PUG-Anmeldung und #bot-befehle auf die aktuelle Fassung bringen
    (sie wurden früher nur beim Anlegen der Kanäle gepostet)."""
    guild = bot_guild()
    if guild is None:
        return []
    done = []
    names = {k: n for k, n, _, _ in server_setup.RAIDS}
    names.update(cfg.get("raid_names") or {})
    regs = cfg.get("raid_reg_messages") or {}
    for key, ids in (cfg.get("raid_channels") or {}).items():
        ch = await channel_by_id((ids or {}).get("signup"))
        if ch is None:
            continue
        name = names.get(key) or rmd.pool_name(key, bot.dkp_data)
        if await _keep_text(ch, f"howto:{key}", server_setup._raid_howto_text(name, key), ("**Anmeldung ", "📋 **Anmeldung ")):
            done.append(f"#{ch.name}")
        if regs.get(key) and await _keep_text(ch, f"reg:{key}", server_setup.raid_registration_text(name), msg_id=int(regs[key])):
            done.append(f"#{ch.name} (Knopf)")
    pug = discord.utils.get(guild.text_channels, name="pug-anmeldung")
    if pug is not None:
        if await _keep_text(pug, "howto:pug", server_setup._pug_howto_text(), ("**PUG-Raids", "🎲 **PUG-Raids")):
            done.append("#pug-anmeldung")
        if cfg.get("pug_reg_message") and await _keep_text(pug, "reg:pug", server_setup.pug_registration_text(),
                                                          msg_id=int(cfg["pug_reg_message"])):
            done.append("#pug-anmeldung (Knopf)")
    for key in server_setup.ASSIGN_RAIDS:
        ach = discord.utils.get(guild.text_channels, name=server_setup.assignment_channel_name(key))
        if ach is not None and await _keep_text(ach, f"assign:{key}", server_setup.assignment_intro_text(key),
                                                ("🗂️ **Einteilung ",), post_missing=True):
            done.append(f"#{ach.name}")
    test_ch = discord.utils.get(guild.text_channels, name="bot-befehle")
    if test_ch is not None and await _keep_text(test_ch, "howto:botcmd", server_setup._bot_commands_text(),
                                                ("**Bot-Befehle für die Gildenleitung", "🛠️ **Hier darfst du")):
        done.append("#bot-befehle")
    return done


async def ensure_voice_limits() -> list[str]:
    """Raid-Sprachkanäle: höchstens so viele Personen wie der Raid Plätze hat (MC 40, Hyjal 20, Barrow Deeps 10 ...)."""
    guild = bot_guild()
    if guild is None or not guild.me.guild_permissions.manage_channels:
        return []
    out = []
    for key, ids in (cfg.get("raid_channels") or {}).items():
        ch = guild.get_channel(int((ids or {}).get("voice") or 0))
        if ch is None or not isinstance(ch, discord.VoiceChannel):
            continue
        limit = server_setup.raid_size(key, cfg)
        if ch.user_limit == limit:
            continue
        try:
            await ch.edit(user_limit=limit, reason="RaidMaster: Sprachkanal so groß wie der Raid")
            out.append(f"{ch.name}: {limit}")
        except discord.HTTPException as e:
            log.warning("Platzzahl für %s nicht gesetzt: %s", ch.name, e)
    return out


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
        if not server_setup.raid_released(key, cfg):
            continue        # ab Bot 1.5.99: erst anlegen, wenn der Raid auf WoW Forever spielbar ist
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


async def sync_raid_visibility() -> list[str]:
    """Raids, die für WoW Forever noch nicht angekündigt sind (forever_raids.json ohne "forever": true), für alle
    ausblenden; angekündigte wieder einblenden.
    Gemerkt in state "hidden_raids" – eingeblendet wird nur, was der Bot selbst ausgeblendet hat."""
    guild = bot_guild()
    perms = guild.me.guild_permissions if guild is not None else None
    if perms is None or not (perms.manage_roles and perms.manage_channels):
        return []
    hidden = state.data.setdefault("hidden_raids", {})
    report = []
    for r in server_setup.RAID_DEFS:
        key = r["key"]
        ids = (cfg.get("raid_channels") or {}).get(key) or {}
        anchor = await channel_by_id(ids.get("signup") or ids.get("tactics") or ids.get("dkp"))
        category = getattr(anchor, "category", None)
        if category is None:
            continue
        targets = server_setup.raid_targets(category, r["prefix"], ids.values())
        reason = "RaidMaster: Raid auf WoW Forever noch nicht spielbar"
        try:
            if not server_setup.raid_released(key, cfg) and key not in hidden:
                prev = await server_setup.hide_raid(guild, targets, reason)
                hidden[key] = {"cat": category.id, "prev": prev}
                state.save()
                report.append(f"🙈 {r['name']} ausgeblendet")
            elif server_setup.raid_released(key, cfg) and key in hidden:
                await server_setup.show_raid(guild, targets, hidden[key].get("prev") or {}, "RaidMaster: Raid freigeschaltet",
                                             members_only=bool(cfg.get("member_area")))
                hidden.pop(key, None)
                state.save()
                report.append(f"👀 {r['name']} wieder sichtbar")
                ch = await channel_by_id(cfg.get("announce_channel_id"))
                if ch:
                    await ch.send(f"🆕 **{r['name']}** ist freigeschaltet – Anmeldung, Taktik, DKP und Loot stehen jetzt in "
                                  f"{category.name}.", allowed_mentions=NO_PING)
        except discord.HTTPException as e:
            report.append(f"⚠️ {r['name']}: Sichtbarkeit nicht geändert ({e})")
    return report


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
# Addon-Versionen (neue ZIP im Ordner "addon") und Ankündigungen: ab 1.5.164 in ankuendigung_bot.py
# ---------------------------------------------------------------------------


# Kanäle, die der Bot früher angelegt hat und die nicht mehr gebraucht werden. Gelöscht wird einmal und nur, wenn
# darin ausschließlich Bot-Beiträge stehen (keine Nachricht eines Mitglieds, kein Thread) und der Kanal nirgends
# eingetragen ist. Sonst bleibt er und der Bot meldet den Grund in #bot-befehle.
UNUSED_CHANNELS = ("allgemein",)


async def clear_channels_once() -> list[str]:
    """Kanäle aus server_setup.CLEAR_CHANNELS_ONCE einmal leeren (z. B. #mc-dkp mit Test-DKP vor dem Serverstart).
    Danach vergisst der Bot seine DKP-Liste in diesem Kanal: eine neue kommt erst mit neuen DKP-Daten aus dem Addon."""
    guild = bot_guild()
    if guild is None:
        return []
    done = state.data.setdefault("cleared_channels", {})
    report = []
    now = datetime.now(ZoneInfo("Europe/Zurich"))
    for name, spec in server_setup.CLEAR_CHANNELS_ONCE.items():
        if not server_setup.clear_allowed(spec, now, done.get(name)):
            continue                    # erledigt oder Zeitfenster vorbei: nie wieder leeren
        tag = spec["tag"]
        ch = next((c for c in guild.text_channels if c.name.casefold() == name.casefold()), None)
        if ch is None:
            done[name] = tag
            state.save()
            continue
        perms = ch.permissions_for(guild.me)
        if not (perms.manage_messages and perms.read_message_history):
            report.append(f"⚠️ #{ch.name} nicht geleert – dem Bot fehlt dort „Nachrichten verwalten“.")
            continue
        try:
            n = await server_setup.clear_channel(ch, spec["before"], "RaidMaster: Kanal einmal geleert (" + tag + ")")
        except discord.HTTPException as e:
            report.append(f"⚠️ #{ch.name} nicht vollständig geleert: {e} – nächster Versuch beim nächsten Start, "
                          f"aber nur bis {spec['until']:%d.%m.%Y %H:%M}.")
            continue
        msgs = state.data.setdefault("dkp_messages", {})
        for pool in list(msgs):
            if dkp_channel_for(pool) == ch.id:
                msgs.pop(pool, None)
        done[name] = tag
        state.save()
        report.append(f"🧹 #{ch.name} einmalig geleert ({n} Nachricht{'en' if n != 1 else ''} von vor "
                      f"{spec['before']:%d.%m.%Y %H:%M}, angeheftete bleiben). Das passiert nie wieder.")
    return report


async def remove_unused_channels_once() -> list[str]:
    guild = bot_guild()
    if guild is None or not guild.me.guild_permissions.manage_channels:
        return []
    done = state.data.setdefault("removed_channels", {})
    report = []
    for name in UNUSED_CHANNELS:
        if name in done:
            continue
        ch = next((c for c in guild.text_channels if c.name.casefold() == name), None)
        if ch is None:
            done[name] = "nicht vorhanden"
            state.save()
            continue
        reason = None
        if ch in (guild.system_channel, guild.rules_channel, guild.public_updates_channel):
            reason = "ist in den Servereinstellungen als System-, Regel- oder Update-Kanal eingetragen"
        elif ch.id in _config_ids(cfg):
            reason = "ist in der config.json eingetragen"
        elif ch.threads:
            reason = "enthält Threads"
        else:
            try:
                async for m in ch.history(limit=1000):
                    if not m.author.bot:
                        reason = "enthält Beiträge von Mitgliedern"
                        break
            except discord.HTTPException:
                reason = "der Bot kann den Verlauf nicht lesen"
        if reason:
            done[name] = "behalten: " + reason
            report.append(f"⚠️ #{ch.name} nicht gelöscht – {reason}. Bitte selbst prüfen und ggf. von Hand löschen.")
        else:
            try:
                await ch.delete(reason="RaidMaster: ungenutzter Kanal")
                done[name] = "gelöscht"
                report.append(f"🗑️ Ungenutzten Kanal #{name} gelöscht (enthielt nur Bot-Beiträge).")
            except discord.HTTPException as e:
                done[name] = f"Fehler: {e}"
                report.append(f"⚠️ #{name} konnte nicht gelöscht werden: {e}")
        state.save()
    return report


async def process_assignment():
    """Neue Einteilung aus dem Addon: Übersicht posten und jedem Spieler eine Direktnachricht schicken."""
    a = rmd.assignment_from_db(bot.dkp_db)
    if not a or int(a.get("v") or 0) <= int(state.data.get("assign_v") or 0):
        return
    state.data["assign_v"] = int(a["v"])
    state.save()
    ch = await assignment_channel(a.get("pool"))
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
# Server-Betrieb: Selbst-Update
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
