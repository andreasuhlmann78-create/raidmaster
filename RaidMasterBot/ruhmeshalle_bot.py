"""Ruhmeshalle (D-3 Schritt 8, ab Bot 1.5.153): Erstkills mit Screenshot, Ruhmeshalle aktualisieren, Rekord-Tafeln
je Raid und Dungeon, Aufräumen alter Einträge (/ruhmeshalle-aufraeumen), Erfolge (/erfolge).

UNVERÄNDERT aus bot.py verschoben. Die reinen Regeln der Tafeln stehen in rekord_tafel.py; hier nur das, was
Discord braucht. Bleibt in bot.py: /rekorde (braucht die Raid-Auswahl raid_pool_autocomplete aus dem Raid-Bereich)
und Raider des Monats (benutzt hall_channel von hier).
bot.py importiert dieses Modul erst NACH "grund.bot = bot" (zwei Befehle werden beim Import angemeldet) und
übernimmt die Namen. Weg A (Antwort der Prüf-Sitzung 15.11. 20:48).
"""
from __future__ import annotations

import asyncio
import os
import re
import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import discord
from discord import app_commands

import grund
import raidmaster_data as rmd
import rekord_tafel
from bot_hilfen import test_info
from grund import bot_guild, channel_by_id, is_admin
from kern import SHOTS_DIR, TZ, book, cfg, fame_db, kills_db, log, save_config, state
from symbole_bot import class_emoji

bot = grund.bot
assert bot is not None, "ruhmeshalle_bot erst nach grund.bot = bot importieren"


async def hall_channel():
    ch = await channel_by_id(cfg.get("hall_channel_id"))
    if ch:
        return ch
    guild = bot_guild()
    if guild is None:
        return None
    ch = discord.utils.get(guild.text_channels, name="ruhmeshalle")
    if ch is None and guild.me.guild_permissions.manage_channels:
        category = None
        for name in ("ankündigungen", "ankuendigungen", "announcements", "willkommen"):
            other = discord.utils.get(guild.text_channels, name=name)
            if other and other.category:
                category = other.category
                break
        overwrites = {guild.default_role: discord.PermissionOverwrite(send_messages=False, add_reactions=True),
                      guild.me: discord.PermissionOverwrite(send_messages=True, attach_files=True, embed_links=True)}
        try:
            ch = await guild.create_text_channel("ruhmeshalle", category=category, overwrites=overwrites,
                                                 topic="🏆 Erstkills, Bestzeiten, Erfolge und der Raider des Monats – postet der RaidMaster-Bot.")
        except discord.HTTPException as e:
            log.warning("#ruhmeshalle nicht angelegt: %s", e)
            return None
    if ch:
        cfg["hall_channel_id"] = ch.id
        save_config()
    return ch


def shot_for(kill: dict) -> str | None:
    if not os.path.isdir(SHOTS_DIR):
        return None
    best = None
    for fn in os.listdir(SHOTS_DIR):
        m_ = re.match(r"^shot_(\d+)_(\d+)\.", fn)
        if m_ and int(m_.group(1)) == kill["e"] and abs(int(m_.group(2)) - kill["t"]) <= rmd.SAME_KILL:
            best = os.path.join(SHOTS_DIR, fn)
    return best


async def member_names_with_dots(names: list[str]) -> str:
    players = (bot.dkp_data or {}).get("players") or {}
    parts = []
    for n in sorted(names, key=str.lower):
        p = players.get(n)
        parts.append(f"{await class_emoji(p.get('c') if isinstance(p, dict) else None)}{n}")
    return ", ".join(parts)


def kill_area(k: dict) -> dict:
    """Raid oder Dungeon eines Kills (ab 1.5.138) – über die Encounter-ID, nicht über den Topf."""
    names = {r["key"]: rmd.pool_name(r["key"], bot.dkp_data) for r in RECORD_BOSSES}
    return rekord_tafel.area_of(k, RECORD_BOSSES, RECORD_DUNGEONS, names)


async def post_first_kill(ch, k: dict) -> bool:
    area = kill_area(k)
    # Ohne Zuordnung wie bisher der Topf; Dungeon-Erstkills ohne Screenshot (Entscheid des Nutzers 15.11. 15:51)
    raid = area["name"] or (rmd.pool_name(k["p"], bot.dkp_data) if k.get("p") else "")
    emb = discord.Embed(title=f"🏆 Erstkill: {k['n']}", colour=0xFF8C1A,
                        description=(f"**{raid}** · <t:{k['t']}:F>\n"
                                     f"Nach **{k['w'] + 1}** {'Versuch' if k['w'] == 0 else 'Versuchen'}"
                                     + (f" · Kampfdauer **{rmd.fmt_duration(k.get('d'))}**" if k.get("d") else "")))
    if k.get("m"):
        emb.add_field(name=f"Dabei ({len(k['m'])})", value=(await member_names_with_dots(k["m"]))[:1024], inline=False)
    path = None if area["dungeon"] else shot_for(k)
    try:
        if path:
            fn = "erstkill" + os.path.splitext(path)[1]
            emb.set_image(url=f"attachment://{fn}")
            await ch.send(embed=emb, file=discord.File(path, filename=fn))
        else:
            await ch.send(embed=emb)
    except discord.HTTPException as e:
        log.warning("Erstkill nicht gepostet: %s", e)
        return False
    # Dungeon: True = fertig (kein Screenshot nachreichen); Raid ohne Bild: False = Bild kommt evtl. später
    state.data.setdefault("first_posted", {})[f"{k['e']}:{k['t']}"] = bool(path) or area["dungeon"]
    return True


async def update_hall_of_fame():
    db = bot.dkp_db or {}
    if test_info(db):
        return
    added = rmd.kills_merge(kills_db.data, rmd.killlog(db), state.data.get("last_upload_by") or "")
    if added:
        kills_db.save()
    ch = await hall_channel() if cfg.get("hall_of_fame", True) else None
    posted = state.data.setdefault("first_posted", {})
    if ch:
        # Erstkills (auch Screenshots, die erst später ankommen)
        for k in kills_db.data["kills"]:
            if not k.get("f"):
                continue
            key = f"{k['e']}:{k['t']}"
            if key not in posted:
                if time.time() - k["t"] < 14 * 86400:
                    await post_first_kill(ch, k)
                else:
                    posted[key] = True
            elif posted[key] is False and not kill_area(k)["dungeon"] and shot_for(k):
                try:
                    path = shot_for(k)
                    await ch.send(f"📸 Der Screenshot vom Erstkill **{k['n']}**:", file=discord.File(path))
                    posted[key] = True
                except discord.HTTPException:
                    pass
        # Rekord-Tafeln je Raid (ab 1.5.136): ersetzen die einzelnen Zeilen "Neuer Rekord"
        try:
            await update_record_boards(ch)
        except discord.HTTPException as e:
            log.warning("Rekord-Tafeln nicht aktualisiert: %s", e)
        state.save()
    await update_achievements(ch)


RECORD_BOSSES = rekord_tafel.load_bosses()
RECORD_DUNGEONS = rekord_tafel.load_dungeons()      # ab 1.5.137: je Dungeon eine Tafel, nach Level sortiert


async def cleanup_old_record_lines(ch) -> int:
    """Einmal: die alten Einzelzeilen "⏱️ Neuer Rekord: …" des Bots löschen (ersetzt durch die Tafeln)."""
    n = 0
    async for m in ch.history(limit=2000):
        if m.author.id == bot.user.id and rekord_tafel.is_old_record_line(m.content):
            try:
                await m.delete()
                n += 1
            except discord.HTTPException:
                pass
            await asyncio.sleep(0.5)
    return n


async def update_record_boards(ch) -> dict:
    """Je Raid und je Dungeon eine Tafel in #ruhmeshalle, Raids und Dungeons unter eigener Überschrift getrennt
    (ab 1.5.139): einmal posten, danach nur bearbeiten (ab 1.5.136).
    Kommt ein Raid neu dazu oder fehlt eine Tafel, werden alle Tafeln in der richtigen Reihenfolge neu gepostet."""
    names = {r["key"]: rmd.pool_name(r["key"], bot.dkp_data) for r in RECORD_BOSSES}
    boards = rekord_tafel.with_headers(
        rekord_tafel.boards(kills_db.data.get("kills") or [], RECORD_BOSSES, names, RECORD_DUNGEONS))
    st = state.data.setdefault("record_boards", {"order": [], "msgs": {}, "hash": {}})
    res = {"posted": 0, "edited": 0, "deleted_old": 0}
    if not state.data.get("record_lines_cleaned"):
        res["deleted_old"] = await cleanup_old_record_lines(ch)
        state.data["record_lines_cleaned"] = True
        log.info("Ruhmeshalle: %d alte Rekordzeilen gelöscht", res["deleted_old"])

    def embed(b):
        e = discord.Embed(title=b["title"], description=rekord_tafel.board_text(b), colour=0xFF8C1A)
        ts = [r["t"] for r in b["rows"] if r["t"]]
        if ts:
            e.timestamp = datetime.fromtimestamp(max(ts), timezone.utc)
            e.set_footer(text="Neuester Rekord")
        return e
    keys = [b["key"] for b in boards]
    repost = keys != st.get("order")
    if not repost:
        for b in boards:
            h = rekord_tafel.board_hash(b)
            if st["hash"].get(b["key"]) == h:
                continue
            try:
                msg = await ch.fetch_message(int(st["msgs"][b["key"]]))
                if b.get("header"):
                    await msg.edit(content=b["header"])
                else:
                    await msg.edit(embed=embed(b))
                st["hash"][b["key"]] = h
                res["edited"] += 1
            except (discord.NotFound, KeyError, ValueError):
                repost = True
                break
    if repost:
        for mid in list(st.get("msgs", {}).values()):
            try:
                await (await ch.fetch_message(int(mid))).delete()
            except (discord.NotFound, ValueError):
                pass
        st["msgs"], st["hash"] = {}, {}
        for b in boards:
            msg = await (ch.send(b["header"]) if b.get("header") else ch.send(embed=embed(b)))
            st["msgs"][b["key"]] = msg.id
            st["hash"][b["key"]] = rekord_tafel.board_hash(b)
            res["posted"] += 1
        st["order"] = keys
    state.save()
    return res


@bot.tree.command(name="ruhmeshalle-aufraeumen",
                  description="Gildenleitung: Einträge in #ruhmeshalle bis und mit einem Datum löschen (erst Vorschau)")
@app_commands.describe(bis="Letzter Tag, der gelöscht wird, TT.MM.JJJJ (z. B. 14.11.2026)",
                       bestaetigen="True = wirklich löschen (endgültig). Ohne: nur zählen, nichts löschen")
async def ruhmeshalle_aufraeumen_cmd(inter: discord.Interaction, bis: str, bestaetigen: bool = False):
    """Ab 1.5.141 (Wunsch des Nutzers 15.11. 16:27: "Einträge bis und mit dem 14.11. löschen"). Löscht alle Nachrichten
    in #ruhmeshalle vor dem Folgetag 00:00 (Zeitzone des Bots) – nicht die aktuellen Rekord-Tafeln/Überschriften und
    nichts Angeheftetes. Erst Vorschau (Anzahl), dann mit bestaetigen:True. Die Kill-Daten bleiben erhalten."""
    if not is_admin(inter.user):
        await inter.response.send_message("Nur für den Gildenchef und die Offiziere.", ephemeral=True)
        return
    cutoff = rekord_tafel.cutoff_end_of_day(bis, ZoneInfo(TZ))
    if cutoff is None:
        await inter.response.send_message("Datum bitte als TT.MM.JJJJ, z. B. 14.11.2026.", ephemeral=True)
        return
    await inter.response.defer(ephemeral=True, thinking=True)
    ch = await hall_channel()
    if ch is None:
        await inter.followup.send("#ruhmeshalle nicht gefunden.", ephemeral=True)
        return
    keep = {int(x) for x in (state.data.get("record_boards") or {}).get("msgs", {}).values()}
    msgs = [m async for m in ch.history(limit=5000, before=datetime.fromtimestamp(cutoff, timezone.utc))]
    todo = rekord_tafel.cleanup_candidates(msgs, cutoff, keep)
    day = datetime.fromtimestamp(cutoff - 1, ZoneInfo(TZ)).strftime("%d.%m.%Y")
    if not bestaetigen:
        await inter.followup.send(
            f"🔎 Vorschau: In {ch.mention} würden **{len(todo)} Einträge** bis und mit **{day}** gelöscht "
            f"(angeheftete und die aktuellen Rekord-Tafeln bleiben). Endgültig, nicht rückgängig zu machen.\n"
            f"Zum Löschen: `/ruhmeshalle-aufraeumen bis:{bis.strip()} bestaetigen:True`", ephemeral=True)
        return
    done = failed = 0
    for m in todo:
        try:
            await m.delete()
            done += 1
        except discord.HTTPException:
            failed += 1
        await asyncio.sleep(0.6)            # Discord: nicht zu schnell
    # gelöschte Erstkills ohne Bild: kein "📸 Screenshot" mehr nachreichen (der Beitrag dazu ist weg)
    posted = state.data.setdefault("first_posted", {})
    for k in kills_db.data.get("kills") or []:
        key = f"{k['e']}:{k['t']}"
        if k["t"] < cutoff and posted.get(key) is False:
            posted[key] = True
    state.save()
    log.info("Ruhmeshalle aufgeräumt bis %s: %d gelöscht, %d nicht löschbar", day, done, failed)
    await inter.followup.send(f"🧹 {done} Einträge bis und mit {day} gelöscht"
                              + (f", {failed} konnten nicht gelöscht werden (Recht „Nachrichten verwalten“?)"
                                 if failed else "") + ".", ephemeral=True)


async def update_achievements(ch):
    earned = rmd.achievements(bot.dkp_data, kills_db.data)
    players = fame_db.data.setdefault("players", {})
    new = []
    for name, codes in earned.items():
        have = players.setdefault(name, {})
        for code, t in codes.items():
            if code not in have:
                have[code] = t
                new.append((name, code))
    first_run = not fame_db.data.get("init")
    fame_db.data["init"] = True
    fame_db.save()
    if first_run or not new or ch is None or not cfg.get("hall_of_fame", True):
        return
    lines = ["🎖️ **Neue Erfolge**"]
    for name, code in sorted(new):
        title, desc = rmd.achievement_title(code, kills_db.data.get("kills"))
        lines.append(f"• **{name}** – {title}" + (f" ({desc})" if desc else ""))
    for part in rmd.split_discord("\n".join(lines)):
        try:
            await ch.send(part)
        except discord.HTTPException:
            pass


@bot.tree.command(name="erfolge", description="Erfolge eines Charakters (leer = deine)")
@app_commands.describe(name="Charaktername")
async def erfolge_cmd(inter: discord.Interaction, name: str | None = None):
    if not name:
        p = book.profile(inter.user.id)
        name = (p.get("main") or p.get("name")) if p else None
    if not name:
        await inter.response.send_message("Gib einen Namen an oder lege dein Profil an (`/charakter`).", ephemeral=True)
        return
    have = next((v for k, v in (fame_db.data.get("players") or {}).items() if k.lower() == name.lower()), None)
    if not have:
        await inter.response.send_message(f"{name} hat noch keine Erfolge – das kommt noch! 💪", ephemeral=True)
        return
    lines = [f"🎖️ **Erfolge von {name}** ({len(have)})"]
    for code, t in sorted(have.items(), key=lambda x: x[1]):
        title, desc = rmd.achievement_title(code, kills_db.data.get("kills"))
        lines.append(f"• **{title}**" + (f" – {desc}" if desc else "") + (f" (<t:{t}:d>)" if t else ""))
    await inter.response.send_message("\n".join(lines)[:2000], ephemeral=True)
