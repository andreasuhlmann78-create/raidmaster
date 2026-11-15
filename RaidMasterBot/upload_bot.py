"""Daten-Upload (D-3 Schritt 34, ab Bot 1.5.181): Empfang der Uploads vom PC der Raidleitung (receive_upload:
RaidMaster.lua, GuildSentinel.lua, Erstkill-Screenshots, Testmodus, Marktdaten), Verarbeitung neuer DKP-Daten
(process_new_data) und die Schleife dkp_loop (alle 30 Sekunden, startet erst nach dem Anmelden: before_dkp).

UNVERÄNDERT aus bot.py verschoben. bot.py importiert dieses Modul erst NACH "grund.bot = bot" und übernimmt
dkp_loop (setup_hook) und receive_upload (on_message). Weg A (Antwort der Prüf-Sitzung 15.11. 20:48).
"""
from __future__ import annotations

import grund

bot = grund.bot
assert bot is not None, "upload_bot erst nach grund.bot = bot importieren"

import asyncio  # noqa: E402
import os  # noqa: E402
import re  # noqa: E402
import time  # noqa: E402

import discord  # noqa: E402
from discord.ext import tasks  # noqa: E402

import raidmaster_data as rmd  # noqa: E402
from bot_hilfen import check_upload, test_info  # noqa: E402
from kern import (  # noqa: E402
    DATA_DIR,
    GS_READY_PATH,
    GS_UPLOAD_PATH,
    SHOTS_DIR,
    UPLOAD_PATH,
    cfg,
    log,
    state,
)
from grund import post_bot_log  # noqa: E402
from bank_bot import post_guild_bank, post_raid_ready  # noqa: E402
from beute_bot import update_lootdb  # noqa: E402
from beutepost_bot import post_new_loot  # noqa: E402
from dkp_befehle_bot import reload_dkp_if_needed  # noqa: E402
from dkp_nachricht_bot import send_raid_dms  # noqa: E402
from dkp_tafel_bot import post_dkp_tables, post_raid_summaries, remove_overall  # noqa: E402
from kanalpflege_bot import ensure_new_raid_categories, sync_raid_visibility  # noqa: E402
from klassen_bot import sync_class_roles  # noqa: E402
from markt_bot import market_intake  # noqa: E402
from mitglieder_bot import maintain_member_area  # noqa: E402
from raid_bot import process_assignment  # noqa: E402
from ruhmeshalle_bot import update_hall_of_fame  # noqa: E402
from skillung_bot import sync_specs  # noqa: E402
from testupload_bot import handle_test_upload  # noqa: E402

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


@dkp_loop.before_loop
async def before_dkp():
    await bot.wait_until_ready()
