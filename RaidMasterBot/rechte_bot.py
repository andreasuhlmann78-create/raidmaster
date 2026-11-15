"""Rechte des Bots (D-3 Schritt 5, ab Bot 1.5.150): check_bot_rights – Server und Rechte beim Start und nach dem
Wiedereinladen prüfen, private Kanäle einmal ausdrücklich freigeben, Audit-Log zum Bot einmal melden (UP-404).

UNVERÄNDERT aus bot.py verschoben. Die reinen Regeln stehen in bot_rechte.py; hier nur das, was Discord braucht.
bot.py importiert dieses Modul erst NACH "grund.bot = bot" und übernimmt check_bot_rights mit Namen.
Weg A (Antwort der Prüf-Sitzung 15.11. 20:48).
"""
from __future__ import annotations

import discord

import bot_rechte
import grund
from grund import bot_guild, post_bot_log
from kern import cfg, log, state

bot = grund.bot
assert bot is not None, "rechte_bot erst nach grund.bot = bot importieren"


async def check_bot_rights(anlass: str) -> list:
    """UP-404 (b)(d), (a): Server und Rechte prüfen; Fehler immer ins Protokoll, Warnungen/Hinweise zusätzlich in
    den Bot-Kanal – nur wenn sie sich geändert haben (kein Lärm bei jedem Neustart). Einmal: Audit-Log zum Bot."""
    res = bot_rechte.start_check(bot.guilds, cfg.get("guild_id"), lambda g: g.me.guild_permissions)
    for level, text in res:
        (log.error if level == "fehler" else log.warning if level == "warnung" else log.info)("%s (%s)", text, anlass)
    if any(level == "fehler" for level, _ in res):
        return res
    key = "|".join(t for _, t in res)
    if key and state.data.get("rechte_meldung") != key:
        try:
            await post_bot_log("🔐 **Rechte des Bots** (" + anlass + "):\n" + "\n".join(f"• {t}" for _, t in res))
            state.data["rechte_meldung"] = key
            state.save()
        except Exception:  # noqa: BLE001
            log.exception("Rechte-Meldung nicht gepostet")
    elif not key and state.data.get("rechte_meldung"):
        state.data.pop("rechte_meldung", None)
        state.save()
    guild = bot_guild()
    if guild and not state.data.get("bot_private_granted") and guild.me.guild_permissions.administrator:
        # UP-404 (d): private Kanäle ausdrücklich für den Bot freigeben, damit "Administrator" danach weg kann
        done = []
        for ch in list(guild.categories) + [c for c in guild.channels if not isinstance(c, discord.CategoryChannel)]:
            if bot_rechte.needs_explicit(ch, guild.me, guild.default_role):
                try:
                    await ch.set_permissions(guild.me, reason="UP-404: ausdrückliche Freigabe für den Bot",
                                             **bot_rechte.BOT_ALLOW)
                    done.append(ch.name)
                except discord.HTTPException as e:
                    log.warning("Freigabe für %s nicht gesetzt: %s", ch.name, e)
        state.data["bot_private_granted"] = True
        state.save()
        log.info("UP-404: %d private Kanäle ausdrücklich für den Bot freigegeben", len(done))
        if done:
            await post_bot_log("🔐 Private Kanäle ausdrücklich für den Bot freigegeben (" + str(len(done)) + "): "
                               + ", ".join(done[:40]) + ". Jetzt kann „Administrator“ bei der Rolle des Bots aus.")
    if not state.data.get("audit_up404_done"):
        if guild and guild.me.guild_permissions.view_audit_log:
            try:
                entries = [e async for e in guild.audit_logs(limit=200)]
                lines = bot_rechte.audit_summary(entries, bot.user.id)
                await post_bot_log("🕵️ **Audit-Log zum Bot** (UP-404, einmalig):\n"
                                   + ("\n".join(f"• {x}" for x in lines[:15]) if lines else
                                      "• keine Einträge zum Bot in den letzten 200 Aktionen"))
                log.info("UP-404 Audit-Log: %d Einträge zum Bot", len(lines))
                state.data["audit_up404_done"] = True
                state.save()
            except discord.HTTPException as e:
                log.warning("Audit-Log nicht lesbar: %s", e)
    return res
