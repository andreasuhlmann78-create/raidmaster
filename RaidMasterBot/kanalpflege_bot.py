"""Kanalpflege (D-3 Schritt 30, ab Bot 1.5.177): feste Bot-Texte in Kanälen aktuell halten, Sprachkanal-Grenzen,
Raid-Kategorien (gelistete und neue), Sichtbarkeit der Raid-Kanäle, einmalige Aufräumer (CLEAR_CHANNELS_ONCE,
nicht mehr gebrauchte Kanäle – nur wenn darin ausschliesslich Bot-Beiträge stehen).

UNVERÄNDERT aus bot.py verschoben (samt Kommentaren direkt darüber): _keep_text, ensure_channel_texts,
ensure_voice_limits, ensure_listed_raid_categories, sync_raid_visibility, ensure_new_raid_categories,
UNUSED_CHANNELS, clear_channels_once, remove_unused_channels_once. Verhalten unverändert (auch: einmalig, mit
Merker im state). bot.py importiert dieses Modul nach "grund.bot = bot" und übernimmt die Namen, die RaidBot und
die Uploads brauchen. Weg A (Antwort der Prüf-Sitzung 15.11. 20:48).
"""
from __future__ import annotations

import asyncio
import zlib
from datetime import datetime
from zoneinfo import ZoneInfo

import discord

import grund
import raidmaster_data as rmd
import server_setup
from bot_hilfen import _config_ids
from dkp_tafel_bot import dkp_channel_for
from grund import NO_PING, bot_guild, channel_by_id
from kern import cfg, log, save_config, state

bot = grund.bot
assert bot is not None, "kanalpflege_bot erst nach grund.bot = bot importieren"


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
