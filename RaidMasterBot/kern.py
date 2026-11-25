"""Kern des Bots: Pfade, Einstellungen, Zeitzone, Logger und Datenbanken (D-3 Schritt 2, ab Bot 1.5.147).

Aus bot.py hierher verschoben, UNVERÄNDERT und in derselben Reihenfolge (Laden der config.json, Anlegen von state,
Datenbanken, Symbol-Liste). Alle Bot-Module holen sich diese Objekte mit "from kern import …" – es gibt sie nur
einmal (gleiche Objekte wie vorher in bot.py). Weg A "kern.py + Module" (Antwort der Prüf-Sitzung 15.11. 20:48).
Das Bot-Objekt selbst bleibt vorerst in bot.py.
"""
from __future__ import annotations

import json
import logging
import os
import shutil
import sys

import raidmaster_data as rmd

BASE = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE, "config.json")
DATA_DIR = os.path.join(BASE, "data")

log = logging.getLogger("raidmaster")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")

ORANGE = 0xFF8C1A
GREY = 0x555555

# ---------------------------------------------------------------------------
# Einstellungen
# ---------------------------------------------------------------------------

DEFAULT_CONFIG = {
    "token": "",
    "guild_id": 0,
    "timezone": "Europe/Zurich",
    "raid_creator_roles": ["Offizier", "Raidleitung"],
    "guild_leader": "",   # Gildenchef (Charaktername, steht in config.json): darf wie die Offiziere alles im Discord verändern
    "reminder_minutes": 60,
    "close_after_hours": 6,
    "savedvariables_path": "",
    "dkp_channel_id": 0,
    "dkp_channels": {},
    "loot_channel_id": 0,
    "assignment_channel_id": 0,
    "officer_channel_id": 0,
    "addon_channel_id": 0,
    "announce_channel_id": 0,
    "pug_channel_id": 0,
    "raid_channels": {},
    "auto_raid_categories": True,
    "notify_addon_updates": True,
    "notify_spec_changes": True,
    "send_assignment_dms": True,
    "data_channel_id": 0,
    "botcmd_channel_id": 0,
    "uploader_webhooks": [],
    "update_repo": "",
    "update_branch": "main",
    "update_token": "",
    "update_check_minutes": 30,
    "backup_days": 7,
    "message_content_intent": False,
    "guild_name": "Alpine Vanguard",
    "welcome_channel_id": 0,
    "command_list_channel_id": 0,
    "pug_invite_code": "",
    "pug_invite_url": "",
}

CONFIG_ERROR = 3   # launcher.py startet dann nicht neu


def load_config() -> dict:
    if not os.path.isfile(CONFIG_PATH):
        example = os.path.join(BASE, "config.example.json")
        if os.path.isfile(example):
            shutil.copy(example, CONFIG_PATH)
        print("Bitte zuerst config.json ausfüllen (Token, Server-ID usw.) – siehe ANLEITUNG.md")
        sys.exit(CONFIG_ERROR)
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    for k, v in DEFAULT_CONFIG.items():
        cfg.setdefault(k, v)
    if not cfg["token"] or "HIER" in cfg["token"]:
        print("In config.json fehlt der Bot-Token – siehe ANLEITUNG.md")
        sys.exit(CONFIG_ERROR)
    return cfg


def save_config():
    """Schreibt die aktuellen Einstellungen zurück in config.json.
    Ab 1.5.197 (D-CI2): Schlüssel, die der Nutzer bei laufendem Bot neu in config.json eingetragen hat (z. B.
    "github_actions_token"), bleiben erhalten – sie werden übernommen statt überschrieben."""
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            disk = json.load(f)
        if isinstance(disk, dict):
            for k, v in disk.items():
                cfg.setdefault(k, v)
    except (OSError, ValueError):
        pass
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


cfg = load_config()
TZ = cfg["timezone"]
book = rmd.RaidBook(DATA_DIR)
state = rmd.Store(os.path.join(DATA_DIR, "state.json"), {"dkp_messages": {}, "last_loot": None, "assign_v": 0,
                                                        "addon_version": "", "addon_message": None})
for _k, _v in {"installed_sha": "", "failed_sha": "", "last_backup": 0, "last_upload": 0, "last_upload_by": ""}.items():
    state.data.setdefault(_k, _v)
UPLOAD_PATH = os.path.join(DATA_DIR, "RaidMaster.lua")
GS_UPLOAD_PATH = os.path.join(DATA_DIR, "GuildSentinel.lua")   # Gildenbank-Bestand von GuildSentinel (nur bank)
# Upload ohne Gildenbank, nur mit Raidfähigkeit (ab 1.5.128, D-GS1) – getrennt, damit der Bank-Stand erhalten bleibt
GS_READY_PATH = os.path.join(DATA_DIR, "GuildSentinel-raidready.lua")
MARKT_DIR = os.path.join(DATA_DIR, "markt")           # MN7: Marktdaten (GSMARKT1), keine Namen
# eigene Beute-Datenbank (aus den Lootfenstern der Bosskills aller Uploader)
lootdb = rmd.Store(os.path.join(DATA_DIR, "loot_db.json"), rmd.lootdb_empty())
# Ruhmeshalle: alle Bosskills (Erstkills, Bestzeiten) und vergebene Erfolge
kills_db = rmd.Store(os.path.join(DATA_DIR, "kills.json"), {"kills": []})
fame_db = rmd.Store(os.path.join(DATA_DIR, "achievements.json"), {"init": False, "players": {}})
SHOTS_DIR = os.path.join(DATA_DIR, "shots")
ADDON_DIR = os.path.join(BASE, "addon")              # D-3 Schritt 9 (1.5.154): aus bot.py – Addon-Zips und Uploader
for _k, _v in rmd.lootdb_empty().items():
    lootdb.data.setdefault(_k, _v)
# Datei-ID -> Name der Spielsymbole (für die Item-Emojis; mitgeliefert, wird regelmäßig aktualisiert)
ICON_MAP_BUNDLED = os.path.join(BASE, "icon_fileids.json.gz")
ICON_MAP_FRESH = os.path.join(DATA_DIR, "icon_fileids.json.gz")
ICON_LISTFILE_URL = "https://github.com/wowdev/wow-listfile/releases/latest/download/community-listfile.csv"
rmd.load_icon_fileids(ICON_MAP_BUNDLED, ICON_MAP_FRESH)
if isinstance(state.data.get("dkp_messages"), list):
    # älteres Format: eine Tabelle -> gehört zu Molten Core
    state.data["dkp_messages"] = {"mc": state.data["dkp_messages"]}
