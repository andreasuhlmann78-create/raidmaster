"""#testberichte aufräumen (ab Bot 1.5.111, anweisung-uploader-nur-neues.txt Punkt 5).

Die Abholung (GitHub-Workflow, addon-check/testberichte.py) schreibt nach jedem Lauf die IDs der Discord-Nachrichten,
die sie verarbeitet hat, nach testberichte/abgeholt.json ({"ids": [...]}) im öffentlichen Repo. Der Bot liest diese
Datei alle 30 Minuten und löscht in #testberichte NUR Nachrichten,
- deren ID in dieser Liste steht und
- die älter als 1 Stunde sind.
Nie in anderen Kanälen (die Nachricht wird nur im Kanal #testberichte angesprochen; eine fremde ID ergibt dort
"nicht gefunden"). Sonst liest, beantwortet und postet der Bot in #testberichte weiterhin nichts.
Braucht dort das Recht "Nachrichten verwalten" (fehlt es, gibt es einen Hinweis und es wird nichts gelöscht).

Offline testbar mit Attrappen (tests/test_tb_aufraeumen.py).
"""
from __future__ import annotations

import json
import re
import time

import discord

CHANNEL = "testberichte"
MIN_AGE = 3600                   # erst löschen, wenn die Nachricht älter als 1 Stunde ist
MAX_PER_RUN = 100                # je Durchgang höchstens so viele (Rate-Grenzen von Discord)
DONE_MAX = 3000                  # so viele erledigte IDs merken (nicht nochmals versuchen)
DISCORD_EPOCH_MS = 1420070400000
SNOWFLAKE = re.compile(r"^\d{15,21}$")


def raw_url(repo: str) -> str:
    """repo = "besitzer/name" (config update_repo). HEAD = Standard-Zweig."""
    return f"https://raw.githubusercontent.com/{repo}/HEAD/testberichte/abgeholt.json"


def parse_ids(text: str) -> list[str]:
    """{"ids": [...]} -> nur gültige Discord-IDs (Ziffern). Alles andere wird ignoriert."""
    try:
        data = json.loads(text)
    except ValueError:
        return []
    ids = data.get("ids") if isinstance(data, dict) else None
    return [str(i) for i in ids or [] if SNOWFLAKE.match(str(i))]


def created_at(msg_id: str) -> float:
    return ((int(msg_id) >> 22) + DISCORD_EPOCH_MS) / 1000.0


def find_channel(guild):
    """Nur der Kanal, der genau #testberichte heisst – keine Ersatznamen."""
    for ch in getattr(guild, "text_channels", None) or []:
        if getattr(ch, "name", None) == CHANNEL:
            return ch
    return None


async def cleanup(guild, ids: list[str], done: list[str], now: float | None = None) -> tuple[int, str | None]:
    """Abgeholte Nachrichten in #testberichte löschen. done = schon erledigte IDs (wird ergänzt).
    Rückgabe: (gelöscht, Hinweis oder None)."""
    now = time.time() if now is None else now
    ch = find_channel(guild)
    if ch is None or not ids:
        return 0, None
    if not ch.permissions_for(guild.me).manage_messages:
        return 0, ("In **#testberichte** fehlt dem Bot das Recht **Nachrichten verwalten** – abgeholte Testberichte "
                   "bleiben stehen (nur für diesen Kanal einschalten).")
    seen = set(done)
    deleted, tried = 0, 0
    for msg_id in ids:
        if msg_id in seen or now - created_at(msg_id) < MIN_AGE:
            continue
        if tried >= MAX_PER_RUN:
            break
        tried += 1
        try:
            await ch.get_partial_message(int(msg_id)).delete()
            deleted += 1
            done.append(msg_id)
        except discord.NotFound:
            done.append(msg_id)          # schon weg (oder nicht in diesem Kanal): nie wieder versuchen
        except discord.Forbidden:
            return deleted, "In **#testberichte** darf der Bot keine Nachrichten löschen (Recht **Nachrichten verwalten**)."
        except discord.HTTPException:
            break                         # später erneut
        seen.add(msg_id)
    del done[:-DONE_MAX]
    return deleted, None
