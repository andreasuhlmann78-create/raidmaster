"""Testmodus (D-3 Schritt 29, ab Bot 1.5.176): Upload aus RaidMasterTest – DKP, Teilnehmer und Loot wie echt
posten und nach 10 Minuten wieder löschen; abgelaufene Testraids (/raid testraid) entfernen.

UNVERÄNDERT aus bot.py verschoben: der Abschnitt "Testmodus (RaidMasterTest)" (handle_test_upload,
test_cleanup_loop, before_test_cleanup) und remove_expired_test_raids (stand bei den Raid-Befehlen).
bot.py importiert dieses Modul nach "grund.bot = bot" und übernimmt handle_test_upload (Uploads) und
test_cleanup_loop (Start in setup_hook). Weg A (Antwort der Prüf-Sitzung 15.11. 20:48).
"""
from __future__ import annotations

import time

import discord
from discord.ext import tasks

import grund
import raidmaster_data as rmd
from beutepost_bot import send_loot_list
from bot_hilfen import test_info
from dkp_tafel_bot import dkp_channel_for, dkp_list_messages
from grund import channel_by_id, raid_channel
from kern import book, cfg, log, state
from testdaten_bot import TEST_TTL, send_test

bot = grund.bot
assert bot is not None, "testupload_bot erst nach grund.bot = bot importieren"


# ---------------------------------------------------------------------------
# Testmodus (RaidMasterTest): DKP, Teilnehmer und Loot wie echt posten, nach 10 Minuten löschen
# ---------------------------------------------------------------------------



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
