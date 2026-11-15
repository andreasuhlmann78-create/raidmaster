"""Gildenname (D-3 Schritt 15, ab Bot 1.5.160): Abstimmung über den Gildennamen in #gildenname (Vorschläge per
Knopf, /gildenname oder als Beitrag, je Vorschlag eine Karte, Übersicht, eine Stimme je Mitglied) und der feste
Gildenname (FIXED_GUILD_NAME: Abstimmung schliessen, Namen übernehmen – einmal beim Start).

UNVERÄNDERT aus bot.py verschoben: der ganze Abschnitt "Abstimmung über den Gildennamen" bis apply_fixed_guild_name,
samt Kommentaren, Konstanten und bot.tree.add_command(name_group). Willkommenstext: willkommen_bot.py.
bot.py importiert dieses Modul nach "grund.bot = bot" (/gildenname wird beim Import angemeldet) und übernimmt die
Namen, die RaidBot, on_interaction und die Befehlsliste brauchen. Weg A (Antwort der Prüf-Sitzung 15.11. 20:48).
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import time

import discord
from discord import app_commands

import grund
from bot_hilfen import name_key, proposer_text, vote_word
from grund import NO_PING, bot_guild, channel_by_id, is_admin, is_chef, post_bot_log
from kern import BASE, ORANGE, book, cfg, log, save_config, state
from willkommen_bot import ensure_welcome

bot = grund.bot
assert bot is not None, "gildenname_bot erst nach grund.bot = bot importieren"


# ---------------------------------------------------------------------------
# Abstimmung über den Gildennamen (#gildenname)
# Jeder kann einen Namen vorschlagen (Knopf, /gildenname vorschlagen oder einfach den Namen in den Kanal schreiben),
# jeder hat eine Stimme (umsetzbar). Zu jedem Vorschlag gibt es eine Karte mit Lore; die Übersicht verlinkt sie.
# ---------------------------------------------------------------------------

NAME_SEEDS_PATH = os.path.join(BASE, "gildenname_vorschlaege.json")
NAME_MIN, NAME_MAX = 2, 24          # WoW: Gildennamen höchstens 24 Zeichen
NAME_STOPWORDS = {"ja", "nein", "ok", "okay", "cool", "nice", "top", "gut", "super", "lol", "haha", "hehe", "danke",
                  "merci", "mega", "geil", "hmm", "hm", "jo", "jep", "nope", "genau", "stimmt", "same", "idk", "gg",
                  "wow", "krass", "hallo", "hoi", "hey", "sali", "salü", "servus", "moin", "gute idee", "finde ich gut"}
# Wörter, an denen man normale Chat-Sätze erkennt ("ich bin dafür") – solche Beiträge sind keine Vorschläge
NAME_CHAT_WORDS = {"ich", "du", "er", "sie", "es", "wir", "ihr", "mir", "mich", "dich", "uns", "euch", "bin", "bist", "ist",
                   "sind", "seid", "war", "wäre", "finde", "findest", "mag", "gefällt", "gefaellt", "klingt", "dafür",
                   "dafuer", "dagegen", "nicht", "kein", "keine", "auch", "aber", "oder", "hat", "habe", "haben", "wie",
                   "was", "wer", "warum", "lieber", "eher", "vielleicht", "besser", "bitte"}
name_lock = asyncio.Lock()


def name_poll() -> dict:
    p = state.data.setdefault("name_poll", {})
    p.setdefault("proposals", {})
    p.setdefault("order", [])
    p.setdefault("seeded", [])
    p.setdefault("imported", [])
    p.setdefault("hinted", [])
    p.setdefault("closed", False)
    p.setdefault("next_id", 1)
    return p


def check_guild_name(raw: str) -> tuple[str | None, str | None]:
    """(sauberer Name, None) oder (None, Fehlertext)."""
    name = re.sub(r"\s+", " ", (raw or "").strip().strip("\"'«»„“”*_`"))
    if len(name) < NAME_MIN or len(name) > NAME_MAX:
        return None, f"Ein Gildenname muss {NAME_MIN} bis {NAME_MAX} Zeichen lang sein."
    if not all(ch.isalpha() or ch in " '-" for ch in name) or not any(ch.isalpha() for ch in name):
        return None, "Ein Gildenname darf nur Buchstaben, Leerzeichen, Bindestrich und Apostroph enthalten (keine Zahlen)."
    for pid in name_poll()["order"]:
        other = name_poll()["proposals"].get(pid)
        if other and name_key(other["name"]) == name_key(name):
            return None, f"**{other['name']}** wurde schon vorgeschlagen – gib ihm doch deine Stimme."
    return name, None


async def name_channel():
    if name_poll().get("closed") and cfg.get("name_poll_channel_id"):
        # Abstimmung vorbei und #gildenname gelöscht (12.11.2026): nicht bei jedem Start "Unknown Channel" melden
        guild = bot_guild()
        if guild is not None and guild.get_channel(int(cfg["name_poll_channel_id"])) is None:
            cfg.pop("name_poll_channel_id", None)
            save_config()
            return None
    ch = await channel_by_id(cfg.get("name_poll_channel_id"))
    if ch:
        return ch
    guild = bot_guild()
    if guild is None:
        return None
    ch = next((c for c in guild.text_channels if "gildenname" in c.name.lower()), None)
    # Abstimmung beendet (ab Bot 1.5.99): fehlt der Kanal, wird er nicht neu angelegt – er darf gelöscht werden
    if ch is None and name_poll().get("closed"):
        return None
    if ch is None and guild.me.guild_permissions.manage_channels:
        category = None
        for name in ("ankündigungen", "ankuendigungen", "announcements", "willkommen"):
            other = discord.utils.get(guild.text_channels, name=name)
            if other and other.category:
                category = other.category
                break
        try:
            ch = await guild.create_text_channel("gildenname", category=category,
                                                 topic="🏷️ Abstimmung über unseren Gildennamen – Namen vorschlagen und abstimmen.")
        except discord.HTTPException as e:
            log.warning("#gildenname nicht angelegt: %s", e)
            return None
    if ch:
        cfg["name_poll_channel_id"] = ch.id
        save_config()
    return ch


def name_ranking() -> list[dict]:
    p = name_poll()
    items = [p["proposals"][pid] for pid in p["order"] if pid in p["proposals"]]
    return sorted(items, key=lambda x: (-len(x.get("votes", [])), x.get("created", 0)))


def name_card_embed(prop: dict) -> discord.Embed:
    lore = (prop.get("lore") or "").strip()
    e = discord.Embed(title=f"🏷️ {prop['name']}", color=ORANGE,
                      description=lore[:4096] if lore else "_Noch keine Lore – wer den Namen vorgeschlagen hat, kann sie mit „Lore bearbeiten“ ergänzen._")
    e.add_field(name="Vorgeschlagen von", value=proposer_text(prop), inline=True)
    e.add_field(name="Stimmen", value=str(len(prop.get("votes", []))), inline=True)
    e.set_footer(text="Abstimmung beendet" if name_poll()["closed"] else "Eine Stimme pro Person – ein Klick auf einen anderen Namen verschiebt sie.")
    return e


def name_card_view(prop: dict) -> discord.ui.View:
    closed = name_poll()["closed"]
    v = discord.ui.View(timeout=None)
    v.add_item(discord.ui.Button(label=f"Dafür stimmen ({len(prop.get('votes', []))})", emoji="👍",
                                 style=discord.ButtonStyle.success, custom_id=f"rmname:vote:{prop['id']}", disabled=closed))
    v.add_item(discord.ui.Button(label="Lore bearbeiten", emoji="📜", style=discord.ButtonStyle.secondary,
                                 custom_id=f"rmname:lore:{prop['id']}"))
    v.add_item(discord.ui.Button(label="Entfernen", emoji="🗑️", style=discord.ButtonStyle.danger,
                                 custom_id=f"rmname:del:{prop['id']}"))
    return v


def name_overview_text() -> str:
    p = name_poll()
    ranking = name_ranking()
    medals = ["🥇", "🥈", "🥉"]
    lines = ["🗳️ **Abstimmung: Unser Gildenname**"]
    if p["closed"]:
        lines.append("**Die Abstimmung ist beendet.**" + (f" Gewonnen hat **{p['winner']}**! 🔥" if p.get("winner") else ""))
    else:
        lines.append("Schreib einfach einen Namen in diesen Kanal oder nutze den Knopf unten. Jeder hat **eine Stimme** – "
                     "stimme direkt auf der Karte des Namens ab. Klick auf einen Namen, um seine Karte mit der Lore zu öffnen.")
    lines.append("")
    if not ranking:
        lines.append("_Noch keine Vorschläge._")
    for i, prop in enumerate(ranking):
        rank = medals[i] if i < 3 and prop.get("votes") else f"{i + 1}."
        name = f"[{prop['name']}]({prop['url']})" if prop.get("url") else prop["name"]
        lore = f" · 📜 [Lore lesen]({prop['url']})" if prop.get("lore") and prop.get("url") else ""
        lines.append(f"{rank} **{name}** – {vote_word(len(prop.get('votes', [])))}{lore} · von {proposer_text(prop)}")
    text = "\n".join(lines)
    return text if len(text) <= 1990 else text[:1980] + "\n…"


def name_overview_view() -> discord.ui.View:
    v = discord.ui.View(timeout=None)
    v.add_item(discord.ui.Button(label="Namen vorschlagen", emoji="✏️", style=discord.ButtonStyle.primary,
                                 custom_id="rmname:new:0", disabled=name_poll()["closed"]))
    return v




async def refresh_name_overview(repost: bool = False):
    """Übersicht aktualisieren; repost=True schiebt sie ans Ende des Kanals (nach einem neuen Vorschlag)."""
    ch = await name_channel()
    if ch is None:
        return
    p = name_poll()
    mid = p.get("overview_msg")
    if mid and not repost:
        try:
            await ch.get_partial_message(int(mid)).edit(content=name_overview_text(), view=name_overview_view(), allowed_mentions=NO_PING)
            return
        except discord.HTTPException:
            pass
    if mid:
        try:
            await ch.get_partial_message(int(mid)).delete()
        except discord.HTTPException:
            pass
    msg = await ch.send(name_overview_text(), view=name_overview_view(), allowed_mentions=NO_PING)
    p["overview_msg"] = msg.id
    state.save()


async def refresh_name_card(prop: dict):
    ch = await name_channel()
    if ch is None or not prop.get("msg"):
        return
    try:
        await ch.get_partial_message(int(prop["msg"])).edit(embed=name_card_embed(prop), view=name_card_view(prop), allowed_mentions=NO_PING)
    except discord.HTTPException:
        log.warning("Karte für %s konnte nicht aktualisiert werden", prop.get("name"))


async def add_name_proposal(name: str, by_id: int | None, by_name: str, lore: str = "", created: int | None = None) -> dict:
    """Legt einen Vorschlag an (Name muss geprüft sein), postet die Karte und schiebt die Übersicht nach unten."""
    ch = await name_channel()
    if ch is None:
        raise RuntimeError("Kanal #gildenname nicht gefunden")
    p = name_poll()
    pid = str(p["next_id"])
    p["next_id"] += 1
    prop = {"id": pid, "name": name, "by": by_id, "by_name": by_name, "lore": (lore or "").strip()[:4000],
            "votes": [], "created": created or int(time.time())}
    msg = await ch.send(embed=name_card_embed(prop), view=name_card_view(prop), allowed_mentions=NO_PING)
    prop["msg"], prop["url"] = msg.id, msg.jump_url
    p["proposals"][pid] = prop
    p["order"].append(pid)
    state.save()
    await refresh_name_overview(repost=True)
    return prop


def member_by_char(char: str):
    guild = bot_guild()
    if guild is None or not char:
        return None
    uid = book.user_for_char(char)
    if uid:
        m = guild.get_member(int(uid))
        if m:
            return m
    low = char.strip().lower()
    for m in guild.members:
        for cand in (m.nick, m.global_name, m.name):
            c = str(cand or "").strip().lower()
            if c and (c == low or c.startswith(low + " ")):
                return m
    return None


def name_from_post(message: discord.Message) -> str | None:
    """Ein Beitrag zählt als Vorschlag, wenn er nur aus einem möglichen Gildennamen besteht (eine Zeile)."""
    text = message.content or ""
    if bot.user:
        text = text.replace(f"<@{bot.user.id}>", "").replace(f"<@!{bot.user.id}>", "")
    text = text.strip()
    if not text or "\n" in text or "http" in text.lower() or "<" in text:
        return None
    if text.strip("!?.").casefold() in NAME_STOPWORDS or text.endswith("?"):
        return None
    words = re.findall(r"[^\W\d_]+", text.casefold())
    if len(words) > 3 or any(w in NAME_CHAT_WORDS for w in words):
        return None
    name, err = check_guild_name(text.strip("!."))
    if name and sum(ch.isalpha() for ch in name) >= 4:
        return name
    return None


async def handle_name_post(message: discord.Message):
    if name_poll()["closed"]:
        return
    if not message.content:
        # ohne "Message Content Intent" kann der Bot den Text nicht lesen -> einmal auf den Knopf hinweisen
        p = name_poll()
        if message.author.id not in p["hinted"]:
            p["hinted"].append(message.author.id)
            state.save()
            try:
                await message.reply("Ich kann hier leider nur Vorschläge lesen, die mit dem Knopf **„Namen vorschlagen“** "
                                    "eingetragen werden (oder in denen du mich erwähnst). Klick ihn unten in der Übersicht an. 🙂",
                                    mention_author=False, delete_after=60)
            except discord.HTTPException:
                pass
        return
    raw = message.content
    if bot.user:
        raw = raw.replace(f"<@{bot.user.id}>", "").replace(f"<@!{bot.user.id}>", "").strip()
    name = name_from_post(message)
    if not name:
        _, err = check_guild_name(raw)
        if err and "schon vorgeschlagen" in err:
            try:
                await message.reply(err, mention_author=False, delete_after=60, allowed_mentions=NO_PING)
            except discord.HTTPException:
                pass
        return
    async with name_lock:
        name, err = check_guild_name(name)
        if not name:
            return
        prop = await add_name_proposal(name, message.author.id, message.author.display_name, created=int(message.created_at.timestamp()))
        name_poll()["imported"].append(message.id)
        state.save()
    try:
        await message.add_reaction("✅")
    except discord.HTTPException:
        pass
    log.info("Gildenname vorgeschlagen: %s (von %s)", prop["name"], message.author)


async def import_old_name_posts() -> int:
    """Beiträge, die schon vor der Abstimmung im Kanal standen, als Vorschläge übernehmen."""
    ch = await name_channel()
    if ch is None:
        return 0
    p = name_poll()
    done, unreadable = 0, 0
    msgs = []
    try:
        async for m in ch.history(limit=200, oldest_first=True):
            msgs.append(m)
    except discord.HTTPException:
        return 0
    for m in msgs:
        if m.author.bot or m.id in p["imported"]:
            continue
        if not m.content:
            unreadable += 1
            continue
        name = name_from_post(m)
        if not name:
            continue
        name, err = check_guild_name(name)
        if not name:
            continue
        await add_name_proposal(name, m.author.id, m.author.display_name, created=int(m.created_at.timestamp()))
        p["imported"].append(m.id)
        state.save()
        done += 1
        try:
            await m.add_reaction("✅")
        except discord.HTTPException:
            pass
    if unreadable and not p.get("unreadable_warned"):
        p["unreadable_warned"] = True
        state.save()
        await post_bot_log(f"🏷️ In {ch.mention} stehen {unreadable} ältere Beiträge, die der Bot nicht lesen kann (Message Content "
                           "Intent ist aus). Bitte solche Namen mit `/gildenname hinzufuegen` in die Abstimmung übernehmen.")
    return done


async def ensure_name_poll() -> str:
    """Beim Start: Kanal finden, alte Beiträge übernehmen, Vorschläge der Gildenleitung posten, Übersicht aktuell halten."""
    ch = await name_channel()
    if ch is None:
        return "Kanal #gildenname nicht gefunden."
    async with name_lock:
        p = name_poll()
        report = []
        if not p.get("started"):
            n = await import_old_name_posts()
            p["started"] = True
            state.save()
            if n:
                report.append(f"{n} Vorschläge aus dem Kanal übernommen")
        seeds = []
        try:
            with open(NAME_SEEDS_PATH, "r", encoding="utf-8") as f:
                seeds = json.load(f).get("vorschlaege", [])
        except (OSError, ValueError):
            pass
        for s in seeds:
            key = s.get("key") or name_key(s.get("name", ""))
            if not key or key in p["seeded"]:
                continue
            p["seeded"].append(key)
            state.save()
            name, err = check_guild_name(s.get("name", ""))
            if not name:
                continue   # schon vorgeschlagen (z. B. von Hand) – nicht doppelt
            m = member_by_char(s.get("von", ""))
            await add_name_proposal(name, m.id if m else None, m.display_name if m else (s.get("von") or "Gildenleitung"), s.get("lore", ""))
            report.append(f"„{name}“ eingetragen")
        await refresh_name_overview()
    return f"🏷️ Abstimmung in {ch.mention}: " + (", ".join(report) if report else "aktuell")


class NameProposalModal(discord.ui.Modal):
    def __init__(self, prop: dict | None = None):
        super().__init__(title="Lore bearbeiten" if prop else "Gildennamen vorschlagen")
        self.prop = prop
        self.name_input = None
        if not prop:
            self.name_input = discord.ui.TextInput(label="Gildenname", min_length=NAME_MIN, max_length=NAME_MAX,
                                                   placeholder="z. B. Alpine Vanguard")
            self.add_item(self.name_input)
        self.lore_input = discord.ui.TextInput(label="Lore / Geschichte zum Namen (freiwillig)", style=discord.TextStyle.paragraph,
                                               required=False, max_length=4000, default=(prop or {}).get("lore") or None,
                                               placeholder="Warum dieser Name? Eine kleine Geschichte dazu …")
        self.add_item(self.lore_input)

    async def on_submit(self, inter: discord.Interaction):
        lore = (self.lore_input.value or "").strip()
        if self.prop:
            async with name_lock:
                prop = name_poll()["proposals"].get(self.prop["id"])
                if not prop:
                    await inter.response.send_message("Diesen Vorschlag gibt es nicht mehr.", ephemeral=True)
                    return
                prop["lore"] = lore
                state.save()
            await inter.response.send_message("📜 Lore gespeichert.", ephemeral=True)
            await refresh_name_card(prop)
            await refresh_name_overview()
            return
        if name_poll()["closed"]:
            await inter.response.send_message("Die Abstimmung ist beendet.", ephemeral=True)
            return
        await inter.response.defer(ephemeral=True, thinking=True)
        async with name_lock:
            name, err = check_guild_name(self.name_input.value)
            if not name:
                await inter.followup.send(err, ephemeral=True)
                return
            prop = await add_name_proposal(name, inter.user.id, inter.user.display_name, lore)
        await inter.followup.send(f"✅ **{prop['name']}** ist in der Abstimmung: {prop['url']}", ephemeral=True)


def may_edit_proposal(user, prop: dict) -> bool:
    return is_admin(user) or (prop.get("by") and int(prop["by"]) == user.id)


async def handle_name_button(inter: discord.Interaction, action: str, pid: str):
    p = name_poll()
    if action == "new":
        if p["closed"]:
            await inter.response.send_message("Die Abstimmung ist beendet.", ephemeral=True)
            return
        await inter.response.send_modal(NameProposalModal())
        return
    prop = p["proposals"].get(pid)
    if not prop:
        await inter.response.send_message("Diesen Vorschlag gibt es nicht mehr.", ephemeral=True)
        return
    if action == "lore":
        if not may_edit_proposal(inter.user, prop):
            await inter.response.send_message("Die Lore kann nur ändern, wer den Namen vorgeschlagen hat (oder die Gildenleitung).", ephemeral=True)
            return
        await inter.response.send_modal(NameProposalModal(prop))
        return
    if action == "del":
        if not may_edit_proposal(inter.user, prop):
            await inter.response.send_message("Entfernen kann nur, wer den Namen vorgeschlagen hat (oder die Gildenleitung).", ephemeral=True)
            return
        async with name_lock:
            p["proposals"].pop(pid, None)
            if pid in p["order"]:
                p["order"].remove(pid)
            state.save()
        await inter.response.send_message(f"🗑️ **{prop['name']}** wurde aus der Abstimmung entfernt.", ephemeral=True)
        try:
            await inter.message.delete()
        except (discord.HTTPException, AttributeError):
            pass
        await refresh_name_overview()
        return
    if action == "vote":
        if p["closed"]:
            await inter.response.send_message("Die Abstimmung ist beendet.", ephemeral=True)
            return
        uid = inter.user.id
        changed = []
        async with name_lock:
            if uid in prop["votes"]:
                prop["votes"].remove(uid)
                note = f"Deine Stimme für **{prop['name']}** ist zurückgenommen."
            else:
                for other in p["proposals"].values():
                    if uid in other.get("votes", []):
                        other["votes"].remove(uid)
                        changed.append(other)
                prop["votes"].append(uid)
                note = f"👍 Deine Stimme geht an **{prop['name']}**." + (f" (vorher: {changed[0]['name']})" if changed else "")
            state.save()
        await inter.response.edit_message(embed=name_card_embed(prop), view=name_card_view(prop))
        await inter.followup.send(note, ephemeral=True)
        for other in changed:
            await refresh_name_card(other)
        await refresh_name_overview()


name_group = app_commands.Group(name="gildenname", description="Abstimmung über den Gildennamen")


@name_group.command(name="vorschlagen", description="Einen Gildennamen (mit Lore) für die Abstimmung vorschlagen")
async def name_propose_cmd(inter: discord.Interaction):
    if name_poll()["closed"]:
        await inter.response.send_message("Die Abstimmung ist beendet.", ephemeral=True)
        return
    await inter.response.send_modal(NameProposalModal())


@name_group.command(name="hinzufuegen", description="Vorschlag eines Mitglieds in die Abstimmung übernehmen (Gildenleitung)")
@app_commands.describe(name="Der vorgeschlagene Gildenname", von="Wer den Namen vorgeschlagen hat", lore="Lore/Geschichte (freiwillig)")
async def name_add_cmd(inter: discord.Interaction, name: str, von: discord.Member | None = None, lore: str = ""):
    if not is_admin(inter.user):
        await inter.response.send_message("Das dürfen nur der Gildenchef und die Offiziere.", ephemeral=True)
        return
    await inter.response.defer(ephemeral=True, thinking=True)
    async with name_lock:
        clean, err = check_guild_name(name)
        if not clean:
            await inter.followup.send(err, ephemeral=True)
            return
        who = von or inter.user
        prop = await add_name_proposal(clean, who.id, who.display_name, lore)
    await inter.followup.send(f"✅ **{prop['name']}** (von {who.display_name}) ist in der Abstimmung: {prop['url']}", ephemeral=True)


@name_group.command(name="abschliessen", description="Abstimmung beenden und Gewinner verkünden (Gildenleitung)")
@app_commands.describe(uebernehmen="Gewinner als Gildennamen speichern und den Willkommenstext anpassen")
async def name_close_cmd(inter: discord.Interaction, uebernehmen: bool = False):
    if not is_admin(inter.user):
        await inter.response.send_message("Das dürfen nur der Gildenchef und die Offiziere.", ephemeral=True)
        return
    await inter.response.defer(ephemeral=True, thinking=True)
    ranking = name_ranking()
    p = name_poll()
    if not ranking:
        await inter.followup.send("Es gibt noch keine Vorschläge.", ephemeral=True)
        return
    top = len(ranking[0].get("votes", []))
    leaders = [x for x in ranking if len(x.get("votes", [])) == top]
    if top == 0 or len(leaders) > 1:
        names = ", ".join(f"**{x['name']}**" for x in leaders)
        await inter.followup.send(f"Kein klarer Gewinner (Gleichstand bei {vote_word(top)}: {names}). "
                                  "Die Abstimmung läuft weiter – z. B. eine Stichwahl mit diesen Namen machen.", ephemeral=True)
        return
    winner = leaders[0]["name"]
    async with name_lock:
        p["closed"] = True
        p["winner"] = winner
        state.save()
    for prop in ranking:
        await refresh_name_card(prop)
    await refresh_name_overview(repost=True)
    note = f"🔥 Abstimmung beendet – Gewinner: **{winner}** ({vote_word(top)})."
    if uebernehmen and not is_chef(inter.user):
        note += "\nDen Gildennamen übernehmen kann nur der Gildenchef (`/willkommen gildenname:…`)."
        uebernehmen = False
    if uebernehmen:
        cfg["guild_name"] = winner
        save_config()
        note += "\n" + await ensure_welcome(update=True)
    await inter.followup.send(note, ephemeral=True)


@name_group.command(name="oeffnen", description="Beendete Abstimmung wieder öffnen (Gildenleitung)")
async def name_open_cmd(inter: discord.Interaction):
    if not is_admin(inter.user):
        await inter.response.send_message("Das dürfen nur der Gildenchef und die Offiziere.", ephemeral=True)
        return
    await inter.response.defer(ephemeral=True, thinking=True)
    p = name_poll()
    async with name_lock:
        p["closed"] = False
        p.pop("winner", None)
        state.save()
    for prop in name_ranking():
        await refresh_name_card(prop)
    await refresh_name_overview(repost=True)
    await inter.followup.send("🗳️ Die Abstimmung ist wieder offen.", ephemeral=True)


bot.tree.add_command(name_group)


# Der Gildenname steht fest: Abstimmung schliessen, Namen speichern, Willkommenstext und Servername anpassen.
# Läuft einmal beim Start (gemerkt in state "guild_name_applied"); danach ändert der Bot nichts mehr daran.
FIXED_GUILD_NAME = "Alpine Vanguard"


async def apply_fixed_guild_name() -> list[str]:
    done = []
    if state.data.get("guild_name_applied") == FIXED_GUILD_NAME:
        return done
    if cfg.get("guild_name") != FIXED_GUILD_NAME:
        cfg["guild_name"] = FIXED_GUILD_NAME
        save_config()
        done.append(f"Gildenname gespeichert: **{FIXED_GUILD_NAME}**")
    # Abstimmung schliessen, Gewinner = der festgelegte Name
    p = name_poll()
    if not p["closed"] or p.get("winner") != FIXED_GUILD_NAME:
        async with name_lock:
            p["closed"] = True
            p["winner"] = FIXED_GUILD_NAME
            state.save()
        for prop in name_ranking():
            await refresh_name_card(prop)
        await refresh_name_overview(repost=True)
        ch = await name_channel()
        if ch is not None:
            try:
                await ch.send(f"🏔️ **Die Abstimmung ist geschlossen.** Unsere Gilde heisst **{FIXED_GUILD_NAME}**! "
                              "Danke an alle fürs Vorschlagen und Abstimmen.", allowed_mentions=NO_PING)
            except discord.HTTPException as e:
                log.warning("Hinweis in #gildenname nicht gepostet: %s", e)
        done.append("Abstimmung in #gildenname geschlossen")
    # Willkommenstext mit dem neuen Namen
    try:
        res = await ensure_welcome(update=True)
        if res:
            done.append(res)
    except Exception:
        log.exception("Willkommenstext konnte nicht aktualisiert werden")
    # Servername
    guild = bot_guild()
    if guild is not None and guild.name != FIXED_GUILD_NAME:
        if guild.me.guild_permissions.manage_guild:
            try:
                await guild.edit(name=FIXED_GUILD_NAME, reason="Gildenname festgelegt")
                done.append(f"Servername geändert: **{FIXED_GUILD_NAME}**")
            except discord.HTTPException as e:
                done.append(f"Servername nicht geändert ({e})")
        else:
            done.append("Servername nicht geändert – dem Bot fehlt das Recht „Server verwalten“")
    state.data["guild_name_applied"] = FIXED_GUILD_NAME
    state.save()
    return done
