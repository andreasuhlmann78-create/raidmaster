"""Addon-Versionen und Ankündigungen (D-3 Schritt 18, ab Bot 1.5.164).

- Addon-Versionen: neue ZIP im Ordner "addon" -> passender Addon-Kanal (#raid-addon, GoldSentinel-Addons) und
  Nachricht an alle; ältere Versionen und englische Release-Notizen werden aufgeräumt; /addon, /addon-hochladen.
- Ankündigungen: Textdateien im Repo-Ordner "announce" werden je einmal gepostet, Versionsreihen ersetzen ältere
  Beiträge, Vorstellungen werden bearbeitet statt neu gepostet, gelöschte Ankündigungen werden entfernt.

UNVERÄNDERT aus bot.py verschoben (samt den Kommentaren direkt darüber): addon_version_key … addon_cmd ohne die
Kanal-Aufräumer (UNUSED_CHANNELS, clear_channels_once, remove_unused_channels_once – bleiben in bot.py, brauchen
dkp_channel_for). Die Merker _releases_cleaned, _announce_cleaned, _rm_cleaned (global) wandern mit allen
Funktionen, die sie setzen und lesen.
bot.py importiert dieses Modul nach "grund.bot = bot" (zwei Befehle werden beim Import angemeldet) und übernimmt
die Namen. Weg A (Antwort der Prüf-Sitzung 15.11. 20:48).
"""
from __future__ import annotations

import asyncio
import os
import re
import zipfile
import zlib

import discord
from discord import app_commands

import grund
import raidmaster_data as rmd
import server_setup
import updater
from bot_hilfen import _Msg, _norm_category, version_tuple, zip_addon_info
from grund import bot_guild, channel_by_id, is_admin, post_bot_log
from kern import ADDON_DIR, BASE, book, cfg, log, save_config, state

bot = grund.bot
assert bot is not None, "ankuendigung_bot erst nach grund.bot = bot importieren"


def addon_version_key(key: str, v: str) -> tuple:
    """Vergleichswert einer Addon-Version. AH Analyzer Pro wurde von 5.9.x auf 0.59.x
    umbenannt (5.9.13 -> 0.59.13): alte Nummern werden dafür umgerechnet, damit
    0.59.14 neuer ist als 5.9.12."""
    t = version_tuple(v)
    if key in ("ahanalyzerpro", "ahsentinel") and t and t[0] >= 1:
        return (0, t[0] * 10 + (t[1] if len(t) > 1 else 0)) + t[2:]
    return t


# Weitere Addons von GoldSentinel: Schlüssel = Name der TOC-Datei (klein, ohne _Vanilla usw.)
# old_keys/old_titles: frühere Namen (AH Analyzer Pro heißt seit 0.62.0 AHSentinel) - deren Beiträge
# gelten als ältere Versionen und werden beim Aufräumen mit gelöscht.
EXTRA_ADDONS = {
    # ab 1.5.98 in #ahsentinel (früher #aktionshaus – der Konfigurationsschlüssel heißt aus Kompatibilität weiter so)
    "ahsentinel": {"title": "AHSentinel", "folder": "AHSentinel", "channel": "aktionshaus_channel_id",
                   "channel_name": "ahsentinel", "old_keys": ["ahanalyzerpro"], "old_titles": ["AH Analyzer Pro"]},
}


async def extra_channel(meta: dict):
    """Kanal eines weiteren Addons. Zeigt die gespeicherte ID auf keinen Kanal mit passendem Namen (z. B. das alte
    #aktionshaus gibt es nicht mehr), wird der Kanal über Namen und Aliase gesucht und die ID umgestellt."""
    names = server_setup.channel_names(meta["channel_name"])
    ch = await channel_by_id(cfg.get(meta["channel"]))
    if ch is not None and getattr(ch, "name", None) == names[0]:
        return ch
    guild = bot_guild()
    found = server_setup.find_channel(guild.text_channels, meta["channel_name"]) if guild else None
    if found is None:
        return ch if ch is not None and getattr(ch, "name", None) in names else None
    if cfg.get(meta["channel"]) != found.id:
        log.info("%s: Kanal auf #%s umgestellt.", meta["title"], found.name)
        cfg[meta["channel"]] = found.id
        save_config()
    return found


def find_addon_package(key: str = "raidmaster") -> tuple[str, str] | None:
    """Neueste ZIP eines Addons im Ordner addon: (Pfad, Version aus der TOC)."""
    if not os.path.isdir(ADDON_DIR):
        return None
    best = None
    for fn in os.listdir(ADDON_DIR):
        if not fn.lower().endswith(".zip"):
            continue
        path = os.path.join(ADDON_DIR, fn)
        info = zip_addon_info(path)
        if not info or info[0] != key:
            continue
        if best is None or addon_version_key(key, info[2]) > addon_version_key(key, best[1]):
            best = (path, info[2])
    return best


def zip_changelog(path: str, key: str, since: str | None, upto: str, limit: int = 3500) -> str:
    """Changelog-Abschnitte aus der ZIP: alles nach Version `since` bis einschließlich `upto`."""
    try:
        with zipfile.ZipFile(path) as z:
            names = z.namelist()
            # Im Discord immer Deutsch: nur die deutsche Zusammenfassung (CHANGELOG.de.md) wird gepostet,
            # ein englischer CHANGELOG.md (für CurseForge) nie
            name = next((n for n in names if n.lower().endswith("/changelog.de.md") or n.lower() == "changelog.de.md"), None)
            if not name:
                return ""
            text = z.read(name).decode("utf-8", "replace")
    except (zipfile.BadZipFile, OSError, KeyError):
        return ""
    lo = addon_version_key(key, since) if since else None
    hi = addon_version_key(key, upto)
    out, keep = [], False
    for line in text.splitlines():
        m = re.match(r"^##\s+v?([\d.]+)", line)
        if m:
            v = addon_version_key(key, m.group(1))
            keep = v <= hi and (lo is None or v > lo)
            if keep:
                out.append(f"**{m.group(1)}**")
            continue
        if keep and not line.startswith(">"):        # Beta-Hinweis weglassen
            out.append(line)
    text = "\n".join(out).strip()
    text = re.sub(r"\n{3,}", "\n\n", text)
    if len(text) > limit:
        text = text[:limit].rsplit("\n", 1)[0] + "\n…"
    return text


_releases_cleaned = set()


async def remove_old_releases(ch, key: str, meta: dict, keep_version: str) -> int:
    """Im Kanal nur die neueste Version behalten: löscht eigene Nachrichten zu älteren Versionen.
    Erkannt werden Beiträge, die den Addon-Namen mit einer älteren Versionsnummer nennen
    (Versions-Posts, Zusammenfassungen) und deren direkte Fortsetzungen (innerhalb von 60 s, ohne Namen)."""
    keep = addon_version_key(key, keep_version)
    pat = re.compile(re.escape(meta["title"]) + r"\D{0,40}?v?(\d+(?:\.\d+)+)")
    old_pats = [re.compile(re.escape(t) + r"\D{0,40}?v?(\d+(?:\.\d+)+)") for t in meta.get("old_titles", [])]
    try:
        hist = [m async for m in ch.history(limit=500)]
    except discord.HTTPException as e:
        log.warning("Verlauf von #%s nicht lesbar: %s", meta["channel_name"], e)
        return 0
    hist.sort(key=lambda m: m.created_at)
    # Beiträge aus announce/ (z. B. die Vorstellung) gehören nicht zu den Versions-Posts: nie anfassen. Bis 1.5.97
    # konnte eine Vorstellung, die kurz nach einer alten Version gepostet wurde, als deren "Fortsetzung" gelöscht werden.
    announced_ids = {int(mid) for r in (state.data.get("announce_msgs") or {}).values() for mid in r.get("ids") or []}
    removed, last_old = 0, None
    for m in hist:
        if m.author != bot.user or m.id in announced_ids:
            last_old = None
            continue
        text = m.content or ""
        for e in m.embeds:
            text += "\n" + (e.title or "")
        first = pat.search(text)
        old = False
        if first:
            old = addon_version_key(key, first.group(1)) < keep
        elif any(p.search(text) for p in old_pats):
            old = True                                   # Beitrag unter dem früheren Namen
        elif last_old is not None and (m.created_at - last_old).total_seconds() <= 60:
            old = True                                   # Fortsetzung einer alten Ankündigung
        if old:
            try:
                await m.delete()
                removed += 1
            except discord.NotFound:
                pass
            except discord.HTTPException as e:
                log.warning("Alte Version (Nachricht %s) nicht gelöscht: %s", m.id, e)
            last_old = m.created_at
        else:
            last_old = None
    if removed:
        log.info("#%s: %d Nachricht(en) zu älteren %s-Versionen gelöscht (nur %s bleibt).",
                 meta["channel_name"], removed, meta["title"], keep_version)
    return removed


async def remove_english_release_notes():
    """Einmalig: englische Changelogs ("– what's new") aus früheren Versions-Beiträgen entfernen.
    Text und Download-Datei bleiben, nur der englische Kasten verschwindet (im Discord alles auf Deutsch)."""
    if state.data.get("english_notes_removed"):
        return
    for meta in EXTRA_ADDONS.values():
        ch = await extra_channel(meta)
        if not ch:
            continue
        try:
            async for m in ch.history(limit=200):
                if m.author.id == bot.user.id and any("what's new" in (e.title or "") for e in m.embeds):
                    await m.edit(embeds=[])
                    await asyncio.sleep(0.5)
        except discord.HTTPException as e:
            log.info("Englische Changelogs in #%s nicht entfernt: %s", meta["channel_name"], e)
            return
    state.data["english_notes_removed"] = True
    state.save()


async def check_extra_releases():
    """Neue Versionen der weiteren Addons (z. B. AHSentinel) in ihrem Kanal posten.
    Ältere Versionen werden danach aus dem Kanal gelöscht - es bleibt immer nur die neueste."""
    try:
        await remove_english_release_notes()
    except Exception as e:  # noqa: BLE001 – Aufräumen darf das Posten nie stören
        log.warning("Englische Changelogs nicht entfernt: %s", e)
    versions = state.data.setdefault("extra_versions", {})
    for key, meta in EXTRA_ADDONS.items():
        # umbenanntes Addon: zuletzt gepostete Version unter dem alten Schlüssel übernehmen
        if not versions.get(key):
            for ok in meta.get("old_keys", []):
                if versions.get(ok):
                    versions[key] = versions[ok]
                    state.save()
                    break
        pkg = find_addon_package(key)
        if not pkg:
            continue
        path, version = pkg
        # einmal nach dem Start: Kanal aufräumen (auch Beiträge älterer Bot-Versionen)
        if key not in _releases_cleaned and versions.get(key):
            ch0 = await extra_channel(meta)
            if ch0:
                _releases_cleaned.add(key)
                try:
                    await remove_old_releases(ch0, key, meta, versions[key])
                except Exception as e:
                    log.warning("Aufräumen von #%s fehlgeschlagen: %s", meta["channel_name"], e)
        if addon_version_key(key, version) <= addon_version_key(key, versions.get(key) or "0"):
            continue
        ch = await extra_channel(meta)
        if not ch:
            log.info("%s %s gefunden, aber Kanal #%s fehlt.", meta["title"], version, meta["channel_name"])
            continue
        notes = zip_changelog(path, key, versions.get(key), version)
        embed = None
        if notes:
            embed = discord.Embed(title=f"{meta['title']} {version} – das ist neu", description=notes, color=0xFFD100)
        await ch.send(
            f"🆕 **{meta['title']} {version}** ist da!\n"
            f"Download: Datei unten herunterladen, entpacken und den Ordner **{meta['folder']}** in "
            "`Interface/AddOns` ersetzen. Deine Einstellungen bleiben erhalten."
            + (f"\nℹ️ Früher **{meta['old_titles'][0]}** – die ZIP enthält beide Ordner, deine Daten werden "
               "beim ersten Start automatisch übernommen." if meta.get("old_titles") else ""),
            embed=embed,
            file=discord.File(path, filename=f"{meta['folder']}-{version}.zip"))
        versions[key] = version
        state.save()
        log.info("%s %s in #%s veröffentlicht.", meta["title"], version, meta["channel_name"])
        try:
            await remove_old_releases(ch, key, meta, version)
        except Exception as e:
            log.warning("Aufräumen von #%s fehlgeschlagen: %s", meta["channel_name"], e)


# Ankündigungen: Textdateien im Repo-Ordner "announce" werden je einmal gepostet.
# Dateiname: <kanal>-<irgendwas>.md, z. B. aktionshaus-0.59.22.md oder raid-addon-info.md
# Für beliebige Kanäle (z. B. andere Projekte): <kanalname>__<titel>.md, z. B. projekte__version-1.2.md
# -> Kanal mit genau diesem Namen. Anhänge: Dateien mit demselben Namen und anderer Endung
# (projekte__version-1.2.png, ….zip, ….pdf) kommen an die erste Nachricht (je höchstens 10 MB).
# Enthält der Titel eine Versionsnummer (…-1.3.md), ersetzt eine neuere Version die ältere: deren
# Nachrichten werden nach dem Posten gelöscht.
ANNOUNCE_DIR = os.path.join(BASE, "announce")
# "aktionshaus-…" (ohne "__") wird ab 1.5.98 nicht mehr gepostet: #aktionshaus gibt es nicht mehr, AHSentinel steht in #ahsentinel
ANNOUNCE_CHANNELS = {"raid-addon": "addon_channel_id"}
ANNOUNCE_ATTACH = (".png", ".jpg", ".jpeg", ".gif", ".zip", ".pdf", ".txt")
# Versionsreihen: <kanal>__<name>-<version>… (z. B. levelpilot__levelpilot-3.3.0.md). Kommt eine neuere
# Version derselben Reihe, löscht der Bot die Nachrichten der älteren (samt Anhängen).
# Reihen/Fassungen und Teilung: EIN Ort für Bot und Discord-Prüfung (D-CHK1, ab 1.5.194) – announce_reihe.py
from announce_reihe import ANNOUNCE_VER, aeltere, announce_series, fassung, old_split, split_parts  # noqa: E402,F401


# Reihen, deren Beitrag bei einer neuen Fassung BEARBEITET wird (statt gelöscht und neu gepostet):
# Vorstellungen, Funktionsübersichten, Hilfen. Nur die Nachrichten, deren Text sich geändert hat,
# werden bearbeitet; kommt ein Teil dazu, wird er angehängt, fällt einer weg, wird er gelöscht.
ANNOUNCE_EDIT_WORDS = ("vorstellung", "funktionen", "uebersicht", "hilfe")


def announce_editable(series: str) -> bool:
    s_ = (series or "").lower()
    return any(w in s_ for w in ANNOUNCE_EDIT_WORDS)


async def edit_announcement(ch, series: str, ver: tuple, parts: list):
    """Beitrag einer älteren Fassung derselben Reihe in diesem Kanal bearbeiten.
    Rückgabe: (alter Dateiname, Nachrichten-IDs, Anzahl geänderter Nachrichten) oder None (dann normal posten)."""
    rec = state.data.setdefault("announce_msgs", {})
    prev = None
    for fn, r in rec.items():
        if r.get("series") == series and r.get("ch") == ch.id and tuple(r.get("ver") or ()) < ver and r.get("ids") \
                and not r.get("attach"):
            if prev is None or tuple(r.get("ver")) > tuple(prev[1].get("ver")):
                prev = (fn, r)
    if not prev:
        return None
    old_fn, r = prev
    msgs = []
    for mid in r["ids"]:
        try:
            msgs.append(await ch.fetch_message(mid))
        except (discord.NotFound, discord.HTTPException):
            return None                 # Beitrag fehlt (z. B. von Hand gelöscht): neu posten
    am = discord.AllowedMentions(users=True, roles=False, everyone=False)
    ids, changed = [], 0
    for i, part in enumerate(parts or [""]):
        text = part[:2000]
        if i < len(msgs):
            if (msgs[i].content or "") != text:
                await msgs[i].edit(content=text, allowed_mentions=am)
                changed += 1
            ids.append(msgs[i].id)
        else:
            m = await ch.send(text, allowed_mentions=am)
            ids.append(m.id)
            changed += 1
    for m in msgs[len(parts or [""]):]:
        try:
            await m.delete()
            changed += 1
        except discord.HTTPException:
            pass
    return old_fn, ids, changed


async def remove_old_announcements(ch, series: str, ver: tuple, keep_fn: str):
    """Löscht die Nachrichten älterer Versionen derselben Reihe. Liefert die Anzahl gelöschter Nachrichten."""
    rec = state.data.setdefault("announce_msgs", {})
    removed = 0

    async def delete(msg):
        nonlocal removed
        try:
            await msg.delete()
            removed += 1
        except discord.NotFound:
            pass
        except discord.HTTPException as e:
            log.warning("Alte Ankündigung %s nicht gelöscht: %s", msg.id, e)

    # 1) gespeicherte Nachrichten (ab Bot 1.5.51)
    for fn, r in list(rec.items()):
        if fn == keep_fn or r.get("series") != series or tuple(r.get("ver") or ()) >= ver:
            continue
        c = ch if r.get("ch") == ch.id else await channel_by_id(r.get("ch"))
        for mid in r.get("ids", []):
            try:
                await delete(await c.fetch_message(mid))
            except discord.NotFound:
                pass
            except (discord.HTTPException, AttributeError) as e:
                log.warning("Alte Ankündigung %s nicht gefunden: %s", mid, e)
        rec.pop(fn, None)
    # 2) ältere Beiträge ohne gespeicherte Nachrichten (vor Bot 1.5.51): im Kanalverlauf an den Anhängen erkennen,
    #    dazu die direkt folgenden Fortsetzungen derselben Ankündigung (ohne Anhang, innerhalb von 20 Sekunden)
    known = {mid for r in rec.values() for mid in r.get("ids", [])}
    try:
        hist = [m async for m in ch.history(limit=100)]
    except discord.HTTPException:
        hist = []
    hist.sort(key=lambda m: m.created_at)
    i = 0
    while i < len(hist):
        m = hist[i]
        old = False
        if m.author == bot.user and m.id not in known:
            for a in m.attachments:
                s_, v_ = announce_series(a.filename)
                if s_ == series and v_ and v_ < ver:
                    old = True
        if not old:
            i += 1
            continue
        await delete(m)
        j = i + 1
        while j < len(hist) and hist[j].author == bot.user and not hist[j].attachments and hist[j].id not in known \
                and (hist[j].created_at - m.created_at).total_seconds() <= 20:
            await delete(hist[j])
            j += 1
        i = j
    state.save()
    return removed


# Kanäle, die der Bot für Ankündigungen selbst anlegt (Kanalname -> Kategorie und Thema).
# Der Kanal übernimmt die Rechte der Kategorie.
ANNOUNCE_AUTO_CHANNELS = {
    "buffsentinel": {
        "category": "Addon's by GoldSentinel",
        "topic": "BuffSentinel – Buff-Erinnerungen, Proc-Buttons und Cooldowns für alle WoW-Versionen",
    },
    "threatsentinel": {
        "category": "Addon's by GoldSentinel",
        "topic": "ThreatSentinel – hilft Tanks, die Aggro zu halten (WoW Forever)",
    },
    "guildsentinel": {
        "category": "Addon's by GoldSentinel",
        "topic": "GuildSentinel – Gildentool: Mitglieder, Gruppensuche, Leveling-Rennen, Raid-Zugänge, Rekrutierung (WoW Forever)",
    },
    "ahsentinel": {
        "category": "Addon's by GoldSentinel",
        "topic": "AHSentinel – Auktionshaus-Addon: Preise, Schnäppchen, Sniper, Verkaufen, Buchhaltung (WoW Forever und alle WoW-Versionen)",
    },
    "professionsentinel": {
        "category": "Addon's by GoldSentinel",
        "topic": "ProfessionSentinel – Rezept-Bibliothek: alle Rezepte von Lehrern, Händlern und Drops, gelernt/fehlend je Beruf (WoW Forever)",
    },
    "lore": {
        "category": "📌 INFO",
        "topic": "Die Geschichte der Alpine Vanguard – Wächter der Pässe im Alteracgebirge (Horde, WoW Forever)",
    },
}


async def ensure_announce_channel(guild, name: str):
    """Legt einen Ankündigungskanal aus ANNOUNCE_AUTO_CHANNELS an (samt Kategorie, falls sie fehlt)."""
    spec = ANNOUNCE_AUTO_CHANNELS.get(name)
    if not spec or guild is None or not guild.me.guild_permissions.manage_channels:
        return None
    want = _norm_category(spec["category"])
    cat = next((c for c in guild.categories if _norm_category(c.name) == want), None)
    try:
        if cat is None:
            cat_def = next((c for c in server_setup.BASE_TOP if _norm_category(c["name"]) == want), None)
            overwrites = None
            if cat_def:
                overwrites = server_setup._overwrites(cat_def.get("mode"), guild, server_setup._known_roles(guild))
            cat = await guild.create_category(spec["category"], overwrites=overwrites or {},
                                              reason="RaidMaster-Bot: Kategorie für Addon-Ankündigungen")
        ch = await guild.create_text_channel(name, category=cat, topic=spec.get("topic"),
                                             reason="RaidMaster-Bot: Kanal für Addon-Ankündigungen")
    except discord.HTTPException as e:
        log.warning("Ankündigungskanal #%s konnte nicht angelegt werden: %s", name, e)
        return None
    log.info("Ankündigungskanal #%s in %s angelegt.", name, cat.name)
    await post_bot_log(f"🆕 Kanal **#{name}** in **{cat.name}** angelegt (für Addon-Ankündigungen).")
    return ch


async def announce_target(fn: str):
    """Zielkanal einer Ankündigungsdatei (None = noch nicht möglich)."""
    low = fn.lower()
    if "__" in low:
        name = low.split("__", 1)[0].lstrip("#")
        guild = bot_guild()
        ch = discord.utils.get(guild.text_channels, name=name) if guild else None
        if ch is None and name in ANNOUNCE_AUTO_CHANNELS:
            ch = await ensure_announce_channel(guild, name)
        if ch is None:
            warned = state.data.setdefault("announce_warned", [])
            if fn not in warned:
                warned.append(fn)
                state.save()
                await post_bot_log(f"📣 Ankündigung **{fn}** wartet: Den Kanal **#{name}** gibt es nicht – bitte anlegen "
                                   "(der Bot braucht dort Schreibrechte), dann wird sie automatisch gepostet.")
        return ch
    chan_key = next((v for k, v in ANNOUNCE_CHANNELS.items() if low.startswith(k + "-")), None)
    return await channel_by_id(cfg.get(chan_key)) if chan_key else None


_announce_cleaned = False


async def cleanup_announcements_once():
    """Einmal nach dem Start: je Versionsreihe die älteren Beiträge löschen (auch solche von älteren Bot-Versionen)."""
    global _announce_cleaned
    if _announce_cleaned:
        return
    _announce_cleaned = True
    newest = {}
    for fn in state.data.get("announced", []):
        series, ver = announce_series(fn)
        if series and (series not in newest or ver > newest[series][1]):
            newest[series] = (fn, ver)
    for series, (fn, ver) in newest.items():
        try:
            ch = await announce_target(fn)
            if ch:
                n = await remove_old_announcements(ch, series, ver, fn)
                if n:
                    log.info("Aufgeräumt: %d Nachricht(en) älterer Versionen vor %s gelöscht.", n, fn)
        except Exception as e:
            log.warning("Aufräumen der Ankündigungen (%s) fehlgeschlagen: %s", series, e)


def _find_member_by_names(guild, names: list[str]):
    """Mitglied zu einem der Namen (Discord-Name, Anzeigename, Spitzname oder registrierter Charakter)."""
    for alt in names:
        a = alt.strip().casefold()
        if not a:
            continue
        uid = book.user_for_char(alt.strip())
        if uid:
            m = guild.get_member(int(uid))
            if m:
                return m
        for m in guild.members:
            for cand in (getattr(m, "nick", None), getattr(m, "global_name", None), m.display_name, m.name):
                c = str(cand or "").strip().casefold()
                if c and (c == a or c.split(" ")[0] == a):
                    return m
    return None


async def resolve_announce_text(text: str) -> tuple[str, list[str]]:
    """Platzhalter in Ankündigungen: {@Name} oder {@Name1/Name2} = Mitglied anpingen, {#kanal} = Link zum Kanal.
    Liefert (Text, nicht gefundene Namen/Kanäle)."""
    guild = bot_guild()
    missing: list[str] = []

    def user(m_):
        raw = m_.group(1)
        mem = _find_member_by_names(guild, raw.split("/")) if guild else None
        if mem:
            return mem.mention
        missing.append("@" + raw)
        return "**@" + raw.split("/")[0].strip() + "**"

    def chan(m_):
        name = m_.group(1).strip().lstrip("#").lower()
        c = server_setup.find_channel(guild.text_channels, name) if guild else None
        if c:
            return c.mention
        missing.append("#" + name)
        return "**#" + name + "**"

    text = re.sub(r"\{@([^{}]+)\}", user, text)
    text = re.sub(r"\{#([^{}]+)\}", chan, text)
    return text, missing


ANNOUNCE_REMOVED_DIR = os.path.join(BASE, updater.ANNOUNCE_REMOVED_DIR)


def _announce_channel_quiet(fn: str):
    """Kanal einer Ankündigung, ohne ihn anzulegen und ohne Meldung (zum Aufräumen)."""
    guild = bot_guild()
    if guild is None:
        return None
    low = fn.lower()
    if "__" in low:
        return discord.utils.get(guild.text_channels, name=low.split("__", 1)[0].lstrip("#"))
    chan_key = next((v for k, v in ANNOUNCE_CHANNELS.items() if low.startswith(k + "-")), None)
    return guild.get_channel(int(cfg.get(chan_key) or 0)) if chan_key else None


async def remove_deleted_announcements():
    """Ankündigungen, deren Datei im Repo gelöscht wurde: Der Updater legt sie bei einem GitHub-Update nach
    announce_entfernt/. Hier löscht der Bot seine Beiträge dazu im Discord (nur eigene Nachrichten) und danach
    die Datei. Schutz: Haben mehr als announce_delete_max (Standard 5) davon noch Beiträge im Discord -> nichts
    löschen, nur melden. Ältere, längst ersetzte Fassungen einer Reihe zählen nicht mit (ab Bot 1.5.101)."""
    if not os.path.isdir(ANNOUNCE_REMOVED_DIR):
        return
    files = sorted(fn for fn in os.listdir(ANNOUNCE_REMOVED_DIR)
                   if fn.lower().endswith(".md") and os.path.isfile(os.path.join(ANNOUNCE_REMOVED_DIR, fn)))
    # ab 1.5.191 (Entscheid des Nutzers 23.11. 11:36/11:45: gelöschte Ankündigungen im Repo wiederherstellen): Liegt eine Datei
    # wieder in announce/, ist sie zurück – ihre Kopie in announce_entfernt/ weg, Beiträge und "announced" bleiben (kein Löschen,
    # kein neues Posten).
    back = [fn for fn in files if os.path.isfile(os.path.join(ANNOUNCE_DIR, fn))]
    for fn in back:
        stem = fn[:-3]
        for x in os.listdir(ANNOUNCE_REMOVED_DIR):
            if x == fn or x.startswith(stem + "."):
                try:
                    os.remove(os.path.join(ANNOUNCE_REMOVED_DIR, x))
                except OSError:
                    pass
    if back:
        log.info("Wiederhergestellte Ankündigungen: %d (Beiträge bleiben)", len(back))
        files = [fn for fn in files if fn not in back]
        if state.data.get("announce_delete_warned"):
            state.data.pop("announce_delete_warned", None)
            state.save()
    if not files or bot_guild() is None:
        return
    # ab 1.5.192 (D-ANN1 a, Entscheid des Nutzers 23.11. 11:36): Der Bot löscht im Discord NIE mehr Beiträge, nur weil ihre Datei
    # im Repo fehlt. Er meldet jede solche Datei EINMAL in #bot-log; Beiträge, "announced" und gespeicherte Nachrichten bleiben
    # (so kann die Datei später wiederhergestellt werden, ohne neu gepostet zu werden). announce_delete_max gilt nicht mehr.
    reported = state.data.setdefault("announce_removed_reported", [])
    new = [fn for fn in files if fn not in reported]
    reported[:] = [fn for fn in reported if fn in files] + new      # Merker nur für Dateien, die noch fehlen
    if not new:
        if state.data.pop("announce_delete_warned", None) is not None:
            state.save()
        return
    live = set(updater.announce_live(new, state.data.get("announced") or [], state.data.get("announce_msgs") or {},
                                     announce_series))
    state.data.pop("announce_delete_warned", None)
    state.save()
    await post_bot_log(f"ℹ️ **{len(new)} Ankündigung{'en' if len(new) != 1 else ''}** im Repo gelöscht – ich lösche im Discord "
                       "NICHTS (Entscheid 23.11.). Ihre Beiträge bleiben stehen; wieder in announce/ = wiederhergestellt:\n"
                       + "\n".join(f"• `{fn}`" + (" – Beitrag steht noch" if fn in live else "") for fn in new))


async def check_announcements():
    if not os.path.isdir(ANNOUNCE_DIR):
        return
    done = state.data.setdefault("announced", [])
    await cleanup_announcements_once()
    try:
        await remove_deleted_announcements()
    except Exception as e:      # Aufräumen darf das Posten nie stören
        log.warning("Entfernte Ankündigungen nicht aufgeräumt: %s", e)
    # ab 1.5.192 (D-ANN2, Entscheid des Nutzers 23.11. 12:03 "alte Addon-Versionen auf keinen Fall wieder posten"): neueste
    # schon gepostete Version je Reihe; eine ältere oder gleiche Version wird nie gepostet, auch wenn ihre Datei neu auftaucht.
    # ab 1.5.194 (D-CHK1): Reihe/Fassung auch ohne Punkt-Version (…-0-vorstellung-19.md, announce_reihe.fassung), und eine Datei,
    # neben der eine neuere Fassung derselben Reihe liegt, wird nie gepostet (am 24.11. 10:31 postete der Bot nach dem Update
    # 1.5.193 die alten GuildSentinel-Vorstellungen -10 bis -18 kurz neu, jede durch die nächste ersetzt).
    newest = {}
    for fn0 in done:
        s0, v0 = fassung(fn0)
        if s0 and (s0 not in newest or v0 > newest[s0]):
            newest[s0] = v0
    listing = sorted(os.listdir(ANNOUNCE_DIR))
    older = aeltere([x for x in listing if x.lower().endswith(".md")])
    skipped = state.data.setdefault("announce_old_skipped", [])
    skip_lines = []
    for fn in listing:
        if not fn.lower().endswith(".md") or fn in done:
            continue
        s1, v1 = fassung(fn)
        why = ""
        if s1 and s1 in newest and v1 <= newest[s1]:
            why = (f"Fassung {'.'.join(map(str, v1))} ist nicht neuer als die schon gepostete "
                   f"{'.'.join(map(str, newest[s1]))}")
        elif fn in older and announce_series(fn)[0] is None:   # Fassung ohne Punkt-Version (…-vorstellung-N.md)
            why = f"ältere Fassung, neueste ist `{older[fn]}`"
        if why:
            if fn not in skipped:
                skipped.append(fn)
                skip_lines.append(f"• `{fn}`: {why}")
            continue
        ch = await announce_target(fn)
        if not ch:
            continue
        try:
            with open(os.path.join(ANNOUNCE_DIR, fn), "r", encoding="utf-8") as f:
                text = f.read().strip()
        except OSError:
            continue
        text, missing = await resolve_announce_text(text)
        if missing:
            await post_bot_log(f"📣 Ankündigung **{fn}**: nicht gefunden – " + ", ".join(missing) + " (ohne Ping gepostet).")
        # Discord: höchstens 2000 Zeichen pro Nachricht - an Absätzen teilen, zu lange Absätze an Zeilen (ab 1.5.194)
        parts = split_parts(text)
        stem = fn[:-3]
        attach = [os.path.join(ANNOUNCE_DIR, x) for x in sorted(os.listdir(ANNOUNCE_DIR))
                  if x.startswith(stem + ".") and x.lower().endswith(ANNOUNCE_ATTACH)
                  and os.path.getsize(os.path.join(ANNOUNCE_DIR, x)) <= 10 * 1024 * 1024][:10]
        # Vorstellung / Übersicht / Hilfe: vorhandenen Beitrag bearbeiten statt neu posten
        series, ver = announce_series(fn)
        if series and announce_editable(series) and not attach:
            try:
                res = await edit_announcement(ch, series, ver, parts)
            except discord.HTTPException as e:
                log.warning("Ankündigung %s nicht bearbeitet: %s", fn, e)
                res = None
            if res:
                old_fn, ids, changed = res
                rec = state.data.setdefault("announce_msgs", {})
                rec.pop(old_fn, None)
                rec[fn] = {"ch": ch.id, "ids": ids, "series": series, "ver": list(ver)}
                done.append(fn)
                if series not in newest or ver > newest[series]:
                    newest[series] = ver
                state.save()
                log.info("Ankündigung %s: Beitrag von %s bearbeitet (%d Nachricht(en) geändert).", fn, old_fn, changed)
                continue
        sent = []
        try:
            for i, p in enumerate(parts or [""]):
                if i == 0 and attach:
                    msg = await ch.send(p[:2000] or None, files=[discord.File(x) for x in attach],
                                        allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False))
                else:
                    msg = await ch.send(p[:2000], allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False))
                sent.append(msg.id)
        except discord.HTTPException as e:
            log.warning("Ankündigung %s nicht gepostet: %s", fn, e)
            continue
        done.append(fn)
        if series and (series not in newest or ver > newest[series]):
            newest[series] = ver
        # ab Bot 1.5.95 auch ohne Versionsnummer speichern: so kann der Bot den Beitrag wieder löschen,
        # wenn die Datei aus announce/ entfernt wird (remove_deleted_announcements)
        state.data.setdefault("announce_msgs", {})[fn] = {"ch": ch.id, "ids": sent, "series": series,
                                                          "ver": list(ver) if ver else None,
                                                          "attach": bool(attach) or None}
        state.save()
        log.info("Ankündigung %s gepostet.", fn)
        # neuere Version derselben Reihe: alte Beiträge entfernen
        if series:
            try:
                n = await remove_old_announcements(ch, series, ver, fn)
                if n:
                    log.info("Ankündigung %s: %d Nachricht(en) älterer Versionen gelöscht.", fn, n)
            except Exception as e:      # Aufräumen darf das Posten nie stören
                log.warning("Alte Versionen zu %s nicht gelöscht: %s", fn, e)
        # gleicher Titel (erste Zeile) wie ein älterer Bot-Beitrag im Kanal: der ältere wird ersetzt
        try:
            title = (parts[0] if parts else "").split("\n", 1)[0].strip()
            n = await remove_same_title(ch, title, sent)
            if n:
                log.info("Ankündigung %s: %d Nachricht(en) mit gleichem Titel ersetzt.", fn, n)
        except Exception as e:
            log.warning("Ältere Beiträge mit gleichem Titel zu %s nicht gelöscht: %s", fn, e)
    if skip_lines:                   # ab 1.5.194: eine Meldung für alle (einmal je Datei), nicht eine je Datei
        state.save()
        await post_bot_log("⏭️ Ankündigungen NICHT gepostet (Entscheid 23.11.: alte Fassungen nie wieder posten):\n"
                           + "\n".join(skip_lines))


async def repair_truncated_announcements() -> list[str]:
    """Einmal je Bot-Version (ab 1.5.194, D-CHK1): Bis 1.5.193 wurde ein Absatz über 2000 Zeichen beim Posten/Bearbeiten
    abgeschnitten (belegt: LevelPilot-Übersicht ab 3.12.58, in 3.12.94 fehlten 3 Zeilen im Discord). Für die NEUESTE Fassung
    jeder Reihe, deren Beitrag so abgeschnitten wurde, werden die eigenen Nachrichten mit der neuen Teilung bearbeitet und
    fehlende Teile angehängt. Nichts wird gelöscht, ältere Fassungen werden nie angefasst. Liefert Meldungen für #bot-log."""
    marker = "announce_truncfix_" + updater.bot_version(BASE)
    if state.data.get(marker) or not os.path.isdir(ANNOUNCE_DIR):
        return []
    present = [x for x in os.listdir(ANNOUNCE_DIR) if x.lower().endswith(".md")]
    older = aeltere(present)
    rec = state.data.setdefault("announce_msgs", {})
    notes = []
    am = discord.AllowedMentions.none()          # Nachbesserung: niemanden erneut anpingen
    for fn, r in list(rec.items()):
        if fn not in present or fn in older or r.get("attach") or not r.get("ids") or not r.get("ch"):
            continue
        try:
            with open(os.path.join(ANNOUNCE_DIR, fn), "r", encoding="utf-8") as f:
                raw = f.read().strip()
        except OSError:
            continue
        text, _missing = await resolve_announce_text(raw)
        if not any(len(p) > 2000 for p in old_split(text)):
            continue
        ch = await channel_by_id(r["ch"])
        if ch is None:
            continue
        msgs = []
        try:
            for mid in r["ids"]:
                msgs.append(await ch.fetch_message(int(mid)))
        except discord.HTTPException:
            notes.append(f"⚠️ Ankündigung `{fn}`: abgeschnitten, aber ein Teil fehlt im Discord – nicht bearbeitet.")
            continue
        parts = split_parts(text)
        ids, edited, added = [], 0, 0
        for i, part in enumerate(parts):
            if i < len(msgs):
                if (msgs[i].content or "") != part:
                    await msgs[i].edit(content=part, allowed_mentions=am)
                    edited += 1
                ids.append(msgs[i].id)
            else:
                m = await ch.send(part, allowed_mentions=am)
                ids.append(m.id)
                added += 1
        ids += [m.id for m in msgs[len(parts):]]          # nie löschen: überzählige Nachrichten bleiben verbunden
        r["ids"] = ids
        if edited or added:
            notes.append(f"✏️ Ankündigung `{fn}`: abgeschnittener Text vervollständigt ({edited} Nachricht(en) bearbeitet, "
                         f"{added} angehängt).")
            log.info("Ankündigung %s: abgeschnittenen Text vervollständigt (%d bearbeitet, %d angehängt)", fn, edited, added)
    state.data[marker] = True
    state.save()
    return notes


async def remove_same_title(ch, title: str, keep_ids: list) -> int:
    """Löscht ältere Bot-Beiträge im Kanal, deren erste Zeile `title` ist – samt ihren direkten
    Fortsetzungen (Bot-Nachrichten ohne Anhang innerhalb von 20 Sekunden). So ersetzt z. B. eine
    überarbeitete Vorstellung die alte."""
    if not title or len(title) < 8:
        return 0
    try:
        hist = [m async for m in ch.history(limit=100)]
    except discord.HTTPException:
        return 0
    hist.sort(key=lambda m: m.created_at)
    keep = set(keep_ids)
    removed, i = 0, 0
    while i < len(hist):
        m = hist[i]
        if m.author != bot.user or m.id in keep or (m.content or "").split("\n", 1)[0].strip() != title:
            i += 1
            continue
        group = [m]
        j = i + 1
        while j < len(hist) and hist[j].author == bot.user and not hist[j].attachments and hist[j].id not in keep \
                and (hist[j].created_at - m.created_at).total_seconds() <= 20:
            group.append(hist[j])
            j += 1
        for g in group:
            try:
                await g.delete()
                removed += 1
            except discord.NotFound:
                pass
            except discord.HTTPException as e:
                log.warning("Alter Beitrag %s nicht gelöscht: %s", g.id, e)
        i = j
    return removed


RM_RELEASE_FILE = re.compile(r"^RaidMaster-v?(\d+(?:\.\d+)+)\.zip$", re.I)
RM_RELEASE_HEAD = re.compile(r"^\W{0,6}\**\s*(?:Neue\s+)?RaidMaster(?:-Version)?\s+v?(\d+(?:\.\d+)+)", re.I)
_rm_cleaned = False


async def remove_old_raidmaster_versions(ch, keep_version: str) -> int:
    """#raid-addon: nur die aktuelle RaidMaster-Version behalten. Gelöscht werden eigene Beiträge mit einer
    älteren Addon-ZIP (RaidMaster-x.y.z.zip) oder die mit "RaidMaster x.y.z" beginnen (Versions-Posts,
    Zusammenfassungen), dazu ihre direkten Fortsetzungen (innerhalb von 60 s). Andere Beiträge
    (Uploader, Hilfe-Texte) bleiben stehen."""
    keep = version_tuple(keep_version)
    try:
        hist = [m async for m in ch.history(limit=500)]
    except discord.HTTPException as e:
        log.warning("Verlauf von #raid-addon nicht lesbar: %s", e)
        return 0
    hist.sort(key=lambda m: m.created_at)
    removed, last_old = 0, None
    for m in hist:
        if m.author != bot.user:
            last_old = None
            continue
        ver = None
        for a in m.attachments:
            hit = RM_RELEASE_FILE.match(a.filename or "")
            if hit:
                ver = hit.group(1)
                break
        if ver is None:
            hit = RM_RELEASE_HEAD.match(m.content or "")
            ver = hit.group(1) if hit else None
        if ver is not None:
            old = version_tuple(ver) < keep
        else:
            old = last_old is not None and not m.attachments and (m.created_at - last_old).total_seconds() <= 60
        if old:
            try:
                await m.delete()
                removed += 1
            except discord.NotFound:
                pass
            except discord.HTTPException as e:
                log.warning("Alte RaidMaster-Version (Nachricht %s) nicht gelöscht: %s", m.id, e)
            last_old = m.created_at
            await asyncio.sleep(0.4)
        else:
            last_old = None
    if removed:
        log.info("#raid-addon: %d Nachricht(en) zu älteren RaidMaster-Versionen gelöscht (nur %s bleibt).", removed, keep_version)
    return removed


ADDON_INTRO = os.path.join(BASE, "raid_addon_intro.md")


def addon_intro_posts(version: str) -> list[str]:
    """Vorstellung + Updates aus raid_addon_intro.md (Nachrichten durch "===" getrennt, //-Zeilen weggelassen)."""
    try:
        with open(ADDON_INTRO, "r", encoding="utf-8") as f:
            raw = f.read()
    except OSError:
        return []
    lines = [l for l in raw.splitlines() if not l.startswith("//")]
    posts = []
    for part in "\n".join(lines).split("\n===\n"):
        part = part.strip().replace("{version}", version)
        if part:
            posts.extend(rmd.split_discord(part))
    return posts


def _is_rm_post(m) -> bool:
    """Eigener Beitrag in #raid-addon zu RaidMaster: Vorstellung, Updates, Versions-Post oder alte Zusammenfassung."""
    text = m.content or ""
    if text.startswith(("🛡️ **RaidMaster", "📜 **Updates**")):
        return True
    if any(RM_RELEASE_FILE.match(a.filename or "") for a in m.attachments):
        return True
    return bool(RM_RELEASE_HEAD.match(text))


async def ensure_addon_intro(ch, path: str, version: str) -> bool:
    """#raid-addon: Vorstellung (mit der aktuellen Addon-ZIP) und Updates. Liefert True, wenn die Version gewechselt hat
    (bearbeitet oder neu gepostet).
    DC-ANN1 (ab 1.5.201, Supervisor 27.11. 10:45): Die Ankündigung einer RaidMaster-Version kommt NUR über announce/
    (raid-addon__raidmaster-<Version>…). Wechselt die stabile Version in download/, wird die vorhandene Vorstellung BEARBEITET
    (Text und ZIP am ersten Beitrag ersetzt) – kein zweiter Beitrag, nichts gelöscht. Neu gepostet wird nur, wenn es noch
    keine Vorstellung gibt oder sie nicht bearbeitet werden kann (z. B. andere Zahl von Teilen)."""
    posts = addon_intro_posts(version)
    if not posts:
        return False
    digest = str(zlib.crc32(("\n".join(posts)).encode("utf-8")))
    rec = state.data.get("addon_intro") or {}
    same_place = rec.get("ch") == ch.id and rec.get("version") == version and rec.get("ids")
    if same_place and rec.get("hash") == digest:
        return False
    if same_place and len(rec["ids"]) == len(posts):
        # nur der Text hat sich geändert: Beiträge bearbeiten (die Datei bleibt dran)
        try:
            for mid, text in zip(rec["ids"], posts):
                await ch.get_partial_message(mid).edit(content=text)
                await asyncio.sleep(0.4)
            rec["hash"] = digest
            state.data["addon_intro"] = rec
            state.save()
            return False
        except discord.HTTPException as e:
            log.info("Vorstellung nicht bearbeitet (%s) – wird neu gepostet.", e)
    elif (rec.get("ch") == ch.id and rec.get("ids") and rec.get("version") != version
          and len(rec["ids"]) == len(posts)):
        # DC-ANN1: neue stabile Version -> Vorstellung bearbeiten und die ZIP am ersten Beitrag ersetzen (kein neuer Beitrag)
        try:
            for i, (mid, text) in enumerate(zip(rec["ids"], posts)):
                if i == 0:
                    await ch.get_partial_message(mid).edit(
                        content=text, attachments=[discord.File(path, filename=f"RaidMaster-{version}.zip")])
                else:
                    await ch.get_partial_message(mid).edit(content=text)
                await asyncio.sleep(0.4)
            state.data["addon_intro"] = {"ch": ch.id, "ids": list(rec["ids"]), "hash": digest, "version": version}
            state.save()
            log.info("#raid-addon: Vorstellung auf RaidMaster %s bearbeitet (ZIP ersetzt, kein neuer Beitrag).", version)
            return True
        except discord.HTTPException as e:
            log.info("Vorstellung nicht bearbeitet (%s) – wird neu gepostet.", e)
    old_ids = set(rec.get("ids") or []) if rec.get("ch") == ch.id else set()
    ids = []
    first = await ch.send(posts[0], file=discord.File(path, filename=f"RaidMaster-{version}.zip"))
    ids.append(first.id)
    for text in posts[1:]:
        m = await ch.send(text)
        ids.append(m.id)
        await asyncio.sleep(0.4)
    state.data["addon_intro"] = {"ch": ch.id, "ids": ids, "hash": digest, "version": version}
    state.data["addon_message"] = first.jump_url
    state.save()
    # alte Vorstellung, alte Versions-Posts und Zusammenfassungen entfernen
    removed = 0
    # DC-ANN1 (ab 1.5.201): Ankündigungen aus announce/ (auch raid-addon__raidmaster-…) nie mitlöschen
    protected = {int(x) for r in (state.data.get("announce_msgs") or {}).values() for x in (r.get("ids") or [])}
    try:
        async for m in ch.history(limit=500):
            if (m.author == bot.user and m.id not in ids and m.id not in protected
                    and (m.id in old_ids or _is_rm_post(m))):
                try:
                    await m.delete()
                    removed += 1
                except discord.HTTPException:
                    pass
                await asyncio.sleep(0.4)
    except discord.HTTPException as e:
        log.warning("Alte Beiträge in #raid-addon nicht entfernt: %s", e)
    log.info("#raid-addon: Vorstellung RaidMaster %s gepostet, %d alte Beiträge entfernt.", version, removed)
    return True


async def tidy_addon_channels() -> list[str]:
    """Addon-Kanäle (Kategorie "Addon's by GoldSentinel"): von den Update-Texten nur den neuesten je Addon stehen lassen
    (ab Bot 1.5.104). Nachrichten mit Datei, Vorstellungen, Übersichten, Hilfen und Beiträge anderer bleiben.
    Die Dateien in announce/ bleiben unberührt; gelöschte Beiträge gelten weiter als gepostet (kein Neuposten)."""
    guild = bot_guild()
    if guild is None or bot.user is None:
        return []
    want = _norm_category(server_setup.ADDON_CATEGORY)
    cat = next((c for c in guild.categories if _norm_category(c.name) == want), None)
    if cat is None:
        return []
    rec = state.data.setdefault("announce_msgs", {})
    # Beiträge aus announce/, die keine Update-Texte sind (Vorstellung, Übersicht, Hilfe, ohne Versionsnummer): schützen
    protected = {int(i) for r in rec.values() if not r.get("series") or announce_editable(r.get("series"))
                 for i in r.get("ids") or []}
    report = []
    for ch in cat.text_channels:
        if not ch.permissions_for(guild.me).read_message_history:
            continue
        try:
            hist = [_Msg(m) async for m in ch.history(limit=300)]
        except discord.HTTPException as e:
            log.warning("#%s nicht lesbar: %s", ch.name, e)
            continue
        deleted = set()
        for mid in server_setup.plan_update_cleanup(hist, bot.user.id, protected):
            try:
                await ch.get_partial_message(mid).delete()
                deleted.add(mid)
                await asyncio.sleep(0.4)
            except discord.NotFound:
                deleted.add(mid)
            except discord.HTTPException as e:
                log.warning("Alter Update-Text %s in #%s nicht gelöscht: %s", mid, ch.name, e)
        if deleted:
            # gespeicherte Beiträge dazu vergessen (bleiben in "announced": werden nicht neu gepostet)
            for fn, r in list(rec.items()):
                if any(int(i) in deleted for i in r.get("ids") or []):
                    rec.pop(fn, None)
            state.save()
            report.append(f"#{ch.name}: {len(deleted)}")
    return report


async def check_addon_release():
    global _rm_cleaned
    await check_extra_releases()
    await check_announcements()
    try:
        rep = await tidy_addon_channels()
        if rep:
            log.info("Alte Update-Texte gelöscht: %s", ", ".join(rep))
            await post_bot_log("🧹 Alte Update-Texte gelöscht (nur der neueste je Addon bleibt, Dateien bleiben): "
                               + ", ".join(rep))
    except Exception:  # noqa: BLE001 – Aufräumen darf das Veröffentlichen nie stören
        log.exception("Addon-Kanäle konnten nicht aufgeräumt werden")
    pkg = find_addon_package("raidmaster")
    if not pkg:
        return
    path, version = pkg
    ch = await channel_by_id(cfg.get("addon_channel_id"))
    new_version = version_tuple(version) > version_tuple(state.data.get("addon_version") or "0")
    if not ch:
        if new_version:
            log.info("Neue Addon-Version %s gefunden, aber kein Kanal #raid-addon eingetragen (/raidmaster-einrichten).", version)
        return
    if os.path.isfile(ADDON_INTRO):
        posted = await ensure_addon_intro(ch, path, version)
        if not new_version:
            return
        if not posted:
            return
    else:
        if not new_version:
            if not _rm_cleaned and state.data.get("addon_version"):
                _rm_cleaned = True
                try:
                    await remove_old_raidmaster_versions(ch, state.data["addon_version"])
                except Exception as e:  # noqa: BLE001 – Aufräumen darf nichts anderes stören
                    log.warning("Aufräumen von #raid-addon fehlgeschlagen: %s", e)
            return
        msg = await ch.send(
            f"🆕 **RaidMaster {version}** ist da!\n"
            "Download: Datei unten herunterladen, entpacken und den Ordner **RaidMaster** in "
            "`Interface/AddOns` ersetzen. Deine Einstellungen und DKP bleiben erhalten.",
            file=discord.File(path, filename=f"RaidMaster-{version}.zip"))
        state.data["addon_message"] = msg.jump_url
        _rm_cleaned = True
        try:
            await remove_old_raidmaster_versions(ch, version)
        except Exception as e:  # noqa: BLE001
            log.warning("Aufräumen von #raid-addon fehlgeschlagen: %s", e)
    state.data["addon_version"] = version
    state.save()
    log.info("Addon %s in #raid-addon veröffentlicht.", version)
    if cfg.get("notify_addon_updates", True):
        await notify_registered(
            f"🆕 **Neue RaidMaster-Version {version}** – bitte das Addon aktualisieren!\n"
            f"Download in **#raid-addon**: {state.data.get('addon_message')}")


ADDON_PN_AUS = "addon_pn_aus"      # ab 1.5.198: Mitglieder, die keine PN "Neue RaidMaster-Version" wollen (/addon-pn)


def addon_pn_off(uid) -> bool:
    return str(uid) in (state.data.get(ADDON_PN_AUS) or [])


async def notify_registered(text: str):
    """Allen registrierten Spielern (Charakter im Bot hinterlegt) eine Direktnachricht schicken – ausser wer sie mit
    /addon-pn ausgeschaltet hat (ab 1.5.198, Wunsch des Nutzers 26.11. 12:59)."""
    sent = failed = skipped = 0
    for uid in list(book.profiles.data.keys()):
        if addon_pn_off(uid):
            skipped += 1
            continue
        try:
            user = bot.get_user(int(uid)) or await bot.fetch_user(int(uid))
            await user.send(text)
            sent += 1
        except discord.HTTPException:
            failed += 1
        await asyncio.sleep(1)
    log.info("Benachrichtigung an %d Spieler verschickt (%d ohne Direktnachrichten, %d ausgeschaltet).", sent, failed, skipped)


@bot.tree.command(name="addon-hochladen", description="Neue Addon-Version (ZIP) hochladen – wird im passenden Kanal veröffentlicht (Gildenleitung)")
@app_commands.describe(datei="Addon-ZIP, z. B. AHSentinel-0.62.0.zip oder RaidMaster-1.6.0.zip")
async def addon_upload_cmd(inter: discord.Interaction, datei: discord.Attachment):
    if not is_admin(inter.user):
        await inter.response.send_message("Das dürfen nur der Gildenchef und die Offiziere.", ephemeral=True)
        return
    if not datei.filename.lower().endswith(".zip") or datei.size > 25 * 1024 * 1024:
        await inter.response.send_message("Bitte eine Addon-ZIP (max. 25 MB) anhängen.", ephemeral=True)
        return
    await inter.response.defer(ephemeral=True, thinking=True)
    os.makedirs(ADDON_DIR, exist_ok=True)
    tmp = os.path.join(ADDON_DIR, "upload.tmp")
    with open(tmp, "wb") as f:
        f.write(await datei.read())
    info = zip_addon_info(tmp)
    if not info or (info[0] != "raidmaster" and info[0] not in EXTRA_ADDONS):
        os.remove(tmp)
        known = ", ".join(["RaidMaster"] + [m["title"] for m in EXTRA_ADDONS.values()])
        await inter.followup.send(f"In der ZIP wurde keine bekannte Addon-TOC mit Version gefunden (bekannt: {known}).", ephemeral=True)
        return
    key, folder, version = info
    target = os.path.join(ADDON_DIR, f"{folder}-{version}.zip")
    os.replace(tmp, target)
    log.info("Addon-ZIP hochgeladen: %s %s von %s", folder, version, inter.user)
    await check_addon_release()
    where = "#raid-addon" if key == "raidmaster" else "#" + EXTRA_ADDONS[key]["channel_name"]
    await inter.followup.send(f"✅ **{folder} {version}** gespeichert – wird in **{where}** veröffentlicht "
                              "(falls die Version neuer ist als die zuletzt gepostete).", ephemeral=True)


@bot.tree.command(name="addon", description="Link zur aktuellen RaidMaster-Addon-Version")
async def addon_cmd(inter: discord.Interaction):
    v = state.data.get("addon_version")
    if not v:
        await inter.response.send_message("Es wurde noch keine Addon-Version veröffentlicht.", ephemeral=True)
        return
    await inter.response.send_message(f"Aktuelle Version: **RaidMaster {v}** – Download: {state.data.get('addon_message')}", ephemeral=True)


@bot.tree.command(name="addon-pn", description="PN bei neuer RaidMaster-Version für dich ein- oder ausschalten")
@app_commands.describe(an="Ein (Standard) oder aus")
async def addon_pn_cmd(inter: discord.Interaction, an: bool):
    """Ab 1.5.198: jedes Mitglied für sich selbst. Gemerkt in state.json "addon_pn_aus" (nur IDs, nichts im Repo)."""
    off = state.data.setdefault(ADDON_PN_AUS, [])
    uid = str(inter.user.id)
    if an and uid in off:
        off.remove(uid)
    elif not an and uid not in off:
        off.append(uid)
    state.save()
    await inter.response.send_message(
        "✅ Du bekommst bei einer neuen RaidMaster-Version wieder eine PN." if an else
        "🔕 Du bekommst bei einer neuen RaidMaster-Version keine PN mehr. Die Ankündigung in **#raid-addon** bleibt; "
        "einschalten mit `/addon-pn an:True`.", ephemeral=True)
