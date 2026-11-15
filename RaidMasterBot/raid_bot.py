"""Raids (D-3 Schritt 32, ab Bot 1.5.179): /raid erstellen|testraid|absagen|softres|schliessen|oeffnen|export|
liste|aufstellung|taktik, Testraid mit 40 Anmeldungen, Aufstellung und Einteilung (aus dem Addon), Taktiken je
Raid, /rekorde, Erinnerungs-Schleife (Erinnerung und automatisches Schliessen), Export für das Addon.

UNVERÄNDERT aus bot.py verschoben: der ganze Abschnitt "Befehle: /raid ..." bis bot.tree.add_command(raid_group)
(samt Testraid-Daten und Laden der Taktiken aus raid_tactics.json neben dieser Datei – gleicher Ordner wie bot.py)
sowie send_export, rekorde_cmd, reminder_loop, before_reminder, process_assignment.
bot.py importiert dieses Modul nach "grund.bot = bot" (/raid und /rekorde werden beim Import angemeldet) und
übernimmt die Namen, die RaidBot, Anmeldung und Uploads brauchen. Weg A (Antwort der Prüf-Sitzung 15.11. 20:48).
"""
from __future__ import annotations

import asyncio
import io
import json
import os
import time
import zlib
from datetime import datetime
from zoneinfo import ZoneInfo

import discord
from discord import app_commands
from discord.ext import tasks

import abwesenheit
import grund
import mc_tactics
import member_area
import raid_post
import raidmaster_data as rmd
import server_setup
from bot_hilfen import clean_softres, raid_view
from dkp_befehle_bot import reload_dkp_if_needed
from ereignis_bot import create_raid_event, delete_raid_event
from grund import bot_guild, channel_by_id, is_creator, raid_channel
from kern import TZ, book, cfg, kills_db, log, save_config, state
from raidanzeige_bot import absence_line, raid_embed, update_raid_message

bot = grund.bot
assert bot is not None, "raid_bot erst nach grund.bot = bot importieren"


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
    absent = absence_line(raid)                                   # D-N1 (ab 1.5.184)
    if absent:
        if len(texts[-1]) + len(absent) + 1 <= 2000:
            texts[-1] += "\n" + absent
        else:
            texts.append(absent)
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


@raid_group.command(name="grenzen", description="Plätze je Rolle festlegen (z. B. höchstens 8 Heiler) – darüber Ersatzbank")
@app_commands.describe(raid="Welcher Raid?", tanks="höchstens so viele Tanks (0 = keine Grenze)",
                       heiler="höchstens so viele Heiler (0 = keine Grenze)",
                       nahkampf="höchstens so viele Nahkämpfer (0 = keine Grenze)",
                       fernkampf="höchstens so viele Fernkämpfer (0 = keine Grenze)")
@app_commands.autocomplete(raid=raid_autocomplete)
async def raid_limits(inter: discord.Interaction, raid: str, tanks: app_commands.Range[int, 0, 40] | None = None,
                      heiler: app_commands.Range[int, 0, 40] | None = None,
                      nahkampf: app_commands.Range[int, 0, 40] | None = None,
                      fernkampf: app_commands.Range[int, 0, 40] | None = None):
    """D-N1 Wunsch 4 (ab Bot 1.5.185): Plätze je Rolle. Ohne Werte: zeigt den Stand. Schon Angemeldete bleiben
    angemeldet (niemand wird verschoben); neue Anmeldungen über der Grenze kommen auf die Ersatzbank."""
    if not is_creator(inter.user):
        await inter.response.send_message("Das dürfen nur der Gildenchef und die Offiziere.", ephemeral=True)
        return
    r = book.get(raid)
    if not r:
        await inter.response.send_message("Raid nicht gefunden.", ephemeral=True)
        return
    given = {"tank": tanks, "heal": heiler, "melee": nahkampf, "ranged": fernkampf}
    if any(v is not None for v in given.values()):
        limits = dict(r.get("limits") or {})
        for role, v in given.items():
            if v is None:
                continue
            if v:
                limits[role] = v
            else:
                limits.pop(role, None)
        if limits:
            r["limits"] = limits
        else:
            r.pop("limits", None)
        book.save()
        await update_raid_message(r)
    text = rmd.limits_text(r) or "Keine Grenzen je Rolle – alle Plätze offen (bis zur Höchstzahl des Raids)."
    over = [rmd.ROLES[role] for role in rmd.LIMIT_ROLES if (r.get("limits") or {}).get(role)
            and sum(1 for s in r["signups"].values() if s["status"] == "an" and s.get("role") == role) > r["limits"][role]]
    if over:
        text += ("\nSchon mehr angemeldet als erlaubt: " + ", ".join(over) + " – die Angemeldeten bleiben, neue kommen "
                 "auf die Ersatzbank.")
    await inter.response.send_message(f"**{r['title']}**\n{text}", ephemeral=True)


def missing_members(members, signups: dict, absent: set[str] | None = None) -> list[str]:
    """D-N1 (ab Bot 1.5.183): Gildenmitglieder (Rolle Mitglied, Raider, Raidleitung oder Offizier; keine Bots) ohne
    jede Rückmeldung (angemeldet, Ersatzbank, vielleicht, abgemeldet) zu einem Raid – sortiert nach Anzeigename.
    Ab 1.5.184: wer am Raidtag abwesend gemeldet ist (absent: Discord-IDs als Text), bekommt "(abwesend gemeldet)"."""
    roles = {n.lower() for n in member_area.MEMBER_ROLES}
    out = []
    for m in members:
        if m.bot or str(m.id) in signups:
            continue
        if any(r.name.lower() in roles for r in m.roles):
            out.append(m.display_name + (" (abwesend gemeldet)" if absent and str(m.id) in absent else ""))
    return sorted(out, key=str.lower)


@raid_group.command(name="fehlend", description="Wer aus der Gilde hat sich zu einem Raid noch nicht gemeldet? (Offiziere)")
@app_commands.describe(raid="Welcher Raid?")
@app_commands.autocomplete(raid=raid_autocomplete)
async def raid_missing(inter: discord.Interaction, raid: str):
    """Nur für die Gildenleitung sichtbar (ephemeral); der Bot schreibt niemanden an."""
    if not is_creator(inter.user):
        await inter.response.send_message("Das dürfen nur der Gildenchef und die Offiziere.", ephemeral=True)
        return
    r = book.get(raid)
    if not r:
        await inter.response.send_message("Raid nicht gefunden.", ephemeral=True)
        return
    guild = inter.guild or bot_guild()
    if guild is None or not bot.intents.members:
        await inter.response.send_message(
            "Dafür braucht der Bot die Mitgliederliste: im Discord-Entwicklerportal unter Bot → Privileged Gateway "
            "Intents den **Server Members Intent** einschalten und den Bot neu starten.", ephemeral=True)
        return
    day = datetime.fromtimestamp(r["start"], ZoneInfo(TZ)).date()
    names = missing_members(guild.members, r["signups"], abwesenheit.absent_on(state.data.get("absences") or {}, day))
    if not names:
        await inter.response.send_message(f"Zu **{r['title']}** haben sich alle Gildenmitglieder gemeldet. ✅",
                                          ephemeral=True)
        return
    text = f"**{r['title']}** – noch keine Rückmeldung von {len(names)} Mitgliedern:\n"
    shown = 0
    for n in names:
        if len(text) + len(n) + 40 > 1900:
            break
        text += f"• {n}\n"
        shown += 1
    if shown < len(names):
        text += f"… und {len(names) - shown} weitere."
    await inter.response.send_message(text, ephemeral=True)


bot.tree.add_command(raid_group)


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
