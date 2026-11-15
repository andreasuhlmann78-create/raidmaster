"""Gildenbank und Raidfähigkeit (D-3 Schritt 10, ab Bot 1.5.155) – beide aus den GuildSentinel-Uploads.

Gildenbank: ein Kanal #gildenbank – oben die Regeln (guild_rules.json), darunter der Bestand vom Bank-Charakter
(gelesen mit RaidMaster oder GuildSentinel). Der Bestand wird bearbeitet, nicht neu gepostet. Dazu /bank.
Der frühere Kanal #gildenbank-bestand wird aufgelöst (guildbank.py).
Raidfähigkeit (RP-D): post_raid_ready – aus GuildSentinelDB.raidReady im Offizierskanal.

UNVERÄNDERT aus bot.py verschoben. Die reinen Regeln stehen in guildbank.py und raid_ready.py; hier nur das, was
Discord braucht. bot.py importiert dieses Modul erst NACH "grund.bot = bot" (/bank wird beim Import angemeldet) und
übernimmt die Namen. Weg A (Antwort der Prüf-Sitzung 15.11. 20:48).
"""
from __future__ import annotations

import os
from datetime import datetime
from zoneinfo import ZoneInfo

import discord
from discord import app_commands

import grund
import guildbank
import raid_ready
import raidmaster_data as rmd
import server_setup
from bot_hilfen import test_info
from grund import NO_PING, bot_guild, channel_by_id, post_bot_log
from kern import GS_READY_PATH, GS_UPLOAD_PATH, TZ, cfg, log, save_config, state
from symbole_bot import item_emoji

bot = grund.bot
assert bot is not None, "bank_bot erst nach grund.bot = bot importieren"


async def post_raid_ready(now: datetime | None = None) -> list[str]:
    """RP-D (ab 1.5.125): Raidfähigkeit aus GuildSentinelDB.raidReady im Offizierskanal – montags einmal, Vorschlag
    zur Umstellung sofort einmal. Keine Namen, nie doppelt, nur #offiziere."""
    # neuester Stand aus Bank-Upload oder Upload nur mit Raidfähigkeit (D-GS1)
    cands = [raid_ready.parse(guildsentinel_db()),
             raid_ready.parse(rmd.load_guildsentinel_db(GS_READY_PATH) if os.path.isfile(GS_READY_PATH) else None)]
    rr = raid_ready.newest(cands)
    if rr is None:
        return []
    guild = bot_guild()
    ch = server_setup.find_channel(guild.text_channels, "offiziere") if guild is not None else None
    if ch is None:
        return []
    now = now or datetime.now(ZoneInfo(TZ))
    sent = []
    key = raid_ready.suggestion_key(rr)
    if key and state.data.get("raidready_suggestion") != key:
        await ch.send(raid_ready.suggestion_text(rr), allowed_mentions=NO_PING)
        state.data["raidready_suggestion"] = key
        state.save()
        sent.append("vorschlag")
    if raid_ready.weekly_due(now, state.data.get("raidready_week")):
        if raid_ready.too_old(rr, now.timestamp()):
            # RP-D3: alter Stand (> 14 Tage) wird nicht als aktuell gepostet
            log.info("Raidfähigkeit nicht gepostet: Stand älter als %s Tage", raid_ready.STALE_SKIP_DAYS)
            state.data["raidready_week"] = raid_ready.week_key(now)
            state.save()
            return sent
        await ch.send(raid_ready.weekly_text(rr, now.timestamp()), allowed_mentions=NO_PING)
        state.data["raidready_week"] = raid_ready.week_key(now)
        state.save()
        sent.append("woche")
    return sent


BANK_CHANNEL = guildbank.BANK_CHANNEL
_gs_cache: dict = {"mtime": None, "db": None}


def guildsentinel_db() -> dict | None:
    """GuildSentinelDB aus dem letzten Upload (nur bank wird benutzt)."""
    if not os.path.isfile(GS_UPLOAD_PATH):
        return None
    mtime = os.path.getmtime(GS_UPLOAD_PATH)
    if _gs_cache["mtime"] != mtime:
        _gs_cache["db"] = rmd.load_guildsentinel_db(GS_UPLOAD_PATH)
        _gs_cache["mtime"] = mtime
    return _gs_cache["db"]


def current_bank() -> dict | None:
    """Neuester Bestand aus RaidMaster und GuildSentinel (bank["src"] = "raidmaster" / "guildsentinel")."""
    return rmd.choose_bank(bot.dkp_db, guildsentinel_db())


async def bank_channel():
    """#gildenbank (Regel-Kanal). Stand der Bestand bisher woanders (#gildenbank-bestand), wird er dort entfernt
    und hier neu gepostet; #gildenbank-bestand wird einmal zu löschen versucht."""
    guild = bot_guild()
    if guild is None:
        return None
    ch = await channel_by_id((cfg.get("rules_channels") or {}).get(BANK_CHANNEL))
    if ch is None:
        ch = guildbank.find_channel(guild.text_channels, BANK_CHANNEL)
    if ch is None:
        return None
    prev_id = state.data.get("bank_channel") or cfg.get("bank_channel_id")
    prev = await channel_by_id(prev_id) if prev_id and int(prev_id) != ch.id else None
    report = await guildbank.migrate_old_channel(guild.text_channels, ch, state.data, bot.user.id if bot.user else 0, prev)
    if cfg.get("bank_channel_id") != ch.id:
        cfg["bank_channel_id"] = ch.id
        save_config()
    state.save()
    for line in report:
        log.info("Gildenbank: %s", line)
        await post_bot_log(line)
    return ch


async def bank_text(bank: dict) -> list[str]:
    lines = [f"📦 **Bestand der Gildenbank** – {bank['char']} · Stand <t:{bank['t']}:f>",
             f"💰 Gold: **{rmd.money_text(bank['gold'])}**" + (f" · Gildenbank: **{rmd.money_text(bank['guild_gold'])}**" if bank.get("guild_gold") else ""), ""]
    for it in bank["items"]:
        em = await item_emoji(rmd.item_link_for(it["id"], it["n"], it["q"]), {"ic": it.get("ic"), "q": it.get("q")})
        lines.append(f"{em} {it['n']} ×{it['c']}" + (f" _(davon {it['mail']} in der Post)_" if it.get("mail") else ""))
    if not bank["items"]:
        lines.append("Leer.")
    lines.append("")
    lines.append("🙋 _Etwas gebraucht? Einfach einen Offizier fragen. Suchen: `/bank Name`._")
    src = rmd.BANK_SOURCES.get(bank.get("src") or "")
    if src:
        lines.append(f"-# gelesen mit {src}")
    return rmd.split_discord("\n".join(lines))


BANK_EMPTY_TEXT = ("📦 **Bestand der Gildenbank**\n\n"
                   "Hier siehst du bald alles, was in unserer Gildenbank liegt – Items und Gold, immer auf dem neuesten Stand.\n\n"
                   "🔄 **So kommt der Bestand hierher:** Der Bank-Charakter hat RaidMaster oder GuildSentinel und stellt sich "
                   "dort als Bank-Charakter ein. Öffnet er Bank oder Briefkasten, liest das Addon alles ein, "
                   "und mit dem nächsten Upload steht es hier.\n\n"
                   "🔍 Suchen geht jederzeit mit `/bank`.")


async def post_guild_bank():
    if test_info(bot.dkp_db or {}):
        return
    bank = current_bank()
    if not bank:
        # noch kein Bestand: kurze Erklärung unter den Regeln (wird später durch den Bestand ersetzt)
        if not state.data.get("bank_messages"):
            ch = await bank_channel()
            if ch is not None and not state.data.get("bank_messages"):
                m = await ch.send(BANK_EMPTY_TEXT)
                state.data["bank_messages"] = [m.id]
                state.data["bank_channel"] = ch.id
                state.save()
        return
    ch = await bank_channel()
    if ch is None:
        return
    if state.data.get("bank_t") == bank["t"] and state.data.get("bank_src") == bank.get("src") \
            and state.data.get("bank_messages"):
        return
    chunks = await bank_text(bank)
    await guildbank.write_bank(ch, chunks, state.data)
    state.data["bank_t"] = bank["t"]
    state.data["bank_src"] = bank.get("src")
    state.save()


@bot.tree.command(name="bank", description="Was ist in der Gildenbank? (Suche nach Name)")
@app_commands.describe(suche="Teil des Namens, leer = alles")
async def bank_cmd(inter: discord.Interaction, suche: str | None = None):
    bank = current_bank()
    if not bank:
        await inter.response.send_message("Noch kein Bestand – der Bank-Charakter muss einmal seine Bank öffnen "
                                          "(RaidMaster → Einstellungen → „Bank-Charakter“ oder in GuildSentinel).",
                                          ephemeral=True)
        return
    q = (suche or "").strip().lower()
    items = [it for it in bank["items"] if not q or q in it["n"].lower()]
    if not items:
        await inter.response.send_message(f"„{suche}“ ist nicht in der Gildenbank (Stand <t:{bank['t']}:R>).", ephemeral=True)
        return
    lines = [f"📦 **Gildenbank** ({bank['char']}, Stand <t:{bank['t']}:R>)" + (f" – Suche „{suche}“" if suche else "")]
    for it in items[:60]:
        lines.append(f"{it['n']} ×{it['c']}")
    if len(items) > 60:
        lines.append(f"… und {len(items) - 60} weitere")
    await inter.response.send_message("\n".join(lines)[:2000], ephemeral=True)
