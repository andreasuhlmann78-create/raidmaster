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
    """Wohin mit einer Nachricht? "upload" = Daten aus #bot-daten, "ignore" = #testberichte und #sync-daten (nie
    auswerten, nie antworten), None = normale Behandlung."""
    if cfg.get("testberichte_channel_id") and int(channel_id) == int(cfg["testberichte_channel_id"]):
        return "ignore"
    if int(channel_id) in sync_channel_ids(cfg):
        return "ignore"
    if cfg.get("data_channel_id") and int(channel_id) == int(cfg["data_channel_id"]) and webhook_id:
        return "upload"
    return None



def market_source(cfg: dict, channel_id: int, webhook_id) -> bool:
    """MN7 (ab 1.5.131): Pakete des Uploaders in #testberichte dürfen auf GSMARKT1-Zeilen gelesen werden – still: nie
    antworten, nie löschen, sonst nichts auswerten. D-MN7c (1.5.132): nur der eigene Uploader-Webhook
    (testberichte_webhook_id, angelegt von /uploader), kein anderer Webhook, keine Personen, nie #sync-daten."""
    hook = cfg.get("testberichte_webhook_id")
    return bool(webhook_id and hook and cfg.get("testberichte_channel_id")
                and int(channel_id) == int(cfg["testberichte_channel_id"]) and int(webhook_id) == int(hook))


def tb_channel_id(cfg: dict) -> int | None:
    """Kanal-ID von #testberichte (für das Nachlesen der Marktdaten nach dem Start, D-MN7e) – oder None."""
    v = cfg.get("testberichte_channel_id")
    return int(v) if v else None

# ---------------------------------------------------------------------------
# Abgleich PC/Laptop (ab Bot 1.5.113, anweisung-uploader-sync-rechner.txt)
# Je Discord-Nutzer ein PRIVATER Kanal (#sync-daten, nur dieser Nutzer und der Bot), ein Webhook und eine
# Index-Nachricht. Der Uploader speichert dort seine Stände und liest sie über den Webhook zurück. Der Bot liest,
# beantwortet und löscht dort nichts; er legt nur an und schickt sync_config.json mit /uploader.
# cfg["sync"] = { "<user_id>": {"channel_id", "webhook_id", "index_id"} }
# ---------------------------------------------------------------------------
SYNC_CHANNEL = "sync-daten"
SYNC_HOOK = "GoldSentinel-Sync"
SYNC_TOPIC = "Abgleich deiner Addon-Daten zwischen deinen Rechnern (Uploader) – privat, bitte nichts löschen."
SYNC_INDEX_TEXT = 'GSSYNC-INDEX – nicht ändern\n{"v":1,"seq":0}'


def sync_channel_ids(cfg: dict) -> set[int]:
    out = set()
    for v in (cfg.get("sync") or {}).values():
        try:
            out.add(int(v.get("channel_id")))
        except (TypeError, ValueError, AttributeError):
            pass
    return out


async def setup_sync(guild, user, cfg: dict, reason: str = "/uploader"):
    """Privaten Kanal, Webhook und Index-Nachricht für `user` finden oder anlegen.
    Liefert (sync_config-Dict oder None, Hinweise)."""
    notes: list[str] = []
    entry = (cfg.setdefault("sync", {})).get(str(user.id)) or {}
    ch = None
    for c in guild.text_channels:
        if entry.get("channel_id") and c.id == int(entry["channel_id"]):
            ch = c
            break
    if ch is None:
        if not guild.me.guild_permissions.manage_channels:
            return None, ["Für den Abgleich PC/Laptop fehlt dem Bot das Recht **Kanäle verwalten** – der Daten-Upload "
                          "funktioniert trotzdem."]
        taken = {c.name for c in guild.text_channels}
        name, n = SYNC_CHANNEL, 2
        while name in taken:
            name, n = f"{SYNC_CHANNEL}-{n}", n + 1
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_webhooks=True,
                                                  read_message_history=True, attach_files=True),
            user: discord.PermissionOverwrite(view_channel=True, read_message_history=True, send_messages=False),
        }
        category = _find(guild.categories, OFFICER_CATEGORY)
        try:
            ch = await guild.create_text_channel(name, category=category, overwrites=overwrites, topic=SYNC_TOPIC,
                                                 reason=reason)
        except discord.HTTPException as e:
            return None, [f"Kanal für den Abgleich konnte nicht angelegt werden ({e}) – der Daten-Upload funktioniert trotzdem."]
        entry = {"channel_id": ch.id}
    if not ch.permissions_for(guild.me).manage_webhooks:
        return None, ["Im Abgleich-Kanal fehlt dem Bot das Recht **Webhooks verwalten**."]
    try:
        hook = await _hook(ch, SYNC_HOOK, reason)
    except discord.HTTPException as e:
        return None, [f"Webhook für den Abgleich nicht angelegt ({e})."]
    index_id = entry.get("index_id")
    if index_id and entry.get("webhook_id") == hook.id:
        try:
            await hook.fetch_message(int(index_id))
        except discord.HTTPException:
            index_id = None
    else:
        index_id = None
    if not index_id:
        try:
            msg = await hook.send(SYNC_INDEX_TEXT, wait=True, allowed_mentions=discord.AllowedMentions.none())
            index_id = msg.id
        except discord.HTTPException as e:
            return None, [f"Abgleich: Index-Nachricht nicht angelegt ({e})."]
    entry.update({"channel_id": ch.id, "webhook_id": hook.id, "index_id": index_id})
    cfg["sync"][str(user.id)] = entry
    return {"sync_webhook_url": hook.url, "sync_index_id": str(index_id)}, notes

