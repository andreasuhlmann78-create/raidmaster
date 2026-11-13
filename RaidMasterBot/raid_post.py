"""Neuen Raid posten (ab Bot 1.5.126, aus bot.py raid_create herausgelöst für den Funktionstest T-R1).

Befund R1 (12.11.2026): Scheitert das Posten (z. B. fehlendes Recht), darf kein Raid ohne Nachricht im Buch bleiben,
und der Ersteller bekommt eine klare Meldung. Erfolgsfall: message_id setzen, speichern, "Raid erstellt in #…".
"""
from __future__ import annotations

import logging

import discord

log = logging.getLogger("raidmaster")


def fail_text(target, status) -> str:
    return (f"⚠️ Ich konnte den Raid nicht in {target.mention} posten ({status}). Mir fehlt dort wohl das Recht "
            "**Nachrichten senden** oder **Links einbetten**. Der Raid wurde nicht angelegt.")


async def post_new_raid(book, raid: dict, target, embed, view, reply):
    """reply(text) = ephemere Antwort an den Ersteller (async). Liefert die Nachricht oder None (gescheitert)."""
    try:
        msg = await target.send(embed=embed, view=view)
    except discord.HTTPException as e:
        book.raids.data["raids"].pop(str(raid["id"]), None)
        book.save()
        log.warning("Raid nicht gepostet in #%s: %s", getattr(target, "name", "?"), e)
        await reply(fail_text(target, getattr(e, "status", "?")))
        return None
    raid["message_id"] = msg.id
    book.save()
    await reply(f"Raid erstellt in {target.mention}.")
    return msg
