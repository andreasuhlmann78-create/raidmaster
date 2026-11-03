"""Einrichtung des Uploaders (/uploader): zwei Webhooks.

- #bot-daten: Webhook "RaidMaster-Uploader" für die Spieldaten (wie bisher; seine ID steht in cfg["uploader_webhooks"]).
- #testberichte (Kategorie 🔒 OFFIZIERE, nur Bot und Admins sehen ihn): Webhook "GoldSentinel-Testberichte" für die
  Testberichte der GoldSentinel-Addons. Der Bot wertet sie NICHT aus, antwortet dort nicht und löscht dort nichts –
  die Addon-Prüfung (GitHub-Workflow testberichte.yml) liest die letzten 500 Nachrichten.

Die Funktionen bekommen Discord-Objekte übergeben und lassen sich offline mit Attrappen testen
(tests/test_testberichte.py).
"""
from __future__ import annotations

import discord

import server_setup

DATA_HOOK = "RaidMaster-Uploader"
TEST_CHANNEL = "testberichte"
TEST_HOOK = "GoldSentinel-Testberichte"
TEST_TOPIC = "Testberichte der GoldSentinel-Addons (Uploader) – liest die Addon-Prüfung. Bitte nichts löschen."
OFFICER_CATEGORY = "🔒 OFFIZIERE"


def _find(items, name):
    for x in items or []:
        if getattr(x, "name", None) == name:
            return x
    return None


async def _hook(channel, name: str, reason: str):
    for wh in await channel.webhooks():
        if wh.name == name and getattr(wh, "token", None):
            return wh
    return await channel.create_webhook(name=name, reason=reason)


async def ensure_test_channel(guild, reason: str = "Testberichte"):
    """#testberichte finden oder anlegen (OFFIZIERE, "hidden"). Liefert (Kanal oder None, Hinweis oder None)."""
    ch = _find(guild.text_channels, TEST_CHANNEL)
    if ch is not None:
        return ch, None
    if not guild.me.guild_permissions.manage_channels:
        return None, ("Für **#testberichte** fehlt dem Bot das Recht **Kanäle verwalten** – Testberichte bleiben aus, "
                      "der Daten-Upload funktioniert trotzdem.")
    category = _find(guild.categories, OFFICER_CATEGORY)
    overwrites = server_setup._overwrites("hidden", guild, server_setup._known_roles(guild))
    try:
        ch = await guild.create_text_channel(TEST_CHANNEL, category=category, overwrites=overwrites,
                                             topic=TEST_TOPIC, reason=reason)
    except discord.HTTPException as e:
        return None, f"**#testberichte** konnte nicht angelegt werden ({e}) – der Daten-Upload funktioniert trotzdem."
    return ch, None


async def setup_uploader_hooks(guild, data_channel, cfg: dict, reason: str = "/uploader"):
    """Webhooks für den Uploader. Liefert (data_url, test_url oder None, Hinweise).
    cfg: uploader_webhooks (nur Daten-Webhook), testberichte_channel_id, testberichte_webhook_id."""
    notes: list[str] = []
    data_hook = await _hook(data_channel, DATA_HOOK, reason)
    ids = [int(x) for x in cfg.get("uploader_webhooks") or []]
    if data_hook.id not in ids:
        ids.append(data_hook.id)
    cfg["uploader_webhooks"] = ids
    test_url = None
    ch, note = await ensure_test_channel(guild, reason)
    if note:
        notes.append(note)
    if ch is not None:
        if not ch.permissions_for(guild.me).manage_webhooks:
            notes.append("In **#testberichte** fehlt dem Bot das Recht **Webhooks verwalten** – Testberichte bleiben aus, "
                         "der Daten-Upload funktioniert trotzdem.")
        else:
            try:
                th = await _hook(ch, TEST_HOOK, reason)
                test_url = th.url
                cfg["testberichte_channel_id"] = ch.id
                cfg["testberichte_webhook_id"] = th.id
            except discord.HTTPException as e:
                notes.append(f"Webhook in **#testberichte** nicht angelegt ({e}) – der Daten-Upload funktioniert trotzdem.")
    return data_hook.url, test_url, notes


def uploader_config(data_url: str, test_url: str | None, bot_id: int) -> dict:
    conf = {"webhook_url": data_url}
    if test_url:
        conf["test_webhook_url"] = test_url
    conf.update({"bot_id": bot_id, "savedvariables_path": "", "check_seconds": 10})
    return conf


def route_message(cfg: dict, channel_id: int, webhook_id) -> str | None:
    """Wohin mit einer Nachricht? "upload" = Daten aus #bot-daten, "ignore" = #testberichte (nie auswerten,
    nie antworten, nie löschen), None = normale Behandlung."""
    if cfg.get("testberichte_channel_id") and int(channel_id) == int(cfg["testberichte_channel_id"]):
        return "ignore"
    if cfg.get("data_channel_id") and int(channel_id) == int(cfg["data_channel_id"]) and webhook_id:
        return "upload"
    return None
