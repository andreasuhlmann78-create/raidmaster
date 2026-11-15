"""Testdaten (D-3 Schritt 26, ab Bot 1.5.173): Testnachrichten senden und zum Löschen vormerken (TEST_TTL, 10
Minuten; übersteht auch einen Neustart) – gebraucht von DKP-Tabellen, Lootlisten und Test-Uploads.

UNVERÄNDERT aus bot.py verschoben: TEST_TTL, send_test. Weg A (Antwort der Prüf-Sitzung 15.11. 20:48).
"""
from __future__ import annotations

import time

import raidmaster_data as rmd
from bot_hilfen import table_file
from kern import state


TEST_TTL = 600


async def send_test(channel, text: str | None, embeds: list | None = None,
                    file_bytes: bytes | None = None, filename: str = "bild.png", view=None):
    """Testnachricht senden und zum Löschen vormerken (übersteht auch einen Neustart des Bots).
    Zu lange Texte werden in Discord-taugliche Stücke geteilt (max. 2000 Zeichen)."""
    if file_bytes:
        m = await channel.send(content=text or None, file=table_file(file_bytes, filename))
        state.data.setdefault("test_messages", []).append([channel.id, m.id, int(time.time()) + TEST_TTL])
    elif view is not None:
        m = await channel.send(content=text or None, view=view)
        state.data.setdefault("test_messages", []).append([channel.id, m.id, int(time.time()) + TEST_TTL])
    elif embeds:
        m = await channel.send(content=text or None, embeds=embeds)
        state.data.setdefault("test_messages", []).append([channel.id, m.id, int(time.time()) + TEST_TTL])
    else:
        for part in rmd.split_discord(text or ""):
            m = await channel.send(part)
            state.data.setdefault("test_messages", []).append([channel.id, m.id, int(time.time()) + TEST_TTL])
    state.save()
