"""bot.py für Ablauf-Tests laden (D-T1, ab Bot 1.5.132).

bot.py liest beim Import config.json neben sich und legt data/ an. Damit im Repo nichts entsteht, wird der Bot in einen
temporären Ordner kopiert (nur .py, .json, .json.gz und VERSION) und dort mit einer Attrappen-config.json geladen
(Token "test-token", keine echten IDs). Netz wird nicht benutzt: es wird nichts gestartet, nur Funktionen aufgerufen.
Der Ordner wird am Ende des Testlaufs gelöscht.
"""
from __future__ import annotations

import atexit
import importlib.util
import json
import os
import shutil
import sys
import tempfile
import types

BOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_cache: dict = {}


def load_bot():
    """Gibt (bot-Modul, temporärer Ordner) zurück; einmal je Testlauf geladen."""
    if "bot" in _cache:
        return _cache["bot"], _cache["dir"]
    tmp = tempfile.mkdtemp(prefix="rmbot-test-")
    atexit.register(shutil.rmtree, tmp, True)
    for name in os.listdir(BOT_DIR):
        src = os.path.join(BOT_DIR, name)
        if os.path.isfile(src) and (name.endswith((".py", ".json", ".json.gz")) or name == "VERSION") \
                and name != "config.json":
            shutil.copy(src, os.path.join(tmp, name))
    with open(os.path.join(BOT_DIR, "config.example.json"), encoding="utf-8") as f:
        conf = json.load(f)
    conf["token"] = "test-token"
    with open(os.path.join(tmp, "config.json"), "w", encoding="utf-8") as f:
        json.dump(conf, f)
    if tmp not in sys.path:
        sys.path.append(tmp)                     # Module des Bots: gleiche Fassung wie im Repo
    if BOT_DIR not in sys.path:
        sys.path.insert(0, BOT_DIR)
    argv = sys.argv
    sys.argv = ["bot.py"]
    try:
        spec = importlib.util.spec_from_file_location("bot_under_test", os.path.join(tmp, "bot.py"))
        mod = importlib.util.module_from_spec(spec)
        sys.modules["bot_under_test"] = mod
        spec.loader.exec_module(mod)
    finally:
        sys.argv = argv
    _cache["bot"], _cache["dir"] = mod, tmp
    return mod, tmp


class FakeAttachment:
    def __init__(self, filename: str, data: bytes = b"", size: int | None = None):
        self.filename = filename
        self._data = data
        self.size = len(data) if size is None else size
        self.reads = 0

    async def read(self):
        self.reads += 1
        return self._data


class FakeMessage:
    def __init__(self, attachments=(), webhook_id=None, content="", channel_id=1, author_id=99):
        self.attachments = list(attachments)
        self.webhook_id = webhook_id
        self.content = content
        self.channel = types.SimpleNamespace(id=channel_id)
        self.author = types.SimpleNamespace(id=author_id, bot=webhook_id is not None)
        self.deleted = False

    async def delete(self):
        self.deleted = True


class FakeChannel:
    def __init__(self, cid=1, history=()):
        self.id = cid
        self._history = list(history)
        self.sent = []

    async def send(self, content=None, **kw):
        self.sent.append((content, kw))
        return types.SimpleNamespace(id=len(self.sent))

    def history(self, limit=100, after=None, oldest_first=None):
        msgs = self._history[:limit]

        async def gen():
            for m in msgs:
                yield m
        return gen()
