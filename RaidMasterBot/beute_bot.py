"""Beute-Datenbank (D-3 Schritt 12, ab Bot 1.5.157): eigene Beute-Datenbank aus den Raids (welcher Boss droppt
was), Beutetabellen in den Loot-Kanälen und die Befehle /beute boss|entfernen|export|tabellen.

UNVERÄNDERT aus bot.py verschoben: update_lootdb, lootdb_text, post_loot_table, beute_group,
lootdb_boss_autocomplete, _boss_by_value, beute_boss, beute_entfernen, beute_export, beute_tabellen und die
Anmeldung der Gruppe (bot.tree.add_command(beute_group)). Die Rechnungen stehen in raidmaster_data.py
(lootdb_merge, lootdb_pools …). Regeln mit Materialien nachziehen: regeln_bot.py.
bot.py importiert dieses Modul nach "grund.bot = bot" (/beute wird beim Import angemeldet) und übernimmt die
Namen. Weg A (Antwort der Prüf-Sitzung 15.11. 20:48).
"""
from __future__ import annotations

import io
import json
import time

import discord
from discord import app_commands

import grund
import raidmaster_data as rmd
from bot_hilfen import test_info
from grund import channel_by_id, is_creator, raid_channel
from kern import cfg, log, lootdb, state
from regeln_bot import ensure_dkp_rules, ensure_guild_rules
from symbole_bot import item_emoji

bot = grund.bot
assert bot is not None, "beute_bot erst nach grund.bot = bot importieren"


async def update_lootdb(force_pools: list[str] | None = None):
    db = bot.dkp_db or {}
    if test_info(db):
        return
    uploader = state.data.get("last_upload_by") or ""
    added = rmd.lootdb_merge(lootdb.data, db, uploader)
    if added:
        lootdb.save()
        log.info("Beute-Datenbank: %d neue Kills von %s.", added, uploader or "?")
    # neue Materialien/Rezepte aus der Beute und den Berufen: #regeln und #pug-regeln nachziehen (nur bei Änderung)
    try:
        await ensure_dkp_rules()
        await ensure_guild_rules()
    except Exception as e:  # noqa: BLE001
        log.warning("Regeln mit Materialien nicht aktualisiert: %s", e)
    if not cfg.get("loot_tables", True):
        return
    pools = force_pools if force_pools is not None else (rmd.lootdb_pools(lootdb.data) if added else [])
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
    lists = [rmd.lootdb_boss_loot(lootdb.data, b["e"])[0][:15] for b in rmd.lootdb_bosses(lootdb.data, pool)]
    lists.append(rmd.lootdb_trash_loot(lootdb.data, pool)[0][:20])
    for items in lists:
        for it in items:
            if it["id"] not in emojis:
                link = rmd.item_link_for(it["id"], it["n"], it["q"])
                emojis[it["id"]] = await item_emoji(link, {"ic": it.get("ic"), "q": it.get("q")})
    kills = sum(b["kills"] for b in rmd.lootdb_bosses(lootdb.data, pool))
    head = (f"📖 **Beutetabelle {rmd.pool_name(pool, bot.dkp_data)}** – aus euren eigenen Raids ({kills} Bosskills, "
            f"{rmd.lootdb_trash_loot(lootdb.data, pool)[1]} Trash-Leichen) · "
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
        await inter.response.send_message("Das dürfen nur der Gildenchef und die Offiziere.", ephemeral=True)
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
        await inter.response.send_message("Das dürfen nur der Gildenchef und die Offiziere.", ephemeral=True)
        return
    data = json.dumps(lootdb.data, ensure_ascii=False, indent=1).encode("utf-8")
    await inter.response.send_message(f"Beute-Datenbank: {len(lootdb.data.get('kills') or [])} Kills, "
                                      f"{len(lootdb.data.get('items') or {})} Items.",
                                      file=discord.File(io.BytesIO(data), filename="beute-datenbank.json"), ephemeral=True)


@beute_group.command(name="tabellen", description="Beutetabellen in den Loot-Kanälen neu posten (Offiziere)")
async def beute_tabellen(inter: discord.Interaction):
    if not is_creator(inter.user):
        await inter.response.send_message("Das dürfen nur der Gildenchef und die Offiziere.", ephemeral=True)
        return
    await inter.response.defer(ephemeral=True)
    pools = rmd.lootdb_pools(lootdb.data)
    await update_lootdb(pools)
    await inter.followup.send(f"Beutetabellen gepostet: {', '.join(rmd.pool_name(p, bot.dkp_data) for p in pools) or 'noch keine Daten'}.",
                              ephemeral=True)


bot.tree.add_command(beute_group)
