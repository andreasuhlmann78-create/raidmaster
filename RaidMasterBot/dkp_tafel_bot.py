"""DKP-Tabellen und Raid-Abrechnung (D-3 Schritt 26, ab Bot 1.5.173): DKP-Stand je Raid-Pool im DKP-Kanal (Bild
und Text, bearbeitet statt neu gepostet), Abrechnung nach jedem Raid, alte Gesamt-Tabelle entfernen, DKP-Kanäle
aufräumen.

UNVERÄNDERT aus bot.py verschoben: der Abschnitt "Hintergrund: DKP-Tabelle und Loot-Protokoll" (dkp_channel_for
bis post_dkp_table, 244 Zeilen). Testnachrichten: testdaten_bot.send_test. bot.py importiert dieses Modul nach
"grund.bot = bot" und übernimmt die Namen, die Uploads, /dkpliste, Kanal-Aufräumer und Test-Uploads brauchen.
Weg A (Antwort der Prüf-Sitzung 15.11. 20:48).
"""
from __future__ import annotations

import asyncio
from datetime import datetime

import discord

import grund
import raidmaster_data as rmd
import render as rimg
from bot_hilfen import table_file
from grund import bot_guild, channel_by_id, raid_channel
from kern import cfg, log, save_config, state
from symbole_bot import class_emoji
from testdaten_bot import send_test

bot = grund.bot
assert bot is not None, "dkp_tafel_bot erst nach grund.bot = bot importieren"


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


async def dkp_list_messages(pool: str, rows: list[dict], data: dict | None, db: dict | None, head: str) -> list[str]:
    """DKP-Stände als feste Textliste – für alle Raids gleich (MC, Onyxia, BWL …):
    Punkt in Klassenfarbe, Name, Klasse, DKP, ggf. Ersatzbank. "Verdient" wird mitgezählt, aber nicht gezeigt."""
    standby = set(str(n) for n in ((((db or {}).get("config") or {}).get("standby")) or {}).keys())
    total, count = rmd.pool_total(rows)
    players = (data or {}).get("players") or {}
    settings = (data or {}).get("settings") or {}
    decay = ""
    if settings.get("autoDecay", True) is not False and int(settings.get("decayPct") or 0) > 0:
        last = int((data or {}).get("lastDecay") or 0)
        decay = (f"⏳ Verfall: {int(settings.get('decayPct'))} % jeden Mittwoch (Raid-Reset)"
                 + (f" · zuletzt <t:{last}:d>" if last > 0 else ""))
    lines = [head, f"Gesamt: **{total} DKP** · {count} Spieler" + (f"\n{decay}" if decay else ""), ""]
    n = 0
    for r_ in rows:
        if r_["dkp"] == 0 and r_["name"] not in standby:
            continue
        n += 1
        dot = await class_emoji(r_.get("class"))
        cls = rimg.CLASS_NAMES.get(str(r_.get("class") or "").upper(), "")
        dkp = f"**{r_['dkp']}** DKP" if r_["dkp"] >= 0 else f"**{r_['dkp']}** DKP ❗"
        main = (players.get(r_["name"]) or {}).get("m") if isinstance(players.get(r_["name"]), dict) else None
        lines.append(f"`{n:>2}.` {dot} **{r_['name']}** · {cls} · {dkp}" + (" · *Ersatzbank*" if r_["name"] in standby else "")
                     + (f" · *Twink von {main}*" if main else ""))
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
