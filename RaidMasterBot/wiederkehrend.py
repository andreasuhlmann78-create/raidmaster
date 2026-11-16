"""Wiederkehrende Raids (D-N1 Wunsch 3, ab Bot 1.5.186) – reine Funktionen ohne Discord.

Eine Vorlage (state.json unter "recurring") beschreibt einen festen Wochentermin:
{"id": 1, "pool": "mc", "title": "Molten Core Mittwoch", "weekday": 2, "time": "20:00", "weeks": 2,
 "description": "", "max": 0, "limits": {"heal": 8}, "paused": false, "creator": <Discord-ID>, "done": ["2026-11-18"]}
weekday: 0 = Montag … 6 = Sonntag. weeks: so viele Wochen im Voraus legt der Bot die Termine an (1–4).
Zeiten gelten in der Zeitzone des Servers (Europe/Zurich); ZoneInfo rechnet Sommer-/Winterzeit selbst.
"done" merkt sich die schon angelegten Tage – auch ein abgesagter oder gelöschter Termin wird nicht neu angelegt.
"""
from __future__ import annotations

import re
from datetime import date, datetime, timedelta

WEEKDAYS = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
MAX_WEEKS = 4
DONE_KEEP_DAYS = 14          # "done"-Einträge so lange nach dem Termin behalten


def parse_time(text: str) -> str:
    """'20:00', '20.00', '8:5' -> 'HH:MM'. ValueError, wenn es keine gültige Uhrzeit ist."""
    m = re.fullmatch(r"\s*(\d{1,2})[:.](\d{1,2})\s*", text or "")
    if not m:
        raise ValueError(text)
    h, mi = int(m.group(1)), int(m.group(2))
    if h > 23 or mi > 59:
        raise ValueError(text)
    return f"{h:02d}:{mi:02d}"


def local_dt(day: date, hhmm: str, tz) -> datetime:
    """Tag + Uhrzeit in der Zeitzone tz (mit Sommer-/Winterzeit)."""
    h, m = (int(x) for x in hhmm.split(":"))
    return datetime(day.year, day.month, day.day, h, m, tzinfo=tz)


def plan(tpl: dict, now: datetime, opens: date | None = None) -> list[datetime]:
    """Termine der Vorlage, die jetzt fällig sind: nach `now`, höchstens weeks*7 Tage voraus, nicht vor dem
    Öffnungsdatum des Raids (opens). now muss eine Zeitzone haben."""
    tz = now.tzinfo
    horizon = now + timedelta(days=7 * max(1, min(MAX_WEEKS, int(tpl.get("weeks") or 2))))
    out = []
    for i in range(0, 7 * MAX_WEEKS + 1):
        d = now.date() + timedelta(days=i)
        if d.weekday() != tpl["weekday"] or (opens and d < opens):
            continue
        dt = local_dt(d, tpl["time"], tz)
        if now < dt <= horizon:
            out.append(dt)
    return out


def already(tpl: dict, dt: datetime, raids: list[dict]) -> bool:
    """Gleicher Raid + gleicher Tag schon da? (in "done" der Vorlage oder als Raid im Buch – auch abgesagt oder
    von Hand erstellt)."""
    day = dt.date().isoformat()
    if day in (tpl.get("done") or []):
        return True
    for r in raids:
        if r.get("pool") == tpl["pool"] and datetime.fromtimestamp(r["start"], dt.tzinfo).date().isoformat() == day:
            return True
    return False


def mark_done(tpl: dict, dt: datetime, today: date):
    """Tag merken; alte Einträge (älter als DONE_KEEP_DAYS) entfernen."""
    keep = (today - timedelta(days=DONE_KEEP_DAYS)).isoformat()
    done = [d for d in (tpl.get("done") or []) if d >= keep]
    if dt.date().isoformat() not in done:
        done.append(dt.date().isoformat())
    tpl["done"] = sorted(done)


def describe(tpl: dict, pool_name: str) -> str:
    """'Molten Core – jeden Mittwoch 20:00, 2 Wochen im Voraus'."""
    w = int(tpl.get("weeks") or 2)
    return (f"{pool_name} – jeden {WEEKDAYS[tpl['weekday']]} {tpl['time']}, "
            f"{w} {'Woche' if w == 1 else 'Wochen'} im Voraus")
