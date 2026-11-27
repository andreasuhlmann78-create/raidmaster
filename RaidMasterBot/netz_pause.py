"""DC-UPL3 (ab Bot 1.5.203, Auftrag Supervisor 27.11.2026 20:55): Abbruch wegen Netz/DNS beim Anmelden.

Am 27.11. konnte der Bot discord.com zeitweise nicht auflösen ("Temporary failure in name resolution"); der Starter wartete nach
jedem Abbruch bis zu 300 s. Jetzt:
- bot.py beendet sich bei einem Netz-/DNS-Fehler beim Anmelden mit NET_CODE und merkt sich in data/netz_aus.json, seit wann
  (erster Fehler) und wie oft.
- launcher.py startet nach NET_CODE schon nach NET_WAIT (45 s) neu – nach mehr als NET_MAX_FAST Versuchen in Folge wieder 300 s
  (ein DNS-Fehler erreicht Discord gar nicht, zählt also nicht gegen die Anmelde-Grenze; ist Discord selbst gestört, nicht drängeln).
- Nach der Anmeldung (on_ready) schreibt der Bot einmal in #bot-log "Discord X Min. nicht erreichbar (Netz/DNS) – wieder verbunden".
Ohne discord.py (der Starter lädt diese Datei).
"""
from __future__ import annotations

import json
import os
import socket
import time

NET_CODE = 4
NET_WAIT = 45
NET_SLOW_WAIT = 300
NET_MAX_FAST = 60


def marker(base: str) -> str:
    return os.path.join(base, "data", "netz_aus.json")


def is_net_error(exc: BaseException) -> bool:
    """Netz/DNS beim Anmelden: aiohttp-Verbindungsfehler, socket.gaierror, Zeitüberschreitung, OSError beim Verbinden."""
    seen = set()
    while exc is not None and id(exc) not in seen:
        seen.add(id(exc))
        name = type(exc).__name__
        if isinstance(exc, (socket.gaierror, TimeoutError, ConnectionError)):
            return True
        if name in ("ClientConnectorError", "ClientConnectorDNSError", "ServerDisconnectedError",
                    "ClientOSError", "GatewayNotFound", "ConnectionClosed"):
            return True
        exc = exc.__cause__ or exc.__context__
    return False


def note_down(base: str, now: float | None = None) -> dict:
    now = time.time() if now is None else now
    path = marker(base)
    try:
        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)
    except (OSError, ValueError):
        d = {}
    d.setdefault("seit", now)
    d["versuche"] = int(d.get("versuche") or 0) + 1
    d["zuletzt"] = now
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(d, f)
    return d


def wait_seconds(base: str) -> int:
    try:
        with open(marker(base), "r", encoding="utf-8") as f:
            n = int(json.load(f).get("versuche") or 0)
    except (OSError, ValueError):
        n = 0
    return NET_SLOW_WAIT if n > NET_MAX_FAST else NET_WAIT


def take_down(base: str, now: float | None = None) -> tuple[int, int] | None:
    """Nach erfolgreicher Anmeldung: (Minuten seit dem ersten Fehler, Versuche) und den Merker löschen; None ohne Ausfall."""
    now = time.time() if now is None else now
    path = marker(base)
    try:
        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)
    except (OSError, ValueError):
        return None
    try:
        os.remove(path)
    except OSError:
        pass
    return max(1, round((now - float(d.get("seit") or now)) / 60)), int(d.get("versuche") or 0)
