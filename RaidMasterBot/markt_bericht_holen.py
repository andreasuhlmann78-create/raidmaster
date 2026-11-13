#!/usr/bin/env python3
"""MN7: Wochenberichte der Marktdaten-Sammelstelle ins Repo holen (GitHub-Workflow markt-bericht.yml, ab Bot 1.5.131).

Der Bot legt montags den Bericht als Anhang GSMARKTW1-<JJJJ>-W<KW>.md in den Bot-Kanal (#bot-befehle), bei einer
Änderung der Blizzard-Realm-Listen (MN8 monatlich) zusätzlich GSBLIZZ1-<JJJJ-MM-TT>.txt. Dieses Skript liest die
Zwischenberichte (/marktdaten bericht:True) heissen GSMARKTW1-<JJJJ>-W<KW>-zwischen-<MMTT-HHMM>.md und
landen unter eigenem Namen. Das Skript liest die letzten Nachrichten des Kanals (nur Nachrichten des Bots selbst), lädt diese Anhänge und speichert sie unter
testberichte/markt/<JJJJ>-W<KW>.md bzw. testberichte/markt/blizzard-<JJJJ-MM-TT>.txt. Keine Namen (die Berichte
enthalten keine), nur feste Dateinamen, nur cdn.discordapp.com, höchstens 1 MB je Datei.

Braucht DISCORD_BOT_TOKEN (Secret) und DISCORD_GUILD_ID (Variable), wie testberichte.yml.
"""
import os
import re
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "testberichte" / "markt"
API = "https://discord.com/api/v10"
CHANNELS = [c.strip() for c in os.environ.get("MARKT_KANAELE", "bot-befehle").split(",") if c.strip()]
NAMES = (re.compile(r"^GSMARKTW1-(\d{4}-W\d{2}(?:-zwischen-\d{4}-\d{4})?)\.md$"), re.compile(r"^GSBLIZZ1-(\d{4}-\d{2}-\d{2})\.txt$"))
MAX = 1024 * 1024
HISTORY = 300


def target(filename: str):
    m = NAMES[0].match(filename or "")
    if m:
        return OUT / f"{m.group(1)}.md"
    m = NAMES[1].match(filename or "")
    if m:
        return OUT / f"blizzard-{m.group(1)}.txt"
    return None


def main() -> int:
    tok = os.environ.get("DISCORD_BOT_TOKEN")
    if not tok:
        print("DISCORD_BOT_TOKEN fehlt – nichts zu tun.")
        return 0
    s = requests.Session()
    s.headers["Authorization"] = "Bot " + tok

    def get(path, **params):
        r = s.get(API + path, params=params, timeout=30)
        r.raise_for_status()
        return r.json()

    me = get("/users/@me")["id"]
    guilds = get("/users/@me/guilds")
    want = os.environ.get("DISCORD_GUILD_ID")
    guild = next((g for g in guilds if g["id"] == want), None) if want else (guilds[0] if guilds else None)
    if not guild:
        print("Server nicht gefunden.")
        return 1
    chans = [c for c in get(f"/guilds/{guild['id']}/channels") if c.get("type") == 0 and c.get("name") in CHANNELS]
    OUT.mkdir(parents=True, exist_ok=True)
    saved = 0
    for ch in chans:
        before, seen = None, 0
        while seen < HISTORY:
            params = {"limit": 100}
            if before:
                params["before"] = before
            batch = get(f"/channels/{ch['id']}/messages", **params)
            if not batch:
                break
            seen += len(batch)
            before = batch[-1]["id"]
            for m in batch:
                if str((m.get("author") or {}).get("id")) != str(me):
                    continue
                for a in m.get("attachments", []):
                    dest = target(a.get("filename", ""))
                    if dest is None or a.get("size", 0) > MAX:
                        continue
                    if not str(a.get("url", "")).startswith("https://cdn.discordapp.com/"):
                        continue
                    r = s.get(a["url"], timeout=60)
                    if not r.ok or len(r.content) > MAX:
                        continue
                    text = r.content.decode("utf-8", errors="replace")
                    if dest.exists() and dest.read_text(encoding="utf-8") == text:
                        continue
                    dest.write_text(text, encoding="utf-8")
                    saved += 1
                    print("gespeichert:", dest.relative_to(ROOT))
            if len(batch) < 100:
                break
    print(f"{saved} Datei(en) neu oder geändert.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
